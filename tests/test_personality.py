from fm27facegen.personality import PERSONALITIES, resolve_personality
from fm27facegen.playerlist import parse_players
from fm27facegen.prompts import FaceOptions, build_prompt

MERC = "Söldner (Mercenary)"


def test_resolve_german_and_english():
    assert resolve_personality("Söldner") == MERC
    assert resolve_personality("mercenary") == MERC
    assert resolve_personality(MERC) == MERC
    assert resolve_personality("Model Citizen") == "Modellbürger (Model Citizen)"
    assert resolve_personality("Ausgeglichen") == "Ausgewogen (Balanced)"
    assert resolve_personality("gibt es nicht") is None


def test_mercenary_gets_tattoo_only_from_min_age():
    tattoos = lambda o: sum("tattoo" in build_prompt(o, seed=s).prompt for s in range(60))
    o = FaceOptions(personality=MERC, personality_strength="Deutlich", age_min=17, age_max=17, tattoo_min_age=16)
    assert tattoos(o) > 30
    o.tattoo_min_age = 18
    assert tattoos(o) == 0
    assert "smirk" in build_prompt(o, seed=1).prompt


def test_all_personalities_build_and_strength():
    for name in PERSONALITIES:
        p = build_prompt(FaceOptions(personality=name, personality_strength="Dezent"), seed=3)
        assert p.meta["persoenlichkeit"] == name and PERSONALITIES[name]["expr"] in p.prompt
    assert build_prompt(FaceOptions(personality="Zufällig"), seed=3).meta["persoenlichkeit"] in PERSONALITIES
    assert build_prompt(FaceOptions(), seed=3).meta["persoenlichkeit"] == ""


def test_aging_keeps_personality_features():
    o = FaceOptions(personality="Zufällig", personality_strength="Deutlich")
    a, b = build_prompt(o, seed=11, age=20), build_prompt(o, seed=11, age=30)
    assert a.meta["persoenlichkeit"] == b.meta["persoenlichkeit"]


def test_list_reads_personality_column():
    txt = "Name;Nation;Alter;Personality\nA B;GER;16;Mercenary\nC D;FRA;15;Ehrgeizig\nE F;ESP;15;\n"
    players, _ = parse_players(txt, ".csv")
    assert [p.personality for p in players] == [MERC, "Ehrgeizig (Ambitious)", None]
