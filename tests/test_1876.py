"""1.8.7.6: kein grauer Saum an der Kante, Geschlecht für die Spielerliste."""
import numpy as np
from PIL import Image

from fm27facegen import settings
from fm27facegen.imaging import ProcessOptions, defringe, process


def test_defringe_removes_grey_edge():
    h = 300
    yy, xx = np.mgrid[:h, :h]
    alpha = np.clip((120 - np.hypot(xx - 150, yy - 150)) / 5, 0, 1).astype(np.float32)
    fg, bg = np.array([120, 80, 50.0]), np.array([170, 170, 170.0])
    rgb = (alpha[..., None] * fg + (1 - alpha[..., None]) * bg).astype(np.uint8)
    out = defringe(rgb, alpha).astype(float)
    edge = (alpha > 0.05) & (alpha < 0.9)
    before = np.linalg.norm(rgb[edge] - fg, axis=1).mean()
    after = np.linalg.norm(out[edge] - fg, axis=1).mean()
    assert after < before * 0.2
    assert np.array_equal(out[alpha > 0.95], rgb[alpha > 0.95].astype(float))  # Person bleibt unverändert


def test_sharpen_keeps_alpha_unchanged():
    img = Image.new("RGB", (512, 512), (200, 200, 200))
    out = process(img, ProcessOptions(transparent=True, sharpen=True))
    assert out.mode == "RGBA" and out.size == (250, 250)


def test_list_gender_default_and_saved(tmp_path):
    f = tmp_path / "e.json"
    s = settings.load(f)
    assert s.list_gender == "Männlich"
    s.list_gender = "Weiblich"
    settings.save(s, f)
    assert settings.load(f).list_gender == "Weiblich"


def test_background_patch_next_to_hair_is_removed(monkeypatch):
    """Modell hält einen Fleck Hintergrund neben den Haaren für 'Person' -> muss trotzdem weg."""
    from fm27facegen import imaging, segment
    h = 512
    rgb = np.full((h, h, 3), 205, np.uint8)                     # hellgrauer Hintergrund
    rgb[60:200, 140:380] = (70, 45, 30)                          # Haare
    rgb[150:400, 160:360] = (200, 150, 120)                      # Gesicht
    rgb[400:, 100:420] = (245, 245, 245)                         # weißes Trikot
    mask = np.zeros((h, h), np.uint8)
    mask[60:, 100:420] = 255
    mask[60:200, 380:430] = 255                                  # Fleck Hintergrund rechts neben den Haaren
    monkeypatch.setattr(segment, "person_mask", lambda img: Image.fromarray(mask))
    out = imaging.remove_background(Image.fromarray(rgb), (160, 150, 200, 250))
    a = np.asarray(out)[..., 3]
    assert a[100:180, 390:420].max() < 30        # Fleck entfernt
    assert a[100:180, 200:300].min() > 240       # Haare bleiben
    assert a[430:500, 150:400].min() > 240       # weißes Trikot unter dem Kinn bleibt
