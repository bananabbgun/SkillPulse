from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlencode

import requests

from skillpulse.paths import BROWSER_PROFILE_DIR
from skillpulse.schema import RawPosting, Source


SEARCH_URL = "https://www.104.com.tw/jobs/search/list"
DETAIL_URL = "https://www.104.com.tw/job/ajax/content/{job_id}"
SEARCH_PAGE_URL = "https://www.104.com.tw/jobs/search/?{query}"
REFERER = "https://www.104.com.tw/jobs/search/?jobsource=joblist_search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def collect_104(
    keywords: Iterable[str],
    limit_per_keyword: int = 20,
    delay_seconds: float = 1.5,
    timeout_seconds: float = 15.0,
    browser_fallback: bool = True,
    headed_browser: bool = False,
    cdp_port: Optional[int] = None,
) -> List[RawPosting]:
    keywords = list(keywords)
    # CDP attach (use an already-running Chrome the user has authenticated) is the most
    # reliable bypass for Cloudflare's pure-JS challenges, so try it before anything else.
    if cdp_port is not None:
        return collect_104_browser(
            keywords=keywords,
            limit_per_keyword=limit_per_keyword,
            delay_seconds=delay_seconds,
            headed=True,
            cdp_port=cdp_port,
        )
    # If the caller explicitly asked for the headed browser, skip the plain-requests path
    # entirely. Cloudflare almost always blocks the raw HTTP route, and the extra latency
    # before the browser pops up just hides which step is waiting.
    if headed_browser and browser_fallback:
        return collect_104_browser(
            keywords=keywords,
            limit_per_keyword=limit_per_keyword,
            delay_seconds=delay_seconds,
            headed=True,
        )
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": REFERER,
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    postings: List[RawPosting] = []
    try:
        for keyword in keywords:
            _warm_session(session, keyword, timeout_seconds)
            params = {
                "ro": "0",
                "kwop": "7",
                "keyword": keyword,
                "expansionType": "area,spec,com,job,wf,wktm",
                "mode": "s",
                "jobsource": "joblist_search",
                "page": "1",
            }
            headers = {
                "Referer": _search_page_url(keyword),
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
            response = session.get(SEARCH_URL, params=params, headers=headers, timeout=timeout_seconds)
            _raise_for_104(response, keyword)
            try:
                payload = response.json()
            except json.JSONDecodeError as decode_exc:
                # 200 OK but HTML body (typical when Cloudflare serves a challenge instead
                # of the JSON endpoint). Convert to RuntimeError so the browser fallback
                # in the outer try/except can fire.
                snippet = response.text[:2000].replace("\n", " ").replace("\r", " ")
                raise RuntimeError(
                    f"104 returned non-JSON for keyword={keyword!r} (status={response.status_code}). "
                    f"Likely Cloudflare challenge. Body preview: {snippet}"
                ) from decode_exc
            rows = payload.get("data", {}).get("list", [])[:limit_per_keyword]
            for row in rows:
                postings.append(_row_to_posting(row, session, timeout_seconds))
                time.sleep(delay_seconds)
            time.sleep(delay_seconds)
        return postings
    except RuntimeError as exc:
        if browser_fallback and _looks_like_browser_challenge(str(exc)):
            return collect_104_browser(
                keywords=keywords,
                limit_per_keyword=limit_per_keyword,
                delay_seconds=delay_seconds,
                headed=headed_browser,
            )
        raise


def _open_persistent_context(playwright, headed: bool):
    """Launch Chromium with a persistent profile so Cloudflare clearance cookies survive runs.

    Stealth patches are applied per-page. The first headed run is the one expected to clear
    Cloudflare (sometimes manually); subsequent runs reuse cf_clearance until it expires.
    """
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(BROWSER_PROFILE_DIR),
        headless=not headed,
        locale="zh-TW",
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 900},
        timezone_id="Asia/Taipei",
        # These flags hide the most obvious automation tells.
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )


