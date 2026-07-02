import type { Lead } from "../types";

export function LeadsTable({ leads }: { leads: Lead[] }) {
  const th = { textAlign: "left" as const, padding: "8px 10px", borderBottom: "2px solid #30363d", position: "sticky" as const, top: 0, background: "#0d1117" };
  const td = { padding: "8px 10px", borderBottom: "1px solid #21262d" };
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", color: "#e6edf3", fontSize: 14 }}>
      <thead><tr>
        <th style={th}>#</th><th style={th}>公司</th><th style={th}>国家</th>
        <th style={th}>城市</th><th style={th}>Email</th><th style={th}>渠道状态</th>
      </tr></thead>
      <tbody>
        {leads.map((l) => (
          <tr key={l.no}>
            <td style={td}>{l.no}</td>
            <td style={td}>{l.website ? <a href={`https://${l.website}`} target="_blank" rel="noreferrer" style={{ color: "#58a6ff" }}>{l.company_en}</a> : l.company_en}</td>
            <td style={td}>{l.country}</td>
            <td style={td}>{l.city}</td>
            <td style={td}>{l.email}</td>
            <td style={td}>{l.outreach.map((o) => `${o.channel}:${o.status}`).join(", ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
