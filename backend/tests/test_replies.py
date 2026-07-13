import pytest

from app import replies, sequences
from app.db import connect, init_schema


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, country, email) VALUES
            (1, 'Alpha AV', 'USA', 'sales@alpha.com'),
            (2, 'Beta Screens', 'USA', 'b@beta.com'),
            (3, 'Gamma LED', 'Brazil', 'g@gamma.com');
        INSERT INTO outreach(lead_no, channel, status, touch_count) VALUES
            (1, 'email', 'messaged', 1),
            (2, 'email', 'messaged', 1);
    """)
    c.commit()
    return c


def test_match_marks_replied_case_insensitive(conn):
    res = replies.match_and_mark(conn, ["SALES@Alpha.com"])
    assert res == {"matched": 1, "newly_replied": 1, "lead_nos": [1]}
    row = conn.execute("SELECT status FROM outreach WHERE lead_no=1 AND channel='email'").fetchone()
    assert row["status"] == "replied"


def test_unknown_sender_ignored(conn):
    assert replies.match_and_mark(conn, ["stranger@nope.com"])["matched"] == 0


def test_already_replied_not_double_counted(conn):
    replies.match_and_mark(conn, ["b@beta.com"])
    res = replies.match_and_mark(conn, ["b@beta.com"])
    assert res["matched"] == 1 and res["newly_replied"] == 0


def test_reply_stops_sequence_enrollment(conn):
    sid = sequences.create_sequence(conn, "S", "email", [{"day_offset": 0, "body": "hi"}])
    sequences.enroll_leads(conn, sid, [1, 2])
    replies.match_and_mark(conn, ["sales@alpha.com"])
    assert {d["lead_no"] for d in sequences.due_queue(conn)} == {2}


def test_poll_uses_injected_fetcher(conn):
    fake = [{"from_addr": "g@gamma.com", "subject": "Re: LED", "body": "hi", "received_at": ""}]
    res = replies.poll_replies(conn, fetch_messages=lambda days: fake)
    assert res["lead_nos"] == [3]
