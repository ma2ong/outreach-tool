import { useEffect, useState } from "react";
import { fetchLeadsPage, fetchStats, markReplied } from "./api";
import type { Lead, Stats } from "./types";
import { Dashboard } from "./components/Dashboard";
import { LeadsTable } from "./components/LeadsTable";
import { LeadDrawer } from "./components/LeadDrawer";
import { OutreachPanel } from "./components/OutreachPanel";
import { DiscoveryPanel } from "./components/DiscoveryPanel";
import { ConnectionPanel } from "./components/ConnectionPanel";

type Page = "dashboard" | "leads" | "discovery" | "channels";

function exportQuery(params: Record<string, string>): string {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
  return qs ? "&" + qs : "";
}

const PAGES: { id: Page; label: string; ico: string }[] = [
  { id: "dashboard", label: "仪表盘", ico: "▦" },
  { id: "leads", label: "客户库", ico: "☰" },
  { id: "discovery", label: "客户开发", ico: "⌕" },
  { id: "channels", label: "渠道连接", ico: "⇄" },
];

function useTheme(): [string, () => void] {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);
  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

export function App() {
  const [page, setPage] = useState<Page>("leads");
  const [theme, toggleTheme] = useTheme();
  const [stats, setStats] = useState<Stats | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [country, setCountry] = useState("");
  const [channel, setChannel] = useState("");
  const [status, setStatus] = useState("");
  const [has, setHas] = useState("");
  const [followUp, setFollowUp] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("no");
  const [order, setOrder] = useState("asc");
  const [leadPage, setLeadPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [detail, setDetail] = useState<Lead | null>(null);
  const [err, setErr] = useState("");

  const PAGE_SIZE = 50;

  function loadLeads() {
    fetchLeadsPage({ country, channel, status, search, has, follow_up: followUp,
      sort, order, limit: String(PAGE_SIZE), offset: String(leadPage * PAGE_SIZE) })
      .then(({ leads, total }) => { setLeads(leads); setTotal(total); })
      .catch((e) => setErr(String(e)));
  }
  function reload() {
    fetchStats().then(setStats).catch((e) => setErr(String(e)));
    loadLeads();
  }
  useEffect(() => { fetchStats().then(setStats).catch((e) => setErr(String(e))); }, []);
  useEffect(loadLeads, [country, channel, status, search, has, followUp, sort, order, leadPage]);

  // Reset to first page whenever a filter/sort changes so offset stays valid.
  const filterReset = () => setLeadPage(0);
  function sortBy(col: string) {
    if (sort === col) { setOrder(order === "asc" ? "desc" : "asc"); }
    else { setSort(col); setOrder("asc"); }
    filterReset();
  }

  async function reply(no: number, channel: string) {
    try { await markReplied(no, channel); reload(); } catch (e) { setErr(String(e)); }
  }

  const shown = leads;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const toggle = (no: number) => setSelected((s) => { const n = new Set(s); if (n.has(no)) { n.delete(no); } else { n.add(no); } return n; });
  const toggleAll = (checked: boolean) => setSelected(checked ? new Set(shown.map((l) => l.no)) : new Set());

  const title = PAGES.find((p) => p.id === page)!.label;
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="pixel-logo"><i /><i /><i /><i /></span>
          <span>
            <div className="brand-name">Maxcolor</div>
            <div className="brand-sub">客户开发系统</div>
          </span>
        </div>
        {PAGES.map((p) => (
          <button key={p.id} className={`nav-item${page === p.id ? " active" : ""}`} onClick={() => setPage(p.id)}>
            <span className="ico">{p.ico}</span><span className="nav-label">{p.label}</span>
          </button>
        ))}
      </aside>
      <div className="main">
        <header className="topbar">
          <h2>{title}</h2>
          <button className="btn btn-sm" onClick={toggleTheme} title="切换主题">
            {theme === "dark" ? "☀ 浅色" : "☾ 深色"}
          </button>
        </header>
        <div className="content">
          {err && <div className="error-text" style={{ marginBottom: 12 }}>加载失败：{err}</div>}
          {page === "dashboard" && stats && (
            <Dashboard stats={stats} onGotoFollowUp={() => {
              setCountry(""); setChannel(""); setStatus(""); setHas(""); setSearch("");
              setFollowUp("due"); setLeadPage(0); setPage("leads");
            }} />
          )}
          {page === "leads" && (
            <>
              <div className="filter-bar">
                <select className="input" value={country} onChange={(e) => { setCountry(e.target.value); filterReset(); }}>
                  <option value="">全部国家</option>
                  {stats && Object.keys(stats.by_country).sort().map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
                <select className="input" value={channel} onChange={(e) => { setChannel(e.target.value); filterReset(); }}>
                  <option value="">全部渠道</option>
                  <option value="email">Email</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="instagram">Instagram</option>
                </select>
                <select className="input" value={status} onChange={(e) => { setStatus(e.target.value); filterReset(); }}>
                  <option value="">全部状态</option>
                  <option value="untouched">未触达</option>
                  <option value="messaged">已触达</option>
                  <option value="replied">已回复</option>
                </select>
                <select className="input" value={has} onChange={(e) => { setHas(e.target.value); filterReset(); }}>
                  <option value="">全部联系方式</option>
                  <option value="phone">有电话/WA</option>
                  <option value="instagram">有 IG</option>
                  <option value="email">有邮箱</option>
                </select>
                <input className="input" placeholder="搜索公司/网站/城市" value={search} onChange={(e) => { setSearch(e.target.value); filterReset(); }} />
                <button className={`btn btn-sm${followUp === "due" ? " btn-primary" : ""}`}
                  onClick={() => { setFollowUp(followUp === "due" ? "" : "due"); filterReset(); }}
                  title="只看已触达但超过7天没回复、或到跟进日期的客户">
                  待跟进{stats?.funnel?.follow_up_due ? ` ${stats.funnel.follow_up_due}` : ""}
                </button>
                <a className="btn btn-sm"
                  href={`/api/leads/export?fmt=xlsx${exportQuery({ country, channel, status, has, follow_up: followUp, search })}`}
                  title="按当前筛选导出 Excel">⬇ 导出 Excel</a>
                <span className="muted">共 {total} 条 · 已选 {selected.size}</span>
              </div>
              <LeadsTable leads={shown} selected={selected} onToggle={toggle} onToggleAll={toggleAll}
                onReply={reply} onOpen={setDetail} sort={sort} order={order} onSort={sortBy} />
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 12 }}>
                <button className="btn btn-sm" disabled={leadPage <= 0} onClick={() => setLeadPage(leadPage - 1)}>← 上一页</button>
                <span className="muted">第 {leadPage + 1} / {pageCount} 页</span>
                <button className="btn btn-sm" disabled={leadPage + 1 >= pageCount} onClick={() => setLeadPage(leadPage + 1)}>下一页 →</button>
              </div>
              {selected.size > 0 && (
                <div className="action-bar">
                  <OutreachPanel selected={[...selected]} onDone={reload} />
                </div>
              )}
            </>
          )}
          {page === "discovery" && <DiscoveryPanel onImported={reload} />}
          {page === "channels" && <ConnectionPanel />}
        </div>
      </div>
      {detail && (
        <LeadDrawer
          lead={detail}
          onClose={() => setDetail(null)}
          onChange={(u) => { setDetail(u); setLeads((ls) => ls.map((l) => (l.no === u.no ? u : l))); }}
        />
      )}
    </div>
  );
}
