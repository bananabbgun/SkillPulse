from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd

from skillpulse.aggregation import ROLE_LABELS, ROLE_ORDER
from skillpulse.paths import FIGURES_DIR, ensure_output_dirs


def write_figures(marts: Dict[str, pd.DataFrame], figures_dir: Path = FIGURES_DIR) -> None:
    """Render the three pipeline-produced figures.

    File names use the report's global numbering (Fig 1 = scope, Fig 2 = architecture
    are author-drawn diagrams in docs/figures/, so this module produces 3, 4, 5).
    """
    ensure_output_dirs()
    figures_dir.mkdir(parents=True, exist_ok=True)
    write_figure_1(marts["role_ai_penetration"], figures_dir / "figure3_ai_penetration.png")
    write_figure_2(marts["ai_premium"], figures_dir / "figure4_ai_premium_vs_backend.png")
    write_figure_3(
        marts["role_skill_demand"],
        figures_dir / "figure5_skill_demand_data_engineer.png",
        focus_role="data_engineer",
    )


def write_figure_1(df: pd.DataFrame, path: Path) -> None:
    plot_df = df[df["role"].isin(ROLE_ORDER)].copy()
    plot_df["share_pct"] = plot_df["ai_inflected_share"] * 100

    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = ["#0f766e" if role == "data_engineer" else "#64748b" for role in plot_df["role"]]
    ax.bar(plot_df["role_label"], plot_df["share_pct"], color=colors)
    ax.set_ylabel("AI-inflected postings (%)")
    ax.set_title("Figure 3. AI Penetration by Role")
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
    ax.set_title("Figure 4. AI Salary Premium vs Backend Control")
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


def write_figure_3(
    df: pd.DataFrame,
    path: Path,
    focus_role: str,
    top_foundational: int = 10,
    top_ai_era: int = 5,
) -> None:
    """Skill demand for one role, with both foundational and AI-era skills represented.

    Pure top-N hides the AI signal when foundational skills dominate the head of the
    distribution. We instead show the top-N foundational PLUS the top-K AI-era skills
    so the curriculum-gap argument in the report is visually grounded.
    """
    role_skills = df[df["role"] == focus_role].copy()
    if role_skills.empty:
        return
    role_skills["pct"] = role_skills["pct_of_role"] * 100
    role_label = ROLE_LABELS.get(focus_role, focus_role)

    foundational = (
        role_skills[~role_skills["ai_era"]].sort_values("count", ascending=False).head(top_foundational)
    )
    ai_era = role_skills[role_skills["ai_era"]].sort_values("count", ascending=False).head(top_ai_era)
    combined = pd.concat([foundational, ai_era], ignore_index=True)
    combined = combined.sort_values("count", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 7.5))
    colors = ["#dc2626" if ai else "#0f766e" for ai in combined["ai_era"]]
    ax.barh(combined["name"], combined["pct"], color=colors)
    ax.set_xlabel("% of postings mentioning this skill")
    ax.set_title(
        f"Figure 5. Skill demand for {role_label} — top {top_foundational} foundational + top {top_ai_era} AI-era"
    )
    ax.set_xlim(0, max(100, combined["pct"].max() + 8))
    for index, row in enumerate(combined.itertuples()):
        ax.text(row.pct + 1, index, f"{row.pct:.0f}%", va="center", fontsize=9)

    legend_handles = [
        Patch(facecolor="#dc2626", label="AI-era skill (Facets 5–6)"),
        Patch(facecolor="#0f766e", label="Foundational skill"),
    ]
    ax.legend(handles=legend_handles, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)

