import re
from typing import Callable

from app.jina import fetch as jina_fetch

_EMAIL = re.compile(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', re.I)
_JUNK = ("sentry", "wixpress", "example.", "@2x", "@3x", ".png", ".jpg", ".jpeg", ".gif", ".webp")
_PREFER = ("info@", "sales@", "contact@", "hello@", "enquiries@", "office@")

_WA = re.compile(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(?:%2B|\+)?(\d{8,15})', re.I)
_TEL = re.compile(r'tel:\+?([\d\-().\s]{8,20})', re.I)
_INTL = re.compile(r'\+\d[\d\-().\s]{7,18}\d')

_IG = re.compile(r'instagram\.com/([A-Za-z0-9_.]{2,30})', re.I)
_IG_JUNK = {"p", "reel", "reels", "explore", "accounts", "stories", "share", "tv"}
_FB = re.compile(r'facebook\.com/([A-Za-z0-9_.\-]{2,50})', re.I)
_FB_JUNK = {"sharer", "sharer.php", "share.php", "share", "plugins", "tr", "dialog",
            "login", "groups", "events", "hashtag", "photo.php", "profile.php",
            "pages", "watch", "policy.php", "privacy"}
_LI = re.compile(r'linkedin\.com/(company|in)/([A-Za-z0-9_\-%.]+)', re.I)


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


def _digits(raw: str) -> str:
    return re.sub(r'\D', '', raw)


def extract_phones(text: str) -> list[str]:
    """Normalized +digits, WhatsApp (wa.me) numbers first."""
    out, seen = [], set()
    groups = (
        [m.group(1) for m in _WA.finditer(text)],
        [m.group(1) for m in _TEL.finditer(text)],
        [m.group(0) for m in _INTL.finditer(text)],
    )
    for grp in groups:
        for raw in grp:
            d = _digits(raw)
            if not 8 <= len(d) <= 15 or d in seen:
                continue
            seen.add(d)
            out.append("+" + d)
    return out


def extract_socials(text: str) -> dict:
    ig = fb = li = None
    for m in _IG.finditer(text):
        h = m.group(1)
        if h.lower() not in _IG_JUNK:
            ig = h
            break
    for m in _FB.finditer(text):
        h = m.group(1)
        if h.lower() not in _FB_JUNK:
            fb = h
            break
    m = _LI.search(text)
    if m:
        li = f"linkedin.com/{m.group(1).lower()}/{m.group(2)}"
    return {"instagram": ig, "facebook": fb, "linkedin": li}


def enrich_domain(domain: str, fetch: Callable[[str], str] = jina_fetch) -> dict:
    emails: list[str] = []
    phones: list[str] = []
    socials = {"instagram": None, "facebook": None, "linkedin": None}
    for path in ("/contact", "/contact-us", ""):
        try:
            text = fetch(f"https://{domain}{path}")
        except Exception:  # noqa: BLE001
            continue
        for e in extract_emails(text):
            if e not in emails:
                emails.append(e)
        for p in extract_phones(text):
            if p not in phones:
                phones.append(p)
        for k, v in extract_socials(text).items():
            if socials[k] is None:
                socials[k] = v
        if emails and phones and all(socials.values()):
            break
    best = None
    for e in emails:
        if any(e.lower().startswith(p) for p in _PREFER):
            best = e
            break
    if best is None and emails:
        best = emails[0]
    return {"domain": domain, "emails": emails, "email": best,
            "phone": phones[0] if phones else None, "phones": phones, **socials}
