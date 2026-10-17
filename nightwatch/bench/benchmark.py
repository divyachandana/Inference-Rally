"""Benchmark the NightWatch normal-pattern model: Hexagon NPU (QNN) vs CPU (XNNPACK).

    python nightwatch/bench/benchmark.py \
        --pte models/normal_pattern_qnn.pte:NPU --pte models/normal_pattern_xnnpack.pte:CPU \
        --seconds 60 --rate max

    python nightwatch/bench/benchmark.py --pte models/normal_pattern_xnnpack.pte:CPU --seconds 10

Each .pte is loaded with executorch.runtime.Runtime exactly like nightwatch/scorer.py, warmed
up, then run on realistic per-resident inputs built with features.vector() (night/day, in bed
/ up, room / corridor / exit). --rate max runs back to back; --rate 4 is the realistic load
(4 residents, each checked once per second).

Reports p50/p95/p99 latency, throughput and, when the battery gauge can be read, average
WHOLE-LAPTOP power while running vs an idle baseline measured first:
    energy per check = (W_running - W_idle) / checks_per_second
It also runs one fixed set of inputs through every .pte and reports the max difference vs the
first one, to show the NPU output matches the CPU. Writes JSON to logs/bench/<timestamp>.json.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from features import vector  # noqa: E402
import power  # noqa: E402

HR_REST = 64.0
ZONES = ["bed", "room", "corridor", "exit"]


def realistic_inputs(n: int, seed: int) -> list[list[float]]:
    """A mix of the moments the live engine sees: mostly quiet nights, some wandering, daytime."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        night = rng.random() < 0.7
        hour = rng.choice([22, 23, 0, 1, 2, 3, 4, 5]) + rng.random() if night else rng.uniform(7, 21)
        up = rng.random() < (0.25 if night else 0.8)
        zone = rng.choices(ZONES, weights=[0, 6, 3, 1] if up else [1, 0, 0, 0])[0]
        motion = rng.uniform(0.2, 0.9) if up else rng.uniform(0.0, 0.1)
        hr = None if rng.random() < 0.1 else HR_REST + (rng.uniform(5, 35) if up else rng.uniform(-6, 4))
        minutes_up = rng.uniform(0, 45) if up else 0.0
        out.append(vector(hour, up, motion, hr, HR_REST, zone, minutes_up))
    return out


def fixed_inputs() -> list[list[float]]:
    """Deterministic grid for the output check: every zone, in/out of bed, night and day."""
    grid = []
    for hour in (2.0, 4.5, 14.0, 23.0):
        for zone in ZONES:
            for up in (False, True):
                for hr in (None, HR_REST, HR_REST + 30):
                    grid.append(vector(hour, up, 0.6 if up else 0.05, hr, HR_REST, zone, 20 if up else 0))
    return grid


class Backend:
    def __init__(self, pte: Path, label: str) -> None:
        import torch
        from executorch.runtime import Runtime

        self._torch = torch
        self.pte, self.label = pte, label
        t = time.perf_counter()
        self._method = Runtime.get().load_program(str(pte)).load_method("forward")
        self.load_ms = (time.perf_counter() - t) * 1000

    def tensor(self, x: list[float]):
        return self._torch.tensor([x], dtype=self._torch.float32)

    def run(self, t) -> float:
        (logit,) = self._method.execute([t])
        return float(logit.flatten()[0])


