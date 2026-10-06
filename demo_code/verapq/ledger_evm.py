"""Optional EVM backend: compiles contracts/VeraPQLedger.sol with solcjs (npm) and deploys it to an
in-process py-evm chain via web3 EthereumTesterProvider. Reports real gas used per transaction.

Requirements: `pip install "eth-tester[py-evm]" web3` and `npm install solc@0.8.26` (solcjs).
Point VERAPQ_SOLCJS at the solcjs binary if it is not on PATH. Same contract runs on Hardhat/anvil.
"""
import json, os, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SOL = HERE / "contracts" / "VeraPQLedger.sol"


def _solcjs():
    p = os.environ.get("VERAPQ_SOLCJS") or shutil.which("solcjs")
    if not p:
        raise RuntimeError("solcjs not found: run `npm install solc@0.8.26` and set VERAPQ_SOLCJS")
    return p


def compile_contract():
    std = {"language": "Solidity", "sources": {"VeraPQLedger.sol": {"content": SOL.read_text()}},
           "settings": {"optimizer": {"enabled": True, "runs": 200}, "viaIR": True, "evmVersion": "cancun",
                        "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}}}
    out = subprocess.run([_solcjs(), "--standard-json"], input=json.dumps(std), capture_output=True,
                         text=True, check=True).stdout
    out = json.loads(out[out.index("{"):])
    errs = [e for e in out.get("errors", []) if e["severity"] == "error"]
    if errs:
        raise RuntimeError(errs[0]["formattedMessage"])
    c = out["contracts"]["VeraPQLedger.sol"]["VeraPQLedger"]
    return c["abi"], c["evm"]["bytecode"]["object"]


ETH = 10 ** 18


class EvmLedger:
    def __init__(self, bond=ETH, round_reward=ETH // 10):
        from web3 import Web3, EthereumTesterProvider
        self.w3 = Web3(EthereumTesterProvider())
        self.acct = self.w3.eth.accounts[0]          # owner + gateway
        self.keeper = self.w3.eth.accounts[9]
        self.bond, self.round_reward = bond, round_reward
        abi, bc = compile_contract()
        tx = self.w3.eth.contract(abi=abi, bytecode=bc).constructor(bond, round_reward).transact({"from": self.acct})
        rcpt = self.w3.eth.wait_for_transaction_receipt(tx)
        self.c = self.w3.eth.contract(address=rcpt.contractAddress, abi=abi)
        self.gas = {"deploy": rcpt.gasUsed}
        self.registry = {}

    def _tx(self, fn, label, gas=29_000_000, value=0, sender=None):
        h = fn.transact({"from": sender or self.acct, "gas": gas, "value": value})
        r = self.w3.eth.wait_for_transaction_receipt(h)
        self.gas.setdefault(label, []).append(r.gasUsed) if label != "deploy" else None
        return r

    def register_device(self, cid, pk_hash, alg=1):
        self.registry[cid] = pk_hash
        self._tx(self.c.functions.registerDevice(cid, pk_hash, alg), "register")

    def commit_round(self, rid, client_root, agg_root, n, dim, trim, k):
        r = self._tx(self.c.functions.commitRound(rid, client_root, agg_root, n, dim, trim, k), "commit")
        return r.blockNumber

    def challenge_seed(self, rid):
        if self.w3.eth.block_number <= self.c.functions.rounds(rid).call()[6]:
            self.w3.provider.ethereum_tester.mine_blocks(1)
        return bytes(self.c.functions.challengeSeed(rid).call())

    def audit(self, rid, clients, samples):
        cs = [(cid, root, sd, list(path)) for cid, root, sd, path in clients]
        ss = [(av, list(ap), list(vals), [list(p) for p in paths]) for av, ap, vals, paths in samples]
        r = self._tx(self.c.functions.audit(rid, cs, ss), "audit")
        from web3.logs import DISCARD  # receipt also carries Rewarded/Slashed logs
        ev = self.c.events.RoundAudited().process_receipt(r, errors=DISCARD)[0]["args"]
        failed = None if ev["accepted"] else ev["failedSample"]
        return ev["accepted"], failed, r.gasUsed

    # ---- crypto-economic layer ----
    def deposit_stake(self, amount, who=None):
        self._tx(self.c.functions.depositStake(), "stake", value=amount)

    def fund_rewards(self, amount):
        self._tx(self.c.functions.fundRewards(), "fund", value=amount)

    def set_payout(self, cid, addr):
        self._tx(self.c.functions.setPayout(cid, addr), "payout")

    def expire(self, rid, keeper=None):
        self.w3.provider.ethereum_tester.mine_blocks(257)
        return self._tx(self.c.functions.expire(rid), "expire", sender=self.keeper)

    def claim(self, who):
        return self._tx(self.c.functions.claim(), "claim", sender=who)

    def econ(self, gw=None):
        gw = gw or self.acct; f = self.c.functions
        dev = sum(f.credit(f.payout(cid).call()).call() for cid in self.registry if f.payout(cid).call() != "0x" + "0" * 40)
        return dict(stake=f.stake(gw).call(), locked=f.locked(gw).call(), credit=f.credit(gw).call(),
                    pool=f.rewardPool().call(), device_credit=dev)
