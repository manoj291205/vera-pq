// Builds VERA-PQ IEEE two-column conference paper (US Letter) as .docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  SectionType, BorderStyle, TabStopType, VerticalAlign, ShadingType,
} = require("docx");

const FONT = "Times New Roman";
const FIG = path.join(__dirname, "figs");
const COLW = 5040; // 3.5 in column, DXA
const PAGE = { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1440, left: 900, right: 900 } };

// ---------------------------------------------------------------- references (numbered by first citation)
const REF = {
  nist8547: 'D. Moody, R. Perlner, A. Regenscheid, A. Robinson, and D. Cooper, "Transition to post-quantum cryptography standards," NIST IR 8547 (Initial Public Draft), Nov. 2024. [Online]. Available: https://csrc.nist.gov/pubs/ir/8547/ipd',
  ncsc: 'UK National Cyber Security Centre, "Timelines for migration to post-quantum cryptography," 2025. [Online]. Available: https://www.ncsc.gov.uk/guidance/pqc-migration-timelines',
  gidney: 'C. Gidney, "How to factor 2048 bit RSA integers with less than a million noisy qubits," arXiv:2505.15917, 2025.',
  mcmahan: 'B. McMahan, E. Moore, D. Ramage, S. Hampson, and B. A. y Arcas, "Communication-efficient learning of deep networks from decentralized data," in Proc. AISTATS, 2017, pp. 1273–1282.',
  casper: 'V. Buterin and V. Griffith, "Casper the friendly finality gadget," arXiv:1710.09437, 2017.',
  truebit: 'J. Teutsch and C. Reitwießner, "A scalable verification solution for blockchains," arXiv:1908.04756, 2019.',
  jiang: 'Y. Jiang, B. Ma, X. Wang, P. Yu, G. Yu, Z. Wang, W. Ni, and R. P. Liu, "Blockchained federated learning for Internet of Things: A comprehensive survey," arXiv:2305.04513, 2023.',
  fips204: 'National Institute of Standards and Technology, "Module-lattice-based digital signature standard," FIPS 204, Aug. 2024.',
  chhetri: 'R. Chhetri, "Benchmarking NIST-standardised ML-KEM and ML-DSA on ARM Cortex-M0+: Performance, memory, and energy on the RP2040," arXiv:2603.19340, 2026.',
  rfc7228: 'C. Bormann, M. Ersue, and A. Keranen, "Terminology for constrained-node networks," IETF RFC 7228, May 2014.',
  ethresear: 'Ethereum Research forum, "The road to post-quantum Ethereum transaction is paved with account abstraction (AA)," thread started by user asanso, Feb. 2025; Falcon-512/1024 gas figures from a post dated Mar. 19, 2026. [Online]. Available: https://ethresear.ch/t/21783',
  eip8051: 'R. Dubois and S. Masson, "EIP-8051: Precompile for ML-DSA signature verification," Ethereum Improvement Proposal (Draft), Oct. 2025.',
  peng: 'Z. Peng, C. Zhao, T. Wang et al., "A survey of zero-knowledge proof based verifiable machine learning," Artificial Intelligence Review, vol. 59, art. 157, 2026; arXiv:2502.18535.',
  verifbfl: 'M. A. Bouchiha et al., "VerifBFL: Leveraging zk-SNARKs for a verifiable blockchained federated learning," in Proc. IEEE/IFIP NOMS, 2025; arXiv:2501.04319 (the current arXiv version is titled "VerifBFL: A blockchain-based crowdsourcing framework for verifiable federated learning").',
  horizen: 'Horizen Labs, "ZK analysis: The true cost of ZK verification," blog post, Dec. 3, 2025. [Online]. Available: https://www.horizenlabs.io/blog/zk-analysis-the-true-cost-of-zk-verification',
  yin: 'D. Yin, Y. Chen, K. Ramchandran, and P. Bartlett, "Byzantine-robust distributed learning: Towards optimal statistical rates," in Proc. ICML, PMLR 80, 2018, pp. 5650–5659.',
  merkle: 'R. C. Merkle, "A digital signature based on a conventional encryption function," in Advances in Cryptology—CRYPTO ’87, LNCS 293, 1988, pp. 369–378.',
  biscotti: 'M. Shayan, C. Fung, C. J. M. Yoon, and I. Beschastnikh, "Biscotti: A blockchain system for private and secure federated learning," IEEE Trans. Parallel Distrib. Syst., vol. 32, no. 7, pp. 1513–1525, 2021.',
  krum: 'P. Blanchard, E. M. El Mhamdi, R. Guerraoui, and J. Stainer, "Machine learning with adversaries: Byzantine tolerant gradient descent," in Proc. NeurIPS, 2017.',
  fltrust: 'X. Cao, M. Fang, J. Liu, and N. Z. Gong, "FLTrust: Byzantine-robust federated learning via trust bootstrapping," in Proc. NDSS, 2021.',
  foolsgold: 'C. Fung, C. J. M. Yoon, and I. Beschastnikh, "The limitations of federated learning in Sybil settings," in Proc. RAID, 2020, pp. 301–316.',
  fang: 'M. Fang, X. Cao, J. Jia, and N. Z. Gong, "Local model poisoning attacks to Byzantine-robust federated learning," in Proc. USENIX Security, 2020, pp. 1605–1622.',
  flpoison: 'H. Zhang, Y. Liu, X. He, J. Wu, T. Cong, and X. Huang, "SoK: Benchmarking poisoning attacks and defenses in federated learning," arXiv:2502.03801, 2025.',
  zkfl: 'Z. Wang, N. Dong, J. Sun, W. Knottenbelt, and Y. Guo, "zkFL: Zero-knowledge proof-based gradient aggregation for federated learning," IEEE Trans. Big Data (accepted); arXiv:2310.02554.',
  xing: 'Z. Xing, Z. Zhang, M. Li, J. Liu, L. Zhu, G. Russello, and M. R. Asghar, "Zero-knowledge proof-based practical federated learning on blockchain," arXiv:2304.05590, 2023.',
  risefl: 'Y. Zhu, Y. Wu, Z. Luo, B. C. Ooi, and X. Xiao, "Secure and verifiable data collaboration with low-cost zero-knowledge proofs," Proc. VLDB Endow., vol. 17, p. 2321 ff., 2024; arXiv:2311.15310.',
  provefl: 'H. Kasyap, A. K. Pradhan, U. I. Atmaca, G. Cormode, and C. Maple, "PRoVeFL: Private robust and verifiable aggregation in federated learning," arXiv:2607.06612, 2026.',
  e2evfl: '"End-to-end verifiable and robust federated learning," arXiv:2609.15521, 2026 [authors to be added].',
  nautilus: '"Nautilus: A verifiable hierarchical federated learning framework for vehicular-edge-cloud systems," arXiv:2606.23017, 2026 [authors to be added].',
  martfl: '"martFL: Federated learning for data marketplaces," arXiv:2309.01098, 2023 [authors and venue to be added].',
  trustchain: 'E. Hallaji, R. Razavi-Far, and M. Saif, "TrustChain: A blockchain framework for auditing and verifying aggregators in decentralized federated learning," arXiv:2502.16406, 2025.',
  arya: 'A. A. Fall, "arya-STARK: Aggregation-robust yet authentic training via STARK proofs," IACR Cryptology ePrint Archive, Paper 2025/2238, 2025 (withdrawn May 2026).',
  fernandez: 'T. M. Fernández-Caramés and P. Fraga-Lamas, "Towards post-quantum blockchain: A review on blockchain cryptography resistant to quantum computing attacks," IEEE Access, vol. 8, pp. 21091–21116, 2020.',
  yang: 'Z. Yang, H. Alfauri, B. Farkiani, R. Jain, R. Di Pietro, and A. Erbad, "A survey and comparison of post-quantum and quantum blockchains," arXiv:2409.01358, 2024.',
  drake: 'J. Drake, D. Khovratovich, M. Kudinov, and B. Wagner, "Hash-based multi-signatures for post-quantum Ethereum," IACR Communications in Cryptology, 2025; ePrint 2025/055.',
  pqm4: 'M. J. Kannwischer, M. Krausz, R. Petri, and S.-Y. Yang, "pqm4: Benchmarking NIST additional post-quantum signature schemes on microcontrollers," IACR ePrint 2024/112, 2024.',
  bflmec: 'R. Xu, S. R. Pokhrel, Q. Lan, and G. Li, "Post quantum secure blockchain-based federated learning for mobile edge computing," arXiv:2302.13258, 2023.',
  pqsbfl: 'D. Commey and G. V. Crosby, "PQS-BFL: A post-quantum secure blockchain-based federated learning framework," arXiv:2505.01866, 2025.',
  zkflpq: 'E. Lansiaux, "Zero-knowledge federated learning with lattice-based hybrid encryption for quantum-resilient medical AI," arXiv:2603.03398, 2026.',
  pdp: 'G. Ateniese, R. Burns, R. Curtmola, J. Herring, L. Kissner, Z. Peterson, and D. Song, "Provable data possession at untrusted stores," in Proc. ACM CCS, 2007, pp. 598–609.',
  onai: 'Onai Inc., "Verification of computation by untrusted source," U.S. Patent 10 873 462 B1, Dec. 2020.',
  pogo: 'J. I. Orlicki, "PoGO: A scalable proof of useful work via quantized gradient descent and Merkle proofs," arXiv:2504.07540, 2025.',
  oqs: 'D. Stebila and M. Mosca, "Post-quantum key exchange for the Internet and the Open Quantum Safe project," in Proc. SAC 2016, LNCS 10532, pp. 14–37, 2017.',
  edgeiiot: 'M. A. Ferrag, O. Friha, D. Hamouda, L. Maglaras, and H. Janicke, "Edge-IIoTset: A new comprehensive realistic cyber security dataset of IoT and IIoT applications for centralized and federated learning," IEEE Access, vol. 10, pp. 40281–40306, 2022.',
  bowles: 'J. Bowles, S. Ahmed, and M. Schuld, "Better than classical? The subtle art of benchmarking quantum machine learning models," arXiv:2403.07059, 2024.',
};
const order = [];
function cite(...keys) {
  const nums = keys.map((k) => {
    if (!REF[k]) throw new Error("missing ref " + k);
    let i = order.indexOf(k);
    if (i < 0) { order.push(k); i = order.length - 1; }
    return i + 1;
  });
  return nums.map((n) => `[${n}]`).join(", ");
}

