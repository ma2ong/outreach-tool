from typing import Callable

from app import repository as repo
from app.search import search_domains
from app.enrich import enrich_domain


def run_discovery(conn, query: str, limit: int = 10,
                  search_fn: Callable = None, enrich_fn: Callable = None,
                  on_progress: Callable[[int, int], None] | None = None) -> list[dict]:
    search_fn = search_fn or (lambda q, lim: search_domains(q, lim))
    enrich_fn = enrich_fn or (lambda d: enrich_domain(d))
    domains = search_fn(query, limit)
    out = []
    total = len(domains)
    for i, d in enumerate(domains, 1):
        info = enrich_fn(d["domain"])
        dup = repo.find_duplicate(conn, website=d["domain"], instagram=None,
                                  company_en=d.get("title") or None)
        out.append({
            "domain": d["domain"],
            "title": d.get("title") or d["domain"],
            "email": info.get("email"),
            "emails": info.get("emails", []),
            "duplicate_of": dup,
        })
        if on_progress:
            on_progress(i, total)
    return out
