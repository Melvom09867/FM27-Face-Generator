"""Erzeugt aus den Einstellungen einen Bild-Prompt (zufällig, aber reproduzierbar per Seed)."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from .data import COUNTRIES, ETHNICITIES
from .personality import NONE as NO_PERSONALITY, PERSONALITIES, RANDOM as RANDOM_PERSONALITY, STRENGTHS, personality_features

AUTO = "Automatisch"

# Auswahl in der Oberfläche (Deutsch) -> Prompt-Text (Englisch)
HAIR_COLORS = {
    AUTO: None,
    "Schwarz": "black",
    "Dunkelbraun": "dark brown",
    "Braun": "brown",
    "Hellbraun": "light brown",
    "Blond": "blonde",
    "Rot": "red",
    "Blondiert / gefärbt": "bleached platinum blonde dyed",
}

HAIR_STYLES_MALE = {
    AUTO: None,
    "Kurz & ordentlich": "short neat haircut",
    "Buzzcut": "buzz cut",
    "Fade": "skin fade haircut with short textured top",
    "Mittellang / zerzaust": "messy medium-length hair",
    "Mittelscheitel": "curtain haircut with middle part",
    "Locken": "short curly hair",
    "Afro": "short afro",
    "Cornrows / Braids": "cornrows",
    "Twists / Dreads": "short twists",
    "Lang mit Dutt": "long hair tied in a man bun",
}

HAIR_STYLES_FEMALE = {
    AUTO: None,
    "Pferdeschwanz": "hair tied back in a ponytail",
    "Dutt": "hair in a tight bun",
    "Kurz / Pixie": "short pixie cut",
    "Schulterlang": "shoulder-length hair tucked behind the ears",
    "Geflochten": "braided hair",
    "Locken zurückgebunden": "curly hair tied back",
    "Box Braids": "box braids tied back",
}

FACIAL_HAIR = {
    AUTO: None,
    "Glattrasiert": "clean-shaven",
    "Leichter Bartschatten": "light stubble",
    "Dreitagebart": "short stubble beard",
    "Kurzer Vollbart": "short trimmed full beard",
    "Schnurrbart-Flaum": "faint teenage moustache fuzz",
}

EXPRESSIONS = {
    "Neutral (Passfoto)": "neutral serious expression",
    "Leichtes Lächeln": "slight closed-mouth smile",
    "Lächeln": "friendly smile",
    "Gemischt (zufällig)": None,
}

CLOTHING = {
    "Schlichtes T-Shirt": "a plain {color} crew-neck t-shirt",
    "Trainingsshirt": "a plain {color} sports training top",
    "Trikot ohne Logo": "a plain {color} football jersey without logos or text",
    "Polo-Shirt": "a plain {color} polo shirt",
}

# Trikot-Muster: Schlüssel -> Art (None = einfarbig, Beschreibung wie bisher)
SHIRT_PATTERNS = {
    "Einfarbig": None,
    "Längsstreifen": "stripes",
    "Querstreifen": "hoops",
    "Andersfarbige Ärmel": "sleeves",
    "Andersfarbiger Kragen": "collar",
}
_GARMENT_NOUNS = {
    "Schlichtes T-Shirt": "crew-neck t-shirt",
    "Trainingsshirt": "sports training top",
    "Trikot ohne Logo": "football jersey",
    "Polo-Shirt": "polo shirt",
}

SHIRT_COLORS = {
    "Zufällig": None,
    "Weiß": "white",
    "Schwarz": "black",
    "Grau": "grey",
    "Dunkelblau": "navy blue",
    "Hellblau": "light blue",
    "Rot": "red",
    "Grün": "green",
    "Gelb": "yellow",
    "Orange": "orange",
    "Lila": "purple",
    "Bordeaux": "maroon",
}

BACKGROUNDS = {
    "Transparent (FM-Cut-out)": "plain uniform light grey background",
    "Hellgrau (Studio)": "plain uniform light grey studio background",
    "Weiß": "plain uniform white studio background",
    "Dunkelgrau": "plain uniform dark grey studio background",
}
TRANSPARENT_BG = "Transparent (FM-Cut-out)"

GENDERS = {"Männlich": "male", "Weiblich": "female"}

NO_SECOND = "—"
PARENT_MODES = {
    "Beide Eltern aus diesem Land": "both",
    "Ein Elternteil (gemischt)": "one",
    "Zufällig": "random",
}

NEGATIVE_PROMPT = (
    "cartoon, anime, illustration, painting, drawing, 3d render, cgi, doll, plastic skin, "
    "airbrushed, beauty filter, makeup, deformed, distorted face, asymmetrical eyes, extra limbs, "
    "hands, blurry, out of focus, low quality, jpeg artifacts, text, watermark, logo, signature, "
    "frame, border, sunglasses, glasses, hat, cap, headphones, multiple people, cropped head, "
    "tilted head, profile view, busy background"
)

_STYLE_POOLS_MALE = {
    "straight": ["short neat side-parted haircut", "short textured crop", "buzz cut",
                 "skin fade haircut with short textured top", "messy medium-length hair",
                 "curtain haircut with middle part", "undercut with slicked back top", "short spiky hair"],
    "wavy": ["short wavy hair", "messy medium-length wavy hair", "curtain haircut with middle part",
             "skin fade haircut with wavy top", "short textured crop", "buzz cut"],
    "curly": ["short curly hair", "curly top with low fade", "medium-length curly hair", "buzz cut",
              "tight curls with taper fade"],
    "coily": ["short afro", "high-top fade", "buzz cut", "short twists", "cornrows",
              "low cut with waves", "short dreadlocks", "taper fade with short coily top"],
}
_STYLE_POOLS_FEMALE = {
    "straight": ["hair tied back in a ponytail", "hair in a tight bun", "shoulder-length hair tucked behind the ears",
                 "short pixie cut", "french braid", "short bob haircut"],
    "wavy": ["wavy hair tied back in a ponytail", "messy bun", "shoulder-length wavy hair", "french braid"],
    "curly": ["curly hair tied back in a ponytail", "curly bun", "shoulder-length curly hair"],
    "coily": ["box braids tied back", "afro puff", "cornrows", "short natural afro", "braided bun"],
}

_SKIN_TEEN = ["a few mild acne spots", "slightly oily teenage skin", "a small blemish on the chin"]
_SKIN_ANY = ["a small mole on the cheek", "slight under-eye shadows", "faint scar on the eyebrow"]


@dataclass
class FaceOptions:
    country: str = "Deutschland"
    ethnicity: str = AUTO           # AUTO oder Schlüssel aus ETHNICITIES
    second_country: str = NO_SECOND  # Herkunft der Eltern (optional)
    parent_mode: str = "Zufällig"
    gender: str = "Männlich"
    age_min: int = 15
    age_max: int = 17
    hair_color: str = AUTO
    hair_style: str = AUTO
    facial_hair: str = AUTO
    expression: str = "Neutral (Passfoto)"
    clothing: str = "Trainingsshirt"
    shirt_color: str = "Zufällig"
    shirt_color2: str = "Zufällig"   # Zweitfarbe (nur bei Mustern)
    shirt_pattern: str = "Einfarbig"
    background: str = TRANSPARENT_BG
    skin_details: bool = True
    extra_prompt: str = ""
    personality: str = NO_PERSONALITY
    personality_strength: str = "Normal"
    tattoo_min_age: int = 16
    # Fremde Bilder: aus dem Bild erkannte Haare/Merkmale (ersetzt die gewürfelten Haare)
    hair_text: str = ""
    look_text: str = ""


@dataclass
class FacePrompt:
    prompt: str
    negative: str
    seed: int
    meta: dict = field(default_factory=dict)


# Hinweis zur Reproduzierbarkeit: Jeder Zufallswert wird IMMER gezogen (auch wenn er nicht
# gebraucht wird) und nur über rng.random() – so liefert derselbe Seed bei einem anderen Alter
# exakt dieselben übrigen Merkmale. Das ist die Grundlage für die Alterungs-Sets.

def _weighted(rng: random.Random, weights: dict[str, float]) -> str:
    keys = list(weights)
    total = float(sum(weights.values())) or 1.0
    x = rng.random() * total
    for k in keys:
        x -= weights[k]
        if x < 0:
            return k
    return keys[-1]


def _pick(rng: random.Random, items: list[str]) -> str:
    return items[min(int(rng.random() * len(items)), len(items) - 1)]


def _merge(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    ta, tb = sum(a.values()) or 1, sum(b.values()) or 1
    out: dict[str, float] = {}
    for d, t in ((a, ta), (b, tb)):
        for k, v in d.items():
            out[k] = out.get(k, 0) + v / t
    return out


def ethnicity_label(key: str) -> str:
    return ETHNICITIES[key]["label"] if key in ETHNICITIES else key


def ethnicity_key_from_label(label: str) -> str:
    if label == AUTO:
        return AUTO
    for key, eth in ETHNICITIES.items():
        if eth["label"] == label:
            return key
    return label if label in ETHNICITIES else AUTO


def _dominant(mix: dict[str, float]) -> str:
    pure = {k: v for k, v in mix.items() if k != "MIXED"} or mix
    return max(pure, key=pure.get)


def _heritage(key: str) -> str:
    return ETHNICITIES[key]["prompt"].split(",")[0]


def _age_phrase(age: int, gender: str) -> str:
    if gender == "female":
        noun = "teenage girl" if age <= 17 else ("young woman" if age <= 23 else "woman")
    else:
        noun = "teenage boy" if age <= 17 else ("young man" if age <= 23 else "man")
    return f"{age}-year-old {noun}"


def _age_features(age: int, gender: str) -> list[str]:
    if age <= 17:
        return ["youthful face"]
    if age <= 24:
        return []
    if age <= 29:
        return ["adult face"]
    if age <= 33:
        return ["mature adult face", "fine lines around the eyes"]
    if age <= 37:
        return ["mature face", "visible crow's feet", "first grey hairs at the temples" if gender == "male" else "fine wrinkles"]
    return ["weathered mature face", "forehead wrinkles", "greying hair at the temples"]


def _facial_hair_pool(age: int) -> dict[str, int]:
    if age <= 15:
        return {"clean-shaven, smooth youthful face": 85, "faint teenage moustache fuzz": 15}
    if age <= 17:
        return {"clean-shaven": 60, "faint teenage moustache fuzz": 25, "very light patchy stubble": 15}
    if age <= 21:
        return {"clean-shaven": 45, "light stubble": 35, "short stubble beard": 15, "thin moustache": 5}
    return {"clean-shaven": 30, "light stubble": 30, "short stubble beard": 25, "short trimmed full beard": 15}


_GENERIC = {"texture": {"straight": 40, "wavy": 30, "curly": 15, "coily": 15},
            "hair": {"black": 45, "dark brown": 35, "brown": 15, "light brown": 5}, "freckles": 0.02}


def build_prompt(opts: FaceOptions, seed: int | None = None, age: int | None = None) -> FacePrompt:
    """Erzeugt einen Prompt. Gleiche Optionen + gleicher Seed = gleiche Person.

    ``age`` überschreibt das Alter, alle anderen Merkmale bleiben gleich (Alterungs-Set).
    """
    if seed is None:
        seed = random.randint(1, 2**31 - 1)
    rng = random.Random(seed)
    gender = GENDERS.get(opts.gender, "male")

    # --- Herkunft -----------------------------------------------------------------------
    known = opts.country in COUNTRIES
    country_en, mix1 = COUNTRIES.get(opts.country, (opts.country, {"EUR_W": 1}))
    second = opts.second_country if opts.second_country in COUNTRIES and opts.second_country != opts.country else None
    mix2 = COUNTRIES[second][1] if second else mix1
    draw1, draw2 = _weighted(rng, mix1), _weighted(rng, mix2)
    mode = PARENT_MODES.get(opts.parent_mode, "random")
    coin = rng.random()
    if mode == "random":
        mode = "both" if coin < 0.5 else "one"

    role = "youth footballer" if (age if age is not None else opts.age_max) <= 21 else "professional footballer"
    origin = f"{role} from {country_en}"
    if opts.ethnicity in ETHNICITIES:
        eth_keys = [opts.ethnicity]
    elif second and mode == "both":
        eth_keys = [draw2]
    elif second:
        # ein Elternteil aus dem Geburtsland (dort übliche Herkunft), einer aus dem zweiten Land
        p1, p2 = _dominant(mix1), (draw2 if draw2 != "MIXED" else _dominant(mix2))
        eth_keys = [p1] if p1 == p2 else [p1, p2]
    elif known:
        eth_keys = [draw1]
    else:
        eth_keys = []  # unbekanntes Land: die KI entscheidet anhand des Ländernamens
    if second:
        roots = second if mode == "both" else f"{opts.country} and {second}"
        roots_en = COUNTRIES[second][0] if mode == "both" else f"{country_en} and {COUNTRIES[second][0]}"
        origin += f", family roots in {roots_en}"
    else:
        roots = opts.country

    if len(eth_keys) == 2:
        e1, e2 = (ETHNICITIES[k] for k in eth_keys)
        eth_text = f"mixed-heritage, half {_heritage(eth_keys[0])} and half {_heritage(eth_keys[1])}"
        texture_w, hair_w = _merge(e1["texture"], e2["texture"]), _merge(e1["hair"], e2["hair"])
        freckles = (e1["freckles"] + e2["freckles"]) / 2
        eth_label = f"{e1['label']} + {e2['label']}"
    elif eth_keys:
        e = ETHNICITIES[eth_keys[0]]
        eth_text, texture_w, hair_w, freckles, eth_label = e["prompt"], e["texture"], e["hair"], e["freckles"], e["label"]
    else:
        eth_text, texture_w, hair_w, freckles, eth_label = "", _GENERIC["texture"], _GENERIC["hair"], 0.02, "durch KI"

    # --- Alter -------------------------------------------------------------------------
    lo, hi = sorted((int(opts.age_min), int(opts.age_max)))
    drawn_age = lo + min(int(rng.random() * (hi - lo + 1)), hi - lo)
    age = int(age) if age is not None else drawn_age

    # --- Haare -------------------------------------------------------------------------
    texture = _weighted(rng, texture_w)
    drawn_color = _weighted(rng, hair_w)
    hair_color = HAIR_COLORS.get(opts.hair_color) or drawn_color
    pools = _STYLE_POOLS_FEMALE if gender == "female" else _STYLE_POOLS_MALE
    drawn_style = _pick(rng, pools[texture])
    style_map = HAIR_STYLES_FEMALE if gender == "female" else HAIR_STYLES_MALE
    hair_style = style_map.get(opts.hair_style) or drawn_style
    hair = f"{hair_color} hair, {hair_style}"
    if opts.hair_text.strip():
        hair = opts.hair_text.strip()

    # --- Gesicht -----------------------------------------------------------------------
    parts_face: list[str] = list(_age_features(age, gender))
    if opts.look_text.strip():
        parts_face.insert(0, opts.look_text.strip())
    fh_roll = rng.random()
    if gender == "male":
        fixed = FACIAL_HAIR.get(opts.facial_hair)
        if fixed:
            parts_face.append(fixed)
        else:
            pool = _facial_hair_pool(age)
            total = sum(pool.values())
            x = fh_roll * total
            for k, w in pool.items():
                x -= w
                if x < 0:
                    parts_face.append(k)
                    break

    r_freckle, r_teen, r_teen_pick, r_any, r_any_pick = (rng.random() for _ in range(5))
    if opts.skin_details:
        if r_freckle < freckles:
            parts_face.append("light freckles")
        if age <= 18 and r_teen < 0.3:
            parts_face.append(_SKIN_TEEN[min(int(r_teen_pick * len(_SKIN_TEEN)), len(_SKIN_TEEN) - 1)])
        if r_any < 0.15:
            parts_face.append(_SKIN_ANY[min(int(r_any_pick * len(_SKIN_ANY)), len(_SKIN_ANY) - 1)])

    expr_pool = [v for v in EXPRESSIONS.values() if v]
    drawn_expr = _pick(rng, expr_pool)
    expression = EXPRESSIONS.get(opts.expression) or drawn_expr

    color_pool = [v for v in SHIRT_COLORS.values() if v]
    drawn_color_shirt = _pick(rng, color_pool)
    color = SHIRT_COLORS.get(opts.shirt_color) or drawn_color_shirt
    clothing = CLOTHING.get(opts.clothing, CLOTHING["Schlichtes T-Shirt"]).format(color=color)

    # --- Persönlichkeit (immer gleiche Anzahl Zufallszahlen ziehen -> Alterungs-Sets bleiben stabil)
    r_pers = rng.random()
    pers_randoms = [rng.random() for _ in range(8)]
    personality = opts.personality
    if personality == RANDOM_PERSONALITY:
        names = list(PERSONALITIES)
        personality = names[min(int(r_pers * len(names)), len(names) - 1)]
    pers_expr, pers_cues = personality_features(
        personality, gender, age, int(opts.tattoo_min_age), STRENGTHS.get(opts.personality_strength, 2), pers_randoms)
    if pers_expr:
        expression = pers_expr
    background = BACKGROUNDS.get(opts.background, BACKGROUNDS["Hellgrau (Studio)"])

    # --- Trikot-Muster mit Zweitfarbe. Neue Zufallszahl erst NACH allen bisherigen ziehen und einfarbig
    # exakt wie bisher beschreiben -> ältere Bilder bleiben beim Alterungs-Set reproduzierbar.
    r_color2 = rng.random()
    pattern = SHIRT_PATTERNS.get(opts.shirt_pattern)
    if pattern:
        others = [c for c in color_pool if c != color]
        color2 = SHIRT_COLORS.get(opts.shirt_color2) or others[min(int(r_color2 * len(others)), len(others) - 1)]
        noun = _GARMENT_NOUNS.get(opts.clothing, _GARMENT_NOUNS["Schlichtes T-Shirt"])
        clothing = {
            "stripes": f"a {color} and {color2} vertically striped {noun}",
            "hoops": f"a {color} and {color2} horizontally hooped {noun}",
            "sleeves": f"a {color} {noun} with contrasting {color2} sleeves",
            "collar": f"a {color} {noun} with a contrasting {color2} collar",
        }[pattern]
        if opts.clothing == "Trikot ohne Logo":
            clothing += ", no logos or text"

    who = ", ".join(x for x in (_age_phrase(age, gender), eth_text, origin) if x)
    # Kurz halten: Bild-KIs gewichten den Anfang stärker, lange Prompts "verwässern" Details
    segments = [
        "football club media day headshot photo of a " + who,
        *pers_cues,
        hair,
        *parts_face,
        expression,
        "facing the camera, centered, entire head and hair visible with empty space above the head, "
        "neck and shirt collar visible",
        f"wearing {clothing}",
        background,
        "bright soft even lighting, sharp focus, natural skin texture, realistic photo",
    ]
    if opts.extra_prompt.strip():
        segments.append(opts.extra_prompt.strip())

    prompt = ", ".join(s for s in segments if s)
    meta = {
        "seed": seed,
        "land": opts.country,
        "herkunft": roots,
        "ethnie": eth_label,
        "ethnie_key": "+".join(eth_keys) or "KI",
        "geschlecht": opts.gender,
        "alter": age,
        "haare": hair,
        "persoenlichkeit": personality if personality in PERSONALITIES else "",
    }
    return FacePrompt(prompt=prompt, negative=NEGATIVE_PROMPT, seed=seed, meta=meta)


# ---------------------------------------------------------------------------
# Alter in einer bereits vorhandenen Beschreibung austauschen (für Bilder, zu denen nur die
# Beschreibung aus generiert.csv bekannt ist – z. B. aus älteren Programmversionen)
# ---------------------------------------------------------------------------
_AGE_RE = re.compile(r"\b(\d{1,2})-year-old (teenage boy|young man|man|teenage girl|young woman|woman)\b")
_ROLE_RE = re.compile(r"\b(youth academy football player|professional football player|youth footballer|"
                      r"professional footballer)\b")
_ALL_AGE_FEATURES = {f for a in range(14, 46) for g in ("male", "female") for f in _age_features(a, g)}
_YOUNG_FACIAL_HAIR = ("clean-shaven, smooth youthful face", "faint teenage moustache fuzz", "very light patchy stubble")


def reage_prompt(prompt: str, age: int, gender_key: str = "Männlich") -> str:
    """Ersetzt Altersangabe und altersabhängige Merkmale in einer fertigen Beschreibung."""
    gender = GENDERS.get(gender_key, "male")
    text = _AGE_RE.sub(_age_phrase(age, gender), prompt, count=1)
    role = "youth footballer" if age <= 21 else "professional footballer"
    text = _ROLE_RE.sub(role, text, count=1)
    parts = [p for p in text.split(", ") if p not in _ALL_AGE_FEATURES]
    if age >= 20:  # Teenager-Flaum passt nicht mehr
        parts = ["clean-shaven" if p in _YOUNG_FACIAL_HAIR else p for p in parts]
    insert_at = next((i + 1 for i, p in enumerate(parts) if "footballer" in p or "football player" in p), 1)
    return ", ".join(parts[:insert_at] + _age_features(age, gender) + parts[insert_at:])
