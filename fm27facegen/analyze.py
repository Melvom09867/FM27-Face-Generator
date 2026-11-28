"""Fremde Bilder (nicht vom Generator) für die Alterung vorbereiten.

Fakten (Alter, Nationalität, 2. Nationalität, Persönlichkeit) kommen aus dem FM-Export – die kann man
einem Gesicht nicht ansehen. Aus dem Bild selbst kommen Geschlecht, Haare/Merkmale (Bildbeschreibung von
Forge) und der Hautton (gemessen). Alter nur als Schätzung, wenn der Spieler nicht im Export steht.
"""
from __future__ import annotations

import copy
import math
import random
import re
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from .prompts import AUTO, NO_SECOND, FaceOptions

try:
    import cv2
except Exception:  # noqa: BLE001
    cv2 = None

# Quelle einer Angabe – wird im Bestätigungsfenster angezeigt
SRC_FM, SRC_IMAGE, SRC_GUESS, SRC_SETTINGS = "fm", "image", "guess", "settings"


@dataclass
class Analysis:
    age: int = 18
    gender: str = "Männlich"
    country: str = ""
    country2: str = NO_SECOND
    personality: str | None = None
    hair: str = ""              # z. B. "curly black hair with blonde tips"
    look: str = ""              # z. B. "olive tan skin, thick dark eyebrows"
    caption: str = ""           # Rohtext der Bildbeschreibung (zur Info)
    src: dict = field(default_factory=dict)  # Feld -> SRC_*


