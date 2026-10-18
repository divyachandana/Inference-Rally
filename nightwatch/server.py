"""NightWatch local server. Standard library only (plus ExecuTorch if a model is loaded).

    python nightwatch/server.py --model models/normal_pattern_qnn.pte --device NPU      # on the Copilot+ PC
    python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --device CPU
    python nightwatch/server.py                                                          # rule fallback
    add --lan to let staff phones on the facility Wi-Fi open /staff/ (still never leaves the building)
    add --fresh to start a clean night instead of restoring tonight's saved state

Restart-safe: alerts (history, care records, acks), events, visits, camera on/off/schedule and doorway
lines and the demo clock are saved to logs/night_state.json (git-ignored) about 1 s after every change
and restored on the next start if the file is from the same night. Scenarios and settings reset it.

Pages:  /dashboard/  (nurse station)   /staff/  (night staff phone)   /sim/  (sensor simulator for demos)

API (JSON):
    POST /api/pair      {"pin": "123456", "name": "Night nurse phone"} -> {"token"}   (other devices must pair;
                        then send header X-NightWatch-Token on every /api/ call. The laptop itself is trusted.)
    GET  /api/state
    GET  /api/bench     benchmark runs from nightwatch/bench/benchmark.py (newest first) + the running job
    POST /api/bench/run {"kind": "detector"|"pattern", "seconds": 10}  start one (laptop only)
    GET  /api/resident?id=R-07   profile, now, last 30 min history, tonight's alerts
    GET  /api/settings  /  POST /api/settings (laptop only; saved to git-ignored data/facility.local.json)
    GET  /api/health    models, cameras, uptime; plus phone PIN/address for the laptop itself
    POST /api/record    {"alert", "affect", "intervention", "nondrug_alt"?, "note"?, "by"}  file a care record
    POST /api/backup    {"alert", "by"}  ask for help: all staff phones alerted
    GET  /api/report    the night's shift report (every alert, response times, severity, draft care records)
    POST /api/sensor    {"type": "door", "exit": "front", "open": true}
                        {"type": "bed" | "hr" | "motion" | "location", "resident": "R-07", ...}
    POST /api/ack       {"alert": 3, "by": "Night nurse"}
    POST /api/resolve   {"alert": 3, "outcome": "Found safe, walked back"}
    POST /api/clock     {"time": "02:08", "speed": 1}
    POST /api/frame     {"camera": "hall12", "jpeg": "<base64>"}   (analysed in memory, never stored)
    POST /api/camera/config {"camera": "hall12", "line": [x1, y1, x2, y2] | null, "inside": 1 | -1}
                        or {"camera": "hall12", "enabled": true|false, "schedule": "always"|"night", "by": "..."}
    POST /api/scenario  {"name": "night_elopement" | "night_bathroom" | "day_visits" | "reset"}
"""
from __future__ import annotations

import argparse
import base64
import json
import socket
from urllib.parse import parse_qs, urlparse
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine import Engine  # noqa: E402
from pairing import Pairing  # noqa: E402
from scorer import build  # noqa: E402
from vision.tracker import Tracker  # noqa: E402

