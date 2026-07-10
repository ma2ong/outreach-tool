"""ICP classification: what kind of LED buyer is this company, and how good a fit?

Classifies a company from its website text into a buyer type and a 0-100 fit score
so the rep works the highest-value prospects first. Categories reflect how LED
display buyers actually differ in value to a manufacturer:

- rental      : event/staging companies — buy repeatedly, price-driven, best fit
- integrator  : AV/system integrators — project pipelines, recurring, best fit
- reseller    : distributors/wholesalers of displays — volume, strong fit
- signage     : sign makers/digital signage cos — regular panel demand, strong fit
- end-user    : venues/retail/churches buying for themselves — one-off, medium
- unknown     : no signal found

Scoring: base score per matched category (weights below) + small bonus per extra
distinct keyword hit (capped). Text matching is case-insensitive substring — the
input is jina-fetched page markdown.
"""
import re

# category -> (base_score, keywords). First matched category (by score desc) wins the label;
# keywords deliberately include common Spanish/Portuguese variants for LatAm sites.
_CATEGORIES: dict[str, tuple[int, tuple[str, ...]]] = {
    "rental": (90, (
        "rental", "staging", "event production", "stage rental", "av rental",
        "concert", "festival", "touring", "alquiler", "locação", "eventos",
    )),
    "integrator": (85, (
        "av integrat", "system integrat", "audiovisual integrat", "integration services",
        "installation services", "audio visual solutions", "av solutions", "integrador",
    )),
    "reseller": (80, (
        "distributor", "wholesale", "reseller", "supplier of led", "led screen supplier",
        "we supply", "dealer", "distribuidor", "mayorista", "atacado",
    )),
    "signage": (75, (
        "signage", "sign company", "sign shop", "billboard", "custom signs",
        "digital sign", "led sign", "letreros", "rotulos", "comunicação visual",
    )),
    "end-user": (50, (
        "our venue", "our church", "our stadium", "our store", "retail chain",
        "shopping mall", "casino", "house of worship",
    )),
}

_BONUS_PER_HIT = 2
_BONUS_CAP = 10

_LABELS = {"rental": "租赁公司", "integrator": "AV集成商", "reseller": "经销商",
           "signage": "标识/广告牌", "end-user": "终端用户", "unknown": "未知"}


def classify_text(text: str) -> dict:
    """Return {icp_type, fit_score, hits} for a page text."""
    low = (text or "").lower()
    best_type, best_score, best_hits = "unknown", 0, []
    for cat, (base, keywords) in _CATEGORIES.items():
        hits = [k for k in keywords if k in low]
        if not hits:
            continue
        score = min(100, base + min(_BONUS_CAP, _BONUS_PER_HIT * (len(hits) - 1)))
        if score > best_score:
            best_type, best_score, best_hits = cat, score, hits
    return {"icp_type": best_type, "fit_score": best_score, "hits": best_hits}


def label(icp_type: str) -> str:
    return _LABELS.get(icp_type, icp_type)


_TAG_RE = re.compile(r"^icp:", re.I)


def apply_to_lead(conn, lead_no: int, icp: dict) -> None:
    """Store classification: target_fit = '类型 (score)', tags get an icp:<type> tag."""
    if icp["icp_type"] == "unknown":
        return
    fit = f"{label(icp['icp_type'])} ({icp['fit_score']})"
    row = conn.execute("SELECT tags FROM leads WHERE no=?", (lead_no,)).fetchone()
    if row is None:
        return
    tags = [t.strip() for t in (row["tags"] or "").split(",") if t.strip()]
    tags = [t for t in tags if not _TAG_RE.match(t)]  # replace any previous icp tag
    tags.append(f"icp:{icp['icp_type']}")
    conn.execute("UPDATE leads SET target_fit=?, tags=? WHERE no=?",
                 (fit, ",".join(tags), lead_no))
    conn.commit()
