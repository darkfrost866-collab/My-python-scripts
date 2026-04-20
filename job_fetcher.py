"""job_fetcher.py — Multi-platform job import: Adzuna API, RSS feeds, Playwright"""
import re
import time
import json
import requests
import feedparser
from datetime import datetime, timedelta

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

try:
    from config import (
        ADZUNA_APP_ID, ADZUNA_APP_KEY,
        LOCATION, MAX_DAYS_OLD, MAX_JOBS,
        EXCLUDED_INDUSTRIES,
    )
except Exception:
    ADZUNA_APP_ID = ADZUNA_APP_KEY = ""
    LOCATION = "Ontario, Canada"
    MAX_DAYS_OLD = 20
    MAX_JOBS = 30
    EXCLUDED_INDUSTRIES = []

# ── Helpers ───────────────────────────────────────────────────────────────────

_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

_SEARCH_QUERIES = [
    "production supervisor",
    "manufacturing supervisor",
    "welding supervisor",
    "manufacturing manager",
    "plant supervisor",
    "operations supervisor",
]


def _clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text or '').strip()


def _get_feed(url: str) -> list:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        feed = feedparser.parse(resp.content if resp.status_code == 200 else url)
    except Exception:
        feed = feedparser.parse(url)
    jobs = []
    for e in feed.entries[:10]:
        title = re.sub(r'\s+-\s+.*$', '', e.get('title', '')).strip()
        jobs.append({
            'title':       title[:100],
            'company':     e.get('author', e.get('publisher', 'Unknown'))[:60],
            'location':    LOCATION,
            'url':         e.get('link', ''),
            'description': _clean_html(e.get('summary', ''))[:600],
            'created':     datetime.now().strftime('%Y-%m-%d'),
            'source':      '',
        })
    return jobs


# ── Source 1: Adzuna API (free, no scraping) ─────────────────────────────────

def fetch_adzuna(query: str = "production supervisor", country: str = "ca",
                 location: str = "Ontario") -> list:
    """Fetch jobs from Adzuna API. Sign up free at developer.adzuna.com."""
    if not ADZUNA_APP_ID or ADZUNA_APP_ID == "your_adzuna_app_id":
        return []
    base = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id":           ADZUNA_APP_ID,
        "app_key":          ADZUNA_APP_KEY,
        "results_per_page": 20,
        "what":             query,
        "where":            location,
        "max_days_old":     MAX_DAYS_OLD,
        "content-type":     "application/json",
    }
    try:
        r = requests.get(base, params=params, timeout=15)
        data = r.json()
        jobs = []
        for item in data.get("results", []):
            jobs.append({
                'title':       item.get('title', '')[:100],
                'company':     item.get('company', {}).get('display_name', 'Unknown')[:60],
                'location':    item.get('location', {}).get('display_name', location),
                'url':         item.get('redirect_url', ''),
                'description': _clean_html(item.get('description', ''))[:600],
                'created':     item.get('created', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))[:10],
                'source':      'Adzuna',
                'salary_min':  item.get('salary_min'),
                'salary_max':  item.get('salary_max'),
            })
        return jobs
    except Exception as exc:
        print(f"  Adzuna API error: {exc}")
        return []


# ── Source 2: RSS feeds (JobBank, Jooble, Eluta, LinkedIn public, WorkopóliS) ─

def fetch_rss_feeds(queries: list = None) -> list:
    if queries is None:
        queries = _SEARCH_QUERIES[:3]

    feeds_map = {
        "JobBank":   "https://www.jobbank.gc.ca/job_search_feed.do?searchstring={q}&locationstring=Ontario",
        "Eluta":     "https://www.eluta.ca/search.rss?q={q}&l=Ontario",
        "Jooble":    "https://ca.jooble.org/rss/search?ukw={q}&rgns=Ontario",
        "Workopolis":"https://www.workopolis.com/en/rss/jobs/?q={q}&l=Ontario",
        "SimplyHired":"https://www.simplyhired.ca/search?q={q}&l=Ontario&pn=1&job-types=fulltime&fdb={days}&rss=1",
    }

    jobs = []
    for name, url_template in feeds_map.items():
        for q in queries[:2]:
            url = url_template.format(q=q.replace(' ', '+'), days=MAX_DAYS_OLD)
            batch = _get_feed(url)
            for j in batch:
                j['source'] = name
            jobs.extend(batch)
            time.sleep(0.8)
        print(f"  {name:14}: {len(jobs)} cumulative")
    return jobs


# ── Source 3: Indeed via Playwright (real browser, bypasses bot detection) ────