STATE_FILE = HERE.parent / "logs" / "night_state.json"   # git-ignored
ENGINE: Engine
DETECTOR: object | None = None
TRACKERS: dict[str, Tracker] = {}
PAIRING: Pairing
# Locking (no deadlocks): ENGINE.lock is an RLock guarding all engine state; every engine method takes it.
# TRACK_LOCK guards TRACKERS and may be held while taking ENGINE.lock, never the other way round.
# DETECT_LOCK serialises the detector (one ExecuTorch method instance is not safe to run concurrently)
# and is never held with the other two. BENCH_LOCK only guards BENCH_JOB's check-and-start.
TRACK_LOCK = threading.Lock()
DETECT_LOCK = threading.Lock()
BENCH_LOCK = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(HERE / "web"), **kwargs)  # type: ignore[arg-type]

    def log_message(self, fmt: str, *args: object) -> None:
        if "/api/state" not in self.path:
            super().log_message(fmt, *args)

    def _authorized(self) -> bool:
        """The laptop is trusted; other devices need a paired token (see pairing.py)."""
        if PAIRING.allowed(self.client_address[0], self.headers.get("X-NightWatch-Token")):
            return True
        self._json({"error": "pair this device first", "pair": True}, 401)
        return False

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/") and not self._authorized():
            return None
        url = urlparse(self.path)
        if url.path == "/api/resident":
            return self._json(ENGINE.resident_detail(parse_qs(url.query).get("id", [""])[0]))
        if url.path == "/api/settings":
            return self._json(ENGINE.settings())
        if url.path == "/api/health":
            return self._json(_health(PAIRING.is_local(self.client_address[0])))
        if self.path == "/api/state":
            view = ENGINE.view()
            if PAIRING.is_local(self.client_address[0]):
                # Only the laptop itself sees the PIN, to show it on the nurse-station screen.
                view["pairing"] = {"pin": PAIRING.pin, "devices": PAIRING.devices}
            return self._json(view)
        if self.path == "/api/report":
            return self._json(ENGINE.report())
        if self.path == "/api/bench":
            return self._json(_bench_runs() | {"job": {k: v for k, v in BENCH_JOB.items() if k != "cmd"}})
        if self.path in ("", "/"):
            self.send_response(302)
            self.send_header("Location", "/home/" if (HERE / "web" / "home" / "index.html").exists() else "/dashboard/")
            self.end_headers()
            return None
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "bad json"}, 400)
        if self.path == "/api/pair":
            ok, result = PAIRING.pair(self.client_address[0], str(body.get("pin", "")), str(body.get("name", "phone")))
            if ok:
                ENGINE.log("pairing", f"New device paired: {str(body.get('name', 'phone'))[:40]}")
                return self._json({"token": result})
            return self._json({"error": result}, 403)
        if not self._authorized():
            return None
        try:
            if self.path == "/api/sensor":
                out = ENGINE.sensor(body)
            elif self.path == "/api/ack":
                out = ENGINE.ack(int(body["alert"]), str(body.get("by", "Staff")))
            elif self.path == "/api/resolve":
                out = ENGINE.resolve(int(body["alert"]), str(body.get("outcome", "Resolved")))
            elif self.path == "/api/clock":
                ENGINE.set_time(str(body["time"]), float(body["speed"]) if "speed" in body else None)
                out = {"ok": True}
            elif self.path == "/api/frame":
                out = _frame(body)
            elif self.path == "/api/camera/config":
                out = _camera_config(body)
            elif self.path == "/api/scenario":
                out = ENGINE.run_scenario(str(body.get("name")))
            elif self.path == "/api/record":
                out = ENGINE.confirm_record(int(body["alert"]), str(body.get("affect", "")), str(body.get("intervention", "")),
                                            body.get("nondrug_alt") or None, str(body.get("note", "")), str(body.get("by", "Staff")))
            elif self.path == "/api/bench/run":
                if not PAIRING.is_local(self.client_address[0]):
                    return self._json({"error": "benchmarks can only be started on the laptop"}, 403)
                out = _bench_run(body)
            elif self.path == "/api/backup":
                out = ENGINE.request_backup(int(body["alert"]), str(body.get("by", "Staff")))
            elif self.path == "/api/settings":
                if not PAIRING.is_local(self.client_address[0]):
                    return self._json({"error": "settings can only be changed on the nurse-station laptop"}, 403)
                out = ENGINE.apply_settings(body, SETTINGS_FILE)
            else:
                return self._json({"error": "not found"}, 404)
        except (KeyError, ValueError) as exc:
            return self._json({"error": f"bad request: {exc}"}, 400)
        return self._json(out)

    def _json(self, data: object, status: int = 200) -> None:
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


BENCH_KEYS = ("label", "pte", "pte_mb", "load_rss_mb", "calls", "per_s", "p50_ms", "p95_ms", "p99_ms",
              "watts_running", "watts_idle", "watts_above_idle", "mj_per_frame", "mj_per_check", "output_check")


