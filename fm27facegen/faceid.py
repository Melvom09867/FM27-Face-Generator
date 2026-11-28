"""Gesichts-Erweiterung für Forge: IP-Adapter FaceID Plus v2 (SDXL).

Beim Altern bekommt Forge zusätzlich das Ausgangsgesicht als Vorlage – die Person bleibt deutlich besser
erkennbar, vor allem bei echten Fotos. Braucht zwei Dateien in Forges Modell-Ordnern (ca. 1,9 GB);
die Gesichtserkennung (InsightFace) und CLIP-H lädt Forge beim ersten Einsatz selbst nach.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import requests

HF = "https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/"
MODEL_FILE = "ip-adapter-faceid-plusv2_sdxl.bin"
LORA_FILE = "ip-adapter-faceid-plusv2_sdxl_lora.safetensors"
FILES = [(MODEL_FILE, "ControlNet", 1_487_555_181), (LORA_FILE, "Lora", 371_842_896)]
MODULE = "InsightFace+CLIP-H (IPAdapter)"
LORA_WEIGHT = 0.6


def models_dir(forge_dir: str | Path) -> Path | None:
    """Forges 'models'-Ordner (Paket von lllyasviel: <Ordner>\\webui\\models, sonst <Ordner>\\models)."""
    if not forge_dir:
        return None
    base = Path(forge_dir)
    for cand in (base / "webui" / "models", base / "models"):
        if cand.is_dir():
            return cand
    return None


def installed(forge_dir: str | Path) -> bool | None:
    """True/False, ob beide Dateien da sind – None, wenn der Forge-Ordner unbekannt ist."""
    md = models_dir(forge_dir)
    if md is None:
        return None
    return all((md / sub / name).is_file() for name, sub, _size in FILES)


def download(forge_dir: str | Path, progress: Callable[[int, int], None] | None = None,
             stop: Callable[[], bool] | None = None) -> None:
    """Lädt die fehlenden Dateien in Forges Modell-Ordner (erst als .part, dann umbenannt)."""
    md = models_dir(forge_dir)
    if md is None:
        raise OSError("Forge-Ordner nicht gefunden")
    todo = [(n, sub, size) for n, sub, size in FILES if not (md / sub / n).is_file()]
    total = sum(size for _n, _s, size in todo) or 1
    done = 0
    for name, sub, _size in todo:
        target = md / sub / name
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_suffix(target.suffix + ".part")
        with requests.get(HF + name, stream=True, timeout=60) as r:
            r.raise_for_status()
            with part.open("wb") as f:
                for chunk in r.iter_content(1 << 20):
                    if stop and stop():
                        raise InterruptedError
                    f.write(chunk)
                    done += len(chunk)
                    if progress:
                        progress(done, total)
        part.replace(target)


def controlnet_unit(model: str, image_b64: str, weight: float) -> dict:
    return {"enabled": True, "module": MODULE, "model": model, "weight": weight, "image": image_b64,
            "resize_mode": "Crop and Resize", "pixel_perfect": True, "control_mode": "Balanced",
            "guidance_start": 0.0, "guidance_end": 1.0}
