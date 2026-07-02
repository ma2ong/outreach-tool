from app import jobs


def test_job_lifecycle():
    jobs.clear()
    jid = jobs.create(total=3)
    assert jobs.get(jid)["status"] == "running"
    assert jobs.get(jid)["total"] == 3
    jobs.update(jid, done=2)
    assert jobs.get(jid)["done"] == 2
    jobs.finish(jid, {"sent": 3, "failed": 0, "skipped": 0, "errors": []})
    j = jobs.get(jid)
    assert j["status"] == "done"
    assert j["result"]["sent"] == 3


def test_get_unknown_returns_none():
    jobs.clear()
    assert jobs.get("nope") is None
