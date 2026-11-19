import csv
import json

import pytest
from PIL import Image

from fm27facegen.generator import META_KEY, RenameError, aging_jobs, load_face, rename_face, trash_files
from fm27facegen.prompts import SHIRT_PATTERNS, FaceOptions, build_prompt

from test_core import fake_portrait


def test_rename_keeps_ageing_possible_for_csv_images(tmp_path):
    img = tmp_path / "Ghana_16J_77.png"
    fake_portrait(250).save(img)
    with (tmp_path / "generiert.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["datei", "zeit", "land", "herkunft", "ethnie", "geschlecht", "alter", "haare", "seed", "prompt"])
        w.writerow([img.name, "x", "Ghana", "Ghana", "Westafrikanisch", "Männlich", "16", "black hair", "77",
                    "photo of a 16-year-old teenage boy, Black West African, youth footballer from Ghana"])
    face = load_face(img)
    assert face.source == "log"
    new = rename_face(face, "Kwame Mensah.png")
    assert new.name == "Kwame Mensah.png" and new.exists() and not img.exists()
    # Infos stecken jetzt in der Datei selbst -> nach dem Umbenennen weiter alterbar
    reloaded = load_face(new)
    assert reloaded.source == "metadata" and reloaded.prompt.seed == 77
    assert json.loads(Image.open(new).info[META_KEY])["legacy"] is True
    assert aging_jobs(reloaded, [25])[0].filename == "Kwame Mensah_mit25"


def test_rename_refuses_existing_name(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    fake_portrait(64).save(a)
    fake_portrait(64).save(b)
    face = load_face(a)
    with pytest.raises(RenameError):
        rename_face(face, "b")
    assert face.path == a and a.exists()
    assert rename_face(face, 'Jonas: "Müller"?').name == "Jonas_ _Müller__.png"  # unerlaubte Zeichen ersetzt


def test_trash_files(tmp_path, monkeypatch):
    import send2trash
    moved = []

    def fake(path):
        moved.append(path)
        if "bad" in path:
            raise OSError("locked")

    monkeypatch.setattr(send2trash, "send2trash", fake)
    ok, bad, missing = tmp_path / "ok.png", tmp_path / "bad.png", tmp_path / "missing.png"
    ok.write_bytes(b"x")
    bad.write_bytes(b"x")
    assert trash_files([ok, bad, missing]) == [bad]
    assert str(missing) not in moved


def test_shirt_patterns():
    base = dict(clothing="Trikot ohne Logo", shirt_color="Rot", shirt_color2="Weiß")
    p = lambda pat: build_prompt(FaceOptions(**base, shirt_pattern=pat), seed=1).prompt
    assert "a plain red football jersey without logos or text" in p("Einfarbig")
    assert "red and white vertically striped football jersey, no logos or text" in p("Längsstreifen")
    assert "with contrasting white sleeves" in p("Andersfarbige Ärmel")
    # Zweitfarbe zufällig: nie gleich der Hauptfarbe
    for s in range(50):
        q = build_prompt(FaceOptions(shirt_color="Rot", shirt_pattern="Querstreifen"), seed=s).prompt
        assert "a red and red" not in q and "horizontally hooped" in q
    assert set(SHIRT_PATTERNS) >= {"Einfarbig", "Längsstreifen", "Querstreifen"}
