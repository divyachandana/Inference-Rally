"""NightWatch engine: resident state, day/night modes and the escalation ladder.

Level 1  Heads-up   resident up and unusual for this time   -> quiet alert to the night staff phone
Level 2  Urgent     exit door / window opened at night       -> loud alert, must be acknowledged
Level 3  Emergency  no acknowledgement in time, or resident  -> on-call supervisor, then emergency
                    confirmed outside                           services per facility policy

Escalation only climbs when nobody responds: one night worker for a whole wing is often busy
with another resident, so the system keeps going for them. It never dials anyone in this build:
contact steps are logged as "(simulated)".
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from features import vector

NIGHT_START, NIGHT_END = 21, 5   # matches the care records' night band (21:00-05:00)
SEVERITY = {1: "routine", 2: "notable", 3: "escalation"}  # the care team's derived severity scale
UNUSUAL_ALERT = 0.9              # model score that counts as "unusual for right now"
SUSTAIN_S = 5                    # ...for this many consecutive seconds (one odd reading is not an alert)


@dataclass
class Resident:
    id: str
    name: str
    room: str
    wander_risk: float
    hr_rest: float
    pattern: str
    what_helped: list[list[object]]
    description: str
    x: float
    y: float
    in_bed: bool = True
    zone: str = "room"
    hr: float | None = None
    motion: float = 0.03
    up_since: float | None = None   # virtual epoch seconds
    unusual: float = 0.0
    unusual_streak: int = 0
    quiet_until: float = 0.0       # real time; staff are with the resident, no new heads-ups
    last_exit: str | None = None

    def suggestions(self) -> list[str]:
        ranked = sorted(self.what_helped, key=lambda h: (-int(h[1]) / max(int(h[2]), 1), -int(h[2])))
        return [f"{name}: settled them {helped} of {tried} times" for name, helped, tried in ranked]


@dataclass
class Exit:
    id: str
    label: str
    kind: str
    x: float
    y: float
    short: str = ""
    open: bool = False


@dataclass
class Alert:
    id: int
    level: int
    title: str
    resident: str | None
    exit: str | None
    created: float = field(default_factory=time.time)
    level_since: float = field(default_factory=time.time)
    acked_by: str | None = None
    acked_at: float | None = None
    resolved: str | None = None
    history: list[tuple[str, str]] = field(default_factory=list)
    contact_step: int = 0
    max_level: int = 0
    went_outside: bool = False
    record: dict[str, object] | None = None


class Engine:
    def __init__(self, facility_path: Path, scorer: object, l1_timeout: float, ack_timeout: float) -> None:
        self.facility_path = facility_path
        self.scorer = scorer
        self.l1_timeout = l1_timeout
        self.ack_timeout = ack_timeout
        self.lock = threading.RLock()
        self.latencies: deque[float] = deque(maxlen=300)
        self._scenario: threading.Thread | None = None
        self._scenario_stop = threading.Event()
        self.reset()

    # ------------------------------------------------------------------ clock and setup

    def reset(self) -> None:
        with self.lock:
            spec = json.loads(self.facility_path.read_text())
            self.facility = spec["facility"]
            self.night_staff = spec["night_staff"]
            self.outside_temp_c = spec["outside_temp_c"]
            self.residents = {r["id"]: Resident(**r) for r in spec["residents"]}
            self.exits = {e["id"]: Exit(**e) for e in spec["exits"]}
            self.alerts: list[Alert] = []
            self.events: deque[dict[str, str]] = deque(maxlen=60)
            self.visits_today = 0
            self._next_alert = 1
            self._base_real = time.time()
            self._base_virtual = self._base_real
            self.speed = 1.0

    def now(self) -> float:
        """Virtual epoch seconds (the demo can jump to 2 am)."""
        return self._base_virtual + (time.time() - self._base_real) * self.speed

    def clock(self) -> datetime:
        return datetime.fromtimestamp(self.now())

    def set_time(self, hhmm: str, speed: float | None = None) -> None:
        with self.lock:
            h, m = (int(v) for v in hhmm.split(":"))
            target = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
            self._base_real, self._base_virtual = time.time(), target.timestamp()
            if speed is not None:
                self.speed = speed
            self.log("clock", f"Clock set to {hhmm} ({'night' if self.is_night() else 'day'} mode)")

    def is_night(self) -> bool:
        h = self.clock().hour
        return h >= NIGHT_START or h < NIGHT_END

    def stamp(self) -> str:
        return self.clock().strftime("%H:%M:%S")

    def log(self, kind: str, text: str) -> None:
        self.events.appendleft({"t": self.stamp(), "kind": kind, "text": text})

    # ------------------------------------------------------------------ sensor events

    def sensor(self, ev: dict[str, object]) -> dict[str, object]:
        with self.lock:
            kind = ev.get("type")
            r = self.residents.get(str(ev.get("resident", "")))
            if kind == "door":
                return self._door(str(ev["exit"]), bool(ev.get("open", True)))
            if r is None:
                return {"error": f"unknown resident {ev.get('resident')!r}"}
            if kind == "bed":
                r.in_bed = bool(ev["in_bed"])
                r.up_since = None if r.in_bed else self.now()
                # Until the wearable reports, assume light movement when up and stillness in bed.
                r.motion = 0.03 if r.in_bed else max(r.motion, 0.25)
                if r.in_bed:
                    r.zone = "room"
                self.log("sensor", f"{r.name} {'back in bed' if r.in_bed else 'out of bed'}")
            elif kind == "hr":
                r.hr = float(ev["bpm"])  # type: ignore[arg-type]
            elif kind == "motion":
                r.motion = float(ev["level"])  # type: ignore[arg-type]
            elif kind == "location":
                zone = str(ev["zone"])
                if zone != r.zone:
                    r.zone = zone
                    if zone != "room" and r.in_bed:
                        r.in_bed, r.up_since = False, r.up_since or self.now()
                    if zone != "room":
                        r.motion = max(r.motion, 0.3)  # moving between zones means walking
                    self.log("sensor", f"{r.name} -> {zone}")
                    if self.is_night() and zone in ("corridor", "common", "exit") and time.time() >= r.quiet_until:
                        # The rule that matters at night: a resident has left their room.
                        self._raise(1, f"{r.name} left their room at {self.clock():%H:%M}", r, None)
                    if zone == "outside":
                        self._outside(r, str(ev.get("exit") or r.last_exit or "an exit"))
            else:
                return {"error": f"unknown event type {kind!r}"}
            return {"ok": True}

    def _door(self, exit_id: str, opened: bool) -> dict[str, object]:
        ex = self.exits.get(exit_id)
        if ex is None:
            return {"error": f"unknown exit {exit_id!r}"}
        ex.open = opened
        if not opened:
            self.log("door", f"{ex.label} closed")
            return {"ok": True}
        near = sorted((r for r in self.residents.values() if not r.in_bed and r.zone in ("exit", "corridor")),
                      key=lambda r: (r.zone != "exit", -r.wander_risk))
        who = near[0] if near else None
        if who:
            who.last_exit = ex.id
        if self.is_night() or ex.kind == "window":
            level = 2 if self.is_night() else 1
            title = f"{ex.label} opened at {self.clock():%H:%M}" + (f": {who.name} nearby" if who else "")
            self._raise(level, title, who, ex)
        else:
            self.visits_today += 1
            self.log("door", f"{ex.label} opened (day: logged as visit #{self.visits_today})")
            if who and who.wander_risk >= 0.7 and who.zone == "exit":
                self._raise(1, f"{who.name} (high wander risk) at the {ex.label.lower()} while it is open", who, ex)
        return {"ok": True}

    def _outside(self, r: Resident, exit_id: str) -> None:
        ex = self.exits.get(exit_id)
        label = ex.label if ex else exit_id
        a = self._raise(3, f"{r.name} is OUTSIDE via {label}. {self.outside_temp_c} °C", r, ex, force=True)
        a.went_outside = True

    # ------------------------------------------------------------------ alerts

    def _open_alert_for(self, r: Resident | None, ex: Exit | None) -> Alert | None:
        for a in self.alerts:
            if a.resolved:
                continue
            if (r and a.resident == r.id) or (ex and a.exit == ex.id and a.resident is None):
                return a
        return None

    def _raise(self, level: int, title: str, r: Resident | None, ex: Exit | None, force: bool = False) -> Alert:
        a = self._open_alert_for(r, ex)
        if a is None:
            a = Alert(self._next_alert, level, title, r.id if r else None, ex.id if ex else None)
            self._next_alert += 1
            self.alerts.append(a)
            a.max_level = level
            a.history.append((self.stamp(), f"Level {level}: {title}"))
            self.log(f"L{level}", title)
        elif level > a.level or force:
            a.title = title
            if ex and not a.exit:
                a.exit = ex.id
            self._set_level(a, max(level, a.level), title)
        if a.level == 3 and a.contact_step == 0:
            self._contact(a)
        return a

    def _set_level(self, a: Alert, level: int, why: str) -> None:
        if level == a.level and a.history:
            return
        a.level, a.level_since = level, time.time()
        a.max_level = max(a.max_level, level)
        if level >= 2:
            a.acked_by, a.acked_at = None, None  # a new urgent fact needs a fresh acknowledgement
        a.history.append((self.stamp(), f"Level {level}: {why}"))
        self.log(f"L{level}", f"Alert #{a.id} -> level {level}: {why}")

    def _contact(self, a: Alert) -> None:
        """Walk the contact chain one step. Never dials in this build."""
        steps = [
            "All staff phones: emergency alarm",
            "Calling on-call supervisor (simulated)",
            "Emergency services would be called now per facility policy (simulated: this demo never dials)",
        ]
        if a.contact_step < len(steps):
            a.history.append((self.stamp(), steps[a.contact_step]))
            self.log("contact", f"Alert #{a.id}: {steps[a.contact_step]}")
            a.contact_step += 1
            a.level_since = time.time()

    def ack(self, alert_id: int, by: str) -> dict[str, object]:
        with self.lock:
            a = next((x for x in self.alerts if x.id == alert_id), None)
            if a is None or a.resolved:
                return {"error": "no such open alert"}
            a.acked_by, a.acked_at = by, time.time()
            secs = round(a.acked_at - a.created)
            a.history.append((self.stamp(), f"Acknowledged by {by} ({secs} s after first alert)"))
            self.log("ack", f"Alert #{a.id} acknowledged by {by} after {secs} s")
            return {"ok": True}

    def resolve(self, alert_id: int, outcome: str) -> dict[str, object]:
        with self.lock:
            a = next((x for x in self.alerts if x.id == alert_id), None)
            if a is None or a.resolved:
                return {"error": "no such open alert"}
            self._close(a, outcome, by_staff=True)
            r = self.residents.get(a.resident or "")
            if r:
                # Staff walked them back: settled in their room, and staff stay close for a while.
                r.zone, r.in_bed, r.up_since, r.motion = "room", True, None, 0.03
                r.hr = r.hr_rest + 8 if r.hr else None
                r.quiet_until = time.time() + 120
            if a.exit and a.exit in self.exits:
                self.exits[a.exit].open = False
            return {"ok": True}

    def _close(self, a: Alert, outcome: str, by_staff: bool) -> None:
        a.resolved = outcome
        a.record = self._care_record(a, by_staff)
        a.history.append((self.stamp(), f"Resolved: {outcome} · severity {a.record['severity']} {a.record['severity_label']}"))
        self.log("resolved", f"Alert #{a.id} resolved: {outcome} (severity {a.record['severity']} {a.record['severity_label']})")

    def _care_record(self, a: Alert, by_staff: bool) -> dict[str, object]:
        """Draft entry in the care team's event-record format (taxonomy v2).

        Location is recorded as a type, never a room, and time as a band at night. Affect and the
        intervention actually used are left for staff to confirm: the system doesn't know them.
        """
        night = self.is_night()
        h = self.clock().hour
        earlier = sum(1 for x in self.alerts if x.resident == a.resident and x.id != a.id and x.created < a.created)
        severity = max(a.max_level, 1)
        return {
            "resident": a.resident,
            "category": "Behaviour and distress",
            "behaviour": "Exit-seeking or wandering" if (a.exit or a.went_outside) else "Restlessness",
            "affect": "(staff to confirm)",
            "frequency": "Isolated" if earlier == 0 else "Repeated",
            "time_of_day": "Night" if night else "Morning" if h < 12 else "Afternoon" if h < 18 else "Evening",
            "night_band": "Night (21:00-05:00)" if night else None,
            "location_type": "Exterior (left the building)" if a.went_outside
                             else "Communal / circulation" if a.exit else "Own room",
            "trigger": "Night / unsettled" if night else None,
            "intervention": "(staff to confirm)" if by_staff else "Monitoring",
            "outcome": "Escalated for clinical review" if severity == 3 else "Managed without further escalation",
            "severity": severity,
            "severity_label": SEVERITY[severity],
            "draft_by": "NightWatch: confirm affect and intervention before filing",
        }

    # ------------------------------------------------------------------ the 1 s loop

    def tick(self) -> None:
        with self.lock:
            hour = self.clock().hour + self.clock().minute / 60
            night = self.is_night()
            for r in self.residents.values():
                minutes_up = 0.0 if r.up_since is None else (self.now() - r.up_since) / 60
                x = vector(hour, not r.in_bed, r.motion, r.hr, r.hr_rest, r.zone, minutes_up)
                r.unusual, ms = self.scorer.score(x)  # type: ignore[attr-defined]
                self.latencies.append(ms)
                r.unusual_streak = r.unusual_streak + 1 if (night and not r.in_bed and r.unusual >= UNUSUAL_ALERT) else 0
                if r.unusual_streak >= SUSTAIN_S and r.zone != "outside" and time.time() >= r.quiet_until:
                    if self._open_alert_for(r, None) is None:
                        hr = f", heart rate {r.hr:.0f} (rest {r.hr_rest:.0f})" if r.hr else ""
                        self._raise(1, f"{r.name} is up at {self.clock():%H:%M}, unusual for them{hr}", r, None)
            now = time.time()
            for a in self.alerts:
                if a.resolved:
                    continue
                r = self.residents.get(a.resident or "")
                if a.level == 1 and r and r.in_bed and not a.exit:
                    # A heads-up clears itself when the resident settles back into bed.
                    self._close(a, "Settled back in bed on their own", by_staff=False)
                    continue
                if a.acked_by:
                    continue
                waited = now - a.level_since
                if a.level == 1 and waited >= self.l1_timeout and r and r.unusual >= UNUSUAL_ALERT:
                    self._set_level(a, 2, f"no response for {int(waited)} s")
                elif a.level == 2 and waited >= self.ack_timeout:
                    self._set_level(a, 3, f"not acknowledged within {int(waited)} s")
                    self._contact(a)
                elif a.level == 3 and waited >= self.ack_timeout:
                    self._contact(a)

    # ------------------------------------------------------------------ view

    def view(self) -> dict[str, object]:
        with self.lock:
            lat = sorted(self.latencies)
            open_alerts = [a for a in self.alerts if not a.resolved]
            acked = [a.acked_at - a.created for a in self.alerts if a.acked_at]
            return {
                "facility": self.facility, "night_staff": self.night_staff, "outside_temp_c": self.outside_temp_c,
                "clock": self.clock().strftime("%H:%M:%S"), "night": self.is_night(), "speed": self.speed,
                "scorer": {"name": self.scorer.name, "device": self.scorer.device,  # type: ignore[attr-defined]
                           "p50_ms": round(lat[len(lat) // 2], 3) if lat else None,
                           "p95_ms": round(lat[int(len(lat) * 0.95)], 3) if lat else None},
                "timeouts": {"l1": self.l1_timeout, "ack": self.ack_timeout},
                "residents": [
                    {"id": r.id, "name": r.name, "room": r.room, "risk": r.wander_risk, "in_bed": r.in_bed,
                     "zone": r.zone, "hr": r.hr, "hr_rest": r.hr_rest, "unusual": round(r.unusual, 3),
                     "pattern": r.pattern, "description": r.description, "x": r.x, "y": r.y,
                     "suggestions": r.suggestions()}
                    for r in self.residents.values()
                ],
                "exits": [vars(e) for e in self.exits.values()],
                "alerts": [self._alert_view(a) for a in sorted(open_alerts, key=lambda a: (-a.level, a.created))],
                "recent": [self._alert_view(a) for a in self.alerts if a.resolved][-5:],
                "events": list(self.events),
                "stats": {"visits_today": self.visits_today, "alerts": len(self.alerts),
                          "median_ack_s": round(sorted(acked)[len(acked) // 2]) if acked else None},
            }

    def _alert_view(self, a: Alert) -> dict[str, object]:
        r = self.residents.get(a.resident or "")
        due = None
        if not a.resolved and not a.acked_by:
            limit = self.l1_timeout if a.level == 1 else self.ack_timeout
            due = max(0, round(limit - (time.time() - a.level_since)))
        return {"id": a.id, "level": a.level, "title": a.title, "resident": a.resident, "exit": a.exit,
                "age_s": round(time.time() - a.created), "acked_by": a.acked_by, "resolved": a.resolved,
                "escalates_in_s": due, "history": a.history,
                "description": r.description if r else None, "room": r.room if r else None,
                "suggestions": r.suggestions()[:2] if r else [],
                "max_level": a.max_level, "record": a.record}

    # ------------------------------------------------------------------ scripted demo scenarios

    def run_scenario(self, name: str) -> dict[str, object]:
        steps = SCENARIOS.get(name)
        if steps is None:
            return {"error": f"unknown scenario {name!r}", "choices": sorted(SCENARIOS)}
        self._scenario_stop.set()
        if self._scenario and self._scenario.is_alive():
            self._scenario.join(timeout=2)
        self._scenario_stop = threading.Event()
        stop = self._scenario_stop

        def run() -> None:
            for delay, action in steps:
                if stop.wait(delay):
                    return
                action(self)

        self._scenario = threading.Thread(target=run, daemon=True, name=f"scenario-{name}")
        self._scenario.start()
        return {"ok": True, "scenario": name}


def _s(ev: dict[str, object]) -> Callable[[Engine], object]:
    return lambda e: e.sensor(ev)


def _unacked(rid: str, ev: dict[str, object]) -> Callable[[Engine], object]:
    """Only happens if nobody has responded to this resident's alert yet."""
    def act(e: Engine) -> None:
        open_alert = next((a for a in e.alerts if a.resident == rid and not a.resolved), None)
        if open_alert is not None and not open_alert.acked_by:
            e.sensor(ev)
    return act


