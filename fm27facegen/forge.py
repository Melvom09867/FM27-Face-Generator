"""Stable Diffusion WebUI Forge automatisch im Hintergrund starten und wieder beenden."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

import requests

IS_WINDOWS = sys.platform.startswith("win")
CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_PROCESS_GROUP = 0x00000200


def find_launcher(folder: str | Path) -> Path | None:
    """Startdatei im Forge-Ordner: run.bat (One-Click-Paket), sonst webui-user.bat."""
    if not folder:
        return None
    folder = Path(folder)
    for cand in (folder / "run.bat", folder / "webui-user.bat", folder / "webui" / "webui-user.bat",
                 folder / "webui.sh", folder / "webui" / "webui.sh"):
        if cand.is_file():
            return cand
    return None


def api_enabled(folder: str | Path) -> bool | None:
    """Steht '--api' in webui-user.bat? None = Datei nicht gefunden (dann nicht prüfbar)."""
    folder = Path(folder)
    for cand in (folder / "webui" / "webui-user.bat", folder / "webui-user.bat"):
        if cand.is_file():
            try:
                text = cand.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return None
            lines = [ln for ln in text.splitlines()
                     if re.match(r"\s*set\s+COMMANDLINE_ARGS\s*=", ln, re.IGNORECASE)]
            return any("--api" in ln for ln in lines)
    return None


def api_state(sd_url: str, timeout: float = 3) -> str:
    """'ready' = API antwortet, 'no_api' = WebUI läuft ohne --api, 'down' = nicht erreichbar."""
    try:
        r = requests.get(sd_url.rstrip("/") + "/sdapi/v1/options", timeout=timeout)
    except requests.RequestException:
        return "down"
    if r.status_code == 200:
        return "ready"
    return "no_api" if r.status_code == 404 else "down"


class ForgeManager:
    """Startet Forge unsichtbar und beendet es wieder – aber nur, wenn wir es selbst gestartet haben."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.proc: subprocess.Popen | None = None
        self.started_by_us = False
        self.state = "idle"  # idle | starting | ready | failed | external
        self._cancel = threading.Event()

    # ---------------------------------------------------------------- Start
    def start(self, folder: str | Path) -> subprocess.Popen:
        launcher = find_launcher(folder)
        if launcher is None:
            raise FileNotFoundError(str(folder))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        log = open(self.log_path, "w", encoding="utf-8", errors="replace")  # noqa: SIM115 – bleibt offen, solange Forge läuft
        env = dict(os.environ)
        env["SD_WEBUI_RESTARTING"] = "1"  # verhindert, dass Forge beim Start ein Browserfenster öffnet
        if IS_WINDOWS:
            cmd = ["cmd", "/c", str(launcher)]
            flags = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
        else:
            cmd = ["bash", str(launcher)] if launcher.suffix == ".sh" else [str(launcher)]
            flags = 0
        self.proc = subprocess.Popen(cmd, cwd=str(launcher.parent), stdout=log, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, env=env, creationflags=flags,
                                     start_new_session=not IS_WINDOWS)
        self.started_by_us = True
        self.state = "starting"
        self._cancel.clear()
        return self.proc

    def wait_ready(self, sd_url: str, timeout: float = 900, interval: float = 3,
                   on_tick: Callable[[int], None] | None = None) -> str:
        """Wartet, bis die API antwortet. Ergebnis: 'ready', 'no_api', 'exited', 'timeout' oder 'cancelled'."""
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if self._cancel.wait(interval):
                return "cancelled"
            state = api_state(sd_url)
            if state in ("ready", "no_api"):
                self.state = "ready" if state == "ready" else "failed"
                return state
            if self.proc is not None and self.proc.poll() is not None:
                self.state = "failed"
                return "exited"
            if on_tick:
                on_tick(int(time.monotonic() - t0))
        self.state = "failed"
        return "timeout"

    # ---------------------------------------------------------------- Ende
    def stop(self) -> None:
        """Beendet Forge samt aller Unterprozesse – nur wenn wir es gestartet haben."""
        self._cancel.set()
        proc, self.proc = self.proc, None
        if not self.started_by_us or proc is None or proc.poll() is not None:
            return
        try:
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True,
                               creationflags=CREATE_NO_WINDOW, timeout=20)
            else:
                import signal
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
        except Exception:  # noqa: BLE001
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass
        self.started_by_us = False
        self.state = "idle"
