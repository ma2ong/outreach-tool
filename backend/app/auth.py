"""Single-user password auth, active only when a password file exists.

No password file -> auth disabled entirely: local double-click usage and tests
stay friction-free. Before exposing the app to the internet, create the file
(start_online.bat refuses to start the tunnel without it).

Session = HMAC(password, session_key) in an HttpOnly cookie; the key is random,
persisted next to the DB, so sessions survive restarts but rotating the file
logs everyone out. A small in-memory lockout slows brute force.
"""
import hashlib
import hmac
import os
import secrets
import time

PASSWORD_FILE = os.environ.get("OUTREACH_PASSWORD_FILE", "auth_password.txt")
SESSION_KEY_FILE = os.environ.get("OUTREACH_SESSION_KEY_FILE", ".session_key")
COOKIE_NAME = "outreach_session"

_FAILS: dict[str, list[float]] = {}
LOCKOUT_AFTER = 5
LOCKOUT_SECONDS = 60


def get_password() -> str | None:
    try:
        with open(PASSWORD_FILE, encoding="utf-8") as f:
            pw = f.read().strip()
        return pw or None
    except OSError:
        return None


def enabled() -> bool:
    return get_password() is not None


def _session_key() -> bytes:
    try:
        with open(SESSION_KEY_FILE, "rb") as f:
            key = f.read()
        if key:
            return key
    except OSError:
        pass
    key = secrets.token_bytes(32)
    with open(SESSION_KEY_FILE, "wb") as f:
        f.write(key)
    return key


def _token(password: str) -> str:
    return hmac.new(_session_key(), password.encode(), hashlib.sha256).hexdigest()


def issue_token() -> str:
    return _token(get_password() or "")


def verify_token(token: str | None) -> bool:
    if not enabled():
        return True
    return bool(token) and hmac.compare_digest(token, issue_token())


def locked_out(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _FAILS.get(ip, []) if now - t < LOCKOUT_SECONDS]
    _FAILS[ip] = recent
    return len(recent) >= LOCKOUT_AFTER


def check_password(candidate: str, ip: str = "?") -> bool:
    pw = get_password()
    ok = pw is not None and hmac.compare_digest(candidate.encode(), pw.encode())
    if not ok:
        _FAILS.setdefault(ip, []).append(time.time())
    else:
        _FAILS.pop(ip, None)
    return ok
