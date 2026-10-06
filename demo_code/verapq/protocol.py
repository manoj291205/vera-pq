"""VERA-PQ protocol core: client commitment + PQ signature, gateway robust aggregation,
ledger-beacon-challenged hash-only audit (build + verify).

All verification here uses only Keccak-256 (hash-based, no pairings / no discrete log),
mirroring contracts/VeraPQLedger.sol exactly.
"""
from dataclasses import dataclass, field
from typing import Dict, List
import random

from .hashing import keccak, u256, leaf_value, leaf_client, round_message
from .merkle import MerkleTree, verify_path
from . import pqsig

SCALE = 10**6  # fixed-point scale for model parameters


class AuditReverted(Exception):
    """Malformed / unauthenticated opening (contract would revert)."""


def ceil_log2(x: int) -> int:
    d = 0
    while (1 << d) < x:
        d += 1
    return d


def quantize(vec) -> List[int]:
    return [int(round(float(x) * SCALE)) for x in vec]


def trimmed_mean_int(vals: List[int], trim: int) -> int:
    """Coordinate-wise trimmed mean with Solidity int256 semantics (truncate toward zero)."""
    s = sorted(vals)
    mid = s[trim:len(s) - trim]
    tot, c = sum(mid), len(mid)
    q = abs(tot) // c
    return q if tot >= 0 else -q


def sample_index(seed: bytes, t: int, dim: int) -> int:
    return int.from_bytes(keccak(seed + u256(t)), "big") % dim


# ---------------------------------------------------------------- client side
@dataclass
class SignedUpdate:
    round_id: int
    client_id: int
    values: List[int]
    tree: MerkleTree
    root: bytes
    sig: bytes
    pk: bytes

    @property
    def sig_digest(self) -> bytes:
        return keccak(self.sig)


def client_prepare(signer: "pqsig.Signer", round_id: int, client_id: int, values: List[int]) -> SignedUpdate:
    """IoT client: commit to its quantized update with a Merkle root and sign (round,id,root) with ML-DSA.
    The client signs a 32-byte digest, never the full vector, so signing cost is independent of model size."""
    tree = MerkleTree([leaf_value(v, j) for j, v in enumerate(values)])
    sig = signer.sign(round_message(round_id, client_id, tree.root))
    return SignedUpdate(round_id, client_id, list(values), tree, tree.root, sig, signer.pk)


# ---------------------------------------------------------------- gateway side
@dataclass
class RoundCommitment:
    round_id: int
    accepted: List[SignedUpdate]
    rejected_ids: List[int]
    agg: List[int]
    agg_tree: MerkleTree
    client_tree: MerkleTree
    trim: int
    k: int

    @property
    def dim(self):
        return len(self.agg)

    @property
    def n(self):
        return len(self.accepted)


def gateway_aggregate(updates: List[SignedUpdate], registry: Dict[int, bytes], trim: int, k: int,
                      mode: str = "honest", tamper_frac: float = 0.0, rng=None) -> RoundCommitment:
    """Edge gateway: verify ML-DSA signatures against the on-ledger key registry, run coordinate-wise
    trimmed mean, and build the two commitments (client-set root, aggregate root).

    mode: honest | lazy (plain mean, i.e. skips robust aggregation) | tamper (alters a fraction of coordinates)
    """
    rng = rng or random.Random(0)
    ok, bad = [], []
    for u in sorted(updates, key=lambda x: x.client_id):
        if registry.get(u.client_id) != keccak(u.pk):
            bad.append(u.client_id)
            continue
        if not pqsig.verify(u.pk, round_message(u.round_id, u.client_id, u.root), u.sig):
            bad.append(u.client_id)
            continue
        # recompute the client's commitment from the received values (binds values to the signed root)
        u.tree = MerkleTree([leaf_value(v, j) for j, v in enumerate(u.values)])
        if u.tree.root != u.root:
            bad.append(u.client_id)
            continue
        ok.append(u)
    n, dim = len(ok), len(ok[0].values)
    assert n > 2 * trim, "need n > 2*trim"
    cols = [[u.values[j] for u in ok] for j in range(dim)]
    if mode == "lazy":
        agg = [int(sum(c) / len(c)) for c in cols]
    else:
        agg = [trimmed_mean_int(c, trim) for c in cols]
    if mode == "tamper":
        m = max(1, int(round(tamper_frac * dim)))
        for j in rng.sample(range(dim), m):
            agg[j] += 5 * SCALE  # inject a large shift into a few coordinates
    agg_tree = MerkleTree([leaf_value(v, j) for j, v in enumerate(agg)])
    client_tree = MerkleTree([leaf_client(u.client_id, u.root, u.sig_digest) for u in ok])
    return RoundCommitment(updates[0].round_id, ok, bad, agg, agg_tree, client_tree, trim, k)


