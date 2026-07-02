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