// ---------------------------------------------------------------- inline markup: **bold** *italic* _{sub} ^{sup}
function runs(s, base = {}) {
  const size = base.size || 20;
  const out = [];
  let b = false, it = false, buf = "";
  const mk = (text, extra = {}) => new TextRun({ text, font: FONT, size, bold: b || !!base.bold, italics: it || !!base.italics,
    smallCaps: !!base.smallCaps, ...extra });
  const flush = () => { if (buf) { out.push(mk(buf)); buf = ""; } };
  for (let p = 0; p < s.length;) {
    if (s.startsWith("**", p)) { flush(); b = !b; p += 2; continue; }
    if (s[p] === "*") { flush(); it = !it; p += 1; continue; }
    if ((s[p] === "_" || s[p] === "^") && s[p + 1] === "{") {
      flush();
      const e = s.indexOf("}", p);
      out.push(mk(s.slice(p + 2, e), s[p] === "_" ? { subScript: true } : { superScript: true }));
      p = e + 1; continue;
    }
    if (s[p] === "\t") { flush(); out.push(new TextRun({ children: ["\t"], font: FONT, size })); p++; continue; }
    buf += s[p]; p++;
  }
  flush();
  return out;
}

const body = [];
const P = (s, opts = {}) => body.push(new Paragraph({
  children: runs(s, opts.run || {}), alignment: opts.align || AlignmentType.JUSTIFIED,
  indent: opts.noIndent ? undefined : { firstLine: 202 }, spacing: { after: 0, line: 228, ...(opts.spacing || {}) },
  keepNext: !!opts.keepNext,
}));

const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];
let h1 = 0, h2 = 0;
function H1(t) {
  h1 += 1; h2 = 0;
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true,
    children: [new TextRun({ text: `${ROMAN[h1 - 1]}. `, font: FONT, size: 20 }), new TextRun({ text: t, font: FONT, size: 20, smallCaps: true })] }));
}
function H2(t) {
  h2 += 1;
  body.push(new Paragraph({ spacing: { before: 100, after: 40 }, keepNext: true,
    children: [new TextRun({ text: `${String.fromCharCode(64 + h2)}. ${t}`, font: FONT, size: 20, italics: true })] }));
}

let figN = 0;
function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}
function Fig(file, caption, widthIn = 3.35) {
  figN += 1;
  const { w, h, data } = pngSize(path.join(FIG, file));
  const pw = Math.round(widthIn * 96);
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 40 }, keepNext: true,
    children: [new ImageRun({ type: "png", data, transformation: { width: pw, height: Math.round((pw * h) / w) } })] }));
  body.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120 },
    children: [new TextRun({ text: `Fig. ${figN}. `, font: FONT, size: 16 }), ...runs(caption, { size: 16 })] }));
  return figN;
}

let tabN = 0;
const thin = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function Tab(title, widths, header, rows, opts = {}) {
  tabN += 1;
  const total = widths.reduce((a, b) => a + b, 0);
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 0 }, keepNext: true,
    children: [new TextRun({ text: `TABLE ${ROMAN[tabN - 1]}`, font: FONT, size: 16 })] }));
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, keepNext: true,
    children: runs(title, { size: 16, smallCaps: true }) }));
  const mkRow = (cells, isHead, isLast) => new TableRow({
    cantSplit: true,
    children: cells.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      margins: { top: 20, bottom: 20, left: 50, right: 50 },
      verticalAlign: VerticalAlign.CENTER,
      borders: { top: isHead ? thin : none, bottom: isHead || isLast ? thin : none, left: none, right: none },
      children: [new Paragraph({ alignment: i === 0 && !opts.centerFirst ? AlignmentType.LEFT : AlignmentType.CENTER,
        keepNext: !isLast, children: runs(String(c), { size: 15, bold: isHead }) })],
    })),
  });
  body.push(new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
    rows: [mkRow(header, true, false), ...rows.map((r, i) => mkRow(r, false, i === rows.length - 1))] }));
  if (opts.note) body.push(new Paragraph({ spacing: { before: 30, after: 120 }, alignment: AlignmentType.JUSTIFIED, children: runs(opts.note, { size: 14 }) }));
  else body.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
  return tabN;
}

let eqN = 0;
function Eq(s) {
  eqN += 1;
  body.push(new Paragraph({ spacing: { before: 60, after: 60 },
    tabStops: [{ type: TabStopType.CENTER, position: COLW / 2 }, { type: TabStopType.RIGHT, position: COLW }],
    children: [...runs("\t" + s + "\t"), new TextRun({ text: `(${eqN})`, font: FONT, size: 20 })] }));
  return eqN;
}

function Algo(title, lines) {
  const cell = new TableCell({
    width: { size: COLW, type: WidthType.DXA }, margins: { top: 40, bottom: 40, left: 80, right: 80 },
    borders: { top: thin, bottom: thin, left: none, right: none },
    children: [
      new Paragraph({ spacing: { after: 40 }, border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "000000", space: 1 } },
        children: runs(title, { size: 16 }) }),
      ...lines.map((l) => new Paragraph({ spacing: { after: 0 }, indent: { left: 240 * (l.match(/^ */)[0].length / 2) },
        children: runs(l.trim(), { size: 16 }) })),
    ],
  });
  body.push(new Paragraph({ spacing: { before: 60 }, children: [] }));
  body.push(new Table({ width: { size: COLW, type: WidthType.DXA }, columnWidths: [COLW], rows: [new TableRow({ cantSplit: true, children: [cell] })] }));
  body.push(new Paragraph({ spacing: { after: 100 }, children: [] }));
}

