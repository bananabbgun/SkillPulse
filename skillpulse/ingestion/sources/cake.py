from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List

from skillpulse.schema import RawPosting, Source


def collect_cake(
    keywords: Iterable[str],
    limit_per_keyword: int = 20,
    delay_seconds: float = 1.5,
) -> List[RawPosting]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Cake collection requires Playwright. Install with `pip install playwright` "
            "and run `python -m playwright install chromium`."
        ) from exc

    postings: List[RawPosting] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 SkillPulse academic research bot")
        try:
            for keyword in keywords:
                page.goto(f"https://www.cake.me/jobs/{keyword}", wait_until="networkidle")
                page.wait_for_timeout(int(delay_seconds * 1000))
                cards = page.locator("a[href*='/jobs/']").all()[:limit_per_keyword]
                seen = set()
                for card in cards:
                    href = card.get_attribute("href") or ""
                    title = (card.inner_text() or "").splitlines()[0].strip()
                    url = href if href.startswith("http") else f"https://www.cake.me{href}"
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    postings.append(_fetch_cake_detail(page, url, title, delay_seconds))
        finally:
            browser.close()
    return postings


def _fetch_cake_detail(page, url: str, fallback_title: str, delay_seconds: float) -> RawPosting:
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(int(delay_seconds * 1000))
    title = _first_text(page, "h1") or fallback_title
    company = _first_text(page, "[data-testid*='company'], a[href*='/companies/']") or ""
    body = _first_text(page, "main") or page.locator("body").inner_text(timeout=5000)
    salary = _salary_hint(body)
    source_job_id = url.rstrip("/").split("/")[-1]
    return RawPosting(
        source=Source.cake,
        source_job_id=source_job_id,
        url=url,
        title=title,
        company=company,
        jd_text=body,
        salary_raw=salary,
        fetched_at=datetime.now(timezone.utc),
    )


def _first_text(page, selector: str) -> str:
    locator = page.locator(selector).first
    try:
        if locator.count() == 0:
            return ""
        return locator.inner_text(timeout=3000).strip()
    except Exception:
        return ""


def _salary_hint(text: str) -> str:
    for line in text.splitlines():
        if any(token in line for token in ("薪", "NT$", "TWD", "年薪", "月薪")):
            return line.strip()
    return ""

