import base64
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
from PIL import Image, ImageDraw

from fm27facegen import data
from fm27facegen.backends import BackendSettings, StableDiffusionWebUIBackend
from fm27facegen.generator import Generator, make_filename
from fm27facegen.imaging import ProcessOptions, crop_to_face, process
from fm27facegen.prompts import TRANSPARENT_BG, FaceOptions, build_prompt


def fake_portrait(size=768):
    img = Image.new("RGB", (size, size), (200, 200, 200))
    d = ImageDraw.Draw(img)
    d.ellipse((size * .35, size * .2, size * .65, size * .6), fill=(190, 140, 110))
    d.rectangle((size * .2, size * .65, size * .8, size), fill=(30, 40, 120))
    return img


def test_all_countries_reference_known_ethnicities():
    for name, (en, mix) in data.COUNTRIES.items():
        assert en and mix, name
        assert all(k in data.ETHNICITIES for k in mix), name


def test_prompt_is_deterministic_and_respects_options():
    o = FaceOptions(country="Nigeria", age_min=16, age_max=16)
    a, b = build_prompt(o, seed=42), build_prompt(o, seed=42)
    assert a.prompt == b.prompt
    assert "16-year-old teenage boy" in a.prompt and "Nigeria" in a.prompt
    assert a.meta["ethnie_key"] == "AFR_W"
    f = build_prompt(FaceOptions(gender="Weiblich", age_min=22, age_max=22, ethnicity="ASIA_E"), seed=1)
    assert "young woman" in f.prompt and "East Asian" in f.prompt
    assert "stubble" not in f.prompt and "beard" not in f.prompt


def test_young_players_rarely_get_beards():
    beards = sum("beard" in build_prompt(FaceOptions(age_min=15, age_max=15), seed=s).prompt for s in range(300))
    assert beards == 0


def test_country_mix_is_followed():
    keys = [build_prompt(FaceOptions(country="Frankreich"), seed=s).meta["ethnie_key"] for s in range(400)]
    assert len(set(keys)) >= 4  # Frankreich hat eine gemischte Verteilung


def test_process_outputs_250_png_rgb_and_transparent():
    out = process(fake_portrait(), ProcessOptions())
    assert out.size == (250, 250) and out.mode == "RGB"
    t = process(fake_portrait(), ProcessOptions(transparent=True))
    assert t.size == (250, 250) and t.mode == "RGBA"
    alpha = np.asarray(t)[:, :, 3]
    assert alpha[2, 2] < 30            # Ecke = Hintergrund -> transparent
    assert alpha[125, 125] > 200       # Mitte = Person -> deckend


def test_crop_never_exceeds_image():
    img = fake_portrait(512)
    out = crop_to_face(img, (0, 0, 200, 200), ProcessOptions(zoom=3.0))
    assert out.size == (512, 512)  # kein aufgefüllter Rand mehr


def test_watermark_strip_is_cut_off():
    img = fake_portrait(512)
    img.paste((255, 0, 0), (300, 480, 512, 512))  # "Wasserzeichen" unten rechts
    out = np.asarray(process(img, ProcessOptions(crop_bottom=0.09, sharpen=False)))
    red = (out[:, :, 0] > 200) & (out[:, :, 1] < 60)
    assert not red.any()


def test_filename_pattern():
    from fm27facegen import i18n
    meta = {"land": "Österreich", "ethnie_key": "EUR_W", "alter": 16, "seed": 7, "geschlecht": "Männlich",
            "persoenlichkeit": "Sehr ehrgeizig (Very Ambitious)"}
    assert make_filename("", meta, 1) == "Oesterreich_16J_Sehr-ehrgeizig_7.png"          # Standard: Land_Alter_Persönlichkeit_ID
    assert make_filename("{land}_{alter}J_{seed}", meta, 1) == "Oesterreich_16J_7.png"
    assert make_filename("{kaputt}", meta, 3) == "Oesterreich_16J_Sehr-ehrgeizig_7.png"
    meta["persoenlichkeit"] = ""
    assert make_filename("", meta, 1) == "Oesterreich_16J_7.png"                           # ohne Persönlichkeit kein "__"
    try:
        i18n.set_language("en")
        meta["persoenlichkeit"] = "Söldner (Mercenary)"
        assert make_filename("", meta, 1) == "Austria_16J_Mercenary_7.png"
    finally:
        i18n.set_language("de")


