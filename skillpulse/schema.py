"""
SkillPulse — Data Contract (schema.py)
======================================

The single source of truth for the shape of data as it flows:

    RawPosting  --(extract + normalize + classify)-->  NormalizedPosting
                                                              |
                                                       aggregation
                                                              v
                          RoleAIPenetration / AIPremiumRow / RoleSkillDemand  (serving marts)

Everything downstream (extractor, classifier, aggregations, dashboard, API) imports
these types. Do NOT invent parallel schemas in other modules.

Requires: pydantic>=2

This file also ships a REFERENCE Taiwan salary parser (`parse_salary`). It handles the
common messy cases; extend it as you see real data. Figure 2 (AI premium) uses only
rows where `SalaryInfo.salary_known` is True and a monthly value exists.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Source(str, Enum):
    job104 = "104"
    cake = "cake"
    other = "other"


class ClusterRole(str, Enum):
    data_engineer = "data_engineer"
    data_scientist = "data_scientist"
    data_analyst = "data_analyst"
    ml_engineer = "ml_engineer"
    algorithm_engineer = "algorithm_engineer"
    ai_engineer = "ai_engineer"
    backend = "backend"          # CONTROL group (in_cluster = False)
    other = "other"

    @property
    def in_cluster(self) -> bool:
        return self not in (ClusterRole.backend, ClusterRole.other)


class SalaryPeriod(str, Enum):
    monthly = "monthly"
    yearly = "yearly"
    hourly = "hourly"
    unknown = "unknown"


# ---------------------------------------------------------------------------
# Salary
# ---------------------------------------------------------------------------

class SalaryInfo(BaseModel):
    """Normalized salary. `monthly_*` are the comparable fields used in analysis."""
    raw: str = ""
    salary_known: bool = False
    period: SalaryPeriod = SalaryPeriod.unknown
    amount_min: Optional[float] = None      # in the original period's units (NTD)
    amount_max: Optional[float] = None
    monthly_min: Optional[float] = None     # normalized to monthly NTD (comparable)
    monthly_max: Optional[float] = None

    @property
    def monthly_point(self) -> Optional[float]:
        """A single comparable monthly figure (midpoint, or whichever bound exists)."""
        lo, hi = self.monthly_min, self.monthly_max
        if lo is not None and hi is not None:
            return (lo + hi) / 2
        return lo if lo is not None else hi


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

class ExtractedSkill(BaseModel):
    skill_id: str          # canonical id from skills_v1.yaml
    name: str
    facet: int             # 1..9
    ai_era: bool = False


# ---------------------------------------------------------------------------
# Postings
# ---------------------------------------------------------------------------

class RawPosting(BaseModel):
    """Exactly what the scraper emits. Fixtures in data/sample/ conform to this."""
    source: Source
    source_job_id: str
    url: str = ""
    title: str = ""
    company: str = ""
    jd_text: str = ""                  # description + requirements, mixed zh/en
    salary_raw: str = ""               # e.g. "月薪 55,000~75,000 元", "面議"
    location: str = ""
    posted_date: Optional[date] = None
    seniority_raw: str = ""            # e.g. "3年以上工作經驗"
    fetched_at: Optional[datetime] = None

    @property
    def posting_id(self) -> str:
        return f"{self.source.value}:{self.source_job_id}"


class NormalizedPosting(BaseModel):
    """The refined record produced by the processing pipeline."""
    posting_id: str
    source: Source
    title: str = ""
    company: str = ""
    role: ClusterRole = ClusterRole.other
    skills: List[ExtractedSkill] = Field(default_factory=list)
    facets_present: List[int] = Field(default_factory=list)
    ai_inflected: bool = False           # has >=1 ai_era skill
    salary: SalaryInfo = Field(default_factory=SalaryInfo)
    seniority_years: Optional[int] = None
    posted_date: Optional[date] = None

    @property
    def skill_count(self) -> int:
        return len(self.skills)

    @property
    def in_cluster(self) -> bool:
        return self.role.in_cluster


# ---------------------------------------------------------------------------
# Serving marts (feed dashboard + API)
# ---------------------------------------------------------------------------

class RoleAIPenetration(BaseModel):
    """Figure 1."""
    role: ClusterRole
    n_postings: int
    ai_inflected: int
    ai_inflected_share: float            # 0..1


class AIPremiumRow(BaseModel):
    """Figure 2. One row per (role, group)."""
    role: ClusterRole
    group: str                           # "ai_inflected" | "non_ai"
    n: int
    n_salary_known: int
    median_monthly_ntd: Optional[float] = None
    mean_skill_count: float = 0.0


class RoleSkillDemand(BaseModel):
    """Figure 3 / API. One row per (role, skill)."""
    role: ClusterRole
    skill_id: str
    name: str
    facet: int
    ai_era: bool
    count: int
    pct_of_role: float                   # 0..1


# ---------------------------------------------------------------------------
# Reference Taiwan salary parser
# ---------------------------------------------------------------------------

_NEGOTIABLE = ("面議", "面試後", "依公司規定", "電議", "待遇面議", "面談")
_MONTHS_PER_YEAR = 12          # documented assumption; TW often pays 13-14 months
_HOURS_PER_MONTH = 176         # 22 working days * 8h, for hourly -> monthly equiv


def _to_number(s: str) -> Optional[float]:
    s = s.replace(",", "").replace("，", "").strip()
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def parse_salary(raw: str) -> SalaryInfo:
    """
    Best-effort parser for Taiwan job-board salary strings. Extend as real data shows
    new patterns. Handles: negotiable, monthly/yearly/hourly, ranges, '以上' open tops.
    Examples it covers:
        "面議"                          -> salary_known=False
        "月薪 40,000~60,000 元"         -> monthly 40000..60000
        "月薪 55000元以上"              -> monthly 55000..None
        "年薪 1,200,000 元"            -> yearly -> monthly ~100000
        "時薪 200 元"                  -> hourly -> monthly equiv
    """
    info = SalaryInfo(raw=raw or "")
    if not raw or any(k in raw for k in _NEGOTIABLE):
        return info

    text = raw.replace("，", ",")

    if any(k in text for k in ("年薪", "/年", "per year", "annual")):
        period = SalaryPeriod.yearly
    elif any(k in text for k in ("時薪", "/hr", "per hour", "hourly")):
        period = SalaryPeriod.hourly
    elif any(k in text for k in ("月薪", "/月", "per month", "monthly")):
        period = SalaryPeriod.monthly
    else:
        period = SalaryPeriod.monthly  # TW default when a number is present w/o unit

    # range "a~b" / "a-b" / "a 到 b"
    parts = re.split(r"[~\-—到至]", text)
    nums = [n for n in (_to_number(p) for p in parts) if n is not None]

    amount_min = amount_max = None
    if len(nums) >= 2:
        amount_min, amount_max = nums[0], nums[1]
    elif len(nums) == 1:
        amount_min = nums[0]
        if "以上" not in text:       # single value w/o "以上" -> treat as point
            amount_max = nums[0]

    if amount_min is None and amount_max is None:
        return info

    def _monthly(v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if period == SalaryPeriod.yearly:
            return v / _MONTHS_PER_YEAR
        if period == SalaryPeriod.hourly:
            return v * _HOURS_PER_MONTH
        return v

    info.salary_known = True
    info.period = period
    info.amount_min = amount_min
    info.amount_max = amount_max
    info.monthly_min = _monthly(amount_min)
    info.monthly_max = _monthly(amount_max)
    return info


def parse_seniority_years(raw: str) -> Optional[int]:
    """'3年以上工作經驗' -> 3 ; '不拘'/'' -> None."""
    if not raw:
        return None
    m = re.search(r"(\d+)\s*年", raw)
    return int(m.group(1)) if m else None