// ================================================================ CONTENT
// Abstract + index terms
body.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 80 }, children: [
  new TextRun({ text: "Abstract", font: FONT, size: 18, bold: true, italics: true }),
  new TextRun({ text: "—", font: FONT, size: 18, bold: true }),
  ...runs("Federated learning (FL) over Internet-of-Things (IoT) devices depends on an edge aggregator that every client must trust, while the cryptography protecting such systems is being migrated to post-quantum (PQ) primitives that are costly on microcontrollers and on blockchains. Verifiable-FL designs that rely on zk-SNARKs add seconds to minutes of proving time and rest on pairing assumptions that a quantum adversary can break. We present VERA-PQ, a framework that spans blockchain, decentralized AI, IoT/edge computing and post-quantum cryptography. Each client commits to its quantized update with a Merkle tree and signs a single 32-byte digest per round with ML-DSA (FIPS 204). The gateway computes a coordinate-wise trimmed mean, commits two Merkle roots to a smart contract, and is then challenged on *k* coordinates derived from the hash of the commit block; the contract re-executes the trimmed mean on those coordinates using only Keccak-256 and integer arithmetic. The same contract holds an ETH bond from the gateway for every round: an accepted audit releases the bond and pays a reward shared with the devices, while a rejected or expired round slashes it, and we derive the bond that makes cheating unprofitable. In a Python/Solidity prototype with eight clients, the audit accepted all 210 honest rounds, rejected all 210 rounds in which the gateway silently replaced the trimmed mean with plain averaging, and detected sparse tampering at the rate predicted by 1−(1−*f*)^{k}; over 100 rounds of 10% tampering the gateway lost 84 ETH of stake while earning 0.8 ETH. Building the audit response took at most 3 ms, whereas on-chain verification with reward settlement cost about 1.4 M gas for *n* = 8 and *k* = 16, roughly six times a Groth16 verification.", { size: 18, bold: true }),
] }));
body.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120 }, children: [
  new TextRun({ text: "Index Terms", font: FONT, size: 18, bold: true, italics: true }),
  new TextRun({ text: "—federated learning, post-quantum cryptography, ML-DSA, blockchain, Ethereum, smart contracts, staking, slashing, cryptoeconomics, Internet of Things, robust aggregation, verifiable computation.", font: FONT, size: 18, bold: true }),
] }));

// I. Introduction
H1("Introduction");
P(`Four technology domains now meet in the same deployments: blockchains used as tamper-evident audit layers, decentralized and federated AI, IoT and edge computing, and the migration to quantum-resistant cryptography. NIST's draft transition plan deprecates RSA and elliptic-curve signatures after 2030 and disallows them after 2035 ${cite("nist8547")}, the UK NCSC targets complete migration by 2035 ${cite("ncsc")}, and recent resource estimates place RSA-2048 within reach of fewer than one million noisy qubits ${cite("gidney")}. Systems built today on IoT fleets and immutable ledgers will still be running when these deadlines arrive.`);
P(`In this paper we take the four domains to be (i) blockchain/Web3, (ii) decentralized and federated AI, (iii) IoT/edge computing, and (iv) quantum computing and post-quantum cryptography. Federated learning ${cite("mcmahan")} is a natural fit for IoT intrusion detection because raw traffic never leaves the device, and blockchains have been proposed to coordinate and record such training ${cite("jiang")}. Combining the four, however, exposes limitations that overlap across domains:`);
P(`**L1 — Untrusted aggregation.** Robust aggregators protect the global model from poisoned clients only if the edge aggregator actually runs them. Clients and model consumers cannot observe this, and recording updates on a ledger does not show that the aggregate was computed correctly. In most designs a misbehaving aggregator also loses nothing, because it has no value at stake (AI × IoT × blockchain).`);
P(`**L2 — PQ cost on devices and ledgers.** An ML-DSA-44 signature is 2,420 bytes against 64 bytes for ECDSA ${cite("fips204")}; on a Cortex-M0+ class microcontroller ML-DSA signing averages about 159 ms with long rejection-sampling tails ${cite("chhetri")}, and the smallest devices have tens of kilobytes of RAM ${cite("rfc7228")}. On Ethereum, a Falcon-512 verification written in Solidity costs about 4.7 M gas versus 3,000 gas for ecrecover ${cite("ethresear")}, and the ML-DSA precompile is still a draft ${cite("eip8051")} (quantum × IoT × blockchain).`);
P(`**L3 — Cost and quantum exposure of verifiability.** Zero-knowledge machine-learning systems are limited mainly by proving cost ${cite("peng")}; VerifBFL, for example, needs up to 81 s per local-training proof and up to 2 s per aggregation proof ${cite("verifbfl")}. Widely deployed SNARKs such as Groth16 (about 220 k gas to verify ${cite("horizen")}) rely on pairings, which a quantum adversary breaks (AI × blockchain × quantum).`);
P(`Our starting observation is that the robust aggregators used in practice, such as the coordinate-wise trimmed mean and median ${cite("yin")}, are *order statistics evaluated independently per coordinate*. Output coordinate *j* depends only on coordinate *j* of the inputs. A verifier can therefore check a random subset of coordinates by re-executing the aggregator on values opened from Merkle commitments ${cite("merkle")}, using nothing but a hash function. No prover, trusted setup or pairing is needed.`);
P(`Building on this observation, this paper makes five contributions:`, { keepNext: true });
P(`**C1.** VERA-PQ, a protocol that binds per-client ML-DSA signatures to Merkle commitments of quantized updates, derives an audit challenge from the ledger after the aggregator has committed, and accepts a federated round only if a smart contract's recomputation of the trimmed mean on the sampled coordinates matches (Section IV).`);
P(`**C2.** A working prototype: a Python reference implementation and a Solidity contract that run on a simulated ledger and on an in-process Ethereum Virtual Machine (EVM), with liboqs and pure-Python ML-DSA back ends (Section VI).`);
P(`**C3.** A security analysis giving the detection bound, the anti-grinding rules and an explicit list of non-goals (Section V).`);
P(`**C4.** An evaluation of model accuracy under client poisoning and gateway misbehaviour, detection rate, computational overhead and gas cost, together with a trade-off comparison against SNARK-, STARK- and signature-only designs (Section VII). Limitations and deployment bottlenecks follow in Section VIII.`);
P(`**C5.** A crypto-economic layer in the same contract: the gateway bonds ETH for every round, accepted rounds pay a reward split between the gateway and the devices, and failed or expired audits slash the bond with a bounty for the keeper who reports the expiry. We derive the minimum bond that makes cheating unprofitable and measure the outcome on the EVM (Sections IV-E, V-D and VII-F).`);

