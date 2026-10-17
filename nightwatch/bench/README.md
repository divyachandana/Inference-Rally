# NightWatch benchmark: Hexagon NPU vs CPU

`benchmark.py` runs the normal-pattern model (~850 parameters, 8 inputs, batch 1) from one or more
ExecuTorch `.pte` files, the same way `nightwatch/scorer.py` does, on realistic per-resident inputs
from `nightwatch/features.py` (quiet nights, wandering, corridor and exit moments, daytime).

It reports, per backend:

- p50 / p95 / p99 latency (ms) and throughput (checks per second)
- average **whole-laptop** power while running vs an idle baseline measured first, and
  energy per check = (W running − W idle) / checks per second (only if the battery gauge can be read)
- an output check: 96 fixed inputs through every `.pte`, max difference vs the first one listed

It prints a markdown table and writes everything (host, versions, args, results, warnings) to
`logs/bench/<timestamp>.json` (git-ignored).

## On the Snapdragon X Elite laptop (Windows on ARM)

Before you start:

1. **Unplug the charger.** The battery gauge only measures power on battery; the script warns if it sees AC.
2. Fixed screen brightness, close other apps, turn off Windows Update / OneDrive sync for the run,
   same power mode ("Best performance" or "Balanced") for every run, and note which one you used.
3. Don't touch the laptop during the idle baseline or the runs.

From the repo root, both models (the first `--pte` is the reference for the output check):

```bash
python nightwatch/bench/benchmark.py --pte models/normal_pattern_qnn.pte:NPU --pte models/normal_pattern_xnnpack.pte:CPU --seconds 60 --rate max
```

Then the realistic load (4 residents, each checked once per second):

```bash
python nightwatch/bench/benchmark.py --pte models/normal_pattern_qnn.pte:NPU --pte models/normal_pattern_xnnpack.pte:CPU --seconds 60 --rate 4
```

Each run takes about idle (60 s) + 2 × (5 s settle + 60 s) ≈ 3 min. Commit nothing from `logs/`; copy the
printed table into the results below.

Options: `--warmup N` (default 500), `--idle-seconds S` (default = `--seconds`, max 60), `--settle S`
(pause between phases, excluded from power, default 5), `--no-power`, `--seed`.

If the QNN `.pte` fails to load, the QNN runtime libraries on the laptop probably don't match the SDK
version it was compiled with; the script stops with the loader error rather than guessing.

## What the numbers mean (and don't)

- **Power is whole-laptop power** from the battery gauge (Windows `root\wmi BatteryStatus.DischargeRate`,
  macOS `ioreg`), not NPU power. Screen, Wi-Fi and background apps are all in it. Only "W above idle",
  measured in the same sitting, says anything about the model.
- Battery gauges update slowly (seconds, some every 10–30 s). Use 60 s runs. If "W above idle" is ≤ 0 or
  jumps between runs, the model's draw is inside the gauge noise; say that rather than quoting a number.
- **Latency is the Python `method.execute()` call**, as in the live server. For a model this small,
  Python binding and dispatch overhead is a large part of it, and the NPU adds a CPU→NPU round trip
  per call. At batch 1 the NPU may well *not* be faster than the CPU; report what you measure.
- `--rate max` keeps the core hot. At `--rate 4` the CPU sleeps between checks, so per-check latency
  is higher (cold caches, lower clocks) but total power is close to idle; that is the real workload.
- The output check compares scores (0–1) on identical inputs. fp16 on the NPU will differ slightly
  from fp32 on the CPU; a max score difference around 1e-3 or below means the same alerts.

## Results

### Reference: MacBook (Apple Silicon, macOS), XNNPACK on CPU — measured

Not the target hardware; shown only so the table shape and magnitudes are clear.
10 s runs (short, so power is noisy), on battery:

| Backend | p50 ms | p95 ms | p99 ms | checks/s | W running | W idle | W above idle | mJ/check |
|---|---|---|---|---|---|---|---|---|
| CPU (XNNPACK), rate max | 0.0043 | 0.0046 | 0.0049 | 221,827 | 20.75 | 19.72 | 1.03 | 0.0047 |
| CPU (XNNPACK), rate 4 | 0.31 | 0.39 | 0.41 | 4 | — | — | — | — |

(rate 4 row run with `--no-power`, 5 s.)

### Snapdragon X Elite, Windows on ARM — to fill in on the laptop

Power mode: ______  Brightness: ______  On battery: yes / no  Date: ______

| Backend | Rate | p50 ms | p95 ms | p99 ms | checks/s | W running | W idle | W above idle | mJ/check | max score diff |
|---|---|---|---|---|---|---|---|---|---|---|
| NPU (QNN, fp16) | max | | | | | | | | | — (reference) |
| CPU (XNNPACK, fp32) | max | | | | | | | | | |
| NPU (QNN, fp16) | 4/s | | | | | | | | | — (reference) |
| CPU (XNNPACK, fp32) | 4/s | | | | | | | | | |
