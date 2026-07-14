from fastapi import APIRouter, HTTPException, Response

from app.browser_engine import CHANNELS
from app.playwright_engine import PlaywrightEngine

router = APIRouter(prefix="/api/channels")

ENGINE = PlaywrightEngine()  # injectable in tests


def _check(channel: str):
    if channel not in CHANNELS:
        raise HTTPException(status_code=400, detail="unknown channel")


@router.get("")
def list_channels():
    return {c: ENGINE.status(c) for c in sorted(CHANNELS)}


@router.post("/{channel}/connect")
def connect(channel: str):
    _check(channel)
    try:
        ENGINE.connect(channel)
    except Exception as exc:  # noqa: BLE001 — a raw 500 told Allen nothing
        raise HTTPException(
            status_code=502,
            detail=f"浏览器启动失败：{exc}。多半是上次的浏览器窗口还占着登录数据；"
                   f"系统已尝试自动清理并重试。若仍失败，关掉所有自动化浏览器窗口后再点一次连接。")
    return {"status": ENGINE.status(channel)}


@router.get("/{channel}/status")
def status(channel: str):
    _check(channel)
    st = ENGINE.refresh(channel) if hasattr(ENGINE, "refresh") else ENGINE.status(channel)
    return {"status": st}


@router.get("/{channel}/qr")
def qr(channel: str):
    _check(channel)
    png = ENGINE.qr_png(channel)
    if png is None:
        raise HTTPException(status_code=404, detail="no qr")
    return Response(content=png, media_type="image/png")
