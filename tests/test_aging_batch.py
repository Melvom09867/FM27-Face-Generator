"""1.8.7.4: Dateinamen beim Altern, '+ Jahre', Warteschlange/Sicherung/Rückgängig, Galerie ohne Sicherungskopie."""

from pathlib import Path

from PIL import Image

from fm27facegen import ingame
from fm27facegen.generator import aging_name, list_folder_images


def test_aging_name():
    assert aging_name("Deutschland_16J_Ehrgeizig_123", 20) == "Deutschland_20J_Ehrgeizig_123"
    assert aging_name("Deutschland_16J_123", 34) == "Deutschland_34J_123"
    assert aging_name("Deutschland_16J_123_mit20", 25) == "Deutschland_25J_123"   # alte Benennung
    assert aging_name("Max Mustermann", 20) == "Max Mustermann_20J"
    assert aging_name("newgen_2002044702", 21) == "newgen_2002044702_21J"
    assert aging_name("Max_20J", 24) == "Max_24J"


def test_gallery_skips_backup(tmp_path):
    (tmp_path / "a.png").write_bytes(b"x")
    for sub in ("Deutschland", "Sicherungskopie", "_tmp"):
        (tmp_path / sub).mkdir()
        (tmp_path / sub / f"{sub}.png").write_bytes(b"x")
    names = sorted(p.name for p in list_folder_images(tmp_path))
    assert names == ["Deutschland.png", "a.png"]


def _png(path: Path, color) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color).save(path)
    return path


def test_replace_backup_and_undo(tmp_path):
    out = tmp_path / "out"
    fd = tmp_path / "facedrop" / "karrieren" / "AZ"
    target = _png(fd / "newgen_1.png", (255, 0, 0))
    staged = _png(tmp_path / "stage" / "newgen_1.png", (0, 0, 255))
    done, failed = ingame.apply_replacements([(staged, target)], out)
    assert done == [target] and not failed and not staged.exists()
    assert Image.open(target).getpixel((0, 0)) == (0, 0, 255)           # neues Bild im Spiel
    backups = list((out / ingame.BACKUP_DIR).rglob("newgen_1.png"))
    assert len(backups) == 1 and Image.open(backups[0]).getpixel((0, 0)) == (255, 0, 0)
    assert ingame.undo_count(out) == 1
    restored, failed = ingame.undo_last(out)
    assert restored == [target] and not failed
    assert Image.open(target).getpixel((0, 0)) == (255, 0, 0)           # altes Bild zurück
    assert ingame.undo_count(out) == 0                                   # nur einmal rückgängig
