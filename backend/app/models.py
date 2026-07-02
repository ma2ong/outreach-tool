from pydantic import BaseModel


class OutreachStatus(BaseModel):
    channel: str
    status: str
    touch_count: int = 0
    message_sent_date: str | None = None
    reply_received: bool = False
    exclude_reason: str | None = None


class Lead(BaseModel):
    no: int
    company_en: str
    company_local: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    linkedin: str | None = None
    business: str | None = None
    target_fit: str | None = None
    whatsapp_verified: bool = False
    source_urls: list[str] = []
    outreach: list[OutreachStatus] = []


class Stats(BaseModel):
    total: int
    by_country: dict[str, int]
    by_channel_status: dict[str, dict[str, int]]
