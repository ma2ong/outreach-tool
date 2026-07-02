import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

GMAIL_USER = "allenma2ong@gmail.com"
PW_FILE = Path.home() / ".gmail_app_password"


def get_password() -> str:
    return os.environ.get("GMAIL_APP_PASSWORD") or (
        PW_FILE.read_text(encoding="utf-8").strip() if PW_FILE.exists() else "")


def build_message(sender: str, to: str, subject: str, body: str, attachment: str | None) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    if attachment and os.path.exists(attachment):
        with open(attachment, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(attachment)}"')
        msg.attach(part)
    return msg


def send_email(to: str, subject: str, body: str, attachment: str | None = None) -> None:
    pw = get_password()
    if not pw:
        raise RuntimeError("Gmail app password missing (~/.gmail_app_password or GMAIL_APP_PASSWORD)")
    msg = build_message(GMAIL_USER, to, subject, body, attachment)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, pw)
        server.sendmail(GMAIL_USER, to, msg.as_bytes())
