from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from skillpulse.aggregation import ROLE_LABELS, ROLE_ORDER
from skillpulse.paths import FIGURES_DIR, MARTS_DIR


st.set_page_config(page_title="SkillPulse", layout="wide")


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
    st.title("SkillPulse")
    marts = load_marts()
    postings = marts["postings"]
    penetration = marts["penetration"]
    premium = marts["premium"]
    skill_demand = marts["skill_demand"]

    roles = [role for role in ROLE_ORDER if role in set(postings["role"])]
    role = st.sidebar.selectbox(
        "Role",
        roles,
        index=roles.index("data_engineer") if "data_engineer" in roles else 0,
        format_func=lambda value: ROLE_LABELS.get(value, value),
    )

    selected = postings[postings["role"] == role]
    selected_penetration = penetration[penetration["role"] == role].iloc[0]
    selected_premium = premium[premium["role"] == role]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Postings", int(selected_penetration["n_postings"]))
    metric_cols[1].metric("AI Penetration", f"{selected_penetration['ai_inflected_share'] * 100:.0f}%")
    metric_cols[2].metric("Salary Known", int(selected["salary_known"].sum()))
    metric_cols[3].metric("Mean Skills", f"{_mean_skill_count(selected):.1f}")

    left, right = st.columns((1.1, 1))
    with left:
        st.subheader("Role-Level AI Penetration")
        chart_df = penetration[penetration["role"].isin(ROLE_ORDER)].copy()
        chart_df["AI Share (%)"] = chart_df["ai_inflected_share"] * 100
        st.bar_chart(chart_df, x="role_label", y="AI Share (%)", color="#0f766e", height=340)

    with right:
        st.subheader("AI Premium vs Backend Control")
        salary_df = premium[premium["median_monthly_ntd"].notna()].copy()
        salary_df["series"] = salary_df["group"].map(
            {"ai_inflected": "AI-inflected", "non_ai": "Non-AI"}
        )
        st.bar_chart(
            salary_df,
            x="role_label",
            y="median_monthly_ntd",
            color="series",
            height=340,
        )

    lower_left, lower_right = st.columns((1, 1))
    with lower_left:
        st.subheader(f"{ROLE_LABELS.get(role, role)} Skill Demand")
        top_skills = (
            skill_demand[skill_demand["role"] == role]
            .sort_values(["count", "name"], ascending=[False, True])
            .head(15)
            .copy()
        )
        top_skills["Demand (%)"] = top_skills["pct_of_role"] * 100
        st.dataframe(
            top_skills[["name", "facet", "ai_era", "count", "Demand (%)"]],
            use_container_width=True,
            hide_index=True,
        )

    with lower_right:
        st.subheader("Figure Outputs")
        fig1 = FIGURES_DIR / "figure1_ai_penetration.png"
        fig2 = FIGURES_DIR / "figure2_ai_premium_vs_backend.png"
        if fig1.exists():
            st.image(str(fig1), caption="Figure 1")
        if fig2.exists():
            st.image(str(fig2), caption="Figure 2")


def _mean_skill_count(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return float(df["skill_ids"].fillna("").map(lambda value: len([x for x in str(value).split(",") if x])).mean())


if __name__ == "__main__":
    main()