def _bench_runs(limit: int = 12) -> dict[str, object]:
    """Benchmark results written by nightwatch/bench/benchmark.py (newest first), without local file paths."""
    runs = []
    for path in sorted((HERE.parent / "logs" / "bench").glob("*.json"), reverse=True)[:limit]:
        try:
            d = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        host = d.get("host", {})
        runs.append({"timestamp": d.get("timestamp"), "kind": d.get("kind"), "inputs": d.get("inputs"),
                     "rate": d.get("requested_rate_per_s"), "power_label": d.get("power_label"),
                     "on_ac": d.get("power_on_ac"),
                     "host": {k: host.get(k) for k in ("system", "machine", "executorch")},
                     "results": [{k: r.get(k) for k in BENCH_KEYS if k in r} for r in d.get("results", [])],
                     "notes": d.get("notes", [])})
    return {"runs": runs}


SETTINGS_FILE = HERE.parent / "data" / "facility.local.json"   # git-ignored
STARTED = time.time()
LAN = {"on": False, "port": 8000}


def _lan_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))   # no packet is sent; picks the outgoing interface
            return s.getsockname()[0]
    except OSError:
        return None


def _health(local: bool) -> dict[str, object]:
    """What's running: for the home page. The PIN and phone address only go to the laptop itself."""
    with ENGINE.lock:
        out = _health_unlocked()
    if local:
        ip = _lan_ip() if LAN["on"] else None
        out["phones"] = {"pin": PAIRING.pin, "paired": PAIRING.devices,
                         "url": f"http://{ip}:{LAN['port']}/staff/" if ip else None}
    return out


def _health_unlocked() -> dict[str, object]:
    return {
        "uptime_s": round(time.time() - STARTED),
        "pattern_model": {"name": ENGINE.scorer.name, "device": ENGINE.scorer.device},  # type: ignore[attr-defined]
        "camera_model": {"name": DETECTOR.name, "device": DETECTOR.device} if DETECTOR else None,  # type: ignore[attr-defined]
        "cameras": [{"id": c["id"], "label": c["label"], "enabled": c["enabled"], "schedule": c["schedule"],
                     "live": time.time() - c["last_frame"] < 3} for c in ENGINE.cameras.values()],
        "lan": LAN["on"], "facility": ENGINE.facility, "settings_file": ENGINE.facility_path.name,
        "tests": "python -m pytest -q tests",
    }


BENCH_JOB: dict[str, object] = {"running": False, "kind": None, "started": None, "log": "", "error": None}


def _bench_pairs(kind: str) -> list[str]:
    """NPU (QNN) and CPU (XNNPACK) builds of one model, whichever exist on this laptop."""
    models = HERE.parent / "models"
    if kind == "detector":
        npu = next((p for p in ("person_ssdlite_qnn_int8.pte", "person_ssdlite_qnn.pte") if (models / p).exists()), None)
        cpu = "person_ssdlite_xnnpack.pte"
    else:
        npu = "normal_pattern_qnn.pte" if (models / "normal_pattern_qnn.pte").exists() else None
        cpu = "normal_pattern_xnnpack.pte"
    pairs = [f"models/{npu}:NPU"] if npu else []
    if (models / cpu).exists():
        pairs.append(f"models/{cpu}:CPU")
    return pairs


def _bench_run(body: dict[str, object]) -> dict[str, object]:
    """Start a short benchmark in the background (laptop only). Results land in /api/bench."""
    import subprocess

    kind = "detector" if body.get("kind") == "detector" else "pattern"
    seconds = int(min(max(float(body.get("seconds", 10)), 3), 60))  # type: ignore[arg-type]
    pairs = _bench_pairs(kind)
    if not pairs:
        return {"error": f"no {kind} model files found in models/"}
    cmd = [sys.executable, str(HERE / "bench" / "benchmark.py"), "--kind", kind, "--seconds", str(seconds), "--rate", "max"]
    for p in pairs:
        cmd += ["--pte", p]
    with BENCH_LOCK:
        if BENCH_JOB["running"]:
            return {"error": "a benchmark is already running"}
        BENCH_JOB.update(running=True, kind=kind, started=time.strftime("%H:%M:%S"), log="", error=None, cmd=" ".join(cmd[1:]))
    ENGINE.log("bench", f"Benchmark started: {kind}, {seconds} s per backend ({', '.join(p.split(':')[1] for p in pairs)})")

    def work() -> None:
        try:
            done = subprocess.run(cmd, cwd=HERE.parent, capture_output=True, text=True, timeout=seconds * 4 + 240)
            BENCH_JOB["log"] = (done.stdout or "")[-4000:]
            if done.returncode:
                BENCH_JOB["error"] = (done.stderr or "benchmark failed")[-1500:]
        except Exception as exc:  # noqa: BLE001
            BENCH_JOB["error"] = repr(exc)
        finally:
            BENCH_JOB["running"] = False
            ENGINE.log("bench", f"Benchmark finished: {kind}" + (" (error)" if BENCH_JOB["error"] else ""))

    threading.Thread(target=work, daemon=True, name="bench").start()
    return {"ok": True, "pairs": pairs}