def test_old_default_pattern_is_migrated(tmp_path):
    from fm27facegen import settings
    f = tmp_path / "e.json"
    f.write_text(json.dumps({"version": 3, "pattern": "{land}_{alter}J_{seed}"}), encoding="utf-8")
    assert settings.load(f).pattern == "{land}_{alter}J_{persoenlichkeit}_{seed}"
    f.write_text(json.dumps({"version": 3, "pattern": "{nr}_{land}"}), encoding="utf-8")
    assert settings.load(f).pattern == "{nr}_{land}"                                  # eigenes Muster bleibt


class _SD(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _SD.last = body
        buf = io.BytesIO()
        fake_portrait(body["width"]).save(buf, "PNG")
        res = json.dumps({"images": [base64.b64encode(buf.getvalue()).decode()]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)

    def log_message(self, *a):
        pass


def test_end_to_end_with_local_sd_mock(tmp_path):
    srv = HTTPServer(("127.0.0.1", 0), _SD)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        bs = BackendSettings(backend=StableDiffusionWebUIBackend.name, sd_url=f"http://127.0.0.1:{srv.server_port}", gen_size=512)
        gen = Generator(bs, ProcessOptions(), tmp_path)
        faces = gen.run(FaceOptions(country="Brasilien", background=TRANSPARENT_BG), 3, base_seed=1)
        assert len(faces) == 3
        for f in faces:
            im = Image.open(f.path)
            assert im.size == (250, 250) and im.format == "PNG" and im.mode == "RGBA"
        assert (tmp_path / "generiert.csv").exists()
        assert "Brazil" in _SD.last["prompt"] and _SD.last["negative_prompt"]
    finally:
        srv.shutdown()


def test_user_override_file(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "COUNTRIES", dict(data.COUNTRIES))  # nach dem Test zurücksetzen
    p = tmp_path / "laender.json"
    p.write_text(json.dumps({"Färöer": {"en": "Faroe Islands", "mix": {"EUR_N": 100, "XYZ": 3}}}), encoding="utf-8")
    warnings = data.load_user_overrides(p)
    assert data.COUNTRIES["Färöer"] == ("Faroe Islands", {"EUR_N": 100})
    assert warnings and "XYZ" in warnings[0]


def test_settings_migration_to_cutout_style(tmp_path):
    from fm27facegen import settings
    from fm27facegen.prompts import TRANSPARENT_BG
    f = tmp_path / "einstellungen.json"
    f.write_text(json.dumps({"face": {"background": "Hellgrau (Studio)", "country": "Ghana"},
                             "process": {"zoom": 2.1, "face_y": 0.45}, "count": 9}), encoding="utf-8")
    s = settings.load(f)
    assert (s.process.zoom, s.process.face_y, s.face.background) == (1.6, 0.56, TRANSPARENT_BG)
    assert s.face.country == "Ghana" and s.count == 9
    settings.save(s, f)
    s.process.zoom = 2.5
    settings.save(s, f)
    assert settings.load(f).process.zoom == 2.5  # nach der Umstellung bleiben eigene Werte erhalten


def test_segmentation_model_used_when_available(tmp_path, monkeypatch):
    from fm27facegen import segment
    calls = []
    monkeypatch.setattr(segment, "person_mask", lambda img: calls.append(1) or Image.new("L", img.size, 0))
    out = process(fake_portrait(), ProcessOptions(transparent=True))
    assert calls and out.mode == "RGBA" and np.asarray(out)[:, :, 3].max() == 0
