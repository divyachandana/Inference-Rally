"""Emergency contact fan-out: phone calls / SMS through Twilio, demo-grade and safe by default.

Hard rules (tested in tests/test_backend_notify.py):
- Dry run by default: nothing real is sent until the nurse-station laptop turns contacts_live on
  (POST /api/contacts {"live": true}). It is never saved, so every server start is a dry run again.
- Emergency services are ALWAYS simulated, whatever their channel says.
- Emergency short codes (911, 112, 999, 000, 110, 119, 118, 08 ...) and anything shorter than
  8 digits are refused as contact numbers, for every role.
- At most one real fan-out per alert per 60 s, at most 5 real calls/SMS per fan-out, and at most
  20 real calls/SMS per hour across the whole server.
- Credentials come only from the environment (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM):
  never logged, never in the state file, never in any file this server writes.
- Messages carry alert facts only (who, where, time, level, outside temperature), never video and
  never health readings, and always start with "This is a NightWatch demo."
- No internet / no Twilio: the contact is marked "simulated" with the reason; staff phones are
  alerted by the local server either way. Sending happens in background threads, so an alert
  never waits on the network (8 s timeout per request).
"""
from __future__ import annotations

import base64
import json
import os
import re
import secrets
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path
from xml.sax.saxutils import escape

ROLES = ("on_call", "family", "owner", "emergency_services", "other")
CHANNELS = ("call", "sms", "call+sms", "simulated")
EMERGENCY_CODES = {"911", "112", "999", "000", "110", "119", "118", "08", "100", "101", "102", "999", "933"}
E164 = re.compile(r"^\+[1-9]\d{7,14}$")
IDENT = re.compile(r"^[A-Za-z0-9_.-]{1,24}$")
FANOUT_GAP_S = 60
MAX_REAL_PER_FANOUT = 5
MAX_REAL_PER_HOUR = 20
TIMEOUT_S = 8
MAX_CONTACTS = 20
PREFIX = "This is a NightWatch demo."

DEFAULT_CONTACTS: list[dict[str, object]] = [
    {"id": "oncall", "role": "on_call", "name": "On-call supervisor", "phone": "", "channel": "simulated", "residents": []},
    {"id": "family-r07", "role": "family", "name": "Family of R-07", "phone": "", "channel": "simulated", "residents": ["R-07"]},
    {"id": "owner", "role": "owner", "name": "Facility owner", "phone": "", "channel": "simulated", "residents": []},
    {"id": "ems", "role": "emergency_services", "name": "Emergency services", "phone": "", "channel": "simulated", "residents": []},
]


class NotConfigured(Exception):
    pass


class Offline(Exception):
    pass


class SendFailed(Exception):
    pass


def clean_phone(raw: object) -> str:
    """Normalise to E.164 ('+15551234821'), or '' for none. Raises ValueError for emergency/short numbers."""
    if raw is None or raw == "":
        return ""
    if not isinstance(raw, str):
        raise ValueError("phone must be text, e.g. +15551234821")
    p = re.sub(r"[\s().-]", "", raw)
    digits = re.sub(r"\D", "", p)
    if digits in EMERGENCY_CODES or len(digits) < 8:
        raise ValueError(f"{raw!r} looks like an emergency or short number: NightWatch never dials those "
                         "(emergency services are always simulated)")
    if not E164.match(p):
        raise ValueError(f"phone {raw!r} must be in international format, e.g. +15551234821")
    return p


def mask(phone: str) -> str:
    return f"{phone[:2]} •••• {phone[-4:]}" if phone else ""


def validate_contacts(items: object) -> list[dict[str, object]]:
    if not isinstance(items, list):
        raise ValueError("contacts must be a list")
    if len(items) > MAX_CONTACTS:
        raise ValueError(f"at most {MAX_CONTACTS} contacts")
    out, seen = [], set()
    for i, c in enumerate(items):
        if not isinstance(c, dict):
            raise ValueError(f"contact {i + 1} must be an object")
        cid = str(c.get("id") or f"c-{secrets.token_hex(3)}")
        if not IDENT.match(cid) or cid in seen:
            raise ValueError(f"contact {i + 1}: id must be unique, 1-24 letters/digits/- _ .")
        seen.add(cid)
        role = c.get("role")
        if role not in ROLES:
            raise ValueError(f"contact {cid}: role must be one of {', '.join(ROLES)}")
        name = str(c.get("name") or "").strip()
        if not name or len(name) > 60:
            raise ValueError(f"contact {cid}: name is required (at most 60 characters)")
        channel = c.get("channel") or "simulated"
        if channel not in CHANNELS:
            raise ValueError(f"contact {cid}: channel must be one of {', '.join(CHANNELS)}")
        try:
            phone = clean_phone(c.get("phone"))
        except ValueError as exc:
            raise ValueError(f"contact {cid}: {exc}") from None
        if channel != "simulated" and role != "emergency_services" and not phone:
            raise ValueError(f"contact {cid}: a phone number is needed for {channel}")
        residents = c.get("residents") or []
        if not isinstance(residents, list) or len(residents) > 50 or not all(isinstance(r, str) and IDENT.match(r) for r in residents):
            raise ValueError(f"contact {cid}: residents must be a list of resident ids")
        out.append({"id": cid, "role": role, "name": name, "phone": phone, "channel": channel, "residents": residents})
    return out


