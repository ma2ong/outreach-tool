import os

from app.main import BACKUP_KEEP, backup_db


def test_backup_creates_dated_copy(tmp_path):
    db = tmp_path / "outreach.db"
    db.write_bytes(b"data")
    dest = backup_db(str(db))
    assert dest and os.path.isfile(dest)
    assert os.path.dirname(dest).endswith("backups")


def test_backup_idempotent_same_day(tmp_path):
    db = tmp_path / "outreach.db"
    db.write_bytes(b"v1")
    dest = backup_db(str(db))
    db.write_bytes(b"v2")
    backup_db(str(db))  # same day: must NOT overwrite the morning snapshot
    with open(dest, "rb") as f:
        assert f.read() == b"v1"


def test_backup_missing_db_noop(tmp_path):
    assert backup_db(str(tmp_path / "nope.db")) is None


def test_backup_prunes_old(tmp_path):
    db = tmp_path / "outreach.db"
    db.write_bytes(b"data")
    bdir = tmp_path / "backups"
    bdir.mkdir()
    for i in range(20):
        (bdir / f"outreach-2026-01-{i + 1:02d}.db").write_bytes(b"old")
    backup_db(str(db))
    assert len(list(bdir.glob("outreach-*.db"))) == BACKUP_KEEP
