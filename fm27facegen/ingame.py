"""„Im Spiel ersetzen“: gealterte Bilder ersetzen FaceDrops Bilder – mit Sicherungskopie und Rückgängig.

Ablauf: Alle neuen Bilder entstehen zuerst in einer Warteschlange (%APPDATA%). Erst wenn der ganze Durchlauf
fertig ist, werden sie in einem Rutsch in FaceDrops Ordner geschoben – vorher wird jedes alte Bild in den
Speicherort unter 'Sicherungskopie\\<Datum Uhrzeit>\\<Karriere>\\' kopiert. 'letzte_ersetzung.json' merkt sich
den letzten Durchlauf, damit er rückgängig gemacht werden kann.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

BACKUP_DIR = "Sicherungskopie"
MANIFEST = "letzte_ersetzung.json"


def staging_dir() -> Path:
    from .settings import config_dir
    d = config_dir() / "warteschlange"
    d.mkdir(parents=True, exist_ok=True)
    return d


def backup_root(output_dir: str | Path) -> Path:
    return Path(output_dir) / BACKUP_DIR


def _move_over(src: Path, dst: Path) -> None:
    """src ersetzt dst (auch über Laufwerksgrenzen)."""
    try:
        os.replace(src, dst)
    except OSError:
        shutil.copy2(src, dst)
        src.unlink(missing_ok=True)


def apply_replacements(pairs: list[tuple[Path, Path]], output_dir: str | Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    """pairs: (neues Bild in der Warteschlange, FaceDrop-Bild). Rückgabe: (ersetzt, [(Ziel, Fehler)])."""
    stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    bdir = backup_root(output_dir) / stamp
    done: list[Path] = []
    failed: list[tuple[Path, str]] = []
    items = []
    for staged, target in pairs:
        staged, target = Path(staged), Path(target)
        try:
            backup = bdir / target.parent.name / target.name
            if target.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            _move_over(staged, target)
            items.append({"target": str(target), "backup": str(backup) if backup.exists() else ""})
            done.append(target)
        except OSError as exc:
            failed.append((target, str(exc)))
    if items:
        root = backup_root(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / MANIFEST).write_text(json.dumps({"time": stamp, "items": items}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    return done, failed


def _manifest(output_dir: str | Path) -> dict | None:
    try:
        return json.loads((backup_root(output_dir) / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def undo_count(output_dir: str | Path) -> int:
    m = _manifest(output_dir)
    return len([i for i in (m or {}).get("items", []) if i.get("backup")])


def undo_last(output_dir: str | Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Holt die Bilder der letzten Ersetzung aus der Sicherungskopie zurück (nur einmal möglich)."""
    m = _manifest(output_dir) or {}
    restored: list[Path] = []
    failed: list[tuple[Path, str]] = []
    for item in m.get("items", []):
        target, backup = Path(item["target"]), Path(item.get("backup") or "")
        if not item.get("backup"):
            continue
        try:
            shutil.copy2(backup, target)
            restored.append(target)
        except OSError as exc:
            failed.append((target, str(exc)))
    try:
        man = backup_root(output_dir) / MANIFEST
        man.replace(man.with_suffix(".rueckgaengig.json"))
    except OSError:
        pass
    return restored, failed
