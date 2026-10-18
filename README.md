# NightWatch

**On-device night supervision for memory care: notices when a resident with dementia is heading
for a door at 2 am, and keeps escalating until a human responds.**
ExecuTorch Hackathon 2026, Compute track (Copilot+ PC, Snapdragon X Elite).

## The problem

People with dementia wander and try to leave ("elopement"), and the worst outcomes happen at night,
when one staff member may be covering a whole wing. Door alarms exist, but an alarm that nobody
answers doesn't help: in one Wisconsin case, a memory-care resident left through a door at 12:41 a.m.
whose alarm workers ignored, according to authorities, and was found dead outside; a jury ordered the
operator to pay about $4M
([McKnight's](https://www.mcknightsseniorliving.com/news/operator-ordered-to-pay-4-million-to-family-after-jury-finds-assisted-living-community-disregarded-safety-of-memory-care-resident/)).
See [Sources](#sources) for more cases and the numbers we cite.

## What NightWatch does

| Level | When | What happens |
|---|---|---|
| 1 Heads-up | At night, a resident is up and the model says it's unusual *for this time* | Quiet alert on the night staff phone, with what has calmed this resident before |
| 2 Urgent | An exit door or window opens at night (or a heads-up gets no response) | Loud alert, must be acknowledged |
| 3 Emergency | Still no acknowledgement, or a resident is confirmed outside | All phones alarm, on-call supervisor, then emergency services per facility policy |

- **Escalation only climbs when nobody responds.** One worker for a whole wing is often busy elsewhere; the system keeps going for them.
- **Day vs night.** During the day, door openings are logged as visits. From 21:00 to 05:00 (the night band used in care records), the same door is urgent.
- **No false alarms for normal nights.** A short ensuite trip at 3 am stays quiet; a heads-up clears itself when the resident settles back into bed.
- **Speaks the care team's language.** Every closed alert gets the team's derived severity badge (1 routine / 2 notable / 3 escalation, from the highest level reached) and a draft care-record entry in their event format: location as a type (never a room), night as a band, affect and intervention left for staff to confirm. Less paperwork for the one person on nights.
- **It never dials anyone in this build.** Contact steps are shown and logged as "(simulated)".

**Architecture diagram and data map:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Why it runs on the device

It works when the facility's internet drops at night, resident data never leaves the building,
and checks take a fraction of a millisecond, so every resident is checked every second.
The "is this normal for right now?" model runs through **ExecuTorch**: XNNPACK on the CPU, or the
Qualcomm (QNN) backend on the **Hexagon NPU**.

## The model

`nightwatch/model/train_anomaly.py`: a ~850-parameter network over 8 live features (time of day,
in/out of bed, movement, heart rate vs resting, corridor, exit zone, minutes up). It is trained to tell
real normal moments from scrambled ones, so it scores *combinations*: the corridor is normal at 2 pm and
unusual at 2 am. It needs no labeled incidents, which matters because real elopement data is rare.

| Moment | Unusual score |
|---|---|
| 2:12 am, up 12 min, at an exit, HR +30 | 1.00 |
| 2:12 am, in the corridor, HR +15 | 1.00 |
| 3:00 am, short ensuite trip | 0.30 |
| 2:00 pm, walking the corridor | 0.07 |

Alerts need a score of at least 0.9 sustained for 5 seconds. **Honest note:** in this build "normal"
comes from *simulated* days. In a facility it would be learned from each resident's own first weeks of data.

## Run it

**Demo in one command** (starts the server with the best available models, NPU if built, and opens the screens):
`powershell -ExecutionPolicy Bypass -File demo.ps1` on the Snapdragon laptop, or `./demo.sh` on macOS/Linux.

Fastest path on any machine: install, then let the health check tell you what works and print the start command.

```bash
pip install -r requirements.txt        # Windows on ARM: powershell -ExecutionPolicy Bypass -File setup_windows.ps1
python nightwatch/check.py             # add --npu once the QNN models are in models/
python -m pytest -q tests              # 13 tests: escalation rules, camera confirmation, box decoding
```

Python 3.10+. The server is standard library only; loading a model needs `torch` and `executorch`.

```bash
python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --device CPU --l1-timeout 20 --ack-timeout 15
```

Open three tabs: <http://localhost:8000/dashboard/> (nurse station), <http://localhost:8000/staff/> (night
staff phone), <http://localhost:8000/sim/> (sensor simulator). Add `--lan` so a real phone on the same Wi-Fi
can open `/staff/` at this computer's IP.

Retrain / re-export:

```bash
pip install torch executorch
python nightwatch/model/train_anomaly.py
cd nightwatch/model && python export.py --backend xnnpack
```

NPU (Snapdragon X Elite): the QNN compile needs an x86_64 host with the Qualcomm AI Engine Direct SDK and
ExecuTorch's Qualcomm backend (not a Mac, not natively on Windows on ARM):

```bash
cd nightwatch/model && python export.py --backend qnn
python nightwatch/server.py --model models/normal_pattern_qnn.pte --device NPU
```

If a model fails to load, the server says so and keeps watching with a rule fallback; the dashboard always
shows which model and device are live.

## Hallway camera (person detection on the device)

The strongest signal that someone left their room at night is *seeing* it. `/camera/` opens a webcam in the
browser and sends frames to the local server, where a person detector (torchvision SSDlite320-MobileNetV3,
COCO weights) runs through **ExecuTorch**: about 6 ms per frame on a MacBook CPU with XNNPACK, NPU via QNN.
Frames are analysed in memory and dropped; nothing is recorded or sent anywhere, and the page shows a blurred
view by default.

**Precision:** a tracker (`nightwatch/vision/tracker.py`) gives each person a stable id across frames, smooths
their box, needs 0.5 confidence to start following someone but keeps them down to 0.3 (half-hidden people aren't
dropped), and the whole frame is letterboxed in (nothing cut off at the edges). On the camera page you click two
points to **draw the doorway line** and flip which side is the room; then only someone's *feet crossing the line
going out* counts, so a person walking along the hallway or staff passing by don't fire. Crossing back in closes
the heads-up. With no line drawn, three frames in a row with a person counts. At night, the hallway camera outside room 12
means R-07 left their room (heads-up); the front-entrance camera means someone is at the exit (urgent).

```bash
python nightwatch/vision/export_detector.py --backend xnnpack     # needs torchvision; writes the .pte + anchors
python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --camera-model models/person_ssdlite_xnnpack.pte
```

**Image quality and precision, continued:** the tracker predicts each person's motion (fast walkers and short
occlusions keep their id) and only counts a crossing once the feet stay on the new side for 2 frames (no flicker
when someone stands on the line). With a doorway drawn, the page sends a **zoomed crop around the door** to the
detector, so people there appear larger, and **night boost** auto-stretches brightness/contrast of dark frames
(capped at ×4 to avoid amplifying sensor noise) before detection.

**Camera on/off and night only:** each camera can be turned off or set to watch only at night (21:00-05:00),
from the camera page or the nurse station. Off means off: the server drops frames without decoding them and the
camera page releases the webcam (its light goes off). Every switch is logged with who did it.

**8-bit model:** `export_detector.py --int8 --calib data/calib` quantizes the detector (PT2E). 3.9 MB instead of
13.8 MB, same boxes on our checks (box overlap 0.95-0.99), and int8 is the format the Hexagon NPU is built for
(`--backend qnn --int8`). On a MacBook CPU it's only slightly faster (5.3 vs 5.7 ms). Calibrate on a few dozen
real frames from the demo camera (kept in git-ignored `data/calib`, deleted afterwards) for best accuracy.

The exported `.pte` and anchors are committed, so the laptop only needs `torch` + `executorch` + `pillow`
(no torchvision). For the NPU: `python nightwatch/vision/export_detector.py --backend qnn` on an x86_64 host with
the QNN SDK, then `--camera-model models/person_ssdlite_qnn.pte --camera-device NPU`.

## Phone pairing (security)

With `--lan`, staff phones reach the laptop over the facility Wi-Fi, so NightWatch makes sure only staff devices
can see or answer alerts. The laptop itself is trusted; any other device must enter the **6-digit PIN shown on
the nurse-station dashboard** (also printed at startup) once. It then gets a random token that it sends with every
request; only a hash is stored (`logs/paired_devices.json`, git-ignored). Wrong PINs lock a device out for 60 s
after 5 tries. Pages hold no data; every `/api/` call from another device without a valid token gets `401`.
`--pin 123456` fixes the PIN for a demo; `--unpair-all` forgets every phone.

## Sensors

| Sensor | Demo | Real |
|---|---|---|
| Door / window contact | `/sim/` (key **D** = front door) | Arduino + reed switch: `hardware/door_sensor/door_sensor.ino` → `python nightwatch/bridges/door_serial.py --port COM5` |
| Heart rate | `/sim/` slider, or `hr_bridge.py --simulate` | A watch broadcasting the standard Bluetooth heart-rate service → `python nightwatch/bridges/hr_bridge.py --ble "Charge 6" --resident R-07` |
| Bed / location | `/sim/` | Bed pressure mat, room/corridor beacons |

Everything posts to `POST /api/sensor` (see `nightwatch/server.py`).

## Demo script (≤ 5 min)

1. **Day (14:00).** Simulator → *Day: visitors come and go*. Doors open, visits are logged, no alarms.
2. **Normal night (03:00).** *Night: R-15 ensuite trip*. Resident gets up, goes back to bed. Nothing fires.
3. **The real thing (02:08).** *Night: R-07 heads for the front door*. Heads-up on the phone → front door opens → urgent → nobody answers → emergency, supervisor, then "emergency services would be called now".
4. Run 3 again and tap **I'm going** on the phone: escalation stops; **Found safe** closes it.
5. Turn Wi-Fi off. It keeps working.

## Data and privacy

- Residents in the demo are **synthetic** (`nightwatch/demo/facility.json`); every number there is invented.
- The design was informed by a memory-care professional on our team and de-identified care records.
  Those records stay in `data/` (git-ignored) and are never committed. `tools/build_profile.py` turns them
  into aggregate-only profiles, locally.

## Sources

Allegations in lawsuits are allegations, not findings. Check amounts against court records before quoting.

- $110M jury verdict, Sacramento: a 100-year-old resident with Alzheimer's died of hypothermia after leaving an assisted-living facility ([Expert Institute](https://www.expertinstitute.com/resources/insights/110m-verdict-assisted-living-elopement/), [Nursing Home Abuse Center](https://www.nursinghomeabusecenter.com/blog/110-million-wrongful-death-lawsuit-against-assisted-living-facility/)). Some reports say $100M.
- About $4M jury verdict, Wisconsin: door alarm ignored at 12:41 a.m. ([McKnight's Senior Living](https://www.mcknightsseniorliving.com/news/operator-ordered-to-pay-4-million-to-family-after-jury-finds-assisted-living-community-disregarded-safety-of-memory-care-resident/)).
- Oregon: family sued a memory-care center and the state after a resident wandered away and froze to death ([OPB](https://www.opb.org/article/2024/04/17/senior-elder-memory-dementia-care-sandy-oregon-ki-soon-hyun-mt-hood/), [KGW](https://www.kgw.com/article/news/local/family-sues-memory-care-center-resident-dementia-escape-death-oregon/283-b6849400-d1f2-42e0-b988-52a0bc36dbfb)).
- Window fall: a dementia patient died after jumping from a second-story window; the state ordered the memory-care unit moved to the first floor ([source](https://nursing-home-neglect.com/dementia-patient-dies-after-jumping-out-of-second-story-window/)).
- Wandering affects roughly 20-30% of nursing-home residents with dementia, depending on study and setting ([Caring for the Ages](https://www.caringfortheages.com/article/S1526-4114(22)00409-7/fulltext), [US News](https://health.usnews.com/senior-care/wandering-and-elopement-in-nursing-homes)).

Not a medical device. It supports staff; it does not replace them.

---

`archive/struggle-detector/` holds the team's earlier prototype (website frustration detector).

**On screen:** `/perf/` shows the live time per check and per frame, plus the latest benchmark runs (NPU vs CPU speedup, energy, output match) as soon as the team runs `nightwatch/bench/benchmark.py`.

## Benchmark

`nightwatch/bench/benchmark.py` compares each model on the Hexagon NPU (QNN) and the CPU (XNNPACK): p50/p95/p99
latency, throughput, whole-laptop power above an idle baseline (battery gauge, so run unplugged), energy per
frame/check, memory, and a check that both backends give the same outputs on the same inputs. It detects the
model from the `.pte`. On the Snapdragon X Elite laptop, from the repo root:

```bash
python nightwatch/bench/benchmark.py --pte models/person_ssdlite_qnn.pte:NPU --pte models/person_ssdlite_xnnpack.pte:CPU --rate max
python nightwatch/bench/benchmark.py --pte models/person_ssdlite_qnn.pte:NPU --pte models/person_ssdlite_xnnpack.pte:CPU --rate 5 --cameras 2
python nightwatch/bench/benchmark.py --pte models/normal_pattern_qnn.pte:NPU --pte models/normal_pattern_xnnpack.pte:CPU --rate max
```

The person detector is the main NPU workload (`--rate 5` = 5 frames/s per camera, what `/camera/` sends). Results
go to `logs/bench/`; setup, caveats and the results tables are in [nightwatch/bench/README.md](nightwatch/bench/README.md).
