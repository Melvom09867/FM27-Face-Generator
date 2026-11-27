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
