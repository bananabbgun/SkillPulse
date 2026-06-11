from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from skillpulse.ingestion.events import append_event_log, write_posting_array
from skillpulse.ingestion.sources.cake import collect_cake
from skillpulse.ingestion.sources.job104 import collect_104
from skillpulse.paths import RAW_DIR, SAMPLE_POSTINGS
from skillpulse.processing.pipeline import load_raw_postings
from skillpulse.schema import RawPosting


DEFAULT_KEYWORDS = [
    "Data Engineer",
    "資料工程師",
    "AI Engineer",
    "Backend Engineer",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect job postings into an append-only event log.")
    parser.add_argument("--sample", action="store_true", help="Append bundled fixtures instead of using the network.")
    parser.add_argument("--source", choices=["104", "cake"], action="append", default=[], help="Live source to collect.")
    parser.add_argument("--keyword", action="append", default=[], help="Keyword to search; repeatable.")
    parser.add_argument("--limit", type=int, default=20, help="Max postings per keyword per source.")
    parser.add_argument("--event-log", type=Path, default=RAW_DIR / "events.jsonl")
    parser.add_argument("--out", type=Path, default=RAW_DIR / "postings_collected.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    postings: List[RawPosting] = []
    keywords = args.keyword or DEFAULT_KEYWORDS

    if args.sample or not args.source:
        postings.extend(load_raw_postings(SAMPLE_POSTINGS))
    else:
        if "104" in args.source:
            postings.extend(collect_104(keywords, limit_per_keyword=args.limit))
        if "cake" in args.source:
            postings.extend(collect_cake(keywords, limit_per_keyword=args.limit))

    event_count = append_event_log(postings, args.event_log)
    array_count = write_posting_array(postings, args.out)
    print(f"Appended {event_count} posting events to {args.event_log}")
    print(f"Wrote {array_count} raw postings to {args.out}")


if __name__ == "__main__":
    main()
