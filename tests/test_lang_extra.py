"""Zusätzliche Sprachen (fm27facegen/lang/*.py): vollständig, gleiche Platzhalter, alles übersetzt."""

import importlib
import re

import pytest

from fm27facegen import i18n
from fm27facegen.country_names_extra import NAMES as COUNTRY_EXTRA
from fm27facegen.data import COUNTRIES
from fm27facegen.locales import ETHNICITY_NAMES, OPTIONS, PERSONALITY_NAMES, STRINGS

PH = re.compile(r"(?<!\{)\{([a-z_]+)\}(?!\})")
FULL = [c for c in i18n.EXTRA if c not in i18n.BASE]


def _mod(code):
    return importlib.import_module(f"fm27facegen.lang.{code.replace('-', '_').lower()}")


@pytest.mark.parametrize("code", i18n.EXTRA)
def test_language_file(code):
    m = _mod(code)
    full = code not in i18n.BASE
    keys = set(STRINGS)
    assert not set(m.STRINGS) - keys, (code, sorted(set(m.STRINGS) - keys))
    if full:
        assert set(m.STRINGS) == keys, (code, sorted(keys - set(m.STRINGS)))
        opt_keys = {f"{c}|{k}" for c, d in OPTIONS.items() for k in d}
        assert set(m.OPTIONS) == opt_keys, (code, sorted(opt_keys ^ set(m.OPTIONS)))
        assert set(m.ETHNICITY) == set(ETHNICITY_NAMES)
        assert set(m.PERSONALITY) == set(PERSONALITY_NAMES)
        assert set(COUNTRY_EXTRA[code]) == set(COUNTRIES)
    for key, text in m.STRINGS.items():
        assert text.strip(), (code, key)
        if key != "hint.pattern":
            assert set(PH.findall(text)) == set(PH.findall(STRINGS[key][0])), (code, key, text)
    for d in (m.OPTIONS, m.ETHNICITY, m.PERSONALITY):
        assert all(v.strip() for v in d.values())


def test_all_languages_selectable_and_marked():
    assert len(i18n.LANGUAGES) == 20 and set(i18n.EXTRA) <= set(i18n.LANGUAGES)
    assert i18n.language_label("de") == "Deutsch"
    assert i18n.language_label("nl") == "Nederlands (AI-vertaald)"
    assert i18n.language_label("en") == "English (AI-translated)"
    try:
        i18n.set_language("nl")
        assert i18n.t("btn.delete") == "Verwijderen"
        assert i18n.country("Deutschland") == "Duitsland"
        assert i18n.opt("hair_color", "Schwarz") == "Zwart"
        assert i18n.opt("hair_color", "Automatisch") == "Automatisch"
        assert i18n.personality("Söldner (Mercenary)") == "Huurling (Mercenary)"
        assert i18n.ethnicity("AFR_W") == "West-Afrikaans"
        i18n.set_language("es-419")
        assert i18n.country("Deutschland") == "Alemania"
        assert i18n.t("btn.delete")  # fällt auf Spanisch zurück
    finally:
        i18n.set_language("de")
