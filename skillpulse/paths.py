from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
SAMPLE_POSTINGS = DATA_DIR / "sample" / "postings_sample.json"
RAW_DIR = DATA_DIR / "raw"
LAKE_DIR = DATA_DIR / "lake"
BROWSER_PROFILE_DIR = DATA_DIR / ".playwright_profile"
TAXONOMY_DIR = REPO_ROOT / "taxonomy"
OUTPUT_DIR = REPO_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"
MARTS_DIR = OUTPUT_DIR / "marts"


def ensure_output_dirs() -> None:
    for path in (RAW_DIR, LAKE_DIR, OUTPUT_DIR, FIGURES_DIR, MARTS_DIR):
        path.mkdir(parents=True, exist_ok=True)

