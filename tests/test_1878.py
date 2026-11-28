"""1.8.7.8: Persönlichkeit beim Altern, fremde Bilder analysieren, Gesichts-Erweiterung, eigene Sprachen."""
import json

import numpy as np
from PIL import Image

from fm27facegen import analyze, fmdata, i18n, userlang
from fm27facegen.backends import BackendSettings, StableDiffusionWebUIBackend
from fm27facegen.generator import Generator, Job, aging_jobs, load_face, use_analysis
from fm27facegen.imaging import ProcessOptions
from fm27facegen.playerlist import Player
from fm27facegen.prompts import FaceOptions, build_prompt

from test_core import fake_portrait


class Img2Img:
    supports_img2img = True

    def __init__(self):
        self.prompts = []

    def generate(self, fp):
        self.prompts.append(fp)
        return fake_portrait(512)

    def img2img(self, fp, init, strength):
        self.prompts.append(fp)
        return fake_portrait(512)


def test_parse_caption_curly_two_tone():
    r = analyze.parse_caption("a close up of a man with curly hair and a black shirt, trending on artstation",
                              "1boy, male focus, black hair, curly hair, blonde hair, multicolored hair, "
                              "thick eyebrows, hair ornament")
    assert r["gender"] == "Männlich" and r["age"] == 27
    assert r["hair"] == "curly black hair with blonde tips"
    assert "thick eyebrows" in r["look"] and "ornament" not in r["look"]
    assert analyze.parse_caption("a young woman with long blonde hair")["gender"] == "Weiblich"
    assert analyze.parse_caption("a teenage boy smiling")["age"] == 17


def test_facts_come_from_fm_export(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    exp = fmdata.save_export([Player(name="Test Spieler", uid="2002045467", age=17, country="Spanien",
                                     country2="Marokko", personality="Ehrgeizig (Ambitious)")])
    exp = fmdata.load_export()
    img = fake_portrait(600)
    a = analyze.analyze(img, path=tmp_path / "newgen_2002045467.png", export=exp,
                        fallback=FaceOptions(country="Niederlande", gender="Weiblich"),
                        describe=lambda im: ("a man with curly hair", "1boy, curly hair, black hair"))
    assert (a.age, a.country, a.country2, a.gender) == (17, "Spanien", "Marokko", "Männlich")
    assert a.src["age"] == "fm" and a.src["gender"] == "image" and a.personality == "Ehrgeizig (Ambitious)"
    assert fmdata.load_export().find(name="test spieler").uid == "2002045467"


def test_prepare_base_is_square():
    img = Image.new("RGB", (1320, 1585), (150, 30, 30))
    base = analyze.prepare_base(img)
    assert base.size[0] == base.size[1]


def test_foreign_image_ages_from_itself(tmp_path):
    foreign = tmp_path / "foto.png"
    fake_portrait(700).save(foreign)
    face = load_face(foreign)
    assert face.source == "unknown"
    a = analyze.Analysis(age=17, gender="Männlich", country="Spanien", country2="Marokko",
                         hair="curly black hair with blonde tips")
    base = analyze.prepare_base(face.image)
    use_analysis(face, analyze.options_for(a), a.age, base)
    jobs = aging_jobs(face, [], relative=1)
    assert len(jobs) == 1 and jobs[0].age == 18 and jobs[0].base_image is base
    be = Img2Img()
    out = Generator(BackendSettings(), ProcessOptions(), tmp_path, backend=be).run_jobs(jobs)[0]
    assert "curly black hair with blonde tips" in be.prompts[0].prompt and "Spain" in be.prompts[0].prompt
    again = load_face(out.path)  # nächste Saison: jetzt mit Bild-Infos, Ausgangsbild = das Foto
    assert again.source == "metadata" and again.base_age == 17 and again.options.hair_text


def test_personality_change_on_ageing(tmp_path):
    be = Img2Img()
    gen = Generator(BackendSettings(), ProcessOptions(), tmp_path, backend=be)
    f = gen.run_jobs([Job(FaceOptions(age_min=17, age_max=17, personality="Ausgewogen (Balanced)"), seed=4)])[0]
    job = aging_jobs(load_face(f.path), [], relative=1, personality="Söldner (Mercenary)")[0]
    assert job.options.personality == "Söldner (Mercenary)"
    out = gen.run_jobs([job])[0]
    assert load_face(out.path).options.personality == "Söldner (Mercenary)"


def test_faceid_payload():
    class Resp:
        def __init__(self, data, code=200):
            self._d, self.status_code, self.text = data, code, ""

        def json(self):
            return self._d

    class Session:
        posts = []

        def get(self, url, timeout=0):
            if "model_list" in url:
                return Resp({"model_list": ["control_x", "ip-adapter-faceid-plusv2_sdxl [187cb962]"]})
            if "loras" in url:
                return Resp([{"name": "ip-adapter-faceid-plusv2_sdxl_lora"}])
            return Resp({"sd_model_checkpoint": "x"})

        def post(self, url, json=None, timeout=0):
            self.posts.append((url, json))
            import base64, io
            buf = io.BytesIO()
            Image.new("RGB", (8, 8)).save(buf, "PNG")
            return Resp({"images": [base64.b64encode(buf.getvalue()).decode()]})

    sess = Session()
    be = StableDiffusionWebUIBackend(BackendSettings(faceid=True), session=sess)
    be.img2img(build_prompt(FaceOptions(), seed=1), fake_portrait(256), 0.5, face_ref=fake_portrait(256))
    payload = [j for u, j in sess.posts if u.endswith("img2img")][-1]
    unit = payload["alwayson_scripts"]["ControlNet"]["args"][0]
    assert unit["model"].startswith("ip-adapter-faceid") and unit["module"].startswith("InsightFace")
    assert "<lora:ip-adapter-faceid-plusv2_sdxl_lora:" in payload["prompt"]
    off = StableDiffusionWebUIBackend(BackendSettings(faceid=False), session=Session())
    off.img2img(build_prompt(FaceOptions(), seed=1), fake_portrait(256), 0.5, face_ref=fake_portrait(256))
    assert "alwayson_scripts" not in [j for u, j in Session.posts if u.endswith("img2img")][-1]


def test_user_language_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    csv_file = tmp_path / "sprache.csv"
    n = userlang.export_csv(csv_file, "en")
    assert n > 500
    import csv
    with open(csv_file, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    for parts in rows:
        if parts[0] == "#name":
            parts[1] = "Filipino"
        elif parts[0] == "text" and parts[1] == "btn.ok":
            parts[4] = "Sige"
        elif parts[0] == "text" and parts[1] == "msg.delete_confirm":
            parts[4] = "Burahin {n}? {wrong}"          # falscher Platzhalter -> verworfen
        elif parts[0] == "country" and parts[1] == "Deutschland":
            parts[4] = "Alemanya"
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(rows)
    name, data, ok, bad = userlang.import_csv(csv_file)
    assert name == "Filipino" and bad >= 1 and data["text"]["btn.ok"] == "Sige"
    code = userlang.save_language(name, data)
    i18n.USER.clear()
    userlang.load_all()
    try:
        i18n.set_language(code)
        assert i18n.t("btn.ok") == "Sige"
        assert i18n.country("Deutschland") == "Alemanya"
        assert "{" not in i18n.t("msg.delete_confirm", n=2, names="x")  # Englisch statt kaputt
        assert i18n.language_label(code) == "Filipino (not from the generator)"
    finally:
        i18n.set_language("de")
    userlang.remove_language(code)
    assert code not in i18n.LANGUAGES