def _tracker(cam: str) -> Tracker:
    if cam not in TRACKERS:
        TRACKERS[cam] = Tracker()
    return TRACKERS[cam]


def _frame(body: dict[str, object]) -> dict[str, object]:
    """Analyse one camera frame in memory. It is never written to disk or sent anywhere."""
    if DETECTOR is None:
        return {"error": "no camera model loaded: start the server with --camera-model"}
    cam = str(body.get("camera", "hall12"))
    active, why = ENGINE.camera_active(cam)
    if not active:
        # Camera is off (or outside its schedule): the frame is dropped without being decoded or analysed.
        return {"paused": True, "reason": why, "tracks": [], "crossings": [], "people": 0}
    jpeg = base64.b64decode(str(body["jpeg"]).split(",")[-1])
    with DETECT_LOCK:
        boxes, ms = DETECTOR.detect(jpeg)  # type: ignore[attr-defined]
    del jpeg
    roi = body.get("roi")
    if roi:
        # The page sent a zoomed-in crop around the doorway: map boxes back to full-frame coordinates,
        # which is where the doorway line lives.
        x0, y0, size = (float(v) for v in roi)  # type: ignore[union-attr]
        for b in boxes:
            b["x1"], b["x2"] = x0 + b["x1"] * size, x0 + b["x2"] * size
            b["y1"], b["y2"] = y0 + b["y1"] * size, y0 + b["y2"] * size
    with TRACK_LOCK:
        tracker = _tracker(cam)
        crossings = tracker.update(boxes)
        tracks, people, has_door = tracker.view(), tracker.people, tracker.doorway is not None
    ENGINE.camera(cam, people, ms, crossings, has_door)
    with ENGINE.lock:
        if cam in ENGINE.cameras:
            # Positions only (no pixels), so the dashboard can draw a privacy-safe "radar" of the doorway.
            ENGINE.cameras[cam]["tracks"] = [{k: t[k] for k in ("id", "x1", "y1", "x2", "y2", "side", "confirmed")}
                                             | {"trail": t["trail"][-8:]} for t in tracks]
    return {"tracks": tracks, "crossings": crossings, "people": people, "ms": round(ms, 1),
            "model": DETECTOR.name, "device": DETECTOR.device}  # type: ignore[attr-defined]


def _camera_config(body: dict[str, object]) -> dict[str, object]:
    """Set the doorway line (line=null clears it), and/or turn analysis on/off or night-only."""
    cam = str(body.get("camera", "hall12"))
    if "enabled" in body or "schedule" in body:
        out = ENGINE.set_camera(cam, bool(body["enabled"]) if "enabled" in body else None,
                                str(body["schedule"]) if "schedule" in body else None, str(body.get("by", "staff")))
        if out.get("error") or "line" not in body:
            with TRACK_LOCK:
                if not ENGINE.camera_active(cam)[0] and cam in TRACKERS:
                    TRACKERS[cam].tracks = []
            return out
    line = body.get("line")
    inside = int(body.get("inside", 1))  # type: ignore[arg-type]
    with TRACK_LOCK:
        _tracker(cam).set_doorway(list(line) if line else None, inside)  # type: ignore[arg-type]
    with ENGINE.lock:
        if cam in ENGINE.cameras:
            ENGINE.cameras[cam]["doorway"] = {"line": line, "inside": inside} if line else None
    return {"ok": True}


