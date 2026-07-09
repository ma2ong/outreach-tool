import { useEffect, useState } from "react";
import { updateLead, addNote } from "../api";
import type { Lead } from "../types";
import { STAGES, STAGE_LABEL } from "../types";

const CH_LABEL: Record<string, string> = { email: "Email", whatsapp: "WhatsApp", instagram: "Instagram" };
const STATE_TEXT: Record<string, string> = { replied: "已回复", messaged: "已触达" };

function fmtTs(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(+d) ? iso : d.toLocaleString();
}

export function LeadDrawer({ lead, onClose, onChange }: {
  lead: Lead; onClose: () => void; onChange: (l: Lead) => void;
}) {
  const [draft, setDraft] = useState<Lead>(lead);
  const [note, setNote] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => { setDraft(lead); setDirty(false); }, [lead.no]);

  const set = (k: keyof Lead, v: string) => { setDraft((d) => ({ ...d, [k]: v })); setDirty(true); };

  async function save() {
    setSaving(true); setErr("");
    try {
      const updated = await updateLead(lead.no, {
        company_en: draft.company_en, country: draft.country, city: draft.city,
        contact_name: draft.contact_name, email: draft.email, phone: draft.phone,
        website: draft.website, instagram: draft.instagram, facebook: draft.facebook,
        linkedin: draft.linkedin, business: draft.business, stage: draft.stage,
        tags: draft.tags, follow_up_date: draft.follow_up_date, next_action: draft.next_action,
      });
      setDraft(updated); setDirty(false); onChange(updated);
    } catch (e) { setErr(String(e)); } finally { setSaving(false); }
  }

  async function saveStage(stage: string) {
    setDraft((d) => ({ ...d, stage }));
    try { const u = await updateLead(lead.no, { stage }); onChange(u); }
    catch (e) { setErr(String(e)); }
  }

  async function submitNote() {
    const t = note.trim();
    if (!t) return;
    try { const u = await addNote(lead.no, t); setDraft(u); setNote(""); onChange(u); }
    catch (e) { setErr(String(e)); }
  }

  const field = (k: keyof Lead, label: string, type = "text") => (
    <div className="field">
      <label>{label}</label>
      <input className="input" type={type} value={(draft[k] as string) ?? ""} onChange={(e) => set(k, e.target.value)} />
    </div>
  );
  const tags = (draft.tags ?? "").split(",").map((t) => t.trim()).filter(Boolean);

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <button className="drawer-close" onClick={onClose} title="关闭">×</button>
        <h2>{draft.company_en}</h2>
        <div className="muted" style={{ marginBottom: 12 }}>#{lead.no} · {draft.country}{draft.city ? ` · ${draft.city}` : ""}</div>

        <div className="field">
          <label>销售阶段</label>
          <select className="input" value={draft.stage} onChange={(e) => saveStage(e.target.value)}>
            {STAGES.map((s) => <option key={s} value={s}>{STAGE_LABEL[s]}</option>)}
          </select>
        </div>

        <div className="field-grid">
          {field("follow_up_date", "下次跟进日期", "date")}
          {field("next_action", "下一步动作")}
        </div>
        <div className="field">
          <label>标签（逗号分隔，如 hot,distributor,大项目）</label>
          <input className="input" value={draft.tags ?? ""} onChange={(e) => set("tags", e.target.value)} placeholder="hot, 经销商, 租赁" />
          {tags.length > 0 && <div style={{ marginTop: 5 }}>{tags.map((t) => <span key={t} className="tag-chip">{t}</span>)}</div>}
        </div>

        <div className="section-title">联系方式</div>
        <div className="field-grid">
          {field("email", "邮箱")}
          {field("phone", "电话 / WhatsApp")}
          {field("website", "官网")}
          {field("contact_name", "联系人")}
          {field("instagram", "Instagram")}
          {field("facebook", "Facebook")}
          {field("linkedin", "LinkedIn")}
        </div>
        <div className="field-grid">
          {field("company_en", "公司名")}
          {field("country", "国家")}
          {field("city", "城市")}
        </div>
        <div className="field">
          <label>业务描述</label>
          <textarea className="input" style={{ height: 64 }} value={draft.business ?? ""} onChange={(e) => set("business", e.target.value)} />
        </div>

        <button className="btn btn-primary" onClick={save} disabled={!dirty || saving}>
          {saving ? "保存中…" : dirty ? "保存修改" : "已保存"}
        </button>
        {err && <span className="error-text" style={{ marginLeft: 10 }}>{err}</span>}

        <div className="section-title">触达状态</div>
        {draft.outreach.length === 0 ? <div className="muted">尚未触达</div> :
          draft.outreach.map((o) => (
            <span key={o.channel} className={`badge badge-${o.status === "replied" ? "replied" : o.status === "messaged" ? "messaged" : "untouched"}`} style={{ marginRight: 6 }}>
              <i />{CH_LABEL[o.channel] ?? o.channel}：{STATE_TEXT[o.status] ?? o.status}
              {o.message_sent_date ? ` (${o.message_sent_date})` : ""}
            </span>
          ))}

        <div className="section-title">跟进记录</div>
        <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
          <input className="input" style={{ flex: 1 }} value={note} placeholder="加一条跟进，如：打了电话，要 P2.5 报价"
            onChange={(e) => setNote(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") submitNote(); }} />
          <button className="btn btn-sm" onClick={submitNote}>添加</button>
        </div>
        {draft.notes.length === 0 ? <div className="muted">还没有跟进记录</div> :
          draft.notes.map((n) => (
            <div key={n.id} className="note-item">
              <div className="ts">{fmtTs(n.created_at)}</div>
              <div>{n.text}</div>
            </div>
          ))}
      </div>
    </div>
  );
}