class _CdpAttachedContext:
    """Adapter so a CDP-attached context can be used in the same `with`-like flow."""

    def __init__(self, browser, context, owns_browser: bool = True):
        self._browser = browser
        self._context = context
        self._owns_browser = owns_browser

    def new_page(self):
        return self._context.new_page()

    def close(self):
        # When attached via CDP we intentionally do NOT close the user's Chrome —
        # we only disconnect from it so their browser keeps running.
        try:
            if self._owns_browser:
                self._browser.close()
        except Exception:
            pass


def _attach_cdp_context(playwright, cdp_port: int):
    """Attach to a Chrome already running with --remote-debugging-port=<cdp_port>.

    Uses the existing default context (and its cookies), so Cloudflare sees the user's
    real Chrome that has presumably already cleared the challenge. timeout is bumped to
    60s because enumerating many existing tabs (especially ones with iframes) can be slow.
    """
    endpoint = f"http://localhost:{cdp_port}"
    try:
        browser = playwright.chromium.connect_over_cdp(endpoint, timeout=60000)
    except Exception as exc:
        raise RuntimeError(
            f"Could not connect to Chrome over CDP at {endpoint}. "
            "Start Chrome first with --remote-debugging-port and keep ONE blank tab open. "
            "Example (Windows PowerShell): "
            "& \"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe\" "
            "--remote-debugging-port=9222 --user-data-dir=\"$env:TEMP\\skillpulse-chrome\""
        ) from exc
    if not browser.contexts:
        context = browser.new_context(
            locale="zh-TW",
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
        )
    else:
        context = browser.contexts[0]
    return _CdpAttachedContext(browser=browser, context=context, owns_browser=False)


def _new_stealth_page(context, apply_stealth: bool = True):
    page = context.new_page()
    if not apply_stealth:
        return page
    try:
        from playwright_stealth import stealth_sync  # type: ignore

        stealth_sync(page)
    except ImportError:
        print("playwright-stealth not installed; running without stealth patches.")
    return page


def collect_104_browser(
    keywords: Iterable[str],
    limit_per_keyword: int = 20,
    delay_seconds: float = 1.5,
    headed: bool = False,
    cdp_port: Optional[int] = None,
) -> List[RawPosting]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "104 blocked the JSON endpoint with a browser challenge, and Playwright "
            "is not installed for browser fallback. Run `python -m pip install -r "
            "requirements-scraping.txt` and `python -m playwright install chromium`, "
            "then retry. If headless Chromium is still challenged, add `--headed-browser`."
        ) from exc

    postings: List[RawPosting] = []
    with sync_playwright() as playwright:
        if cdp_port is not None:
            context = _attach_cdp_context(playwright, cdp_port)
            apply_stealth = False  # User's real Chrome doesn't need (or want) patching.
        else:
            context = _open_persistent_context(playwright, headed=headed)
            apply_stealth = True
        page = _new_stealth_page(context, apply_stealth=apply_stealth)
        try:
            _warm_browser_session(page, headed=headed or cdp_port is not None, cdp=cdp_port is not None)
            for keyword in keywords:
                search_url = _browser_search_page_url(keyword)
                _goto_104(page, search_url)
                _wait_for_challenge_if_present(page, headed=headed)
                page.wait_for_timeout(int(delay_seconds * 1000))
                rows = _fetch_search_rows_in_browser(page, keyword, limit_per_keyword)
                if rows:
                    for row in rows:
                        url = _job_url(_strip_job_prefix(str(row.get("jobNo") or "")))
                        if url:
                            postings.append(_fetch_104_browser_detail(page, url, delay_seconds, fallback_row=row))
                        else:
                            postings.append(_row_to_browser_posting(row))
                        time.sleep(delay_seconds)
                    continue
                urls = _collect_job_urls_from_page(page, limit_per_keyword)
                if not urls:
                    print(f"104 browser fallback: no job links for keyword {keyword!r}; trying next keyword.")
                    continue
                for url in urls:
                    postings.append(_fetch_104_browser_detail(page, url, delay_seconds))
                    time.sleep(delay_seconds)
        finally:
            context.close()
    if not postings:
        raise RuntimeError(
            "104 browser fallback completed but collected zero postings. "
            "Likely Cloudflare is still blocking. Try a Chinese role keyword such as `資料工程師`, "
            "lower `--limit`, run with `--headed-browser` and manually solve the challenge, "
            "or fall back to the --url-file path."
        )
    return postings


