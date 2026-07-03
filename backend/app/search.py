import re
import urllib.parse
from typing import Callable

from app.jina import fetch as jina_fetch

_SKIP = ("duckduckgo.com", "jina.ai", "wikipedia.org", "w3.org", "schema.org", "google.com", "bing.com")


def search_domains(query: str, limit: int = 10,
                   fetch: Callable[[str], str] = jina_fetch) -> list[dict]:
    enc = urllib.parse.quote(query)
    text = fetch(f"https://html.duckduckgo.com/html/?q={enc}")
    seen: dict[str, dict] = {}
    for m in re.finditer(r'uddg=([^&"\)\s]+)', text):
        target = urllib.parse.unquote(m.group(1))
        host = urllib.parse.urlparse(target).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if not host or any(s in host for s in _SKIP):
            continue
        if host not in seen:
            seen[host] = {"domain": host, "title": ""}
        if len(seen) >= limit:
            break
    return list(seen.values())
