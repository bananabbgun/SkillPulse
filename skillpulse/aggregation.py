from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from skillpulse.paths import MARTS_DIR, ensure_output_dirs
from skillpulse.schema import ClusterRole


ROLE_ORDER = [
    "data_engineer",
    "data_analyst",
    "data_scientist",
    "ml_engineer",
    "algorithm_engineer",
    "ai_engineer",
    "backend",
]


ROLE_LABELS = {
    "data_engineer": "Data Engineer",
    "data_analyst": "Data Analyst",
    "data_scientist": "Data Scientist",
    "ml_engineer": "ML Engineer",
    "algorithm_engineer": "Algorithm Engineer",
    "ai_engineer": "AI Engineer",
    "backend": "Backend Control",
    "other": "Other",
}


def build_marts(postings_df: pd.DataFrame, skills_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    ensure_output_dirs()
    penetration = _ai_penetration(postings_df)
    premium = _ai_premium(postings_df)
    skill_demand = _skill_demand(postings_df, skills_df)

    marts = {
        "role_ai_penetration": penetration,
        "ai_premium": premium,
        "role_skill_demand": skill_demand,
    }
    for name, df in marts.items():
        df.to_csv(MARTS_DIR / f"{name}.csv", index=False, encoding="utf-8")
        df.to_parquet(MARTS_DIR / f"{name}.parquet", index=False)
    _try_write_duckdb(marts, MARTS_DIR / "skillpulse.duckdb")
    return marts


def _ai_penetration(postings_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        postings_df.groupby("role", dropna=False)
        .agg(n_postings=("posting_id", "count"), ai_inflected=("ai_inflected", "sum"))
        .reset_index()
    )
    grouped["ai_inflected_share"] = grouped["ai_inflected"] / grouped["n_postings"]
    return _with_role_order(grouped)


def _ai_premium(postings_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    df = postings_df[postings_df["role"].isin(ROLE_ORDER)].copy()
    df["group"] = df["ai_inflected"].map(lambda value: "ai_inflected" if value else "non_ai")
    for (role, group), part in df.groupby(["role", "group"]):
        salary_known = part[part["salary_known"] & part["monthly_point"].notna()]
        rows.append(
            {
                "role": role,
                "group": group,
                "n": int(len(part)),
                "n_salary_known": int(len(salary_known)),
                "median_monthly_ntd": None
                if salary_known.empty
                else float(salary_known["monthly_point"].median()),
                "mean_skill_count": float(part["skill_ids"].map(_skill_count).mean()),
            }
        )
    result = pd.DataFrame(rows)
    return _with_role_order(result)


def _skill_demand(postings_df: pd.DataFrame, skills_df: pd.DataFrame) -> pd.DataFrame:
    role_counts = postings_df.groupby("role")["posting_id"].count().to_dict()
    grouped = (
        skills_df.groupby(["role", "skill_id", "name", "facet", "ai_era"])
        .size()
        .reset_index(name="count")
    )
    grouped["pct_of_role"] = grouped.apply(
        lambda row: row["count"] / role_counts.get(row["role"], 1), axis=1
    )
    grouped = grouped.sort_values(["role", "count", "name"], ascending=[True, False, True])
    return _with_role_order(grouped)


def _with_role_order(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "role" not in df.columns:
        return df
    order = {role: index for index, role in enumerate(ROLE_ORDER)}
    df = df.copy()
    df["role_order"] = df["role"].map(lambda role: order.get(role, 999))
    df["role_label"] = df["role"].map(lambda role: ROLE_LABELS.get(role, str(role)))
    return df.sort_values(["role_order", "role"]).drop(columns=["role_order"]).reset_index(drop=True)


def _skill_count(value: object) -> int:
    if not isinstance(value, str) or not value:
        return 0
    return len([item for item in value.split(",") if item])


def _try_write_duckdb(marts: Dict[str, pd.DataFrame], db_path: Path) -> None:
    try:
        import duckdb  # type: ignore
    except ImportError:
        return
    connection = duckdb.connect(str(db_path))
    try:
        for name, df in marts.items():
            connection.register("df", df)
            connection.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df")
            connection.unregister("df")
    finally:
        connection.close()

