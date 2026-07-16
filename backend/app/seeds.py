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
    ("跟进2：案例+提问（西语）", "es", "Re: Pantallas LED — una pregunta rápida",
     f"""Hola {{contact}}:

Le escribo de nuevo sobre los paneles LED para {{name}}.

Una pregunta rápida para no hacerle perder tiempo: ¿está cotizando para un proyecto concreto ahora mismo, o busca tener un proveedor a mano para cuando surja? Cualquiera de las dos respuestas me sirve — le enviaré solo lo que realmente le convenga.

Si prefiere no recibir estos correos, responda "unsubscribe" y no volveré a escribirle.

{SIGNOFF}"""),
    ("跟进3：最后一封（西语）", "es", "Re: Pantallas LED — cierro el tema",
     f"""Hola {{contact}}:

Este es mi último correo, no quiero llenarle la bandeja de entrada.

Si las pantallas LED no están entre sus prioridades ahora, no hay problema. Si surge algo más adelante, aquí abajo están mis datos y le envío precios el mismo día que me escriba.

{SIGNOFF}"""),
    ("跟进2：案例+提问（葡语）", "pt", "Re: Painéis LED — uma pergunta rápida",
     f"""Olá {{contact}},

Retomando o assunto dos painéis LED para a {{name}}.

Uma pergunta rápida para não tomar seu tempo: você está cotando para um projeto específico agora, ou quer manter um fornecedor à mão para quando surgir? Qualquer resposta me ajuda — envio só o que realmente faz sentido.

Se preferir não receber estes e-mails, responda "unsubscribe" e não entrarei mais em contato.

{SIGNOFF}"""),
    ("跟进3：最后一封（葡语）", "pt", "Re: Painéis LED — encerrando o assunto",
     f"""Olá {{contact}},

Este é meu último e-mail, não quero lotar sua caixa de entrada.

Se painéis LED não estão na sua pauta agora, sem problema. Se aparecer algo mais à frente, meus contatos estão abaixo e envio preços no mesmo dia em que você pedir.

{SIGNOFF}"""),
    ("首次触达（韩语）", "ko", "LED 디스플레이 패널 — 심천 공장 직거래",
     f"""안녕하세요 {{contact}}님,

저는 중국 심천의 LED 디스플레이 제조 공장에서 근무하는 Allen이라고 합니다.

{{name}}의 LED 디스플레이 관련 업무를 보고 연락드립니다. 저희는 P0.7–P10 실내외 LED 패널을 공장 직거래 가격으로 공급하고 있으며, 최근 프로젝트 자료를 첨부해 드립니다.

진행 중이거나 예정된 LED 디스플레이 건이 있으시면, 크기·시청 거리·픽셀 피치·실내외 용도에 맞춰 적합한 사양을 추천해 드리겠습니다.

이 메일 수신을 원치 않으시면 "unsubscribe"라고 회신해 주시면 더 이상 연락드리지 않겠습니다.

{SIGNOFF}"""),
    ("跟进2：案例+提问（韩语）", "ko", "Re: LED 디스플레이 패널 — 간단한 문의",
     f"""안녕하세요 {{contact}}님,

{{name}} 관련 LED 패널 건으로 다시 연락드립니다.

시간을 뺏지 않도록 간단히 여쭙겠습니다. 지금 특정 프로젝트를 위해 공급처를 찾고 계신가요, 아니면 필요할 때를 대비해 거래처를 확보해 두시려는 건가요? 어느 쪽이든 알려주시면 실제로 도움이 될 만한 자료만 보내드리겠습니다.

이 메일 수신을 원치 않으시면 "unsubscribe"라고 회신해 주십시오.

{SIGNOFF}"""),
    ("跟进3：最后一封（韩语）", "ko", "Re: LED 디스플레이 패널 — 마지막 안내",
     f"""안녕하세요 {{contact}}님,

받은 편지함을 어지럽히고 싶지 않아 이번이 마지막 메일입니다.

지금 LED 디스플레이가 검토 대상이 아니시라면 전혀 괜찮습니다. 추후 필요하시면 아래 연락처로 문의해 주시면, 요청하신 당일에 견적을 보내드리겠습니다.

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
    ("DM 首次触达（韩语）", "ko",
     "안녕하세요 {name}님, 저는 중국 심천의 LED 디스플레이 공장에서 근무하는 Allen입니다. P0.7–P10 실내외 LED 패널을 공장 직거래 가격으로 공급하고 있습니다. 예정된 LED 디스플레이 건이 있으시면 최근 프로젝트 자료를 기꺼이 공유해 드리겠습니다."),
    ("DM 跟进（英语）", "en",
     "Hi {name}, following up on my last message. Are you working on an LED display project right now, or should I check back later? Either way, happy to send specs and pricing whenever it's useful."),
]

def _by_lang(lang: str) -> dict[str, tuple[str, str]]:
    """{step_key: (subject, body)} for one language, keyed off the template names."""
    out = {}
    for name, tpl_lang, subject, body in EMAIL_TEMPLATES:
        if tpl_lang != lang:
            continue
        key = "first" if name.startswith("首次") else "f2" if name.startswith("跟进2") else "f3"
        out[key] = (subject, body)
    return out


# 冷邮件的回复几乎都在第 2–4 触，所以每个序列都是 3 步：第 0 / 3 / 8 天。
# 一语一序列：西语国家用英语话术回复率腰斩，所以不共用一个序列。
SEQUENCE_LANGS = [("en", "英语"), ("es", "西语"), ("pt", "葡语"), ("ko", "韩语")]

EMAIL_SEQUENCES = [
    {
        "name": f"冷邮件 3 步跟进（{label}）",
        "channel": "email",
        "steps": [
            {"day_offset": 0, "subject": _by_lang(lang)["first"][0], "body": _by_lang(lang)["first"][1]},
            {"day_offset": 3, "subject": _by_lang(lang)["f2"][0], "body": _by_lang(lang)["f2"][1]},
            {"day_offset": 8, "subject": _by_lang(lang)["f3"][0], "body": _by_lang(lang)["f3"][1]},
        ],
    }
    for lang, label in SEQUENCE_LANGS
]


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


def seed_sequences(conn) -> list[int]:
    """Add the 3-step cold-email sequences (EN/ES/PT); skips ones already there."""
    from app import sequences
    added = []
    for seq in EMAIL_SEQUENCES:
        if conn.execute("SELECT 1 FROM sequences WHERE name=?", (seq["name"],)).fetchone():
            continue
        added.append(sequences.create_sequence(conn, seq["name"], seq["channel"], seq["steps"]))
    return added
