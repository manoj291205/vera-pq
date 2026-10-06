# VERA-PQ: complete runbook (from today to submission)

**CONFIDENTIAL.** Keep this folder and its GitHub repository private until VIT's IPR&TT Cell has decided on a patent filing.

Folder layout after unzipping:

```
VERA-PQ_project/
  RUNBOOK.md            <- this file
  demo_code/            <- protocol, contract, demo, experiments, tests
  paper/                <- VERA-PQ_IEEE_paper.docx (+ .pdf preview), make_figures.py, build_paper.js, figs/
```

---

## Step 0: Today, before anything is shown to anyone (about 30 min)

1. Email VIT's IPR&TT Cell and ask whether they can file an Indian **provisional** application before the 9 Oct demo. Attach Sections 4.4–4.5 of the research report (the invention disclosure and the draft claims).
2. If they cannot file before 9 Oct, ask the evaluators whether the demo can be closed (evaluators only), and do not post anything online.
3. Ask the IPR Cell who must be named as inventor. Inventors are the people who contributed to the *conception* of the claimed idea, which is a different test from authorship; if anyone else (for example your faculty guide) contributed to the idea, they may need to be named.
4. Keep the GitHub repository **private**. Do not upload to arXiv, LinkedIn, YouTube or Discord.
5. Upload to Turnitin only after you have heard back from the IPR Cell, if you can wait that long.

---

## Step 1: Set up a laptop (about 15 min)

**Windows:** use WSL2 with Ubuntu 22.04 or 24.04 (`wsl --install` in an admin PowerShell, then reboot). Native Windows also works for the pure-Python path. **Mac and Linux:** use a normal terminal.

You need Python 3.10–3.13, git, and (only for the on-chain demo) Node.js 18 or later.

```bash
cd VERA-PQ_project/demo_code
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install numpy scikit-learn pandas matplotlib dilithium-py pycryptodome
python test_verapq.py              # expect 10 lines starting with PASS
python run_demo.py --rounds 5      # honest gateway: every round "audit=ACCEPT", accuracy ~0.89, gateway earns ETH
```

If both commands work, the core demo works. Everything below is optional polish.

---

## Step 2 (optional, recommended): fast post-quantum signatures with liboqs (about 15 min; Linux, WSL or Mac)

```bash
sudo apt install -y cmake ninja-build build-essential git       # Mac: brew install cmake ninja
git clone --depth 1 --branch 0.15.0 https://github.com/open-quantum-safe/liboqs
cmake -S liboqs -B build -GNinja -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON \
  -DOQS_MINIMAL_BUILD="SIG_ml_dsa_44;SIG_ml_dsa_65;SIG_falcon_512;SIG_sphincs_sha2_128f_simple;KEM_ml_kem_768" \
  -DCMAKE_INSTALL_PREFIX=$HOME/_oqs
ninja -C build install
export OQS_INSTALL_PATH=$HOME/_oqs                              # add this line to ~/.bashrc
pip install liboqs-python
python -c "import oqs; print(oqs.get_enabled_sig_mechanisms()[:4])"
```

Without liboqs, the code falls back to the pure-Python ML-DSA automatically. It is about 500× slower but gives identical protocol results. To force a backend, set `VERAPQ_PQ_BACKEND=pure` or `VERAPQ_PQ_BACKEND=liboqs`.

---

## Step 3 (optional): on-chain path with real gas (about 10 min)

```bash
pip install web3 "eth-tester[py-evm]"
npm install solc@0.8.26
export VERAPQ_SOLCJS=$PWD/node_modules/.bin/solcjs
python run_demo.py --ledger evm --rounds 3     # expect audit=ACCEPT, gas of about 1.4M per round, ETH rewards credited
python run_demo.py --ledger evm --rounds 2 --gateway lazy   # expect REJECT and stake 10 -> 8 ETH
```

