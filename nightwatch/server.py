"""NightWatch local server. Standard library only (plus ExecuTorch if a model is loaded).

    python nightwatch/server.py --model models/normal_pattern_qnn.pte --device NPU      # on the Copilot+ PC
    python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --device CPU
    python nightwatch/server.py                                                          # rule fallback
    add --lan to let staff phones on the facility Wi-Fi open /staff/ (still never leaves the building)

Pages:  /dashboard/  (nurse station)   /staff/  (night staff phone)   /sim/  (sensor simulator for demos)

API (JSON):
    GET  /api/state
    POST /api/sensor    {"type": "door", "exit": "front", "open": true}
                        {"type": "bed" | "hr" | "motion" | "location", "resident": "R-07", ...}
    POST /api/ack       {"alert": 3, "by": "Night nurse"}
    POST /api/resolve   {"alert": 3, "outcome": "Found safe, walked back"}
    POST /api/clock     {"time": "02:08", "speed": 1}
    POST /api/frame     {"camera": "hall12", "jpeg": "<base64>"}   (analysed in memory, never stored)
    POST /api/camera/config {"camera": "hall12", "line": [x1, y1, x2, y2] | null, "inside": 1 | -1}
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
from scorer import build  # noqa: E402
from vision.tracker import Tracker  # noqa: E402

ENGINE: Engine
DETECTOR: object | None = None
TRACKERS: dict[str, Tracker] = {}
TRACK_LOCK = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(HERE / "web"), **kwargs)  # type: ignore[arg-type]

    def log_message(self, fmt: str, *args: object) -> None:
        if "/api/state" not in self.path:
            super().log_message(fmt, *args)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/state":
            return self._json(ENGINE.view())
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
    jpeg = base64.b64decode(str(body["jpeg"]).split(",")[-1])
    boxes, ms = DETECTOR.detect(jpeg)  # type: ignore[attr-defined]
    del jpeg
    with TRACK_LOCK:
        tracker = _tracker(cam)
        crossings = tracker.update(boxes)
        tracks, people, has_door = tracker.view(), tracker.people, tracker.doorway is not None
    ENGINE.camera(cam, people, ms, crossings, has_door)
    return {"tracks": tracks, "crossings": crossings, "people": people, "ms": round(ms, 1),
            "model": DETECTOR.name, "device": DETECTOR.device}  # type: ignore[attr-defined]


def _camera_config(body: dict[str, object]) -> dict[str, object]:
    """Set (or clear, with line=null) the doorway line for one camera."""
    cam = str(body.get("camera", "hall12"))
    line = body.get("line")
    inside = int(body.get("inside", 1))  # type: ignore[arg-type]
    with TRACK_LOCK:
        _tracker(cam).set_doorway(list(line) if line else None, inside)  # type: ignore[arg-type]
    with ENGINE.lock:
        if cam in ENGINE.cameras:
            ENGINE.cameras[cam]["doorway"] = {"line": line, "inside": inside} if line else None
    return {"ok": True}


def main() -> None:
    global ENGINE, DETECTOR
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
    args = p.parse_args()

    ENGINE = Engine(args.facility, build(args.model, args.device), args.l1_timeout, args.ack_timeout)

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
    ThreadingHTTPServer((host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
