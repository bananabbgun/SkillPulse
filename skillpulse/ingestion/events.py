from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from skillpulse.schema import RawPosting


def append_event_log(postings: Iterable[RawPosting], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("a", encoding="utf-8") as fh:
        for posting in postings:
            event = {
                "event_type": "posting_seen",
                "event_time": datetime.now(timezone.utc).isoformat(),
                "posting": posting.model_dump(mode="json"),
            }
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
            count += 1
    return count


def read_event_log(path: Path) -> List[RawPosting]:
    postings: List[RawPosting] = []
    if not path.exists():
        return postings
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            event = json.loads(line)
            postings.append(RawPosting.model_validate(event["posting"]))
    return postings


def write_posting_array(postings: Iterable[RawPosting], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [posting.model_dump(mode="json") for posting in postings]
    with path.open("w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    return len(rows)

