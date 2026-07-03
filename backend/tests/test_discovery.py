from app import discovery


def test_run_discovery_flags_duplicates_and_progress(conn):
    # conn fixture: lead 1 has website 'alpha.com'
    search_fn = lambda q, limit: [{"domain": "alpha.com", "title": ""},
                                  {"domain": "newco.com", "title": ""}]
    enrich_fn = lambda d: {"domain": d, "emails": [f"info@{d}"], "email": f"info@{d}"}
    seen = []
    cands = discovery.run_discovery(conn, "led", 10, search_fn=search_fn, enrich_fn=enrich_fn,
                                    on_progress=lambda done, total: seen.append((done, total)))
    by = {c["domain"]: c for c in cands}
    assert by["alpha.com"]["duplicate_of"] == 1
    assert by["newco.com"]["duplicate_of"] is None
    assert by["newco.com"]["email"] == "info@newco.com"
    assert seen[-1] == (2, 2)
