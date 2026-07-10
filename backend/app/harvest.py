"""Harvest company domains from a directory-style page.

Point it at a competitor's "where to buy / distributors" page or a trade-show
exhibitor listing (ISE / InfoComm / LED China) and it pulls every outbound company
domain, which then flows through the same enrich pipeline as keyword search. This
turns two LED-specific high-value buyer pools into candidates without a browser.
"""
import re
import urllib.parse
from typing import Callable

from app.jina import fetch as jina_fetch

# Hosts that are never a prospect's own site.
_SKIP = (
    "duckduckgo.com", "jina.ai", "wikipedia.org", "w3.org", "schema.org",
    "google.com", "bing.com", "youtube.com", "youtu.be", "vimeo.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
    "t.me", "wa.me", "whatsapp.com", "pinterest.com", "tiktok.com",
    "gstatic.com", "googleapis.com", "cloudflare.com", "gravatar.com",
    "apple.com", "microsoft.com", "adobe.com", "wordpress.org", "gmpg.org",
)
_URL = re.compile(r'https?://[^\s"\'<>\)\]]+', re.I)


def _host(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def harvest_domains(url: str, limit: int = 40,
                    fetch: Callable[[str], str] = jina_fetch) -> list[str]:
    """Return distinct external company domains linked from `url`, in page order."""
    text = fetch(url)
    self_host = _host(url)
    out: list[str] = []
    seen: set[str] = set()
    for m in _URL.finditer(text):
        host = _host(m.group(0))
        if not host or host in seen:
            continue
        # a prospect's site has a dot and isn't localhost/an IP literal
        if "." not in host or host.split(":")[0] == "localhost" or host.replace(".", "").replace(":", "").isdigit():
            continue
        if host == self_host or any(s in host for s in _SKIP):
            continue
        seen.add(host)
        out.append(host)
        if len(out) >= limit:
            break
    return out
