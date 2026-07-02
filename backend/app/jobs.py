import uuid

_JOBS: dict[str, dict] = {}


def clear() -> None:
    _JOBS.clear()


def create(total: int) -> str:
    jid = uuid.uuid4().hex[:12]
    _JOBS[jid] = {"id": jid, "status": "running", "done": 0, "total": total, "result": None}
    return jid


def update(jid: str, done: int) -> None:
    if jid in _JOBS:
        _JOBS[jid]["done"] = done


def finish(jid: str, result: dict) -> None:
    if jid in _JOBS:
        _JOBS[jid].update(status="done", result=result)


def fail(jid: str, error: str) -> None:
    if jid in _JOBS:
        _JOBS[jid].update(status="error", result={"error": error})


def get(jid: str) -> dict | None:
    return _JOBS.get(jid)