def build_audit(rc: RoundCommitment, seed: bytes):
    """Gateway answers the ledger-derived challenge with Merkle openings for k sampled coordinates."""
    clients = [(u.client_id, u.root, u.sig_digest, rc.client_tree.proof(i)) for i, u in enumerate(rc.accepted)]
    samples = []
    for t in range(rc.k):
        j = sample_index(seed, t, rc.dim)
        samples.append((rc.agg[j], rc.agg_tree.proof(j),
                        [u.values[j] for u in rc.accepted],
                        [u.tree.proof(j) for u in rc.accepted]))
    return clients, samples


def verify_audit(seed: bytes, client_root: bytes, agg_root: bytes, n: int, dim: int, trim: int, k: int,
                 registry: Dict[int, bytes], clients, samples):
    """Python mirror of VeraPQLedger.audit. Returns (accepted, failed_sample_index or None).
    Raises AuditReverted for malformed/unauthenticated openings."""
    dc, dd = ceil_log2(n), ceil_log2(dim)
    if len(clients) != n or len(samples) != k:
        raise AuditReverted("shape")
    for i, (cid, uroot, sdig, path) in enumerate(clients):
        if i > 0 and cid <= clients[i - 1][0]:
            raise AuditReverted("order")
        if cid not in registry:
            raise AuditReverted("unregistered")
        if len(path) != dc or not verify_path(leaf_client(cid, uroot, sdig), i, path, client_root):
            raise AuditReverted("client path")
    for t, (aval, apath, vals, paths) in enumerate(samples):
        j = sample_index(seed, t, dim)
        if len(vals) != n:
            raise AuditReverted("width")
        for i in range(n):
            if len(paths[i]) != dd or not verify_path(leaf_value(vals[i], j), j, paths[i], clients[i][1]):
                raise AuditReverted("value path")
        if len(apath) != dd or not verify_path(leaf_value(aval, j), j, apath, agg_root):
            raise AuditReverted("agg path")
        if trimmed_mean_int(vals, trim) != aval:
            return False, t  # provable mis-aggregation -> round rejected
    return True, None


def audit_calldata_bytes(n: int, dim: int, k: int) -> int:
    """Approximate ABI payload size of the audit transaction (dominant terms)."""
    dc, dd = ceil_log2(n), ceil_log2(dim)
    clients = n * (32 * 3 + 32 * dc + 64)
    samples = k * (32 + 32 * dd + 64 + n * 32 + 64 + n * (32 * dd + 64) + 64)
    return clients + samples


def detection_probability(dim: int, tampered: int, k: int) -> float:
    """P[at least one of k uniform (with replacement) samples hits a tampered coordinate]."""
    return 1.0 - (1.0 - tampered / dim) ** k


# ---------------------------------------------------------------- signature spot-check (dependent-claim feature)
def sig_spotcheck_index(seed: bytes, n: int) -> int:
    """Ledger picks one accepted client per round, from the same unpredictable seed."""
    return int.from_bytes(keccak(b"VERA-PQ/sigcheck" + seed), "big") % n


def build_sig_opening(rc: RoundCommitment, seed: bytes):
    u = rc.accepted[sig_spotcheck_index(seed, rc.n)]
    return u.client_id, u.root, u.pk, u.sig


def verify_sig_opening(seed: bytes, round_id: int, clients, registry, opening) -> bool:
    """Checks: selected index matches seed; pk matches registry hash; keccak(sig) matches committed sigDigest;
    ML-DSA verifies over the round message. Needs an ML-DSA verifier on the ledger (precompile, e.g. EIP-8051
    draft, or a PQ-native chain); in the EVM demo this check is NOT executed on-chain."""
    i = sig_spotcheck_index(seed, len(clients))
    cid, root, sdig, _ = clients[i]
    ocid, oroot, pk, sig = opening
    return (ocid == cid and oroot == root and registry.get(cid) == keccak(pk) and keccak(sig) == sdig
            and pqsig.verify(pk, round_message(round_id, cid, root), sig))
