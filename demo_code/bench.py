#!/usr/bin/env python3
"""Micro-benchmarks for the paper's TODO tables (run on YOUR machines; sandbox numbers are smoke tests only).

  python bench.py sigs        # PQ vs classical signature sizes/timings (liboqs if available)
  python bench.py detect      # empirical vs analytic detection probability of a tampering gateway
  python bench.py gas         # on-chain audit gas vs (n clients, k samples, dim)  [needs EVM backend]
"""
import json, os, random, statistics, sys, time
from pathlib import Path
from verapq import protocol as P, pqsig
from verapq.hashing import keccak
from verapq.merkle import MerkleTree

OUT = Path("results"); OUT.mkdir(exist_ok=True)


def timeit(fn, reps):
    ts = []
    for _ in range(reps):
        t = time.perf_counter(); fn(); ts.append((time.perf_counter() - t) * 1000)
    return statistics.median(ts)


def bench_sigs(reps=50):
    rows, msg = [], keccak(b"digest")
    try:
        import warnings; warnings.simplefilter("ignore")
        import oqs
        for alg in [a for a in ("ML-DSA-44", "ML-DSA-65", "ML-DSA-87", "Falcon-512", "SPHINCS+-SHA2-128f-simple",
                                "SLH_DSA_PURE_SHA2_128F") if a in oqs.get_enabled_sig_mechanisms()]:
            s = oqs.Signature(alg); pk = s.generate_keypair(); sig = s.sign(msg)
            rows.append(dict(alg=alg, backend="liboqs", pk=len(pk), sig=len(sig),
                             keygen_ms=timeit(lambda: oqs.Signature(alg).generate_keypair(), reps // 5 or 1),
                             sign_ms=timeit(lambda: s.sign(msg), reps),
                             verify_ms=timeit(lambda: oqs.Signature(alg).verify(msg, sig, pk), reps)))
    except Exception as e:
        print("liboqs unavailable:", e)
    from dilithium_py.ml_dsa import ML_DSA_44
    pk, sk = ML_DSA_44.keygen(); sig = ML_DSA_44.sign(sk, msg)
    rows.append(dict(alg="ML-DSA-44", backend="dilithium-py", pk=len(pk), sig=len(sig), keygen_ms=None,
                     sign_ms=timeit(lambda: ML_DSA_44.sign(sk, msg), 5), verify_ms=timeit(lambda: ML_DSA_44.verify(pk, msg, sig), 5)))
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes
    k = ec.generate_private_key(ec.SECP256K1()); sig = k.sign(msg, ec.ECDSA(hashes.SHA256()))
    rows.append(dict(alg="ECDSA-secp256k1 (classical baseline)", backend="cryptography", pk=64, sig=64,
                     keygen_ms=None, sign_ms=timeit(lambda: k.sign(msg, ec.ECDSA(hashes.SHA256())), reps),
                     verify_ms=timeit(lambda: k.public_key().verify(sig, msg, ec.ECDSA(hashes.SHA256())), reps)))
    for r in rows:
        print(f"{r['alg']:<40}{r['backend']:<14} pk={r['pk']:>5}B sig={r['sig']:>6}B "
              f"sign={r['sign_ms']:.3f}ms verify={r['verify_ms']:.3f}ms")
    (OUT / "bench_sigs.json").write_text(json.dumps(rows, indent=2))


def bench_detect(trials=300, n=8, dim=1024, trim=2):
    rng = random.Random(1)
    vals = [[rng.randint(-10**6, 10**6) for _ in range(dim)] for _ in range(n)]
    trees = [MerkleTree([__import__("verapq.hashing", fromlist=["x"]).leaf_value(v, j) for j, v in enumerate(row)]) for row in vals]
    good = [P.trimmed_mean_int([vals[i][j] for i in range(n)], trim) for j in range(dim)]
    res = []
    for m in (1, 10, 50):
        for k in (8, 32, 128):
            hits = 0
            for tr in range(trials):
                bad = set(rng.sample(range(dim), m))
                seed = keccak(f"{m}-{k}-{tr}".encode())
                hits += any(P.sample_index(seed, t, dim) in bad for t in range(k))
            res.append(dict(dim=dim, tampered=m, k=k, empirical=hits / trials, analytic=P.detection_probability(dim, m, k)))
            print(f"dim={dim} tampered={m:>3} k={k:>3}  empirical={hits/trials:.3f}  analytic={res[-1]['analytic']:.3f}")
    (OUT / "bench_detect.json").write_text(json.dumps(res, indent=2))


def bench_gas():
    from verapq.ledger_evm import EvmLedger
    from verapq.pqsig import Signer
    L = EvmLedger(); rows = []; rid = 0
    signers = {}
    L.deposit_stake(1000 * 10 ** 18); L.fund_rewards(100 * 10 ** 18)
    econ_gas = dict(deploy=L.gas["deploy"], depositStake=L.gas["stake"][0], fundRewards=L.gas["fund"][0])
    for n in (4, 8, 16):
        for dim in (32, 1024):
            for k in (4, 16, 32):
                warm = (dim, k) == (32, 4)  # one unrecorded round per n so new devices' credit slots exist
                for _ in range(2 if warm else 1):
                  rid += 1; rng = random.Random(rid); ups = []
                  for cid in range(1, n + 1):
                    if cid not in signers:
                        signers[cid] = Signer(); L.register_device(cid, keccak(signers[cid].pk))
                        L.set_payout(cid, L.w3.to_checksum_address(keccak(b"dev%d" % cid)[:20]))
                    ups.append(P.client_prepare(signers[cid], rid, cid, [rng.randint(-10**6, 10**6) for _ in range(dim)]))
                  trim = max(1, n // 4)
                  rc = P.gateway_aggregate(ups, L.registry, trim, k)
                  L.commit_round(rid, rc.client_tree.root, rc.agg_tree.root, n, dim, trim, k)
                  ok, _, gas = L.audit(rid, *P.build_audit(rc, L.challenge_seed(rid)))
                  if warm:
                      warm = False; continue
                  rows.append(dict(n=n, dim=dim, k=k, accepted=ok, audit_gas=gas, commit_gas=L.gas["commit"][-1],
                                   calldata_est=P.audit_calldata_bytes(n, dim, k)))
                  print(rows[-1])
    (OUT / "bench_gas.json").write_text(json.dumps(rows, indent=2))
    # economics: a rejected audit (slash) and an expired round (keeper bounty), n=8, d=32, k=16
    for mode in ("tamper", "expire"):
        rid += 1; rng = random.Random(rid)
        ups = [P.client_prepare(signers[c], rid, c, [rng.randint(-10**6, 10**6) for _ in range(32)]) for c in range(1, 9)]
        rc = P.gateway_aggregate(ups, L.registry, 2, 16, mode="tamper", tamper_frac=1.0, rng=rng)
        L.commit_round(rid, rc.client_tree.root, rc.agg_tree.root, 8, 32, 2, 16)
        if mode == "tamper":
            ok, _, gas = L.audit(rid, *P.build_audit(rc, L.challenge_seed(rid))); econ_gas["audit_rejected_slash"] = gas
        else:
            econ_gas["expire_with_bounty"] = L.expire(rid).gasUsed
    econ_gas["claim"] = L.claim(L.acct).gasUsed
    econ_gas["commit_with_bond"] = L.gas["commit"][-1]
    print(econ_gas)
    (OUT / "bench_econ_gas.json").write_text(json.dumps(econ_gas, indent=2))


if __name__ == "__main__":
    {"sigs": bench_sigs, "detect": bench_detect, "gas": bench_gas}[sys.argv[1] if len(sys.argv) > 1 else "sigs"]()
