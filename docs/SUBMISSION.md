# NightWatch: HackerSquad submission text

Copy each block into the matching form field. `[Brackets]` are placeholders the team must fill.

---

## Title

NightWatch

## Tagline (one line)

On-device night supervision for memory care: it sees when a resident with dementia leaves their room at
night, and keeps escalating until a human responds.

## Track

Compute (Copilot+ PC, Snapdragon X Elite)

## Description

People with dementia sometimes try to leave their care home ("elopement"), and the worst outcomes happen at
night, when one staff member may be covering a whole wing. Door alarms exist, but an alarm nobody answers
doesn't help, and by the time the door alarm goes off it is already late. In one Wisconsin case, according to
authorities, a memory-care resident left through a door at 12:41 a.m. whose alarm workers ignored, and was
found dead outside; a jury ordered the operator to pay about $4M.

The moment the care team actually cares about is earlier: **a resident leaving their room at night.**
NightWatch runs entirely on a Snapdragon X Elite laptop at the facility. A hallway camera, door and window
contacts, a heart-rate watch and bed and location sensors feed an escalation ladder:

1. **Heads-up**: at night, a resident leaves their room (seen by the hallway camera or the location
   sensors), or the normal-pattern model says what they're doing is unusual for this hour. Quiet alert on
   the night staff phone, with what has calmed this resident before. Bathroom trips inside the room don't
   count.
2. **Urgent**: an exit door or window opens at night, a camera sees someone at the front entrance, or the
   heads-up got no response. Loud alert that must be acknowledged.
3. **Emergency**: still no acknowledgement, or the resident is confirmed outside. All phones, the on-call
   supervisor, then emergency services through the facility's own contact chain.

It only climbs when nobody responds. During the day, doors and camera sightings are logged, not alarmed.
When an alert closes, NightWatch gives it the care team's own severity badge (1 routine / 2 notable /
3 escalation) and drafts a care-record entry in their format, with affect and intervention left for staff to
confirm.

Our design rule: **fixed rules for what we know is dangerous, ML for what we have to see.** A door opening at
2 a.m. doesn't need a model; recognising a person in a hallway frame does.

The design came from a memory-care professional on our team. In their experience, one night worker can be
covering around 40 residents, and residents get out even through pinned doors.

NightWatch supports staff; it does not replace them. It is not a medical device.

## How we used ExecuTorch

Two models run on the device through ExecuTorch:

- **Person detector (the heavy, continuous workload).** torchvision SSDlite320-MobileNetV3 with COCO
  weights, exported by `nightwatch/vision/export_detector.py`. The browser page `/camera/` sends webcam
  frames to the local server, which runs the detector and keeps only the person count. Three frames in a row
  with a person confirms a sighting. About 6 ms per frame on a MacBook CPU with XNNPACK during development.
  A camera running all night is the main reason for the NPU.
- **Normal-pattern model.** A ~850-parameter network over 8 live features (time of day, in/out of bed,
  movement, heart rate vs resting, corridor, exit zone, minutes up), trained to tell real normal moments from
  scrambled ones. It scores *combinations* (the corridor is normal at 2 p.m., unusual at 2 a.m.) and needs
  no labeled incidents. `nightwatch/model/train_anomaly.py`, exported by `nightwatch/model/export.py`.
- **Backends.** Both export to **XNNPACK** for the CPU and to **Qualcomm QNN** for the **Hexagon NPU** (the
  QNN compile runs on an x86_64 host with the Qualcomm AI Engine Direct SDK). [Team: state whether the QNN
  builds were run on the NPU. As of writing they have not been.]
- **Runtime.** The dashboard shows which models and devices are live and the measured latency. If a model
  fails to load, the server says so and a rule fallback keeps watching.
- **Why on-device.** Camera frames of people with dementia must not leave the building; facility internet
  drops at night; and a detector running on every frame all night needs a low-power always-on chip.

**Measured on the Snapdragon X Elite** (see `nightwatch/bench/README.md`):

| Per inference | CPU (XNNPACK) | NPU (QNN) |
|---|---|---|
| Person detector, latency p50 | [__ ms] | [__ ms] |
| Person detector, energy | [__ mJ] | [__ mJ] |
| Normal-pattern model, latency p50 | [__ ms] | [__ ms] |
| Normal-pattern model, energy | [__ mJ] | [__ mJ] |

