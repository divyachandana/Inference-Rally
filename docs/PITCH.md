# NightWatch: 3-minute pitch

Spoken script, about 420 words at a calm pace. Timings are cumulative. Slide names refer to the deck.
Placeholders in `[brackets]` must be filled from the team's own measurements before presenting. Do not
round them up and do not say a number we didn't measure.

---

## 0:00–0:35 · The problem (slides: Cover, Problem, Cases)

> In Wisconsin, a memory-care resident walked out through a door at 12:41 in the morning. According to
> authorities, the door alarm went off and workers ignored it. The resident was found dead outside. A jury
> ordered the operator to pay about four million dollars.
>
> That case isn't unusual. Wandering affects roughly 20 to 30 percent of nursing-home residents with
> dementia, and the worst outcomes happen at night. One of our teammates works in memory care. In their
> experience, one night worker can be covering around forty residents, and residents get out even through
> pinned doors. The alarm exists. What's missing is something that keeps going when nobody answers.

*Notes:* say "according to authorities" and "a jury ordered". The 1-to-40 ratio and pinned doors are our
teammate's experience; say so. If you mention Sacramento, say "a verdict reported at over $100 million"
(sources say $100M or $110M).

## 0:35–1:05 · What NightWatch does (slide: Ladder)

> NightWatch is night supervision that runs on this laptop. It watches door sensors, a heart-rate watch and
> bed and location data, and it has three levels.
>
> A quiet **heads-up** to the night staff phone when a resident is up and that's unusual for this time of
> night. **Urgent** when an exit opens at night, or nobody answered the heads-up. **Emergency** if still
> nobody answers: all phones, the on-call supervisor, then emergency services through the facility's own
> contact chain. It only climbs when nobody responds. It never auto-dials 911; in this build those steps are
> simulated.

## 1:05–1:55 · Live demo (slide: Demo, then switch to laptop + phone)

> **Daytime, 2 p.m.** Visitors come and go. Doors are logged as visits. No alarms.
>
> **3 a.m.** A resident gets up for a short ensuite trip and goes back to bed. Nothing fires.
>
> **2:08 a.m.** Another resident gets up, heart rate climbing, heads down the corridor. Heads-up on the
> phone. The front door opens: urgent. Nobody answers: emergency, supervisor, and "emergency services would
> be called now."
>
> **Same night, answered.** I tap "I'm going." The climb stops. "Found safe" closes it, with a severity
> badge and a draft care record.
>
> **Now I turn Wi-Fi off.** It keeps working.

*Notes:* if time is short, skip beat 2 and say it in one line. Residents are synthetic; say so if asked.

## 1:55–2:25 · Why it has to run on the device (slides: How it works, Why on the device)

> A safety system can't depend on the cloud. Facility internet drops at night too. Heart rate and location
> of people with dementia shouldn't leave the building. And each check takes a fraction of a millisecond,
> so every resident is checked every second, all night.
>
> The "is this normal for right now?" model is about 850 parameters, running through ExecuTorch: XNNPACK on
> the CPU, and the Qualcomm QNN backend on the Hexagon NPU. It learned by telling real normal moments from
> scrambled ones, so it needs no labeled incidents.

## 2:25–2:45 · Results (slide: Results)

> On the Snapdragon X Elite, one check takes **[NPU p50 latency, ms]** on the NPU versus
> **[CPU p50 latency, ms]** on the CPU, using **[NPU energy per check, mJ]** versus
> **[CPU energy per check, mJ]**. A resident at the exit at 2 a.m. with a raised heart rate scores 1.00; a
> normal bathroom trip scores 0.30. To be clear: "normal" here was learned from simulated days. In a
> facility, it would come from each resident's own first weeks.

*Notes:* only read numbers out loud once they are in `README.md` → Benchmark. If the NPU run isn't
measured in time, say "we measured [CPU p50] on the CPU; the NPU build is [status]" and nothing more.

## 2:45–3:00 · Close (slides: Workflow, What's next)

> Every alert ends as a draft record in the care team's own format, for staff to confirm. NightWatch
> supports the night shift; it doesn't replace them. The worker in Wisconsin had an alarm. NightWatch is
> what keeps going when nobody answers. Thank you.

---

## Placeholders to fill

- `[NPU p50 latency, ms]`, `[CPU p50 latency, ms]`
- `[NPU energy per check, mJ]`, `[CPU energy per check, mJ]`
- Fallback line if the NPU isn't measured: `[status]`
