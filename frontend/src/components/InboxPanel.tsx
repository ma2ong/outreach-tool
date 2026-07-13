import { useEffect, useState } from "react";
import { fetchInbox, markInboxRead, pollReplies } from "../api";
import type { InboxMessage } from "../types";

const KIND_LABEL: Record<string, string> = { reply: "回复", bounce: "退信", unsubscribe: "退订" };
const KIND_COLOR: Record<string, string> = { reply: "badge-replied", bounce: "badge-untouched", unsubscribe: "badge-messaged" };

function fmtTs(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(+d) ? iso : d.toLocaleString();
}

export function InboxPanel({ onOpenLead, onUnreadChange }: {
  onOpenLead: (leadNo: number) => void;
  onUnreadChange?: () => void;
}) {
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const [polling, setPolling] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  function reload() {
    fetchInbox(unreadOnly).then(setMessages).catch((e) => setErr(String(e)));
  }
  useEffect(reload, [unreadOnly]);

  async function poll() {
    setPolling(true); setMsg("正在从 Gmail 拉取近 7 天邮件…");
    try {
      const r = await pollReplies();
      setMsg(`拉取完成：回复 ${r.replies} 封、退信 ${r.bounces} 封（邮箱已标无效，不再发送）、退订 ${r.unsubscribes} 家（已停止一切触达）`);
      reload(); onUnreadChange?.();
    } catch (e) { setMsg("拉取失败（需配置 Gmail 授权码）：" + String(e)); }
    finally { setPolling(false); }
  }

  async function toggleOpen(m: InboxMessage) {
    setOpen(open === m.id ? null : m.id);
    if (!m.is_read) {
      try {
        await markInboxRead(m.id);
        setMessages((ms) => ms.map((x) => (x.id === m.id ? { ...x, is_read: 1 } : x)));
        onUnreadChange?.();
      } catch { /* 已读标记失败不打断阅读 */ }
    }
  }

  return (
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <h3 style={{ margin: 0 }}>收件箱（{messages.length}）</h3>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label className="muted" style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />只看未读
          </label>
          <button className="btn btn-sm" onClick={poll} disabled={polling}
            title="拉取 Gmail 近 7 天邮件：客户回复入库、退信自动标无效邮箱、退订自动停发">
            {polling ? "拉取中…" : "↻ 拉取邮件"}
          </button>
        </div>
      </div>
      <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>
        客户回了什么直接在这里看，不用去翻 Gmail。退信自动把邮箱标为无效、退订自动停止一切触达。
      </div>
      {err && <div className="error-text" style={{ marginTop: 8 }}>加载失败：{err}</div>}
      {msg && <div className="muted" style={{ marginTop: 8 }}>{msg}</div>}
      {messages.length === 0 ? (
        <div className="muted" style={{ marginTop: 12 }}>还没有邮件。点「拉取邮件」从 Gmail 同步客户回复。</div>
      ) : (
        <div style={{ marginTop: 10 }}>
          {messages.map((m) => (
            <div key={m.id} className="note-item" style={{ cursor: "pointer", opacity: m.is_read && open !== m.id ? 0.75 : 1 }}
              onClick={() => toggleOpen(m)}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span className={`badge ${KIND_COLOR[m.kind] ?? ""}`}><i />{KIND_LABEL[m.kind] ?? m.kind}</span>
                <strong style={{ fontWeight: m.is_read ? 500 : 700 }}>{m.company_en}</strong>
                {m.country && <span className="muted">{m.country}</span>}
                <span className="muted" style={{ fontSize: 12 }}>{m.subject || "(无主题)"}</span>
                <span className="muted" style={{ marginLeft: "auto", fontSize: 12 }}>{fmtTs(m.received_at)}</span>
              </div>
              {open === m.id && (
                <div style={{ marginTop: 8 }}>
                  <div className="muted" style={{ fontSize: 12 }}>发件人：{m.from_addr}</div>
                  <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 13, margin: "6px 0" }}>{m.body || "(无正文)"}</pre>
                  <button className="btn btn-sm" onClick={(e) => { e.stopPropagation(); onOpenLead(m.lead_no); }}>
                    打开客户详情 →
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
