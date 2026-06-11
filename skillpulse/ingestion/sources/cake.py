from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Iterable, List, Optional
from urllib.parse import quote_plus

from skillpulse.schema import RawPosting, Source


SEARCH_URL = "https://www.cake.me/jobs?q={query}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def collect_cake(
    keywords: Iterable[str],
    limit_per_keyword: int = 20,
    delay_seconds: float = 1.0,
    headed: bool = False,
) -> List[RawPosting]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Cake collection requires Playwright. Install with `python -m pip install -r "
            "requirements-scraping.txt` and `python -m playwright install chromium`."
        ) from exc

    postings: List[RawPosting] = []
    seen_urls: set = set()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        context = browser.new_context(
            locale="zh-TW",
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()
        try:
            for keyword in keywords:
                urls = _collect_search_results(page, keyword, limit_per_keyword, delay_seconds)
                for url in urls:
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    posting = _fetch_detail(page, url, delay_seconds)
                    if posting:
                        postings.append(posting)
                    time.sleep(delay_seconds)
        finally:
            browser.close()
    return postings


def _collect_search_results(page, keyword: str, limit: int, delay_seconds: float) -> List[str]:
    """Load the search page, lazy-scroll a few times, return real /companies/.../jobs/... URLs."""
    url = SEARCH_URL.format(query=quote_plus(keyword))
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(int(delay_seconds * 1000))

    # Lazy-load: Cake renders more cards as you scroll. Stop when we've seen enough.
    seen: set = set()
    results: List[str] = []
    for _ in range(10):
        for anchor in page.locator("a[href*='/companies/'][href*='/jobs/']").all():
            try:
                href = anchor.get_attribute("href") or ""
            except Exception:
                continue
            if not href or href in seen:
                continue
            seen.add(href)
            results.append(_absolute_url(href))
            if len(results) >= limit:
                return results
        page.evaluate("window.scrollBy(0, 1500)")
        page.wait_for_timeout(800)
    return results


def _fetch_detail(page, url: str, delay_seconds: float) -> Optional[RawPosting]:
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            print(f"cake detail load failed for {url}: {exc}")
            return None
    page.wait_for_timeout(int(delay_seconds * 1000))

    try:
        body = page.locator("body").inner_text(timeout=10000)
    except Exception:
        body = ""
    title = _first_text(page, "h1")
    company = _first_text(page, "h2") or _first_text(page, "a[href^='/companies/']")
    salary_raw = _extract_cake_salary(page, body)
    location = _extract_cake_location(page, body)

    source_job_id = _job_id_from_url(url)
    return RawPosting(
        source=Source.cake,
        source_job_id=source_job_id,
        url=url,
        title=title,
        company=company,
        jd_text=body,
        salary_raw=salary_raw,
        location=location,
        seniority_raw="",
        fetched_at=datetime.now(timezone.utc),
    )


def _absolute_url(href: str) -> str:
    href = href.strip()
    if href.startswith("http"):
        return href.split("?")[0]
    if href.startswith("//"):
        return "https:" + href.split("?")[0]
    if href.startswith("/"):
        return "https://www.cake.me" + href.split("?")[0]
    return "https://www.cake.me/" + href.split("?")[0]


def _job_id_from_url(url: str) -> str:
    # e.g. https://www.cake.me/companies/tsmc/jobs/data-engineer-02c7e9
    # -> "tsmc/data-engineer-02c7e9" (company + slug keeps it unique even if slugs collide).
    try:
        path = url.split("cake.me", 1)[1]
    except IndexError:
        return url
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 4 and parts[0] == "companies" and parts[2] == "jobs":
        return f"{parts[1]}/{parts[3]}"
    return parts[-1] if parts else url


def _first_text(page, selector: str) -> str:
    try:
        locator = page.locator(selector).first
        if locator.count() == 0:
            return ""
        return (locator.inner_text(timeout=3000) or "").strip()
    except Exception:
        return ""


_SALARY_LINE = re.compile(
    r"(?:\d[\d,]*\s*(?:[~\-至]\s*\d[\d,]*)?\s*\+?\s*(?:TWD|NT\$|NTD|新台幣)|月薪|年薪|時薪|面議|negotiable|TWD\s*/\s*月)",
    re.IGNORECASE,
)


def _extract_cake_salary(page, body: str) -> str:
    """Cake shows things like '40,000+ TWD / 月' or 'TWD 60,000 - 80,000 / 月'."""
    # Try the dedicated salary span first.
    for sel in ("span:has-text('TWD')", "span:has-text('NT$')", "[class*='salary']"):
        try:
            loc = page.locator(sel).first
            if loc.count():
                txt = (loc.inner_text(timeout=1500) or "").strip()
                if txt and _SALARY_LINE.search(txt):
                    return txt
        except Exception:
            continue
    # Fall back to scanning the body for a likely line.
    for line in body.splitlines():
        line = line.strip()
        if _SALARY_LINE.search(line):
            return line
    return ""


_LOCATION_KEYWORDS = ("台北", "新北", "桃園", "新竹", "台中", "台南", "高雄", "Taipei", "Hsinchu", "Taichung", "Kaohsiung", "remote", "遠端")


def _extract_cake_location(page, body: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if any(token in line for token in _LOCATION_KEYWORDS) and len(line) < 80:
            return line
    return ""
