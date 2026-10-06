"""Run: python -m pytest -q test_verapq.py   (or: python test_verapq.py)"""
import random
from verapq import protocol as P, pqsig
from verapq.hashing import keccak
from verapq.ledger_sim import SimLedger


ETH = 10 ** 18


def _ledger():
    L = SimLedger(bond=ETH, round_reward=ETH // 10)
    L.deposit_stake(10 * ETH); L.fund_rewards(5 * ETH)
    return L


def _setup(n=6, dim=16, trim=1, k=8, mode="honest", frac=0.0):
    L = _ledger(); rng = random.Random(3); ups = []
    for cid in range(1, n + 1):
        s = pqsig.Signer(); L.register_device(cid, keccak(s.pk)); L.set_payout(cid, f"device-{cid}")
        ups.append(P.client_prepare(s, 1, cid, [rng.randint(-1000, 1000) for _ in range(dim)]))
    rc = P.gateway_aggregate(ups, L.registry, trim, k, mode=mode, tamper_frac=frac, rng=rng)
    L.commit_round(1, rc.client_tree.root, rc.agg_tree.root, rc.n, rc.dim, trim, k)
    return L, rc, ups


def test_honest_accepts():
    L, rc, _ = _setup()
    assert L.audit(1, *P.build_audit(rc, L.challenge_seed(1)))[0]


def test_full_tamper_rejected():
    L, rc, _ = _setup(mode="tamper", frac=1.0)
    assert not L.audit(1, *P.build_audit(rc, L.challenge_seed(1)))[0]


def test_forged_signature_dropped():
    L, rc, ups = _setup()
    ups[0].sig = bytes(len(ups[0].sig))
    rc2 = P.gateway_aggregate(ups, L.registry, 1, 8)
    assert ups[0].client_id in rc2.rejected_ids


def test_substituted_value_reverts():
    L, rc, _ = _setup()
    clients, samples = P.build_audit(rc, L.challenge_seed(1))
    av, ap, vals, paths = samples[0]
    vals = list(vals); vals[0] += 1  # gateway lies about a client's committed value
    samples[0] = (av, ap, vals, paths)
    try:
        L.audit(1, clients, samples); assert False, "should revert"
    except P.AuditReverted:
        pass


def test_values_not_matching_signed_root_dropped():
    L, rc, ups = _setup()
    ups[1].values = list(ups[1].values); ups[1].values[0] += 7  # values altered after signing
    rc2 = P.gateway_aggregate(ups, L.registry, 1, 8)
    assert ups[1].client_id in rc2.rejected_ids


def test_sig_spotcheck_detects_forged_client():
    """Gateway fabricates every client's update with a junk signature but a self-consistent sigDigest:
    Merkle checks pass, only the ML-DSA spot-check catches it."""
    L, rc, ups = _setup()
    from verapq.merkle import MerkleTree
    from verapq.hashing import leaf_client
    for u in rc.accepted:
        u.sig = bytes(len(u.sig))
    rc.client_tree = MerkleTree([leaf_client(u.client_id, u.root, u.sig_digest) for u in rc.accepted])
    L2 = _ledger(); L2.registry = L.registry
    L2.commit_round(1, rc.client_tree.root, rc.agg_tree.root, rc.n, rc.dim, rc.trim, rc.k)
    seed = L2.challenge_seed(1)
    clients, samples = P.build_audit(rc, seed)
    assert P.verify_audit(seed, rc.client_tree.root, rc.agg_tree.root, rc.n, rc.dim, rc.trim, rc.k,
                          L2.registry, clients, samples)[0]          # hash-only audit alone passes
    assert not L2.audit(1, clients, samples, P.build_sig_opening(rc, seed))[0]  # spot-check rejects


def test_honest_round_pays_gateway_and_devices():
    L, rc, _ = _setup()
    assert L.audit(1, *P.build_audit(rc, L.challenge_seed(1)))[0]
    e = L.econ()
    assert e["stake"] == 10 * ETH and e["locked"] == 0              # bond released, nothing slashed
    each = (ETH // 20) // 6                                          # devices' half split 6 ways
    assert e["credit"] == ETH // 20 and e["device_credit"] == 6 * each  # 0.1 ETH split 50/50
    assert e["pool"] == 5 * ETH - ETH // 20 - 6 * each                 # rounding dust stays in pool


def test_cheating_round_slashes_bond():
    L, rc, _ = _setup(mode="tamper", frac=1.0)
    assert not L.audit(1, *P.build_audit(rc, L.challenge_seed(1)))[0]
    e = L.econ()
    assert e["stake"] == 9 * ETH and e["credit"] == 0 and e["pool"] == 6 * ETH


def test_withheld_round_expires_with_keeper_bounty():
    L, rc, _ = _setup()
    L.expire(1, keeper="keeper")
    assert L.econ()["stake"] == 9 * ETH and L.credit["keeper"] == ETH // 10


def test_commit_needs_unbonded_stake():
    L = SimLedger(bond=ETH); L.deposit_stake(ETH // 2)
    try:
        L.commit_round(1, b"\0" * 32, b"\0" * 32, 6, 16, 1, 8); assert False, "should need stake"
    except AssertionError as ex:
        assert "insufficient stake" in str(ex)


if __name__ == "__main__":
    for f in [test_honest_accepts, test_full_tamper_rejected, test_forged_signature_dropped, test_substituted_value_reverts,
              test_values_not_matching_signed_root_dropped, test_sig_spotcheck_detects_forged_client,
              test_honest_round_pays_gateway_and_devices, test_cheating_round_slashes_bond,
              test_withheld_round_expires_with_keeper_bounty, test_commit_needs_unbonded_stake]:
        f(); print("PASS", f.__name__)
