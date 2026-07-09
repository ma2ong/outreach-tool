import datetime as _dt

import pytest

from app import sequences, repository
from app.db import connect, init_schema


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, country, email) VALUES
            (1, 'Alpha AV', 'USA', 'a@alpha.com'),
            (2, 'Beta Screens', 'USA', 'b@beta.com'),
            (3, 'Gamma LED', 'Brazil', 'g@gamma.com');
    """)
    c.commit()
    return c


def _seq(conn, channel="email"):
    return sequences.create_sequence(conn, "Cold 3-touch", channel, [
        {"day_offset": 0, "subject": "Hi {name}", "body": "First touch to {name}"},
        {"day_offset": 3, "subject": "Re: {name}", "body": "Second touch"},
        {"day_offset": 7, "body": "Last touch"},
    ])


def test_create_and_list(conn):
    sid = _seq(conn)
    seqs = sequences.list_sequences(conn)
    assert len(seqs) == 1
    assert seqs[0]["id"] == sid
    assert len(seqs[0]["steps"]) == 3
    assert seqs[0]["steps"][1]["day_offset"] == 3


def test_enroll_makes_step0_due_today(conn):
    sid = _seq(conn)
    n = sequences.enroll_leads(conn, sid, [1, 2])
    assert n == 2
    due = sequences.due_queue(conn)
    assert {d["lead_no"] for d in due} == {1, 2}
    assert all(d["step_order"] == 0 for d in due)
    assert due[0]["body"] == "First touch to {name}"


def test_enroll_skips_already_replied(conn):
    sid = _seq(conn)
    repository.mark_replied(conn, 1, "email")
    n = sequences.enroll_leads(conn, sid, [1, 2])
    assert n == 1  # lead 1 skipped
    assert {d["lead_no"] for d in sequences.due_queue(conn)} == {2}


def test_enroll_is_idempotent(conn):
    sid = _seq(conn)
    sequences.enroll_leads(conn, sid, [1])
    assert sequences.enroll_leads(conn, sid, [1]) == 0


def test_advance_moves_to_next_step_not_due_yet(conn):
    sid = _seq(conn)
    sequences.enroll_leads(conn, sid, [1])
    eid = sequences.due_queue(conn)[0]["enrollment_id"]
    sequences.advance_enrollment(conn, eid)
    # step 1 is day_offset 3 -> not due today
    assert sequences.due_queue(conn) == []
    row = conn.execute("SELECT current_step, status, next_due_date FROM sequence_enrollments"
                       " WHERE id=?", (eid,)).fetchone()
    assert row["current_step"] == 1
    assert row["status"] == "active"
    assert row["next_due_date"] > _dt.date.today().isoformat()


def test_advance_past_last_step_completes(conn):
    sid = _seq(conn)
    sequences.enroll_leads(conn, sid, [1])
    eid = sequences.due_queue(conn)[0]["enrollment_id"]
    sequences.advance_enrollment(conn, eid)
    sequences.advance_enrollment(conn, eid)  # -> step 2
    sequences.advance_enrollment(conn, eid)  # past last -> completed
    row = conn.execute("SELECT status FROM sequence_enrollments WHERE id=?", (eid,)).fetchone()
    assert row["status"] == "completed"


def test_reply_stops_active_enrollment(conn):
    sid = _seq(conn)
    sequences.enroll_leads(conn, sid, [1, 2])
    repository.mark_replied(conn, 1, "email")
    assert {d["lead_no"] for d in sequences.due_queue(conn)} == {2}
    row = conn.execute("SELECT status FROM sequence_enrollments WHERE lead_no=1").fetchone()
    assert row["status"] == "replied"


def test_reply_on_other_channel_does_not_stop(conn):
    sid = _seq(conn, "email")
    sequences.enroll_leads(conn, sid, [1])
    repository.mark_replied(conn, 1, "whatsapp")  # different channel
    assert {d["lead_no"] for d in sequences.due_queue(conn)} == {1}


def test_due_queue_filters_by_channel(conn):
    email_sid = _seq(conn, "email")
    wa_sid = sequences.create_sequence(conn, "WA", "whatsapp", [{"day_offset": 0, "body": "hi"}])
    sequences.enroll_leads(conn, email_sid, [1])
    sequences.enroll_leads(conn, wa_sid, [2])
    assert {d["lead_no"] for d in sequences.due_queue(conn, "email")} == {1}
    assert {d["lead_no"] for d in sequences.due_queue(conn, "whatsapp")} == {2}