// II. Related work
H1("Background and Related Work");
H2("Blockchain-Based Federated Learning");
P(`Blockchains have been used to replace the central FL server, record model updates and reward participants. Biscotti ${cite("biscotti")} combines a ledger with Multi-Krum and verifier committees, and a 2023 survey of blockchained FL for IoT ${cite("jiang")} lists overhead and compatibility as open problems. In most of these systems the ledger stores updates or models, while correctness of the aggregate is assumed or delegated to consensus. Bonding and slashing are standard tools for making misbehaviour costly: proof-of-stake Ethereum slashes validators that sign conflicting messages ${cite("casper")}, and Truebit uses deposits and verification games to check outsourced computation ${cite("truebit")}. VERA-PQ applies a bond to the aggregator itself and ties slashing to a hash-only audit, so the penalty is triggered automatically by the contract rather than by a dispute.`);
H2("Robust Aggregation and Poisoning");
P(`Krum ${cite("krum")}, the coordinate-wise trimmed mean and median ${cite("yin")}, FLTrust ${cite("fltrust")} and FoolsGold ${cite("foolsgold")} limit the influence of malicious clients. Local model-poisoning attacks can still degrade them ${cite("fang")}, and a recent benchmark evaluates 15 attacks against 17 defenses ${cite("flpoison")}. These defenses all assume that the aggregator executes them faithfully; VERA-PQ removes that assumption for order-statistic aggregators.`);
H2("Verifiable Aggregation");
P(`zkFL ${cite("zkfl")} has the aggregator produce a zero-knowledge proof of correct aggregation that blockchain miners verify. Xing *et al.* ${cite("xing")} and VerifBFL ${cite("verifbfl")} also prove local training with zk-SNARKs, and RiseFL ${cite("risefl")} reduces the cost of input checks. A survey of ZK-based verifiable ML ${cite("peng")} identifies proving cost and circuit expressiveness as the main barriers. TrustChain ${cite("trustchain")} audits aggregators statistically with an independence test rather than cryptographically. The closest design to ours is arya-STARK ${cite("arya")}, which combines Dilithium signatures with STARK proofs of trimmed-mean aggregation; it gives deterministic soundness at the cost of full proof generation, whereas VERA-PQ uses no prover at all and accepts probabilistic soundness. Other recent designs verify robust aggregation with multi-key homomorphic encryption across several servers ${cite("provefl")}, with non-interactive zero-knowledge proofs over a cosine-similarity filter ${cite("e2evfl")}, or, in martFL, with a zero-knowledge proof of weighted aggregation for data marketplaces ${cite("martfl")}. Nautilus ${cite("nautilus")} comes closest in spirit: it spot-checks a random 5% of updates against an on-chain commitment, but the checked property is that a node followed its training and compression policy, not that the aggregator computed an order statistic correctly, and the challenged node answers with a zk-SNARK.`);
H2("Post-Quantum Cryptography on Ledgers and Devices");
P(`ML-DSA is standardized in FIPS 204 ${cite("fips204")}. Surveys of post-quantum blockchains ${cite("fernandez", "yang")} highlight the size and verification cost of PQ signatures, and hash-based multi-signatures have been proposed for Ethereum consensus ${cite("drake")}. A draft EIP prices an ML-DSA precompile at 4,500 gas ${cite("eip8051")}. On Cortex-M4, pqm4 measures ML-DSA-44 signing at about 3.9 M cycles ${cite("pqm4")}, and ML-DSA-87 needs up to 119.6 KB of stack on a Cortex-M0+ ${cite("chhetri")}. In FL, BFL-MEC ${cite("bflmec")} and PQS-BFL ${cite("pqsbfl")} sign updates with Dilithium/ML-DSA but do not verify the aggregation, while ZKFL-PQ ${cite("zkflpq")} proves norm bounds on updates with lattice-based ZK and has no ledger.`);
H2("Sampling-Based Verification");
P(`Spot-checking with random challenges is classical in provable data possession ${cite("pdp")}. A patent by Onai ${cite("onai")} verifies a sequential computation by sampling Merkle-committed checkpoints, and PoGO ${cite("pogo")} uses Merkle proofs with random leaf checks to verify gradient training for consensus. VERA-PQ differs in what it samples: the output coordinates of a multi-input order statistic over PQ-authenticated client commitments, with the challenge seed taken from an external ledger block rather than from the prover's own commitment. Table ${ROMAN[tabN]} summarizes the coverage.`);
const T1 = Tab("Coverage of Closest Designs", [1500, 590, 590, 590, 590, 590, 590],
  ["Design", "PQ auth.", "Verif. agg.", "Robust agg.", "Ledger", "Prover-free", "IoT"],
  [
    [`Biscotti ${cite("biscotti")}`, "–", "P", "Y", "Y", "Y", "–"],
    [`zkFL ${cite("zkfl")}`, "–", "Y", "–", "Y", "–", "–"],
    [`VerifBFL ${cite("verifbfl")}`, "–", "Y", "–", "Y", "–", "P"],
    [`TrustChain ${cite("trustchain")}`, "–", "P", "P", "Y", "Y", "–"],
    [`arya-STARK ${cite("arya")}`, "Y", "Y", "Y", "–", "–", "–"],
    [`BFL-MEC ${cite("bflmec")}`, "Y", "–", "P", "Y", "Y", "P"],
    [`PQS-BFL ${cite("pqsbfl")}`, "Y", "–", "–", "Y", "Y", "–"],
    [`ZKFL-PQ ${cite("zkflpq")}`, "Y", "P", "P", "–", "–", "–"],
    ["**VERA-PQ (ours)**", "Y", "Y", "Y", "Y", "Y", "P"],
  ],
  { note: "Y = provided; P = partial (e.g., statistical or committee-based checks, norm bounds only, or edge rather than device-class evaluation); – = not provided or not reported in the source. Entries reflect our reading of each paper's abstract and main text." });

// III. System and threat model
H1("System and Threat Model");
H2("Entities");
P(`The system has four kinds of entity (Fig. 1). **Clients** *C*_{1}, …, *C*_{n} are IoT or edge devices that train a local intrusion-detection model and hold an ML-DSA key pair; each device is registered on the ledger by the hash of its public key and a signature-algorithm identifier. The **edge gateway** *G* collects updates, aggregates them, posts commitments and answers challenges. The **ledger contract** *L* stores the registry and round commitments, derives challenges and runs the audit. **Model consumers** apply only aggregates whose round the contract has accepted.`);
Fig("fig1_architecture.png", "VERA-PQ architecture. Clients send quantized updates with a Merkle root and one ML-DSA signature; the gateway aggregates and commits, the ledger derives a challenge seed from the commit block, and only audited rounds reach model consumers.");
H2("Adversary");
P(`**A1 (Byzantine clients).** Up to *t* of *n* clients send arbitrary updates. This is handled by the trimmed mean itself, which requires *n* > 2*t*, not by the audit.`);
P(`**A2 (malicious gateway).** The gateway may skip robust aggregation and use a cheaper rule (the *lazy* gateway), alter any subset of output coordinates (*tampering*), substitute client values, drop or fabricate clients, or try to grind the challenge by re-committing.`);
P(`**A3 (quantum adversary).** The adversary can break RSA, elliptic-curve signatures and pairing-based SNARKs, but not ML-DSA or Keccak-256 at their stated security levels.`);
H2("Assumptions and Non-Goals");
P(`We assume collision resistance of Keccak-256, existential unforgeability of ML-DSA, correct execution of the ledger, and that the hash of the block containing a commitment cannot be predicted by the gateway when it commits. VERA-PQ does not hide update values (sampled coordinates are revealed on chain), does not prove that clients trained honestly, and does not make the host chain's own transaction signatures quantum-safe.`);

