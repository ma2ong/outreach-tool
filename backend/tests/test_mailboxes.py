import pytest

from app import mailboxes as mb
from app.db import connect, init_schema


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    return c


def _add(conn, email, cap=2):
    return mb.add_mailbox(conn, email, "smtp.x.com", 465, email, "pw", daily_cap=cap)


def test_add_list_hides_password(conn):
    _add(conn, "a@x.com")
    rows = mb.list_mailboxes(conn)
    assert rows[0]["email"] == "a@x.com"
    assert "password" not in rows[0]
    assert rows[0]["sent_today"] == 0
    assert mb.list_mailboxes(conn, include_secrets=True)[0]["password"] == "pw"


def test_no_active_falls_through(conn):
    assert mb.has_active(conn) is False
    assert mb.pick_mailbox(conn) is None
    assert mb.total_remaining(conn) == 0


def test_pick_least_used_then_records(conn):
    a = _add(conn, "a@x.com", cap=2)
    b = _add(conn, "b@x.com", cap=2)
    assert mb.total_remaining(conn) == 4
    # first pick: lowest id among equal usage
    m1 = mb.pick_mailbox(conn); mb.record_send(conn, m1["id"])
    assert m1["id"] == a
    # now a has 1 send, b has 0 -> pick b
    m2 = mb.pick_mailbox(conn); mb.record_send(conn, m2["id"])
    assert m2["id"] == b
    assert mb.total_remaining(conn) == 2


def test_capped_mailbox_excluded(conn):
    a = _add(conn, "a@x.com", cap=1)
    mb.record_send(conn, a)
    assert mb.pick_mailbox(conn) is None       # a is capped, no others
    assert mb.total_remaining(conn) == 0
    b = _add(conn, "b@x.com", cap=1)
    assert mb.pick_mailbox(conn)["id"] == b     # b still has room


def test_inactive_excluded(conn):
    a = _add(conn, "a@x.com", cap=5)
    mb.set_active(conn, a, False)
    assert mb.has_active(conn) is False
    assert mb.pick_mailbox(conn) is None


def test_delete(conn):
    a = _add(conn, "a@x.com")
    assert mb.delete_mailbox(conn, a) is True
    assert mb.list_mailboxes(conn) == []