def collect_104_urls(
    urls: Iterable[str],
    delay_seconds: float = 1.5,
    headed: bool = False,
    cdp_port: Optional[int] = None,
) -> List[RawPosting]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "104 URL import requires Playwright. Run `python -m pip install -r "
            "requirements-scraping.txt` and `python -m playwright install chromium`."
        ) from exc

    clean_urls = [_normalize_104_url(url) for url in urls if url.strip()]
    postings: List[RawPosting] = []
    with sync_playwright() as playwright:
        if cdp_port is not None:
            context = _attach_cdp_context(playwright, cdp_port)
            apply_stealth = False
        else:
            context = _open_persistent_context(playwright, headed=headed)
            apply_stealth = True
        page = _new_stealth_page(context, apply_stealth=apply_stealth)
        try:
            _warm_browser_session(page, headed=headed or cdp_port is not None, cdp=cdp_port is not None)
            for url in clean_urls:
                postings.append(_fetch_104_browser_detail(page, url, delay_seconds))
                time.sleep(delay_seconds)
        finally:
            context.close()
    return postings


def read_urls_file(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.strip().startswith("#")]


def _warm_session(session: requests.Session, keyword: str, timeout_seconds: float) -> None:
    """Load the public search page first so 104 can set normal browser cookies."""
    url = _search_page_url(keyword)
    response = session.get(url, timeout=timeout_seconds)
    if response.status_code >= 400:
        _raise_for_104(response, keyword)
    time.sleep(0.5)


def _raise_for_104(response: requests.Response, keyword: str) -> None:
    if response.status_code < 400:
        return
    # Keep more of the body so challenge tokens like "Just a moment" / "cf-mitigated"
    # are reliably visible to _looks_like_browser_challenge.
    snippet = response.text[:2000].replace("\n", " ").replace("\r", " ")
    raise RuntimeError(
        "104 rejected the request "
        f"(status={response.status_code}, keyword={keyword!r}, url={response.url}). "
        "This is usually bot protection or a changed endpoint. "
        f"Response preview: {snippet}"
    )


def _looks_like_browser_challenge(message: str) -> bool:
    lowered = message.lower()
    return (
        "just a moment" in lowered
        or "cloudflare" in lowered
        or "cf-mitigated" in lowered
        or "cf-chl" in lowered
        or "status=403" in lowered
        or "status=503" in lowered
    )


def _strip_job_prefix(value: str) -> str:
    """Correctly strip the 'job/' prefix if present (str.lstrip removes char-set, not prefix)."""
    if value.startswith("job/"):
        return value[len("job/"):]
    return value


def _search_page_url(keyword: str) -> str:
    query = urlencode(
        {
            "ro": "0",
            "kwop": "7",
            "keyword": keyword,
            "expansionType": "area,spec,com,job,wf,wktm",
            "mode": "s",
            "jobsource": "joblist_search",
        }
    )
    return SEARCH_PAGE_URL.format(query=query)


def _browser_search_page_url(keyword: str) -> str:
    query = urlencode({"keyword": keyword, "jobsource": "joblist_search"})
    return SEARCH_PAGE_URL.format(query=query)


def _row_to_posting(row: Dict, session: requests.Session, timeout_seconds: float) -> RawPosting:
    source_job_id = str(row.get("jobNo") or row.get("link", {}).get("job") or row.get("job_id") or "")
    job_id = _strip_job_prefix(source_job_id)
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


def _normalize_104_url(url: str) -> str:
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/"):
        url = "https://www.104.com.tw" + url
    return url.split("?")[0]


