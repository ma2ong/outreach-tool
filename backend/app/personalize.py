"""Safe template personalization for outreach messages.

Replaces only the known tokens below; anything else in braces is left intact,
so a stray '{price}' in a template can never crash a send (str.format raised
KeyError). {contact} falls back to 'there' so 'Hi {contact}' always reads fine.
"""
import re

_TOKEN_RE = re.compile(r"\{(name|company|contact|country|city)\}")


def render(text: str | None, lead: dict) -> str:
    if not text:
        return ""
    company = lead.get("company_en") or ""
    contact = (lead.get("contact_name") or "").strip()
    values = {
        "name": company,
        "company": company,
        "contact": contact.split()[0] if contact else "there",
        "country": lead.get("country") or "",
        "city": lead.get("city") or "",
    }
    return _TOKEN_RE.sub(lambda m: values[m.group(1)], text)
