"""FaceDrop-Erkennung, Doppelte-Bilder-Suche, Zwischenablage-Format, Selbst-Update (ohne echtes Windows)."""

import os
import struct
import time
import zipfile
from pathlib import Path

from fm27facegen import facedrop, selfupdate, settings, update, winclip

PNG_OURS = b"\x89PNG\r\n\x1a\n" + b"iTXtfm27facegen\x00" + b"x" * 500


def _make_fd(user_dir: Path, version="0.4.1", career="AZ", mtime=None) -> Path:
    fd = user_dir / "facedrop"
    (fd / "karrieren" / career).mkdir(parents=True)
    (fd / "startschutz.txt").write_text(f"{version} / 27.1.0.2505117\n0\n", encoding="utf-8")
    (fd / "karrieren.json").write_text('{"%s": "%s Karriere"}' % (career, career), encoding="utf-8")
    (fd / "platzhalter.txt").write_text("2000532754=person_default\n12095984=person_default\n", encoding="utf-8")
    if mtime:
        os.utime(fd / "startschutz.txt", (mtime, mtime))
    return fd


def test_parse_launch_option_with_escaped_quotes():
    text = '"LaunchOptions"\t\t"user_data_location=\\"C:\\\\Privat\\\\FM User Ordner\\""'
    assert facedrop.parse_user_data_locations(text) == ["C:\\Privat\\FM User Ordner"]
    text = '"LaunchOptions"  "-windowed user_data_location=D:\\\\FM27 -nosound"'
    assert facedrop.parse_user_data_locations(text) == ["D:\\FM27"]
    assert facedrop.parse_user_data_locations('"LaunchOptions" "-windowed"') == []


def test_steam_launch_option_and_active_folder(tmp_path, monkeypatch):
    home = tmp_path / "home"
    steam = home / ".steam" / "steam"
    custom = tmp_path / "FM User Ordner"
    cfg = steam / "userdata" / "123" / "config"
    cfg.mkdir(parents=True)
    path_txt = str(custom).replace("\\", "\\\\")
    (cfg / "localconfig.vdf").write_text(
        '"UserLocalConfigStore"\n{\n "apps"\n {\n  "3551340"\n  {\n   "LaunchOptions"  '
        f'"user_data_location=\\"{path_txt}\\""\n  }}\n }}\n}}\n', encoding="utf-8")
    docs_fm = home / "Documents" / "Sports Interactive" / "Football Manager 27"
    old = time.time() - 3600
    _make_fd(docs_fm, mtime=old)            # alter Ort (Sicherung nach Umzug)
    active = _make_fd(custom, career="Benfica")  # hier schreibt FaceDrop gerade
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(facedrop.sys, "platform", "linux")

    assert steam in facedrop.steam_roots()
    assert facedrop.steam_user_data_locations() == [custom]
    assert facedrop.find_facedrop_dir() == active
    # "FM-Ordner suchen" findet zuerst den eigenen Benutzerordner aus der Startoption
    found = settings.find_fm_folders()
    assert found[0] == custom and docs_fm in found


def test_facedrop_cfg_folder(tmp_path):
    game = tmp_path / "steamapps" / "common" / "Football Manager 27"
    (game / "BepInEx" / "config").mkdir(parents=True)
    (game / "BepInEx" / "config" / facedrop.CFG_NAME).write_text(
        "[Speicherort]\n\n## Ordner\nFM-Benutzerordner = D:\\FM27\n", encoding="utf-8")
    assert facedrop.fm_game_dirs([tmp_path]) == [game]
    assert facedrop.facedrop_cfg_user_dirs([game]) == [Path("D:\\FM27")]


def test_read_info_and_images(tmp_path):
    fd = _make_fd(tmp_path)
    (fd / "karrieren" / "AZ" / "newgen_2002044702.png").write_bytes(PNG_OURS)
    (fd / "club_123.png").write_bytes(b"logo")
    (fd / "person_default.png").write_bytes(b"x")
    (fd / "12095984.png").write_bytes(b"real")
    info = facedrop.read_info(fd)
    assert info.version == "0.4.1" and info.careers == {"AZ": "AZ Karriere"} and info.without_face == 2
    assert [p.name for p in facedrop.career_images(fd, "AZ")] == ["newgen_2002044702.png"]
    assert [p.name for p in facedrop.career_images(fd, None)] == ["12095984.png"]  # keine Logos/Platzhalter
    assert facedrop.player_id(fd / "karrieren" / "AZ" / "newgen_2002044702.png") == "2002044702"
    assert facedrop.is_facedrop_path(fd / "karrieren" / "AZ" / "x.png")
    assert facedrop.is_facedrop_path(tmp_path / "graphics" / "facedrop" / "x.png")
    assert not facedrop.is_facedrop_path(tmp_path / "FM27 Faces" / "x.png")


