import type { Lead } from "../types";

export function LeadsTable({ leads, selected, onToggle, onToggleAll, onReply }: {
  leads: Lead[]; selected: Set<number>;
  onToggle: (no: number) => void; onToggleAll: (checked: boolean) => void;
  onReply: (no: number, channel: string) => void;
}) {
  const th = { textAlign: "left" as const, padding: "8px 10px", borderBottom: "2px solid #30363d", position: "sticky" as const, top: 0, background: "#0d1117" };
  const td = { padding: "8px 10px", borderBottom: "1px solid #21262d" };
  const allChecked = leads.length > 0 && leads.every((l) => selected.has(l.no));
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", color: "#e6edf3", fontSize: 14 }}>
      <thead><tr>
        <th style={th}><input type="checkbox" checked={allChecked} onChange={(e) => onToggleAll(e.target.checked)} /></th>
        <th style={th}>#</th><th style={th}>公司</th><th style={th}>国家</th>
        <th style={th}>城市</th><th style={th}>Email</th><th style={th}>渠道状态</th>
      </tr></thead>
      <tbody>
        {leads.map((l) => (
          <tr key={l.no}>
            <td style={td}><input type="checkbox" checked={selected.has(l.no)} onChange={() => onToggle(l.no)} /></td>
            <td style={td}>{l.no}</td>
            <td style={td}>{l.website ? <a href={`https://${l.website}`} target="_blank" rel="noreferrer" style={{ color: "#58a6ff" }}>{l.company_en}</a> : l.company_en}</td>
            <td style={td}>{l.country}</td>
            <td style={td}>{l.city}</td>
            <td style={td}>{l.email}</td>
            <td style={td}>{l.outreach.map((o) => (
              <span key={o.channel}
                onClick={o.status === "messaged" ? () => onReply(l.no, o.channel) : undefined}
                title={o.status === "messaged" ? "点击标记为已回复" : undefined}
                style={{
                  display: "inline-block", marginRight: 6, padding: "1px 8px", borderRadius: 10, fontSize: 12,
                  background: o.status === "replied" ? "#1a4d2e" : "#21262d",
                  color: o.status === "replied" ? "#3fb950" : "#e6edf3",
                  cursor: o.status === "messaged" ? "pointer" : "default",
                }}>
                {o.channel}:{o.status === "replied" ? "已回复" : o.status}
              </span>
            ))}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
