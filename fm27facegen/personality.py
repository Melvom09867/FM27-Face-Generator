"""FM-Persönlichkeiten -> sichtbare Merkmale (Stil, Ausstrahlung, Accessoires).

Jede Persönlichkeit hat
  expr : Gesichtsausdruck (ersetzt den Ausdruck aus den Einstellungen)
  cues : Liste (Merkmal, Gewicht, Flags) – daraus werden je nach Ausprägung 1–3 gezogen
         Flags: "tattoo" = nur ab dem eingestellten Tattoo-Mindestalter, "male" = nur bei Männern

Die Namen sind die offiziellen deutschen FM-Bezeichnungen, die englischen stehen in Klammern
(damit auch englische FM-Exporte erkannt werden).
"""

from __future__ import annotations

import re

NONE = "Keine"
RANDOM = "Zufällig"

_TATTOO_ALT = ["a small silver ear stud", "a thin gold chain necklace", "a sharp hairline lineup"]

# Bausteine
_NEAT = ("neatly groomed, tidy haircut", 3, "")
_NO_INK = ("no tattoos, no jewellery", 2, "")
_CALM = ("calm, composed look", 2, "")
_FOCUS = ("intense focused gaze", 3, "")
_SMIRK = ("slight confident smirk", 2, "")

PERSONALITIES: dict[str, dict] = {
    # Offizielle deutsche FM-Bezeichnungen (Quelle: fm.zweierkette.de/handbuch/persoenlichkeit),
    # alphabetisch; * = gibt es nur bei Newgens
    "Ausgewogen (Balanced)": {
        "expr": "relaxed, neutral expression",
        "cues": [_CALM, ("simple practical haircut", 2, "")]},
    "Belastbar (Resilient)": {
        "expr": "calm, determined expression",
        "cues": [_CALM, ("small old scar on the eyebrow", 1, ""), _FOCUS]},
    "Charismatischer Führer (Charismatic Leader)": {
        "expr": "charismatic, confident smile",
        "cues": [("strong confident posture", 2, ""), ("stylish neat haircut", 2, ""), ("bright engaging eyes", 2, "")]},
    "Ehrgeizig (Ambitious)": {
        "expr": "confident, determined expression",
        "cues": [("sharp modern haircut", 3, ""), ("a small diamond ear stud", 2, ""), _SMIRK]},
    "Ehrlich (Honest)": {
        "expr": "open, friendly expression",
        "cues": [_NEAT, ("open honest face", 2, "")]},
    "Energisch (Spirited)": {
        "expr": "lively, energetic grin",
        "cues": [("bright lively eyes", 2, ""), ("slightly messy textured hair", 2, "")]},
    "Erfolgshungrig (Driven)": {
        "expr": "fierce, hungry, determined expression",
        "cues": [_FOCUS, ("sharp modern haircut", 2, ""), ("lean athletic face", 2, "")]},
    "Fair (Sporting)": {
        "expr": "friendly, respectful expression",
        "cues": [_NEAT, ("open friendly face", 2, "")]},
    "Frohnatur (Jovial)": {
        "expr": "big warm friendly smile",
        "cues": [("cheerful twinkling eyes", 3, ""), ("laugh lines", 1, "")]},
    "Führungspersönlichkeit (Leader)": {
        "expr": "confident, composed expression",
        "cues": [("confident posture", 2, ""), _CALM]},
    "Geringes Selbstvertrauen (Low Self-Belief)": {
        "expr": "shy, uncertain expression",
        "cues": [("slightly hunched shoulders", 2, ""), ("nervous look", 2, "")]},
    "Hingebungsvoll (Devoted)": {
        "expr": "warm, sincere expression",
        "cues": [("modest, down-to-earth look", 2, ""), _CALM]},
    "Konsequent (Resolute)": {
        "expr": "determined, steady expression",
        "cues": [("strong set jaw", 2, ""), _FOCUS, _NEAT]},
    "Lässig (Casual)": {
        "expr": "relaxed, slightly bored expression",
        "cues": [("messy unkempt hair", 3, ""), ("half-closed sleepy eyes", 1, ""), ("slightly wrinkled shirt", 2, "")]},
    "Loyal (Loyal)": {
        "expr": "warm, modest expression",
        "cues": [("modest, down-to-earth look", 2, ""), _NEAT]},
    "Modellbürger (Model Citizen)": {
        "expr": "warm, friendly, trustworthy expression",
        "cues": [_NEAT, _NO_INK, ("clean, well-rested look", 2, "")]},
    "Musterprofi (Model Professional)": {
        "expr": "calm, serious, professional expression",
        "cues": [_NEAT, _NO_INK, ("athletic, disciplined look", 3, "")]},
    "Nachlässig (Slack)": {
        "expr": "disinterested, lazy expression",
        "cues": [("messy unkempt hair", 3, ""), ("tired eyes with dark circles", 2, ""), ("slightly wrinkled shirt", 2, "")]},
    "Natürliche Autorität (Born Leader)": {
        "expr": "confident, commanding expression",
        "cues": [("strong confident posture, chin slightly raised", 3, ""), _CALM, _NEAT]},
    "Ohne Ehrgeiz (Unambitious)": {
        "expr": "indifferent, relaxed expression",
        "cues": [("messy hair", 2, ""), ("relaxed slouching posture", 2, "")]},
    "Opportunist (Fickle)": {
        "expr": "smug, aloof expression",
        "cues": [("trendy bleached dyed hair", 2, ""), ("diamond stud earrings", 2, ""),
                 ("a small tattoo below the ear", 2, "tattoo"), ("a thin gold chain necklace", 1, "")]},
    "Perfektionist (Perfectionist)": {
        "expr": "intense, serious expression",
        "cues": [("immaculately groomed, perfectly styled hair", 3, ""), ("neatly shaped eyebrows", 2, ""), _FOCUS]},
    "Professionell (Professional)": {
        "expr": "serious, focused expression",
        "cues": [_NEAT, ("disciplined athletic look", 2, ""), _CALM]},
    "Realist (Realist)": {
        "expr": "neutral, matter-of-fact expression",
        "cues": [_CALM, ("simple practical haircut", 2, "")]},
    "Relativ ehrgeizig (Fairly Ambitious)": {
        "expr": "confident expression",
        "cues": [("modern haircut", 2, ""), _SMIRK]},
    "Relativ fair (Fairly Sporting)": {
        "expr": "friendly, open expression",
        "cues": [_NEAT, ("open friendly face", 1, "")]},
    "Relativ loyal (Fairly Loyal)": {
        "expr": "warm, modest expression",
        "cues": [("modest, down-to-earth look", 2, ""), _NEAT]},
    "Relativ professionell (Fairly Professional)": {
        "expr": "neutral, focused expression",
        "cues": [_NEAT, _CALM]},
    "Relativ zielstrebig (Fairly Determined)": {
        "expr": "determined expression",
        "cues": [_FOCUS, _NEAT]},
    "Rückgratlos (Spineless)": {
        "expr": "timid, insecure expression",
        "cues": [("slightly hunched shoulders", 2, ""), ("nervous look", 3, "")]},
    "Schnell entmutigt (Easily Discouraged)": {
        "expr": "uncertain, slightly worried expression",
        "cues": [("nervous look", 2, ""), ("tired eyes", 1, "")]},
    "Sehr ehrgeizig (Very Ambitious)": {
        "expr": "confident, self-assured expression",
        "cues": [("stylish fashionable haircut", 3, ""), ("a small diamond ear stud", 2, ""), _SMIRK,
                 ("a small tattoo on the side of the neck", 1, "tattoo")]},
    "Sehr loyal (Very Loyal)": {
        "expr": "warm, humble smile",
        "cues": [("modest, down-to-earth look", 3, ""), _NEAT]},
    "Söldner (Mercenary)": {
        "expr": "cocky, self-assured smirk",
        "cues": [("a visible tattoo on the side of the neck", 4, "tattoo"), ("a thin gold chain necklace", 3, ""),
                 ("diamond stud earrings", 3, ""), ("sharp designer haircut with crisp lineup", 2, ""),
                 ("a shaved line in the eyebrow", 1, "")]},
    "Temperamentvoll (Temperamental)": {
        "expr": "intense, slightly scowling expression",
        "cues": [("furrowed brow", 3, ""), ("tense jaw", 2, ""), ("small scar on the eyebrow", 1, ""),
                 ("a tattoo on the side of the neck", 1, "tattoo")]},
    "Unbeschwert (Light-Hearted)": {
        "expr": "easygoing cheerful smile",
        "cues": [("relaxed happy look", 2, ""), ("slightly messy hair", 2, "")]},
    "Unentschlossen (Low Determination)": {
        "expr": "hesitant, unsure expression",
        "cues": [("slightly messy hair", 2, ""), ("nervous look", 2, "")]},
    "Unsportlich (Unsporting)": {
        "expr": "smug, provocative smirk",
        "cues": [("a shaved line in the eyebrow", 2, ""), ("a tattoo on the side of the neck", 2, "tattoo"),
                 ("a gold chain necklace", 2, "")]},
    "Willensstark (Iron Willed)": {
        "expr": "stern, unshakable expression",
        "cues": [_FOCUS, ("strong set jaw", 3, ""), ("short practical haircut", 2, "")]},
    "Zielstrebig (Determined)": {
        "expr": "determined, serious expression",
        "cues": [_FOCUS, ("strong set jaw", 2, "")]},
}

