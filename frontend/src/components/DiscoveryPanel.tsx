import { useState } from "react";
import { startDiscover, startPageDiscover, fetchDiscoverJob, importLeads } from "../api";
import type { Candidate } from "../types";

const ICP_LABEL: Record<string, string> = {
  rental: "租赁公司", integrator: "AV集成商", reseller: "经销商",
  signage: "标识/广告牌", "end-user": "终端用户",
};

const MARKETS = ["USA", "Canada", "Mexico", "Brazil", "Chile", "Argentina", "Colombia", "Peru",
  "UK", "Germany", "France", "Spain", "Italy", "Netherlands", "Poland",
  "UAE", "Saudi Arabia", "South Korea", "Japan", "Australia", "South Africa",
  "India", "Thailand", "Vietnam", "Indonesia", "Philippines", "Turkey"];

const DEFAULT_QUERIES = `LED video wall installer contact
LED display rental company contact
AV integrator LED screen contact`;

// One click appends a proven angle as an extra search line.
const PRESET_QUERIES = ["LED signage company", "stage production LED screen rental",
  "church AV LED wall", "LED screen distributor", "digital billboard company"];

export function DiscoveryPanel({ onImported }: { onImported: () => void }) {
  const [mode, setMode] = useState<"search" | "page">("search");
  const [query, setQuery] = useState(DEFAULT_QUERIES);
  const [url, setUrl] = useState("");
  const [country, setCountry] = useState("USA");
  const [cands, setCands] = useState<Candidate[]>([]);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const queryLines = query.split("\n").map((l) => l.trim()).filter(Boolean);

  async function run() {
    if (mode === "page" && !url.trim()) { setMsg("请粘贴名录/经销商页 URL"); return; }
    if (mode === "search" && queryLines.length === 0) { setMsg("请至少填一行搜索关键词"); return; }
    setBusy(true); setMsg(mode === "page" ? "抓取名录中…" : "搜索深挖中…"); setCands([]); setPicked(new Set());
    try {
      // 每行一条搜索；选了国家自动拼进关键词，结果按域名合并去重
      const composed = queryLines.map((l) => (country.trim() ? `${l} ${country.trim()}` : l));
      const { job_id } = mode === "page" ? await startPageDiscover(url.trim(), 40) : await startDiscover(composed, 10);
      const poll = setInterval(async () => {
        const j = await fetchDiscoverJob(job_id);
        setMsg(`进度 ${j.done}/${j.total}`);
        if (j.status !== "running") {
          clearInterval(poll); setBusy(false);
          if (j.result && "candidates" in j.result) {
            setCands(j.result.candidates);
            setPicked(new Set(j.result.candidates
              .filter((c) => !c.duplicate_of && (c.email || c.phone || c.instagram))
              .map((c) => c.domain)));
            setMsg(`找到 ${j.result.candidates.length} 个候选`);
          } else if (j.result && "error" in j.result) {
            setMsg("失败：" + j.result.error);
          }
        }
      }, 2000);
    } catch (e) { setBusy(false); setMsg("失败：" + String(e)); }
  }

  async function doImport() {
    const chosen = cands.filter((c) => picked.has(c.domain));
    if (chosen.length === 0) { setMsg("请先勾选要导入的候选"); return; }
    try {
      const res = await importLeads(country, chosen.map((c) => ({
        company_en: c.title, website: c.domain, email: c.email,
        phone: c.phone, instagram: c.instagram, facebook: c.facebook, linkedin: c.linkedin,
        source: c.source, icp_type: c.icp_type, fit_score: c.fit_score,
      })));
      const skipNote = res.skipped.length
        ? `；${res.skipped.length} 家已在库跳过（${res.skipped.map((s) => `${s.website ?? s.company_en} → #${s.duplicate_of}`).join("、")}）`
        : "";
      setMsg(`已导入 ${res.imported} 家${skipNote}`);
      // 表格状态列同步为已在库，避免误以为没导进去
      const dupMap = new Map(res.skipped.map((s) => [s.website, s.duplicate_of]));
      setCands((cs) => cs.map((c) => (picked.has(c.domain) && !c.duplicate_of
        ? { ...c, duplicate_of: dupMap.get(c.domain) ?? -1 } : c)));
      setPicked(new Set());
      onImported();
    } catch (e) { setMsg("导入失败：" + String(e)); }
  }

  const toggle = (d: string) => setPicked((s) => { const n = new Set(s); if (n.has(d)) { n.delete(d); } else { n.add(d); } return n; });
  const dash = <span className="muted">—</span>;
  return (
    <div className="card">
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        <button className={`btn btn-sm${mode === "search" ? " btn-primary" : ""}`} onClick={() => setMode("search")}>关键词搜索</button>
        <button className={`btn btn-sm${mode === "page" ? " btn-primary" : ""}`} onClick={() => setMode("page")}>名录 / 竞品经销商页</button>
      </div>
      {mode === "search" ? (
        <>
          <h3>搜索深挖：官网自动提取邮箱 / 电话 / WhatsApp / IG / FB</h3>
          <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>
            一行一条搜索，多行会依次跑并按域名合并去重；选了目标国家会自动拼进每条关键词。
          </div>
          <textarea className="input" style={{ width: "100%", height: 74, marginBottom: 6 }}
            value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder={"一行一条，如：\nLED video wall installer contact\nLED display rental company contact"} />
          <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap", alignItems: "center" }}>
            <span className="muted" style={{ fontSize: 12 }}>加一条：</span>
            {PRESET_QUERIES.map((p) => (
              <button key={p} className="btn btn-sm" disabled={query.includes(p)}
                onClick={() => setQuery((q) => (q.trim() ? q.trimEnd() + "\n" : "") + p)}>＋{p}</button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap", alignItems: "center" }}>
            <label className="muted" style={{ fontSize: 13 }}>目标国家</label>
            <input className="input" list="market-list" style={{ width: 150 }} value={country}
              onChange={(e) => setCountry(e.target.value)} placeholder="选择或输入国家" />
            <datalist id="market-list">
              {MARKETS.map((m) => <option key={m} value={m} />)}
            </datalist>
            <button className="btn btn-primary" onClick={run} disabled={busy}>
              {busy ? "搜索中…" : `搜索深挖（${queryLines.length} 条）`}
            </button>
          </div>
        </>
      ) : (
        <>
          <h3>从名录 / 竞品经销商页批量挖客户</h3>
          <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
            粘贴一个「列出很多公司」的页面 URL —— 竞品的 where-to-buy / distributors 页（如 Absen、Leyard 经销商列表），或展会参展商名录（ISE / InfoComm / LED China）。系统会抓出页面里的公司域名，逐个深挖联系方式。这些是 LED 行业最精准的现成买家池。
          </div>
          <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
            <input className="input" style={{ flex: 1, minWidth: 260 }} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…  经销商页 / 参展商名录 URL" />
            <input className="input" style={{ width: 90 }} value={country} onChange={(e) => setCountry(e.target.value)} placeholder="国家" />
            <button className="btn btn-primary" onClick={run} disabled={busy}>{busy ? "抓取中…" : "抓取名录"}</button>
          </div>
        </>
      )}
      {msg && <div className="muted" style={{ marginBottom: 10 }}>{msg}</div>}
      {cands.length > 0 && (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead><tr>
                <th></th><th>网站</th><th>类型</th><th>邮箱</th><th>电话 / WhatsApp</th><th>IG</th><th>FB</th><th>状态</th>
              </tr></thead>
              <tbody>
                {cands.map((c) => (
                  <tr key={c.domain}>
                    <td><input type="checkbox" disabled={!!c.duplicate_of} checked={picked.has(c.domain)} onChange={() => toggle(c.domain)} /></td>
                    <td><a href={`https://${c.domain}`} target="_blank" rel="noreferrer">{c.domain}</a></td>
                    <td>{c.icp_type && c.icp_type !== "unknown"
                      ? <span title={`契合分 ${c.fit_score}`}>{ICP_LABEL[c.icp_type] ?? c.icp_type} <span className="muted">{c.fit_score}</span></span>
                      : dash}</td>
                    <td>{c.email || dash}</td>
                    <td className="num">{c.phone
                      ? <a href={`https://wa.me/${c.phone.replace(/\D/g, "")}`} target="_blank" rel="noreferrer" style={{ color: "var(--green)" }}>{c.phone}</a>
                      : dash}</td>
                    <td>{c.instagram
                      ? <a href={`https://instagram.com/${c.instagram}`} target="_blank" rel="noreferrer">@{c.instagram}</a>
                      : dash}</td>
                    <td>{c.facebook
                      ? <a href={`https://facebook.com/${c.facebook}`} target="_blank" rel="noreferrer">{c.facebook}</a>
                      : dash}</td>
                    <td>{c.duplicate_of === -1
                      ? <span style={{ color: "var(--green)" }}>已导入 ✓</span>
                      : c.duplicate_of
                        ? <span className="warn-text">已在库 #{c.duplicate_of}</span>
                        : <span style={{ color: "var(--green)" }}>新</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="btn btn-green" style={{ marginTop: 10 }} onClick={doImport}>
            导入选中（{picked.size}）
          </button>
        </>
      )}
    </div>
  );
}
