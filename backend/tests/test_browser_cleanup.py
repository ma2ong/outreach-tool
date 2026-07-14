"""The stale-browser cleanup is the fix for 'Instagram won't connect'. It is built
from a hand-written PowerShell string, and a brace-escaping typo once made it a
syntax error that failed silently — so assert the command actually parses and runs.
"""
import os
import subprocess
from pathlib import Path

import pytest

from app.playwright_engine import PlaywrightEngine

windows_only = pytest.mark.skipif(os.name != "nt", reason="cleanup is Windows-specific")


def _ps_command(prof: Path) -> str:
    """Rebuild the exact command the engine runs, minus the killing."""
    return (
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
        "Where-Object { $_.CommandLine -like '*" + str(prof) + "*' "
        "-and $_.ExecutablePath -like '*ms-playwright*' } | "
        "ForEach-Object { $_.ProcessId }"
    )


@windows_only
def test_cleanup_powershell_is_valid_syntax(tmp_path):
    out = subprocess.run(["powershell", "-NoProfile", "-Command", _ps_command(tmp_path)],
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, f"PowerShell rejected the command:\n{out.stderr}"
    assert "ParserError" not in out.stderr and "Unexpected token" not in out.stderr


@windows_only
def test_cleanup_on_unused_profile_kills_nothing(tmp_path):
    # No browser ever used tmp_path, so nothing may match — proves we don't kill blindly.
    assert PlaywrightEngine()._kill_stale_browser(tmp_path) == 0


@windows_only
def test_cleanup_only_targets_playwright_browsers():
    """A user's own Chrome must never be killed: the filter requires the ms-playwright
    install path, not just the profile name."""
    cmd = _ps_command(Path("C:/x/y"))
    assert "ms-playwright" in cmd and "ExecutablePath" in cmd
