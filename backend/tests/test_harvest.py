from app import harvest

_PAGE = """
# Absen Distributors Worldwide

Find a partner near you:

- [LED Pro USA](https://www.ledprousa.com/about)
- [Bright Screens](https://brightscreens.de/kontakt)
- [Visual Impact](http://visualimpact.com.br)
- duplicate link again https://www.ledprousa.com/contact
- Follow us on [Facebook](https://facebook.com/absen) and [Instagram](https://instagram.com/absen)
- Powered by [Absen](https://absen.com) — this is the page's own site
- CDN asset https://cdn.googleapis.com/x.js
"""


def _fetch(url):
    return _PAGE


def test_harvest_extracts_external_company_domains():
    doms = harvest.harvest_domains("https://absen.com/where-to-buy", fetch=_fetch)
    assert doms == ["ledprousa.com", "brightscreens.de", "visualimpact.com.br"]


def test_harvest_skips_self_social_and_junk():
    doms = harvest.harvest_domains("https://absen.com/where-to-buy", fetch=_fetch)
    assert "absen.com" not in doms          # self
    assert "facebook.com" not in doms       # social
    assert "googleapis.com" not in doms     # junk/cdn


def test_harvest_respects_limit():
    doms = harvest.harvest_domains("https://absen.com/where-to-buy", limit=2, fetch=_fetch)
    assert doms == ["ledprousa.com", "brightscreens.de"]