// IV. Framework
H1("The VERA-PQ Framework");
H2("Client Commitment and Signing");
P(`In round *r*, client *i* computes its update Δ_{i} ∈ ℝ^{d}, quantizes it with scale *s* = 10^{6} to integers *v*_{i,j} = round(*s*Δ_{i,j}), and builds a Merkle tree whose leaves bind each value to its coordinate index:`);
Eq("ℓ_{i,j} = H(*v*_{i,j} ‖ *j*),   root_{i} = MerkleRoot(ℓ_{i,1}, …, ℓ_{i,d})");
P(`where *H* is Keccak-256 and values are encoded as 256-bit two's-complement integers, matching the EVM. The client then signs one fixed-length digest:`, { noIndent: true });
Eq("*m*_{i} = H(tag ‖ *r* ‖ *i* ‖ root_{i}),   σ_{i} = Sign(*sk*_{i}, *m*_{i})");
P(`where tag is the domain-separation string "VERA-PQ/update/v1" and Sign is ML-DSA-44. Because only the 32-byte digest is signed, the device performs one ML-DSA signature per round regardless of the model dimension *d*. The client sends (Δ_{i}, root_{i}, σ_{i}, *pk*_{i}) to the gateway.`, { noIndent: true });
H2("Gateway Filtering and Aggregation");
P(`The gateway accepts an update only if *H*(*pk*_{i}) matches the registry entry for *i*, σ_{i} verifies, and the Merkle root recomputed from the received values equals root_{i}. It sorts accepted clients by identifier and computes, for each coordinate,`);
Eq("*a*_{j} = trunc( Σ_{k=t+1}^{n−t} *v*_{(k),j} / (*n* − 2*t*) )");
P(`where *v*_{(k),j} is the *k*-th smallest value at coordinate *j* and integer division truncates toward zero identically in Python and Solidity. The gateway builds a client-set tree with leaves *H*(*i* ‖ root_{i} ‖ *H*(σ_{i})), so each signature is bound into the commitment, and an aggregate tree with leaves *H*(*a*_{j} ‖ *j*). It then calls commitRound(*r*, *R*_{C}, *R*_{A}, *n*, *d*, *t*, *k*). The contract requires *r* to equal the next expected round and the previous round to be resolved.`, { noIndent: true });
H2("Challenge and Audit");
P(`Once the commit block *b*_{r} is sealed, the challenge seed and sampled coordinates are`);
Eq("seed_{r} = H(blockhash(*b*_{r}) ‖ *R*_{C} ‖ *R*_{A} ‖ *r*)");
P(`and the sampled coordinates are *j*_{τ} = H(seed_{r} ‖ τ) mod *d* for τ = 0, …, *k*−1. The gateway submits an audit transaction containing, for every client, its identifier, root_{i}, *H*(σ_{i}) and a path into *R*_{C}; and, for every sampled coordinate, *a*_{j} with its path into *R*_{A} and all *n* client values *v*_{i,j} with their paths into root_{i}. The contract runs Algorithm 1 (Fig. 2). Malformed openings revert the transaction, while a correctly opened but wrong aggregate marks the round rejected. If no audit arrives within 256 blocks (the window in which blockhash is available), anyone can call expire(*r*), which also rejects the round.`, { noIndent: true });
Algo("**Algorithm 1:** Audit(*r*, client openings, samples) executed by contract *L*", [
  "**Require:** status(*r*) = committed; *b*_{r} < block.number ≤ *b*_{r} + 256",
  "1: seed ← *H*(blockhash(*b*_{r}) ‖ *R*_{C} ‖ *R*_{A} ‖ *r*)",
  "2: **for** *c* = 1 … *n* **do**",
  "  3: require id_{c} > id_{c−1} and pkHash[id_{c}] ≠ 0",
  "  4: require MerkleVerify(*R*_{C}, *H*(id_{c} ‖ root_{c} ‖ *h*_{c}), π_{c})",
  "5: **for** τ = 0 … *k*−1 **do**",
  "  6: *j* ← *H*(seed ‖ τ) mod *d*",
  "  7: require MerkleVerify(*R*_{A}, *H*(*a*_{j} ‖ *j*), π_{A})",
  "  8: **for** *c* = 1 … *n*: require MerkleVerify(root_{c}, *H*(*v*_{c,j} ‖ *j*), π_{c,j})",
  "  9: **if** TrimMean_{t}(*v*_{1,j}, …, *v*_{n,j}) ≠ *a*_{j} **then**",
  "    10: status(*r*) ← rejected; emit RoundAudited(*r*, false, τ); **return**",
  "11: status(*r*) ← accepted; emit RoundAudited(*r*, true, –)",
]);
Fig("fig2_sequence.png", "Message flow of one VERA-PQ round. The challenge is fixed only after the commit block is sealed, so the gateway cannot know which coordinates will be opened when it commits.");
H2("Signature Spot-Check and Crypto-Agility");
P(`To catch fabricated clients, the seed also selects one client per round, which must reveal (*pk*, σ). The verifier checks that *H*(*pk*) matches the registry, that *H*(σ) matches the digest bound in the client-set leaf, and that σ verifies under ML-DSA. On a PQ-native chain or with the draft ML-DSA precompile ${cite("eip8051")} this runs on chain; in our prototype it runs in the simulated ledger. The registry stores a per-device algorithm identifier, so devices can migrate from classical to hybrid to ML-DSA-only authentication without redeploying the contract.`);
H2("Crypto-Economic Layer: Staking, Rewards and Slashing");
P(`The contract is also an incentive mechanism denominated in ETH. A gateway first calls depositStake(); commitRound then requires at least *B* of unlocked stake and locks *B* (the bond) to round *r*. The operator funds a reward pool with fundRewards(), and each device registers a payout address. The round settles in the same transaction as the audit:`);
P(`• **Accepted:** the bond is unlocked, and a reward *R* is taken from the pool, half credited to the gateway and half split equally across the *n* devices in the client set.`, { noIndent: true });
P(`• **Rejected:** the bond is slashed from the gateway's stake into the reward pool, so a cheating gateway funds the rewards of future honest rounds.`, { noIndent: true });
P(`• **Expired:** if no audit arrives within 256 blocks, anyone may call expire(*r*); the bond is slashed and 10% of it is credited to the caller as a keeper bounty.`, { noIndent: true });
P(`All payments are credited to an internal balance and withdrawn later with claim(), a pull-payment pattern that keeps external calls out of the audit transaction and closes the usual re-entrancy path. Stake can be withdrawn only when it is not locked to an unresolved round. Our prototype uses *B* = 1 ETH and *R* = 0.1 ETH.`);

// V. Security analysis
H1("Security Analysis");
H2("Binding");
P(`Each sampled value is bound to the client's signed root by its Merkle path, each root is bound to σ_{i} by the signature and by *H*(σ_{i}) in the client-set leaf, and each aggregate value is bound to *R*_{A}. Substituting any value at a sampled coordinate therefore fails path verification deterministically under collision resistance of *H*.`);
H2("Detection Probability");
P(`Suppose the gateway reports wrong aggregates on *m* of the *d* coordinates, a fraction *f* = *m*/*d*. Because the challenge is unpredictable at commit time and indices are sampled uniformly with replacement, one round detects the deviation with probability`);
Eq("*P*_{det} = 1 − (1 − *f*)^{k}");
P(`so a target detection probability *P* requires`, { noIndent: true });
Eq("*k* ≥ ln(1 − *P*) / ln(1 − *f*)");
P(`For *P* = 0.95 this gives *k* = 29 when *f* = 10% and *k* = 299 when *f* = 1%. A lazy gateway that replaces the trimmed mean with the plain mean produces a different integer on almost every coordinate whenever the extreme values are not symmetric, so it is caught with probability close to one even for small *k*.`, { noIndent: true });
H2("Grinding and Withholding");
P(`A gateway might try to re-commit until it obtains a favourable challenge. Strictly sequential round identifiers, the requirement that the previous round be resolved, and the expiry rule together mean that each committed round is either audited against the challenge it received or rejected. A block proposer colluding with the gateway can still bias blockhash; production deployments should use RANDAO, a VRF or a commit-reveal beacon instead.`);
H2("Economic Security");
P(`Let a cheating gateway gain *G* per round (for example, the computation it saves or a payment from an attacker), and let *P* = *P*_{det} from (5). An honest round pays *R*. A cheating round pays *R* + *G* if undetected and loses *B* if detected, so cheating is unprofitable when (1 − *P*)(*R* + *G*) − *P*·*B* ≤ *R*, that is, when`);
Eq("*B* ≥ *G*(1 − *P*)/*P* − *R*");
P(`For a lazy gateway *P* ≈ 1 and any positive bond suffices. For 10% tampering with *k* = 16 on *d* = 31, *P* ≈ 0.80, so a bond of a quarter of the gain is enough; for a single tampered coordinate (*P* ≈ 0.41) the bond must be about 1.5*G*. Selective withholding does not help: a gateway that sees an unfavourable challenge and refuses to answer loses *B* through expire(), exactly as if it had been caught, and the keeper bounty means some party is always paid to trigger the expiry.`, { noIndent: true });
H2("Post-Quantum View");
P(`The audit path uses only Keccak-256 and integer arithmetic. Generic quantum attacks reduce its preimage resistance to about 2^{128} (Grover) and its collision resistance to about 2^{85} (Brassard–Høyer–Tapp), and client authentication uses ML-DSA. The construction therefore relies on no pairing or discrete-logarithm assumption. The overall system is not fully post-quantum on Ethereum, however, because the host chain still signs transactions with secp256k1.`);

