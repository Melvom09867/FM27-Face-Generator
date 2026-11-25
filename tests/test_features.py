import json
import threading
from http.server import HTTPServer

from PIL import Image

from fm27facegen.backends import BackendSettings, StableDiffusionWebUIBackend
from fm27facegen.generator import Generator, Job, aging_jobs, parse_ages
from fm27facegen.imaging import ProcessOptions
from fm27facegen.playerlist import load_players, parse_players
from fm27facegen.prompts import FaceOptions, build_prompt

from test_core import _SD

FM_HTML = """<html><body><table>
<tr><th>Inf</th><th>Name</th><th>Position</th><th>Alter</th><th>Nat</th><th>2. Nat</th><th>UID</th></tr>
<tr><td></td><td>Jonas Müller</td><td>ST</td><td>15</td><td>GER</td><td></td><td>2000123456</td></tr>
<tr><td></td><td>Kwame Boateng</td><td>DM</td><td>16</td><td>GER</td><td>GHA</td><td>2000123457</td></tr>
<tr><td></td><td>Luca Rossi</td><td>AMC</td><td>16 Jahre</td><td>Italien</td><td></td><td>2000123458</td></tr>
<tr><td></td><td>Jean Ndayishimiye</td><td>D</td><td>15</td><td>BDI</td><td></td><td>2000123459</td></tr>
</table></body></html>"""

FM_TXT = """| Name           | Age | Nationality | Second Nationality |
| -------------- | --- | ----------- | ------------------ |
| Tom Smith      | 16  | England     | Jamaica            |
| Kenji Sato     | 15  | Japan       |                    |
"""


def test_parse_fm_html():
    players, warnings = parse_players(FM_HTML, ".html")
    assert [p.name for p in players] == ["Jonas Müller", "Kwame Boateng", "Luca Rossi", "Jean Ndayishimiye"]
    assert players[1].country == "Deutschland" and players[1].country2 == "Ghana"
    assert players[2].age == 16 and players[2].country == "Italien"
    assert players[0].uid == "2000123456"
    assert players[3].country == "Burundi" and not warnings


def test_parse_fm_txt_and_csv(tmp_path):
    players, _ = parse_players(FM_TXT, ".txt")
    assert [(p.name, p.country, p.country2, p.age) for p in players] == [
        ("Tom Smith", "England", "Jamaika", 16), ("Kenji Sato", "Japan", None, 15)]
    f = tmp_path / "liste.csv"
    f.write_bytes("Name;Nation;Alter\nÉmile Dubois;Frankreich;17\n".encode("cp1252"))
    players, _ = load_players(f)
    assert players[0].name == "Émile Dubois" and players[0].country == "Frankreich" and players[0].age == 17


def test_unknown_country_is_reported():
    players, warnings = parse_players("Name;Nation;Alter\nA B;Atlantis;16\n", ".csv")
    assert players[0].country is None and "Atlantis" in warnings[0]
    p = build_prompt(FaceOptions(country="Atlantis"), seed=1)
    assert "from Atlantis" in p.prompt and p.meta["ethnie_key"] == "KI"


def test_missing_header_gives_error():
    players, warnings = parse_players("foo;bar\n1;2\n", ".csv")
    assert not players and "Kopfzeile" in warnings[0]


def test_aging_keeps_features_and_changes_age():
    o = FaceOptions(country="Brasilien", second_country="Nigeria", parent_mode="Zufällig")
    a = build_prompt(o, seed=99, age=16)
    b = build_prompt(o, seed=99, age=30)
    for key in ("ethnie", "haare", "herkunft"):
        assert a.meta[key] == b.meta[key]
    assert a.meta["alter"] == 16 and b.meta["alter"] == 30
    assert "30-year-old man" in b.prompt and "fine lines" in b.prompt
    assert "professional footballer" in b.prompt


def test_parent_modes():
    both = FaceOptions(country="Deutschland", second_country="Ghana", parent_mode="Beide Eltern aus diesem Land")
    one = FaceOptions(country="Deutschland", second_country="Ghana", parent_mode="Ein Elternteil (gemischt)")
    assert {build_prompt(both, seed=s).meta["ethnie_key"] for s in range(30)} == {"AFR_W"}
    assert {build_prompt(one, seed=s).meta["ethnie_key"] for s in range(30)} == {"EUR_W+AFR_W"}
    assert "footballer from Germany, family roots in Ghana" in build_prompt(both, seed=1).prompt


