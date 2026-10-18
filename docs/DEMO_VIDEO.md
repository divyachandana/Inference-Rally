# NightWatch: demo video script (≤ 5 min)

Order: day visits → normal night → live hallway-camera walk-out at 02:08 → elopement escalating unanswered →
same scenario answered on the phone → privacy: camera off → Wi-Fi off → morning shift report.
Target about 4:50. The presenter page (`/sim/`) has the same beats as a step-by-step guide.

## Setup before recording

- Snapdragon X Elite laptop with a webcam. Run the health check, then start the server with both models:
  ```bash
  python nightwatch/check.py
  python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --device CPU \
    --camera-model models/person_ssdlite_xnnpack.pte --camera-device CPU \
    --l1-timeout 20 --ack-timeout 15 --lan
  ```
  Use the `_qnn.pte` files with `--device NPU` / `--camera-device NPU` **only if they have actually been
  compiled and run on the NPU**. The dashboard shows the `--device` / `--camera-device` labels, which are just
  what you typed: make sure they match the `.pte` you loaded (`_qnn` ↔ NPU, `_xnnpack` ↔ CPU), and that the
  voiceover says the same.
- **Camera page (`/camera/`):** choose *Hallway camera outside room 12*, **Start camera**, keep the privacy
  view on. Click two points to **draw the doorway line** and set which side is the room. Rehearse the
  walk-out a few times: feet must cross the line going out.
- **Test the camera on a real person before recording.** If it doesn't fire reliably, use the presenter
  scenario **Camera: R-07 walks out** for shot 5. It is tagged SIMULATED on the radar; leave that tag in frame
  and say so in the voiceover.
- **Screen layout for every shot:** nurse-station dashboard (`/dashboard/`) on the left two-thirds; the staff
  phone on the right third. Best: a real phone on the same Wi-Fi opening `http://<laptop-ip>:8000/staff/`,
  filmed or mirrored. Fallback: a phone-sized browser window on `/staff/`. For shot 5, show the camera page
  (privacy view on) as a small window, or cut to it briefly. The presenter page is shown only to start a beat.
- On the phone, tap **Start shift** first so sound and vibration work. Record system audio.
- Lower-third captions are in *italics*. Keep them on screen 3–4 seconds.

## Shot list

| # | Time | On screen | Voiceover | Caption |
|---|---|---|---|---|
| 1 | 0:00–0:15 | Title card: "NightWatch: on-device night supervision for memory care". Then the dashboard, calm. | "People with dementia sometimes leave their room at night, when one worker may be covering a whole wing. NightWatch notices, and keeps escalating until a person responds. Everything runs on this laptop." | *Snapdragon X Elite · ExecuTorch* |
| 2 | 0:15–0:30 | Zoom on the dashboard header (models and devices) and the **Camera radar · positions only** card. | "Two models run here through ExecuTorch: a person detector for the hallway camera, and a small model that knows what's normal for each resident. The nurse station sees positions, never video." | *Detector [CPU/NPU] · [__ ms/frame]* |
| 3 | 0:30–0:50 | Presenter → *Day visits*. Doors open and close; visits logged. Phone quiet. | "Two in the afternoon. Visitors come and go. Doors are logged as visits. No alarms." | *Day: doors logged, no alarms* |
| 4 | 0:50–1:10 | Presenter → *Normal night* (R-15 ensuite trip). R-15 out of bed, back in bed. Phone quiet. | "Three in the morning. A bathroom trip inside the room. Nothing fires: the care team only cares when someone leaves the room." | *Bathroom trip in the room: no alert* |
| 5 | 1:10–2:00 | Presenter → **Reset**, clock **02:08**. Camera page with the doorway line. A teammate walks out across the line. Radar: a track crosses the line. Dashboard: "R-07 left their room at 02:08". Phone buzzes. Teammate steps back in: the heads-up clears. | "Two-oh-eight. This webcam stands in for the hallway camera outside room 12, and this line is the doorway. Someone steps out across it: R-07 has left their room. A quiet heads-up goes to the night phone. Someone walking along the hallway wouldn't count, and stepping back in clears it. Frames are analysed in memory and dropped: nothing is recorded or sent." | *Live: person detected on the device* (or *SIMULATED camera data* on the fallback) |
| 6 | 2:00–2:50 | Presenter → *Elopement, unanswered*. Heads-up → front door opens, urgent → countdown runs out → **full-screen level-3 takeover** on the dashboard, all phones, supervisor, "Emergency services would be called now (simulated)". Don't touch the phone. | "Now say nobody answers, because the one worker is with someone else. R-07 reaches the front door: urgent. Still no answer, so it climbs: emergency, every phone, the on-call supervisor, then emergency services through the facility's own contact chain. In this demo that last step is simulated; it never dials anyone." | *No answer → it keeps escalating* |
| 7 | 2:50–3:30 | Presenter → *Answered on the phone*. Tap **I'm going** (show the finger). Escalation stops. Tap **Found safe**. Dashboard: closed with severity badge and draft care record. | "Same night, but this time the worker answers. 'I'm going.' The escalation stops. 'Found safe' closes it, with the care team's own severity badge and a draft care record in their format." | *Answered → escalation stops* |
| 8 | 3:30–4:00 | Presenter or dashboard → turn the hallway camera **off**. Camera page: webcam released (show the webcam light going off if visible). Radar card shows "Camera off"; log line shows who switched it. Then show the **night only** option. Turn cameras back on. | "Families and staff decide when it watches. Night only, or off. Off means physically off: the webcam is released, frames are dropped unanalysed, and every switch is logged with who did it." | *Camera off: nothing analysed* |
| 9 | 4:00–4:25 | Turn Wi-Fi off on the laptop (show the OS toggle). Dashboard shows **Offline · still protecting**. Run the elopement again or walk past the webcam. Alert still appears on the dashboard. | "Now Wi-Fi is off. It keeps protecting: both models, the ladder and the dashboard all run on the device." | *Wi-Fi off: still protecting* |
| 10 | 4:25–4:50 | Open `/report/`: the night shift handover. Scroll: totals, median response time, severity 1/2/3, alerts by resident, timeline, draft care records, camera privacy switches. End card: repo URL, team names, "Not a medical device. Supports staff; does not replace them." | "And in the morning, one report for the handover: every alert, how fast someone responded, severity, and draft care records ready for staff to confirm. NightWatch. It notices early, and keeps going when nobody answers." | — |

**Shot 9 note:** with Wi-Fi off, a real phone can't reach the laptop unless they share a local hotspot. Show
the alert on the dashboard; don't imply the phone received it unless it did.

## What must be true in the video

- Residents are synthetic (`nightwatch/demo/facility.json`). Nothing from `data/` appears on screen.
- The person on camera is a teammate who agreed to be filmed; privacy view stays on.
- Simulated camera data, if used, stays visibly tagged SIMULATED and is said out loud.
- The emergency step is labelled simulated; we never claim it calls 911.
- The device in the header matches what the voiceover says. No NPU claim unless it ran on the NPU.

## Placeholders to fill

- Shot 2 caption: `[CPU/NPU]`, `[__ ms/frame]` (read from the dashboard during the take)
- Camera tested on a real person: yes/no (shot 5 live vs SIMULATED fallback)
- End card: team names `[Name] ×4`
- Shot 9: phone on a local hotspot or dashboard only