def fetch_indeed_playwright(queries: list = None) -> list:
    if not PLAYWRIGHT_AVAILABLE:
        return []
    if queries is None:
        queries = _SEARCH_QUERIES[:3]

    jobs = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=_HEADERS['User-Agent'])

            for q in queries:
                url = f"https://ca.indeed.com/jobs?q={q.replace(' ','+')}&l=Ontario&fromage=7"
                page.goto(url, timeout=30000)
                page.wait_for_timeout(3000)

                for card in page.query_selector_all('div.job_seen_beacon')[:8]:
                    try:
                        title_el   = card.query_selector('h2 a span')
                        company_el = card.query_selector('[data-testid="company-name"]')
                        loc_el     = card.query_selector('[data-testid="text-location"]')
                        link_el    = card.query_selector('h2 a')
                        snippet_el = card.query_selector('.job-snippet')

                        title   = title_el.inner_text()   if title_el   else q.title()
                        company = company_el.inner_text() if company_el else "Indeed Employer"
                        loc     = loc_el.inner_text()     if loc_el     else "Ontario"
                        link    = link_el.get_attribute('href') if link_el else ""
                        snippet = snippet_el.inner_text() if snippet_el else title

                        jobs.append({
                            'title':       title[:100],
                            'company':     company[:60],
                            'location':    loc,
                            'url':         f"https://ca.indeed.com{link}" if link.startswith('/') else link,
                            'description': snippet[:600],
                            'created':     datetime.now().strftime('%Y-%m-%d'),
                            'source':      'Indeed',
                        })
                    except Exception:
                        continue
                time.sleep(2)

            browser.close()
    except Exception as exc:
        print(f"  Playwright error: {exc}")
    return jobs


# ── Source 4: LinkedIn RSS (public job search RSS) ────────────────────────────

def fetch_linkedin_rss(queries: list = None) -> list:
    if queries is None:
        queries = _SEARCH_QUERIES[:2]
    jobs = []
    for q in queries:
        url = (
            "https://www.linkedin.com/jobs/search/?keywords="
            + q.replace(' ', '%20')
            + "&location=Ontario%2C%20Canada&f_TPR=r604800&trk=public_jobs_jobs-search-bar_search-submit"
        )
        # LinkedIn blocks RSS directly; use the public jobs RSS endpoint
        rss_url = f"https://www.linkedin.com/jobs/search.rss?keywords={q.replace(' ','+')}&location=Ontario,+Canada"
        batch = _get_feed(rss_url)
        for j in batch:
            j['source'] = 'LinkedIn'
        jobs.extend(batch)
        time.sleep(1)
    return jobs


# ── Scoring ───────────────────────────────────────────────────────────────────

def _compute_ats(job: dict) -> int:
    txt = (job['title'] + ' ' + job['description']).lower()
    score = 70
    kw_groups = {
        12: ['lean', 'six sigma', 'kaizen', 'continuous improvement'],
        10: ['weld', 'cwb', 'tssa', 'fabricat'],
        8:  ['iso', 'iatf', 'as9100', 'qms'],
        6:  ['union', 'labour', 'labor'],
        5:  ['hse', 'ohsa', 'safety', 'jhsc'],
        4:  ['root cause', 'rca', '5s', 'kpi'],
        3:  ['erp', 'sap', 'production planning'],
    }
    for pts, kws in kw_groups.items():
        if any(kw in txt for kw in kws):
            score += pts
    return min(score, 98)


def _classify_industry(txt: str) -> str:
    txt = txt.lower()
    if 'aerospace' in txt or 'as9100' in txt:
        return 'Aerospace'
    if 'automotive' in txt or 'iatf' in txt:
        return 'Automotive'
    if 'weld' in txt or 'cwb' in txt or 'tssa' in txt:
        return 'Welding'
    if 'food' in txt or 'beverage' in txt or 'dairy' in txt:
        return 'Food'
    return 'Manufacturing'


# ── Filtering ─────────────────────────────────────────────────────────────────

def filter_jobs(jobs: list,
                industries: list = None,
                job_types: list  = None,
                locations: list  = None,
                min_ats: int     = 0,
                keyword: str     = "") -> list:
    """
    Filter and score jobs.
    - industries: e.g. ['Manufacturing', 'Automotive']
    - job_types:  e.g. ['Supervisor', 'Manager']
    - locations:  e.g. ['Ontario']
    - min_ats:    minimum ATS threshold
    - keyword:    free-text search in title/description
    """
    excluded = EXCLUDED_INDUSTRIES or [
        'food', 'dairy', 'bakery', 'restaurant', 'server', 'cook', 'chef',
        'retail', 'cashier', 'pizza', 'grocery',
    ]

    filtered = []
    for job in jobs:
        txt = (job['title'] + ' ' + job.get('description', '')).lower()

        # Must be a relevant supervisory / management role
        if not re.search(r'supervisor|manager|lead|foreman|superintendent', job['title'], re.I):
            continue
        if not re.search(r'manufactur|production|plant|weld|fabricat|operations|automotive|aerospace|industrial', txt):
            continue
        if any(bad in txt for bad in excluded):
            continue

        # Keyword search
        if keyword and keyword.lower() not in txt:
            continue

        # Location filter
        if locations:
            job_loc = job.get('location', '').lower()
            if not any(loc.lower() in job_loc for loc in locations):
                continue

        # Industry + job_type filters applied after classification
        industry = _classify_industry(txt)
        job['industry'] = industry
        job['ats']      = _compute_ats(job)
        job['level']    = 'Supervisor/Manager'

        if industries and industry not in industries:
            continue
        if min_ats and job['ats'] < min_ats:
            continue

        filtered.append(job)

    # Deduplicate by URL
    seen, unique = set(), []
    for j in filtered:
        key = j.get('url', '').split('?')[0].lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(j)

    unique.sort(key=lambda x: x['ats'], reverse=True)
    return unique[:MAX_JOBS]


