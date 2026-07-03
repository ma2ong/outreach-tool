import re
from typing import Callable

from app.jina import fetch as jina_fetch

_EMAIL = re.compile(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', re.I)
_JUNK = ("sentry", "wixpress", "example.", "@2x", "@3x", ".png", ".jpg", ".jpeg", ".gif", ".webp")
_PREFER = ("info@", "sales@", "contact@", "hello@", "enquiries@", "office@")


def extract_emails(text: str) -> list[str]:
    out, seen = [], set()
    for m in _EMAIL.finditer(text):
        e = m.group(0)
        low = e.lower()
        if any(j in low for j in _JUNK):
            continue
        if low not in seen:
            seen.add(low)
            out.append(e)
    return out


def enrich_domain(domain: str, fetch: Callable[[str], str] = jina_fetch) -> dict:
    emails: list[str] = []
    for path in ("/contact", "/contact-us", ""):
        try:
            text = fetch(f"https://{domain}{path}")
        except Exception:  # noqa: BLE001
            continue
        for e in extract_emails(text):
            if e not in emails:
                emails.append(e)
        if emails:
            break
    best = None
    for e in emails:
        if any(e.lower().startswith(p) for p in _PREFER):
            best = e
            break
    if best is None and emails:
        best = emails[0]
    return {"domain": domain, "emails": emails, "email": best}
