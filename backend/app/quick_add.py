"""One-click lead capture from any URL the salesperson is looking at.

Paste an Instagram/Facebook/LinkedIn profile URL or a company website; we work out
which field it belongs in. Websites go through the normal enrich pipeline so the
lead arrives with email/phone/socials/ICP already filled where possible.
"""
import re
from urllib.parse import urlparse


class BadUrl(ValueError):
    pass


_IG_HOSTS = {"instagram.com", "m.instagram.com"}
_FB_HOSTS = {"facebook.com", "m.facebook.com", "web.facebook.com", "fb.com"}
# IG paths that are content, not a profile
_IG_NON_PROFILE = {"p", "reel", "reels", "explore", "stories", "accounts"}


def parse_url(raw: str) -> dict:
    """Map a pasted URL to the lead field it fills: instagram / facebook / linkedin / website."""
    url = (raw or "").strip()
    if not url:
        raise BadUrl("请粘贴客户主页或官网链接")
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    p = urlparse(url)
    host = p.netloc.lower().split(":")[0].removeprefix("www.")
    if not host or "." not in host:
        raise BadUrl("链接格式不对，请粘贴完整网址")
    parts = [s for s in p.path.split("/") if s]
    if host in _IG_HOSTS:
        if not parts or parts[0].lower() in _IG_NON_PROFILE:
            raise BadUrl("需要 Instagram 主页链接（instagram.com/账号名），不是帖子链接")
        return {"instagram": parts[0]}
    if host in _FB_HOSTS:
        if not parts:
            raise BadUrl("需要 Facebook 主页链接（facebook.com/主页名）")
        if parts[0] in ("people", "pg") and len(parts) > 1:
            return {"facebook": parts[1]}
        return {"facebook": parts[0]}
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        if not parts:
            raise BadUrl("需要 LinkedIn 公司页链接（linkedin.com/company/…）")
        return {"linkedin": "linkedin.com/" + "/".join(parts[:2])}
    return {"website": host}


def display_name(fields: dict) -> str:
    """Readable default company name from a handle/domain; the drawer lets Allen fix it."""
    handle = fields.get("instagram") or fields.get("facebook") or ""
    if not handle:
        src = fields.get("linkedin") or fields.get("website") or ""
        handle = src.removeprefix("linkedin.com/company/").removeprefix("linkedin.com/in/")
        handle = handle.split("/")[0].split(".")[0]
    return re.sub(r"[._\-]+", " ", handle).strip().title()
