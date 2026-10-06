#!/usr/bin/env bash
# Demo-day script: honest -> attacked-without-audit -> attacked-with-audit (slashed) -> withheld (expired),
# then the EVM path if available. Every run prints the gateway's ETH stake and the rewards paid.
set -e
cd "$(dirname "$0")"
echo "== 1. Honest gateway, 2/8 poisoned clients: every round ACCEPTED, gateway + devices earn ETH =="
python3 run_demo.py --rounds 5 --out results/demo_honest.json
echo "== 2. Lazy gateway (plain mean) WITHOUT audit: poisoned model accepted AND the cheater is paid =="
python3 run_demo.py --rounds 5 --gateway lazy --no-audit --out results/demo_lazy_noaudit.json
echo "== 3. Lazy gateway WITH audit: rounds REJECTED, 1 ETH bond slashed per round =="
python3 run_demo.py --rounds 5 --gateway lazy --out results/demo_lazy_audit.json
echo "== 4. Tampering gateway (10% coords) WITH audit =="
python3 run_demo.py --rounds 5 --gateway tamper --tamper-frac 0.1 --out results/demo_tamper.json
echo "== 5. Gateway refuses to answer the challenge: a keeper expires the round, earns a 10% bounty =="
python3 run_demo.py --rounds 3 --gateway lazy --withhold --out results/demo_withhold.json
if python3 -c "import web3, eth_tester" 2>/dev/null && { [ -n "$VERAPQ_SOLCJS" ] || command -v solcjs >/dev/null; }; then
  echo "== 6. Same flow on in-process EVM (real ETH balances, real gas) =="
  python3 run_demo.py --ledger evm --rounds 3 --out results/demo_evm.json
  python3 run_demo.py --ledger evm --rounds 2 --gateway lazy --out results/demo_evm_slash.json
fi
python3 test_verapq.py
