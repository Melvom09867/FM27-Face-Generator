"""'Jetzt aktualisieren': neue Version herunterladen und die laufende .exe austauschen.

Ablauf: ZIP der neuesten Version laden -> neue .exe als '<Name>.exe.new' neben die alte legen ->
kleines Hilfsskript wartet, bis der Generator beendet ist, ersetzt die .exe und startet sie neu.
Funktioniert nur in der fertigen Windows-.exe und nur, wenn ihr Ordner beschreibbar ist
(sonst bleibt der Weg über die Download-Seite).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Callable

import requests

DOC_SUFFIXES = (".md", ".txt", ".json")


def exe_path() -> Path | None:
    """Pfad der laufenden .exe – None, wenn nicht als .exe gestartet (z. B. aus dem Quellcode)."""
    if getattr(sys, "frozen", False) and sys.platform.startswith("win"):
        return Path(sys.executable).resolve()
    return None


def can_self_update() -> bool:
    exe = exe_path()
    if not exe:
        return False
    probe = exe.parent / ".fm27_update_test"
    try:
        probe.write_bytes(b"")
        probe.unlink()
        return True
    except OSError:
        return False


def download(url: str, dest: Path, progress: Callable[[float], None] | None = None,
             cancelled: Callable[[], bool] | None = None, timeout: float = 30) -> None:
    with requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": "FM27-FaceGenerator"}) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with dest.open("wb") as f:
            for chunk in r.iter_content(1 << 16):
                if cancelled and cancelled():
                    raise InterruptedError
                f.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(min(done / total, 1.0))


STAGE_DIR = "_update_new"


def unpack(zip_path: Path, target_dir: Path, exe_name: str) -> tuple[str, Path]:
    """Update-Paket auspacken.

    Programmordner-Paket (ab 1.8.7.2: .exe + _internal): alles nach '<Programmordner>/_update_new' –
    Rückgabe ("folder", Ordner mit der neuen .exe). Altes Ein-Datei-Paket: neue .exe als '<exe_name>.new' –
    Rückgabe ("exe", Pfad). Anleitungen/PatchNotes werden in beiden Fällen gleich aktualisiert."""
    with zipfile.ZipFile(zip_path) as z:
        names = [i.filename.replace("\\", "/") for i in z.infolist()]
        if any("/_internal/" in "/" + n for n in names):
            stage = target_dir / STAGE_DIR
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
            stage.mkdir(parents=True)
            root = stage.resolve()
            for info in z.infolist():
                dest = (stage / info.filename).resolve()
                if root not in dest.parents and dest != root:
                    raise ValueError("unsafe path in update package")
            z.extractall(stage)
            hits = [p for p in stage.rglob(exe_name)]
            if not hits:
                raise ValueError("no .exe in update package")
            return "folder", hits[0].parent
        new_exe = target_dir / (exe_name + ".new")
        found = False
        for info in z.infolist():
            name = Path(info.filename).name
            if info.is_dir() or not name:
                continue
            if name.lower().endswith(".exe"):
                with z.open(info) as src, new_exe.open("wb") as dst:
                    dst.write(src.read())
                found = True
            elif name.lower().endswith(DOC_SUFFIXES) and name.lower() != "laender.json":
                try:
                    with z.open(info) as src:
                        (target_dir / name).write_bytes(src.read())
                except OSError:
                    pass  # Anleitung gerade geöffnet o. Ä. – unwichtig
    if not found:
        raise ValueError("no .exe in update package")
    return "exe", new_exe


def helper_script(pid: int, exe: Path, source: Path, kind: str = "exe") -> str:
    """Wartet aufs Programmende, tauscht das Programm aus und startet es neu.

    kind="exe": .exe ersetzen (bis zu 60 Versuche). kind="folder": alten _internal-Ordner löschen und den neuen
    Programmordner hineinkopieren (eigene Dateien wie laender.json bleiben erhalten)."""
    app = exe.parent
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        "set n=0",
        ":wait",
        f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul',
        "if errorlevel 1 goto swap",
        "timeout /t 1 /nobreak >nul",
        "goto wait",
        ":swap",
    ]
    if kind == "folder":
        lines += [
            f'if exist "{app}\\_internal" rmdir /s /q "{app}\\_internal" >nul 2>&1',
            f'if not exist "{app}\\_internal" goto copy',
            "set /a n+=1",
            "if %n% geq 60 goto end",
            "timeout /t 1 /nobreak >nul",
            "goto swap",
            ":copy",
            f'robocopy "{source}" "{app}" /E /MOVE /R:30 /W:1 /NFL /NDL /NJH /NJS /NP >nul',
            "if errorlevel 8 goto end",
            f'rmdir /s /q "{app}\\{STAGE_DIR}" >nul 2>&1',
        ]
    else:
        lines += [
            f'move /y "{source}" "{exe}" >nul 2>&1',
            "if not errorlevel 1 goto start",
            "set /a n+=1",
            "if %n% geq 60 goto end",
            "timeout /t 1 /nobreak >nul",
            "goto swap",
        ]
    lines += [":start", f'start "" "{exe}"', ":end", 'del "%~f0"', ""]
    return "\r\n".join(lines)


def launch_swap(source: Path, kind: str = "exe") -> None:
    """Startet das Hilfsskript; danach muss sich der Generator beenden."""
    exe = exe_path()
    if not exe:
        raise RuntimeError("not running as .exe")
    bat = Path(tempfile.gettempdir()) / f"fm27_update_{os.getpid()}.bat"
    bat.write_text(helper_script(os.getpid(), exe, source, kind), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("_MEI", "_PYI"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"  # neue .exe soll ihren eigenen Temp-Ordner anlegen
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(["cmd", "/c", str(bat)], env=env, creationflags=flags, close_fds=True,
                     cwd=str(exe.parent))
