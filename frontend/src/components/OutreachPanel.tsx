import { useState } from "react";
import { startEmailSend, fetchJob } from "../api";
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

export function OutreachPanel({ selected, onDone }: { selected: number[]; onDone: () => void }) {
  const [subject, setSubject] = useState(DEFAULT_SUBJECT);
  const [body, setBody] = useState(DEFAULT_BODY);
  const [job, setJob] = useState<SendJob | null>(null);
  const [msg, setMsg] = useState("");
  const [sending, setSending] = useState(false);

  async function send() {
    if (selected.length === 0) { setMsg("请先勾选客户"); return; }
    setSending(true); setMsg(""); setJob(null);
    try {
      const start = await startEmailSend({ lead_nos: selected, subject, body });
      setMsg(`已选 ${start.selected} 家，符合发送条件（有邮箱且未发过）${start.eligible} 家，开始发送…`);
      const poll = setInterval(async () => {
        const j = await fetchJob(start.job_id);
        setJob(j);
        if (j.status !== "running") {
          clearInterval(poll); setSending(false); onDone();
        }
      }, 1500);
    } catch (e) { setMsg("发送失败：" + String(e)); setSending(false); }
  }

  const box = { background: "#0d1117", color: "#e6edf3", border: "1px solid #30363d", borderRadius: 6, padding: 8, width: "100%" };
  return (
    <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 16, marginBottom: 20 }}>
      <h3 style={{ color: "#e6edf3", marginTop: 0 }}>邮件触达（已选 {selected.length} 家）</h3>
      <input style={{ ...box, marginBottom: 8 }} value={subject} onChange={(e) => setSubject(e.target.value)} />
      <textarea style={{ ...box, height: 180, fontFamily: "inherit" }} value={body} onChange={(e) => setBody(e.target.value)} />
      <div style={{ marginTop: 10, display: "flex", gap: 12, alignItems: "center" }}>
        <button onClick={send} disabled={sending}
          style={{ background: sending ? "#30363d" : "#238636", color: "#fff", border: "none", borderRadius: 6, padding: "8px 18px", cursor: sending ? "default" : "pointer" }}>
          {sending ? "发送中…" : "发送邮件"}
        </button>
        {job && <span style={{ color: "#8b949e" }}>进度 {job.done}/{job.total}
          {job.status === "done" && job.result && "sent" in job.result &&
            ` — 成功 ${job.result.sent}，失败 ${job.result.failed}，跳过 ${job.result.skipped}`}
          {job.status === "error" && job.result && "error" in job.result && ` — 错误：${job.result.error}`}
        </span>}
      </div>
      {msg && <div style={{ color: "#8b949e", marginTop: 8 }}>{msg}</div>}
    </div>
  );
}
