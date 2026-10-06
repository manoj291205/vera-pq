"""Pure-Python simulated ledger (no node needed). Mirrors VeraPQLedger.sol state machine:
register -> commit (block b) -> seed = keccak(blockhash(b) | clientRoot | aggRoot | roundId) -> audit.
Gas is NOT measured here (use the EVM backend for gas).
Also mirrors the crypto-economic layer (bond / reward / slash, amounts in wei) exactly."""
import time
from .hashing import keccak, u256
from . import protocol as P

ETH = 10 ** 18
GATEWAY_SHARE_BPS, KEEPER_BPS = 5000, 1000


class SimLedger:
    def __init__(self, bond=ETH, round_reward=ETH // 10):
        self.blocks = [keccak(b"genesis")]
        self.registry, self.alg, self.rounds, self.events = {}, {}, {}, []
        self.bond, self.round_reward = bond, round_reward
        self.stake, self.locked, self.credit, self.payout = {}, {}, {}, {}
        self.reward_pool = 0
        self.sender = "gateway"

    # ---- crypto-economic layer (mirrors VeraPQLedger.sol) ----
    def deposit_stake(self, amount, who="gateway"):
        self.stake[who] = self.stake.get(who, 0) + amount

    def fund_rewards(self, amount):
        self.reward_pool += amount

    def set_payout(self, cid, addr):
        self.payout[cid] = addr

    def _reward(self, rid, gw, client_ids):
        self.locked[gw] -= self.bond
        pay = min(self.round_reward, self.reward_pool); self.reward_pool -= pay
        g = pay * GATEWAY_SHARE_BPS // 10000; each = (pay - g) // len(client_ids)
        self.credit[gw] = self.credit.get(gw, 0) + g
        for cid in client_ids:
            to = self.payout.get(cid)
            if to is None: self.reward_pool += each
            else: self.credit[to] = self.credit.get(to, 0) + each
        self.reward_pool += (pay - g) - each * len(client_ids)
        self.events.append(("Rewarded", rid, gw, g, each))

    def _slash(self, rid, gw, keeper=None):
        self.locked[gw] -= self.bond; self.stake[gw] -= self.bond
        bounty = 0 if keeper is None else self.bond * KEEPER_BPS // 10000
        if keeper is not None: self.credit[keeper] = self.credit.get(keeper, 0) + bounty
        self.reward_pool += self.bond - bounty
        self.events.append(("Slashed", rid, gw, self.bond, keeper, bounty))

    def settle_unchecked(self, rid, client_ids):
        """Baseline only: a ledger that trusts the gateway pays the reward without auditing."""
        self.rounds[rid]["status"] = "accepted-unchecked"
        self._reward(rid, self.rounds[rid]["gw"], client_ids)

    def expire(self, rid, keeper="keeper"):
        R = self.rounds[rid]
        for _ in range(257):
            self._mine(b"tick")                     # 256-block challenge window passes unanswered
        assert R["status"] == "committed" and len(self.blocks) - 1 > R["block"] + 256, "not expired"
        R["status"] = "rejected"; self.events.append(("RoundAudited", rid, False, "expired"))
        self._slash(rid, R["gw"], keeper)

    def econ(self, gw="gateway"):
        return dict(stake=self.stake.get(gw, 0), locked=self.locked.get(gw, 0), credit=self.credit.get(gw, 0),
                    pool=self.reward_pool, device_credit=sum(v for k, v in self.credit.items() if k not in (gw, "keeper")))

    def _mine(self, payload: bytes):
        self.blocks.append(keccak(self.blocks[-1] + payload + str(time.time_ns()).encode()))
        return len(self.blocks) - 1

    def register_device(self, cid, pk_hash, alg=1):
        self.registry[cid], self.alg[cid] = pk_hash, alg
        self._mine(b"reg" + u256(cid) + pk_hash)

    def commit_round(self, rid, client_root, agg_root, n, dim, trim, k):
        assert rid == len(self.rounds) + 1 and n > 2 * trim, "sequential round ids"
        assert rid == 1 or self.rounds[rid - 1]["status"] != "committed", "previous round unresolved"
        gw = self.sender
        assert self.stake.get(gw, 0) - self.locked.get(gw, 0) >= self.bond, "insufficient stake"
        self.locked[gw] = self.locked.get(gw, 0) + self.bond
        b = self._mine(b"commit" + u256(rid) + client_root + agg_root)
        self.rounds[rid] = dict(client_root=client_root, agg_root=agg_root, n=n, dim=dim, trim=trim, k=k,
                                block=b, status="committed", gw=gw)
        return b

    def challenge_seed(self, rid):
        R = self.rounds[rid]
        if len(self.blocks) - 1 <= R["block"]:
            self._mine(b"tick")  # challenge only after the commit block is sealed
        return keccak(self.blocks[R["block"]] + R["client_root"] + R["agg_root"] + u256(rid))

    def audit(self, rid, clients, samples, sig_opening=None):
        R = self.rounds[rid]
        if sig_opening is not None and not P.verify_sig_opening(self.challenge_seed(rid), rid, clients,
                                                                self.registry, sig_opening):
            R["status"] = "rejected"; self.events.append(("RoundAudited", rid, False, "sig"))
            self._slash(rid, R["gw"])
            return False, "sig", None
        ok, failed = P.verify_audit(self.challenge_seed(rid), R["client_root"], R["agg_root"], R["n"], R["dim"],
                                    R["trim"], R["k"], self.registry, clients, samples)
        R["status"] = "accepted" if ok else "rejected"
        self.events.append(("RoundAudited", rid, ok, failed))
        if ok: self._reward(rid, R["gw"], [c[0] for c in clients])
        else: self._slash(rid, R["gw"])
        self._mine(b"audit" + u256(rid))
        return ok, failed, None  # (accepted, failed_sample, gas)
