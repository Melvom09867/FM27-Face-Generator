"""KI-Freistellung (Person vom Hintergrund trennen) für den FM-Cut-out-Look.

Verwendet das Modell ``u2net_human_seg`` (aus dem Open-Source-Projekt rembg, ONNX-Format),
ausgeführt direkt mit OpenCV – keine zusätzliche Bibliothek nötig.
Das Modell (~176 MB) wird beim ersten Freistellen einmalig heruntergeladen und unter
``%APPDATA%\\FM27FaceGenerator\\models`` gespeichert.
"""

from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from .i18n import t

try:
    import cv2
except Exception:  # noqa: BLE001
    cv2 = None

MODEL_NAME = "u2net_human_seg.onnx"
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx"
MODEL_SHA256 = "01eb6a29a5c4d8edb30b56adad9bb3a2a0535338e480724a213e0acfd2d1c73c"
MODEL_SIZE_MB = 176

_net = None
_lock = threading.Lock()


def models_dir() -> Path:
    base = os.environ.get("APPDATA")
    root = Path(base) / "FM27FaceGenerator" if base else Path.home() / ".fm27facegenerator"
    return root / "models"


def model_path() -> Path:
    return models_dir() / MODEL_NAME


def model_available() -> bool:
    return model_path().exists()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_model(status: Callable[[str], None] | None = None) -> bool:
    """Lädt das Modell herunter, falls es fehlt. Gibt True zurück, wenn es danach verfügbar ist."""
    path = model_path()
    if path.exists():
        return True
    import requests  # erst hier, damit die Bildverarbeitung auch ohne Netzwerk-Import läuft

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    say = status or (lambda _m: None)
    try:
        with requests.get(MODEL_URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0)) or MODEL_SIZE_MB * 1024 * 1024
            done = 0
            with tmp.open("wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
                    done += len(chunk)
                    say(t("seg.download", pct=done * 100 // total, done=done >> 20, total=total >> 20))
        if _sha256(tmp) != MODEL_SHA256:
            tmp.unlink(missing_ok=True)
            say(t("seg.corrupt"))
            return False
        tmp.replace(path)
        return True
    except Exception as exc:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        say(t("seg.failed", e=exc))
        return False


def _get_net():
    global _net
    with _lock:
        if _net is None and cv2 is not None and model_available():
            _net = cv2.dnn.readNetFromONNX(str(model_path()))
        return _net


def person_mask(img: Image.Image) -> Image.Image | None:
    """Alpha-Maske (L, 0–255) der Person oder None, wenn das Modell nicht verfügbar ist."""
    net = _get_net()
    if net is None:
        return None
    rgb = img.convert("RGB")
    a = np.asarray(rgb.resize((320, 320), Image.Resampling.BICUBIC)).astype(np.float32) / 255.0
    a = (a - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    blob = a.transpose(2, 0, 1)[None].astype(np.float32)
    with _lock:  # cv2.dnn-Netze sind nicht thread-sicher
        net.setInput(blob)
        out = net.forward()
    pred = out.reshape(out.shape[-2], out.shape[-1])
    pred = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
    # Kanten straffen: Halbtransparenz nur in einem schmalen Übergang behalten
    pred = np.clip((pred - 0.15) / 0.7, 0.0, 1.0)
    mask = Image.fromarray((pred * 255).astype(np.uint8)).resize(rgb.size, Image.Resampling.BILINEAR)
    return mask