def test_find_duplicates(tmp_path):
    fd = _make_fd(tmp_path / "fm")
    out = tmp_path / "out"
    out.mkdir()
    ours = out / "Deutschland_20J_x_1.png"
    ours.write_bytes(PNG_OURS)
    other = out / "Deutschland_21J_x_2.png"
    other.write_bytes(PNG_OURS + b"anders")
    foreign = out / "fremd.png"  # gleicher Inhalt, aber nicht vom Generator -> nie anfassen
    foreign.write_bytes(b"\x89PNG fremd")
    copy = fd / "karrieren" / "AZ" / "newgen_1.png"
    copy.write_bytes(PNG_OURS)
    (fd / "karrieren" / "AZ" / "newgen_2.png").write_bytes(b"\x89PNG fremd")
    # FaceDrops eigene Kopie unter graphics\facedrop gilt nie als "unsere" Datei
    gfx = tmp_path / "fm" / "graphics" / "facedrop"
    gfx.mkdir(parents=True)
    (gfx / "x.png").write_bytes(PNG_OURS)
    index = facedrop.facedrop_index(fd)
    own = [ours, other, foreign, gfx / "x.png"]
    assert facedrop.find_duplicates(own, index) == {ours: copy}
    assert facedrop.find_duplicates(own, {}) == {}


def test_dropfiles_bytes():
    data = winclip.dropfiles_bytes([Path("/tmp/a.png")])
    p_files, _x, _y, _nc, wide = struct.unpack("<IiiII", data[:20])
    assert p_files == 20 and wide == 1
    names = data[20:].decode("utf-16-le")
    assert names.endswith("a.png\0\0")
    assert winclip.copy_files([]) is False


def test_selfupdate_unpack_and_script(tmp_path):
    z = tmp_path / "pkg.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("FM27-FaceGenerator.exe", b"MZ new")
        zf.writestr("PatchNotes_DE.txt", "neu")
        zf.writestr("laender.json", "{}")  # Nutzerdatei nie überschreiben
    target = tmp_path / "app"
    target.mkdir()
    (target / "laender.json").write_text("mein", encoding="utf-8")
    new = selfupdate.unpack(z, target, "FM27-FaceGenerator.exe")
    assert new.name == "FM27-FaceGenerator.exe.new" and new.read_bytes() == b"MZ new"
    assert (target / "PatchNotes_DE.txt").read_text(encoding="utf-8") == "neu"
    assert (target / "laender.json").read_text(encoding="utf-8") == "mein"
    script = selfupdate.helper_script(4242, Path("C:/A B/x.exe"), Path("C:/A B/x.exe.new"))
    assert 'PID eq 4242' in script and 'move /y' in script and 'start ""' in script
    assert selfupdate.can_self_update() is False  # nicht als .exe gestartet


def test_update_returns_asset(monkeypatch):
    class R:
        status_code = 200

        @staticmethod
        def json():
            return {"tag_name": "v1.9.0", "html_url": "https://x/rel", "prerelease": False,
                    "assets": [{"name": "FM27-FaceGenerator-windows.zip", "browser_download_url": "https://x/z.zip"}]}

    monkeypatch.setattr(update.requests, "get", lambda *a, **k: R())
    assert update.check_latest() == {"version": "1.9.0", "url": "https://x/rel", "asset": "https://x/z.zip"}


def test_settings_facedrop_fields(tmp_path):
    p = tmp_path / "e.json"
    s = settings.AppSettings()
    assert s.facedrop_cleanup == "ask" and s.facedrop_dir == ""
    s.facedrop_cleanup, s.facedrop_dir = "auto", "D:\\FM27\\facedrop"
    settings.save(s, p)
    s2 = settings.load(p)
    assert s2.facedrop_cleanup == "auto" and s2.facedrop_dir == "D:\\FM27\\facedrop"


def test_update_with_prereleases(monkeypatch):
    rels = [{"tag_name": "v1.8.0", "prerelease": False, "html_url": "a",
             "assets": [{"name": "FM27-FaceGenerator-windows.zip", "browser_download_url": "z0"}]},
            {"tag_name": "v1.8.4", "prerelease": True, "html_url": "b",
             "assets": [{"name": "FM27-FaceGenerator-windows.zip", "browser_download_url": "z4"}]},
            {"tag_name": "v1.9.0", "draft": True, "assets": [{"name": "x-windows.zip"}]}]

    class R:
        status_code = 200

        @staticmethod
        def json():
            return rels

    monkeypatch.setattr(update.requests, "get", lambda *a, **k: R())
    assert update.check_latest(include_prereleases=True) == {"version": "1.8.4", "url": "b", "asset": "z4"}
