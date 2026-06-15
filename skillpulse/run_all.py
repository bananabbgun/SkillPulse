from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from skillpulse.aggregation import build_marts
from skillpulse.analysis.figures import write_figures
from skillpulse.paths import FIGURES_DIR, MARTS_DIR, SAMPLE_POSTINGS, ensure_output_dirs
from skillpulse.processing.pipeline import normalize_with_engine, write_normalized_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the SkillPulse local MVP pipeline.")
    parser.add_argument("--sample", action="store_true", help="Use data/sample/postings_sample.json.")
    parser.add_argument("--input", type=Path, default=None, help="Raw postings JSON file.")
    parser.add_argument("--require-spark", action="store_true", help="Fail if PySpark is unavailable.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    raw_path = SAMPLE_POSTINGS if args.sample or args.input is None else args.input

    normalized, engine = normalize_with_engine(raw_path, require_spark=args.require_spark)
    postings_df = write_normalized_outputs(normalized)
    skills_df = pd.read_csv(MARTS_DIR / "posting_skills.csv")
    marts = build_marts(postings_df, skills_df)
    write_figures(marts)

    print(f"SkillPulse pipeline complete using {engine}.")
    print(f"Input: {raw_path}")
    print(f"Normalized postings: {len(postings_df)}")
    print(f"Marts: {MARTS_DIR}")
    print(f"Figures: {FIGURES_DIR / 'figure3_ai_penetration.png'}")
    print(f"Figures: {FIGURES_DIR / 'figure4_ai_premium_vs_backend.png'}")
    print(f"Figures: {FIGURES_DIR / 'figure5_skill_demand_data_engineer.png'}")


if __name__ == "__main__":
    main()
