# Inference Rally

> On-device AI models race taxis through a 3D maze. Every turn is a decision; every second is compute.

ExecuTorch Hackathon — Compute Track (Copilot+ PC, Snapdragon X Elite).
Each racer is the same (or a different) model on a different compute unit — **NPU vs GPU vs CPU**.
At every junction the model is asked *left, right or straight?* and its car **waits while it thinks**,
so faster on-device inference visibly wins.

See **[docs/PLAN.md](docs/PLAN.md)** for the plan and architecture, and
**[docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md)** for coding rules.

## Demo video

[![Inference Rally demo video: click to watch on YouTube](https://img.youtube.com/vi/c1g9Ugve1Pw/maxresdefault.jpg)](https://youtu.be/c1g9Ugve1Pw)

▶️ **[Watch the demo on YouTube](https://youtu.be/c1g9Ugve1Pw)**

## Screenshots

![DEMO mode (earlier build): simulated NPU vs GPU vs CPU racing through the maze, with the live map and standings](docs/images/demo-race.png)

| PLAY mode (earlier Llama-3.2-1B build) | Race results |
|---|---|
| ![PLAY mode race](docs/images/play-race.png) | ![Results screen](docs/images/results.png) |

## Two modes

| Mode | Racers | Needs |
|---|---|---|
| **DEMO** (default) | **Gemma-4-E2B on the Snapdragon NPU** (real, ExecuTorch + QNN) vs simulated GPU and CPU racers | the QNN bundle |
| **PLAY** | **DC (you, arrow keys)** vs **Gemma-4-E2B on the NPU** (real) vs a simulated GPU racer | the QNN bundle |

Switch with **G** (or the MODE button). Lineups live in `racers.yaml` (`demo`, `play`, and `sim`, which
is fully simulated and runs on any machine: `python -m inference_rally.server --profile sim`).

Only the NPU racer is a real model; the GPU/CPU racers are simulated with speeds estimated relative to
the measured NPU run (~170 ms to first token, ~13.7 tokens/s). Their HUD labels say **SIM**.

## How the NPU racer works

The game server launches `host\qnn_llm_host.exe` from the
[ExecuTorch QNN bundle](https://github.com/divyachandana/gamehub) (`qnn:` in `racers.yaml` holds the
paths) and talks to it over the named pipe `\\.\pipe\rally_gemma`. The model is loaded once (~3 s,
in the background while the title screen shows) and stays loaded across races. Each junction is a
one-shot request (`"reset": true`), streamed token by token so TTFT and tokens/sec are timed on our
side. If a host is already serving the pipe (e.g. started with the bundle's `start_host.ps1
-PipeName rally_gemma`), the game reuses it. Host output goes to `logs/qnn_host.log`.

If the NPU host can't start, its car shows "MODEL OFFLINE" and keeps going with fallback moves.

## Quick start (Windows on Snapdragon)

Needs the QAIRT SDK (`C:\Qualcomm\AIStack\QAIRT\2.46.0.260424`) and the Gemma QNN bundle with its
`.pte` and `tokenizer.json`. Adjust `qnn:` in `racers.yaml` if yours live elsewhere.

```powershell
# 1. Python game server (once) — ARM64 Python 3.12
py -3.12-arm64 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"

# 2. Frontend (once)
cd frontend; npm install; npm run build; cd ..

# 3. Run (serves the built UI)
.venv\Scripts\python -m inference_rally.server
```

Open <http://localhost:8000> and press **Enter**. For frontend work with hot reload, run
`.\scripts\dev.ps1` instead (server on :8000, Vite UI on <http://localhost:5173>).

In PLAY mode the overview map is locked until you finish — like the models, you only know where the
exit is (follow the green beam).

### Controls

| Key | Action |
|---|---|
| Enter | Start / rematch (same maze) |
| N | New random maze |
| G | Switch DEMO / PLAY |
| ← ↑ → | Drive at a junction (PLAY): left / straight / right |
| ↓ | U-turn (PLAY) |
| M | Sound on/off |
| P | Retro pixels on/off |
| 1 / 2 / 3 | Focus one racer full screen |
| 0 / Esc | Back to split screen |

## Layout

- `src/inference_rally/` – Python game server
  - `maze.py` seeded maze + A* · `race.py` race engine · `deciders.py` racers' brains: simulated, Gemma on the NPU, human
  - `qnn_host.py` launches `qnn_llm_host.exe` and speaks its named-pipe protocol
  - `prompts.py` junction prompt + reply parsing · `metrics.py` TTFT / tokens/sec timing
  - `models.py` typed config + event schema · `server.py` Starlette + Server-Sent Events
- `frontend/` – Three.js split-screen game (Vite)
  - `world/` maze, scenery, procedural pixel textures · `cars/` car model, driving, option arrows
  - `render/` split-screen viewports, overview map · `hud/` HUD, leaderboard, overlays · `audio/` chiptune synth
- `racers.yaml` – race settings, NPU host paths (`qnn:`) and racer profiles (`demo`, `play`, `sim`)
- `tests/` – pytest suite (game logic runs offline with simulated racers)
- `scripts/` – `dev.ps1` (Windows) / `dev.sh` run server + UI
- `docs/` – plan, architecture, coding standards

## Checks

```bash
ruff check . && ruff format --check . && mypy src && pytest
```
