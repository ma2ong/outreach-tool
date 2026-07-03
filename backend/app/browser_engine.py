from typing import Protocol

CHANNELS = {"whatsapp", "instagram"}


class BrowserEngine(Protocol):
    def status(self, channel: str) -> str: ...
    def connect(self, channel: str) -> None: ...
    def qr_png(self, channel: str) -> bytes | None: ...


class FakeEngine:
    """In-memory engine for tests. Status: disconnected -> connecting -> connected."""

    def __init__(self):
        self._state: dict[str, str] = {}

    def status(self, channel: str) -> str:
        return self._state.get(channel, "disconnected")

    def connect(self, channel: str) -> None:
        if self._state.get(channel) != "connected":
            self._state[channel] = "connecting"

    def simulate_login(self, channel: str) -> None:
        self._state[channel] = "connected"

    def qr_png(self, channel: str) -> bytes | None:
        return b"FAKEPNG" if self._state.get(channel) == "connecting" else None
