import csv
import json

from PIL import Image

from fm27facegen.backends import BackendSettings
from fm27facegen.generator import (META_KEY, Generator, Job, aging_jobs, load_cached_raw, load_face)
from fm27facegen.imaging import ProcessOptions
from fm27facegen.prompts import FaceOptions, build_prompt, reage_prompt

from test_core import fake_portrait


class FakeBackend:
    supports_img2img = False

    def __init__(self):
        self.prompts = []

    def generate(self, fp):
        self.prompts.append(fp.prompt)
        return fake_portrait(512)


def make_gen(tmp_path, backend=None):
    return Generator(BackendSettings(), ProcessOptions(), tmp_path, backend=backend or FakeBackend())


def test_png_contains_info_and_reload_reproduces_face(tmp_path):
    gen = make_gen(tmp_path)
    opts = FaceOptions(country="Brasilien", second_country="Nigeria", personality="Söldner (Mercenary)",
                       age_min=16, age_max=16)
    face = gen.run_jobs([Job(opts, seed=4242)])[0]
    info = json.loads(Image.open(face.path).info[META_KEY])
    assert info["seed"] == 4242 and info["options"]["country"] == "Brasilien"

    loaded = load_face(face.path)
    assert loaded.source == "metadata" and not loaded.legacy
    assert loaded.prompt.prompt == face.prompt.prompt          # gleiche Person
    assert loaded.raw is not None                             # Rohbild aus dem Zwischenspeicher
    assert loaded.image.size == (250, 250)

    jobs = aging_jobs(loaded, [16, 25])
    assert [j.age for j in jobs] == [25]
    assert build_prompt(jobs[0].options, jobs[0].seed, 25).prompt == build_prompt(opts, 4242, 25).prompt
    aged = gen.run_jobs(jobs)[0]
    assert aged.path.name == f"{face.path.stem}_mit25.png"

    # Alterungs-Set aus einem bereits gealterten Bild: kein "_mit25_mit30"
    again = aging_jobs(load_face(aged.path), [30])
    assert again[0].filename == f"{face.path.stem}_mit30"


def test_reload_from_old_csv_log(tmp_path):
    # Bild aus einer älteren Version: keine Infos in der PNG, aber ein Eintrag in generiert.csv (altes Format)
    img_path = tmp_path / "Ghana_16J_77.png"
    fake_portrait(250).save(img_path)
    old_prompt = ("realistic close-up passport-style headshot photograph of a 16-year-old teenage boy, "
                  "Black West African, dark skin, youth academy football player from Ghana, black hair, short afro, "
                  "youthful face, clean-shaven, neutral serious expression")
    with (tmp_path / "generiert.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["datei", "zeit", "land", "ethnie", "geschlecht", "alter", "haare", "seed", "prompt"])
        w.writerow([img_path.name, "2026-11-17", "Ghana", "Westafrikanisch", "Männlich", "16", "black hair", "77",
                    old_prompt])

    loaded = load_face(img_path)
    assert loaded.source == "log" and loaded.legacy and loaded.prompt.seed == 77
    jobs = aging_jobs(loaded, [16, 30])
    assert len(jobs) == 1 and jobs[0].seed == 77
    assert "30-year-old man" in jobs[0].prompt_text and "youthful face" not in jobs[0].prompt_text
    assert "Black West African" in jobs[0].prompt_text and "short afro" in jobs[0].prompt_text

    backend = FakeBackend()
    aged = make_gen(tmp_path, backend).run_jobs(jobs)[0]
    assert backend.prompts[-1] == jobs[0].prompt_text
    reloaded = load_face(aged.path)                           # gealtertes Bild trägt jetzt selbst die Infos
    assert reloaded.source == "metadata" and reloaded.legacy and reloaded.prompt.meta["alter"] == 30


def test_reload_unknown_image(tmp_path):
    p = tmp_path / "fremd.png"
    Image.new("RGBA", (250, 250), (0, 0, 0, 0)).save(p)
    loaded = load_face(p, FaceOptions(country="Japan"))
    assert loaded.source == "unknown" and loaded.options.country == "Japan"
    jobs = aging_jobs(loaded, [20])
    assert jobs[0].init_image is not None and jobs[0].init_image.mode == "RGB"  # Vorlage für lokales SD


def test_reage_prompt_keeps_features():
    p = build_prompt(FaceOptions(age_min=16, age_max=16, personality="Musterprofi (Model Professional)"), seed=9).prompt
    q = reage_prompt(p, 34)
    assert "34-year-old man" in q and "professional footballer" in q and "youth footballer" not in q
    assert "visible crow's feet" in q
    assert reage_prompt(q, 16).count("youthful face") == 1


def test_raw_cache_roundtrip():
    from fm27facegen.generator import cache_raw
    cache_raw(Image.new("RGB", (64, 64), (10, 20, 30)), 5, 18)
    assert load_cached_raw(5, 18).size == (64, 64)
    assert load_cached_raw(5, 19) is None
