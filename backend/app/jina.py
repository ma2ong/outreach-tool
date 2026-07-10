import httpx

BASE = "https://r.jina.ai/"

# jina returns HTTP 200 for pages it could reach but that are really block/challenge
# pages; treating those as content poisons enrich/classify with junk text.
_BLOCK_MARKERS = (
    "Warning: Target URL returned error",
    "Checking your browser before accessing",
    "Just a moment...",
    "Attention Required! | Cloudflare",
    "Access denied | ",
)


class BlockedPage(Exception):
    """The site answered with an anti-bot / error interstitial, not real content."""


def fetch(url: str, timeout: int = 45) -> str:
    r = httpx.get(BASE + url, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    head = r.text[:600]
    if any(m in head for m in _BLOCK_MARKERS):
        raise BlockedPage(url)
    return r.text
