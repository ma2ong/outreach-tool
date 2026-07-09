from pydantic import BaseModel


class OutreachStatus(BaseModel):
    channel: str
    status: str
    touch_count: int = 0
    message_sent_date: str | None = None
    reply_received: bool = False
    exclude_reason: str | None = None


class Note(BaseModel):
    id: int
    created_at: str | None = None
    text: str


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
    stage: str = "new"
    tags: str | None = None
    follow_up_date: str | None = None
    next_action: str | None = None
    source_urls: list[str] = []
    outreach: list[OutreachStatus] = []
    notes: list[Note] = []


class Stats(BaseModel):
    total: int
    by_country: dict[str, int]
    by_channel_status: dict[str, dict[str, int]]
    reach: dict[str, dict[str, int]] = {}
    funnel: dict[str, int] = {}
