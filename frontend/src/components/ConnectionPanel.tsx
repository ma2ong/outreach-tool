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

  const dot = (st: string) => st === "connected" ? "#3fb950" : st === "connecting" ? "#d29922" : "#8b949e";
  return (
    <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 16, marginBottom: 20 }}>
      <h3 style={{ color: "#e6edf3", marginTop: 0 }}>渠道连接</h3>
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {Object.keys(LABELS).map((ch) => (
          <div key={ch} style={{ color: "#e6edf3" }}>
            <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 5, background: dot(status[ch] || "disconnected"), marginRight: 6 }} />
            {LABELS[ch]}：{status[ch] === "connected" ? "已连接" : status[ch] === "connecting" ? "等待登录…" : "未连接"}
            {status[ch] !== "connected" && (
              <button onClick={() => connect(ch)} style={{ marginLeft: 10, background: "#1f6feb", color: "#fff", border: "none", borderRadius: 6, padding: "4px 12px" }}>连接</button>
            )}
          </div>
        ))}
      </div>
      {active === "whatsapp" && status.whatsapp === "connecting" && (
        <div style={{ marginTop: 14, color: "#e6edf3" }}>
          <div style={{ marginBottom: 6 }}>用手机 WhatsApp 扫描下方二维码登录（登录一次长期保持）：</div>
          <img alt="WhatsApp QR" src={`/api/channels/whatsapp/qr?t=${qrTick}`} style={{ width: 260, height: 260, background: "#fff", borderRadius: 8 }} />
        </div>
      )}
      {active === "instagram" && status.instagram === "connecting" && (
        <div style={{ marginTop: 14, color: "#8b949e" }}>已打开 Instagram 登录窗口，请在弹出的浏览器窗口中登录（含验证码）。登录后状态会自动更新。</div>
      )}
    </div>
  );
}
