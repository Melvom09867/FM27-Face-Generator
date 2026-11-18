import re
from pathlib import Path

from fm27facegen import i18n
from fm27facegen.backends import BACKENDS
from fm27facegen.country_names import NAMES
from fm27facegen.data import COUNTRIES, ETHNICITIES
from fm27facegen.locales import ETHNICITY_NAMES, OPTIONS, PERSONALITY_NAMES, STRINGS
from fm27facegen.personality import PERSONALITIES, STRENGTHS
from fm27facegen.prompts import (AUTO, BACKGROUNDS, CLOTHING, EXPRESSIONS, FACIAL_HAIR, GENDERS, HAIR_COLORS,
                                 HAIR_STYLES_FEMALE, HAIR_STYLES_MALE, PARENT_MODES, SHIRT_COLORS)

PH = re.compile(r"(?<!\{)\{([a-z_]+)\}(?!\})")


def test_all_strings_have_8_languages_and_same_placeholders():
    for key, row in STRINGS.items():
        assert len(row) == 8 and all(row), key
        if key == "hint.pattern":
            continue  # Dateinamen-Platzhalter, wird nie formatiert
        ref = set(PH.findall(row[0]))
        for text in row:
            assert set(PH.findall(text)) == ref, (key, text)


def test_all_options_translated():
    expected = {
        "hair_color": [k for k in HAIR_COLORS if k != AUTO],
        "hair_style": [k for k in {**HAIR_STYLES_MALE, **HAIR_STYLES_FEMALE} if k != AUTO],
        "facial_hair": [k for k in FACIAL_HAIR if k != AUTO],
        "expression": list(EXPRESSIONS), "clothing": list(CLOTHING),
        "shirt_color": [k for k in SHIRT_COLORS if k != "Zufällig"], "background": list(BACKGROUNDS),
        "gender": list(GENDERS), "parent_mode": list(PARENT_MODES), "strength": list(STRENGTHS),
        "backend": list(BACKENDS),
    }
    for cat, keys in expected.items():
        for k in keys:
            row = OPTIONS[cat].get(k)
            assert row and len(row) == 8 and all(row), (cat, k)
    for row in OPTIONS["_common"].values():
        assert len(row) == 8 and all(row)
    assert set(ETHNICITY_NAMES) == set(ETHNICITIES) and all(len(r) == 7 and all(r) for r in ETHNICITY_NAMES.values())
    assert set(PERSONALITY_NAMES) == set(PERSONALITIES) and all(len(r) == 6 and all(r) for r in PERSONALITY_NAMES.values())
    assert set(NAMES) == set(COUNTRIES) and all(len(r) == 7 and all(r) for r in NAMES.values())


def test_every_used_key_exists():
    src = "\n".join(p.read_text(encoding="utf-8") for p in Path("fm27facegen").glob("*.py"))
    used = set(re.findall(r"\bt\(\s*[\"']([a-z_]+\.[a-z_0-9]+)[\"']", src))
    missing = sorted(k for k in used if k not in STRINGS)
    assert not missing, missing


def test_translation_functions():
    try:
        i18n.set_language("it")
        assert i18n.t("btn.delete") == "Elimina"
        assert i18n.country("Deutschland") == "Germania"
        assert i18n.opt("hair_color", "Schwarz") == "Neri"
        assert i18n.opt("hair_color", "Automatisch") == "Automatico"
        assert i18n.personality("Söldner (Mercenary)") == "Mercenario (Mercenary)"
        assert i18n.ethnicity("AFR_W") == "Africano occidentale"
        assert i18n.t("status.info", pos=1, total=5, msg="x") == "Immagine 1 di 5: x"
        i18n.set_language("en")
        assert i18n.personality("Söldner (Mercenary)") == "Mercenary"
        i18n.set_language("xx")
        assert i18n.get_language() == "de"
        assert i18n.personality("Söldner (Mercenary)") == "Söldner (Mercenary)"
    finally:
        i18n.set_language("de")


def test_import_understands_other_languages():
    from fm27facegen.data import resolve_country
    from fm27facegen.personality import resolve_personality
    from fm27facegen.playerlist import parse_players

    assert resolve_country("Germania") == "Deutschland"
    assert resolve_country("Allemagne") == "Deutschland"
    assert resolve_country("ドイツ") == "Deutschland"
    assert resolve_country("독일") == "Deutschland"
    assert resolve_country("Costa do Marfim") == "Elfenbeinküste"
    assert resolve_personality("Mercenario") == "Söldner (Mercenary)"
    assert resolve_personality("傭兵") == "Söldner (Mercenary)"

    it = "Nome;Età;Nazionalità;Seconda nazionalità;Personalità\nLuca Bianchi;16;Italia;Ghana;Mercenario\n"
    ja = "名前;年齢;国籍;性格\n田中 太郎;15;日本;模範的プロ\n"
    ko = "이름,나이,국적\n김민준,16,대한민국\n"
    p_it = parse_players(it, ".csv")[0][0]
    assert (p_it.name, p_it.age, p_it.country, p_it.country2, p_it.personality) == (
        "Luca Bianchi", 16, "Italien", "Ghana", "Söldner (Mercenary)")
    p_ja = parse_players(ja, ".csv")[0][0]
    assert (p_ja.name, p_ja.age, p_ja.country, p_ja.personality) == ("田中 太郎", 15, "Japan", "Musterprofi (Model Professional)")
    p_ko = parse_players(ko, ".csv")[0][0]
    assert (p_ko.name, p_ko.country) == ("김민준", "Südkorea")
