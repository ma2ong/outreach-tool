import { useEffect, useState } from "react";
import { fetchLeadsPage, fetchStats, markReplied, fetchSequences, enrollLeads, startVerify, fetchVerifyJob, startClassify, fetchClassifyJob } from "./api";
import type { Lead, Stats, Sequence } from "./types";
import { Dashboard } from "./components/Dashboard";
import { LeadsTable } from "./components/LeadsTable";
import { LeadDrawer } from "./components/LeadDrawer";
import { OutreachPanel } from "./components/OutreachPanel";
import { DiscoveryPanel } from "./components/DiscoveryPanel";
import { ConnectionPanel } from "./components/ConnectionPanel";
import { MailboxPanel } from "./components/MailboxPanel";
import { SequencesPanel } from "./components/SequencesPanel";

type Page = "dashboard" | "leads" | "sequences" | "discovery" | "channels";

function exportQuery(params: Record<string, string>): string {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
  return qs ? "&" + qs : "";
}

const PAGES: { id: Page; label: string; ico: string }[] = [
  { id: "dashboard", label: "仪表盘", ico: "▦" },
  { id: "leads", label: "客户库", ico: "☰" },
  { id: "sequences", label: "跟进序列", ico: "⇉" },
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
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [enrollMsg, setEnrollMsg] = useState("");
  const [err, setErr] = useState("");

  const PAGE_SIZE = 50;

  useEffect(() => { fetchSequences().then(setSequences).catch(() => {}); }, []);
  async function enroll(sid: number) {
    try {
      const r = await enrollLeads(sid, [...selected]);
      setEnrollMsg(`已把 ${r.enrolled} 家加入序列（${r.selected - r.enrolled} 家已在其中或已回复被跳过）`);
      fetchSequences().then(setSequences).catch(() => {});
    } catch (e) { setEnrollMsg("加入序列失败：" + String(e)); }
  }

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

  const [verifyMsg, setVerifyMsg] = useState("");
  const [verifying, setVerifying] = useState(false);
  async function verifyEmails() {
    setVerifying(true); setVerifyMsg("验证邮箱中（查 MX 记录）…");
    try {
      const scope = selected.size > 0 ? [...selected] : undefined;
      const { job_id } = await startVerify(scope);
      const poll = setInterval(async () => {
        const j = await fetchVerifyJob(job_id);
        if (j.status !== "running") {
          clearInterval(poll); setVerifying(false);
          if (j.result && "checked" in j.result) {
            const r = j.result;
            setVerifyMsg(`已验证 ${r.checked} 个邮箱：有效 ${r.valid}，角色邮箱 ${r.role}，无效 ${r.invalid}（发送时自动跳过），无法判定 ${r.unknown}`);
            reload();
          } else if (j.result && "error" in j.result) { setVerifyMsg("验证失败：" + j.result.error); }
        }
      }, 1500);
    } catch (e) { setVerifying(false); setVerifyMsg("验证失败：" + String(e)); }
  }

  const [classifying, setClassifying] = useState(false);
  async function classifyLeads() {
    setClassifying(true); setVerifyMsg("客户分级中（逐个读官网判断客户类型，较慢）…");
    try {
      const scope = selected.size > 0 ? [...selected] : undefined;
      const { job_id } = await startClassify(scope);
      const poll = setInterval(async () => {
        const j = await fetchClassifyJob(job_id);
        if (j.status === "running") { setVerifyMsg(`客户分级中 ${j.done}${j.total ? "/" + j.total : ""}…`); return; }
        clearInterval(poll); setClassifying(false);
        if (j.result && "checked" in j.result) {
          const types = Object.entries(j.result.by_type).map(([t, n]) => `${t} ${n}`).join("，");
          setVerifyMsg(`已分级 ${j.result.checked} 家：${types || "未识别出类型"}。按"客户类型"列排序可优先打高价值客户。`);
          reload();
        } else if (j.result && "error" in j.result) { setVerifyMsg("分级失败：" + j.result.error); }
      }, 2000);
    } catch (e) { setClassifying(false); setVerifyMsg("分级失败：" + String(e)); }
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
                <button className="btn btn-sm" onClick={verifyEmails} disabled={verifying}
                  title="查 MX 记录验证邮箱有效性，无效邮箱发送时自动跳过（降 bounce 保送达）。勾选客户则只验证选中的，否则验证全部。">
                  {verifying ? "验证中…" : selected.size > 0 ? `✓ 验证选中邮箱` : "✓ 验证全部邮箱"}
                </button>
                <button className="btn btn-sm" onClick={classifyLeads} disabled={classifying}
                  title="读官网内容自动判断客户类型（租赁/集成商/经销商/标识厂/终端）+ 契合分，写入客户类型列。勾选客户则只分级选中的。">
                  {classifying ? "分级中…" : selected.size > 0 ? "★ 分级选中客户" : "★ 分级全部客户"}
                </button>
                <span className="muted">共 {total} 条 · 已选 {selected.size}</span>
              </div>
              {verifyMsg && <div className="muted" style={{ marginBottom: 8 }}>{verifyMsg}</div>}
              <LeadsTable leads={shown} selected={selected} onToggle={toggle} onToggleAll={toggleAll}
                onReply={reply} onOpen={setDetail} sort={sort} order={order} onSort={sortBy} />
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 12 }}>
                <button className="btn btn-sm" disabled={leadPage <= 0} onClick={() => setLeadPage(leadPage - 1)}>← 上一页</button>
                <span className="muted">第 {leadPage + 1} / {pageCount} 页</span>
                <button className="btn btn-sm" disabled={leadPage + 1 >= pageCount} onClick={() => setLeadPage(leadPage + 1)}>下一页 →</button>
              </div>
              {selected.size > 0 && (
                <div className="action-bar">
                  {sequences.length > 0 && (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
                      <span className="muted" style={{ fontSize: 13 }}>把已选 {selected.size} 家加入序列：</span>
                      <select className="input" value="" onChange={(e) => { if (e.target.value) enroll(Number(e.target.value)); }}>
                        <option value="">选择一个序列…</option>
                        {sequences.map((s) => <option key={s.id} value={s.id}>{s.name}（{s.channel}）</option>)}
                      </select>
                      {enrollMsg && <span className="muted">{enrollMsg}</span>}
                    </div>
                  )}
                  <OutreachPanel selected={[...selected]} onDone={reload} />
                </div>
              )}
            </>
          )}
          {page === "sequences" && <SequencesPanel onChanged={reload} />}
          {page === "discovery" && <DiscoveryPanel onImported={reload} />}
          {page === "channels" && <><ConnectionPanel /><MailboxPanel /></>}
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