def _hr_ramp(rid: str, start: int, end: int, steps: int, gap: float) -> list[tuple[float, Callable[[Engine], object]]]:
    return [(gap, _s({"type": "hr", "resident": rid, "bpm": start + (end - start) * i / (steps - 1)})) for i in range(steps)]


SCENARIOS: dict[str, list[tuple[float, Callable[[Engine], object]]]] = {
    # 02:08. R-07 gets up, gets agitated, heads for the front door, and walks out if nobody responds.
    "night_elopement": [
        (0, lambda e: (e.reset(), e.set_time("02:08"))),
        (1, _s({"type": "hr", "resident": "R-07", "bpm": 67})),
        (2, _s({"type": "bed", "resident": "R-07", "in_bed": False})),
        (1, _s({"type": "motion", "resident": "R-07", "level": 0.5})),
        *_hr_ramp("R-07", 72, 96, 6, 1.5),
        (1, _s({"type": "location", "resident": "R-07", "zone": "corridor"})),
        (6, _s({"type": "location", "resident": "R-07", "zone": "exit"})),
        (3, _s({"type": "door", "exit": "front", "open": True})),
        (40, _unacked("R-07", {"type": "location", "resident": "R-07", "zone": "outside", "exit": "front"})),
    ],
    # 03:00. R-15 makes a short ensuite trip. Normal for them: the system should stay quiet.
    "night_bathroom": [
        (0, lambda e: (e.reset(), e.set_time("03:00"))),
        (1, _s({"type": "hr", "resident": "R-15", "bpm": 63})),
        (2, _s({"type": "bed", "resident": "R-15", "in_bed": False})),
        (1, _s({"type": "motion", "resident": "R-15", "level": 0.3})),
        (1, _s({"type": "hr", "resident": "R-15", "bpm": 68})),
        (20, _s({"type": "bed", "resident": "R-15", "in_bed": True})),
    ],
    # 14:00. Visitors come and go; residents walk the corridors. Logged, no alarms.
    "day_visits": [
        (0, lambda e: (e.reset(), e.set_time("14:00"))),
        *[(0.5, _s({"type": "location", "resident": rid, "zone": z}))
          for rid, z in (("R-03", "common"), ("R-21", "corridor"), ("R-15", "common"), ("R-07", "common"))],
        (3, _s({"type": "door", "exit": "front", "open": True})),
        (2, _s({"type": "door", "exit": "front", "open": False})),
        (5, _s({"type": "door", "exit": "garden", "open": True})),
        (2, _s({"type": "door", "exit": "garden", "open": False})),
        (5, _s({"type": "door", "exit": "front", "open": True})),
        (2, _s({"type": "door", "exit": "front", "open": False})),
    ],
    "reset": [(0, lambda e: e.reset())],
}