// VI. Implementation
H1("Implementation");
P(`The prototype consists of a Python package (hashing, Merkle trees, PQ signatures, protocol, simulated ledger, EVM ledger and FL modules) and a Solidity contract, VeraPQLedger, compiled with solc 0.8.26 using the via-IR pipeline. ML-DSA is provided by liboqs 0.15.0 ${cite("oqs")} through liboqs-python 0.16.0.1, with dilithium-py 1.4.0 (a pure-Python FIPS 204 implementation) as a fallback; Keccak-256 comes from pycryptodome. The EVM back end deploys the contract on an in-process chain (py-evm through eth-tester 0.14.0b1 and web3 8.0.0); deployment costs 1.65 M gas. The simulated ledger mirrors the contract logic, including the stake, reward and slashing accounting to the wei, and additionally performs the ML-DSA spot-check. Ten unit tests (honest acceptance, full tampering, forged signature, substituted value, values not matching the signed root, fabricated client, reward payout, slashing, expiry with keeper bounty, and commit without sufficient stake) pass on both signature back ends, and the Python verifier and the contract agreed on every configuration in Section VII-E.`);
P(`The FL task is binary intrusion-style classification with logistic regression. Because our three-day build window did not allow preprocessing a full IoT intrusion dataset, the experiments use a synthetic tabular dataset generated with scikit-learn (30 features, 12 informative and 6 redundant, 60/40 class balance, 2% label noise), split into 400 samples per client and a fixed 2,000-sample test set. A loader for Edge-IIoTset ${cite("edgeiiot")} is included but was not used for the results reported here. Each client runs two epochs of mini-batch SGD per round. Table ${ROMAN[tabN]} lists the parameters. All measurements in Section VII were taken on a 2-vCPU Intel Xeon at 2.80 GHz with 7 GB of RAM running Linux and Python 3.13.`);
P(`**Independent reproduction.** Before the crypto-economic layer was added (it does not change audit outcomes), we also ran the demonstration scenarios and the unit tests on a second, independent Windows laptop (hardware details to be added) that used the pure-Python ML-DSA fallback, with eight clients, two sign-flipping clients, trim *t* = 2 and *k* = 16. The outcomes were identical to those on the first machine. An honest gateway was accepted in all five rounds, with accuracy rising from 0.885 to 0.906. A lazy gateway without the audit was accepted in all five rounds while accuracy fell to 0.113–0.132. The same lazy gateway with the audit, and a gateway tampering with 10% of the coordinates, were rejected in all five rounds, and all six unit tests passed. Only the timings differed. Client commit-and-sign took 31–71 ms per client in pure Python, against about 1.2 ms with liboqs, and gateway verification and aggregation took 75–95 ms (one round 282 ms) against about 8 ms. The signature back end therefore dominates device-side cost in an unoptimized deployment.`);
Tab("Experimental Parameters", [2300, 2740], ["Parameter", "Value"], [
  ["Clients *n* / trim *t*", "8 / 2 (E1, E2); 4–32 (E3, E4)"],
  ["Model / dimension *d*", "Logistic regression; 31 (E1), 256 (E2), 32–1024 (E3, E4)"],
  ["Local training", "2 epochs, SGD, lr 0.2, batch 64"],
  ["Rounds / seeds", "10 rounds × 3 seeds (E1); 1 round × 100 seeds (E2)"],
  ["Attacks", "Sign-flip (×8), Gaussian (σ = 8·std(Δ))"],
  ["Gateway modes", "honest, lazy (plain mean), tamper (shift fraction *f*)"],
  ["Samples *k*", "16 (E1); 4–32 (E2, E4)"],
  ["Signature", "ML-DSA-44 (liboqs 0.15.0)"],
  ["Quantization", "*s* = 10^{6}, int256 leaves"],
]);

