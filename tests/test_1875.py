"""1.8.7.5: Alterung ohne 'Abdriften', Speicherort graphics\\faces, Sortierung nach Nachnamen."""
import json

from PIL import Image

from fm27facegen import ingame, settings
from fm27facegen.backends import BackendSettings
from fm27facegen.generator import BASE_KEY, Generator, Job, aging_jobs, load_face
from fm27facegen.imaging import ProcessOptions
from fm27facegen.prompts import FaceOptions

from test_core import fake_portrait


class Img2ImgBackend:
    supports_img2img = True

    def __init__(self):
        self.calls = []  # ("txt", Alter) oder ("img", Alter, id der Vorlage)

    def generate(self, fp):
        self.calls.append(("txt", fp.meta.get("alter")))
        return fake_portrait(512)

    def img2img(self, fp, init, strength):
        self.calls.append(("img", fp.meta.get("alter"), init.tobytes()[:64]))
        return fake_portrait(512)


def _gen(tmp_path, backend):
    return Generator(BackendSettings(), ProcessOptions(), tmp_path, backend=backend)


def test_seasons_always_start_from_the_original_face(tmp_path):
    be = Img2ImgBackend()
    gen = _gen(tmp_path, be)
    face = gen.run_jobs([Job(FaceOptions(country="Niederlande", age_min=16, age_max=16), seed=77)])[0]
    assert BASE_KEY in Image.open(face.path).info
    origin = load_face(face.path).base.tobytes()[:64]

    path = face.path
    for season in range(4):  # 4× Saison +1
        loaded = load_face(path)
        assert loaded.base_age == 16
        job = aging_jobs(loaded, [], relative=1)[0]
        path = gen.run_jobs([job])[0].path
    ages = [c[1] for c in be.calls if c[0] == "img"]
    assert ages == [17, 18, 19, 20]
    # jede Alterung nutzt dieselbe Vorlage (das erste Bild) – nichts schaukelt sich auf
    assert {c[2] for c in be.calls if c[0] == "img"} == {origin}


def test_old_aged_image_rebuilds_its_original(tmp_path):
    """Bild aus 1.8.7.4 (ohne Ausgangsbild, schon gealtert): erst das 16-jährige Gesicht neu, dann altern."""
    be = Img2ImgBackend()
    gen = _gen(tmp_path, be)
    face = gen.run_jobs([Job(FaceOptions(age_min=16, age_max=16), seed=5, age=21)])[0]
    im = Image.open(face.path)
    info = json.loads(im.info["fm27facegen"])
    info.pop("base_age")
    old = tmp_path / "alt.png"
    from fm27facegen.imaging import save_png
    save_png(im.copy(), old, {"fm27facegen": json.dumps(info)})  # ohne Ausgangsbild
    from fm27facegen import generator
    generator.raw_cache_dir().mkdir(parents=True, exist_ok=True)
    for f in generator.raw_cache_dir().glob("*"):
        f.unlink()
    be.calls.clear()
    job = aging_jobs(load_face(old), [], relative=1)[0]
    assert job.rebuild_base and job.base_age == 16
    gen.run_jobs([job])
    assert be.calls[0] == ("txt", 16) and be.calls[1][:2] == ("img", 22)


def test_output_dir_moves_to_faces_with_backup(tmp_path):
    old = tmp_path / "FM" / "graphics" / "FM27 Face Generator"
    (old / ingame.BACKUP_DIR / "2026-11-20").mkdir(parents=True)
    (old / "Ismail Ka.png").write_bytes(b"x")
    backup = old / ingame.BACKUP_DIR / "2026-11-20" / "a.png"
    backup.write_bytes(b"y")
    (old / ingame.BACKUP_DIR / ingame.MANIFEST).write_text(
        json.dumps({"items": [{"target": "t.png", "backup": str(backup)}]}), encoding="utf-8")
    cfg_file = tmp_path / "einstellungen.json"
    cfg_file.write_text(json.dumps({"output_dir": str(old), "version": 4}), encoding="utf-8")

    s = settings.load(cfg_file)
    new = tmp_path / "FM" / "graphics" / "faces" / "FM27 Face Generator"
    assert s.output_dir == str(new) and s.moved_from == str(old)
    assert (new / "Ismail Ka.png").exists() and not old.exists()
    assert ingame.undo_count(new) == 1  # Rückgängig findet die verschobene Sicherungskopie
    assert settings.fm_output_dir(tmp_path / "FM") == new


def test_surname_sort():
    from fm27facegen.gui import surname_key
    names = ["Merijn van Dijk", "Ismail Ka", "Jur Schipper", "Kevin van Ouytsel", "Christian Šimunović", "Latrell Aken"]
    assert sorted(names, key=surname_key) == ["Latrell Aken", "Merijn van Dijk", "Ismail Ka", "Kevin van Ouytsel",
                                               "Jur Schipper", "Christian Šimunović"]


def test_fast_mode_uses_single_step_sampler():
    from fm27facegen import backends

    class Resp:
        status_code = 200
        text = ""

        def __init__(self, data):
            self._d = data

        def json(self):
            return self._d

    class Session:
        def __init__(self):
            self.payload = None

        def get(self, url, timeout=0):
            return Resp({"sd_model_checkpoint": "RealVisXL_V5.0_Lightning"})

        def post(self, url, json=None, timeout=0):
            self.payload = json
            import base64, io
            buf = io.BytesIO()
            Image.new("RGB", (8, 8)).save(buf, "PNG")
            return Resp({"images": [base64.b64encode(buf.getvalue()).decode()]})

    from fm27facegen.prompts import build_prompt
    for fast, sampler in ((False, "DPM++ SDE"), (True, "Euler")):
        sess = Session()
        be = backends.StableDiffusionWebUIBackend(BackendSettings(sd_fast=fast), session=sess)
        be.generate(build_prompt(FaceOptions(), seed=1))
        assert sess.payload["sampler_name"] == sampler and sess.payload["steps"] == 6
