import { useEffect, useState } from "react";
import { fetchChannels, connectChannel, channelStatus } from "../api";

const LABELS: Record<string, string> = { whatsapp: "WhatsApp", instagram: "Instagram" };

export function ConnectionPanel() {
  const [status, setStatus] = useState<Record<string, string>>({});
  const [active, setActive] = useState<string | null>(null);
  const [qrTick, setQrTick] = useState(0);

  useEffect(() => { fetchChannels().then(setStatus).catch(() => {}); }, []);

  useEffect(() => {
    if (!active) return;
    const t = setInterval(async () => {
      try {
        const st = await channelStatus(active);
        setStatus((s) => ({ ...s, [active]: st }));
        setQrTick((n) => n + 1);
        if (st === "connected") { clearInterval(t); setActive(null); }
      } catch { /* ignore */ }
    }, 3000);
    return () => clearInterval(t);
  }, [active]);

  async function connect(ch: string) {
    setStatus((s) => ({ ...s, [ch]: "connecting" }));
    setActive(ch);
    await connectChannel(ch).catch(() => {});
  }

  const dot = (st: string) => st === "connected" ? "var(--green)" : st === "connecting" ? "var(--warn)" : "var(--gray)";
  return (
    <div className="card">
      <h3>渠道连接</h3>
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", alignItems: "center" }}>
        {Object.keys(LABELS).map((ch) => (
          <div key={ch}>
            <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 5, background: dot(status[ch] || "disconnected"), marginRight: 6 }} />
            {LABELS[ch]}：{status[ch] === "connected" ? "已连接" : status[ch] === "connecting" ? "等待登录…" : "未连接"}
            {status[ch] !== "connected" && (
              <button className="btn btn-primary btn-sm" style={{ marginLeft: 10 }} onClick={() => connect(ch)}>连接</button>
            )}
          </div>
        ))}
      </div>
      {active === "whatsapp" && status.whatsapp === "connecting" && (
        <div style={{ marginTop: 14 }}>
          <div style={{ marginBottom: 6 }}>用手机 WhatsApp 扫描下方二维码登录（登录一次长期保持）：</div>
          <img alt="WhatsApp QR" src={`/api/channels/whatsapp/qr?t=${qrTick}`} style={{ width: 260, height: 260, background: "#fff", borderRadius: 8 }} />
        </div>
      )}
      {active === "instagram" && status.instagram === "connecting" && (
        <div className="muted" style={{ marginTop: 14 }}>已打开 Instagram 登录窗口，请在弹出的浏览器窗口中登录（含验证码）。登录后状态会自动更新。</div>
      )}
    </div>
  );
}
