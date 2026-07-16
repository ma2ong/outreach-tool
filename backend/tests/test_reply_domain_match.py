"""Cold email goes to info@/sales@ but the human who replies is often a different
person at the same company (john@acme.com). Exact-email matching misses that reply,
so the sequence keeps chasing someone who already answered. Domain fallback fixes it,
but must never fire on free-mail domains (john@gmail.com is not 'the same company' as
info@gmail.com).
"""
import pytest

from app import replies, sequences
from app.db import connect, init_schema


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, country, email) VALUES
            (1, 'Acme LED',   'USA', 'info@acme.com'),
            (2, 'Beta Screens','USA', 'sales@beta.com'),
            (3, 'Gmail Guy',  'USA', 'someone@gmail.com'),
            (4, 'Acme Sales', 'USA', 'sales@acme.com');
        INSERT INTO outreach(lead_no, channel, status, touch_count) VALUES
            (1, 'email', 'messaged', 1),
            (2, 'email', 'messaged', 1),
            (3, 'email', 'messaged', 1),
            (4, 'email', 'messaged', 1);
    """)
    c.commit()
    return c


def _msg(from_addr, subject="Re: LED", body="interested, send a quote"):
    return {"from_addr": from_addr, "subject": subject, "body": body,
            "received_at": "2026-07-16T09:00:00"}


def test_reply_from_different_person_same_company_is_matched(conn):
    # we emailed info@acme.com; the reply comes from john@acme.com
    res = replies.process_messages(conn, [_msg("john@acme.com")])
    assert res["replies"] >= 1
    # both acme.com leads are marked replied — the whole company answered
    for no in (1, 4):
        st = conn.execute("SELECT status FROM outreach WHERE lead_no=? AND channel='email'", (no,)).fetchone()
        assert st["status"] == "replied", f"lead {no} should be replied"


def test_domain_fallback_does_not_touch_other_companies(conn):
    replies.process_messages(conn, [_msg("john@acme.com")])
    st = conn.execute("SELECT status FROM outreach WHERE lead_no=2 AND channel='email'").fetchone()
    assert st["status"] == "messaged"  # beta.com untouched


def test_free_mail_domain_never_matches_by_domain(conn):
    # a stranger at gmail.com must NOT mark our gmail lead as replied
    res = replies.process_messages(conn, [_msg("random.person@gmail.com")])
    assert res["replies"] == 0
    st = conn.execute("SELECT status FROM outreach WHERE lead_no=3 AND channel='email'").fetchone()
    assert st["status"] == "messaged"


def test_exact_match_still_wins(conn):
    res = replies.process_messages(conn, [_msg("sales@beta.com")])
    assert res["replies"] == 1
    assert res["lead_nos"] == [2]


def test_domain_reply_stops_sequence_for_whole_company(conn):
    sid = sequences.create_sequence(conn, "S", "email", [{"day_offset": 0, "body": "hi"},
                                                          {"day_offset": 3, "body": "follow up"}])
    sequences.enroll_leads(conn, sid, [1, 4])
    replies.process_messages(conn, [_msg("procurement@acme.com")])
    # neither acme lead should still be due — both companies-people are done
    assert sequences.due_queue(conn) == []
