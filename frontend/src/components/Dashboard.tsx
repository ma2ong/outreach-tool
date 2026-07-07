import { useEffect, useState } from "react";
import { fetchQuota } from "../api";
import type { Stats } from "../types";
import { StatCards } from "./StatCards";

export function Dashboard({ stats }: { stats: Stats }) {
  const [quota, setQuota] = useState<Record<string, { sent_today: number; cap: number }>>({});
  useEffect(() => { fetchQuota().then(setQuota).catch(() => {}); }, []);

  const countries = Object.entries(stats.by_country).sort((a, b) => b[1] - a[1]).slice(0, 15);
  const max = countries[0]?.[1] ?? 1;
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
      <div className="card" style={{ maxWidth: 560 }}>
        <h3>国家分布（前 15）</h3>
        {countries.map(([c, n]) => (
          <div key={c} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ width: 110, flex: "none" }}>{c}</span>
            <div style={{ flex: 1, background: "var(--surface-2)", borderRadius: 4, height: 14 }}>
              <div style={{ width: `${(n / max) * 100}%`, background: "var(--accent)", borderRadius: 4, height: 14 }} />
            </div>
            <span className="num muted" style={{ width: 40, textAlign: "right" }}>{n}</span>
          </div>
        ))}
      </div>
    </>
  );
}
