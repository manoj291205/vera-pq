#!/usr/bin/env python3
"""Experiment grid for the paper (E1-E4). Writes results/exp_*.csv. Run on your own machine and paste
the CSVs back; sandbox runs are smoke tests only.

  python experiments.py E1   # accuracy/F1 vs attack x aggregator(gateway mode) x audit on/off
  python experiments.py E2   # tamper detection rate vs k and tamper fraction (many seeds)
  python experiments.py E3   # overhead: sign/verify/build/verify-time vs n, dim  (sim ledger)
  python experiments.py E4   # gas vs n, dim, k on EVM  (= bench.py gas)
Add --csv PATH --label-col COL [--normal-value V] to E1 to use Edge-IIoTset / CICIoT2023.
"""
import csv, itertools, sys
from pathlib import Path
import numpy as np
import run_demo

OUT = Path("results"); OUT.mkdir(exist_ok=True)


def _run(**kw):
    argv = []
    for k, v in kw.items():
        if v is True:
            argv.append(f"--{k.replace('_', '-')}")
        elif v not in (None, False):
            argv += [f"--{k.replace('_', '-')}", str(v)]
    return run_demo.main(argv + ["--quiet", "--out", "results/_tmp.json"])


def write(name, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote results/{name} ({len(rows)} rows)")


def E1(extra):
    rows = []
    for attack, mal, gw, audit, seed in itertools.product(["none", "signflip", "gaussian"], [0, 1, 2, 3],
                                                          ["honest", "lazy"], [True, False], [1, 2, 3]):
        if attack == "none" and mal > 0 or attack != "none" and mal == 0:
            continue
        log = _run(attack=attack, malicious=mal, gateway=gw, no_audit=not audit, rounds=10, seed=seed, **extra)
        last = log["rounds"][-1]
        rows.append(dict(attack=attack, malicious=mal, gateway=gw, audit=audit, seed=seed, final_acc=last["acc"],
                         final_f1=last["f1"], rounds_rejected=sum(not r["accepted"] for r in log["rounds"])))
    write("exp_E1.csv", rows)


def E2(extra):
    rows = []
    for k, frac in itertools.product([4, 8, 16, 32], [0.01, 0.05, 0.1, 0.25]):
        det = []
        for seed in range(int(__import__("os").environ.get("E2_SEEDS", "20"))):
            log = _run(gateway="tamper", tamper_frac=frac, k=k, rounds=1, seed=seed, features=255, **extra)
            det.append(not log["rounds"][0]["accepted"])
        m = max(1, round(frac * 256))
        rows.append(dict(k=k, tamper_frac=frac, dim=256, detect_rate=float(np.mean(det)),
                         analytic=1 - (1 - m / 256) ** k))
    write("exp_E2.csv", rows)


def E3(extra):
    rows = []
    for n, feats in itertools.product([8, 16, 32], [31, 255, 1023]):
        log = _run(clients=n, malicious=n // 4, trim=n // 4, features=feats, rounds=3, seed=1, **extra)
        rr = log["rounds"]
        rows.append(dict(n=n, dim=feats + 1, sign_ms=np.mean([r["sign_ms_mean"] for r in rr]),
                         gw_ms=np.mean([r["gateway_verify_agg_ms"] for r in rr]),
                         build_ms=np.mean([r["audit_build_ms"] for r in rr]),
                         verify_ms=np.mean([r["audit_verify_ms"] for r in rr]),
                         calldata_est=rr[0]["audit_calldata_bytes_est"], sig_bytes=rr[0]["sig_bytes"],
                         backend=log["backend"]))
    write("exp_E3.csv", rows)


def E4(extra):
    import bench; bench.bench_gas()


if __name__ == "__main__":
    which = sys.argv[1]; extra = {}
    rest = sys.argv[2:]
    for i in range(0, len(rest), 2):
        extra[rest[i].lstrip("-").replace("-", "_")] = rest[i + 1]
    {"E1": E1, "E2": E2, "E3": E3, "E4": E4}[which](extra)
