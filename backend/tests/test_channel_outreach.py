from app import channel_outreach as co
from app.browser_engine import FakeEngine


def _seed(conn):
    conn.executescript("""
        DELETE FROM outreach;
        DELETE FROM leads;
        INSERT INTO leads(no, company_en, phone, instagram) VALUES
            (1,'Alpha','+1 (555) 123-4567','alpha_ig'),
            (2,'Beta',NULL,'beta_ig'),
            (3,'Gamma','+55 11 99999-8888',NULL),
            (4,'Delta','+1 555 000 1111','delta_ig');
        INSERT INTO outreach(lead_no, channel, status) VALUES (4,'whatsapp','messaged');
    """)
    conn.commit()


def test_eligible_whatsapp_needs_phone_and_not_sent(conn):
    _seed(conn)
    elig = co.eligible(conn, [1, 2, 3, 4], "whatsapp")
    assert [l["no"] for l in elig] == [1, 3]  # 2 no phone, 4 already messaged


def test_eligible_instagram_needs_handle(conn):
    _seed(conn)
    elig = co.eligible(conn, [1, 2, 3, 4], "instagram")
    assert [l["no"] for l in elig] == [1, 2, 4]  # 3 has no instagram


def test_send_whatsapp_normalizes_number_and_marks(conn):
    _seed(conn)
    eng = FakeEngine()
    res = co.send_channel_campaign(conn, [1, 3], "whatsapp", "Hi {name}", eng, delay_range=(0, 0))
    assert res["sent"] == 2
    # phone normalized to digits only
    assert ("whatsapp", "15551234567", "Hi Alpha") in eng.sent
    assert ("whatsapp", "5511999998888", "Hi Gamma") in eng.sent
    rows = conn.execute("SELECT lead_no FROM outreach WHERE channel='whatsapp' AND status='messaged' ORDER BY lead_no").fetchall()
    assert [r["lead_no"] for r in rows] == [1, 3, 4]


def test_send_instagram_uses_handle(conn):
    _seed(conn)
    eng = FakeEngine()
    res = co.send_channel_campaign(conn, [1], "instagram", "yo {name}", eng, delay_range=(0, 0))
    assert res["sent"] == 1
    assert eng.sent == [("instagram", "alpha_ig", "yo Alpha")]


def test_send_records_failure(conn):
    _seed(conn)
    eng = FakeEngine()
    eng.fail_targets.add("15551234567")
    res = co.send_channel_campaign(conn, [1], "whatsapp", "Hi", eng, delay_range=(0, 0))
    assert res["failed"] == 1 and res["sent"] == 0