def test_parse_ages():
    assert parse_ages("16, 20; 25-27 99 abc") == [16, 20, 25, 26, 27]


def test_list_and_aging_end_to_end(tmp_path):
    srv = HTTPServer(("127.0.0.1", 0), _SD)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        bs = BackendSettings(backend=StableDiffusionWebUIBackend.name, sd_url=f"http://127.0.0.1:{srv.server_port}", gen_size=512)
        gen = Generator(bs, ProcessOptions(), tmp_path)
        players, _ = parse_players(FM_HTML, ".html")
        jobs = [Job(options=FaceOptions(country=p.country or p.nation_raw,
                                        second_country=p.country2 or "—"), age=p.age, filename=p.name) for p in players]
        faces = gen.run_jobs(jobs)
        assert sorted(f.path.name for f in faces) == sorted(f"{p.name}.png" for p in players)
        assert "16-year-old" in faces[1].prompt.prompt

        aging = aging_jobs(faces[0], [15, 20, 30])  # 15 = aktuelles Alter -> übersprungen
        assert [j.age for j in aging] == [20, 30]
        aged = gen.run_jobs(aging)
        assert [f.path.name for f in aged] == ["Jonas Müller_20J.png", "Jonas Müller_30J.png"]
        assert "init_images" in _SD.last and _SD.last["seed"] == faces[0].prompt.seed  # lokal: img2img
        assert Image.open(aged[0].path).size == (250, 250)

        # Neu würfeln mit überschreiben behält den Dateinamen
        g2 = Generator(bs, ProcessOptions(), tmp_path, overwrite=True)
        again = g2.run_jobs([Job(options=faces[0].options, filename=faces[0].path.stem)])
        assert again[0].path == faces[0].path
    finally:
        srv.shutdown()


def test_check_sd_webui(tmp_path):
    from http.server import BaseHTTPRequestHandler

    import pytest

    from fm27facegen.backends import BackendError, check_sd_webui

    class H(BaseHTTPRequestHandler):
        api = True

        def do_GET(self):  # noqa: N802
            if not H.api:
                self.send_response(404); self.end_headers(); return
            body = {"/sdapi/v1/options": {"sd_model_checkpoint": "RealVisXL_V5.0.safetensors"},
                    "/sdapi/v1/sd-models": [{"model_name": "RealVisXL_V5.0"}]}[self.path]
            data = json.dumps(body).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(data))); self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        s = BackendSettings(sd_url=f"http://127.0.0.1:{srv.server_port}")
        assert check_sd_webui(s) == {"model": "RealVisXL_V5.0.safetensors", "models": ["RealVisXL_V5.0"], "fast": False}
        H.api = False
        with pytest.raises(BackendError, match="--api"):
            check_sd_webui(s)
    finally:
        srv.shutdown()
    with pytest.raises(BackendError, match="Keine Verbindung"):
        check_sd_webui(BackendSettings(sd_url="http://127.0.0.1:9"))


def test_lightning_model_gets_fast_settings():
    from fm27facegen.backends import StableDiffusionWebUIBackend, is_fast_model
    assert is_fast_model("RealVisXL_V5.0_Lightning_fp16.safetensors [abc]")
    assert not is_fast_model("RealVisXL_V5.0_fp16.safetensors")

    class Resp:
        def __init__(self, data): self.status_code, self._d, self.text = 200, data, ""
        def json(self): return self._d

    class Http:
        sent = None
        def get(self, url, timeout): return Resp({"sd_model_checkpoint": "RealVisXL_V5.0_Lightning_fp16.safetensors"})
        def post(self, url, json, timeout):
            Http.sent = json
            import base64, io
            buf = io.BytesIO(); Image.new("RGB", (64, 64)).save(buf, "PNG")
            return Resp({"images": [base64.b64encode(buf.getvalue()).decode()]})

    b = StableDiffusionWebUIBackend(BackendSettings(), session=Http())
    b.generate(build_prompt(FaceOptions(), seed=1))
    assert Http.sent["steps"] == 6 and Http.sent["cfg_scale"] == 1.5 and Http.sent["sampler_name"] == "DPM++ SDE"
