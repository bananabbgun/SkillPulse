from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

from skillpulse.aggregation import ROLE_LABELS, ROLE_ORDER
from skillpulse.paths import FIGURES_DIR, ensure_output_dirs


def write_figures(marts: Dict[str, pd.DataFrame], figures_dir: Path = FIGURES_DIR) -> None:
    ensure_output_dirs()
    figures_dir.mkdir(parents=True, exist_ok=True)
    write_figure_1(marts["role_ai_penetration"], figures_dir / "figure1_ai_penetration.png")
    write_figure_2(marts["ai_premium"], figures_dir / "figure2_ai_premium_vs_backend.png")


def write_figure_1(df: pd.DataFrame, path: Path) -> None:
    plot_df = df[df["role"].isin(ROLE_ORDER)].copy()
    plot_df["share_pct"] = plot_df["ai_inflected_share"] * 100

    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = ["#0f766e" if role == "data_engineer" else "#64748b" for role in plot_df["role"]]
    ax.bar(plot_df["role_label"], plot_df["share_pct"], color=colors)
    ax.set_ylabel("AI-inflected postings (%)")
    ax.set_title("Figure 1. AI Penetration by Role")
    ax.set_ylim(0, max(100, plot_df["share_pct"].max() + 10))
    ax.tick_params(axis="x", rotation=30)
    for index, row in enumerate(plot_df.itertuples()):
        ax.text(index, row.share_pct + 2, f"{row.share_pct:.0f}%\nn={row.n_postings}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_figure_2(df: pd.DataFrame, path: Path) -> None:
    plot_df = df[df["role"].isin(ROLE_ORDER)].copy()
    pivot = plot_df.pivot(index="role", columns="group", values="median_monthly_ntd").reindex(ROLE_ORDER)
    labels = [ROLE_LABELS.get(role, role) for role in pivot.index]
    x = range(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    non_ai = pivot.get("non_ai", pd.Series(index=pivot.index, dtype=float))
    ai = pivot.get("ai_inflected", pd.Series(index=pivot.index, dtype=float))
    # matplotlib bar() rejects None values; coerce to NaN so empty bars are simply not drawn.
    non_ai_vals = pd.to_numeric(non_ai, errors="coerce").fillna(0)
    ai_vals = pd.to_numeric(ai, errors="coerce").fillna(0)
    ax.bar([pos - width / 2 for pos in x], non_ai_vals, width=width, label="Non-AI", color="#94a3b8")
    ax.bar([pos + width / 2 for pos in x], ai_vals, width=width, label="AI-inflected", color="#0f766e")
    ax.set_ylabel("Median monthly salary (NTD)")
    ax.set_title("Figure 2. AI Salary Premium vs Backend Control")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.legend()

    n_lookup = {
        (row.role, row.group): int(row.n_salary_known)
        for row in plot_df.itertuples()
    }
    for pos, role in enumerate(pivot.index):
        for offset, group, series in ((-width / 2, "non_ai", non_ai), (width / 2, "ai_inflected", ai)):
            value = series.loc[role]
            if pd.notna(value):
                ax.text(pos + offset, value + 2500, f"n={n_lookup.get((role, group), 0)}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)