# Ältere bzw. alternative Bezeichnungen (frühere FM-Versionen, Übersetzungsvarianten)
ALIASES = {
    "Ausgeglichen": "Ausgewogen (Balanced)",
    "Unbeständig": "Opportunist (Fickle)",
    "Low Self Belief": "Geringes Selbstvertrauen (Low Self-Belief)",
    "Professionell": "Professionell (Professional)",
    "Professionel": "Professionell (Professional)",
}

STRENGTHS = {"Dezent": 1, "Normal": 2, "Deutlich": 3}


def personality_names() -> list[str]:
    return [NONE, RANDOM] + list(PERSONALITIES)


def _norm(text: str) -> str:
    from .data import norm_text
    return norm_text(text)


def resolve_personality(raw: str) -> str | None:
    """'Mercenary', 'Söldner' oder 'Söldner (Mercenary)' -> Schlüssel in PERSONALITIES."""
    key = _norm(raw or "")
    if not key:
        return None
    for name in PERSONALITIES:
        de, _, en = name.partition(" (")
        if key in (_norm(name), _norm(de), _norm(en.rstrip(")"))):
            return name
    for alias, name in ALIASES.items():
        if key == _norm(alias):
            return name
    from .locales import PERSONALITY_NAMES  # übersetzte Namen (it, fr, es, pt, ja, ko)
    for name, row in PERSONALITY_NAMES.items():
        if any(key == _norm(local) for local in row):
            return name
    return None


def personality_features(name: str, gender: str, age: int, tattoo_min_age: int,
                         strength: int, randoms: list[float]) -> tuple[str | None, list[str]]:
    """Gibt (Ausdruck, Merkmale) zurück. ``randoms`` = feste Anzahl Zufallszahlen (Reproduzierbarkeit)."""
    p = PERSONALITIES.get(name)
    if not p:
        return None, []
    scored = []
    for i, (text, weight, flags) in enumerate(p["cues"]):
        if "male" in flags and gender != "male":
            continue
        if "tattoo" in flags and age < tattoo_min_age:
            text = _TATTOO_ALT[i % len(_TATTOO_ALT)]
        r = randoms[i % len(randoms)]
        scored.append((r ** (1.0 / weight), text))  # gewichtete Auswahl ohne Zurücklegen
    scored.sort(reverse=True)
    picked: list[str] = []
    for _, text in scored:
        if text not in picked:
            picked.append(text)
        if len(picked) >= strength:
            break
    return p["expr"], picked