def _restore_state(path: Path, fresh: bool) -> None:
    """Restore tonight's saved alerts/cameras/clock after a restart, and redraw saved doorway lines."""
    if fresh or not path.exists():
        print("State: clean night" + (" (--fresh)" if fresh else ""))
        return
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        print(f"State: {path.name} unreadable ({exc!r}), starting a clean night")
        return
    ok, why = ENGINE.restore(data)
    print(f"State: {'restored' if ok else 'not restored'} from {path.name} ({why})")
    if not ok:
        return
    with TRACK_LOCK:
        for cid, cam in ENGINE.snapshot()["cameras"].items():  # type: ignore[union-attr]
            if cam.get("doorway"):
                _tracker(cid).set_doorway(list(cam["doorway"]["line"]), int(cam["doorway"].get("inside", 1)))


def main() -> None:
    global ENGINE, DETECTOR, PAIRING
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", type=Path, help=".pte normal-pattern model (omit = rule fallback)")
    p.add_argument("--device", default="CPU", help="label for the dashboard: NPU or CPU")
    p.add_argument("--facility", type=Path, default=HERE / "demo" / "facility.json")
    p.add_argument("--l1-timeout", type=float, default=45, help="seconds a level-1 alert waits before level 2")
    p.add_argument("--ack-timeout", type=float, default=25, help="seconds a level-2/3 alert waits before escalating")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--lan", action="store_true", help="listen on the local network so staff phones can connect")
    p.add_argument("--camera-model", type=Path, help="person detector .pte (models/person_ssdlite_*.pte)")
    p.add_argument("--camera-device", default="CPU", help="label for the dashboard: NPU or CPU")
    p.add_argument("--pin", help="fixed 6-digit pairing PIN for staff phones (default: random each start)")
    p.add_argument("--unpair-all", action="store_true", help="forget every paired phone")
    p.add_argument("--fresh", action="store_true", help="start a clean night (don't restore logs/night_state.json)")
    p.add_argument("--state", type=Path, default=STATE_FILE, help="where tonight's state is saved")
    args = p.parse_args()

    facility = args.facility
    if facility == HERE / "demo" / "facility.json" and SETTINGS_FILE.exists():
        facility = SETTINGS_FILE   # settings edited on this laptop win over the demo file
    ENGINE = Engine(facility, build(args.model, args.device), args.l1_timeout, args.ack_timeout)
    LAN.update(on=args.lan, port=args.port)
    PAIRING = Pairing(HERE.parent / "logs" / "paired_devices.json", args.pin)
    if args.unpair_all:
        PAIRING.unpair_all()
    _restore_state(args.state, args.fresh)
    ENGINE.start_autosave(args.state)

    def loop() -> None:
        while True:
            try:
                ENGINE.tick()
            except Exception as exc:  # noqa: BLE001 - the watch loop must never stop
                print(f"[tick] error: {exc!r}")
            time.sleep(1)

    if args.camera_model:
        from vision.detector import PersonDetector

        # Low threshold here on purpose: the tracker needs 0.5 to start following someone but
        # keeps following down to 0.3, so a half-hidden person isn't dropped.
        DETECTOR = PersonDetector(args.camera_model, args.camera_model.parent / "person_ssdlite_anchors.pt",
                                  args.camera_device, threshold=0.3)
        print(f"Camera model: {DETECTOR.name} on {DETECTOR.device}")
    threading.Thread(target=loop, daemon=True, name="tick").start()
    host = "0.0.0.0" if args.lan else "127.0.0.1"
    print(f"Scorer: {ENGINE.scorer.name} on {ENGINE.scorer.device}")  # type: ignore[attr-defined]
    print(f"Dashboard http://localhost:{args.port}/dashboard/   Staff http://localhost:{args.port}/staff/   "
          f"Simulator http://localhost:{args.port}/sim/   Camera http://localhost:{args.port}/camera/")
    if args.lan:
        print("LAN mode: staff phones on this network can open /staff/ using this computer's IP address.")
        print(f"Phone pairing PIN: {PAIRING.pin}   ({PAIRING.devices} phone(s) already paired)")
    ThreadingHTTPServer((host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