`contracts/VeraPQLedger.sol` deploys unchanged on Hardhat or Anvil if an evaluator asks to see it in Remix. That route has not been tested; the in-process EVM is the tested path.

---

## Step 4: Put the code in a private GitHub repository (about 5 min)

```bash
cd VERA-PQ_project
printf ".venv/\nnode_modules/\n__pycache__/\n*.pyc\nliboqs/\nbuild/\n" > .gitignore
git init && git add . && git commit -m "VERA-PQ prototype and paper sources"
# create a PRIVATE repo on github.com, then:
git remote add origin https://github.com/<your-username>/vera-pq.git
git branch -M main && git push -u origin main
```

Keep the repository private.

---

## Step 5: Re-run the experiments on your own machine (about 15 min)

The numbers in the paper were measured on a 2-vCPU cloud Xeon. Re-running on your laptop lets you report your own hardware. `python bench.py gas` also writes `results/bench_econ_gas.json` (gas for staking, slashing, expiry and claims).

```bash
cd demo_code
python experiments.py E1                  # accuracy table -> results/exp_E1.csv     (~3 min)
E2_SEEDS=100 python experiments.py E2     # detection rate -> results/exp_E2.csv     (~5 min)
python experiments.py E3                  # overhead       -> results/exp_E3.csv     (~2 min)
python bench.py sigs                      # signature table -> results/bench_sigs.json
python bench.py gas                       # gas sweep (needs Step 3) -> results/bench_gas.json
cd ../paper && python make_figures.py     # regenerates figs/*.png from your results
```

Then update the paper in Word:

- **Tables III–V and the gas numbers in Sections VII-A to VII-E:** copy the new values in by hand from the CSV and JSON files. Alternatively, send the files back and have them updated for you.
- **Figures:** replace each image with the regenerated `figs/fig3_accuracy.png`, `figs/fig4_detection.png` and `figs/fig5_gas.png` (right-click the image, then Change Picture).
- **Hardware line at the end of Section VI-A:** replace it with your CPU, RAM, OS and Python version.

If you do not re-run, leave the hardware line exactly as written. It is true for where the numbers were measured.

**Optional: a real dataset (Edge-IIoTset).** Download `DNN-EdgeIIoT-dataset.csv` from IEEE DataPort or Kaggle (search "Edge-IIoTset"), then:

```bash
python experiments.py E1 --csv /path/DNN-EdgeIIoT-dataset.csv --label-col Attack_label
```

The loader drops non-numeric columns. If you use it, add one row to Table IV and remove the sentence in Sections VI and VIII that says real-dataset results are future work.

---

## Step 6: Finish the paper (most of your remaining time)

1. **Author and contributions.** Fill in your email in the author block. Section IX and Table VII are written for a team of one; edit them so they describe what you actually did and what you did not do, and add any AI-use disclosure your course requires.
2. **Rewrite the prose in your own words.** The course limits AI-generated content to 20%. Submitted as-is, this draft would almost certainly fail that check, and it would breach your course's integrity rule. Keep the structure, equations, tables, figures and numbers, and rewrite the sentences. Start with the abstract, the introduction, related work and the discussion, since detectors weight those most.
3. **References.** Re-checked on 6 Oct against the source pages: NIST IR 8547 authors, the Horizen blog (3 Dec 2025, about 220 k gas for 2 public inputs), the ethresear.ch thread and its Falcon gas post (19 Mar 2026), zkFL (accepted by IEEE Trans. Big Data), RiseFL authors, and PRoVeFL authors. Still to do by hand:
   - Three entries marked "[authors to be added]" in the reference list (arXiv 2609.15521, 2606.23017, 2309.01098). Open each arXiv page, copy the author names, and delete the bracket.
   - VerifBFL (arXiv 2501.04319): the page now shows a different title from the NOMS one; confirm the full author list and the published title on IEEE Xplore.
   - RiseFL: add the issue number and page range from the VLDB page.
   - zkFL: add volume and pages once IEEE Xplore lists them.
   - Every other reference: open it once before submitting.
   - **Novelty check.** Four of the five preprints flagged in the research report were read: none samples coordinates of an order-statistic aggregator against a ledger challenge. PRoVeFL uses multi-key homomorphic encryption, arXiv 2609.15521 uses zero-knowledge proofs over a cosine-similarity filter, Nautilus spot-checks 5% of updates with zk-SNARKs for policy compliance, and martFL uses zero-knowledge proofs. US patent 12671576 was not read; open it before any patent filing.
