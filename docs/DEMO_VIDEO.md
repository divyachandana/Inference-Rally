# NightWatch: demo video script (≤ 5 min)

Follows the demo script in the README: day visits → normal night → elopement escalating unanswered →
same scenario answered on the phone → Wi-Fi off. Target length about 4:30, leaving margin under 5:00.

## Setup before recording

- Snapdragon X Elite laptop, server started with the model the video claims:
  ```bash
  python nightwatch/server.py --model models/normal_pattern_qnn.pte --device NPU --l1-timeout 20 --ack-timeout 15 --lan
  ```
  (Use `normal_pattern_xnnpack.pte --device CPU` if the NPU build isn't ready, and say "CPU" in the voiceover.
  The dashboard header shows the model file and the `--device` label. That label is just what you pass on
  the command line, so make sure it matches the `.pte` you loaded: `_qnn.pte` ↔ `NPU`, `_xnnpack.pte` ↔ `CPU`.)
- **Screen layout for every shot:** dashboard (`/dashboard/`) on the left two-thirds; the staff phone on the
  right third. Best: a real phone on the same Wi-Fi opening `http://<laptop-ip>:8000/staff/`, filmed or
  mirrored. Fallback: a phone-sized browser window on `/staff/`. The simulator (`/sim/`) stays in a third
  tab, shown only when starting a scenario.
- Tap **Start shift** on the phone first so sound and vibration work. Record system audio so the alert
  sounds are heard.
- Lower-third captions are in *italics* below. Keep them on screen 3–4 seconds.

## Shot list

| # | Time | On screen | Voiceover | Caption |
|---|---|---|---|---|
| 1 | 0:00–0:20 | Title card: "NightWatch: on-device night supervision for memory care". Then the dashboard, calm, clock showing night. | "People with dementia sometimes try to leave at night, when one worker may be covering a whole wing. NightWatch notices, and keeps escalating until a person responds. Everything runs on this laptop." | *Snapdragon X Elite · ExecuTorch* |
| 2 | 0:20–0:40 | Zoom on the dashboard header chip: model name and device (NPU or CPU), latency readout. | "This is the nurse-station view. Up here: the model and the chip it's running on, and how long each check takes." | *Model on [NPU/CPU] · p50 [__ ms]* |
| 3 | 0:40–1:15 | Simulator → *Day: visitors come and go*. Dashboard: doors open and close, log fills with visits. Phone stays quiet. | "Two in the afternoon. Visitors come and go, residents walk the corridor. Doors are logged as visits. No alarms: during the day this is normal." | *Day: doors logged, no alarms* |
| 4 | 1:15–1:50 | Simulator → *Night: R-15 ensuite trip*. Dashboard: R-15 out of bed, model score rises a little, back in bed. Phone stays quiet. | "Three in the morning. This resident gets up for a short ensuite trip and goes back to bed. The model scores it as normal for them. Nothing fires." | *Night: normal trip, no alert* |
| 5 | 1:50–3:00 | Simulator → *Night: R-07 heads for the front door*. Hold on the split screen. Heads-up on the phone (show what has calmed R-07 before) → front door opens, urgent, loud alert → countdown runs out → emergency, all phones, supervisor, "Emergency services would be called now (simulated)". Do not touch the phone. | "Two-oh-eight. Resident R-07 is up, heart rate climbing, heading down the corridor. That's unusual for this time, so a quiet heads-up goes to the night phone, with what has settled them before. Now the front door opens: urgent. Nobody answers, because the one worker is busy elsewhere. So it climbs: emergency, every phone, the on-call supervisor, and then emergency services through the facility's own contact chain. In this demo that last step is simulated; it never dials anyone." | *No answer → it keeps escalating* |
| 6 | 3:00–3:50 | Same scenario again. At the heads-up or urgent alert, tap **I'm going** on the phone (show the finger). Dashboard: acknowledged, escalation stops. Tap **Found safe**. Dashboard: alert closed with severity badge and the draft care record. | "Same night, but this time the worker answers. 'I'm going.' The escalation stops. 'Found safe' closes it. The alert gets the care team's own severity badge and a draft care-record entry in their format: location as a type, never a room; affect and intervention left for staff to confirm." | *Answered → escalation stops* |
| 7 | 3:50–4:20 | Turn Wi-Fi off on the laptop (show the OS Wi-Fi toggle). Run a scenario again (or trigger the front door with key **D** in the simulator). Alert still appears on the dashboard. | "Now we turn the Wi-Fi off. It keeps working: the model, the ladder and the dashboard all run on the device." | *Wi-Fi off: still watching* |
| 8 | 4:20–4:35 | End card: repo URL, team names, "Not a medical device. Supports staff; does not replace them." | "NightWatch. It keeps going when nobody answers." | — |

## Notes for shot 7

With Wi-Fi off, a real phone on the network can't reach the laptop; show the alert on the dashboard (and on
the phone-sized browser window on the laptop if used). Don't imply the phone received it unless it did.
[Team: decide whether to show a phone tethered or on a local hotspot; if so, say "local network, no
internet".]

## What must be true in the video

- Residents are synthetic. If a name or room is on screen, it comes from `nightwatch/demo/facility.json`.
- Nothing from `data/` appears on screen.
- The emergency step is labelled simulated; we never claim it calls 911.
- The device shown in the header matches what the voiceover says.

## Placeholders to fill

- Shot 2 caption: `[NPU/CPU]`, `p50 [__ ms]` (read from the dashboard during the take)
- End card: team names `[Name] ×4`
- Shot 7: phone-on-local-network decision
