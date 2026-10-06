#!/usr/bin/env python3
"""Generate the paper figures from demo_code/results. Run from the paper/ folder."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

RES = Path(__file__).resolve().parent.parent / "demo_code" / "results"
OUT = Path(__file__).resolve().parent / "figs"
OUT.mkdir(exist_ok=True)

C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#dddcd5"
plt.rcParams.update({
    "font.family": "Liberation Serif", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.4, "savefig.dpi": 300, "mathtext.fontset": "stix",
})
W = 3.4  # single IEEE column, inches


def box(ax, x, y, w, h, text, fc="#f3f2ee", ec=INK, fs=7, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=INK, linespacing=1.15)


def arrow(ax, p, q, text=None, off=(0, 0.06), style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=7, lw=0.8, color=INK, linestyle=ls))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center", va="bottom",
                fontsize=5.8, color=INK)


def fig_architecture():
    fig, ax = plt.subplots(figsize=(W, 2.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.4); ax.axis("off")
    ys = [5.9, 4.3, 2.3]
    for i, y in enumerate(ys):
        lab = f"IoT client $C_{i+1}$" if i < 2 else "IoT client $C_n$"
        box(ax, 0.05, y, 2.45, 1.2, lab + "\ntrain, quantize,\nMerkle-commit, sign", fs=5.5)
    ax.text(1.27, 3.75, "...", ha="center", fontsize=8, color=MUTED)
    box(ax, 3.45, 2.6, 2.75, 3.9, "Edge gateway $G$\n\n1. registry + ML-DSA\n    check\n2. trimmed mean\n"
        "3. client-set root,\n    aggregate root\n4. answer challenge", fc="#e6effa", fs=5.5)
    box(ax, 7.15, 2.6, 2.8, 3.9, "Ledger contract $L$\n\ndevice registry\n(keccak pk, algId)\n\n"
        "commit / audit /\nexpire rounds\nKeccak-only checks\n\nETH stake: bond,\nreward, slash", fc="#fdeee6", fs=5.5)
    box(ax, 7.15, 0.05, 2.8, 1.5, "Model consumers\napply only accepted\naggregates", fc="#e5f5ee", fs=5.5)
    for y in ys:
        arrow(ax, (2.5, y + 0.6), (3.45, 4.55))
    ax.text(2.97, 1.6, r"$(\Delta_i, root_i, \sigma_i, pk_i)$", fontsize=5.5, ha="center")
    arrow(ax, (6.2, 5.6), (7.15, 5.6)); ax.text(6.67, 5.7, "commit\n+ bond", fontsize=5.2, ha="center")
    arrow(ax, (7.15, 4.55), (6.2, 4.55)); ax.text(6.67, 4.65, "seed", fontsize=5.2, ha="center")
    arrow(ax, (6.2, 3.5), (7.15, 3.5)); ax.text(6.67, 3.6, "audit", fontsize=5.2, ha="center")
    arrow(ax, (8.55, 2.6), (8.55, 1.55)); ax.text(8.7, 1.95, "accept / reject", fontsize=5.2, ha="left")
    fig.savefig(OUT / "fig1_architecture.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig_sequence():
    fig, ax = plt.subplots(figsize=(W, 2.9))
    ax.set_xlim(0, 10); ax.set_ylim(0, 11); ax.axis("off")
    xs = {"Client $C_i$": 1.2, "Gateway $G$": 5.0, "Ledger $L$": 8.8}
    for name, x in xs.items():
        box(ax, x - 1.0, 10.0, 2.0, 0.8, name, fs=7)
        ax.plot([x, x], [0.3, 10.0], color=MUTED, lw=0.6, ls=(0, (3, 2)))
    steps = [
        ("Client $C_i$", "Gateway $G$", r"$\Delta_i$, $root_i$, $\sigma_i=\mathrm{Sign}(sk_i,m_i)$"),
        ("Gateway $G$", "Gateway $G$", "verify, TrimMean$_t$, build trees"),
        ("Gateway $G$", "Ledger $L$", "commitRound(r, clientRoot, aggRoot, n, d, t, k)"),
        ("Ledger $L$", "Ledger $L$", "block $b_r$ sealed: seed = H(blockhash || roots || r)"),
        ("Ledger $L$", "Gateway $G$", r"challenge: $j_\tau$ = H(seed || $\tau$) mod d"),
        ("Gateway $G$", "Ledger $L$", "audit(r, client openings, k column samples)"),
        ("Ledger $L$", "Ledger $L$", "verify paths, recompute TrimMean on k columns"),
        ("Ledger $L$", "Client $C_i$", "RoundAudited(r, accepted)  /  expire(r)"),
    ]
    y = 9.3
    for a, b, t in steps:
        xa, xb = xs[a], xs[b]
        if a == b:
            ax.add_patch(FancyBboxPatch((xa - 0.12, y - 0.42), 0.24, 0.5, boxstyle="square,pad=0", fc=C1, ec=C1))
            ha = "right" if xa > 7 else "left"
            ax.text(xa + (-0.3 if ha == "right" else 0.3), y - 0.2, t, fontsize=5.8, ha=ha, va="center", bbox=dict(fc="white", ec="none", pad=0.6))
        else:
            arrow(ax, (xa, y - 0.15), (xb, y - 0.15))
            ax.text((xa + xb) / 2, y - 0.05, t, fontsize=5.8, ha="center", va="bottom", bbox=dict(fc="white", ec="none", pad=0.6))
        y -= 1.12
    fig.savefig(OUT / "fig2_sequence.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig_accuracy():
    d = pd.read_csv(RES / "exp_E1.csv")
    d = d[d.attack.isin(["none", "signflip"])]
    g = d.groupby(["malicious", "gateway", "audit"]).final_acc.agg(["mean", "std"]).reset_index()
    def pick(gw, au):
        s = g[(g.gateway == gw) & (g.audit == au)].sort_values("malicious")
        return s["mean"].to_numpy(), s["std"].to_numpy()
    series = [("FedAvg gateway, no audit", pick("lazy", False), C2, "//"),
              ("Trimmed mean, no audit", pick("honest", False), C1, ""),
              ("VERA-PQ (lazy gateway, audited)", pick("lazy", True), C3, "..")]
    fig, ax = plt.subplots(figsize=(W, 1.9))
    x = np.arange(4); bw = 0.26
    for i, (lab, (m, s), c, h) in enumerate(series):
        ax.bar(x + (i - 1) * bw, m, bw * 0.92, yerr=s, color=c, edgecolor="white", linewidth=0.6, hatch=h,
               error_kw=dict(lw=0.6, capsize=1.5, ecolor=INK), label=lab, zorder=3)
    ax.set_xticks(x); ax.set_xticklabels(["0/8", "1/8", "2/8", "3/8"])
    ax.set_xlabel("Sign-flipping clients (trim t = 2)"); ax.set_ylabel("Final test accuracy")
    ax.set_ylim(0, 1.05); ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.32), ncol=2, frameon=False, handlelength=1.2)
    fig.savefig(OUT / "fig3_accuracy.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig_detection():
    d = pd.read_csv(RES / "exp_E2.csv")
    fig, ax = plt.subplots(figsize=(W, 1.9))
    kk = np.arange(1, 41)
    for (f, c, mk) in [(0.01, C1, "o"), (0.05, C2, "s"), (0.10, C3, "^"), (0.25, C4, "D")]:
        m = max(1, round(f * 256))
        ax.plot(kk, 1 - (1 - m / 256) ** kk, color=c, lw=1.2, label=f"f = {int(f*100)}%")
        s = d[np.isclose(d.tamper_frac, f)]
        ax.plot(s.k, s.detect_rate, ls="none", marker=mk, ms=4.5, mfc=c, mec="white", mew=0.8, color=c)
    ax.set_xlabel("Sampled coordinates per round, k"); ax.set_ylabel("P(detect) per round")
    ax.set_xlim(0, 41); ax.set_ylim(0, 1.04)
    ax.legend(loc="lower right", frameon=False, ncol=2)
    ax.text(1, 0.93, "lines: 1-(1-f)^k   markers: 100 seeds", fontsize=6, color=MUTED)
    fig.savefig(OUT / "fig4_detection.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig_gas():
    g = pd.DataFrame(json.load(open(RES / "bench_gas.json")))
    g["nk"] = g.n * g.k
    fig, ax = plt.subplots(figsize=(W, 1.95))
    for dim, c, mk in [(32, C1, "o"), (1024, C2, "s")]:
        s = g[g.dim == dim].sort_values("nk")
        ax.plot(s.nk, s.audit_gas / 1e6, ls="none", marker=mk, ms=4.5, mfc=c, mec="white", mew=0.8,
                label=f"VERA-PQ audit, d = {dim}")
        p = np.polyfit(s.nk, s.audit_gas / 1e6, 1)
        xx = np.linspace(0, 520, 50)
        ax.plot(xx, np.polyval(p, xx), color=c, lw=0.9)
    ax.axhline(0.22, color=INK, lw=0.8, ls=(0, (4, 2)))
    ax.text(330, 0.55, "Groth16 verify ~0.22M", fontsize=6, color=INK)
    ax.axhline(4.7, color=MUTED, lw=0.8, ls=(0, (1, 1.5)))
    ax.text(5, 4.95, "one Falcon-512 verify in Solidity ~4.7M", fontsize=6, color=MUTED)
    ax.set_xlabel("n x k (clients x sampled coordinates)"); ax.set_ylabel("Gas (millions)")
    ax.set_xlim(0, 530); ax.set_ylim(0, 9)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.88), frameon=False)
    fig.savefig(OUT / "fig5_gas.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    fig_architecture(); fig_sequence(); fig_accuracy(); fig_detection(); fig_gas()
    print("figures written to", OUT)
