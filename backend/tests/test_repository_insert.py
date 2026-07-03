from app import repository as repo


def test_next_no_empty(tmp_path):
    from app.db import connect, init_schema
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    assert repo.next_no(c) == 1


def test_insert_and_next_no(conn):
    n = repo.next_no(conn)  # conn fixture has leads 1..3
    assert n == 4
    repo.insert_lead(conn, {"company_en": "New Co", "country": "USA",
                            "website": "new.com", "email": "info@new.com"})
    lead = repo.get_lead(conn, 4)
    assert lead.company_en == "New Co"
    assert lead.email == "info@new.com"
    assert repo.next_no(conn) == 5
