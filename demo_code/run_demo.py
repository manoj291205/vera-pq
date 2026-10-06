#!/usr/bin/env python3
"""VERA-PQ end-to-end demo.

Flow per round: IoT clients train locally -> quantize -> Merkle-commit -> ML-DSA sign digest
-> edge gateway verifies PQ signatures against ledger key registry -> trimmed-mean aggregation
-> commits (clientRoot, aggRoot) on ledger -> ledger derives challenge seed from commit block hash
-> gateway opens k sampled coordinates -> ledger re-computes trimmed mean on those coordinates
with Keccak-only checks -> round accepted/rejected.

Usage:
  python run_demo.py                               # pure-Python ledger
  python run_demo.py --ledger evm                  # in-process EVM (needs web3, eth-tester, solcjs)
  python run_demo.py --gateway tamper --tamper-frac 0.05
  python run_demo.py --gateway lazy                # gateway skips robust aggregation (plain mean)
  python run_demo.py --gateway lazy --withhold     # gateway never answers the challenge; a keeper expires it

Crypto-economics: the gateway deposits --deposit ETH of stake and must lock --bond ETH per round.
Accepted round: bond released + --reward ETH paid (50% gateway, 50% split across devices).
Rejected round: bond slashed into the reward pool. Expired round: same, with a 10% bounty to the keeper.
"""
import argparse, json, random, time
from pathlib import Path
import numpy as np

from verapq import pqsig, protocol as P, fl
from verapq.hashing import keccak, KECCAK_IMPL


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--clients", type=int, default=8)
    ap.add_argument("--malicious", type=int, default=2)
    ap.add_argument("--attack", default="signflip", choices=["signflip", "gaussian", "none"])
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--features", type=int, default=30)
    ap.add_argument("--trim", type=int, default=2)
    ap.add_argument("--k", type=int, default=16, help="audited coordinates per round")
    ap.add_argument("--gateway", default="honest", choices=["honest", "lazy", "tamper"])
    ap.add_argument("--tamper-frac", type=float, default=0.1)
    ap.add_argument("--ledger", default="sim", choices=["sim", "evm"])
    ap.add_argument("--non-iid", type=float, default=None)
    ap.add_argument("--no-audit", action="store_true", help="baseline: ledger accepts gateway output unchecked")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--csv", default=None, help="real dataset CSV (Edge-IIoTset / CICIoT2023)")
    ap.add_argument("--label-col", default="Attack_label")
    ap.add_argument("--normal-value", default=None)
    ap.add_argument("--bond", type=float, default=1.0, help="ETH bonded by the gateway per round")
    ap.add_argument("--reward", type=float, default=0.1, help="ETH reward per accepted round")
    ap.add_argument("--deposit", type=float, default=10.0, help="ETH the gateway stakes up front")
    ap.add_argument("--pool", type=float, default=5.0, help="ETH the operator puts in the reward pool")
    ap.add_argument("--withhold", action="store_true", help="gateway never answers the challenge (round expires)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--out", default="results/run.json")
    return run(ap.parse_args(argv))