class Twilio:
    """Stdlib-only Twilio REST client. Credentials are read from the environment on every call."""

    API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/{what}.json"

    @staticmethod
    def configured() -> bool:
        return all(os.environ.get(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM"))

    def _post(self, what: str, fields: dict[str, str]) -> str:
        sid, token, sender = (os.environ.get(k, "") for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM"))
        if not (sid and token and sender):
            raise NotConfigured("Twilio not configured")
        req = urllib.request.Request(
            self.API.format(sid=urllib.parse.quote(sid), what=what),
            urllib.parse.urlencode({**fields, "From": sender}).encode(),
            {"Authorization": "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode(),
             "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                return str(json.loads(r.read() or b"{}").get("status") or "queued")
        except urllib.error.HTTPError as exc:
            try:
                msg = json.loads(exc.read()).get("message") or exc.reason
            except (ValueError, OSError):
                msg = exc.reason
            msg = re.sub(r"\+?\d{6,}", lambda m: mask(m[0]), str(msg))[:160]   # no full numbers in history/logs
            raise SendFailed(f"Twilio said HTTP {exc.code}: {msg}") from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError):
            raise Offline("no internet: staff phones still alerted") from None

    def call(self, to: str, text: str) -> str:
        say = escape(text)
        twiml = (f'<Response><Say voice="alice">{say}</Say><Pause length="1"/>'
                 f'<Say voice="alice">Repeating. {say}</Say></Response>')
        return self._post("Calls", {"To": to, "Twiml": twiml})

    def sms(self, to: str, text: str) -> str:
        return self._post("Messages", {"To": to, "Body": text})


class Notifier:
    def __init__(self, path: Path | None, transport: object | None = None) -> None:
        self.path = path
        self.transport = transport or Twilio()
        self.live = False                 # dry run until the laptop turns it on; never saved
        self._lock = threading.Lock()
        self._sent: deque[float] = deque()  # real sends in the last hour
        self.contacts = self._load()

    def _load(self) -> list[dict[str, object]]:
        if self.path is None:
            return [dict(c) for c in DEFAULT_CONTACTS]
        try:
            return validate_contacts(json.loads(self.path.read_text()).get("contacts"))
        except (OSError, ValueError, AttributeError):
            contacts = [dict(c) for c in DEFAULT_CONTACTS]
            if not self.path.exists():
                self._save(contacts)
            return contacts

    def _save(self, contacts: list[dict[str, object]]) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"_note": "Local only (git-ignored data/). Edit in /settings/ or POST /api/contacts.",
                                   "contacts": contacts}, indent=2))
        os.replace(tmp, self.path)

    def configured(self) -> bool:
        return bool(getattr(self.transport, "configured", lambda: False)())

    def view(self, local: bool) -> dict[str, object]:
        with self._lock:
            contacts = [dict(c) if local else dict(c, phone=mask(str(c["phone"]))) for c in self.contacts]
            return {"live": self.live, "twilio_configured": self.configured(), "contacts": contacts,
                    "roles": list(ROLES), "channels": list(CHANNELS),
                    "limits": {"fanout_gap_s": FANOUT_GAP_S, "per_fanout": MAX_REAL_PER_FANOUT, "per_hour": MAX_REAL_PER_HOUR}}

    def update(self, contacts: object | None = None, live: bool | None = None) -> None:
        clean = validate_contacts(contacts) if contacts is not None else None
        with self._lock:
            if clean is not None:
                self._save(clean)
                self.contacts = clean
            if live is not None:
                self.live = live

    def contacts_for(self, resident: str | None) -> list[dict[str, object]]:
        """Who to tell about an alert: family only for their own resident; resident lists scope others too."""
        with self._lock:
            out = []
            for c in self.contacts:
                scoped = c["residents"]
                if c["role"] == "family" and not resident:
                    continue
                if scoped and resident not in scoped:  # type: ignore[operator]
                    continue
                out.append(dict(c))
            return out

    def take_budget(self) -> bool:
        """One real send against the hourly cap."""
        with self._lock:
            now = time.time()
            while self._sent and now - self._sent[0] > 3600:
                self._sent.popleft()
            if len(self._sent) >= MAX_REAL_PER_HOUR:
                return False
            self._sent.append(now)
            return True

    def send(self, channel: str, to: str, text: str) -> tuple[str, str]:
        """Blocking (run in a thread). Returns (status, detail)."""
        try:
            fn = self.transport.call if channel == "call" else self.transport.sms  # type: ignore[attr-defined]
            twilio_status = fn(to, text)
            return ("calling" if channel == "call" else "sent"), str(twilio_status)
        except NotConfigured as exc:
            return "simulated", str(exc)
        except Offline as exc:
            return "simulated", str(exc)
        except SendFailed as exc:
            return "failed", str(exc)
        except Exception as exc:  # noqa: BLE001 - never let a send crash anything
            return "failed", type(exc).__name__
