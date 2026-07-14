import os
import queue
import re
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path

LOGIN_URLS = {
    "whatsapp": "https://web.whatsapp.com/",
    "instagram": "https://www.instagram.com/accounts/login/",
    "facebook": "https://www.facebook.com/login/",
}
DATA_DIR = Path(os.environ.get("OUTREACH_BROWSER_DIR", str(Path.home() / ".outreach-tool" / "browser")))

# selector that indicates a logged-in (connected) session
_CONNECTED = {
    "whatsapp": "#pane-side",
    "instagram": "svg[aria-label='Home'], a[href='/']",
    "facebook": "div[role='navigation'], a[aria-label='Home'], a[href*='/me/']",
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
    def _kill_stale_browser(self, prof: Path) -> int:
        """Kill a leftover Playwright browser still holding this profile directory.

        Killing the server (crash, taskkill, closing the window) does NOT kill the
        chromium it launched; the orphan keeps the profile locked and every later
        launch dies with exitCode=21 — which is exactly what "Instagram won't connect"
        looked like. Chrome's renderer children quote the path (--user-data-dir="C:\\...")
        while the parent doesn't, and they hold the lock too, so match the bare path.
        Matching requires BOTH the profile path and the ms-playwright install dir,
        so Allen's own Chrome is never touched.
        """
        if os.name != "nt":
            return 0
        ps = (
            "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
            "Where-Object { $_.CommandLine -like '*" + str(prof) + "*' "
            "-and $_.ExecutablePath -like '*ms-playwright*' } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }"
        )
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                                 capture_output=True, text=True, timeout=25)
        except Exception:  # noqa: BLE001
            return 0
        return len([line for line in out.stdout.split() if line.strip()])

    def _launch(self, prof: Path):
        args = ["--window-position=80,80", "--window-size=1100,820"]
        try:
            return self._p.chromium.launch_persistent_context(str(prof), headless=False, args=args)
        except Exception:  # noqa: BLE001
            if not self._kill_stale_browser(prof):
                raise
            time.sleep(2)
            return self._p.chromium.launch_persistent_context(str(prof), headless=False, args=args)

    def _page(self, channel):
        ctx = self._ctx.get(channel)
        if ctx is not None:
            try:  # a context whose window the user closed is dead — rebuild it
                ctx.pages
            except Exception:  # noqa: BLE001
                self._ctx.pop(channel, None)
                ctx = None
        if ctx is None:
            prof = DATA_DIR / channel
            prof.mkdir(parents=True, exist_ok=True)
            ctx = self._ctx[channel] = self._launch(prof)
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

    def _send_op(self, channel, target, message, image=None):
        page = self._page(channel)
        if channel == "whatsapp":
            url = f"https://web.whatsapp.com/send?phone={target}&text={urllib.parse.quote(message)}"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # invalid/unregistered number surfaces a dialog instead of a chat
            try:
                if page.get_by_text(re.compile("invalid|not.*valid|isn't on whatsapp|无效", re.I)).first.is_visible(timeout=4000):
                    raise RuntimeError("number not on WhatsApp")
            except RuntimeError:
                raise
            except Exception:  # noqa: BLE001
                pass
            box = page.locator("footer div[contenteditable='true']").first
            box.wait_for(state="visible", timeout=45000)
            page.wait_for_timeout(1500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
            if image:
                self._wa_attach_image(page, image)
            return True
        if channel == "instagram":
            page.goto(f"https://www.instagram.com/{target}/", wait_until="domcontentloaded", timeout=60000)
            btn = page.get_by_role("button", name=re.compile("message|发消息|发送消息|信息", re.I)).first
            btn.click(timeout=20000)
            box = page.locator("div[contenteditable='true'][role='textbox'], textarea[placeholder]").first
            box.wait_for(state="visible", timeout=30000)
            box.click()
            page.wait_for_timeout(400)
            page.keyboard.insert_text(message)  # Input.insertText: works with React contenteditable (Chrome 130+)
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            if image:
                # DM thread keeps a hidden file input; selecting a photo sends it immediately
                page.locator("input[type='file']").last.set_input_files(image)
                page.wait_for_timeout(4000)
            return True
        if channel == "facebook":
            # Page inbox lives on the page itself; the Message button opens the chat dock.
            page.goto(f"https://www.facebook.com/{target}", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            btn = page.get_by_role("button", name=re.compile("^(message|发消息|发送消息|send message)$", re.I)).first
            try:
                btn.click(timeout=20000)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("no Message button on this page (not a business page, or DMs off)") from exc
            box = page.locator("div[contenteditable='true'][role='textbox'], div[aria-label*='Message'][contenteditable='true']").first
            box.wait_for(state="visible", timeout=30000)
            box.click()
            page.wait_for_timeout(400)
            page.keyboard.insert_text(message)
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
            if image:
                page.locator("input[type='file']").last.set_input_files(image)
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter")
                page.wait_for_timeout(4000)
            return True
        raise ValueError(f"unsupported channel {channel}")

    def _wa_attach_image(self, page, image):
        page.locator("div[title='Attach'], button[aria-label*='Attach'], span[data-icon='plus'], span[data-icon='clip'], span[data-icon='plus-rounded']").first.click(timeout=15000)
        page.wait_for_timeout(800)
        page.locator("input[type='file'][accept*='image']").first.set_input_files(image)
        send = page.locator("span[data-icon='send'], span[data-icon='wds-ic-send-filled'], div[role='button'][aria-label*='Send']").first
        send.wait_for(state="visible", timeout=30000)
        send.click()
        page.wait_for_timeout(3000)

    # ---- public thread-safe API ----
    def status(self, channel: str) -> str:
        return self._state.get(channel, "disconnected")

    def send_message(self, channel: str, target: str, message: str, image: str | None = None) -> None:
        self._call(self._send_op, channel, target, message, image, timeout=150)

    def connect(self, channel: str) -> None:
        self._state[channel] = "connecting"
        self._call(self._connect_op, channel)

    def refresh(self, channel: str) -> str:
        st = self._call(self._refresh_op, channel)
        self._state[channel] = st
        return st

    def qr_png(self, channel: str) -> bytes | None:
        return self._qr.get(channel)
