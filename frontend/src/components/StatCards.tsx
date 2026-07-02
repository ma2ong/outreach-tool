import type { Stats } from "../types";

export function StatCards({ stats }: { stats: Stats }) {
  const email = stats.by_channel_status.email ?? {};
  const ig = stats.by_channel_status.instagram ?? {};
  const wa = stats.by_channel_status.whatsapp ?? {};
  const card = (label: string, value: number | string) => (
    <div style={{ background: "#1e2733", color: "#e6edf3", padding: 16, borderRadius: 8, minWidth: 140 }}>
      <div style={{ fontSize: 13, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 700 }}>{value}</div>
    </div>
  );
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
      {card("客户总数", stats.total)}
      {card("Email 已发", email.messaged ?? 0)}
      {card("IG 已发", ig.messaged ?? 0)}
      {card("WhatsApp 已发", wa.messaged ?? 0)}
      {card("国家数", Object.keys(stats.by_country).length)}
    </div>
  );
}