def run(a):

    rng = np.random.default_rng(a.seed); prng = random.Random(a.seed)
    if not a.quiet:
        print(f"[setup] PQ backend={pqsig.BACKEND} alg={pqsig.ALG} keccak={KECCAK_IMPL} ledger={a.ledger}")
    wei = lambda eth: int(round(eth * 10 ** 18))
    fmt = lambda w: f"{w / 10 ** 18:.3f}"
    if a.no_audit and a.ledger == "evm":
        raise SystemExit("--no-audit is a baseline for the simulated ledger only")
    if a.ledger == "evm":
        from verapq.ledger_evm import EvmLedger
        L = EvmLedger(wei(a.bond), wei(a.reward)); print(f"[setup] contract deployed, gas={L.gas['deploy']}")
    else:
        from verapq.ledger_sim import SimLedger
        L = SimLedger(wei(a.bond), wei(a.reward))
    L.deposit_stake(wei(a.deposit)); L.fund_rewards(wei(a.pool))

    if a.csv:
        nv = a.normal_value
        nv = int(nv) if nv is not None and nv.lstrip("-").isdigit() else nv
        data, (Xte, yte) = fl.load_csv(a.csv, a.label_col, a.clients, nv, seed=a.seed, non_iid_alpha=a.non_iid)
        a.features = data[0][0].shape[1]
    else:
        data, (Xte, yte) = fl.make_data(a.clients, a.features, seed=a.seed, non_iid_alpha=a.non_iid)
    signers, t0 = {}, time.perf_counter()
    for cid in range(1, a.clients + 1):
        signers[cid] = pqsig.Signer()
        L.register_device(cid, keccak(signers[cid].pk), 1)
        if a.ledger == "evm":
            acc = L.w3.eth.accounts
            L.set_payout(cid, acc[cid] if cid < 9 else L.w3.to_checksum_address(keccak(b"dev%d" % cid)[:20]))
        else:
            L.set_payout(cid, f"device-{cid}")
    keygen_ms = (time.perf_counter() - t0) * 1000 / a.clients
    malicious = set(range(1, a.malicious + 1))
    dim = a.features + 1
    w = np.zeros(dim)
    log = dict(config=vars(a), backend=pqsig.BACKEND, keygen_ms_per_client=keygen_ms, rounds=[])
    e0 = L.econ()
    if not a.quiet:
        print(f"[econ] gateway stake={fmt(e0['stake'])} ETH, bond/round={a.bond} ETH, reward/round={a.reward} ETH, "
              f"reward pool={fmt(e0['pool'])} ETH")

    for rid in range(1, a.rounds + 1):
        ups, sign_ms = [], []
        for cid in range(1, a.clients + 1):
            X, y = data[cid - 1]
            delta = fl.local_train(w, X, y, seed=a.seed + rid * 100 + cid) - w
            if cid in malicious and a.attack != "none":
                delta = fl.poison(delta, a.attack, rng)
            t = time.perf_counter()
            ups.append(P.client_prepare(signers[cid], rid, cid, P.quantize(delta)))
            sign_ms.append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        rc = P.gateway_aggregate(ups, L.registry, a.trim, a.k, mode=a.gateway, tamper_frac=a.tamper_frac, rng=prng)
        agg_ms = (time.perf_counter() - t) * 1000
        L.commit_round(rid, rc.client_tree.root, rc.agg_tree.root, rc.n, rc.dim, rc.trim, rc.k)
        seed = L.challenge_seed(rid)
        t = time.perf_counter()
        clients, samples = P.build_audit(rc, seed)
        prove_ms = (time.perf_counter() - t) * 1000
        t = time.perf_counter()
        if a.no_audit:  # baseline: ledger trusts the gateway and pays it (simulated ledger only)
            ok, failed, gas = True, None, None
            L.settle_unchecked(rid, [u.client_id for u in rc.accepted])
        elif a.withhold:  # gateway refuses to open the challenge; anyone may expire the round after 256 blocks
            r_ = L.expire(rid)
            ok, failed = False, "expired"
            gas = r_.gasUsed if hasattr(r_, "gasUsed") else None
        else:
            if a.ledger == "sim":  # sim ledger also spot-checks one ML-DSA signature per round
                ok, failed, gas = L.audit(rid, clients, samples, P.build_sig_opening(rc, seed))
            else:
                ok, failed, gas = L.audit(rid, clients, samples)
        verify_ms = (time.perf_counter() - t) * 1000

        if ok:
            w = w + np.array(rc.agg) / P.SCALE
        acc, f1 = fl.evaluate(w, Xte, yte)
        r = dict(round=rid, accepted=ok, failed_sample=failed, rejected_clients=rc.rejected_ids, acc=acc, f1=f1,
                 sign_ms_mean=float(np.mean(sign_ms)), gateway_verify_agg_ms=agg_ms, audit_build_ms=prove_ms,
                 audit_verify_ms=verify_ms, audit_gas=gas, audit_calldata_bytes_est=P.audit_calldata_bytes(rc.n, dim, a.k),
                 sig_bytes=len(ups[0].sig), pk_bytes=len(ups[0].pk))
        e = L.econ(); r["econ_wei"] = e
        log["rounds"].append(r)
        if not a.quiet:
            print(f"[round {rid}] audit={'ACCEPT' if ok else 'EXPIRED (keeper slashed bond)' if failed == 'expired' else 'REJECT(sample %s)' % failed} acc={acc:.3f} f1={f1:.3f} "
                  f"sign={r['sign_ms_mean']:.1f}ms gw={agg_ms:.1f}ms build={prove_ms:.1f}ms verify={verify_ms:.1f}ms"
                  + (f" gas={gas}" if gas else ""))
            print(f"          stake={fmt(e['stake'])} ETH  gateway earned={fmt(e['credit'])}  "
                  f"devices earned={fmt(e['device_credit'])}  pool={fmt(e['pool'])}"
                  + (f"  keeper bounty={fmt(L.credit.get('keeper', 0) if hasattr(L, 'credit') else L.c.functions.credit(L.keeper).call())}" if a.withhold else ""))

    e = L.econ(); log["econ_final_wei"] = e
    if not a.quiet:
        print(f"[econ] gateway stake {fmt(e0['stake'])} -> {fmt(e['stake'])} ETH "
              f"(slashed {fmt(e0['stake'] - e['stake'])}), gateway rewards {fmt(e['credit'])} ETH, "
              f"device rewards {fmt(e['device_credit'])} ETH")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(log, indent=2, default=str))
    if not a.quiet:
        print(f"[done] wrote {a.out}")
    return log


if __name__ == "__main__":
    main()
