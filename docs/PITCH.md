# NightWatch: 3-minute pitch

Spoken script, about 460 words at a calm pace. Timings are cumulative. Slide names refer to the deck.
Placeholders in `[brackets]` must be filled from the team's own measurements before presenting. Do not round
them up and do not say a number we didn't measure. Until NPU numbers are in `nightwatch/bench/README.md`, say
"built for the NPU", never "runs on the NPU" as a result.

The presenter page (`/sim/`) has a step-by-step guide with the same beats; keep it on a second screen.

---

## 0:00–0:35 · The problem (slides: Cover, Problem, Cases)

> In Wisconsin, a memory-care resident walked out through a door at 12:41 in the morning. According to
> authorities, the door alarm went off and workers ignored it. The resident was found dead outside. A jury
> ordered the operator to pay about four million dollars.
>
> That case isn't unusual. Wandering affects roughly 20 to 30 percent of nursing-home residents with
> dementia, and the worst outcomes happen at night. One of our teammates works in memory care. In their
> experience, one night worker can be covering around forty residents, and residents get out even through
> pinned doors. By the time a door alarm goes off, it's already late. What the care team wants to know is
> earlier: **a resident has left their room at night.**

*Notes:* say "according to authorities" and "a jury ordered". The 1-to-40 ratio and pinned doors are our
teammate's experience; say so. If you mention Sacramento, say "a verdict reported at over $100 million"
(sources say $100M or $110M).

## 0:35–1:10 · What NightWatch does (slide: Ladder)

> NightWatch is night supervision that runs on one laptop at the nurse station. A hallway camera watches one
> line: the doorway. When a resident's feet cross it going out at night, the night nurse's phone gets a quiet
> **heads-up**. Staff walking along the hallway don't count.
>
> If an exit door opens, it's **urgent**. If still nobody answers, it's an **emergency**: a full-screen
> takeover at the nurse station, every staff phone, and at the same moment the on-call supervisor, the
> family and the owner get a message. The night nurse can also press "Call for help" or "Need backup" any
> time. It only climbs when nobody responds, and it never calls 911: emergency services stay in the
> facility's own chain and are simulated in this build.

## 1:10–2:00 · Live demo (slide: Demo, then switch to laptop + phone)

> **3 a.m.** A resident gets up for the bathroom inside their room. Nothing fires.
>
> **2:08 a.m.** This webcam is the hallway camera outside room 12. *[Teammate walks out across the doorway
> line.]* The phone buzzes: R-07 left their room. The nurse station shows a dot on a radar, never video.
>
> **Nobody answers.** Front door: urgent. Still nothing: emergency, and *[hold up the second phone]* the
> on-call supervisor just got this message.
>
> **Same night, answered.** "I'm going." The climb stops. "Found safe," and two taps file the care record.
>
> **Privacy is a switch.** Camera off: the webcam light goes off and nothing is analysed.

*Notes:* only do the live walk-out if detection has been tested on a real person on this laptop
(`[camera tested on a real person: yes/no]`). If not, run **Camera: R-07 walks out** on the presenter page;
it's tagged SIMULATED on screen; say "this run uses simulated camera data". Contacts are a dry run until the
nurse station turns the live switch on; only show a received message if it really arrived
(`[live contact message tested: yes/no, channel]`). Residents are synthetic.

## 2:00–2:30 · Why it has to run on the device (slides: How it works, Why on the device)

> Two models run here through ExecuTorch. The heavy one is a person detector watching the doorway all night,
> quantized to 8 bits, 3.9 megabytes, the format the Snapdragon's NPU is built for. The small one asks "is
> this normal for this resident right now?" Fixed rules handle what we know is dangerous; AI handles what we
> have to *see*.
>
> On the device, video and health readings never leave the building. Only a short alert text goes out, to
> people the facility chose. It keeps working with the internet down. **Families and staff decide when it
> watches: night only, or off, and off means physically off.**

## 2:30–2:45 · Results (slide: Results)

> The person detector takes about 5 milliseconds a frame on a laptop CPU. On the Snapdragon X Elite it's
> **[detector p50, CPU, ms]** on the CPU and **[detector p50, NPU, ms]** on the NPU, at
> **[detector energy per frame, NPU vs CPU, mJ]**. "Normal" for the small model was learned from simulated
> days; in a facility it would come from each resident's own first weeks.

*Notes:* 5.3 ms (int8) / 5.5–5.7 ms (fp32) were measured on a dev MacBook CPU; say "a laptop CPU", not
"Snapdragon". The `/perf/` page labels which machine each run came from. If the NPU isn't measured in time:
"the int8 model and QNN export are built for the NPU; we haven't measured it on the NPU yet."

## 2:45–3:00 · Close (slides: Workflow, What's next)

> In the morning there's one handover report, and families get a calm answer to "how was their night?"
> NightWatch supports the night shift; it doesn't replace them. In Wisconsin there was an alarm. NightWatch
> notices earlier, and keeps going when nobody answers. Thank you.

---

## Placeholders to fill

- `[camera tested on a real person: yes/no]` (live walk-out vs the SIMULATED presenter scenario)
- `[live contact message tested: yes/no, channel]` (iMessage and/or ntfy push; otherwise don't show a received message)
- `[detector p50, CPU, ms]` and `[detector p50, NPU, ms]` on the Snapdragon X Elite
- `[detector energy per frame, NPU vs CPU, mJ]`