def pct(sorted_vals: list[float], p: float) -> float:
    k = (len(sorted_vals) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def timed_run(b: Backend, tensors: list, seconds: float, rate: float | None) -> tuple[list[float], float]:
    """Run for `seconds`; return (latencies in ms, wall seconds)."""
    lat: list[float] = []
    interval = 1.0 / rate if rate else 0.0
    start = time.perf_counter()
    end = start + seconds
    nxt = start
    i = 0
    while True:
        now = time.perf_counter()
        if now >= end:
            break
        if rate:
            if now < nxt:
                time.sleep(min(nxt - now, end - now))
                continue
            nxt = max(nxt + interval, now)  # fell behind: don't burst to catch up
        t = tensors[i % len(tensors)]
        t0 = time.perf_counter()
        b.run(t)
        lat.append((time.perf_counter() - t0) * 1000)
        i += 1
    return lat, time.perf_counter() - start


def parse_pte(spec: str) -> tuple[Path, str]:
    path, _, label = spec.rpartition(":")
    if not path or "/" in label or "\\" in label:  # no label given (or a Windows drive letter)
        path, label = spec, Path(spec).stem
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        p = ROOT / p
    return p, label


def versions() -> dict:
    out = {"python": platform.python_version()}
    for mod in ("torch", "executorch"):
        try:
            from importlib.metadata import version
            out[mod] = version(mod)
        except Exception:  # noqa: BLE001
            out[mod] = None
    return out


def fmt(v, nd=3, unit=""):
    return "n/a" if v is None else f"{v:.{nd}f}{unit}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pte", action="append", required=True, metavar="PATH:LABEL",
                    help="a .pte and a label, e.g. models/normal_pattern_qnn.pte:NPU (repeatable)")
    ap.add_argument("--seconds", type=float, default=60, help="timed run per backend (default 60)")
    ap.add_argument("--rate", default="max", help="'max' (back to back) or checks per second, e.g. 4")
    ap.add_argument("--warmup", type=int, default=500, help="untimed runs before timing (default 500)")
    ap.add_argument("--idle-seconds", type=float, default=None,
                    help="idle power baseline before the runs (default: same as --seconds, max 60)")
    ap.add_argument("--settle", type=float, default=5,
                    help="pause between phases, excluded from power averages (default 5 s)")
    ap.add_argument("--no-power", action="store_true", help="skip battery-gauge power")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rate = None if args.rate == "max" else float(args.rate)
    idle_s = args.idle_seconds if args.idle_seconds is not None else min(args.seconds, 60)

    specs = [parse_pte(s) for s in args.pte]
    backends = []
    for path, label in specs:
        if not path.exists():
            sys.exit(f"not found: {path}")
        print(f"loading {label}: {path.name}")
        backends.append(Backend(path, label))

    # 1. Output check: same fixed inputs through every backend, compare to the first.
    grid = fixed_inputs()
    logits = {b.label: [b.run(b.tensor(x)) for x in grid] for b in backends}
    ref = backends[0].label
    sig = lambda z: 1 / (1 + math.exp(z))  # noqa: E731 - score = sigmoid(-logit), as in scorer.py
    match = {}
    for b in backends:
        dl = max(abs(a - r) for a, r in zip(logits[b.label], logits[ref]))
        ds = max(abs(sig(a) - sig(r)) for a, r in zip(logits[b.label], logits[ref]))
        match[b.label] = {"vs": ref, "inputs": len(grid), "max_abs_logit_diff": dl, "max_abs_score_diff": ds}

    # 2. Timed runs, with one power sampler covering idle baseline + every backend.
    inputs = realistic_inputs(2000, args.seed)
    sampler = None if args.no_power else power.PowerSampler(interval_s=1.0)
    results = []
    idle_w = None
    if sampler:
        sampler.__enter__()
    try:
        if sampler:
            print(f"idle baseline: {idle_s:.0f} s - don't touch the laptop")
            time.sleep(args.settle)
            t0 = time.perf_counter()
            time.sleep(idle_s)
            idle_w = sampler.mean_watts(t0, time.perf_counter())
            idle_n = sampler.count(t0, time.perf_counter())
        for b in backends:
            tensors = [b.tensor(x) for x in inputs]
            for i in range(args.warmup):
                b.run(tensors[i % len(tensors)])
            if sampler:
                time.sleep(args.settle)
            print(f"running {b.label} for {args.seconds:.0f} s at rate {args.rate}")
            t0 = time.perf_counter()
            lat, wall = timed_run(b, tensors, args.seconds, rate)
            t1 = time.perf_counter()
            lat.sort()
            cps = len(lat) / wall
            run_w = sampler.mean_watts(t0, t1) if sampler else None
            net_w = None if run_w is None or idle_w is None else run_w - idle_w
            results.append({
                "label": b.label, "pte": str(b.pte.relative_to(ROOT) if b.pte.is_relative_to(ROOT) else b.pte),
                "pte_kb": round(b.pte.stat().st_size / 1024, 1), "load_ms": round(b.load_ms, 1),
                "checks": len(lat), "seconds": round(wall, 2), "checks_per_s": round(cps, 1),
                "p50_ms": pct(lat, 50), "p95_ms": pct(lat, 95), "p99_ms": pct(lat, 99),
                "mean_ms": statistics.fmean(lat), "max_ms": lat[-1],
                "power_samples": sampler.count(t0, t1) if sampler else 0,
                "watts_running": run_w, "watts_idle": idle_w, "watts_above_idle": net_w,
                "mj_per_check": None if net_w is None else net_w / cps * 1000,
                "output_check": match[b.label],
            })
    finally:
        if sampler:
            sampler.__exit__(None, None, None)

    # 3. Report.
    have_power = idle_w is not None
    print()
    print(f"NightWatch normal-pattern model, batch 1, {args.seconds:.0f} s per backend, rate {args.rate}, "
          f"{platform.system()} {platform.machine()}")
    print()
    print("| Backend | p50 ms | p95 ms | p99 ms | checks/s | W running | W idle | W above idle | mJ/check "
          f"| max score diff vs {ref} |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['label']} | {r['p50_ms']:.4f} | {r['p95_ms']:.4f} | {r['p99_ms']:.4f} | {r['checks_per_s']:.0f} "
              f"| {fmt(r['watts_running'], 2)} | {fmt(r['watts_idle'], 2)} | {fmt(r['watts_above_idle'], 2)} "
              f"| {fmt(r['mj_per_check'], 4)} | {r['output_check']['max_abs_score_diff']:.2e} |")
    print()
    notes = []
    if sampler is None:
        notes.append("power: skipped (--no-power)")
    elif not have_power:
        notes.append(f"power: battery gauge could not be read ({sampler.error or 'no samples'}) - latency only")
    else:
        notes.append(f"power: {power.LABEL}; idle baseline {idle_w:.2f} W from {idle_n} samples")
        if sampler.saw_ac:
            notes.append("WARNING: AC power was connected during the run - unplug and rerun; watts are not valid")
        if any(r["watts_above_idle"] is not None and r["watts_above_idle"] <= 0 for r in results):
            notes.append("note: a backend measured at or below idle - the model's draw is inside gauge noise; "
                         "use a longer --seconds or --rate max")
        if args.seconds < 60:
            notes.append("note: runs shorter than 60 s give noisy battery-gauge averages")
    notes.append(f"output check: {len(grid)} fixed inputs, max |score diff| vs {ref} "
                 + ", ".join(f"{k}={v['max_abs_score_diff']:.2e}" for k, v in match.items()))
    for n in notes:
        print(n)

    out_dir = ROOT / "logs" / "bench"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = out_dir / f"{stamp}.json"
    out.write_text(json.dumps({
        "timestamp": stamp,
        "host": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(),
                 "processor": platform.processor(), **versions()},
        "args": vars(args), "power_label": power.LABEL if have_power else None,
        "power_on_ac": sampler.saw_ac if sampler else None, "results": results, "notes": notes,
    }, indent=2))
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
