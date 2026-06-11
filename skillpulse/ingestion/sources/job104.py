from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

import requests

from skillpulse.schema import RawPosting, Source


SEARCH_URL = "https://www.104.com.tw/jobs/search/list"
DETAIL_URL = "https://www.104.com.tw/job/ajax/content/{job_id}"
REFERER = "https://www.104.com.tw/jobs/search/"


def collect_104(
    keywords: Iterable[str],
    limit_per_keyword: int = 20,
    delay_seconds: float = 1.5,
    timeout_seconds: float = 15.0,
) -> List[RawPosting]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 SkillPulse academic research bot",
            "Accept": "application/json, text/plain, */*",
            "Referer": REFERER,
        }
    )
    postings: List[RawPosting] = []
    for keyword in keywords:
        params = {
            "ro": "0",
            "kwop": "7",
            "keyword": keyword,
            "expansionType": "area,spec,com,job,wf,wktm",
            "mode": "s",
            "jobsource": "skillpulse_academic",
            "page": "1",
        }
        response = session.get(SEARCH_URL, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("data", {}).get("list", [])[:limit_per_keyword]
        for row in rows:
            postings.append(_row_to_posting(row, session, timeout_seconds))
            time.sleep(delay_seconds)
        time.sleep(delay_seconds)
    return postings


def _row_to_posting(row: Dict, session: requests.Session, timeout_seconds: float) -> RawPosting:
    source_job_id = str(row.get("jobNo") or row.get("link", {}).get("job") or row.get("job_id") or "")
    job_id = source_job_id.lstrip("job/")
    title = str(row.get("jobName") or row.get("title") or "")
    company = str(row.get("custName") or row.get("company") or "")
    url = _job_url(job_id)
    detail = _fetch_detail(session, job_id, url, timeout_seconds) if job_id else {}
    jd_text = _detail_text(detail) or str(row.get("description") or row.get("desc") or "")
    salary_raw = str(row.get("salaryDesc") or row.get("salary") or detail.get("salary") or "")
    location = str(row.get("jobAddrNoDesc") or row.get("addressRegion") or detail.get("address") or "")
    seniority = str(row.get("periodDesc") or detail.get("condition", {}).get("workExp") or "")

    return RawPosting(
        source=Source.job104,
        source_job_id=job_id or source_job_id,
        url=url,
        title=title,
        company=company,
        jd_text=jd_text,
        salary_raw=salary_raw,
        location=location,
        seniority_raw=seniority,
        fetched_at=datetime.now(timezone.utc),
    )


def _fetch_detail(session: requests.Session, job_id: str, referer: str, timeout_seconds: float) -> Dict:
    headers = {"Referer": referer}
    response = session.get(DETAIL_URL.format(job_id=job_id), headers=headers, timeout=timeout_seconds)
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", payload)


def _detail_text(detail: Dict) -> str:
    if not detail:
        return ""
    pieces = [
        detail.get("jobDetail", {}).get("jobDescription"),
        detail.get("condition", {}).get("other"),
        " ".join(detail.get("condition", {}).get("specialty", []) or []),
        " ".join(detail.get("condition", {}).get("skill", []) or []),
    ]
    return "\n".join(str(piece) for piece in pieces if piece)


def _job_url(job_id: Optional[str]) -> str:
    if not job_id:
        return ""
    return f"https://www.104.com.tw/job/{job_id}"