def _warm_browser_session(page, headed: bool, cdp: bool = False) -> None:
    """Open the 104 home page once so Cloudflare can grant cf_clearance before we hit the search list.

    Headed mode prints a loud, flushed instruction so the user knows to bring the browser
    window to the foreground and solve the challenge if shown. CDP mode assumes the user's
    real Chrome has already cleared Cloudflare; we still wait briefly in case it hasn't.
    """
    if headed and not cdp:
        print("=" * 70, flush=True)
        print("OPENING CHROMIUM WINDOW. Please bring it to the foreground.", flush=True)
        print("If a Cloudflare 'Verify you are human' page appears, CLICK THE CHECKBOX.", flush=True)
        print("This script will wait up to 120 seconds for you to solve it.", flush=True)
        print("=" * 70, flush=True)
    elif cdp:
        print("=" * 70, flush=True)
        print("Attached to your existing Chrome via CDP. Using its cookies.", flush=True)
        print("If 104 prompts a Cloudflare challenge in that tab, please solve it manually.", flush=True)
        print("=" * 70, flush=True)
    _goto_104(page, "https://www.104.com.tw/")
    _wait_for_challenge_if_present(page, headed=headed or cdp)
    page.wait_for_timeout(1500)


def _wait_for_challenge_if_present(page, headed: bool = False) -> None:
    """Poll for up to ~120s (headed) / ~30s (headless) waiting for Cloudflare to clear.

    In headed mode the user may need to click the checkbox; we keep polling the page title
    until it stops saying 'Just a moment...'. In headless mode the timeout is short — if it
    doesn't clear automatically, the caller will fall back / retry.
    """
    deadline = time.time() + (120 if headed else 30)
    interval_ms = 2000
    notified = False
    while time.time() < deadline:
        title = ""
        try:
            title = (page.title() or "").lower()
        except Exception:
            pass
        if "just a moment" not in title and "attention required" not in title:
            return
        if headed and not notified:
            print("Cloudflare challenge detected — please solve it in the visible browser window. Waiting up to 120s.")
            notified = True
        page.wait_for_timeout(interval_ms)


def _collect_job_urls_from_page(page, limit: int) -> List[str]:
    anchors = page.locator("a[href*='/job/']").all()
    urls: List[str] = []
    seen = set()
    for anchor in anchors:
        href = anchor.get_attribute("href") or ""
        if "/job/" not in href:
            continue
        url = href if href.startswith("http") else f"https://www.104.com.tw{href}"
        url = url.split("?")[0]
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= limit:
            break
    return urls


def _goto_104(page, url: str) -> None:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as exc:
        if "ERR_ABORTED" not in str(exc):
            raise
        page.wait_for_timeout(3000)


def _fetch_search_rows_in_browser(page, keyword: str, limit: int) -> List[Dict]:
    params = {
        "ro": "0",
        "kwop": "7",
        "keyword": keyword,
        "expansionType": "area,spec,com,job,wf,wktm",
        "mode": "s",
        "jobsource": "joblist_search",
        "page": "1",
    }
    endpoint = SEARCH_URL + "?" + urlencode(params)
    payload_text = page.evaluate(
        """async ({ endpoint }) => {
            const response = await fetch(endpoint, {
                credentials: 'include',
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            return await response.text();
        }""",
        {"endpoint": endpoint},
    )
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        preview = payload_text[:300].replace("\n", " ")
        print(f"104 browser JSON endpoint returned non-JSON for {keyword!r}: {preview}")
        # Caller will fall through to DOM scraping (`_collect_job_urls_from_page`).
        return []
    return payload.get("data", {}).get("list", [])[:limit]


def _row_to_browser_posting(row: Dict) -> RawPosting:
    source_job_id = str(row.get("jobNo") or row.get("link", {}).get("job") or row.get("job_id") or "")
    job_id = _strip_job_prefix(source_job_id)
    title = str(row.get("jobName") or row.get("title") or "")
    company = str(row.get("custName") or row.get("company") or "")
    return RawPosting(
        source=Source.job104,
        source_job_id=job_id or source_job_id or title,
        url=_job_url(job_id),
        title=title,
        company=company,
        jd_text=str(row.get("description") or row.get("desc") or title),
        salary_raw=str(row.get("salaryDesc") or row.get("salary") or ""),
        location=str(row.get("jobAddrNoDesc") or row.get("addressRegion") or ""),
        seniority_raw=str(row.get("periodDesc") or ""),
        fetched_at=datetime.now(timezone.utc),
    )


