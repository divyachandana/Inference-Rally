# NightWatch: demo video script (≤ 5 min)

Order: day visits → normal night → live hallway-camera moment (resident leaves their room at 02:08) →
elopement escalating unanswered → same scenario answered on the phone → Wi-Fi off. Target about 4:45.

## Setup before recording

- Snapdragon X Elite laptop with a webcam. Start the server with both models:
  ```bash
  python nightwatch/server.py --model models/normal_pattern_xnnpack.pte --device CPU \
    --camera-model models/person_ssdlite_xnnpack.pte --camera-device CPU \
    --l1-timeout 20 --ack-timeout 15 --lan
  ```
  For the NPU, use the `_qnn.pte` files with `--device NPU` / `--camera-device NPU` **only if they have
  actually been compiled and run on the NPU**. The dashboard shows the `--device` / `--camera-device` labels,
  which are just what you typed: make sure they match the `.pte` you loaded (`_qnn` ↔ NPU, `_xnnpack` ↔ CPU),
  and that the voiceover says the same.
- **Test the camera on a real person before recording.** Detection on a real person hasn't been verified
  yet. If it doesn't fire reliably, record shot 5 with the simulator (see the fallback in shot 5).
- **Screen layout for every shot:** dashboard (`/dashboard/`) on the left two-thirds; the staff phone on the
  right third. Best: a real phone on the same Wi-Fi opening `http://<laptop-ip>:8000/staff/`, filmed or
  mirrored. Fallback: a phone-sized browser window on `/staff/`. For shot 5, add the camera page
  (`/camera/`, privacy view **on**) as a small window in the dashboard area, or cut to it briefly. The
  simulator (`/sim/`) is shown only when starting a scenario or setting the clock.
- On the phone, tap **Start shift** first so sound and vibration work. Record system audio.
- Lower-third captions are in *italics*. Keep them on screen 3–4 seconds.

## Shot list

| # | Time | On screen | Voiceover | Caption |
|---|---|---|---|---|
| 1 | 0:00–0:20 | Title card: "NightWatch: on-device night supervision for memory care". Then the dashboard, calm. | "People with dementia sometimes leave their room at night, when one worker may be covering a whole wing. NightWatch notices, and keeps escalating until a person responds. Everything runs on this laptop." | *Snapdragon X Elite · ExecuTorch* |
| 2 | 0:20–0:40 | Zoom on the dashboard header: normal-pattern model and device, hallway camera chip with ms/frame. | "Two models run here through ExecuTorch: a person detector for the hallway camera, and a small model that knows what's normal for each resident at each hour." | *Detector [CPU/NPU] · [__ ms/frame]* |
| 3 | 0:40–1:05 | Simulator → *Day: visitors come and go*. Doors open and close, log fills with visits. Phone quiet. | "Two in the afternoon. Visitors come and go. Doors are logged as visits. No alarms." | *Day: doors logged, no alarms* |
| 4 | 1:05–1:30 | Simulator → *Night: R-15 ensuite trip*. R-15 out of bed, back in bed. Phone quiet. | "Three in the morning. This resident gets up for the bathroom inside their own room and goes back to bed. Nothing fires: the care team only cares when someone leaves the room." | *Bathroom trip in the room: no alert* |
| 5 | 1:30–2:20 | Simulator → **Reset**, then clock **02:08 (night)**. Camera page: *Hallway camera outside room 12*, **Start camera**, privacy view on. A teammate walks out of a doorway in front of the webcam. Dashboard: "person seen", R-07 moves to the corridor, heads-up "R-07 left their room at 02:08". Phone buzzes. | "Two-oh-eight. This webcam stands in for the hallway camera outside room 12. Someone steps out of the doorway. Three frames with a person and it's confirmed: R-07 has left their room. A quiet heads-up goes to the night phone, with what has settled them before. The view is blurred, and frames are analysed in memory and dropped: nothing is recorded or sent." | *Live: person detected on the device* |
| 6 | 2:20–3:20 | Simulator → *Night: R-07 heads for the front door*. Hold on the split screen. Heads-up → front door opens, urgent, loud → countdown runs out → emergency, all phones, supervisor, "Emergency services would be called now (simulated)". Don't touch the phone. | "Now say nobody answers, because the one worker is with someone else. R-07 reaches the front door: urgent. Still no answer, so it climbs: emergency, every phone, the on-call supervisor, then emergency services through the facility's own contact chain. In this demo that last step is simulated; it never dials anyone." | *No answer → it keeps escalating* |
| 7 | 3:20–4:05 | Same scenario again. At the alert, tap **I'm going** on the phone (show the finger). Escalation stops. Tap **Found safe**. Dashboard: closed with severity badge and the draft care record. | "Same night, but this time the worker answers. 'I'm going.' The escalation stops. 'Found safe' closes it, with the care team's own severity badge and a draft care-record entry in their format: location as a type, never a room; affect and intervention left for staff to confirm." | *Answered → escalation stops* |
| 8 | 4:05–4:30 | Turn Wi-Fi off on the laptop (show the OS toggle). Walk past the webcam again, or press **D** in the simulator for the front door. Alert still appears on the dashboard. | "Now Wi-Fi is off. It keeps working: both models, the ladder and the dashboard all run on the device." | *Wi-Fi off: still watching* |
| 9 | 4:30–4:45 | End card: repo URL, team names, "Not a medical device. Supports staff; does not replace them." | "NightWatch. It notices early, and keeps going when nobody answers." | — |

**Shot 5 fallback (if the camera isn't reliable on a real person):** skip the webcam. After Reset and 02:08,
set R-07's zone to *corridor* in the simulator's Residents panel and say "in this take the hallway signal comes from
the simulator". Don't show the camera page as if it detected someone.

**Shot 8 note:** with Wi-Fi off, a real phone can't reach the laptop unless they share a local hotspot. Show
the alert on the dashboard; don't imply the phone received it unless it did.

## What must be true in the video

- Residents are synthetic (`nightwatch/demo/facility.json`). Nothing from `data/` appears on screen.
- The person on camera is a teammate who agreed to be filmed; privacy view stays on.
- The emergency step is labelled simulated; we never claim it calls 911.
- The device in the header matches what the voiceover says. No NPU claim unless it ran on the NPU.

## Placeholders to fill

- Shot 2 caption: `[CPU/NPU]`, `[__ ms/frame]` (read from the dashboard during the take)
- Camera tested on a real person: yes/no (shot 5 live vs fallback)
- End card: team names `[Name] ×4`
- Shot 8: phone on a local hotspot or dashboard only