## Privacy

Camera frames are analysed in memory and dropped: nothing is recorded, stored or sent anywhere, and only a
person count reaches the alert logic. The camera page shows a blurred privacy view by default.

## What's real vs simulated

| Real | Simulated or not yet verified |
|---|---|
| Both ExecuTorch models, their XNNPACK and QNN export paths, on-device inference on CPU | Running on the NPU: [not yet run / run on (date)] |
| Person detector on webcam frames, privacy view, 3-frame confirmation | Detection on a real person: [verified / not yet verified] |
| The escalation ladder, day/night modes, acknowledgement and resolution | "Normal" for the small model was learned from **simulated days**; in a facility it would come from each resident's own first weeks |
| Staff phone page and nurse-station dashboard over the local network | Residents are **synthetic** (`nightwatch/demo/facility.json`); every number there is invented |
| Works with Wi-Fi off | Emergency contact steps: shown and logged as "(simulated)". It never dials anyone, and never auto-dials 911 |
| Bridges for a real door sensor (Arduino + reed switch) and a Bluetooth heart-rate watch | Other sensor events in the demo come from the browser simulator (`/sim/`). [Team: real sensors used on the day, if any] |
| Severity badge and draft care record in the care team's format | |

The design was informed by de-identified care records shared by our memory-care teammate. Those records stay
off the repo (git-ignored); only aggregate profiles were built from them, locally. No real patient data is in
the code, the demo or this submission.

## Setup

Python 3.10+. The server is standard library only; models need `torch`, `executorch` and `pillow`. The
detector `.pte` and its anchors are committed, so torchvision is only needed to re-export.

```bash
git clone https://github.com/lucasmasen/ExecuTorch && cd ExecuTorch
pip install torch executorch pillow
python nightwatch/model/train_anomaly.py
cd nightwatch/model && python export.py --backend xnnpack && cd ../..
python nightwatch/server.py --model models/normal_pattern_xnnpack.pte \
  --camera-model models/person_ssdlite_xnnpack.pte --l1-timeout 20 --ack-timeout 15
```

Open <http://localhost:8000/dashboard/> (nurse station), <http://localhost:8000/staff/> (staff phone),
<http://localhost:8000/sim/> (sensor simulator) and <http://localhost:8000/camera/> (hallway camera). Add
`--lan` to open `/staff/` from a phone on the same Wi-Fi.

NPU (Snapdragon X Elite): compile on an x86_64 host with the Qualcomm AI Engine Direct SDK and ExecuTorch's
Qualcomm backend, then run on the laptop:

```bash
cd nightwatch/model && python export.py --backend qnn && cd ../..
python nightwatch/vision/export_detector.py --backend qnn
python nightwatch/server.py --model models/normal_pattern_qnn.pte --device NPU \
  --camera-model models/person_ssdlite_qnn.pte --camera-device NPU
```

Demo: in the simulator press **Reset**, set the clock to **02:08**, start the camera on *Hallway camera
outside room 12* and walk out of a doorway in front of the webcam: the phone gets a heads-up. Then run
*Night: R-07 heads for the front door* and leave the phone alone to watch it escalate; run it again and tap
**I'm going**.

## Links

- Repo: https://github.com/lucasmasen/ExecuTorch
- Demo video: [link]
- Slides: [link]

## Team

| Name | Role |
|---|---|
| [Name] | [role] |
| [Name] | [role] |
| [Name] | [role] |
| [Name] | Memory-care professional: problem, workflow and care-record design |

## Sources for the cases we cite

Lawsuit claims are allegations; amounts are jury verdicts as reported. Full links are in the README → Sources.

- Wisconsin, about $4M jury verdict: McKnight's Senior Living.
- Sacramento: jury verdict reported at $100M+ (reported as $110M by some sources and $100M by others).
- Wandering affects roughly 20–30% of nursing-home residents with dementia, depending on study and setting.

## Placeholders to fill

- Benchmark table: detector and normal-pattern model, CPU vs NPU, latency and energy
- Whether the QNN builds were run on the NPU (and when)
- Whether detection was verified on a real person
- Real sensors used on the day (if any)
- Demo video link, slides link
- Team names and roles (×4)
