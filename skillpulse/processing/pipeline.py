from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

from skillpulse.classification import RoleClassifier
from skillpulse.extraction import SkillExtractor, ai_inflected, facets_present
from skillpulse.paths import LAKE_DIR, MARTS_DIR, ensure_output_dirs
from skillpulse.schema import NormalizedPosting, RawPosting, parse_salary, parse_seniority_years
from skillpulse.taxonomy import load_role_prototypes, load_skill_taxonomy


def load_raw_postings(path: Path) -> List[RawPosting]:
    with path.open("r", encoding="utf-8") as fh:
        rows = json.load(fh)
    return [RawPosting.model_validate(row) for row in rows]


def normalize_posting(raw: RawPosting, extractor: SkillExtractor, classifier: RoleClassifier) -> NormalizedPosting:
    skills = extractor.extract(" ".join([raw.title, raw.jd_text]))
    return NormalizedPosting(
        posting_id=raw.posting_id,
        source=raw.source,
        title=raw.title,
        company=raw.company,
        role=classifier.classify(raw.title, skills),
        skills=skills,
        facets_present=facets_present(skills),
        ai_inflected=ai_inflected(skills),
        salary=parse_salary(raw.salary_raw),
        seniority_years=parse_seniority_years(raw.seniority_raw),
        posted_date=raw.posted_date,
    )


def normalize_postings(raw_postings: Iterable[RawPosting]) -> List[NormalizedPosting]:
    skills = load_skill_taxonomy()
    roles = load_role_prototypes()
    extractor = SkillExtractor(skills)
    classifier = RoleClassifier(roles)
    return [normalize_posting(raw, extractor, classifier) for raw in raw_postings]


def normalize_with_engine(raw_path: Path, require_spark: bool = False) -> Tuple[List[NormalizedPosting], str]:
    """Run the normalizer through local PySpark when available, otherwise pandas/Python.

    The transformation function is shared, so the fallback produces identical output.
    """
    try:
        from pyspark.sql import SparkSession  # type: ignore
    except ImportError:
        if require_spark:
            raise
        raw_postings = load_raw_postings(raw_path)
        return normalize_postings(raw_postings), "pandas-fallback"

    spark = (
        SparkSession.builder.master("local[*]")
        .appName("skillpulse-local-mvp")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    try:
        rows = spark.read.option("multiLine", "true").json(str(raw_path)).toJSON().collect()
        raw_postings = [RawPosting.model_validate(json.loads(row)) for row in rows]
        return normalize_postings(raw_postings), "pyspark-local"
    finally:
        spark.stop()


def write_normalized_outputs(normalized: List[NormalizedPosting]) -> pd.DataFrame:
    ensure_output_dirs()
    flat_rows = []
    skill_rows = []
    for posting in normalized:
        base = posting.model_dump(mode="json")
        salary = base.pop("salary")
        skills = base.pop("skills")
        base.pop("facets_present")
        flat_rows.append(
            {
                **base,
                "skill_ids": ",".join(skill["skill_id"] for skill in skills),
                "skill_names": ", ".join(skill["name"] for skill in skills),
                "facets_present": ",".join(str(skill["facet"]) for skill in skills),
                "salary_known": salary["salary_known"],
                "salary_period": salary["period"],
                "monthly_min": salary["monthly_min"],
                "monthly_max": salary["monthly_max"],
                "monthly_point": posting.salary.monthly_point,
            }
        )
        for skill in skills:
            skill_rows.append(
                {
                    "posting_id": posting.posting_id,
                    "role": posting.role.value,
                    "skill_id": skill["skill_id"],
                    "name": skill["name"],
                    "facet": skill["facet"],
                    "ai_era": skill["ai_era"],
                }
            )

    postings_df = pd.DataFrame(flat_rows)
    skills_df = pd.DataFrame(skill_rows)
    postings_df.to_csv(MARTS_DIR / "normalized_postings.csv", index=False, encoding="utf-8")
    skills_df.to_csv(MARTS_DIR / "posting_skills.csv", index=False, encoding="utf-8")

    postings_df.to_parquet(LAKE_DIR / "normalized_postings.parquet", index=False)
    skills_df.to_parquet(LAKE_DIR / "posting_skills.parquet", index=False)
    return postings_df
