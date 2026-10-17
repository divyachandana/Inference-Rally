# NightWatch: HackerSquad submission text

Copy each block into the matching form field. `[Brackets]` are placeholders the team must fill.

---

## Title

NightWatch

## Tagline (one line)

On-device night supervision for memory care: it notices when a resident with dementia heads for a door at
2 a.m., and keeps escalating until a human responds.

## Track

Compute (Copilot+ PC, Snapdragon X Elite)

## Description

People with dementia sometimes try to leave their care home ("elopement"), and the worst outcomes happen at
night, when one staff member may be covering a whole wing. Door alarms exist, but an alarm nobody answers
doesn't help. In one Wisconsin case, according to authorities, a memory-care resident left through a door at
12:41 a.m. whose alarm workers ignored, and was found dead outside; a jury ordered the operator to pay about
$4M.

NightWatch runs entirely on a Snapdragon X Elite laptop at the facility. It reads door and window contacts,
a heart-rate watch and bed and location sensors, and every second asks a tiny ExecuTorch model: "is this
normal for this resident right now?" It then runs an escalation ladder:

1. **Heads-up**: a resident is up at night and it's unusual for this time. Quiet alert on the night staff
   phone, with what has calmed this resident before.
2. **Urgent**: an exit door or window opens at night, or the heads-up got no response. Loud alert that must
   be acknowledged.
3. **Emergency**: still no acknowledgement, or the resident is confirmed outside. All phones, the on-call
   supervisor, then emergency services through the facility's own contact chain.

It only climbs when nobody responds. During the day, door openings are logged as visits; from 21:00 to 05:00
the same door is urgent. A short ensuite trip at 3 a.m. stays quiet. When an alert closes, NightWatch gives
it the care team's own severity badge (1 routine / 2 notable / 3 escalation) and drafts a care-record entry
in their format, with affect and intervention left for staff to confirm.

The design came from a memory-care professional on our team. In their experience, one night worker can be
covering around 40 residents, and residents get out even through pinned doors.

NightWatch supports staff; it does not replace them. It is not a medical device.

## How we used ExecuTorch

- **The model.** A ~850-parameter PyTorch network over 8 live features (time of day, in/out of bed, movement,
  heart rate vs resting, corridor, exit zone, minutes up). It's trained to tell real normal moments from
  scrambled ones, so it scores *combinations* (the corridor is normal at 2 p.m., unusual at 2 a.m.) and needs
  no labeled incidents. Code: `nightwatch/model/train_anomaly.py`.
- **Export.** `nightwatch/model/export.py` lowers it to ExecuTorch `.pte` programs for two backends:
  - **XNNPACK** on the Snapdragon CPU (`--backend xnnpack`)
  - **Qualcomm QNN** on the **Hexagon NPU** (`--backend qnn`; compiled on an x86_64 host with the Qualcomm AI
    Engine Direct SDK)
- **Runtime.** The server loads the `.pte` and scores every resident every second. The dashboard shows which
  model and device are live and the measured latency. If a model fails to load, a rule fallback keeps
  watching and the dashboard says so.
- **Why on-device.** It keeps working when facility internet drops at night; resident data never leaves the
  building; and each check is fast and cheap enough to run on every resident, every second, all night.

**Measured on the Snapdragon X Elite** (see README → Benchmark):

| Per check | CPU (XNNPACK) | NPU (QNN) |
|---|---|---|
| Latency p50 | [__ ms] | [__ ms] |
| Latency p99 | [__ ms] | [__ ms] |
| Energy | [__ mJ] | [__ mJ] |

## What's real vs simulated

| Real | Simulated |
|---|---|
| The ExecuTorch model, its export to XNNPACK and QNN, and on-device inference | "Normal" was learned from **simulated days**; in a facility it would be learned from each resident's own first weeks |
| The escalation ladder, day/night modes, acknowledgement and resolution | Residents are **synthetic** (`nightwatch/demo/facility.json`); every number there is invented |
| Staff phone page and nurse-station dashboard over the local network | The emergency contact steps: shown and logged as "(simulated)". It never dials anyone, and never auto-dials 911 |
| Works with Wi-Fi off | Sensor events in the demo come from the browser simulator (`/sim/`) |
| Bridges for a real door sensor (Arduino + reed switch) and a Bluetooth heart-rate watch | [Team: state which real sensors were used on the day, if any] |
| Severity badge and draft care record in the care team's format | |

The design was informed by de-identified care records shared by our memory-care teammate. Those records stay
off the repo (git-ignored); only aggregate profiles were built from them, locally. No real patient data is in
the code, the demo or this submission.

## Setup

Python 3.10+. The server is standard library only; loading a model needs `torch` and `executorch`.

```bash
git clone https://github.com/lucasmasen/ExecuTorch && cd ExecuTorch
pip install torch executorch
python nightwatch/model/train_anomaly.py
cd nightwatch/model && python export.py --backend xnnpack && cd ../..
python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --device CPU --l1-timeout 20 --ack-timeout 15
```

Open <http://localhost:8000/dashboard/> (nurse station), <http://localhost:8000/staff/> (staff phone) and
<http://localhost:8000/sim/> (sensor simulator). Add `--lan` to open `/staff/` from a phone on the same Wi-Fi.

NPU (Snapdragon X Elite): compile on an x86_64 host with the Qualcomm AI Engine Direct SDK and ExecuTorch's
Qualcomm backend, then run on the laptop:

```bash
cd nightwatch/model && python export.py --backend qnn && cd ../..
python nightwatch/server.py --model models/normal_pattern_qnn.pte --device NPU
```

Demo: in the simulator run *Day: visitors come and go*, then *Night: R-15 ensuite trip*, then *Night: R-07
heads for the front door* (leave the phone alone to watch it escalate; run it again and tap **I'm going**).

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

- Benchmark table: CPU/NPU latency p50 and p99, energy per check
- Real sensors used on the day (if any)
- Demo video link, slides link
- Team names and roles (×4)
