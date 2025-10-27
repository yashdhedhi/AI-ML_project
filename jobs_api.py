import os
import json
import requests
import pathlib
from typing import List, Dict, Optional

# Default country for Adzuna; change if needed via ENV ADZUNA_COUNTRY
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "in")

def _load_local_jobs() -> List[Dict]:
    p = pathlib.Path("jobs_sample.json")
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []

# ---------- Adzuna ----------
def get_jobs_adzuna(
    query: str,
    location: str = "India",
    results_per_page: int = 10,
    page: int = 1,
) -> List[Dict]:
    app_id = os.getenv("ADZUNA_APP_ID") or os.getenv("ADZUNAAPPID")
    app_key = os.getenv("ADZUNA_APP_KEY") or os.getenv("ADZUNAAPPKEY")
    if not app_id or not app_key:
        raise RuntimeError("Adzuna credentials missing. Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env/Secrets.")
    url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/{page}"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "where": location,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])

# ---------- Workable (per-company public widget) ----------
def get_workable_company_jobs(company_slug: str) -> List[Dict]:
    url = f"https://apply.workable.com/api/v1/widget/accounts/{company_slug}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    jobs: List[Dict] = []
    for j in data.get("jobs", []):
        jobs.append({
            "title": j.get("title", ""),
            "company": {"display_name": company_slug},
            "location": {"display_name": j.get("location", "")},
            "description": (j.get("description", "") or j.get("requirements", "") or ""),
            "redirect_url": j.get("url", ""),
        })
    return jobs

def get_jobs_workable(company_slugs: List[str], limit_per_company: int = 10) -> List[Dict]:
    all_jobs: List[Dict] = []
    for slug in company_slugs:
        try:
            items = get_workable_company_jobs(slug)[:limit_per_company]
            all_jobs.extend(items)
        except Exception:
            continue
    return all_jobs

# ---------- Arbeitnow (free, no key) ----------
def get_jobs_arbeitnow(
    query: str,
    location: Optional[str] = None,  # API doesn’t filter by location directly; keep for signature parity
    results_per_page: int = 20,
    page: int = 1,
) -> List[Dict]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {"query": query, "page": page}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("data", [])
    jobs: List[Dict] = []
    for j in data[:results_per_page]:
        loc = ", ".join(filter(None, [j.get("location"), "Remote" if j.get("remote") else None]))
        jobs.append({
            "title": j.get("title", ""),
            "company": {"display_name": j.get("company", "")},
            "location": {"display_name": loc},
            "description": j.get("description", "") or "",
            "redirect_url": j.get("url", ""),
        })
    return jobs

# ---------- Unified router ----------
def get_jobs(
    source: str,
    query: str,
    location: str,
    results_per_page: int,
    workable_companies: List[str],
    page: int = 1,
) -> List[Dict]:
    if source == "Workable":
        per = max(1, results_per_page // max(1, len(workable_companies)))
        return get_jobs_workable(workable_companies, limit_per_company=per)
    if source == "Adzuna":
        return get_jobs_adzuna(query=query, location=location, results_per_page=results_per_page, page=page)
    if source == "Arbeitnow":
        return get_jobs_arbeitnow(query=query, location=location, results_per_page=results_per_page, page=page)
    return []
