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

DEFAULT_PATTERN = "{land}_{alter}J_{seed}"
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


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")
    return text or "x"


def safe_filename(name: str) -> str:
    """Erlaubt Umlaute/Akzente (z. B. Spielernamen), entfernt nur unter Windows verbotene Zeichen."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name)).strip(" .")
    return name[:150] or "face"


def make_filename(pattern: str, meta: dict, index: int, extra: dict | None = None) -> str:
    values = {
        "land": _slug(meta.get("land", "")),
        "herkunft": _slug(meta.get("herkunft", "")),
        "ethnie": _slug(meta.get("ethnie_key", "")),
        "alter": meta.get("alter", ""),
        "geschlecht": "w" if meta.get("geschlecht") == "Weiblich" else "m",
        "seed": meta.get("seed", ""),
        "nr": f"{index:03d}",
        "datum": dt.date.today().strftime("%Y%m%d"),
        "name": "", "uid": "",
    }
    values.update(extra or {})
    try:
        name = (pattern or DEFAULT_PATTERN).format(**values)
    except (KeyError, IndexError, ValueError):
        name = DEFAULT_PATTERN.format(**values)
    return safe_filename(name) + ".png"


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
        fp = build_prompt(job.options, seed=job.seed, age=job.age)
        if job.prompt_text:
            meta = {**fp.meta, **(job.meta or {}), "seed": fp.seed}
            if job.age is not None:
                meta["alter"] = job.age
            fp = FacePrompt(prompt=job.prompt_text, negative=fp.negative, seed=fp.seed, meta=meta)
        if job.init_image is not None and getattr(self.backend, "supports_img2img", False):
            raw = self.backend.img2img(fp, job.init_image, AGING_STRENGTH)
        else:
            raw = self.backend.generate(fp)
        proc = ProcessOptions(**{**self.proc.__dict__, "transparent": job.options.background == TRANSPARENT_BG,
                                 "crop_bottom": getattr(self.backend, "watermark_strip", 0.0)})
        if proc.transparent:
            from .segment import ensure_model
            ensure_model(getattr(self.backend, "status_cb", None))
        img = process(raw, proc)
        name = safe_filename(job.filename) + ".png" if job.filename else make_filename(self.pattern, fp.meta, index)
        path = self.out_dir / name
        if not self.overwrite:
            path = _unique(path)
        legacy = bool(job.prompt_text)
        save_png(img, path, {META_KEY: face_info(fp, job.options, legacy)})
        self._log(path, fp)
        cache_raw(raw, fp.seed, fp.meta.get("alter"))
        return GeneratedFace(path=path, image=img, prompt=fp, options=copy.deepcopy(job.options), raw=raw,
                             legacy=legacy)

    def generate_one(self, face_opts: FaceOptions, index: int = 1, seed: int | None = None) -> GeneratedFace:
        return self.generate_job(Job(options=face_opts, seed=seed), index)

    # ------------------------------------------------------------------ mehrere Bilder
    def run_jobs(self, jobs: list[Job],
                 on_done: Callable[[int, Job, GeneratedFace], None] | None = None,
                 on_error: Callable[[int, Job, Exception], None] | None = None) -> list[GeneratedFace]:
        results: list[GeneratedFace] = []
        for i, job in enumerate(jobs, start=1):
            if self.cancel.is_set():
                break
            if job.seed is None:
                job.seed = random.randint(1, 2**31 - 1)
            try:
                face = self.generate_job(job, index=i)
                results.append(face)
                if on_done:
                    on_done(i, job, face)
            except Exception as exc:  # noqa: BLE001
                if on_error:
                    on_error(i, job, exc)
                else:
                    raise
            if self.delay and i < len(jobs) and not self.cancel.is_set():
                self.cancel.wait(self.delay)
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


def aging_jobs(face: GeneratedFace, ages: list[int]) -> list[Job]:
    """Jobs für ein Alterungs-Set: gleicher Seed + gleiche Merkmale, nur das Alter ändert sich."""
    try:
        base_age = int(face.prompt.meta.get("alter"))
    except (TypeError, ValueError):
        base_age = None
    stem = re.sub(r"_mit\d+$", "", face.path.stem)  # aus einem Alterungsbild heraus nicht "_mit20_mit30"
    init = face.raw if face.raw is not None else as_init_image(face.image)
    gender = face.prompt.meta.get("geschlecht", face.options.gender)
    jobs = []
    for age in ages:
        if age == base_age:
            continue
        job = Job(options=copy.deepcopy(face.options), seed=face.prompt.seed, age=age,
                  filename=f"{stem}_mit{age}", init_image=init)
        if face.legacy:
            job.prompt_text = reage_prompt(face.prompt.prompt, age, gender)
            job.meta = dict(face.prompt.meta)
        jobs.append(job)
    return jobs


# ---------------------------------------------------------------------------
# Bildinfos in der PNG, Rohbild-Zwischenspeicher, Laden vorhandener Bilder
# ---------------------------------------------------------------------------
META_KEY = "fm27facegen"
RAW_CACHE_KEEP = 400  # so viele Rohbilder bleiben im Zwischenspeicher (je ca. 100–300 KB)


def face_info(fp: FacePrompt, options: FaceOptions, legacy: bool = False) -> str:
    """JSON mit allem, was für ein späteres Alterungs-Set nötig ist."""
    data = {"v": 1, "seed": fp.seed, "age": fp.meta.get("alter"), "legacy": legacy,
            "options": asdict(options), "prompt": fp.prompt, "meta": fp.meta}
    return json.dumps(data, ensure_ascii=False, default=str)


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


def _find_in_log(path: Path) -> dict | None:
    log = path.parent / "generiert.csv"
    if not log.exists():
        return None
    try:
        with log.open(encoding="utf-8-sig", newline="") as f:
            rows = [r for r in csv.DictReader(f, delimiter=";") if r.get("datei") == path.name]
    except (OSError, csv.Error):
        return None
    return rows[-1] if rows else None  # bei überschriebenen Dateien gilt der neueste Eintrag


def load_face(path: str | Path, fallback: FaceOptions | None = None) -> GeneratedFace:
    """Lädt ein vorhandenes Bild in die Galerie – mit allen Infos, die sich finden lassen."""
    path = Path(path)
    with Image.open(path) as im:
        im.load()
        info_text = im.info.get(META_KEY)
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
            return GeneratedFace(path=path, image=image, prompt=fp, options=options,
                                 raw=load_cached_raw(seed, fp.meta.get("alter")), source="metadata", legacy=legacy)
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
