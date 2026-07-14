"""Ready-made templates and a follow-up sequence, loaded in one click.

The lead base has 800+ touches but zero saved templates and zero sequences: the
features exist, they just start from a blank page, so they never get used. These
seeds are Allen's actual outreach voice (factory-direct, no company name in DMs,
case photo attached) so the first send is one click, not one hour of typing.
"""

SIGNOFF = """Best regards,
Allen Ma
Shenzhen Maxcolor Visual Co., Ltd.
WhatsApp/WeChat: +86 135-7087-1001
Email: allenma2ong@gmail.com"""

OPT_OUT = 'If you\'d prefer not to receive these emails, just reply "unsubscribe" and I won\'t contact you again.'

EMAIL_TEMPLATES = [
    ("首次触达（英语）", "en", "LED Display Panels — Factory Direct from Shenzhen",
     f"""Hi {{contact}},

I'm Allen, from an LED display manufacturing factory in Shenzhen, China.

I came across {{name}} and your LED display work. We supply P0.7–P10 indoor and outdoor LED panels at factory-direct pricing, and I've attached a sheet of recent projects.

If you have an upcoming LED display need, I can recommend options based on size, viewing distance, pixel pitch, and indoor/outdoor use.

{OPT_OUT}

{SIGNOFF}"""),
    ("首次触达（西语）", "es", "Pantallas LED — Precio directo de fábrica (Shenzhen)",
     f"""Hola {{contact}}:

Soy Allen, de una fábrica de pantallas LED en Shenzhen, China.

Vi el trabajo de {{name}} en pantallas LED. Fabricamos paneles LED P0.7–P10 para interior y exterior a precio directo de fábrica. Adjunto una hoja con proyectos recientes.

Si tienen algún proyecto de pantalla LED, puedo recomendarles opciones según tamaño, distancia de visión, pixel pitch y uso interior/exterior.

Si prefiere no recibir estos correos, responda "unsubscribe" y no volveré a escribirle.

{SIGNOFF}"""),
    ("首次触达（葡语）", "pt", "Painéis LED — Preço direto de fábrica (Shenzhen)",
     f"""Olá {{contact}},

Sou o Allen, de uma fábrica de painéis LED em Shenzhen, China.

Vi o trabalho da {{name}} com painéis LED. Fornecemos painéis LED P0.7–P10 para interior e exterior a preço direto de fábrica. Segue em anexo uma folha com projetos recentes.

Se tiver algum projeto de painel LED, posso recomendar opções conforme tamanho, distância de visão, pixel pitch e uso interno/externo.

Se preferir não receber estes e-mails, responda "unsubscribe" e não entrarei mais em contato.

{SIGNOFF}"""),
    ("跟进2：案例+提问（英语）", "en", "Re: LED Display Panels — quick question",
     f"""Hi {{contact}},

Following up on my note about LED panels for {{name}}.

Quick question so I don't waste your time: are you sourcing for a specific project right now, or keeping a supplier on file for when one comes up? Either answer is useful — I'll send what actually fits.

{OPT_OUT}

{SIGNOFF}"""),
    ("跟进3：最后一封（英语）", "en", "Re: LED Display Panels — closing the loop",
     f"""Hi {{contact}},

Last note from me — I don't want to clutter your inbox.

If LED displays aren't on your radar, no problem at all. If they come up later, my details are below and I'll send pricing the same day you ask.

{SIGNOFF}"""),
]

# DM 规矩：不提公司名、只说 from Shenzhen China、必带案例图（发送端自动附图）
DM_TEMPLATES = [
    ("DM 首次触达（英语）", "en",
     "Hi {name}, this is Allen from an LED display factory in Shenzhen, China. We supply P0.7–P10 indoor and outdoor LED panels at factory-direct pricing. Happy to share recent project references if you have upcoming LED display needs."),
    ("DM 首次触达（西语）", "es",
     "Hola {name}, soy Allen, de una fábrica de pantallas LED en Shenzhen, China. Fabricamos paneles LED P0.7–P10 para interior y exterior a precio directo de fábrica. Con gusto le comparto referencias de proyectos recientes si tienen algún proyecto de pantalla LED."),
    ("DM 首次触达（葡语）", "pt",
     "Olá {name}, sou o Allen, de uma fábrica de painéis LED em Shenzhen, China. Fornecemos painéis LED P0.7–P10 para interior e exterior a preço direto de fábrica. Posso enviar referências de projetos recentes se tiver alguma necessidade de painel LED."),
    ("DM 跟进（英语）", "en",
     "Hi {name}, following up on my last message. Are you working on an LED display project right now, or should I check back later? Either way, happy to send specs and pricing whenever it's useful."),
]

# 冷邮件的回复几乎都在第 2–4 触，所以默认序列是 3 步：第 0 / 3 / 8 天。
EMAIL_SEQUENCE = {
    "name": "冷邮件 3 步跟进（英语）",
    "channel": "email",
    "steps": [
        {"day_offset": 0, "subject": EMAIL_TEMPLATES[0][2], "body": EMAIL_TEMPLATES[0][3]},
        {"day_offset": 3, "subject": EMAIL_TEMPLATES[3][2], "body": EMAIL_TEMPLATES[3][3]},
        {"day_offset": 8, "subject": EMAIL_TEMPLATES[4][2], "body": EMAIL_TEMPLATES[4][3]},
    ],
}


def seed_templates(conn) -> int:
    """Add the starter templates; skips any whose name already exists."""
    from app import repository
    existing = {t.name for t in repository.list_templates(conn)}
    added = 0
    for name, lang, subject, body in EMAIL_TEMPLATES:
        if name not in existing:
            repository.add_template(conn, name, "email", subject, body, lang)
            added += 1
    for name, lang, body in DM_TEMPLATES:
        for channel in ("whatsapp", "instagram"):
            full = f"{name} · {'WA' if channel == 'whatsapp' else 'IG'}"
            if full not in existing:
                repository.add_template(conn, full, channel, None, body, lang)
                added += 1
    return added


def seed_sequence(conn) -> int | None:
    """Add the 3-step cold-email follow-up sequence if it isn't there yet."""
    from app import sequences
    row = conn.execute("SELECT id FROM sequences WHERE name=?", (EMAIL_SEQUENCE["name"],)).fetchone()
    if row:
        return None
    return sequences.create_sequence(conn, EMAIL_SEQUENCE["name"], EMAIL_SEQUENCE["channel"],
                                     EMAIL_SEQUENCE["steps"])