def _fetch_104_browser_detail(
    page,
    url: str,
    delay_seconds: float,
    fallback_row: Optional[Dict] = None,
) -> RawPosting:
    """Open a 104 job detail page and extract the JD text.

    fallback_row is the list-API row that pointed us here; when challenges or selector
    misses make detail extraction thin, we use it to backfill title/company/salary so we
    never emit a posting with empty jd_text purely because of a DOM hiccup.
    """
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    _wait_for_challenge_if_present(page)
    page.wait_for_timeout(int(delay_seconds * 1000))
    try:
        body = page.locator("body").inner_text(timeout=10000)
    except Exception:
        body = ""
    title = _first_text(page, "h1") or _first_nonempty_line(body)
    company = _extract_company_from_104(page)
    salary_raw = _extract_label_value(page, "工作待遇", first_line_only=True)
    location = _extract_label_value(page, "上班地點", first_line_only=True)
    seniority = _extract_label_value(page, "工作經歷", first_line_only=True)
    source_job_id = url.rstrip("/").split("/")[-1]

    if fallback_row:
        title = title or str(fallback_row.get("jobName") or "")
        company = company or str(fallback_row.get("custName") or "")
        list_desc = str(fallback_row.get("description") or fallback_row.get("desc") or "")
        if list_desc and list_desc not in body:
            body = (body + "\n" + list_desc).strip()
        salary_raw = salary_raw or str(fallback_row.get("salaryDesc") or "")
        location = location or str(fallback_row.get("jobAddrNoDesc") or "")
        seniority = seniority or str(fallback_row.get("periodDesc") or "")

    # Last-ditch fallback to the regex hints (in case selectors break after a 104 redesign).
    salary_raw = salary_raw or _salary_hint(body)
    location = location or _location_hint(body)

    return RawPosting(
        source=Source.job104,
        source_job_id=source_job_id,
        url=url,
        title=title,
        company=company,
        jd_text=body,
        salary_raw=salary_raw,
        location=location,
        seniority_raw=seniority,
        fetched_at=datetime.now(timezone.utc),
    )


def _extract_company_from_104(page) -> str:
    """The company name on 104 detail pages sits inside the header link list.

    Selector probe showed the second `header a / .job-header a` element is the company.
    We pick the longest non-trivial text to avoid '104人力銀行' / '翻譯' siblings.
    """
    candidates: List[str] = []
    for selector in ("header a", ".job-header a", "[class*='cust'] a"):
        try:
            elements = page.locator(selector).all()[:10]
        except Exception:
            continue
        for el in elements:
            try:
                text = (el.inner_text(timeout=1500) or "").strip()
            except Exception:
                continue
            if not text or text in {"104人力銀行", "翻譯", "請選取語言"}:
                continue
            if any(brand in text for brand in ("公司", "股份", "有限", "銀行", "科技", "集團", "Inc", "Ltd", "Co.")):
                candidates.append(text)
    if not candidates:
        return ""
    # Pick the longest — '第一銀行_第一商業銀行股份有限公司' beats '第一銀行'.
    return max(candidates, key=len)


def _extract_label_value(page, label: str, first_line_only: bool = False) -> str:
    """Take the first sibling text after a label div (e.g. '工作待遇' -> '待遇面議')."""
    for selector in (
        f"div:has-text('{label}') + div",
        f"dt:has-text('{label}') + dd",
        f"[class*='job-detail'] :has-text('{label}') + *",
    ):
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            text = (locator.inner_text(timeout=1500) or "").strip()
        except Exception:
            continue
        if not text:
            continue
        if first_line_only:
            text = _first_nonempty_line(text)
        return text
    return ""


def _first_text(page, selector: str) -> str:
    try:
        locator = page.locator(selector).first
        if locator.count() == 0:
            return ""
        return locator.inner_text(timeout=3000).strip()
    except Exception:
        return ""


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _salary_hint(text: str) -> str:
    for line in text.splitlines():
        if any(token in line for token in ("薪", "待遇", "NT$", "TWD")):
            return line.strip()
    return ""


def _location_hint(text: str) -> str:
    for line in text.splitlines():
        if any(token in line for token in ("台北", "新北", "桃園", "新竹", "台中", "台南", "高雄")):
            return line.strip()
    return ""
