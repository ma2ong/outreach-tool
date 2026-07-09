from app import repository as repo
from app.db import connect, init_schema


def _conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    return c


def test_add_and_list_templates(tmp_path):
    c = _conn(tmp_path)
    tid = repo.add_template(c, "韩国邮件", "email", "LED projects", "Hi {name}...")
    repo.add_template(c, "WA 开场", "whatsapp", None, "Hi {name}, Allen here")
    assert isinstance(tid, int)
    email = repo.list_templates(c, channel="email")
    assert [t.name for t in email] == ["韩国邮件"]
    assert email[0].body == "Hi {name}..."
    assert len(repo.list_templates(c)) == 2


def test_delete_template(tmp_path):
    c = _conn(tmp_path)
    tid = repo.add_template(c, "临时", "whatsapp", None, "x")
    assert repo.delete_template(c, tid) is True
    assert repo.list_templates(c) == []
    assert repo.delete_template(c, 999) is False
