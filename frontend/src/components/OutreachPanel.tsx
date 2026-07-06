import { useState } from "react";
import { startEmailSend, startChannelSend, fetchJob } from "../api";
import type { SendJob } from "../types";

const DEFAULT_SUBJECT = "Recent LED Display Installations in Korea";
const DEFAULT_BODY = `Hi {name},

I'm Allen, from an LED display manufacturing factory in Shenzhen, China.

I came across your LED video wall and display work and wanted to share a recent project reference from Korea. The attached sheet includes indoor fine-pitch LED walls, outdoor LED screens, and commercial installations.

If you ever need LED panels or full displays, I can recommend options based on size, viewing distance, pixel pitch, and indoor/outdoor use.

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

  const isEmail = channel === "email";

  async function send() {
    if (selected.length === 0) { setMsg("请先勾选客户"); return; }
    setSending(true); setMsg(""); setJob(null);
    try {
      const start = isEmail
        ? await startEmailSend({ lead_nos: selected, subject, body })
        : await startChannelSend(channel, selected, dm);
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

  const box = { background: "#0d1117", color: "#e6edf3", border: "1px solid #30363d", borderRadius: 6, padding: 8, width: "100%" };
  return (
    <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 16, marginBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <h3 style={{ color: "#e6edf3", margin: 0 }}>触达（已选 {selected.length} 家）</h3>
        <select value={channel} onChange={(e) => setChannel(e.target.value)} style={{ ...box, width: "auto" }}>
          <option value="email">Email</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="instagram">Instagram</option>
        </select>
      </div>
      {isEmail ? (
        <>
          <input style={{ ...box, marginBottom: 8 }} value={subject} onChange={(e) => setSubject(e.target.value)} />
          <textarea style={{ ...box, height: 180, fontFamily: "inherit" }} value={body} onChange={(e) => setBody(e.target.value)} />
        </>
      ) : (
        <>
          <div style={{ color: "#d29922", fontSize: 13, marginBottom: 6 }}>
            ⚠️ {channel === "whatsapp" ? "WhatsApp" : "Instagram"} 自动私信有平台限制，已强制限速（每条间隔 1-4 分钟），单批上限 20 条。请先在「渠道连接」里确认已连接。
          </div>
          <textarea style={{ ...box, height: 120, fontFamily: "inherit" }} value={dm} onChange={(e) => setDm(e.target.value)} />
        </>
      )}
      <div style={{ marginTop: 10, display: "flex", gap: 12, alignItems: "center" }}>
        <button onClick={send} disabled={sending}
          style={{ background: sending ? "#30363d" : "#238636", color: "#fff", border: "none", borderRadius: 6, padding: "8px 18px", cursor: sending ? "default" : "pointer" }}>
          {sending ? "发送中…" : isEmail ? "发送邮件" : `发送 ${channel === "whatsapp" ? "WhatsApp" : "Instagram"} 私信`}
        </button>
        {job && <span style={{ color: "#8b949e" }}>进度 {job.done}/{job.total}
          {job.status === "done" && job.result && "sent" in job.result &&
            ` — 成功 ${job.result.sent}，失败 ${job.result.failed}，跳过 ${job.result.skipped}${job.result.deferred ? `，延后 ${job.result.deferred}` : ""}`}
          {job.status === "error" && job.result && "error" in job.result && ` — 错误：${job.result.error}`}
        </span>}
      </div>
      {msg && <div style={{ color: "#8b949e", marginTop: 8 }}>{msg}</div>}
    </div>
  );
}