# ---------------------------------------------------------------------------
# Bildausschnitt: quadratisch um das Gesicht (img2img verzerrt sonst Hochformat-Fotos)
# ---------------------------------------------------------------------------
def prepare_base(img: Image.Image) -> Image.Image:
    from .generator import as_init_image
    from .imaging import detect_face
    rgb = as_init_image(img)
    w, h = rgb.size
    face = detect_face(rgb)
    if face is None:
        side = min(w, h)
        cx, cy = w / 2, h / 2
    else:
        fx, fy, fw, fh = face
        side = min(max(fw, fh) * 2.6, max(w, h))
        cx, cy = fx + fw / 2, fy + fh / 2 + fh * 0.12
    half = side / 2
    box = [int(round(cx - half)), int(round(cy - half)), int(round(cx + half)), int(round(cy + half))]
    # Ränder außerhalb des Bildes mit den Randpixeln auffüllen (keine schwarzen Balken)
    pad = max(0, -box[0], -box[1], box[2] - w, box[3] - h)
    if pad:
        arr = np.pad(np.asarray(rgb), ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        rgb = Image.fromarray(arr)
        box = [b + pad for b in box]
    return rgb.crop(tuple(box))


# ---------------------------------------------------------------------------
# Hautton messen (ITA-Winkel im Lab-Farbraum, Wangen/Stirn ohne Augen und Mund)
# ---------------------------------------------------------------------------
SKIN_TEXTS = [(55, "very fair skin"), (41, "fair skin"), (28, "light olive skin"), (10, "olive tan skin"),
              (-30, "brown skin"), (-999, "dark brown skin")]


def skin_tone(img: Image.Image) -> str:
    from .imaging import detect_face
    if cv2 is None:
        return ""
    rgb = as_rgb = img.convert("RGB")
    face = detect_face(as_rgb)
    if face is None:
        return ""
    fx, fy, fw, fh = face
    arr = np.asarray(rgb)
    patches = [arr[fy + int(fh * 0.50): fy + int(fh * 0.68), fx + int(fw * 0.15): fx + int(fw * 0.35)],
               arr[fy + int(fh * 0.50): fy + int(fh * 0.68), fx + int(fw * 0.65): fx + int(fw * 0.85)],
               arr[fy + int(fh * 0.12): fy + int(fh * 0.25), fx + int(fw * 0.35): fx + int(fw * 0.65)]]
    px = np.concatenate([p.reshape(-1, 3) for p in patches if p.size])
    if len(px) < 30:
        return ""
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(float)
    L = np.median(lab[:, 0]) * 100 / 255
    b = np.median(lab[:, 2]) - 128
    ita = math.degrees(math.atan2(L - 50, b if abs(b) > 1e-3 else 1e-3))
    return next(text for limit, text in SKIN_TEXTS if ita > limit)


# ---------------------------------------------------------------------------
# Bildbeschreibung (Forge: CLIP-Text und, falls vorhanden, DeepBooru-Stichworte) auswerten
# ---------------------------------------------------------------------------
_FEMALE = re.compile(r"\b(woman|women|girl|female|lady|1girl)\b")
_MALE = re.compile(r"\b(man|men|boy|male|guy|1boy|male focus)\b")
_AGE_WORDS = [(r"\b(child|kid)\b", 13), (r"\b(teen|teenage|teenager|boy|girl)\b", 17), (r"\byoung (man|woman)\b", 21),
              (r"\b(middle[- ]aged)\b", 40), (r"\b(old|elderly|senior)\b", 60), (r"\b(man|woman)\b", 27)]
_HAIR_COLORS = ("black", "dark brown", "brown", "light brown", "blonde", "blond", "red", "ginger", "auburn",
                "grey", "gray", "white", "silver", "dyed")
_HAIR_TAGS_KEEP = ("hair", "beard", "stubble", "mustache", "moustache", "goatee", "sideburns", "undercut",
                   "fade", "dreadlocks", "braid", "cornrows", "afro", "bald", "buzz cut", "earring", "freckles",
                   "eyebrows", "mole")
_HAIR_TAGS_SKIP = ("hair ornament", "hairband", "hairclip", "hair between eyes", "hair over", "hair intakes",
                   "hair flaps", "sidelocks", "ahoge", "hair bun ornament")


def parse_caption(caption: str, tags: str = "") -> dict:
    """Aus 'a close up of a man with curly hair, …' + 'black hair, curly hair, blonde hair, …'
    -> {'gender': 'Männlich', 'age': 21, 'hair': 'curly black hair with blonde highlights', 'look': '…'}"""
    text = (caption or "").lower()
    first = text.split(",")[0]
    tag_list = [x.strip().replace("_", " ") for x in (tags or "").lower().split(",") if x.strip()]
    out: dict = {}
    both = first + " " + " ".join(tag_list)
    f, m = bool(_FEMALE.search(both)), bool(_MALE.search(both))
    if f != m:
        out["gender"] = "Weiblich" if f else "Männlich"
    for pattern, age in _AGE_WORDS:
        if re.search(pattern, first):
            out["age"] = age
            break

    # Haare: Stichworte bevorzugt (genauer), sonst Phrasen aus dem Satz
    hair_tags = [x for x in tag_list if any(k in x for k in _HAIR_TAGS_KEEP)
                 and not any(s in x for s in _HAIR_TAGS_SKIP)]
    colors = [c for c in _HAIR_COLORS if any(x == f"{c} hair" for x in hair_tags)]
    shapes = [x.replace(" hair", "") for x in hair_tags if x.endswith(" hair") and x.replace(" hair", "")
              not in _HAIR_COLORS and x not in ("multicolored hair", "two-tone hair", "streaked hair")]
    two_tone = any(x in hair_tags for x in ("multicolored hair", "two-tone hair", "streaked hair",
                                            "gradient hair"))
    hair = ""
    if colors or shapes:
        main = colors[0] if colors else ""
        hair = " ".join(x for x in (", ".join(shapes[:2]), main) if x).strip() + " hair"
        if two_tone and len(colors) > 1:
            hair += f" with {colors[1]} tips"
        elif len(colors) > 1:
            hair += f" with {colors[1]} highlights"
    else:
        found = re.findall(r"((?:[a-z-]+ ){0,3}hair(?: with [a-z -]+?)?)(?= and | with |$|,)", first)
        if found:
            hair = found[0].strip()
    out["hair"] = re.sub(r"\s+", " ", hair).replace("blond hair", "blonde hair")
    others = [x for x in hair_tags if not x.endswith(" hair")]
    out["look"] = ", ".join(dict.fromkeys(others))[:120]
    return out


def analyze(img: Image.Image, path=None, export=None, fallback: FaceOptions | None = None,
            describe=None) -> Analysis:
    """describe(img) -> (caption, tags) – Bildbeschreibung über Forge (darf fehlen oder fehlschlagen)."""
    fb = fallback or FaceOptions()
    a = Analysis(country=fb.country, src={"age": SRC_GUESS, "gender": SRC_GUESS, "country": SRC_SETTINGS})
    caption, tags = "", ""
    if describe is not None:
        try:
            caption, tags = describe(img)
        except Exception:  # noqa: BLE001 – ohne Beschreibung geht es auch
            caption, tags = "", ""
    a.caption = caption
    parsed = parse_caption(caption, tags)
    if parsed.get("gender"):
        a.gender, a.src["gender"] = parsed["gender"], SRC_IMAGE
    if parsed.get("age"):
        a.age, a.src["age"] = parsed["age"], SRC_GUESS
    a.hair = parsed.get("hair", "")
    if a.hair:
        a.src["hair"] = SRC_IMAGE
    look = [x for x in (skin_tone(img), parsed.get("look", "")) if x]
    a.look = ", ".join(look)

    p = export.find(path=path) if (export is not None and path is not None) else None
    if p is not None:
        if p.age:
            a.age, a.src["age"] = int(p.age), SRC_FM
        if p.country:
            a.country, a.src["country"] = p.country, SRC_FM
        a.country2 = p.country2 if p.country2 and p.country2 != a.country else NO_SECOND
        if p.personality:
            a.personality, a.src["personality"] = p.personality, SRC_FM
    return a


def options_for(a: Analysis, base: FaceOptions | None = None) -> FaceOptions:
    """Beschreibung für die Alterung eines fremden Bildes."""
    o = copy.deepcopy(base or FaceOptions())
    o.country = a.country or o.country
    o.second_country = a.country2 or NO_SECOND
    o.ethnicity = AUTO
    o.gender = a.gender
    o.age_min = o.age_max = int(a.age)
    o.hair_color = o.hair_style = o.facial_hair = AUTO
    o.hair_text = a.hair
    o.look_text = a.look
    if a.personality:
        o.personality = a.personality
    o.extra_prompt = ""
    return o


def new_seed() -> int:
    return random.randint(1, 2**31 - 1)
