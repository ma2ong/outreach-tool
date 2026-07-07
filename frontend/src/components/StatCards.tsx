import type { Stats } from "../types";

export function StatCards({ stats }: { stats: Stats }) {
  const email = stats.by_channel_status.email ?? {};
  const ig = stats.by_channel_status.instagram ?? {};
  const wa = stats.by_channel_status.whatsapp ?? {};
  const replied = (email.replied ?? 0) + (ig.replied ?? 0) + (wa.replied ?? 0);
  const card = (label: string, value: number | string) => (
    <div className="card stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
  return (
    <div className="cards-row">
      {card("客户总数", stats.total)}
      {card("Email 已发", email.messaged ?? 0)}
      {card("WhatsApp 已发", wa.messaged ?? 0)}
      {card("IG 已发", ig.messaged ?? 0)}
      {card("已回复", replied)}
      {card("国家数", Object.keys(stats.by_country).length)}
    </div>
  );
}
