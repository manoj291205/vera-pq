# VERA-PQ demo (course project)

**CONFIDENTIAL. Keep this repository PRIVATE until a patent application is filed.**

Verifiable Edge Robust Aggregation with Post-Quantum, hash-only attestation for blockchain-anchored
federated learning on IoT. Author: Manojkumar Ashokkumar.

## Install (pure-Python path, always works)
    pip install numpy scikit-learn dilithium-py pycryptodome
    python run_demo.py

## Fast PQC (optional, liboqs)
    pip install liboqs-python
    # liboqs-python tries to auto-build liboqs on first import (slow, needs git+cmake).
    # A faster minimal build:
    git clone --depth 1 --branch 0.15.0 https://github.com/open-quantum-safe/liboqs
    cmake -S liboqs -B build -GNinja -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON \
      -DOQS_MINIMAL_BUILD="SIG_ml_dsa_44;SIG_ml_dsa_65;SIG_falcon_512;SIG_sphincs_sha2_128f_simple;KEM_ml_kem_768" \
      -DCMAKE_INSTALL_PREFIX=$HOME/_oqs && ninja -C build install
    export OQS_INSTALL_PATH=$HOME/_oqs

Force a backend with `VERAPQ_PQ_BACKEND=pure|liboqs`. Algorithm: `VERAPQ_PQ_ALG=ML-DSA-44|ML-DSA-65`.

## On-chain path (optional, real gas)
    pip install web3 "eth-tester[py-evm]"
    npm install solc@0.8.26 && export VERAPQ_SOLCJS=$PWD/node_modules/.bin/solcjs
    python run_demo.py --ledger evm
The same `contracts/VeraPQLedger.sol` deploys unchanged on Hardhat/anvil.

## Crypto-economics (staking, slashing, rewards)
`VeraPQLedger.sol` is also an incentive contract, paid in ETH:
- The gateway calls `depositStake()` and must have `bond` (default 1 ETH) of unlocked stake to commit a round.
- **Accepted audit:** bond released; `roundReward` (default 0.1 ETH) from the reward pool is credited 50% to
  the gateway and 50% split across the round's devices (via `setPayout`).
- **Rejected audit:** bond slashed into the reward pool.
- **No answer within 256 blocks:** anyone calls `expire()`, the bond is slashed and the caller gets a 10% bounty.
- Payments are pull-based (`credit` + `claim()`), so settlement never makes an external call.

Flags: `--bond --reward --deposit --pool --withhold`. Gas: `python bench.py gas` also writes
`results/bench_econ_gas.json` (commit with bond, slash, expire, claim).

## Demo day
    ./run_all.sh
    python bench.py sigs | detect | gas
    python test_verapq.py
