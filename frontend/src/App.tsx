import { useEffect, useState } from "react";
import { fetchLeads, fetchStats } from "./api";
import type { Lead, Stats } from "./types";
import { StatCards } from "./components/StatCards";
import { LeadsTable } from "./components/LeadsTable";
import { OutreachPanel } from "./components/OutreachPanel";
import { DiscoveryPanel } from "./components/DiscoveryPanel";

export function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [country, setCountry] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [err, setErr] = useState("");

  function reload() {
    fetchStats().then(setStats).catch((e) => setErr(String(e)));
    fetchLeads({ country, search }).then(setLeads).catch((e) => setErr(String(e)));
  }
  useEffect(() => { fetchStats().then(setStats).catch((e) => setErr(String(e))); }, []);
  useEffect(() => { fetchLeads({ country, search }).then(setLeads).catch((e) => setErr(String(e))); }, [country, search]);

  const toggle = (no: number) => setSelected((s) => { const n = new Set(s); if (n.has(no)) { n.delete(no); } else { n.add(no); } return n; });
  const toggleAll = (checked: boolean) => setSelected(checked ? new Set(leads.map((l) => l.no)) : new Set());

  const input = { background: "#0d1117", color: "#e6edf3", border: "1px solid #30363d", borderRadius: 6, padding: "6px 10px" };
  return (
    <div style={{ fontFamily: "system-ui, sans-serif", background: "#0d1117", minHeight: "100vh", padding: 24 }}>
      <h1 style={{ color: "#e6edf3" }}>客户开发看板</h1>
      {err && <div style={{ color: "#f85149" }}>加载失败：{err}</div>}
      {stats && <StatCards stats={stats} />}
      <DiscoveryPanel onImported={reload} />
      <OutreachPanel selected={[...selected]} onDone={reload} />
      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <select style={input} value={country} onChange={(e) => setCountry(e.target.value)}>
          <option value="">全部国家</option>
          {stats && Object.keys(stats.by_country).sort().map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <input style={input} placeholder="搜索公司/网站/城市" value={search} onChange={(e) => setSearch(e.target.value)} />
        <span style={{ color: "#8b949e", alignSelf: "center" }}>{leads.length} 条 · 已选 {selected.size}</span>
      </div>
      <LeadsTable leads={leads} selected={selected} onToggle={toggle} onToggleAll={toggleAll} />
    </div>
  );
}
