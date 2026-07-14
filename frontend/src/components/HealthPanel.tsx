import { useState } from "react";
import { scanHealth, fixHealth, type HealthLead } from "../api";

const ISSUE_META: Record<string, { title: string; hint: string; fixable: boolean; fixLabel?: string }> = {
  peer: { title: "同行 / 供应商", hint: "中国·港台 LED 厂（+86 电话或 .cn 域名）——发给他们纯浪费额度", fixable: true, fixLabel: "标为不再联系" },
  directory: { title: "B2B 目录站 / 平台", hint: "alibaba、tradekey 这类平台，不是买家", fixable: true, fixLabel: "标为不再联系" },
  stale_stage: { title: "阶段没跟上", hint: "已经发过消息，销售阶段却还停在「新客户」", fixable: true, fixLabel: "推进到「已联系」" },
  no_contact: { title: "没有任何联系方式", hint: "邮箱/电话/IG/FB 全空——留着占位，永远发不出去。建议手动删或补资料", fixable: false },
  junk_name: { title: "公司名可疑", hint: "抓成了 Contact / Home 这种网页标题，发信开头会很怪，建议打开改名", fixable: false },
};

export function HealthPanel({ onFixed }: { onFixed: () => void }) {
  const [issues, setIssues] = useState<Record<string, HealthLead[]> | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function scan() {
    setBusy(true); setMsg("体检中…");
    try {
      const r = await scanHealth();
      setIssues(r.issues);
      setMsg(r.total === 0 ? "客户库很干净，没发现问题 ✓" : `发现 ${r.total} 处问题`);
    } catch (e) { setMsg("体检失败：" + String(e)); }
    finally { setBusy(false); }
  }

  async function fix(key: string) {
    setBusy(true);
    try {
      const done = await fixHealth([key]);
      setMsg(`已处理 ${Object.values(done).reduce((a, b) => a + b, 0)} 条`);
      await scan();
      onFixed();
    } catch (e) { setMsg("处理失败：" + String(e)); }
    finally { setBusy(false); }
  }

  const keys = issues ? Object.keys(issues).filter((k) => issues[k].length) : [];
  return (
    <div className="card" style={{ marginBottom: 10, padding: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <button className="btn btn-sm btn-primary" onClick={scan} disabled={busy}>
          {busy ? "体检中…" : "🩺 开始体检"}
        </button>
        <span className="muted" style={{ fontSize: 12 }}>
          查出正在浪费你触达额度的数据：混进来的同行、B2B 平台、没联系方式的空客户、抓错的公司名
        </span>
        {msg && <span className="muted" style={{ fontSize: 12 }}>{msg}</span>}
      </div>
      {keys.length > 0 && (
        <div style={{ marginTop: 10 }}>
          {keys.map((k) => {
            const meta = ISSUE_META[k] ?? { title: k, hint: "", fixable: false };
            const list = issues![k];
            return (
              <div key={k} className="note-item">
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <strong>{meta.title}</strong>
                  <span className="warn-text">{list.length} 条</span>
                  {meta.fixable && (
                    <button className="btn btn-sm btn-green" style={{ marginLeft: "auto" }}
                      onClick={() => fix(k)} disabled={busy}>
                      一键{meta.fixLabel}（{list.length}）
                    </button>
                  )}
                </div>
                <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>{meta.hint}</div>
                <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                  {list.slice(0, 6).map((l) => `#${l.no} ${l.website || l.company_en}`).join("、")}
                  {list.length > 6 ? ` …等 ${list.length} 条` : ""}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
