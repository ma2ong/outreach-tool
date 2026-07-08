import { useEffect, useState } from "react";
import { fetchQuota } from "../api";
import type { Stats, ChannelReach } from "../types";
import { StatCards } from "./StatCards";

const CH_LABEL: Record<string, string> = { email: "Email", whatsapp: "WhatsApp", instagram: "Instagram" };

function ReachRow({ channel, r }: { channel: string; r: ChannelReach }) {
  const base = Math.max(r.have, 1);
  const messagedOnly = r.messaged - r.replied;
  const pct = (v: number) => `${(v / base) * 100}%`;
  return (
    <div className="reach-row">
      <span className="ch-name">{CH_LABEL[channel] ?? channel}</span>
      <div className="reach-track" title={`可发 ${r.have}｜已触达 ${r.messaged}｜已回复 ${r.replied}｜未触达可发 ${r.untouched}`}>
        {r.replied > 0 && <div style={{ width: pct(r.replied), background: "var(--green)" }} />}
        {messagedOnly > 0 && <div style={{ width: pct(messagedOnly), background: "var(--blue)" }} />}
        {r.untouched > 0 && <div style={{ width: pct(r.untouched), background: "var(--warn)" }} />}
      </div>
      <span className="reach-meta">可发 {r.have} · 已发 {r.messaged} · 还可发 <b>{r.untouched}</b></span>
    </div>
  );
}

export function Dashboard({ stats }: { stats: Stats }) {
  const [quota, setQuota] = useState<Record<string, { sent_today: number; cap: number }>>({});
  useEffect(() => { fetchQuota().then(setQuota).catch(() => {}); }, []);

  const f = stats.funnel;
  const funnelBase = Math.max(f?.total ?? stats.total, 1);
  const stages = [
    { label: "客户总数", value: f?.total ?? stats.total },
    { label: "有联系方式", value: f?.with_contact ?? 0 },
    { label: "已触达", value: f?.touched ?? 0 },
    { label: "已回复", value: f?.replied ?? 0 },
  ];

  const countries = Object.entries(stats.by_country).sort((a, b) => b[1] - a[1]).slice(0, 15);
  const maxC = countries[0]?.[1] ?? 1;
  return (
    <>
      <StatCards stats={stats} />
      <div className="cards-row">
        {Object.entries(quota).map(([ch, q]) => (
          <div key={ch} className="card stat-card">
            <div className="stat-label">今日 {ch === "whatsapp" ? "WhatsApp" : "Instagram"} 额度</div>
            <div className="stat-value">{q.sent_today}<span className="muted" style={{ fontSize: 15 }}> / {q.cap}</span></div>
            {q.sent_today >= q.cap && <div className="warn-text">已到日上限，明天再发</div>}
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>触达漏斗</h3>
        <div className="funnel-grid">
          {stages.map((s, i) => {
            const pct = Math.round((s.value / funnelBase) * 100);
            return (
              <div key={s.label} className="funnel-tile">
                <div className="stat-label">{s.label}</div>
                <div className="stat-value">{s.value}</div>
                <div className="muted" style={{ fontSize: 12 }}>{i === 0 ? "100%" : `${pct}% of 总数`}</div>
                <div className="funnel-track"><div className="funnel-bar" style={{ width: `${pct}%`, marginTop: 0 }} /></div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>渠道可发覆盖</h3>
        {["whatsapp", "email", "instagram"].map((ch) =>
          stats.reach?.[ch] ? <ReachRow key={ch} channel={ch} r={stats.reach[ch]} /> : null)}
        <div className="reach-legend">
          <span><i style={{ background: "var(--green)" }} />已回复</span>
          <span><i style={{ background: "var(--blue)" }} />已触达（未回复）</span>
          <span><i style={{ background: "var(--warn)" }} />未触达可发</span>
          <span><i style={{ background: "var(--surface-2)" }} />无此联系方式</span>
        </div>
        <div className="muted" style={{ fontSize: 12 }}>
          条形长度 = 有该联系方式的客户数；灰色轨道剩余部分为已排除/无联系方式。「还可发」是当前该渠道能立即发送的客户数。
        </div>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        <h3>国家分布（前 15）</h3>
        {countries.map(([c, n]) => (
          <div key={c} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ width: 110, flex: "none" }}>{c}</span>
            <div style={{ flex: 1, background: "var(--surface-2)", borderRadius: 4, height: 14 }}>
              <div style={{ width: `${(n / maxC) * 100}%`, background: "var(--accent)", borderRadius: 4, height: 14 }} />
            </div>
            <span className="num muted" style={{ width: 40, textAlign: "right" }}>{n}</span>
          </div>
        ))}
      </div>
    </>
  );
}
