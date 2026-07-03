import httpx

BASE = "https://r.jina.ai/"


def fetch(url: str, timeout: int = 45) -> str:
    r = httpx.get(BASE + url, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    return r.text
