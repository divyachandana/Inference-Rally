# NightWatch: 3-minute pitch

Spoken script, about 440 words at a calm pace. Timings are cumulative. Slide names refer to the deck.
Placeholders in `[brackets]` must be filled from the team's own measurements before presenting. Do not
round them up and do not say a number we didn't measure. Nothing has been run on the NPU yet: until it has,
don't say "on the NPU" as a result, only as the target.

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

## 0:35–1:05 · What NightWatch does (slide: Ladder)

> NightWatch is night supervision that runs on this laptop. A hallway camera and room sensors watch for one
> thing at night: a resident leaving their room. That's an immediate, quiet **heads-up** on the night staff
> phone. Bathroom trips inside the room don't count.
>
> If an exit door opens, or a camera sees someone at the front entrance, it's **urgent**. If still nobody
> answers, it's an **emergency**: all phones, the on-call supervisor, then emergency services through the
> facility's own contact chain. It only climbs when nobody responds. It never auto-dials 911; in this build
> those steps are simulated.

## 1:05–2:00 · Live demo (slide: Demo, then switch to laptop + phone)

> **Daytime, 2 p.m.** Visitors come and go. Doors are logged as visits. No alarms.
>
> **Now it's 2:08 a.m.** This webcam is the hallway camera outside room 12. *[Teammate walks out of a
> doorway in front of the webcam.]* Three frames with a person, and the phone buzzes: R-07 left their room.
> The camera view is blurred, and no frame is stored or sent anywhere.
>
> **Nobody answers.** The resident reaches the front door: urgent. Still nothing: emergency, supervisor,
> and "emergency services would be called now."
>
> **Same night, answered.** I tap "I'm going." The climb stops. "Found safe" closes it, with a severity
> badge and a draft care record.
>
> **Now I turn Wi-Fi off.** It keeps working.

*Notes:* only do the live walk-out if detection has been tested on a real person on this laptop beforehand
(`[camera tested on a real person: yes/no]`). If not, run *Night: R-07 heads for the front door* in the
simulator instead and say "here the hallway signal comes from the simulator". Residents are synthetic.

## 2:00–2:30 · Why it has to run on the device (slides: How it works, Why on the device)

> There are two models here, both running through ExecuTorch. The heavy one is a person detector looking
> at camera frames all night: that continuous workload is exactly what the Snapdragon's NPU is for. The
> small one is about 850 parameters and asks "is this normal for this resident right now?"
>
> And we chose on purpose: fixed rules for what we know is dangerous, a door at 2 a.m.; machine learning
> for what we have to *see*.
>
> It has to be on the device. Cameras pointed at people with dementia can't stream to a cloud, facility
> internet drops at night, and a safety system can't wait on either.

## 2:30–2:45 · Results (slide: Results)

> The person detector takes about 6 milliseconds a frame on a laptop CPU with XNNPACK. On the Snapdragon X
> Elite it's **[detector p50, CPU, ms]** on the CPU and **[detector p50, NPU, ms]** on the NPU, at
> **[detector energy per frame, NPU vs CPU, mJ]**. To be clear: "normal" for the small model was learned from
> simulated days; in a facility it would come from each resident's own first weeks.

*Notes:* the 6 ms figure was measured on a MacBook CPU during development; say "a laptop CPU", not
"Snapdragon". Read Snapdragon and NPU numbers only once they're in `nightwatch/bench/README.md`. If the NPU
isn't measured in time: "the QNN export path for the NPU is built; we haven't run it on the NPU yet."

## 2:45–3:00 · Close (slides: Workflow, What's next)

> Every alert ends as a draft record in the care team's own format, for staff to confirm. NightWatch
> supports the night shift; it doesn't replace them. In Wisconsin there was an alarm. NightWatch notices
> earlier, and keeps going when nobody answers. Thank you.

---

## Placeholders to fill

- `[camera tested on a real person: yes/no]` (decides live walk-out vs simulator)
- `[detector p50, CPU, ms]` and `[detector p50, NPU, ms]` on the Snapdragon X Elite
- `[detector energy per frame, NPU vs CPU, mJ]`
- Normal-pattern model CPU/NPU numbers if you choose to quote them (deck → Results)
