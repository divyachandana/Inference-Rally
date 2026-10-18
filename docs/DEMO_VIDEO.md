# NightWatch: demo video script (≤ 5 min)

Order: normal night → live hallway-camera walk-out at 02:08 → elopement escalating unanswered, with the
emergency contacts notified → same night answered on the phone, care record in two taps → privacy: camera
off → Wi-Fi off → morning shift report and family view. Target about 4:50. The presenter page (`/sim/`) has
the same beats as a step-by-step guide.

## Setup before recording

- Snapdragon X Elite laptop with a webcam, from the repo root:
  ```bash
  python nightwatch/check.py
  ./demo.sh          # Snapdragon laptop: powershell -ExecutionPolicy Bypass -File demo.ps1 -Pin 246810
  ```
  The launcher picks the QNN (NPU) models if they're in `models/`, otherwise the committed XNNPACK (CPU) ones.
  `/home/` (System status) and the dashboard chips name the device each model is on. The voiceover must say
  the same device; no NPU claim unless the chips say NPU.
- **Staff phone:** a real phone on the same Wi-Fi opens `http://<laptop-ip>:8000/staff/` (the QR code on
  `/home/`), enters the 6-digit PIN, enters a name, and taps **Start shift** so sound and vibration work.
- **Contact phone (optional, for shot 4):** a second phone set up as the on-call supervisor in the presenter
  page's emergency contacts panel, using iMessage (sent by this Mac's Messages app) and/or ntfy push. Use
  **Send test** first. Turn **Real sending** ON (with its confirm) just before recording; it resets to OFF
  (dry run) at every server start. Only real phone numbers or topics of team members who agreed; never an emergency number (the server
  refuses them anyway). If it isn't tested, skip the second phone and show the contact list on the dashboard.
- **Camera page (`/camera/`):** *Hallway camera outside room 12*, **Start camera**, privacy view on, **Draw
  doorway**. Rehearse the walk-out: feet must cross the line going out. If it doesn't fire reliably on a real
  person, use the presenter scenario **Camera: R-07 walks out** for shot 2; it is tagged SIMULATED on the radar.
  Keep the tag in frame and say so.
- **Screen layout:** nurse station (`/dashboard/`) on the left two-thirds; the staff phone on the right third
  (filmed or mirrored). The camera page appears as a small window in shot 2; the presenter page only to start
  a beat. Record system audio. *Italic* captions stay on screen 3–4 s.

## Shot list

| # | Time | On screen | Voiceover | Caption |
|---|---|---|---|---|
| 1 | 0:00–0:30 | Title card, then the nurse station, calm. Presenter → *Normal night* (R-15 ensuite trip). R-15 out of bed, back in bed. Phone quiet. | "People with dementia sometimes leave their room at night, when one worker may be covering a whole wing. NightWatch runs on this laptop and notices. Three a.m.: a bathroom trip inside the room. Nothing fires; the care team only cares when someone leaves the room." | *Snapdragon X Elite · ExecuTorch · residents are synthetic* |
| 2 | 0:30–1:20 | Presenter → **Reset**, clock **02:08**. Camera page with the doorway line, blurred, "Frames stored: 0". A teammate walks out across the line. Radar: a track crosses from ROOM to HALLWAY. Phone buzzes: "R-07 left their room". | "Two-oh-eight. This webcam stands in for the hallway camera outside room 12. Someone steps out across the doorway: R-07 has left their room. A quiet heads-up on the night phone, with what has calmed them before. A person detector runs through ExecuTorch on this laptop; frames are analysed in memory and dropped, and the nurse station sees a dot, never video." | *Live: person detected on the device* (or *SIMULATED camera data*) |
| 3 | 1:20–2:10 | Presenter → *Elopement, unanswered*. Don't touch the phone. Heads-up → front door opens, urgent → countdown → **full-screen emergency takeover**, all phones. | "Now nobody answers, because the one worker is with someone else. R-07 reaches the front door: urgent. Still nothing, so it climbs: emergency, on every staff phone." | *No answer → it keeps escalating* |
| 4 | 2:10–2:40 | Dashboard: emergency contacts list, who has been notified. Cut to the second phone receiving the message (it starts "This is a NightWatch demo."). Emergency services row reads **simulated**. | "At the same moment, the on-call supervisor, the family and the owner are notified. Only a short alert text leaves the building, never video or health readings. Emergency services stay in the facility's chain: NightWatch never calls 911, and in this demo that step is simulated." | *Contacts notified · emergency services simulated* |
| 5 | 2:40–3:20 | Presenter → *Answered on the phone*. On the staff phone tap **I'm going** (show the finger): the climb stops. Tap **Found safe**, then the 2-tap care record. Briefly show **Need backup** and the ES language switch. | "Same night, answered. 'I'm going.' The escalation stops. 'Found safe,' and two taps record what happened, as a draft in the care team's own format. If the nurse needs a hand, 'Need backup' calls the others. The phone works in English and Spanish." | *Answered → escalation stops* |
| 6 | 3:20–3:45 | Turn the hallway camera **off** (dashboard or camera page). Webcam light goes off; radar card shows "Camera off"; log line names who switched it. Show the **night only** option, then turn it back on. | "Families and staff decide when it watches: night only, or off. Off means physically off: the webcam is released and nothing is analysed. Every switch is logged." | *Camera off: nothing analysed* |
| 7 | 3:45–4:05 | Turn Wi-Fi off (show the OS toggle). Dashboard: **Offline · still protecting**, "Internet needed: No". Press **D** on the presenter page (front door): urgent alert appears on the dashboard. | "Now the internet is gone. The models, the ladder and the nurse station keep working on the device." | *Offline · still protecting* |
| 8 | 4:05–4:35 | `/report/`: night shift handover. Scroll: totals, median response time, severity 1/2/3, per resident, timeline, care records (filed vs draft), camera switches. | "In the morning, one page for the handover: every alert, how fast someone answered, severity, and the care records, filed or ready to confirm." | *Morning handover* |
| 9 | 4:35–4:50 | `/family/?id=R-07`: "How was their night?". End card: repo URL, team names, "Not a medical device. Supports staff; does not replace them." | "And families get a calm answer to 'how was their night?' NightWatch. It notices early, and keeps going when nobody answers." | — |

**Shot 7 note:** with the laptop's Wi-Fi off, phones can't reach it unless they share a local hotspot, and
iMessage/ntfy need the internet (the contact shows as simulated, with the reason). Show the alert on the
dashboard; don't imply a phone received it unless it did.

## What must be true in the video

- Residents are synthetic (`nightwatch/demo/facility.json`). Nothing from `data/` appears on screen.
- The person on camera is a teammate who agreed; privacy view stays on. Contact phones belong to team members
  who agreed; numbers are masked on screen.
- Simulated camera data, if used, stays visibly tagged SIMULATED and is said out loud.
- Emergency services are always simulated; we never claim it calls 911.
- The device named on screen matches the voiceover. No NPU claim unless it ran on the NPU.

## Placeholders to fill

- Camera tested on a real person: yes/no (shot 2 live vs SIMULATED fallback)
- Live contact message tested: yes/no, and which channel (iMessage, ntfy) (shot 4)
- End card: team names `[Name] ×4`
- Shot 7: phones on a local hotspot, or dashboard only
