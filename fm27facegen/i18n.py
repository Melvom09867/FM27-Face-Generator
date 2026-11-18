"""Mehrsprachigkeit: aktuelle Sprache, Übersetzungsfunktion und Anzeigenamen für Auswahlwerte.

Intern bleiben alle Auswahlwerte (Länder, Haarfarben, Persönlichkeiten …) deutsche Schlüssel –
so bleiben gespeicherte Einstellungen gültig, egal welche Sprache gerade aktiv ist.
Übersetzt wird nur die Anzeige.
"""

from __future__ import annotations

LANGS = ("de", "en", "it", "fr", "es", "pt", "ja", "ko")
LANGUAGES = {
    "de": "Deutsch",
    "en": "English",
    "it": "Italiano",
    "fr": "Français",
    "es": "Español",
    "pt": "Português",
    "ja": "日本語",
    "ko": "한국어",
}
DEFAULT = "de"

_lang = DEFAULT


def set_language(code: str) -> None:
    global _lang
    _lang = code if code in LANGS else DEFAULT


def get_language() -> str:
    return _lang


def _pick(row: tuple[str, ...], lang: str | None = None) -> str:
    i = LANGS.index(lang or _lang)
    text = row[i] if i < len(row) else ""
    return text or row[1] or row[0]  # Rückfall: Englisch, dann Deutsch


def t(key: str, lang: str | None = None, **kw) -> str:
    """Übersetzt einen Text-Schlüssel; mit Platzhaltern {name} wird formatiert.

    ``lang`` erlaubt eine andere als die aktuelle Sprache (z. B. Vorschau im Sprachdialog).
    """
    from .locales import STRINGS
    row = STRINGS.get(key)
    if row is None:
        return key
    text = _pick(row, lang if lang in LANGS else None)
    return text.format(**kw) if kw else text


def opt(category: str, key: str) -> str:
    """Anzeigename eines Auswahlwerts (z. B. opt('hair_color', 'Schwarz') -> 'Black')."""
    from .locales import OPTIONS
    row = OPTIONS.get(category, {}).get(key) or OPTIONS.get("_common", {}).get(key)
    return _pick(row) if row else key


def country(name_de: str) -> str:
    """Ländername in der aktuellen Sprache (Schlüssel = deutscher Name)."""
    if _lang == "de":
        return name_de
    from .country_names import LANGS as CL, NAMES
    row = NAMES.get(name_de)
    if not row:
        return name_de
    return row[CL.index(_lang)] or row[0]


def ethnicity(key: str) -> str:
    from .data import ETHNICITIES
    from .locales import ETHNICITY_NAMES
    if key in ETHNICITY_NAMES and _lang != "de":
        return _pick(("",) + ETHNICITY_NAMES[key])
    return ETHNICITIES[key]["label"] if key in ETHNICITIES else key


def personality(key: str) -> str:
    """Persönlichkeit: Deutsch/Englisch mit offiziellem FM-Namen, sonst Übersetzung + englischer FM-Name."""
    from .locales import PERSONALITY_NAMES
    if key in ("Keine", "Zufällig"):
        return opt("_common", key)
    de, _, en = key.partition(" (")
    en = en.rstrip(")")
    if _lang == "de":
        return key
    if _lang == "en":
        return en or key
    row = PERSONALITY_NAMES.get(key)
    if not row:
        return en or key
    local = row[LANGS.index(_lang) - 2]
    return f"{local} ({en})" if local and local != en else en
