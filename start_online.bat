@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "backend\auth_password.txt" (
  echo [X] 未设置访问密码，拒绝上线（公网裸奔=客户库对外敞开）。
  echo     请先在 backend\auth_password.txt 里写一行密码，再运行本脚本。
  pause
  exit /b 1
)

where cloudflared >nul 2>nul
if errorlevel 1 (
  echo [i] 首次使用：正在安装 cloudflared（Cloudflare Tunnel 客户端）…
  winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
  if errorlevel 1 (
    echo [X] cloudflared 安装失败，请手动安装后重试：winget install Cloudflare.cloudflared
    pause
    exit /b 1
  )
)

echo [i] 启动本地服务（端口 8000）…
start "outreach-tool-server" cmd /c "cd backend && python -m uvicorn app.main:app --port 8000"
timeout /t 6 /nobreak >nul

echo [i] 建立公网隧道…窗口里出现 https://xxxx.trycloudflare.com 就是你的公网网址。
echo     注意：免费隧道每次重启网址会变；想要固定网址需要一个自己的域名（可再找我配置）。
echo     关闭本窗口 = 下线（本地 http://127.0.0.1:8000 不受影响）。
cloudflared tunnel --url http://127.0.0.1:8000
