import { useEffect, useState } from "react";
import { startEmailSend, startChannelSend, fetchJob, fetchQuota, fetchTemplates, createTemplate } from "../api";
import type { SendJob, Template } from "../types";

const DEFAULT_SUBJECT = "Recent LED Display Installations in Korea";
const DEFAULT_BODY = `Hi {name},

I'm Allen, from an LED display manufacturing factory in Shenzhen, China.

I came across your LED video wall and display work and wanted to share a recent project reference from Korea. The attached sheet includes indoor fine-pitch LED walls, outdoor LED screens, and commercial installations.

If you ever need LED panels or full displays, I can recommend options based on size, viewing distance, pixel pitch, and indoor/outdoor use.

If you'd prefer not to receive these emails, just reply "unsubscribe" and I won't contact you again.

Best regards,
Allen Ma
Shenzhen Maxcolor Visual Co., Ltd.
WhatsApp/WeChat: +86 135-7087-1001
Email: allenma2ong@gmail.com`;

const DM_BODY = `Hi {name}, this is Allen from an LED display factory in Shenzhen, China. We supply P0.7–P10 indoor and outdoor LED panels at factory-direct pricing. Happy to share recent project references if you have upcoming LED display needs.`;

export function OutreachPanel({ selected, onDone }: { selected: number[]; onDone: () => void }) {
  const [channel, setChannel] = useState("email");
  const [subject, setSubject] = useState(DEFAULT_SUBJECT);
  const [body, setBody] = useState(DEFAULT_BODY);
  const [dm, setDm] = useState(DM_BODY);
  const [job, setJob] = useState<SendJob | null>(null);
  const [msg, setMsg] = useState("");
  const [sending, setSending] = useState(false);
  const [quota, setQuota] = useState<Record<string, { sent_today: number; cap: number }>>({});
  const [templates, setTemplates] = useState<Template[]>([]);
  const [tplName, setTplName] = useState("");
  const [attachment, setAttachment] = useState("");

  const isEmail = channel === "email";
  useEffect(() => {
    if (!isEmail) fetchQuota().then(setQuota).catch(() => {});
  }, [channel, sending, isEmail]);
  useEffect(() => { fetchTemplates(channel).then(setTemplates).catch(() => {}); }, [channel]);

  function applyTemplate(id: string) {
    const t = templates.find((x) => String(x.id) === id);
    if (!t) return;
    if (isEmail) { if (t.subject) setSubject(t.subject); setBody(t.body); }
    else setDm(t.body);
  }

  async function saveTemplate() {
    const name = tplName.trim();
    if (!name) { setMsg("请先填模板名"); return; }
    try {
      await createTemplate({ name, channel, subject: isEmail ? subject : null, body: isEmail ? body : dm });
      setTplName(""); setMsg(`已保存模板「${name}」`);
      fetchTemplates(channel).then(setTemplates).catch(() => {});
    } catch (e) { setMsg("保存模板失败：" + String(e)); }
  }

  async function send() {
    if (selected.length === 0) { setMsg("请先勾选客户"); return; }
    setSending(true); setMsg(""); setJob(null);
    try {
      const att = attachment.trim() || undefined;
      const start = isEmail
        ? await startEmailSend({ lead_nos: selected, subject, body, ...(att ? { attachment: att } : {}) })
        : await startChannelSend(channel, selected, dm, att);
      const unit = isEmail ? "有邮箱" : channel === "whatsapp" ? "有电话" : "有IG";
      const willSend = (start as { will_send?: number }).will_send;
      const capNote = !isEmail && willSend !== undefined && willSend < start.eligible
        ? `，本批只发前 ${willSend} 家（防封号上限），其余 ${start.eligible - willSend} 家下次再发`
        : "";
      setMsg(`已选 ${start.selected} 家，符合条件（${unit}且未发过）${start.eligible} 家${capNote}，开始发送…`);
      const poll = setInterval(async () => {
        const j = await fetchJob(start.job_id);
        setJob(j);
        if (j.status !== "running") { clearInterval(poll); setSending(false); onDone(); }
      }, 1500);
    } catch (e) { setMsg("发送失败：" + String(e)); setSending(false); }
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <h3 style={{ margin: 0, fontSize: 15 }}>触达（已选 {selected.length} 家）</h3>
        <select className="input" value={channel} onChange={(e) => setChannel(e.target.value)}>
          <option value="email">Email</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="instagram">Instagram</option>
        </select>
      </div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap", alignItems: "center" }}>
        <select className="input" value="" onChange={(e) => applyTemplate(e.target.value)} title="载入已存话术模板">
          <option value="">{templates.length ? "选择模板载入…" : "（暂无模板）"}</option>
          {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <input className="input" style={{ width: 140 }} placeholder="模板名" value={tplName} onChange={(e) => setTplName(e.target.value)} />
        <button className="btn btn-sm" onClick={saveTemplate}>另存为模板</button>
      </div>
      {isEmail ? (
        <>
          <input className="input" style={{ width: "100%", marginBottom: 8 }} value={subject} onChange={(e) => setSubject(e.target.value)} />
          <textarea className="input" style={{ height: 150 }} value={body} onChange={(e) => setBody(e.target.value)} />
        </>
      ) : (
        <>
          <div className="warn-text" style={{ marginBottom: 6 }}>
            ⚠️ {channel === "whatsapp" ? "WhatsApp" : "Instagram"} 自动私信有平台限制，已强制限速（每条间隔 1-4 分钟），单批上限 20 条。每条消息自动附带案例图。请先在「渠道连接」里确认已连接。
            {quota[channel] && ` 今日已发 ${quota[channel].sent_today}/${quota[channel].cap}${quota[channel].sent_today >= quota[channel].cap ? "，已到日上限，明天再发" : ""}`}
          </div>
          <textarea className="input" style={{ height: 100 }} value={dm} onChange={(e) => setDm(e.target.value)} />
        </>
      )}
      <div style={{ marginTop: 8 }}>
        <input className="input" style={{ width: "100%" }} value={attachment} onChange={(e) => setAttachment(e.target.value)}
          placeholder="附件路径（留空 = 默认案例图；可粘贴「产品报价」页生成的报价卡路径）" title="随消息发送的图片/附件文件路径" />
      </div>
      <div style={{ marginTop: 10, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <button className="btn btn-green" onClick={send} disabled={sending}>
          {sending ? "发送中…" : isEmail ? "发送邮件" : `发送 ${channel === "whatsapp" ? "WhatsApp" : "Instagram"} 私信`}
        </button>
        {job && <span className="muted">进度 {job.done}/{job.total}
          {job.status === "done" && job.result && "sent" in job.result &&
            ` — 成功 ${job.result.sent}，失败 ${job.result.failed}，跳过 ${job.result.skipped}${job.result.deferred ? `，延后 ${job.result.deferred}` : ""}`}
          {job.status === "error" && job.result && "error" in job.result && ` — 错误：${job.result.error}`}
        </span>}
      </div>
      {msg && <div className="muted" style={{ marginTop: 8 }}>{msg}</div>}
    </div>
  );
}
