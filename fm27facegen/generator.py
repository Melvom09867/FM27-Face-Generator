"""Ablauf: Prompt bauen -> Bild erzeugen -> nachbearbeiten -> speichern (+ Protokoll)."""

from __future__ import annotations

import copy
import csv
import json
import datetime as dt
import random
import re
import threading
import time
import unicodedata
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from .backends import BackendSettings, make_backend
from .imaging import ProcessOptions, process, save_png
from .prompts import (GENDERS, NEGATIVE_PROMPT, TRANSPARENT_BG, FaceOptions, FacePrompt, build_prompt,
                      reage_prompt)

DEFAULT_PATTERN = "{land}_{alter}J_{persoenlichkeit}_{seed}"
OLD_DEFAULT_PATTERNS = ("{land}_{alter}J_{seed}",)  # alte Standardmuster -> werden automatisch umgestellt
AGING_STRENGTH = 0.5  # img2img-Stärke beim Alterungs-Set (lokal): kleiner = ähnlicher, größer = mehr Alterung


@dataclass
class Job:
    """Ein zu erzeugendes Bild."""
    options: FaceOptions
    seed: int | None = None
    age: int | None = None             # überschreibt das Alter (Alterungs-Set / Spielerliste)
    filename: str | None = None        # Dateiname ohne .png; None = Dateinamen-Muster
    init_image: Image.Image | None = None  # Ausgangsbild für img2img (nur lokal)
    tag: Any = None                    # frei verwendbar (z. B. Zeile der Spielerliste)
    prompt_text: str | None = None     # fertige Beschreibung statt build_prompt (Bilder aus älteren Versionen)
    meta: dict | None = None           # Bildinfos zu prompt_text
    out_dir: Path | None = None        # Zielordner nur für diesen Job (sonst der des Generators)
    out_path: Path | None = None       # fester Zielpfad (überschreibt) – z. B. Warteschlange für "Im Spiel ersetzen"
    replace: Path | None = None        # dieses FaceDrop-Bild wird nach dem Durchlauf durch das neue ersetzt
    # Alterung immer vom ERSTEN Bild aus (Ausgangsbild), nie vom zuletzt gealterten – sonst verändert sich das Gesicht
    # mit jeder Saison weiter. base_image/base_age werden ins neue Bild übernommen.
    base_image: Image.Image | None = None
    base_age: int | None = None
    rebuild_base: bool = False         # Ausgangsbild fehlt: erst neu erzeugen (gleicher Seed, Ausgangsalter)


@dataclass
class GeneratedFace:
    path: Path
    image: Image.Image
    prompt: FacePrompt
    options: FaceOptions = field(default_factory=FaceOptions)
    raw: Image.Image | None = None     # unbearbeitetes KI-Bild (für Alterungs-Sets)
    # Herkunft der Infos: "generated" (gerade erzeugt), "metadata" (aus der PNG), "log" (aus generiert.csv),
    # "unknown" (keine Infos – Alterungs-Set nur mit lokalem Stable Diffusion)
    source: str = "generated"
    legacy: bool = False               # True = nur fertige Beschreibung bekannt (Alter wird darin ersetzt)
    timing: dict = field(default_factory=dict)  # Sekunden: "gen" (KI-Bild), "post" (Freistellen + Speichern)
    base: Image.Image | None = None    # Ausgangsbild (erstes KI-Bild dieses Spielers) für weitere Alterungen
    base_age: int | None = None
    player_name: str | None = None     # Name aus der Spielerliste (Sortierung in 'Neu erstellt')