def search_jobs(jobs: list, query: str) -> list:
    """Free-text search across title, company, description."""
    q = query.lower()
    return [
        j for j in jobs
        if q in j.get('title', '').lower()
        or q in j.get('company', '').lower()
        or q in j.get('description', '').lower()
    ]


# ── Fallback dataset ──────────────────────────────────────────────────────────

_FALLBACK = [
    {'title': 'Production Supervisor — 2nd Shift', 'company': 'Magna International',    'location': 'Newmarket, ON',   'url': 'https://jobs.magna.com',        'description': 'Automotive manufacturing Lean Six Sigma union leadership IATF 16949', 'created': '2026-04-18', 'source': 'Fallback'},
    {'title': 'Welding Supervisor',                'company': 'Linamar Corporation',    'location': 'Guelph, ON',      'url': 'https://linamar.com/careers',   'description': 'TSSA CWB welding root cause 5S kaizen fabrication',                  'created': '2026-04-17', 'source': 'Fallback'},
    {'title': 'Manufacturing Manager',             'company': 'Bombardier Aerospace',   'location': 'Mississauga, ON', 'url': 'https://bombardier.com/careers','description': 'Aerospace AS9100 HSE Six Sigma production management',               'created': '2026-04-16', 'source': 'Fallback'},
    {'title': 'Plant Supervisor',                  'company': 'Stellantis Canada',      'location': 'Windsor, ON',     'url': 'https://stellantis.com/careers','description': 'Automotive assembly union workforce Lean ISO',                       'created': '2026-04-15', 'source': 'Fallback'},
    {'title': 'Operations Supervisor',             'company': 'Martinrea International','location': 'Vaughan, ON',     'url': 'https://martinrea.com/careers', 'description': 'Metal forming Lean root cause analysis IATF',                        'created': '2026-04-14', 'source': 'Fallback'},
    {'title': 'Production Manager',                'company': 'ArcelorMittal Dofasco',  'location': 'Hamilton, ON',    'url': 'https://dofasco.ca/careers',    'description': 'Steel manufacturing HSE OHSA JHSC Lean Six Sigma',                   'created': '2026-04-13', 'source': 'Fallback'},
    {'title': 'Shift Supervisor',                  'company': 'Celestica',              'location': 'Toronto, ON',     'url': 'https://celestica.com/careers', 'description': 'Electronics ISO 9001 Six Sigma KPI management',                      'created': '2026-04-12', 'source': 'Fallback'},
    {'title': 'Manufacturing Supervisor',          'company': 'Honda Canada',           'location': 'Alliston, ON',    'url': 'https://honda.ca/careers',      'description': 'Automotive Lean kaizen 5S production planning union',                 'created': '2026-04-11', 'source': 'Fallback'},
]


# ── Main entry point ──────────────────────────────────────────────────────────

def fetch_all(use_playwright: bool = True, use_adzuna: bool = True,
              use_rss: bool = True, use_linkedin: bool = True) -> list:
    jobs = []
    print("\nFetching jobs from all sources...")

    if use_playwright:
        batch = fetch_indeed_playwright()
        jobs.extend(batch)
        print(f"  Indeed (Playwright) : {len(batch)} jobs")

    if use_adzuna:
        for q in _SEARCH_QUERIES[:3]:
            batch = fetch_adzuna(q)
            jobs.extend(batch)
        print(f"  Adzuna API          : {sum(1 for j in jobs if j.get('source')=='Adzuna')} jobs")
        time.sleep(1)

    if use_rss:
        batch = fetch_rss_feeds()
        jobs.extend(batch)

    if use_linkedin:
        batch = fetch_linkedin_rss()
        jobs.extend(batch)
        print(f"  LinkedIn RSS        : {len(batch)} jobs")

    # Fallback if nothing was fetched
    if len(jobs) < 5:
        print("  Using fallback dataset.")
        jobs.extend(_FALLBACK)

    print(f"\n  TOTAL RAW JOBS      : {len(jobs)}")
    return jobs
