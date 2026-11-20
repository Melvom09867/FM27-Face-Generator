"""Zusammenarbeit mit der Mod FaceDrop (nur lesen – in FaceDrops Ordnern wird nie etwas verändert).

FaceDrop legt übernommene Bilder als unveränderte Kopie ab:
    <FM-Benutzerordner>\\facedrop\\karrieren\\<Spielstand>\\newgen_<Spieler-ID>.png   (Newgens, Trainer …)
    <FM-Benutzerordner>\\facedrop\\<…>.png                                          (echte Spieler, Logos)
Der FM-Benutzerordner ist standardmäßig Dokumente\\Sports Interactive\\Football Manager 27, kann aber per
Steam-Startoption user_data_location="…" oder in FaceDrops Konfiguration (BepInEx) woanders liegen.
Welchen Ordner FaceDrop gerade benutzt, verrät die Datei startschutz.txt, die es bei jedem Spielstart schreibt.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

LOGO_PREFIXES = ("club_", "comp_", "nation_")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")
FM_DIR_NAMES = ("Football Manager 27", "Football Manager 2027")
CFG_NAME = "de.spielerbilder.facedrop.cfg"


# ---------------------------------------------------------------------- Steam
def steam_roots() -> list[Path]:
    """Steam-Installationsordner (Registry, sonst Standardpfade)."""
    roots: list[Path] = []
    if sys.platform.startswith("win"):
        try:
            import winreg
            for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                              (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
                try:
                    with winreg.OpenKey(hive, key) as k:
                        for name in ("SteamPath", "InstallPath"):
                            try:
                                roots.append(Path(winreg.QueryValueEx(k, name)[0]))
                            except OSError:
                                pass
                except OSError:
                    pass
        except ImportError:
            pass
        for env in ("ProgramFiles(x86)", "ProgramFiles"):
            if os.environ.get(env):
                roots.append(Path(os.environ[env]) / "Steam")
    else:
        roots += [Path.home() / ".steam" / "steam", Path.home() / ".local" / "share" / "Steam"]
    out, seen = [], set()
    for r in roots:
        try:
            key = str(r.resolve()).lower()
        except OSError:
            continue
        if r.is_dir() and key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _vdf_paths(text: str) -> list[str]:
    return [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', text)]


def steam_libraries(roots: list[Path] | None = None) -> list[Path]:
    libs: list[Path] = []
    for root in roots if roots is not None else steam_roots():
        libs.append(root)
        vdf = root / "steamapps" / "libraryfolders.vdf"
        try:
            libs += [Path(p) for p in _vdf_paths(vdf.read_text(encoding="utf-8", errors="replace"))]
        except OSError:
            pass
    out, seen = [], set()
    for lib in libs:
        k = str(lib).lower().rstrip("\\/")
        if k not in seen:
            seen.add(k)
            out.append(lib)
    return out


def fm_game_dirs(libraries: list[Path] | None = None) -> list[Path]:
    """Installationsordner von FM27 (dort liegt auch FaceDrops BepInEx-Konfiguration)."""
    dirs = []
    for lib in libraries if libraries is not None else steam_libraries():
        for name in FM_DIR_NAMES:
            d = lib / "steamapps" / "common" / name
            if d.is_dir():
                dirs.append(d)
    return dirs


def parse_user_data_locations(text: str) -> list[str]:
    """Liest user_data_location=… aus Steams localconfig.vdf (Startoptionen, Anführungszeichen dort maskiert)."""
    found = []
    for m in re.finditer(r'user_data_location\s*=\s*(\\?"(?P<q>.*?)\\?"|(?P<u>[^\s"\\]+(?:\\\\[^\s"\\]+)*))', text):
        value = m.group("q") if m.group("q") is not None else m.group("u")
        value = value.replace("\\\\", "\\").strip()
        if value and value not in found:
            found.append(value)
    return found


def steam_user_data_locations(roots: list[Path] | None = None) -> list[Path]:
    """FM-Benutzerordner aus den Steam-Startoptionen aller Steam-Konten auf diesem PC."""
    out: list[Path] = []
    for root in roots if roots is not None else steam_roots():
        for cfg in (root / "userdata").glob("*/config/localconfig.vdf"):
            try:
                text = cfg.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for p in parse_user_data_locations(text):
                if Path(p) not in out:
                    out.append(Path(p))
    return out


def facedrop_cfg_user_dirs(game_dirs: list[Path] | None = None) -> list[Path]:
    """In FaceDrops Konfiguration eingetragener FM-Benutzerordner (falls jemand ihn von Hand gesetzt hat)."""
    out = []
    for gd in game_dirs if game_dirs is not None else fm_game_dirs():
        cfg = gd / "BepInEx" / "config" / CFG_NAME
        try:
            text = cfg.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r"^\s*FM-Benutzerordner\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        if m and m.group(1):
            out.append(Path(m.group(1)))
    return out


# ---------------------------------------------------------------------- Benutzerordner / FaceDrop-Ordner
def default_user_dirs() -> list[Path]:
    from .settings import documents_dirs
    out = []
    for docs in documents_dirs():
        for name in FM_DIR_NAMES:
            d = docs / "Sports Interactive" / name
            if d.is_dir():
                out.append(d)
    return out


def user_data_candidates() -> list[Path]:
    """Alle denkbaren FM27-Benutzerordner: eigener (Steam/FaceDrop-cfg) zuerst, dann der Standard."""
    out: list[Path] = []
    for p in facedrop_cfg_user_dirs() + steam_user_data_locations() + default_user_dirs():
        if p.is_dir() and p not in out:
            out.append(p)
    return out


def _activity(facedrop_dir: Path) -> float:
    """Wie kürzlich FaceDrop diesen Ordner benutzt hat (startschutz.txt schreibt es bei jedem Spielstart)."""
    for name in ("startschutz.txt", "platzhalter.txt", "karrieren.json"):
        try:
            return (facedrop_dir / name).stat().st_mtime
        except OSError:
            continue
    try:
        return facedrop_dir.stat().st_mtime
    except OSError:
        return 0.0


def find_facedrop_dir(candidates: list[Path] | None = None) -> Path | None:
    """Der FaceDrop-Ordner, den FaceDrop gerade benutzt (bei mehreren: zuletzt aktiver)."""
    dirs = [c / "facedrop" for c in (candidates if candidates is not None else user_data_candidates())
            if (c / "facedrop").is_dir()]
    return max(dirs, key=_activity) if dirs else None


# ---------------------------------------------------------------------- Inhalt des FaceDrop-Ordners
@dataclass
class FaceDropInfo:
    folder: Path
    version: str = ""
    careers: dict[str, str] = field(default_factory=dict)  # Ordnername -> Anzeigename
    without_face: int = 0                                  # Spieler, die im Spiel noch den Standardkopf haben


def read_info(folder: Path) -> FaceDropInfo:
    info = FaceDropInfo(folder=folder)
    try:
        first = (folder / "startschutz.txt").read_text(encoding="utf-8", errors="replace").splitlines()[0]
        info.version = first.split("/")[0].strip()
    except (OSError, IndexError):
        pass
    names: dict[str, str] = {}
    try:
        data = json.loads((folder / "karrieren.json").read_text(encoding="utf-8"))
        if isinstance(data, dict):
            names = {str(k): str(v) for k, v in data.items()}
    except (OSError, ValueError):
        pass
    kdir = folder / "karrieren"
    if kdir.is_dir():
        for d in sorted(kdir.iterdir(), key=lambda p: p.name.casefold()):
            if d.is_dir():
                info.careers[d.name] = names.get(d.name, d.name)
    try:
        lines = (folder / "platzhalter.txt").read_text(encoding="utf-8", errors="replace").splitlines()
        info.without_face = sum(1 for ln in lines if "=" in ln and ln.split("=", 1)[1].strip().startswith("person_default"))
    except OSError:
        pass
    return info


def is_face_image(path: Path) -> bool:
    name = path.name.lower()
    return (path.suffix.lower() in IMAGE_SUFFIXES and not name.startswith(LOGO_PREFIXES)
            and not name.startswith("person_default"))


def career_images(folder: Path, career: str | None) -> list[Path]:
    """Gesichter einer Karriere – oder (career=None) die echten Spieler direkt im FaceDrop-Ordner. Neueste zuerst."""
    base = folder / "karrieren" / career if career else folder
    try:
        files = [p for p in base.iterdir() if p.is_file() and is_face_image(p)]
    except OSError:
        return []
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def all_face_images(folder: Path) -> list[Path]:
    """Alle von FaceDrop übernommenen Gesichter (alle Karrieren + echte Spieler)."""
    out = career_images(folder, None)
    kdir = folder / "karrieren"
    if kdir.is_dir():
        for d in kdir.iterdir():
            if d.is_dir():
                out += career_images(folder, d.name)
    return out


def is_facedrop_path(path: Path) -> bool:
    """Liegt die Datei in einem Ordner von FaceDrop (facedrop\\… oder graphics\\facedrop\\…)? Dort nie etwas ändern."""
    return any(part.casefold() == "facedrop" for part in Path(path).parent.parts)


def player_id(path: Path) -> str:
    m = re.search(r"(\d{4,})", path.stem)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------- Doppelte Bilder erkennen
_hash_cache: dict[tuple[str, int, float], str] = {}


def file_hash(path: Path) -> str:
    st = path.stat()
    key = (str(path), st.st_size, st.st_mtime)
    if key not in _hash_cache:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _hash_cache[key] = h.hexdigest()
    return _hash_cache[key]


def facedrop_index(folder: Path) -> dict[str, Path]:
    """Inhalt (Hash) -> Datei im FaceDrop-Ordner."""
    index = {}
    for p in all_face_images(folder):
        try:
            index[file_hash(p)] = p
        except OSError:
            continue
    return index


def find_duplicates(own_files: list[Path], index: dict[str, Path]) -> dict[Path, Path]:
    """Eigene Bilder, von denen FaceDrop eine identische Kopie hat: eigene Datei -> FaceDrop-Datei.

    Schnell auch bei vielen Bildern: Hashes werden nur für Dateien berechnet, deren Größe passt."""
    if not index:
        return {}
    sizes = set()
    for p in index.values():
        try:
            sizes.add(p.stat().st_size)
        except OSError:
            pass
    dups = {}
    for p in own_files:
        if is_facedrop_path(p):
            continue  # FaceDrops eigene Dateien (z. B. graphics\\facedrop) sind nie "unsere" Kopie
        try:
            if p.stat().st_size in sizes:
                h = file_hash(p)
                if h in index and index[h] != p and is_own_image(p):
                    dups[p] = index[h]
        except OSError:
            continue
    return dups


def is_own_image(path: Path) -> bool:
    """Vom Generator erzeugt? (Unsere PNGs tragen den Metadaten-Schlüssel 'fm27facegen'.)"""
    try:
        with path.open("rb") as f:
            return b"fm27facegen" in f.read(256 * 1024)
    except OSError:
        return False
