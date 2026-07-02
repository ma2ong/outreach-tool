from app.models import Lead, OutreachStatus, Stats


def test_lead_from_row_parses_source_urls():
    lead = Lead(no=1, company_en="A", source_urls=["https://x.com"],
                outreach=[OutreachStatus(channel="email", status="messaged")])
    assert lead.no == 1
    assert lead.outreach[0].channel == "email"


def test_stats_shape():
    s = Stats(total=10, by_country={"USA": 5}, by_channel_status={"email": {"messaged": 3}})
    assert s.total == 10
    assert s.by_country["USA"] == 5