def _slug(text: str) -> str:
    text = str(text)
    for a, b in (("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")
    return text or "x"


def safe_filename(name: str) -> str:
    """Erlaubt Umlaute/Akzente (z. B. Spielernamen), entfernt nur unter Windows verbotene Zeichen."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name)).strip(" .")
    return name[:150] or "face"


def make_filename(pattern: str, meta: dict, index: int, extra: dict | None = None) -> str:
    values = {
        "land": _slug(_country_for_file(meta.get("land", ""))),
        "herkunft": _slug(meta.get("herkunft", "")),
        "ethnie": _slug(meta.get("ethnie_key", "")),
        "alter": meta.get("alter", ""),
        "geschlecht": "w" if meta.get("geschlecht") == "Weiblich" else "m",
        "seed": meta.get("seed", ""),
        "nr": f"{index:03d}",
        "datum": dt.date.today().strftime("%Y%m%d"),
        "name": "", "uid": "",
        "persoenlichkeit": _personality_slug(meta.get("persoenlichkeit", "")),
    }
    values.update(extra or {})
    try:
        name = (pattern or DEFAULT_PATTERN).format(**values)
    except (KeyError, IndexError, ValueError):
        name = DEFAULT_PATTERN.format(**values)
    name = re.sub(r"_{2,}", "_", name).strip("_-")  # leere Platzhalter (z. B. keine Persönlichkeit) entfernen
    return safe_filename(name) + ".png"


def _country_for_file(key: str) -> str:
    """Land für den Dateinamen: deutsch bei deutscher Oberfläche, sonst englisch."""
    from .data import COUNTRIES
    from .i18n import get_language
    if get_language() != "de" and key in COUNTRIES:
        return COUNTRIES[key][0]
    return key


def _personality_slug(key: str) -> str:
    """Persönlichkeit für den Dateinamen: deutsch bei deutscher Oberfläche, sonst der englische FM-Name."""
    if not key:
        return ""
    from .i18n import get_language
    de, _, en = key.partition(" (")
    return _slug(de if get_language() == "de" or not en else en.rstrip(")"))


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    for i in range(2, 10_000):
        cand = path.with_name(f"{path.stem}_{i}{path.suffix}")
        if not cand.exists():
            return cand
    return path


class Generator:
    def __init__(self, backend_settings: BackendSettings, process_opts: ProcessOptions,
                 out_dir: Path, pattern: str = DEFAULT_PATTERN, delay: float = 0.0, backend=None,
                 overwrite: bool = False):
        self.backend = backend or make_backend(backend_settings)
        self.proc = process_opts
        self.out_dir = Path(out_dir)
        self.pattern = pattern
        self.delay = delay
        self.overwrite = overwrite
        self.cancel = threading.Event()
        if hasattr(self.backend, "cancel_event"):
            self.backend.cancel_event = self.cancel

    # ------------------------------------------------------------------ einzelnes Bild
    def generate_job(self, job: Job, index: int = 1) -> GeneratedFace:
        t0 = time.perf_counter()
        fp, raw = self._render(job)
        return self._finish(job, fp, raw, index, time.perf_counter() - t0)

    def _render(self, job: Job) -> tuple[FacePrompt, Image.Image]:
        """KI-Bild erzeugen (läuft auf der Grafikkarte bzw. online)."""
        fp = build_prompt(job.options, seed=job.seed, age=job.age)
        if job.prompt_text:
            meta = {**fp.meta, **(job.meta or {}), "seed": fp.seed}
            if job.age is not None:
                meta["alter"] = job.age
            fp = FacePrompt(prompt=job.prompt_text, negative=fp.negative, seed=fp.seed, meta=meta)
        img2img = getattr(self.backend, "supports_img2img", False)
        if job.rebuild_base and img2img and job.base_age is not None and not job.prompt_text:
            # Ausgangsbild fehlt (z. B. Bild aus 1.8.7.4): gleiches Gesicht im Ausgangsalter neu malen
            job.base_image = self.backend.generate(build_prompt(job.options, seed=job.seed, age=job.base_age))
            job.init_image = job.base_image
            job.rebuild_base = False
        if job.init_image is not None and img2img:
            raw = self.backend.img2img(fp, job.init_image, AGING_STRENGTH)
        else:
            raw = self.backend.generate(fp)
        return fp, raw

    def _finish(self, job: Job, fp: FacePrompt, raw: Image.Image, index: int, t_gen: float) -> GeneratedFace:
        """Freistellen, zuschneiden, speichern (läuft parallel zum nächsten KI-Bild)."""
        t0 = time.perf_counter()
        proc = ProcessOptions(**{**self.proc.__dict__, "transparent": job.options.background == TRANSPARENT_BG,
                                 "crop_bottom": getattr(self.backend, "watermark_strip", 0.0)})
        if proc.transparent:
            from .segment import ensure_model
            ensure_model(getattr(self.backend, "status_cb", None))
        img = process(raw, proc)
        if job.out_path is not None:
            path = Path(job.out_path)  # feste Stelle (Warteschlange) – wird überschrieben
        else:
            name = safe_filename(job.filename) + ".png" if job.filename else make_filename(self.pattern, fp.meta, index)
            path = Path(job.out_dir or self.out_dir) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not self.overwrite:
                path = _unique(path)
        legacy = bool(job.prompt_text)
        # Ausgangsbild: bei Alterung das übergebene, sonst ist dieses Bild selbst das Ausgangsbild
        base, base_age = (job.base_image, job.base_age) if job.base_image is not None else (raw, fp.meta.get("alter"))
        save_png(img, path, {META_KEY: face_info(fp, job.options, legacy, base_age), BASE_KEY: encode_base(base)})
        if job.out_path is None:
            self._log(path, fp)
        cache_raw(raw, fp.seed, fp.meta.get("alter"))
        timing = {"gen": round(t_gen, 2), "post": round(time.perf_counter() - t0, 2)}
        _log_timing(path.name, timing, getattr(self.backend, "last_settings", ""))
        return GeneratedFace(path=path, image=img, prompt=fp, options=copy.deepcopy(job.options), raw=raw,
                             legacy=legacy, timing=timing, base=base, base_age=base_age)

    def generate_one(self, face_opts: FaceOptions, index: int = 1, seed: int | None = None) -> GeneratedFace:
        return self.generate_job(Job(options=face_opts, seed=seed), index)

    # ------------------------------------------------------------------ mehrere Bilder
    def run_jobs(self, jobs: list[Job],
                 on_done: Callable[[int, Job, GeneratedFace], None] | None = None,
                 on_error: Callable[[int, Job, Exception], None] | None = None,
                 retries: int = 0) -> list[GeneratedFace]:
        """Alle Jobs nacheinander. Während die KI schon das nächste Bild malt, wird das vorige im Hintergrund
        freigestellt und gespeichert (spart pro Bild die Nachbearbeitungszeit). retries: so oft wird ein
        fehlgeschlagenes Bild erneut versucht, bevor es übersprungen wird (wichtig für lange Läufe über Nacht)."""
        from concurrent.futures import ThreadPoolExecutor
        results: list[GeneratedFace] = []

        def finish(i: int, job: Job, fp: FacePrompt, raw: Image.Image, t_gen: float) -> None:
            try:
                face = self._finish(job, fp, raw, i, t_gen)
            except Exception as exc:  # noqa: BLE001
                if on_error:
                    on_error(i, job, exc)
                    return
                raise
            results.append(face)
            if on_done:
                on_done(i, job, face)

        pending = None
        with ThreadPoolExecutor(max_workers=1) as pool:
            for i, job in enumerate(jobs, start=1):
                if self.cancel.is_set():
                    break
                if job.seed is None:
                    job.seed = random.randint(1, 2**31 - 1)
                rendered = None
                for attempt in range(retries + 1):
                    try:
                        t0 = time.perf_counter()
                        fp, raw = self._render(job)
                        rendered = (fp, raw, time.perf_counter() - t0)
                        break
                    except Exception as exc:  # noqa: BLE001
                        if attempt < retries and not self.cancel.is_set():
                            continue
                        if on_error:
                            on_error(i, job, exc)
                        else:
                            if pending is not None:
                                pending.result()
                            raise
                if rendered is not None:
                    if pending is not None:
                        pending.result()  # höchstens ein Bild gleichzeitig in der Nachbearbeitung
                    pending = pool.submit(finish, i, job, *rendered)
                if self.delay and i < len(jobs) and not self.cancel.is_set():
                    self.cancel.wait(self.delay)
            if pending is not None:
                pending.result()
        return results

    def run(self, face_opts: FaceOptions, count: int,
            on_done: Callable[[int, GeneratedFace], None] | None = None,
            on_error: Callable[[int, Exception], None] | None = None,
            base_seed: int | None = None) -> list[GeneratedFace]:
        rng = random.Random(base_seed)
        jobs = [Job(options=face_opts, seed=rng.randint(1, 2**31 - 1)) for _ in range(count)]
        return self.run_jobs(
            jobs,
            on_done=(lambda i, j, f: on_done(i, f)) if on_done else None,
            on_error=(lambda i, j, e: on_error(i, e)) if on_error else None,
        )

    def _log(self, path: Path, fp: FacePrompt) -> None:
        log = self.out_dir / "generiert.csv"
        new = not log.exists()
        try:
            with log.open("a", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                if new:
                    w.writerow(["datei", "zeit", "land", "herkunft", "ethnie", "geschlecht", "alter", "haare", "seed", "prompt"])
                m = fp.meta
                w.writerow([path.name, time.strftime("%Y-%m-%d %H:%M:%S"), m["land"], m.get("herkunft", ""),
                            m["ethnie"], m["geschlecht"], m["alter"], m["haare"], m["seed"], fp.prompt])
        except OSError:
            pass  # Protokoll ist nur ein Extra – Bild ist trotzdem gespeichert


def face_age(face: GeneratedFace) -> int | None:
    """Gespeichertes Alter eines Bildes (None = unbekannt, z. B. fremdes Bild ohne Infos)."""
    if face.source == "unknown":
        return None
    try:
        return int(face.prompt.meta.get("alter"))
    except (TypeError, ValueError):
        return None


_AGE_TOKEN = re.compile(r"(?<![0-9])(\d{1,2})J(?=_|$)")


def aging_name(stem: str, age: int) -> str:
    """Dateiname fürs neue Alter: 'Deutschland_16J_Ehrgeizig_123' -> 'Deutschland_20J_Ehrgeizig_123'.
    Ohne Altersangabe im Namen (z. B. umbenannt in den Spielernamen) wird '_20J' angehängt."""
    stem = re.sub(r"_mit\d+$", "", stem)  # alte Benennung (bis 1.8.7.3): Name_mit20
    if _AGE_TOKEN.search(stem):
        return _AGE_TOKEN.sub(f"{age}J", stem, count=1)
    return f"{stem}_{age}J"


def aging_jobs(face: GeneratedFace, ages: list[int], relative: int = 0) -> list[Job]:
    """Jobs für ein Alterungs-Set: gleicher Seed + gleiche Merkmale, nur das Alter ändert sich.

    relative > 0: statt fester Alter das gespeicherte Alter um so viele Jahre erhöhen (z. B. +4)."""
    base_age = face_age(face)
    if relative:
        if base_age is None:
            return []
        ages = [min(45, base_age + relative)]
    stem = face.path.stem
    # Vorlage ist immer das Ausgangsbild (erstes KI-Bild), nicht das zuletzt gealterte Bild
    origin, origin_age, rebuild = face.base, face.base_age, False
    if origin is None and origin_age is not None and face.source != "unknown":
        origin = load_cached_raw(face.prompt.seed, origin_age)
    if origin is None and face.source == "metadata" and not face.legacy and origin_age is not None \
            and origin_age != base_age:
        rebuild = True  # nur das gealterte Bild ist da -> Ausgangsbild mit gleichem Seed neu erzeugen
    if origin is None and not rebuild:
        origin = face.raw if face.raw is not None else as_init_image(face.image)
        origin_age = base_age
    gender = face.prompt.meta.get("geschlecht", face.options.gender)
    jobs = []
    for age in ages:
        if age == base_age:
            continue
        job = Job(options=copy.deepcopy(face.options), seed=face.prompt.seed, age=age,
                  filename=aging_name(stem, age), init_image=origin, base_image=origin, base_age=origin_age,
                  rebuild_base=rebuild)
        if face.legacy:
            job.prompt_text = reage_prompt(face.prompt.prompt, age, gender)
            job.meta = dict(face.prompt.meta)
        jobs.append(job)
    return jobs


# ---------------------------------------------------------------------------
# Bildinfos in der PNG, Rohbild-Zwischenspeicher, Laden vorhandener Bilder
# ---------------------------------------------------------------------------
META_KEY = "fm27facegen"
BASE_KEY = "fm27facegen_base"  # Ausgangsbild (JPEG, Base64) – damit jede Alterung vom selben Gesicht ausgeht
BASE_SIZE = 512
RAW_CACHE_KEEP = 400  # so viele Rohbilder bleiben im Zwischenspeicher (je ca. 100–300 KB)


def face_info(fp: FacePrompt, options: FaceOptions, legacy: bool = False, base_age=None) -> str:
    """JSON mit allem, was für ein späteres Alterungs-Set nötig ist."""
    data = {"v": 1, "seed": fp.seed, "age": fp.meta.get("alter"), "legacy": legacy,
            "options": asdict(options), "prompt": fp.prompt, "meta": fp.meta,
            "base_age": base_age if base_age is not None else fp.meta.get("alter")}
    return json.dumps(data, ensure_ascii=False, default=str)


def encode_base(img: Image.Image | None) -> str:
    """Ausgangsbild klein als JPEG/Base64 (ca. 30–50 KB) – FM und FaceDrop ignorieren den Text-Block."""
    if img is None:
        return ""
    import base64
    import io
    im = img.convert("RGB")
    im.thumbnail((BASE_SIZE, BASE_SIZE))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def decode_base(text: str | None) -> Image.Image | None:
    if not text:
        return None
    try:
        import base64
        import io
        with Image.open(io.BytesIO(base64.b64decode(text))) as im:
            return im.convert("RGB")
    except Exception:  # noqa: BLE001
        return None


def raw_cache_dir() -> Path:
    from .segment import models_dir
    return models_dir().parent / "raw"


def _raw_cache_path(seed, age) -> Path:
    return raw_cache_dir() / f"{seed}_{age}.jpg"


def cache_raw(raw: Image.Image | None, seed, age) -> None:
    """Unbearbeitetes KI-Bild für spätere Alterungs-Sets aufheben (beste Qualität bei lokalem SD)."""
    if raw is None or seed is None:
        return
    try:
        d = raw_cache_dir()
        d.mkdir(parents=True, exist_ok=True)
        raw.convert("RGB").save(_raw_cache_path(seed, age), "JPEG", quality=90)
        files = sorted(d.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in files[RAW_CACHE_KEEP:]:
            old.unlink(missing_ok=True)
    except OSError:
        pass


def load_cached_raw(seed, age) -> Image.Image | None:
    try:
        path = _raw_cache_path(seed, age)
        if path.exists():
            with Image.open(path) as im:
                return im.convert("RGB")
    except OSError:
        pass
    return None


def as_init_image(img: Image.Image) -> Image.Image:
    """Fertiges (evtl. transparentes) Bild als Vorlage für img2img: auf hellgrauen Hintergrund legen."""
    if img.mode == "RGBA":
        bg = Image.new("RGBA", img.size, (200, 200, 200, 255))
        bg.alpha_composite(img)
        return bg.convert("RGB")
    return img.convert("RGB")


def _options_from_dict(data: dict) -> FaceOptions:
    names = {f.name for f in fields(FaceOptions)}
    return FaceOptions(**{k: v for k, v in (data or {}).items() if k in names})


_log_cache: dict[tuple[str, float], dict[str, dict]] = {}


def _find_in_log(path: Path) -> dict | None:
    """Eintrag zu einer Datei in generiert.csv (pro Datei-Stand nur einmal eingelesen – schnell auch bei vielen Bildern)."""
    log = path.parent / "generiert.csv"
    try:
        key = (str(log), log.stat().st_mtime)
    except OSError:
        return None
    if key not in _log_cache:
        rows: dict[str, dict] = {}
        try:
            with log.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f, delimiter=";"):
                    if r.get("datei"):
                        rows[r["datei"]] = r  # bei überschriebenen Dateien gilt der neueste Eintrag
        except (OSError, csv.Error):
            return None
        _log_cache.clear()  # nur den zuletzt gelesenen Stand behalten
        _log_cache[key] = rows
    return _log_cache[key].get(path.name)


SKIP_DIRS = ("sicherungskopie",)  # Sicherungen alter FaceDrop-Bilder gehören nicht in die Galerie


def list_folder_images(base: str | Path, limit: int = 2000) -> list[Path]:
    """PNG-Bilder im Speicherort und in dessen direkten Unterordnern (z. B. 'je Land'), neueste zuerst.
    Die Sicherungskopie und Ordner, die mit '_' oder '.' beginnen, werden übersprungen."""
    base = Path(base)
    if not base.is_dir():
        return []
    subs = [p for p in base.glob("*/*.png")
            if p.parent.name.casefold() not in SKIP_DIRS and not p.parent.name.startswith(("_", "."))]
    files = [p for p in base.glob("*.png")] + subs
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def _log_timing(name: str, timing: dict, settings: str = "") -> None:
    """Zeitmessung je Bild (%APPDATA%\\FM27FaceGenerator\\timing.log) – zeigt, wo die Zeit hängt."""
    try:
        from .settings import config_dir
        log = config_dir() / "timing.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists() and log.stat().st_size > 300_000:
            log.write_text("", encoding="utf-8")
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  KI {timing['gen']:.1f} s  "
                    f"Nachbearbeitung {timing['post']:.1f} s  {name}" + (f"  [{settings}]" if settings else "") + "\n")
    except OSError:
        pass


def search_key(text: str) -> str:
    """Vergleichsform für die Suche: 'Söldner' findet auch 'Soeldner', 'sehr ehrgeizig' auch 'Sehr-ehrgeizig'."""
    if not str(text).strip():
        return ""
    return _slug(text).replace("-", "").casefold()


def load_face(path: str | Path, fallback: FaceOptions | None = None) -> GeneratedFace:
    """Lädt ein vorhandenes Bild in die Galerie – mit allen Infos, die sich finden lassen."""
    path = Path(path)
    with Image.open(path) as im:
        im.load()
        info_text = im.info.get(META_KEY)
        base_img = decode_base(im.info.get(BASE_KEY))
        image = im.convert("RGBA") if ("A" in im.getbands() or "transparency" in im.info) else im.convert("RGB")
    fallback = copy.deepcopy(fallback or FaceOptions())

    if info_text:
        try:
            data = json.loads(info_text)
            options = _options_from_dict(data.get("options"))
            seed, age, legacy = int(data["seed"]), data.get("age"), bool(data.get("legacy"))
            if legacy:
                fp = FacePrompt(prompt=data["prompt"], negative=NEGATIVE_PROMPT, seed=seed, meta=data.get("meta", {}))
            else:
                fp = build_prompt(options, seed=seed, age=int(age) if age is not None else None)
            base_age = data.get("base_age")
            if base_age is None:  # Bild aus 1.8.7.4 oder älter: Ausgangsalter = Alter in den Einstellungen
                base_age = options.age_min if options.age_min == options.age_max else None
            return GeneratedFace(path=path, image=image, prompt=fp, options=options,
                                 raw=load_cached_raw(seed, fp.meta.get("alter")), source="metadata", legacy=legacy,
                                 base=base_img, base_age=int(base_age) if base_age is not None else None)
        except (ValueError, KeyError, TypeError):
            pass  # beschädigte Infos -> wie Bild ohne Infos behandeln

    row = _find_in_log(path)
    if row and row.get("seed", "").isdigit() and row.get("prompt"):
        options = fallback
        land = row.get("land", "")
        if land:
            options.country = land
        if row.get("geschlecht") in GENDERS:
            options.gender = row["geschlecht"]
        try:
            age = int(row.get("alter", ""))
            options.age_min = options.age_max = age
        except ValueError:
            age = None
        meta = {"seed": int(row["seed"]), "land": land, "herkunft": row.get("herkunft") or land,
                "ethnie": row.get("ethnie", ""), "ethnie_key": "", "geschlecht": options.gender,
                "alter": age, "haare": row.get("haare", ""), "persoenlichkeit": ""}
        fp = FacePrompt(prompt=row["prompt"], negative=NEGATIVE_PROMPT, seed=int(row["seed"]), meta=meta)
        return GeneratedFace(path=path, image=image, prompt=fp, options=options,
                             raw=load_cached_raw(int(row["seed"]), age), source="log", legacy=True)

    # Fremdes Bild ohne Infos: aktuelle Einstellungen als Beschreibung, Bild selbst dient als Vorlage
    fp = build_prompt(fallback, seed=random.randint(1, 2**31 - 1))
    return GeneratedFace(path=path, image=image, prompt=fp, options=fallback, raw=None, source="unknown")


def parse_ages(text: str) -> list[int]:
    """'16, 20, 25-27' -> [16, 20, 25, 26, 27] (nur 14–45)."""
    ages: list[int] = []
    for part in re.split(r"[,; ]+", text.strip()):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            a, b = sorted((int(m.group(1)), int(m.group(2))))
            ages.extend(range(a, b + 1))
        elif part.isdigit():
            ages.append(int(part))
    return sorted({a for a in ages if 14 <= a <= 45})


# ---------------------------------------------------------------------------
# Dateiverwaltung aus der Galerie: Papierkorb, Umbenennen
# ---------------------------------------------------------------------------
def trash_files(paths: list[Path]) -> list[Path]:
    """Verschiebt Dateien in den Papierkorb. Gibt die Dateien zurück, bei denen das nicht ging."""
    try:
        from send2trash import send2trash
    except Exception:  # noqa: BLE001
        return [p for p in paths if p.exists()]
    failed = []
    for p in paths:
        if not p.exists():
            continue  # schon weg – nichts zu tun
        try:
            send2trash(str(p))
        except Exception:  # noqa: BLE001
            failed.append(p)
    return failed


class RenameError(Exception):
    pass


def rename_face(face: GeneratedFace, new_stem: str) -> Path:
    """Benennt die Bilddatei um. Bilder, deren Infos nur in generiert.csv stehen, bekommen die Infos dabei
    in die PNG geschrieben – sonst ginge nach dem Umbenennen die Zuordnung (und das Alterungs-Set) verloren."""
    new_stem = safe_filename(new_stem.strip().removesuffix(".png").removesuffix(".PNG"))
    target = face.path.with_name(new_stem + ".png")
    if target == face.path:
        return face.path
    if target.exists():
        raise RenameError(target.name)
    if face.source == "log" and face.path.exists():
        save_png(face.image, face.path, {META_KEY: face_info(face.prompt, face.options, legacy=True)})
        face.source = "metadata"
    face.path.rename(target)
    face.path = target
    return target
