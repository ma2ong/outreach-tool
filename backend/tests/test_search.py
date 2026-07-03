from app import search

FAKE_DDG = """Markdown Content:
## [AV One | LED Video Walls](https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.avone.com%2F&rut=x)
## [Bright Screens](https://duckduckgo.com/l/?uddg=https%3A%2F%2Fbrightscreens.com%2Fcontact&rut=y)
## [AV One again](https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.avone.com%2Fabout&rut=z)
"""


def test_search_domains_extracts_unique_domains():
    out = search.search_domains("led wall", limit=10, fetch=lambda url: FAKE_DDG)
    domains = [c["domain"] for c in out]
    assert domains == ["avone.com", "brightscreens.com"]  # deduped, www stripped, order preserved


def test_search_domains_respects_limit():
    out = search.search_domains("led wall", limit=1, fetch=lambda url: FAKE_DDG)
    assert len(out) == 1