// VII. Results
H1("Results and Discussion");
H2("Signature Primitives");
P(`Table ${ROMAN[tabN]} compares the PQ signature schemes on our x86 machine. ML-DSA-44 signs in 0.06 ms with liboqs, but its signature is 38 times larger than a 64-byte ECDSA signature. Falcon-512 has a smaller signature (654 bytes, variable length) but 7.5 ms key generation and floating-point arithmetic, and SPHINCS+-128f produces 17 KB signatures. The pure-Python fallback is roughly 570 times slower than liboqs for signing. The ECDSA baseline uses a different library (Python cryptography) and is shown only for scale. For microcontrollers we rely on published measurements ${cite("pqm4", "chhetri")}. VERA-PQ amortizes these costs by signing one 32-byte digest per round, rather than per message or per parameter.`);
Tab("Signature Cost on x86 (mean of repeated runs)", [1600, 820, 820, 900, 900], ["Scheme", "pk (B)", "sig (B)", "sign (ms)", "verify (ms)"], [
  ["ML-DSA-44 (liboqs)", "1,312", "2,420", "0.061", "0.026"],
  ["ML-DSA-65 (liboqs)", "1,952", "3,309", "0.069", "0.036"],
  ["Falcon-512 (liboqs)", "897", "654", "0.257", "0.048"],
  ["SPHINCS+-SHA2-128f", "32", "17,088", "10.29", "1.19"],
  ["ML-DSA-44 (pure Python)", "1,312", "2,420", "34.97", "12.65"],
  ["ECDSA secp256k1", "64", "64", "0.416", "0.405"],
]);
H2("Model Protection Under Poisoning and Gateway Misbehaviour");
P(`Table ${ROMAN[tabN]} and Fig. 3 report final test accuracy after ten rounds (mean ± standard deviation over three seeds). With an honest gateway the audit changes nothing: all 210 audited honest rounds were accepted and accuracy was identical to the unaudited trimmed mean. Without the audit, a lazy gateway that silently substitutes plain averaging lets one sign-flipping client cut accuracy from 0.912 to 0.277, and two such clients cut it to 0.176. Gaussian poisoning is milder because the noise partly averages out (0.845 with three attackers). With the audit enabled, every one of the 210 rounds produced by the lazy gateway was rejected, including the attack-free runs, because the plain mean differs from the agreed trimmed mean as soon as the extreme values are asymmetric. The model therefore stayed at its initial state (accuracy 0.408) instead of being corrupted. The audit provides safety, not liveness: an operator who sees repeated rejections must replace the gateway. In a separate run where the gateway shifted 10% of the coordinates (*d* = 31, *k* = 16), all five rounds were rejected.`);
P(`With three sign-flipping clients and *t* = 2, the trimmed mean itself fails (0.173), and the audit, correctly, accepts these rounds because the gateway did exactly what was agreed. The audit verifies execution of the chosen aggregator, not whether *t* was chosen well; *t* must be set at least as large as the expected number of malicious clients.`);
Tab("Final Accuracy After 10 Rounds (n = 8, t = 2)", [1150, 1300, 1300, 1290], ["Attack", "FedAvg gateway, no audit", "Trimmed mean (honest)", "Lazy gateway + audit"], [
  ["None", "0.912 ± 0.031", "0.913 ± 0.030", "rejected 30/30"],
  ["Sign-flip 1/8", "0.277 ± 0.025", "0.911 ± 0.031", "rejected 30/30"],
  ["Sign-flip 2/8", "0.176 ± 0.020", "0.907 ± 0.036", "rejected 30/30"],
  ["Sign-flip 3/8", "0.172 ± 0.010", "0.173 ± 0.017", "rejected 30/30"],
  ["Gaussian 1/8", "0.905 ± 0.031", "0.912 ± 0.031", "rejected 30/30"],
  ["Gaussian 2/8", "0.886 ± 0.028", "0.912 ± 0.031", "rejected 30/30"],
  ["Gaussian 3/8", "0.845 ± 0.030", "0.911 ± 0.026", "rejected 30/30"],
], { note: "Rejected rounds are not applied, so the audited model stays at its initial accuracy (0.408 ± 0.007). The honest-gateway column is identical with and without the audit (0 of 210 rounds rejected)." });
Fig("fig3_accuracy.png", "Final accuracy versus number of sign-flipping clients. The audit cannot rescue a model once attackers exceed *t*, but it prevents a lazy gateway from silently applying a corrupted aggregate.");
H2("Detection of Sparse Tampering");
P(`Fig. 4 shows the empirical detection rate over 100 seeds for *d* = 256 against the analytic curve of (5). All sixteen configurations fall within 2.1 binomial standard deviations of the prediction; for example, *f* = 10% and *k* = 16 gives 0.82 measured against 0.820 predicted, and *f* = 25% and *k* = 16 gives 0.99 against 0.990. Very sparse tampering remains hard to catch: with *f* = 1%, even *k* = 32 detects only about a quarter of attempts in a single round.`);
Fig("fig4_detection.png", "Per-round detection probability versus number of sampled coordinates *k* (*d* = 256). Lines: 1−(1−*f*)^{k}; markers: empirical rate over 100 seeds.");
H2("Computational Overhead");
P(`Table ${ROMAN[tabN]} breaks down the per-round cost. Client time covers building the Merkle tree and signing; it grows with *d* (0.8–1.2 ms at *d* = 32 to 16–18 ms at *d* = 1,024) because of hashing in Python, while the signature itself takes about 0.06 ms. Gateway verification and aggregation grows with *n*·*d* and reaches 610 ms for *n* = 32 and *d* = 1,024. Building the audit response, the analogue of proof generation, took at most 3 ms in every configuration, compared with up to 2 s for a SNARK aggregation proof in VerifBFL ${cite("verifbfl")}; the hardware differs, so this comparison is indicative only. The audit payload grows from 41 KB to 232 KB of calldata across the grid.`);
Tab("Per-Round Time (ms) and Audit Calldata", [520, 620, 900, 900, 900, 1200], ["*n*", "*d*", "Client", "Gateway", "Audit build", "Calldata (KB)"], [
  ["8", "32", "1.21", "8.2", "0.64", "41"],
  ["8", "1024", "18.31", "139.9", "0.79", "64"],
  ["16", "32", "0.75", "10.2", "0.70", "76"],
  ["16", "1024", "16.20", "328.6", "1.67", "120"],
  ["32", "32", "0.86", "21.4", "1.17", "147"],
  ["32", "1024", "17.67", "610.1", "2.98", "232"],
], { note: "Client = Merkle commitment + ML-DSA signing; Gateway = signature and root checks + trimmed mean + trees. Python implementation, liboqs ML-DSA-44, mean of three rounds; calldata is the estimated ABI payload of the audit transaction." });
H2("On-Chain Cost");
P(`Committing a round costs about 149 k gas regardless of parameters, of which about 25 k is locking the bond. Fig. 5 shows that audit gas, including reward settlement, is almost exactly linear in *n*·*k* (*R*^{2} > 0.99): about 10.5 k gas per client-sample plus 112 k for *d* = 32, and 16.1 k per client-sample plus 169 k for *d* = 1,024, the difference coming from longer Merkle paths. For the demonstration setting (*n* = 8, *k* = 16, *d* = 32) the audit costs 1.39 M gas, measured on the EVM, of which reward settlement adds about 4%, against roughly 220 k for a Groth16 verification with two public inputs ${cite("horizen")} and 4.7 M for a single Falcon-512 verification in Solidity ${cite("ethresear")}. The largest configuration (*n* = 16, *d* = 1,024, *k* = 32) costs 8.46 M gas, which is impractical on a public layer-1 chain. Verifying eight ML-DSA signatures through the draft precompile would cost about 36 k gas ${cite("eip8051")}, but that would only authenticate the inputs, not check the aggregate.`);
Fig("fig5_gas.png", "Measured audit gas versus *n*·*k* on the EVM for *d* = 32 and *d* = 1,024, with linear fits. Horizontal lines give reference costs for a Groth16 verification and for one Falcon-512 verification in Solidity.");
H2("Crypto-Economic Outcomes");
P(`Table ${ROMAN[tabN]} reports the gateway's balance sheet in each demonstration scenario (8 devices, 2 sign-flipping clients, *B* = 1 ETH, *R* = 0.1 ETH, 10 ETH initial stake). The no-audit baseline shows the core problem in economic terms: a lazy gateway poisons the model and is still paid the full reward. With the audit, the same gateway is slashed in every round. Over 100 rounds of 10% tampering (*k* = 16, *d* = 31) the gateway was caught and slashed in 84 rounds (80.4 predicted) and earned rewards from only 16, a net loss of 83.2 ETH against a 5 ETH profit for honest behaviour; with a single tampered coordinate it was slashed in 47 of 100 rounds (40.8 predicted). On the EVM, the stake, credit and pool balances matched the simulated ledger to the wei in every scenario we ran. The economic calls are cheap next to the audit: depositStake 45 k, fundRewards 44 k, expire with bounty 66 k and claim 29 k gas, while a rejected audit with slashing costs 1.25 M gas.`);
Tab("Gateway Balance Sheet per Scenario (Simulated Ledger)", [1500, 700, 900, 940, 1000], ["Scenario", "Accepted", "Slashed (ETH)", "Gateway reward (ETH)", "Final acc."], [
  ["Honest, 5 rounds", "5/5", "0", "0.25", "0.906"],
  ["Lazy, no audit, 5 rounds", "5/5", "0", "0.25", "0.132"],
  ["Lazy + audit, 5 rounds", "0/5", "5", "0", "0.389"],
  ["Withholding (expired), 3 rounds", "0/3", "3", "0", "0.389"],
  ["Tamper *f* = 10%, 100 rounds", "16/100", "84", "0.80", "–"],
  ["Tamper 1 coord., 100 rounds", "53/100", "47", "2.65", "–"],
], { note: "Devices receive the same total reward as the gateway in accepted rounds. In the withholding scenario the keeper earned 0.1 ETH per expired round. Final accuracy 0.389 is the initial model, because rejected rounds are never applied." });
H2("Trade-Off Comparison");
P(`Table ${ROMAN[tabN]} places VERA-PQ among the alternatives. It trades the constant verification cost and deterministic soundness of SNARK-based verification for no prover time, no trusted setup and no pairing assumption. STARK-based designs such as arya-STARK ${cite("arya")} keep deterministic soundness and PQ plausibility but require proof generation. Signature-only PQ blockchain FL ${cite("bflmec", "pqsbfl")} authenticates inputs cheaply but leaves aggregation unverified. Of the four, VERA-PQ is the only one whose security level can be tuned per round through *k*, which makes it best suited to permissioned chains or rollups where gas is cheap but proving hardware at the edge is not.`);
Tab("Qualitative Trade-Offs", [1060, 1000, 1000, 1000, 980], ["Property", "VERA-PQ", "SNARK agg. proof", "STARK proof", "PQ-signed BFL"], [
  ["Soundness", "1−(1−*f*)^{k}", "Deterministic", "Deterministic", "None (agg.)"],
  ["Prover cost", "≤ 3 ms", "Seconds", "Seconds+", "None"],
  ["On-chain verify", "0.3–8.5 M gas, ∝ *n*·*k*", "≈ 220 k gas", "Large proofs", "Signatures only"],
  ["PQ assumptions", "Hash + ML-DSA", "No (pairings)", "Yes (hash)", "Yes"],
  ["Trusted setup", "No", "Groth16: yes", "No", "No"],
  ["Update privacy", "No", "Yes", "Possible", "No"],
], { note: "SNARK: zkFL, VerifBFL; STARK: arya-STARK; PQ-signed BFL: BFL-MEC, PQS-BFL. Values for other designs are taken from their papers and cited sources; only VERA-PQ was measured here." });

