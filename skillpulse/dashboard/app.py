from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from skillpulse.aggregation import ROLE_LABELS, ROLE_ORDER
from skillpulse.paths import MARTS_DIR


# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------
TEAL = "#0f766e"           # foundational skills / selected role / "good" delta
RED = "#dc2626"            # AI-era skills / negative delta
SLATE_500 = "#64748b"      # secondary text
SLATE_300 = "#cbd5e1"      # neutral bars
SLATE_50 = "#f8fafc"       # card background
GREEN = "#16a34a"          # positive delta


st.set_page_config(page_title="SkillPulse", page_icon="📊", layout="wide")


def _inject_css() -> None:
    """Tighten Streamlit defaults so the dashboard reads like a one-page brief."""
    st.markdown(
        f"""
        <style>
            .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }}
            h1, h2, h3 {{ letter-spacing: -0.01em; }}
            .sp-section-title {{
                display: flex; align-items: baseline; gap: 0.6rem;
                margin: 1.6rem 0 0.4rem 0;
                border-left: 4px solid {TEAL};
                padding-left: 0.75rem;
            }}
            .sp-section-title h3 {{ margin: 0; font-weight: 600; }}
            .sp-section-title span.sp-hint {{ color: {SLATE_500}; font-size: 0.85rem; }}
            .sp-headline {{
                background: {SLATE_50};
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 1rem 1.25rem;
                margin: 0.5rem 0 1rem 0;
                line-height: 1.55;
                font-size: 1.02rem;
            }}
            .sp-premium-card {{
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 1rem 1.25rem;
                height: 100%;
            }}
            .sp-premium-label {{
                color: {SLATE_500};
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.3rem;
            }}
            .sp-premium-value {{ font-size: 1.9rem; font-weight: 600; line-height: 1.2; }}
            .sp-premium-unit  {{ font-size: 0.7em; color: {SLATE_500}; font-weight: 400; }}
            .sp-premium-foot  {{ color: {SLATE_500}; font-size: 0.8rem; margin-top: 0.4rem; }}
            .sp-warn          {{ color: {RED}; font-size: 0.8rem; margin-top: 0.4rem; }}
            div[data-testid="stMetricValue"] {{ font-size: 1.6rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section(title: str, hint: str = "") -> None:
    hint_html = f'<span class="sp-hint">{hint}</span>' if hint else ""
    st.markdown(
        f'<div class="sp-section-title"><h3>{title}</h3>{hint_html}</div>',
        unsafe_allow_html=True,
    )


@st.cache_data
def load_marts() -> dict:
    required = {
        "postings": MARTS_DIR / "normalized_postings.csv",
        "penetration": MARTS_DIR / "role_ai_penetration.csv",
        "premium": MARTS_DIR / "ai_premium.csv",
        "skill_demand": MARTS_DIR / "role_skill_demand.csv",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing marts. Run `python -m skillpulse.run_all --sample` first.")
    return {name: pd.read_csv(path) for name, path in required.items()}


def main() -> None:
    _inject_css()
    st.title("SkillPulse")
    st.caption(
        "Taiwan data / AI job market — a one-page brief for training providers. "
        "Pick a role and read it like a story: is the role real, what skills does it need, "
        "and does AI come with a salary premium?"
    )

    marts = load_marts()
    postings = marts["postings"]
    penetration = marts["penetration"]
    premium = marts["premium"]
    skill_demand = marts["skill_demand"]

    available_roles = [r for r in ROLE_ORDER if r in set(postings["role"])]
    default_idx = available_roles.index("data_engineer") if "data_engineer" in available_roles else 0
    role = st.sidebar.selectbox(
        "Role",
        available_roles,
        index=default_idx,
        format_func=lambda value: ROLE_LABELS.get(value, value),
    )
    st.sidebar.divider()
    source_counts = postings["source"].value_counts()
    source_str = "  •  ".join(f"{src} : {cnt}" for src, cnt in source_counts.items())
    st.sidebar.markdown(
        f"**Dataset**  \n"
        f"Total postings : **{len(postings)}**  \n"
        f"{source_str}"
    )
    st.sidebar.caption(
        "“AI-inflected” = the posting mentions at least one Facet 5 (Generative AI) "
        "or Facet 6 (MLOps) skill. Dual-use infra (Docker, Kubernetes, FastAPI, CI/CD) "
        "is intentionally excluded so the backend control group is not falsely flagged."
    )

    role_label = ROLE_LABELS.get(role, role)
    role_postings = postings[postings["role"] == role]
    role_pen = penetration[penetration["role"] == role].iloc[0]
    role_premium = premium[premium["role"] == role]

    _render_headline(role_label, role_pen, role_premium)
    _render_skill_chart(role_label, skill_demand, role)
    _render_premium_panel(role_premium)
    _render_sample_postings(role_label, role_postings)
    _render_penetration_context(penetration, role)


# ---------------------------------------------------------------------------
# 1. Headline — the one-sentence answer
# ---------------------------------------------------------------------------

def _render_headline(role_label: str, role_pen: pd.Series, role_premium: pd.DataFrame) -> None:
    _section(
        "The headline",
        f"for {role_label}",
    )

    n = int(role_pen["n_postings"])
    ai_share = float(role_pen["ai_inflected_share"]) * 100

    ai_row = role_premium[role_premium["group"] == "ai_inflected"]
    non_row = role_premium[role_premium["group"] == "non_ai"]
    ai_med = _safe_median(ai_row)
    non_med = _safe_median(non_row)

    cols = st.columns(3)
    cols[0].metric("Postings", n)
    cols[1].metric("AI-inflected share", f"{ai_share:.0f}%")
    if ai_med is not None and non_med is not None:
        delta_pct = (ai_med - non_med) / non_med * 100
        cols[2].metric(
            "AI vs non-AI median salary",
            f"NT${int(ai_med):,} / NT${int(non_med):,}",
            f"{delta_pct:+.0f}%",
        )
    elif ai_med is not None:
        cols[2].metric("AI median salary", f"NT${int(ai_med):,}", "no non-AI baseline")
    elif non_med is not None:
        cols[2].metric("Non-AI median salary", f"NT${int(non_med):,}", "no AI baseline")
    else:
        cols[2].metric("Median salary", "—", "no salary data")

    st.markdown(
        f'<div class="sp-headline">{_one_sentence(role_label, n, ai_share, ai_med, non_med)}</div>',
        unsafe_allow_html=True,
    )


def _one_sentence(role_label: str, n: int, ai_share: float, ai_med, non_med) -> str:
    if ai_med is not None and non_med is not None:
        delta = (ai_med - non_med) / non_med * 100
        if delta > 5:
            trend = "carries a premium"
        elif delta < -5:
            trend = "trails non-AI postings"
        else:
            trend = "is essentially flat vs non-AI"
        return (
            f"<b>{role_label}</b> — {n} postings collected; {ai_share:.0f}% list at least one "
            f"AI-era skill. AI-inflected postings have a median salary of NT${int(ai_med):,} / month "
            f"vs NT${int(non_med):,} for non-AI — AI {trend} ({delta:+.0f}%)."
        )
    if ai_med is not None:
        return (
            f"<b>{role_label}</b> — {n} postings collected; {ai_share:.0f}% list at least one "
            f"AI-era skill. AI-inflected median: NT${int(ai_med):,} / month. "
            "No non-AI baseline available."
        )
    if non_med is not None:
        return (
            f"<b>{role_label}</b> — {n} postings collected; {ai_share:.0f}% list at least one "
            f"AI-era skill. Non-AI median: NT${int(non_med):,} / month. "
            "No salary signal yet on the AI-inflected side."
        )
    return (
        f"<b>{role_label}</b> — {n} postings collected; {ai_share:.0f}% list at least one "
        "AI-era skill. Salary data too sparse to compare."
    )


def _safe_median(row: pd.DataFrame):
    if row.empty:
        return None
    val = row.iloc[0]["median_monthly_ntd"]
    if pd.isna(val):
        return None
    return float(val)


# ---------------------------------------------------------------------------
# 2. Skill demand — AI-era highlighted in red
# ---------------------------------------------------------------------------

def _render_skill_chart(role_label: str, skill_demand: pd.DataFrame, role: str) -> None:
    _section("Top skills demanded", f"red = AI-era, teal = foundational")
    role_skills = skill_demand[skill_demand["role"] == role].copy()
    if role_skills.empty:
        st.info("No skill demand signal yet for this role.")
        return

    top = role_skills.sort_values("count", ascending=False).head(15).copy()
    top["pct"] = top["pct_of_role"] * 100
    top["Skill type"] = top["ai_era"].map({True: "AI-era", False: "Foundational"})

    import altair as alt

    chart = (
        alt.Chart(top)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("name:N", sort="-x", title=None, axis=alt.Axis(labelFontSize=12)),
            x=alt.X(
                "pct:Q",
                title="% of postings mentioning this skill",
                axis=alt.Axis(format=".0f", labelFontSize=11),
            ),
            color=alt.Color(
                "Skill type:N",
                scale=alt.Scale(domain=["AI-era", "Foundational"], range=[RED, TEAL]),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[
                alt.Tooltip("name:N", title="Skill"),
                alt.Tooltip("pct:Q", format=".1f", title="% of postings"),
                alt.Tooltip("count:Q", title="postings"),
                alt.Tooltip("Skill type:N"),
            ],
        )
        .properties(height=440)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(
        f"Read this as the curriculum signal for **{role_label}**. A tall red bar means an AI-era "
        "skill is moving into the role's baseline — a candidate to add to the syllabus. "
        "Taxonomy facets 5 (Generative AI) and 6 (MLOps) define the red layer."
    )


# ---------------------------------------------------------------------------
# 3. AI premium — three-card callout
# ---------------------------------------------------------------------------

def _render_premium_panel(role_premium: pd.DataFrame) -> None:
    _section("AI-skill salary premium", "non-AI vs AI-inflected medians")

    ai_row = role_premium[role_premium["group"] == "ai_inflected"]
    non_row = role_premium[role_premium["group"] == "non_ai"]
    ai_med = _safe_median(ai_row)
    non_med = _safe_median(non_row)
    ai_n = int(ai_row.iloc[0]["n_salary_known"]) if not ai_row.empty else 0
    non_n = int(non_row.iloc[0]["n_salary_known"]) if not non_row.empty else 0

    col_non, col_ai, col_delta = st.columns([1, 1, 1.2])
    with col_non:
        _premium_card("Non-AI postings", non_med, non_n)
    with col_ai:
        _premium_card("AI-inflected postings", ai_med, ai_n)
    with col_delta:
        _delta_card(ai_med, non_med, ai_n, non_n)


def _premium_card(label: str, median, n: int) -> None:
    if median is not None:
        body = (
            f'<div class="sp-premium-value">NT${int(median):,}'
            f'<span class="sp-premium-unit"> / month</span></div>'
            f'<div class="sp-premium-foot">median over n = {n} salary-known postings</div>'
        )
    else:
        body = (
            '<div class="sp-premium-value">—</div>'
            '<div class="sp-premium-foot">no salary-known postings</div>'
        )
    st.markdown(
        f'<div class="sp-premium-card">'
        f'<div class="sp-premium-label">{label}</div>'
        f'{body}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _delta_card(ai_med, non_med, ai_n: int, non_n: int) -> None:
    if ai_med is not None and non_med is not None:
        delta = (ai_med - non_med) / non_med * 100
        if delta > 5:
            color = GREEN
        elif delta < -5:
            color = RED
        else:
            color = SLATE_500
        smaller_n = min(ai_n, non_n)
        warn = (
            f'<div class="sp-warn">Small sample (min n = {smaller_n}) — interpret with caution.</div>'
            if smaller_n < 10 else ""
        )
        body = (
            f'<div class="sp-premium-value" style="color:{color}">{delta:+.1f}%</div>'
            f'<div class="sp-premium-foot">AI median vs non-AI median.</div>{warn}'
        )
    else:
        body = (
            '<div class="sp-premium-value">—</div>'
            '<div class="sp-premium-foot">Both sides need salary data to compute.</div>'
        )
    st.markdown(
        f'<div class="sp-premium-card">'
        f'<div class="sp-premium-label">Premium</div>'
        f'{body}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 4. Sample postings — concrete proof
# ---------------------------------------------------------------------------

def _render_sample_postings(role_label: str, role_postings: pd.DataFrame) -> None:
    _section("Sample postings", f"six real listings classified as {role_label}")
    if role_postings.empty:
        st.info("No postings collected for this role yet.")
        return

    sample = role_postings.copy()
    sample["has_salary"] = sample["salary_known"]
    sample = sample.sort_values(
        ["ai_inflected", "has_salary", "monthly_point"],
        ascending=[False, False, False],
    ).head(6)

    display = sample[["title", "company", "source", "ai_inflected", "monthly_point", "skill_names"]].copy()
    display.columns = ["Title", "Company", "Source", "AI", "Monthly NTD", "Skills found"]
    display["AI"] = display["AI"].map({True: "✓", False: ""})
    display["Source"] = display["Source"].str.upper()
    display["Monthly NTD"] = display["Monthly NTD"].map(
        lambda v: f"NT${int(v):,}" if pd.notna(v) else "—"
    )
    display["Skills found"] = display["Skills found"].fillna("").str.slice(0, 80)
    st.dataframe(display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# 5. Cross-role context
# ---------------------------------------------------------------------------

def _render_penetration_context(penetration: pd.DataFrame, current_role: str) -> None:
    _section(
        "AI penetration across the cluster",
        "where this role sits; backend is the non-AI control",
    )
    chart_df = penetration[penetration["role"].isin(ROLE_ORDER)].copy()
    chart_df["AI share (%)"] = chart_df["ai_inflected_share"] * 100
    chart_df["Selected"] = chart_df["role"].map(lambda r: "Selected" if r == current_role else "Other")

    import altair as alt

    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                "role_label:N",
                sort=[ROLE_LABELS[r] for r in ROLE_ORDER],
                title=None,
                axis=alt.Axis(labelAngle=-25, labelFontSize=11),
            ),
            y=alt.Y(
                "AI share (%):Q",
                axis=alt.Axis(format=".0f", labelFontSize=11),
            ),
            color=alt.Color(
                "Selected:N",
                scale=alt.Scale(domain=["Selected", "Other"], range=[TEAL, SLATE_300]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("role_label:N", title="Role"),
                alt.Tooltip("n_postings:Q", title="postings"),
                alt.Tooltip("AI share (%):Q", format=".1f"),
            ],
        )
        .properties(height=280)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


if __name__ == "__main__":
    main()
