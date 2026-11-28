"""Mehrsprachigkeit: aktuelle Sprache, Übersetzungsfunktion und Anzeigenamen für Auswahlwerte.

Intern bleiben alle Auswahlwerte (Länder, Haarfarben, Persönlichkeiten …) deutsche Schlüssel –
so bleiben gespeicherte Einstellungen gültig, egal welche Sprache gerade aktiv ist.
Übersetzt wird nur die Anzeige.
"""

from __future__ import annotations

LANGS = ("de", "en", "it", "fr", "es", "pt", "ja", "ko")  # Spalten der Tabellen in locales.py
# Weitere Sprachen (wie in FM27) stehen je Sprache in fm27facegen/lang/<code>.py.
# Varianten (es-419, pt-PT) übernehmen alles Fehlende von ihrer Grundsprache.
EXTRA = ("es-419", "pt-PT", "nl", "da", "no", "sv", "pl", "ru", "tr", "el", "id", "zh")
BASE = {"es-419": "es", "pt-PT": "pt"}
LANGUAGES = {  # Reihenfolge in der Sprachauswahl
    "de": "Deutsch",
    "en": "English",
    "es": "Español (España)",
    "es-419": "Español (Latinoamérica)",
    "fr": "Français",
    "it": "Italiano",
    "nl": "Nederlands",
    "da": "Dansk",
    "no": "Norsk",
    "sv": "Svenska",
    "pl": "Polski",
    "pt": "Português (Brasil)",
    "pt-PT": "Português (Portugal)",
    "ru": "Русский",
    "tr": "Türkçe",
    "el": "Ελληνικά",
    "id": "Bahasa Indonesia",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "简体中文",
}
DEFAULT = "de"
USER: dict[str, dict] = {}  # importierte Sprachen (userlang.py): Code -> {"text": {...}, "option": {...}, …}

_lang = DEFAULT


def set_language(code: str) -> None:
    global _lang
    _lang = code if code in LANGUAGES else DEFAULT


def language_label(code: str) -> str:
    """Name in der Sprachauswahl – alle Übersetzungen außer Deutsch sind KI-erstellt und so gekennzeichnet."""
    name = LANGUAGES.get(code, code)
    if code in USER:
        # Kennzeichnung in der aktuellen (eingebauten) Sprache – nie aus der importierten Datei
        return f"{name} ({t('lang.user', lang=_lang if _lang not in USER else 'en')})"
    return name if code == "de" else f"{name} ({t('lang.ai', lang=code)})"


def _extra(code: str):
    """Sprachmodul fm27facegen/lang/<code>.py (z. B. 'es-419' -> es_419)."""
    import importlib
    from . import lang  # noqa: F401 – damit PyInstaller alle Sprachdateien einpackt
    return importlib.import_module(f".lang.{code.replace('-', '_').lower()}", __package__)


def _base(code: str) -> str:
    return BASE.get(code, "en")


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
    code = lang if lang in LANGUAGES else _lang
    if code in USER:
        text = USER[code]["text"].get(key) or _pick(row, "en")
        if key == "lang.user":  # Kennzeichnung nie aus der importierten Datei
            text = _pick(row, "en")
        try:
            return text.format(**kw) if kw else text
        except (KeyError, IndexError, ValueError):
            text = _pick(row, "en")
    elif code in LANGS:
        text = _pick(row, code)
    else:
        text = _extra(code).STRINGS.get(key) or _pick(row, _base(code))
    return text.format(**kw) if kw else text


def opt(category: str, key: str) -> str:
    """Anzeigename eines Auswahlwerts (z. B. opt('hair_color', 'Schwarz') -> 'Black')."""
    from .locales import OPTIONS
    row = OPTIONS.get(category, {}).get(key) or OPTIONS.get("_common", {}).get(key)
    if not row:
        return key
    if _lang in USER:
        u = USER[_lang]["option"]
        return u.get(f"{category}|{key}") or u.get(f"_common|{key}") or _pick(row, "en")
    if _lang in LANGS:
        return _pick(row)
    o = _extra(_lang).OPTIONS
    return o.get(f"{category}|{key}") or o.get(f"_common|{key}") or _pick(row, _base(_lang))


def country(name_de: str) -> str:
    """Ländername in der aktuellen Sprache (Schlüssel = deutscher Name)."""
    if _lang == "de":
        return name_de
    from .country_names import LANGS as CL, NAMES
    row = NAMES.get(name_de)
    if not row:
        return name_de
    if _lang in USER:
        return USER[_lang]["country"].get(name_de) or row[CL.index("en")]
    if _lang in CL:
        return row[CL.index(_lang)] or row[0]
    from .country_names_extra import NAMES as EX
    return EX.get(_lang, {}).get(name_de) or (row[CL.index(BASE[_lang])] if _lang in BASE else row[0])


def ethnicity(key: str) -> str:
    from .data import ETHNICITIES
    from .locales import ETHNICITY_NAMES
    if key in ETHNICITY_NAMES and _lang in USER:
        return USER[_lang]["ethnicity"].get(key) or _pick(("",) + ETHNICITY_NAMES[key], "en")
    if key in ETHNICITY_NAMES and _lang != "de":
        row = ("",) + ETHNICITY_NAMES[key]
        if _lang in LANGS:
            return _pick(row)
        return _extra(_lang).ETHNICITY.get(key) or _pick(row, _base(_lang))
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
    if _lang in USER:
        local = USER[_lang]["personality"].get(key)
        return f"{local} ({en})" if local and local != en else (en or key)
    row = PERSONALITY_NAMES.get(key)
    if not row:
        return en or key
    if _lang in LANGS:
        local = row[LANGS.index(_lang) - 2]
    else:
        local = _extra(_lang).PERSONALITY.get(key) or (
            row[LANGS.index(BASE[_lang]) - 2] if _lang in BASE else en)
    return f"{local} ({en})" if local and local != en else en
