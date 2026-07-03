import { useState } from "react";
import { startDiscover, fetchDiscoverJob, importLeads } from "../api";
import type { Candidate } from "../types";

export function DiscoveryPanel({ onImported }: { onImported: () => void }) {
  const [query, setQuery] = useState("LED video wall installer AV integrator USA contact");
  const [country, setCountry] = useState("USA");
  const [cands, setCands] = useState<Candidate[]>([]);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function run() {
    setBusy(true); setMsg("搜索深挖中…"); setCands([]); setPicked(new Set());
    try {
      const { job_id } = await startDiscover(query, 10);
      const poll = setInterval(async () => {
        const j = await fetchDiscoverJob(job_id);
        setMsg(`进度 ${j.done}/${j.total}`);
        if (j.status !== "running") {
          clearInterval(poll); setBusy(false);
          if (j.result && "candidates" in j.result) {
            setCands(j.result.candidates);
            setPicked(new Set(j.result.candidates.filter((c) => !c.duplicate_of && c.email).map((c) => c.domain)));
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
    const res = await importLeads(country, chosen.map((c) => ({ company_en: c.title, website: c.domain, email: c.email })));
    setMsg(`已导入 ${res.imported} 家`); onImported();
  }

  const box = { background: "#0d1117", color: "#e6edf3", border: "1px solid #30363d", borderRadius: 6, padding: "6px 10px" };
  const toggle = (d: string) => setPicked((s) => { const n = new Set(s); if (n.has(d)) { n.delete(d); } else { n.add(d); } return n; });
  return (
    <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 16, marginBottom: 20 }}>
      <h3 style={{ color: "#e6edf3", marginTop: 0 }}>客户开发（搜索 + 深挖 + 入库）</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input style={{ ...box, flex: 1 }} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="关键词，如 LED video wall installer Texas" />
        <input style={{ ...box, width: 90 }} value={country} onChange={(e) => setCountry(e.target.value)} placeholder="国家" />
        <button onClick={run} disabled={busy} style={{ background: busy ? "#30363d" : "#1f6feb", color: "#fff", border: "none", borderRadius: 6, padding: "6px 16px" }}>
          {busy ? "搜索中…" : "搜索深挖"}
        </button>
      </div>
      {msg && <div style={{ color: "#8b949e", marginBottom: 8 }}>{msg}</div>}
      {cands.length > 0 && (
        <>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#e6edf3", fontSize: 13 }}>
            <thead><tr>
              <th></th><th style={{ textAlign: "left", padding: 6 }}>网站</th>
              <th style={{ textAlign: "left", padding: 6 }}>邮箱</th><th style={{ textAlign: "left", padding: 6 }}>状态</th>
            </tr></thead>
            <tbody>
              {cands.map((c) => (
                <tr key={c.domain}>
                  <td style={{ padding: 6 }}><input type="checkbox" disabled={!!c.duplicate_of} checked={picked.has(c.domain)} onChange={() => toggle(c.domain)} /></td>
                  <td style={{ padding: 6 }}><a href={`https://${c.domain}`} target="_blank" rel="noreferrer" style={{ color: "#58a6ff" }}>{c.domain}</a></td>
                  <td style={{ padding: 6 }}>{c.email || <span style={{ color: "#8b949e" }}>—</span>}</td>
                  <td style={{ padding: 6 }}>{c.duplicate_of ? <span style={{ color: "#d29922" }}>已在库 #{c.duplicate_of}</span> : <span style={{ color: "#3fb950" }}>新</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={doImport} style={{ marginTop: 10, background: "#238636", color: "#fff", border: "none", borderRadius: 6, padding: "8px 18px" }}>
            导入选中（{picked.size}）
          </button>
        </>
      )}
    </div>
  );
}
