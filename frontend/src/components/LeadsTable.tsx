import type { Lead } from "../types";

const CHANNELS = [
  { key: "email", label: "Email" },
  { key: "whatsapp", label: "WA" },
  { key: "instagram", label: "IG" },
];

/** Pick the most WhatsApp-likely number out of a free-text phone field. */
export function waNumber(phone: string): string | null {
  const parts = phone.split(/[/;,]/);
  const best = parts.find((p) => /wa/i.test(p)) ?? parts.find((p) => p.includes("+")) ?? parts[0];
  const digits = (best.match(/\d/g) || []).join("");
  return digits.length >= 8 && digits.length <= 15 ? digits : null;
}

function igUrl(handle: string): string {
  const h = handle.replace(/^@/, "");
  return h.includes("instagram.com") ? `https://${h.replace(/^https?:\/\//, "")}` : `https://instagram.com/${h}`;
}

function fbUrl(page: string): string {
  return page.includes("facebook.com") ? `https://${page.replace(/^https?:\/\//, "")}` : `https://facebook.com/${page}`;
}

function channelState(l: Lead, channel: string): "replied" | "messaged" | "untouched" {
  const o = l.outreach.find((x) => x.channel === channel);
  if (!o) return "untouched";
  if (o.status === "replied") return "replied";
  if (o.status === "messaged") return "messaged";
  return "untouched";
}

const STATE_TEXT = { replied: "已回复", messaged: "已触达", untouched: "未触达" } as const;

export function LeadsTable({ leads, selected, onToggle, onToggleAll, onReply }: {
  leads: Lead[]; selected: Set<number>;
  onToggle: (no: number) => void; onToggleAll: (checked: boolean) => void;
  onReply: (no: number, channel: string) => void;
}) {
  const allChecked = leads.length > 0 && leads.every((l) => selected.has(l.no));
  return (
    <div className="table-wrap">
      <table className="table">
        <thead><tr>
          <th><input type="checkbox" checked={allChecked} onChange={(e) => onToggleAll(e.target.checked)} /></th>
          <th>#</th><th>公司</th><th>国家</th><th>城市</th>
          <th>邮箱</th><th>电话 / WhatsApp</th><th>IG</th><th>FB</th><th>渠道状态</th>
        </tr></thead>
        <tbody>
          {leads.map((l) => {
            const wa = l.phone ? waNumber(l.phone) : null;
            return (
              <tr key={l.no}>
                <td><input type="checkbox" checked={selected.has(l.no)} onChange={() => onToggle(l.no)} /></td>
                <td className="num muted">{l.no}</td>
                <td>{l.website
                  ? <a href={`https://${l.website.replace(/^https?:\/\//, "")}`} target="_blank" rel="noreferrer">{l.company_en}</a>
                  : l.company_en}</td>
                <td>{l.country}</td>
                <td>{l.city}</td>
                <td>{l.email ? <a href={`mailto:${l.email}`}>{l.email}</a> : <span className="muted">—</span>}</td>
                <td className="num">{l.phone
                  ? (wa
                    ? <a href={`https://wa.me/${wa}`} target="_blank" rel="noreferrer"
                        title="点击打开 WhatsApp 对话" style={{ color: "var(--green)" }}>
                        {l.phone}{l.whatsapp_verified ? " ✓" : ""}
                      </a>
                    : l.phone)
                  : <span className="muted">—</span>}</td>
                <td>{l.instagram
                  ? <a href={igUrl(l.instagram)} target="_blank" rel="noreferrer">@{l.instagram.replace(/^@/, "")}</a>
                  : <span className="muted">—</span>}</td>
                <td>{l.facebook
                  ? <a href={fbUrl(l.facebook)} target="_blank" rel="noreferrer">{l.facebook.replace(/^https?:\/\/(www\.)?facebook\.com\//, "")}</a>
                  : <span className="muted">—</span>}</td>
                <td>
                  {CHANNELS.map(({ key, label }) => {
                    const st = channelState(l, key);
                    const clickable = st === "messaged";
                    return (
                      <span key={key}
                        className={`badge badge-${st}${clickable ? " clickable" : ""}`}
                        style={{ marginRight: 4 }}
                        onClick={clickable ? () => onReply(l.no, key) : undefined}
                        title={clickable ? `${label} 已触达 — 点击标记为已回复` : `${label} ${STATE_TEXT[st]}`}>
                        <i />{label}
                      </span>
                    );
                  })}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
