from typing import Callable

from app import repository as repo
from app.search import search_domains
from app.enrich import enrich_domain
from app.harvest import harvest_domains


def _enrich_candidates(conn, domains: list[dict], enrich_fn: Callable,
                       source: str, on_progress: Callable[[int, int], None] | None) -> list[dict]:
    out = []
    total = len(domains)
    for i, d in enumerate(domains, 1):
        info = enrich_fn(d["domain"])
        dup = repo.find_duplicate(conn, website=d["domain"], instagram=None,
                                  company_en=d.get("title") or None)
        out.append({
            "domain": d["domain"],
            "title": d.get("title") or info.get("company") or d["domain"],
            "email": info.get("email"),
            "emails": info.get("emails", []),
            "phone": info.get("phone"),
            "instagram": info.get("instagram"),
            "facebook": info.get("facebook"),
            "linkedin": info.get("linkedin"),
            "source": source,
            "duplicate_of": dup,
        })
        if on_progress:
            on_progress(i, total)
    return out


def run_discovery(conn, query: str, limit: int = 10,
                  search_fn: Callable = None, enrich_fn: Callable = None,
                  on_progress: Callable[[int, int], None] | None = None) -> list[dict]:
    search_fn = search_fn or (lambda q, lim: search_domains(q, lim))
    enrich_fn = enrich_fn or (lambda d: enrich_domain(d))
    domains = search_fn(query, limit)
    return _enrich_candidates(conn, domains, enrich_fn, "搜索", on_progress)


def run_page_discovery(conn, url: str, limit: int = 40,
                       harvest_fn: Callable = None, enrich_fn: Callable = None,
                       on_progress: Callable[[int, int], None] | None = None) -> list[dict]:
    """Harvest company domains from a directory/distributor page, then enrich each."""
    harvest_fn = harvest_fn or (lambda u, lim: harvest_domains(u, lim))
    enrich_fn = enrich_fn or (lambda d: enrich_domain(d))
    domains = [{"domain": h, "title": ""} for h in harvest_fn(url, limit)]
    return _enrich_candidates(conn, domains, enrich_fn, "名录/经销商页", on_progress)