4. **Format.** The document is US Letter, two-column, Times New Roman 10 pt, with IEEE-style headings, captions and references. It is 8 pages; the limit is 12. If your instructor requires the official IEEE template file, download it from ieee.org/conferences/publishing/templates.html and paste each section in with Paste Special → Keep Text Only, then reapply the template's styles.
5. **Check before submitting.** Run Turnitin once you have IPR clearance, and aim for less than 10% similarity. Export to PDF. Check that no page goes past 12 and that every figure is readable when printed.

---

## Step 7: Demo day, 9 Oct (about 5 minutes of presenting)

The evening before, rehearse once and record a private screen capture as a backup.

```bash
cd demo_code && source .venv/bin/activate
./run_all.sh            # Windows without WSL: run the five python commands in run_all.sh one by one
```

What to say at each stage:

1. **Honest gateway, 2 of 8 poisoned clients.** Every round is accepted and accuracy reaches about 0.90, because the trimmed mean works.
2. **Lazy gateway, no audit.** Accuracy collapses to about 0.13 and nobody notices. This is the problem.
3. **Lazy gateway, audit on.** Every round is rejected and the poisoned model is never applied. This is the contribution.
   Point at the `[econ]` lines: in stage 1 the gateway and devices earn ETH; in stage 2 the cheating gateway is *paid* for poisoning the model; in stage 3 it loses 1 ETH of stake per round (10 → 5 ETH).
4. **Gateway tampering with 10% of coordinates.** Most rounds are rejected and slashed; occasionally one slips through, which is the probabilistic detection. Show Fig. 4 for the 1 − (1 − f)^k bound, then the bond bound B ≥ G(1 − P)/P − R: cheating is still a losing bet (in 100 rounds the gateway lost 84 ETH to earn 0.8 ETH).
5. **Gateway refuses to answer.** A keeper calls `expire()`, the bond is slashed, and the keeper earns a 10% bounty. Refusing is no escape.
6. **On the EVM.** The same flow runs on a real contract with real ETH balances, about 1.4M gas per audit. Be upfront about the trade-off: about 6× a Groth16 verification, but with no prover, no trusted setup and no pairings.

Close with `python test_verapq.py`, which prints 10 PASS lines.

Expect these questions:

- **"Is it post-quantum end to end?"** No. The client signatures (ML-DSA) and the audit (Keccak only) are quantum-resistant, but Ethereum's own transaction signatures are not.
- **"Why not a zero-knowledge proof?"** A ZK proof takes seconds to generate and most deployed SNARKs rely on pairings. Our audit takes milliseconds to prepare, at the cost of more gas and probabilistic detection.
- **"What about privacy?"** There is none. Sampled values are public. This is listed as a limitation.
- **"Where does the reward money come from?"** An operator funds the pool, and slashed bonds refill it, so cheaters pay for honest rounds. Payments use the pull pattern (`claim()`), so there is no re-entrancy risk during the audit.
- **"How big should the bond be?"** At least G(1 − P)/P − R, where G is what the gateway gains by cheating. The 1 ETH / 0.1 ETH values in the demo are illustrative.

---

## Step 8: Submission, 21 Oct

- Submit the PDF exported from the final Word file, plus the source repository link only if the course requires it. The repository can be shared privately with the evaluator.
- After a provisional application is filed, the code can be made public and the paper can go to a conference. Do not file outside India within 6 weeks of the Indian filing without Form 25 permission (Section 39 of the Patents Act).
