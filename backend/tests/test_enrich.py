from app import enrich


def test_extract_emails_filters_junk():
    text = "Contact info@acme.com or sales@acme.com. img@2x.png sentry@abc.io a@b.jpg"
    got = enrich.extract_emails(text)
    assert got == ["info@acme.com", "sales@acme.com"]


def test_enrich_domain_picks_best_email():
    pages = {
        "https://acme.com/contact": "reach info@acme.com",
        "https://acme.com": "home",
    }
    out = enrich.enrich_domain("acme.com", fetch=lambda url: pages.get(url, ""))
    assert out["domain"] == "acme.com"
    assert out["email"] == "info@acme.com"
    assert "info@acme.com" in out["emails"]


def test_enrich_domain_no_email():
    out = enrich.enrich_domain("none.com", fetch=lambda url: "no address here")
    assert out["email"] is None
    assert out["emails"] == []
