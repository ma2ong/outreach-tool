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


def test_list_leads_untouched_for_channel(conn):
    # lead2 email row is 'prospect' (never messaged), lead3 has no email row
    assert {l.no for l in repo.list_leads(conn, channel="email", status="untouched")} == {2, 3}
    assert {l.no for l in repo.list_leads(conn, channel="whatsapp", status="untouched")} == {1, 2}


def test_list_leads_untouched_any_channel(conn):
    assert [l.no for l in repo.list_leads(conn, status="untouched")] == [2]


def test_list_leads_untouched_excludes_replied(conn):
    repo.mark_replied(conn, 2, "email")
    assert [l.no for l in repo.list_leads(conn, channel="email", status="untouched")] == [3]


def test_list_leads_has_contact(conn):
    conn.execute("UPDATE leads SET phone='+123456789', email='a@b.com' WHERE no=1")
    conn.execute("UPDATE leads SET email='' WHERE no=2")
    conn.commit()
    assert [l.no for l in repo.list_leads(conn, has="phone")] == [1]
    assert {l.no for l in repo.list_leads(conn, has="instagram")} == {1, 3}
    assert [l.no for l in repo.list_leads(conn, has="email")] == [1]


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


def test_stats_reach_and_funnel(conn):
    # lead1: email+phone+ig(alphaig); lead2: email only; lead3: ig(gammaig) only
    conn.execute("UPDATE leads SET email='a@a.com', phone='+111' WHERE no=1")
    conn.execute("UPDATE leads SET email='b@b.com' WHERE no=2")
    conn.commit()
    s = repo.stats(conn)
    # email: have {1,2}=2, messaged {1}=1 (lead2 is 'prospect'), untouched {2}=1
    assert s.reach["email"] == {"have": 2, "messaged": 1, "replied": 0, "untouched": 1}
    # whatsapp: have {1}=1 (only lead1 has phone), messaged {3}=1 (outreach row), untouched {1}=1
    assert s.reach["whatsapp"] == {"have": 1, "messaged": 1, "replied": 0, "untouched": 1}
    # instagram: have {1,3}=2, messaged {1}=1, untouched {3}=1
    assert s.reach["instagram"] == {"have": 2, "messaged": 1, "replied": 0, "untouched": 1}
    # funnel: total 3, with_contact 3, touched {1,3}=2, replied 0
    assert s.funnel == {"total": 3, "with_contact": 3, "touched": 2, "replied": 0}


def test_stats_reach_counts_replied(conn):
    conn.execute("UPDATE leads SET email='a@a.com' WHERE no=1")
    conn.commit()
    repo.mark_replied(conn, 1, "email")
    s = repo.stats(conn)
    assert s.reach["email"]["replied"] == 1
    assert s.reach["email"]["messaged"] == 1  # replied still counts as touched
    assert s.funnel["replied"] == 1
