from app.channels import email_adapter


def test_build_message_has_subject_body_attachment(tmp_path):
    att = tmp_path / "poster.jpg"
    att.write_bytes(b"\xff\xd8\xff\xe0fake")
    msg = email_adapter.build_message(
        sender="me@gmail.com", to="x@y.com", subject="Hi Bob",
        body="Hello Bob", attachment=str(att))
    assert msg["To"] == "x@y.com"
    assert msg["Subject"] == "Hi Bob"
    payloads = msg.get_payload()
    assert any(p.get_filename() == "poster.jpg" for p in payloads)
    assert any(
        p.get_content_type() == "text/plain"
        and "Hello Bob" in p.get_payload(decode=True).decode("utf-8")
        for p in payloads
    )


def test_build_message_no_attachment():
    msg = email_adapter.build_message(
        sender="me@gmail.com", to="x@y.com", subject="S", body="B", attachment=None)
    assert msg["Subject"] == "S"


def test_missing_attachment_raises_not_silently_dropped():
    """The copy says 'I've attached a sheet' — sending without it looks broken to the
    customer, and Allen would never know. Fail loudly instead."""
    import pytest
    from app.channels.email_adapter import build_message
    with pytest.raises(FileNotFoundError):
        build_message("a@x.com", "b@y.com", "s", "b", r"C:\nope\missing.jpg")


def test_attachment_included_when_present(tmp_path):
    from app.channels.email_adapter import build_message
    f = tmp_path / "poster.jpg"
    f.write_bytes(b"img")
    msg = build_message("a@x.com", "b@y.com", "s", "b", str(f))
    assert any("poster.jpg" in str(p.get("Content-Disposition") or "") for p in msg.walk())


def test_465_ssl_failure_falls_back_to_starttls(monkeypatch):
    """This machine's network kills the TLS handshake on 465 (SSLEOFError) while 587
    works. Without the fallback, every send in a campaign fails."""
    import ssl
    from app.channels import email_adapter as ea

    tried: list[int] = []

    class FakeServer:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def sendmail(self, *a): pass

    def fake_open(host, port, user, pw):
        tried.append(port)
        if port == 465:
            raise ssl.SSLEOFError("EOF in violation of protocol")
        return FakeServer()

    monkeypatch.setattr(ea, "_open", fake_open)
    ea.send_via({"email": "a@x.com", "smtp_host": "smtp.gmail.com", "port": 465,
                 "username": "a@x.com", "password": "p"}, "b@y.com", "s", "b", None)
    assert tried == [465, 587]


def test_wrong_password_does_not_retry_on_587(monkeypatch):
    """A bad password must surface as a bad password, not get masked by a port retry."""
    import smtplib
    import pytest
    from app.channels import email_adapter as ea

    tried: list[int] = []

    def fake_open(host, port, user, pw):
        tried.append(port)
        raise smtplib.SMTPAuthenticationError(535, b"bad password")

    monkeypatch.setattr(ea, "_open", fake_open)
    with pytest.raises(smtplib.SMTPAuthenticationError):
        ea.test_mailbox({"email": "a@x.com", "smtp_host": "smtp.gmail.com", "port": 465,
                         "username": "a@x.com", "password": "wrong"})
    assert tried == [465]