// VIII. Limitations
H1("Limitations and Deployment Bottlenecks");
P(`**Gas grows linearly in *n*·*k*.** Beyond a few dozen clients the audit becomes too expensive for a public layer-1 chain. Deployments should use a permissioned chain or a rollup, commit chunks of *c* coordinates per leaf to reduce path overhead, or switch to an optimistic variant in which the audit runs only when a challenger disputes a round. None of these variants is implemented yet.`);
P(`**Soundness is probabilistic.** Very sparse tampering (*f* ≈ 1/*d*) evades a single audit with high probability. Repeated rounds, larger *k* and the slashable bond raise the cost of such attacks, but only in expectation.`);
P(`**Economic parameters.** The bound in (7) needs an estimate of the gain *G*, which is hard to know in practice, and our *B* and *R* are illustrative. Rewards depend on an operator funding the pool, ETH price volatility changes the real value of the bond, and we did not simulate strategic agents or collusion between the gateway and devices. Clients themselves are not bonded; poisoning clients are handled by the trimmed mean, not by slashing.`);
P(`**No update privacy.** Sampled update values are published on chain, which is incompatible with secure aggregation; order statistics cannot be computed over masked values. Differential privacy at the client is possible but reduces accuracy.`);
P(`**Randomness and host-chain security.** A block proposer colluding with the gateway can bias blockhash. On Ethereum, transaction signatures remain secp256k1, the on-chain ML-DSA spot-check depends on a draft precompile ${cite("eip8051")}, and the Falcon standard (FIPS 206) has not yet been published. Our EVM path therefore checks the binding of public keys only at the gateway.`);
P(`**Evaluation scope.** The results use synthetic tabular data, a logistic-regression model with *d* ≤ 1,024, at most 32 clients and x86 hardware; no microcontroller was measured, so device costs are taken from the literature ${cite("pqm4", "chhetri")}. Results on Edge-IIoTset ${cite("edgeiiot")}, on deep models and on Raspberry Pi-class devices remain to be produced. The trimmed mean is known to degrade under strongly non-IID data and when attackers exceed *t*. Finally, we deliberately left quantum machine learning out of scope: careful benchmarks find that classical baselines generally match or beat current QML models ${cite("bowles")}.`);

// IX. Team
H1("Limitations and Contributions (Team Size: One)");
P(`The project was carried out by a single student within a three-day build window before the demonstration. The author is responsible for the protocol design, the Solidity contract with its staking and slashing layer, the EVM integration, the federated-learning pipeline and attack models, the experiments, the figures and this report. Working alone shaped the scope in three ways: we used synthetic data rather than a full IoT intrusion dataset, used an in-process EVM rather than a public testnet, and cited microcontroller measurements rather than collecting our own. Table ${ROMAN[tabN]} lists each area of work together with the limitation that follows from a one-person team.`);
Tab("Contributions and Team-Size Limitations", [1500, 3540], ["Work area", "Limitation due to a one-person team"], [
  ["Protocol and security analysis", "No independent review of the threat model or the detection bound; all arguments are by the author alone"],
  ["Solidity contract and EVM path", "Not audited or cross-implemented by a second developer; tested only on an in-process EVM"],
  ["Staking and slashing layer", "Parameters chosen illustratively; no game-theoretic simulation or external review of the incentive design"],
  ["FL pipeline and attacks", "One synthetic dataset and two attack types; no real IoT dataset yet"],
  ["Experiments E1–E4", "Measured on one machine and reproduced once on a second laptop; no third-party replication"],
  ["Writing and figures", "No internal peer review before submission"],
]);

// X. Conclusion
H1("Conclusion and Future Work");
P(`VERA-PQ addresses three limitations shared by blockchain, federated AI, IoT and post-quantum cryptography: the untrusted aggregator, the cost of PQ signatures on devices and ledgers, and the cost and quantum exposure of zero-knowledge verification. Because robust aggregators are coordinate-wise order statistics, a smart contract can audit them from Merkle openings using only a hash function. Our prototype shows that this blocks a gateway that silently weakens the aggregator, detects tampering at the analytically predicted rate, and costs only milliseconds at the gateway. Because the same contract bonds the gateway's ETH and slashes it on a failed or expired audit, cheating also becomes unprofitable once the bond exceeds a bound set by the detection probability. The price is on-chain gas that grows with *n*·*k* and soundness that is probabilistic. Future work will add chunked leaves, an optimistic dispute mode, a game-theoretic study of the incentive parameters, evaluation on Edge-IIoTset and Raspberry Pi devices, and deployment on a chain with native ML-DSA verification.`);

// References
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true,
  children: [new TextRun({ text: "References", font: FONT, size: 20, smallCaps: true })] }));
order.forEach((k, i) => body.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 20 },
  indent: { left: 360, hanging: 360 }, children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT, size: 16 }), new TextRun({ text: REF[k], font: FONT, size: 16 })],
  tabStops: [{ type: TabStopType.LEFT, position: 360 }] })));
const unused = Object.keys(REF).filter((k) => !order.includes(k));
if (unused.length) console.warn("unused refs:", unused);

// ---------------------------------------------------------------- title block (single column)
const nob = { top: none, bottom: none, left: none, right: none };
const authorCell = (name, lines) => new TableCell({
  width: { size: 3480, type: WidthType.DXA }, borders: nob,
  children: [
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: name, font: FONT, size: 22 })] }),
    ...lines.map((l) => new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: l, font: FONT, size: 20, italics: !l.includes("@") && !l.startsWith("[email") })] })),
  ],
});
const aff = ["School of Computer Science and Engineering", "Vellore Institute of Technology", "Vellore, India"];
const titleBlock = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({
    text: "VERA-PQ: A Post-Quantum, Hash-Only Smart Contract with Staking and Slashing for Verifiable Edge Aggregation in Blockchain-Based Federated Learning",
    font: FONT, size: 48 })] }),
  new Table({ width: { size: 10440, type: WidthType.DXA }, columnWidths: [10440], borders: { ...nob, insideHorizontal: none, insideVertical: none },
    rows: [new TableRow({ children: [
      new TableCell({ width: { size: 10440, type: WidthType.DXA }, borders: nob, children: [
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Manojkumar Ashokkumar", font: FONT, size: 22 })] }),
        ...aff.map((l) => new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: l, font: FONT, size: 20, italics: true })] })),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "[email]", font: FONT, size: 20 })] }),
      ] }),
    ] })] }),
  new Paragraph({ spacing: { after: 200 }, children: [] }),
];

const doc = new Document({
  creator: "Manojkumar Ashokkumar",
  title: "VERA-PQ",
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  sections: [
    { properties: { page: PAGE }, children: titleBlock },
    { properties: { type: SectionType.CONTINUOUS, page: PAGE, column: { space: 360, count: 2, equalWidth: true } }, children: body },
    { properties: { type: SectionType.CONTINUOUS, page: PAGE }, children: [new Paragraph({ children: [] })] },
  ],
});
Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "VERA-PQ_IEEE_paper.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, "refs:", order.length);
});
