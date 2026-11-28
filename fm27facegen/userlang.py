"""Eigene Übersetzungen: Sprache als CSV exportieren (für Excel), übersetzen lassen und wieder importieren.

Importierte Sprachen sind reine Textdaten (JSON in %APPDATA%\\FM27FaceGenerator\\sprachen) – es wird nie Code
ausgeführt. Jeder Text wird geprüft: Platzhalter wie {n} müssen zum englischen Original passen, sonst bleibt
für diesen Text das Englische. In der Sprachauswahl steht immer '(nicht vom Generator)' dahinter.
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

from . import i18n

SECTIONS = ("text", "option", "country", "ethnicity", "personality")
MAX_LEN = 3000
_PH = re.compile(r"\{(\w*)\}")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f‪-‮⁦-⁩]")


def lang_dir() -> Path:
    from .settings import config_dir
    return config_dir() / "sprachen"


def _rows(code: str) -> list[tuple[str, str, str, str, str]]:
    """(Bereich, Schlüssel, Deutsch, Englisch, Text in Sprache 'code')"""
    from .country_names import NAMES
    from .locales import ETHNICITY_NAMES, OPTIONS, PERSONALITY_NAMES, STRINGS
    from .data import ETHNICITIES
    old = i18n.get_language()
    out = []
    try:
        for key in STRINGS:
            out.append(("text", key, i18n.t(key, lang="de"), i18n.t(key, lang="en"), i18n.t(key, lang=code)))
        for cat, items in OPTIONS.items():
            for key in items:
                vals = []
                for lang in ("de", "en", code):
                    i18n.set_language(lang)
                    vals.append(i18n.opt(cat, key))
                out.append(("option", f"{cat}|{key}", *vals))
        for table, fn, keys in (("country", i18n.country, list(NAMES)),
                                ("ethnicity", i18n.ethnicity, [k for k in ETHNICITIES if k in ETHNICITY_NAMES]),
                                ("personality", i18n.personality, list(PERSONALITY_NAMES))):
            for key in keys:
                vals = []
                for lang in ("de", "en", code):
                    i18n.set_language(lang)
                    vals.append(fn(key))
                out.append((table, key, *vals))
    finally:
        i18n.set_language(old)
    return out


def export_csv(path: str | Path, code: str) -> int:
    """CSV mit Semikolon (öffnet direkt in Excel). Spalte 'Übersetzung' ist mit der gewählten Sprache vorbelegt."""
    rows = _rows(code)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["#name", "Name der Sprache hier eintragen / enter the language name here", "", "", ""])
        w.writerow(["Bereich", "Schlüssel", "Deutsch", "English", "Übersetzung"])
        w.writerows(rows)
    return len(rows)


def _valid(text: str, english: str) -> str | None:
    text = _CTRL.sub("", text or "").strip()
    if not text or len(text) > MAX_LEN:
        return None
    if sorted(_PH.findall(text)) != sorted(_PH.findall(english)):
        return None
    try:
        kw = {k: 1 for k in _PH.findall(english) if k}
        text.format(**kw)
    except (KeyError, IndexError, ValueError):
        return None
    return text


def import_csv(path: str | Path) -> tuple[str, dict, int, int]:
    """Liest eine übersetzte CSV. Rückgabe: (Name, Daten, übernommen, verworfen)."""
    raw = Path(path).read_bytes()[:20_000_000].decode("utf-8-sig", errors="replace")
    dialect = ";" if raw.count(";") >= raw.count(",") else ","
    reader = csv.reader(io.StringIO(raw), delimiter=dialect)
    name, data, ok, bad = "", {s: {} for s in SECTIONS}, 0, 0
    english = {(r[0], r[1]): r[3] for r in _rows("en")}
    for row in reader:
        if not row:
            continue
        if row[0].strip() == "#name" and len(row) > 1:
            cand = _CTRL.sub("", row[1]).strip()
            if cand and not cand.startswith("Name der Sprache"):
                name = cand[:40]
            continue
        if len(row) < 5 or row[0] not in SECTIONS:
            continue
        section, key, text = row[0], row[1], row[4]
        en = english.get((section, key))
        if en is None or not text.strip():
            continue
        good = _valid(text, en)
        if good is None:
            bad += 1
            continue
        data[section][key] = good
        ok += 1
    return name, data, ok, bad


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return "user-" + (s or "sprache")[:24]


def save_language(name: str, data: dict) -> str:
    code = _slug(name)
    d = lang_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{code}.json").write_text(json.dumps({"name": name, **data}, ensure_ascii=False, indent=0),
                                    encoding="utf-8")
    register(code, name, data)
    return code


def remove_language(code: str) -> None:
    try:
        (lang_dir() / f"{code}.json").unlink()
    except OSError:
        pass
    i18n.USER.pop(code, None)
    i18n.LANGUAGES.pop(code, None)


def register(code: str, name: str, data: dict) -> None:
    i18n.USER[code] = {s: dict(data.get(s, {})) for s in SECTIONS}
    i18n.LANGUAGES[code] = name


def load_all() -> None:
    """Beim Start: alle importierten Sprachen anmelden (kaputte Dateien werden übersprungen)."""
    d = lang_dir()
    if not d.is_dir():
        return
    for f in sorted(d.glob("user-*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            name = _CTRL.sub("", str(data.get("name", ""))).strip()[:40] or f.stem
            clean = {s: {str(k): str(v) for k, v in (data.get(s) or {}).items() if isinstance(v, str)}
                     for s in SECTIONS}
            register(f.stem, name, clean)
        except (OSError, ValueError, AttributeError):
            continue
