from app import repository as repo


def test_list_leads_all(conn):
    leads = repo.list_leads(conn)
    assert len(leads) == 3


def test_list_leads_filter_country(conn):
    leads = repo.list_leads(conn, country="USA")
    assert {l.no for l in leads} == {1, 2}


def test_list_leads_filter_channel_status(conn):
    leads = repo.list_leads(conn, channel="email", status="messaged")
    assert [l.no for l in leads] == [1]


def test_list_leads_search(conn):
    leads = repo.list_leads(conn, search="gamma")
    assert [l.no for l in leads] == [3]


def test_get_lead_includes_outreach(conn):
    lead = repo.get_lead(conn, 1)
    assert lead.company_en == "Alpha AV"
    channels = {o.channel for o in lead.outreach}
    assert channels == {"email", "instagram"}


def test_find_duplicate_by_website(conn):
    assert repo.find_duplicate(conn, website="alpha.com", instagram=None, company_en="X") == 1
    assert repo.find_duplicate(conn, website="new.com", instagram=None, company_en="New") is None


def test_stats(conn):
    s = repo.stats(conn)
    assert s.total == 3
    assert s.by_country == {"USA": 2, "Brazil": 1}
    assert s.by_channel_status["email"]["messaged"] == 1
    assert s.by_channel_status["email"]["prospect"] == 1
    assert s.by_channel_status["instagram"]["messaged"] == 1
