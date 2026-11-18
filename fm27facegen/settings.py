"""Speichert die zuletzt verwendeten Einstellungen (%APPDATA%\\FM27FaceGenerator\\einstellungen.json)."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .backends import BackendSettings
from .generator import DEFAULT_PATTERN
from .imaging import ProcessOptions
from .prompts import FaceOptions


def config_dir() -> Path:
    base = os.environ.get("APPDATA")
    return Path(base) / "FM27FaceGenerator" if base else Path.home() / ".fm27facegenerator"


def default_output_dir() -> Path:
    docs = Path.home() / "Documents"
    return (docs if docs.exists() else Path.home()) / "FM27 Faces"


def documents_dirs() -> list[Path]:
    home = Path.home()
    cands = [home / "Documents", home / "Dokumente", home / "OneDrive" / "Documents", home / "OneDrive" / "Dokumente"]
    for env in ("OneDrive", "OneDriveConsumer"):
        if os.environ.get(env):
            cands += [Path(os.environ[env]) / "Documents", Path(os.environ[env]) / "Dokumente"]
    seen, out = set(), []
    for c in cands:
        if c.is_dir() and c.resolve() not in seen:
            seen.add(c.resolve())
            out.append(c)
    return out


def find_fm_folders() -> list[Path]:
    """Sucht Football-Manager-Benutzerordner (…\\Sports Interactive\\Football Manager …), neueste zuerst."""
    found: list[Path] = []
    for docs in documents_dirs():
        si = docs / "Sports Interactive"
        if not si.is_dir():
            continue
        for d in si.iterdir():
            if d.is_dir() and d.name.lower().startswith("football manager"):
                found.append(d)

    def rank(p: Path):
        nums = [int(n) for n in re.findall(r"\d+", p.name)]
        year = max((n if n > 100 else 2000 + n for n in nums), default=0)
        return (year, p.stat().st_mtime)

    return sorted(found, key=rank, reverse=True)


@dataclass
class AppSettings:
    face: FaceOptions = field(default_factory=FaceOptions)
    backend: BackendSettings = field(default_factory=BackendSettings)
    process: ProcessOptions = field(default_factory=ProcessOptions)
    output_dir: str = field(default_factory=lambda: str(default_output_dir()))
    pattern: str = DEFAULT_PATTERN
    count: int = 5
    delay: float = 3.0
    subfolder_per_country: bool = False
    overwrite: bool = False
    list_name_mode: str = "Name"
    list_parent_mode: str = "Zufällig"
    aging_ages: str = "16, 20, 25, 30, 34"
    language: str = "de"
    ask_language: bool = True  # Sprachauswahl beim Start zeigen
    version: int = 3  # Version der Einstellungen (für automatische Umstellung nach Updates)


def _fill(cls, data: dict):
    names = {f.name for f in fields(cls)}
    obj = cls()
    for k, v in (data or {}).items():
        if k in names:
            cur = getattr(obj, k)
            try:
                setattr(obj, k, type(cur)(v) if cur is not None and not isinstance(cur, str) else v)
            except (TypeError, ValueError):
                pass
    return obj


def load(path: Path | None = None) -> AppSettings:
    path = path or config_dir() / "einstellungen.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return AppSettings()
    s = AppSettings(
        face=_fill(FaceOptions, raw.get("face")),
        backend=_fill(BackendSettings, raw.get("backend")),
        process=_fill(ProcessOptions, raw.get("process")),
    )
    for k in ("output_dir", "pattern", "count", "delay", "subfolder_per_country", "overwrite",
              "list_name_mode", "list_parent_mode", "aging_ages", "language", "ask_language"):
        if k in raw:
            try:
                setattr(s, k, type(getattr(s, k))(raw[k]))
            except (TypeError, ValueError):
                pass
    if int(raw.get("version", 1) or 1) < 3:
        # v1.4: Zuschnitt und Hintergrund auf FM-Cut-out-Stil umstellen
        defaults_face, defaults_proc = FaceOptions(), ProcessOptions()
        s.process.zoom, s.process.face_y = defaults_proc.zoom, defaults_proc.face_y
        s.face.background = defaults_face.background
        s.face.clothing = defaults_face.clothing
    s.version = 3
    return s


def save(s: AppSettings, path: Path | None = None) -> None:
    path = path or config_dir() / "einstellungen.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(s), indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
