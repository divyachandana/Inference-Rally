# NightWatch · 5-minute demo script

For the recorded video and the live demo. About 700 spoken words, roughly 5:00 at a calm pace.
**SAY** is what you speak. **DO** is what's on screen. Lines in *(brackets)* are optional cuts if you run long.

**Before you hit record**
- Presenter page (`/sim/`) → **Reset everything** → Contacts → **Real sending: ON** (iMessage to the team phone).
- Click once on the dashboard (enables alarm sound). In the phone window: enter a name, tap **enable sound**.
- Windows: dashboard big on the left, the staff phone window on the right, presenter behind them.
- Camera page (`/camera/`): setup guide done, doorway line drawn, privacy blur on. If the webcam is unreliable, use the
  simulated walk-out (it's labelled SIMULATED on screen; say so).
- Have your phone next to the laptop, Messages open.

---

## 0:00–0:35 · The problem

**DO:** Title slide, or the dashboard idle at night ("All quiet").

**SAY:**
> In Wisconsin, a memory-care resident walked out through a door at 12:41 in the morning. According to authorities,
> the door alarm went off and workers ignored it. She was found dead outside, and a jury ordered the operator to pay
> about four million dollars.
>
> It isn't rare. Wandering affects roughly a quarter of nursing-home residents with dementia, and the worst cases
> happen at night. One of our teammates works in memory care: in her experience, one night worker can cover around
> forty residents. An alarm only helps if someone answers it.

## 0:35–0:55 · What NightWatch is

**DO:** Dashboard: floor plan, residents in bed, the chips row (model on this laptop, "Internet needed: No").

**SAY:**
> This is NightWatch. It runs entirely on one laptop at the nurse station. It notices when a resident leaves their
> room at night, and it keeps escalating until a human responds. Nothing leaves the building: no cloud, no video
> recorded.

## 0:55–1:25 · No false alarms

**DO:** Presenter → **Visitors come and go** (14:00). Doors open, "visit logged", no alarm.
Then **R-15 ensuite trip** (03:00). R-15 gets up and goes back to bed: nothing fires.

**SAY:**
> During the day, door openings are just logged as visits. At night it stays quiet for normal things: R-15 gets up
> for the bathroom and goes back to bed. No alert. False alarms are what teach staff to ignore alarms, so this matters
> as much as catching the real thing.

## 1:25–2:35 · The real thing, and nobody answers

**DO:** Presenter → **R-07 heads for the front door** (02:08). Don't touch the phone.
Point at: heads-up on the phone window → front door opens → **URGENT** → countdown → **EMERGENCY** full-screen
takeover → "Who's been contacted" list → your phone receives the iMessages.

**SAY:**
> Two in the morning. R-07, who has a history of exit-seeking, leaves their room. Within seconds the night worker's
> phone gets a heads-up, with what usually calms this resident: a short walk with staff.
>
> Now the front door opens. That's urgent. And this time, nobody answers: the worker is busy with someone else.
> NightWatch doesn't wait. After fifteen seconds it escalates to emergency: every staff phone, the on-call
> supervisor, the family and the facility owner, all at once.
>
> *(Hold up your phone.)* That's a real message arriving now. Emergency services shows as "would be called per
> facility policy": calling 911 stays a human decision, and the system refuses emergency numbers by design.

## 2:35–3:15 · The same night, answered

**DO:** Presenter → **R-07 heads for the front door** again. In the phone window tap **I'm going** at the heads-up,
then **Found safe**. The 2-tap care-record sheet appears: pick a state and what helped → **File**.

**SAY:**
> Same night, but the worker answers. One tap: I'm going. The escalation stops, and everyone can see who's
> responding. Found safe. Then two taps file the care record in the care team's own format: their pick-lists, their
> severity scale. Paperwork at 3 a.m. becomes two taps.

## 3:15–3:55 · The camera, and privacy

**DO:** Camera page: walk out across the doorway line (or run **Camera: R-07 walks out (simulated)**, and say it's
simulated). Show the "LEFT the room" banner, then the dashboard radar (positions only). Then flip the camera **off**:
"Camera off · the webcam is released".

**SAY:**
> How does it know someone left the room? A person detector runs on this laptop, many times a second. You draw the
> doorway once, and only feet crossing it going out count, so staff walking past don't trigger it.
>
> Every frame is analysed in memory and thrown away. Nothing is recorded. The dashboard only ever sees dots, never
> video. And families and staff decide when it watches: night only, or off. Off means off: the webcam is released.

## 3:55–4:30 · Why on-device, and the AI

**DO:** `/perf/`: live milliseconds per check and per frame, model names and device. Optionally turn Wi-Fi off and show
the dashboard still running ("Offline · still protecting").

**SAY:**
> Under the hood: two models running through ExecuTorch, on the device. A person detector for the camera, and a small
> model that learned what normal looks like for each moment of the night. The safety-critical escalation is plain
> rules, on purpose, so it's always predictable.
>
> Because it's on-device, it works when the internet drops at night, resident data never leaves the building, and
> checking every resident every second costs nothing. *(On the Snapdragon laptop: [N] milliseconds per frame on the
> [NPU/CPU]. Only say numbers you measured.)*

## 4:30–4:50 · The morning

**DO:** `/report/`: the shift report. Then `/family/?id=R-07`.

**SAY:**
> In the morning, the day team gets a handover: every alert, how fast staff responded, and the records already
> drafted. And the family can read a calm summary of their relative's night, with no video and no one else's data.

## 4:50–5:00 · Close

**DO:** Back to the dashboard, "All quiet". Or the title slide.

**SAY:**
> NightWatch: it notices earlier, and it keeps going when nobody answers. Everything stays in the building. Thank you.

---

## If you're running long (cut in this order)
1. The family-view sentence (4:30).
2. "Paperwork at 3 a.m. becomes two taps" (2:35).
3. The Wi-Fi-off moment (3:55).

## Honesty notes (keep these true on camera)
- Residents are synthetic. The simulated camera walk-out is labelled SIMULATED; say "simulated" if you use it.
- The phone window on the laptop is "the staff phone view"; a real phone pairs with a PIN over the facility Wi-Fi.
- Messages go out by iMessage/push in this demo; production would use calls/SMS. Only alert text leaves the building.
- No NPU numbers unless measured on the Snapdragon laptop. Lawsuit wording: "according to authorities", "a jury ordered".
- "Supports staff". It is not a medical device.
