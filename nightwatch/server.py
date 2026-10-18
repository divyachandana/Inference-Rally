"""NightWatch local server. Standard library only (plus ExecuTorch if a model is loaded).

    python nightwatch/server.py --model models/normal_pattern_qnn.pte --device NPU      # on the Copilot+ PC
    python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --device CPU
    python nightwatch/server.py                                                          # rule fallback
    add --lan to let staff phones on the facility Wi-Fi open /staff/ (still never leaves the building)

Pages:  /dashboard/  (nurse station)   /staff/  (night staff phone)   /sim/  (sensor simulator for demos)

API (JSON):
    POST /api/pair      {"pin": "123456", "name": "Night nurse phone"} -> {"token"}   (other devices must pair;
                        then send header X-NightWatch-Token on every /api/ call. The laptop itself is trusted.)
    GET  /api/state
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

ENGINE: Engine
DETECTOR: object | None = None
TRACKERS: dict[str, Tracker] = {}
TRACK_LOCK = threading.Lock()
PAIRING: Pairing


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
        if self.path == "/api/state":
            view = ENGINE.view()
            if PAIRING.is_local(self.client_address[0]):
                # Only the laptop itself sees the PIN, to show it on the nurse-station screen.
                view["pairing"] = {"pin": PAIRING.pin, "devices": PAIRING.devices}
            return self._json(view)
        if self.path == "/api/report":
            return self._json(ENGINE.report())
        if self.path in ("", "/"):
            self.send_response(302)
            self.send_header("Location", "/dashboard/")
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
    args = p.parse_args()

    ENGINE = Engine(args.facility, build(args.model, args.device), args.l1_timeout, args.ack_timeout)
    PAIRING = Pairing(HERE.parent / "logs" / "paired_devices.json", args.pin)
    if args.unpair_all:
        PAIRING.unpair_all()

    def loop() -> None:
        while True:
            ENGINE.tick()
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
