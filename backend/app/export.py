import csv
import io

from app.models import Lead

COLUMNS = [
    "no", "company_en", "country", "city", "stage", "tags",
    "email", "phone", "website", "instagram", "facebook", "linkedin",
    "follow_up_date", "next_action",
    "email_status", "whatsapp_status", "instagram_status",
    "business",
]


def _row(lead: Lead) -> list:
    st = {o.channel: o.status for o in lead.outreach}
    return [
        lead.no, lead.company_en, lead.country, lead.city, lead.stage, lead.tags,
        lead.email, lead.phone, lead.website, lead.instagram, lead.facebook, lead.linkedin,
        lead.follow_up_date, lead.next_action,
        st.get("email", ""), st.get("whatsapp", ""), st.get("instagram", ""),
        lead.business,
    ]


def build_csv(leads: list[Lead]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(COLUMNS)
    for lead in leads:
        w.writerow(["" if v is None else v for v in _row(lead)])
    # utf-8-sig so Excel opens Chinese/accented text correctly
    return buf.getvalue().encode("utf-8-sig")


def build_xlsx(leads: list[Lead]) -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "leads"
    ws.append(COLUMNS)
    for lead in leads:
        ws.append(["" if v is None else v for v in _row(lead)])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
