import os
import queue
import threading
from pathlib import Path

LOGIN_URLS = {
    "whatsapp": "https://web.whatsapp.com/",
    "instagram": "https://www.instagram.com/accounts/login/",
}
DATA_DIR = Path(os.environ.get("OUTREACH_BROWSER_DIR", str(Path.home() / ".outreach-tool" / "browser")))

# selector that indicates a logged-in (connected) session
_CONNECTED = {
    "whatsapp": "#pane-side",
    "instagram": "svg[aria-label='Home'], a[href='/']",
}
# selector for the login QR / code (whatsapp only)
_QR = {
    "whatsapp": "canvas[aria-label*='Scan'], div[data-ref], canvas",
}


class PlaywrightEngine:
    """Owns a worker thread running the sync Playwright API (which must stay on one
    thread). Public methods are thread-safe and block on the worker via a future."""

    def __init__(self):
        self._q: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._state: dict[str, str] = {}
        self._qr: dict[str, bytes | None] = {}
        self._lock = threading.Lock()

    # ---- worker-thread plumbing ----
    def _ensure_thread(self):
        with self._lock:
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()

    def _run(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            self._p = p
            self._ctx: dict[str, object] = {}
            while True:
                fn, args, fut = self._q.get()
                try:
                    fut["result"] = fn(*args)
                except Exception as exc:  # noqa: BLE001
                    fut["error"] = exc
                finally:
                    fut["done"].set()

    def _call(self, fn, *args, timeout=180):
        self._ensure_thread()
        fut = {"done": threading.Event(), "result": None, "error": None}
        self._q.put((fn, args, fut))
        if not fut["done"].wait(timeout):
            raise TimeoutError("browser op timed out")
        if fut["error"]:
            raise fut["error"]
        return fut["result"]

    # ---- ops that run ON the worker thread ----
    def _page(self, channel):
        if channel not in self._ctx:
            prof = DATA_DIR / channel
            prof.mkdir(parents=True, exist_ok=True)
            self._ctx[channel] = self._p.chromium.launch_persistent_context(
                str(prof), headless=False,
                args=["--window-position=80,80", "--window-size=1100,820"])
        ctx = self._ctx[channel]
        return ctx.pages[0] if ctx.pages else ctx.new_page()

    def _connect_op(self, channel):
        page = self._page(channel)
        page.goto(LOGIN_URLS[channel], wait_until="domcontentloaded", timeout=60000)
        return True

    def _refresh_op(self, channel):
        if channel not in self._ctx:
            return "disconnected"
        pages = self._ctx[channel].pages
        if not pages:
            return "disconnected"
        page = pages[0]
        try:
            if page.locator(_CONNECTED[channel]).first.is_visible(timeout=2500):
                self._qr[channel] = None
                return "connected"
        except Exception:  # noqa: BLE001
            pass
        if channel in _QR:
            try:
                el = page.locator(_QR[channel]).first
                if el.is_visible(timeout=2500):
                    self._qr[channel] = el.screenshot()
                    return "connecting"
            except Exception:  # noqa: BLE001
                pass
        return "connecting"

    # ---- public thread-safe API ----
    def status(self, channel: str) -> str:
        return self._state.get(channel, "disconnected")

    def connect(self, channel: str) -> None:
        self._state[channel] = "connecting"
        self._call(self._connect_op, channel)

    def refresh(self, channel: str) -> str:
        st = self._call(self._refresh_op, channel)
        self._state[channel] = st
        return st

    def qr_png(self, channel: str) -> bytes | None:
        return self._qr.get(channel)
