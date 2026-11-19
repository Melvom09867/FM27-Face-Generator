"""Bild-KI-Anbindungen.

* Pollinations  – online, kostenlos, kein Konto nötig (optional API-Key für mehr Tempo)
* Stable Diffusion WebUI (AUTOMATIC1111 / Forge / reForge) – lokal & offline, braucht eigene GPU
"""

from __future__ import annotations

import base64
import io
import re
import threading
import time
import urllib.parse
from dataclasses import dataclass
from typing import Callable

import requests
from PIL import Image

from .i18n import t
from .prompts import FacePrompt

USER_AGENT = "FM27-FaceGenerator/1.7.1"


class BackendError(RuntimeError):
    """Fehler mit verständlicher (deutscher) Meldung für die Oberfläche."""


@dataclass
class BackendSettings:
    backend: str = "Pollinations (online, kostenlos)"
    pollinations_url: str = "https://image.pollinations.ai/prompt/"
    pollinations_model: str = "flux"
    pollinations_token: str = ""
    sd_url: str = "http://127.0.0.1:7860"
    sd_steps: int = 30
    sd_cfg: float = 5.0
    sd_sampler: str = "DPM++ 2M SDE"
    sd_scheduler: str = "Karras"
    gen_size: int = 768
    timeout: int = 180


def _open_image(data: bytes, where: str) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img.convert("RGB")
    except Exception as exc:  # noqa: BLE001
        snippet = data[:200].decode("utf-8", "replace")
        raise BackendError(t("be.invalid_image", where=where, snippet=snippet)) from exc


FREE_INTERVAL = 46.0  # Pollinations ohne Key: 1 Bild alle 45 Sekunden pro IP-Adresse
_last_request = 0.0
_pace_lock = threading.Lock()


class PollinationsBackend:
    name = "Pollinations (online, kostenlos)"
    supports_img2img = False

    def __init__(self, settings: BackendSettings, session: requests.Session | None = None):
        self.s = settings
        self.http = session or requests.Session()
        self.cancel_event: threading.Event | None = None   # vom Generator gesetzt (Abbrechen)
        self.status_cb: Callable[[str], None] | None = None  # Statusmeldungen für die Oberfläche
        self.free_interval = FREE_INTERVAL

    @property
    def watermark_strip(self) -> float:
        """Ohne Key setzt Pollinations unten rechts ein Wasserzeichen -> diesen Streifen abschneiden."""
        return 0.0 if self.s.pollinations_token.strip() else 0.09

    # -------------------------------------------------------------- Warten
    def _status(self, msg: str) -> None:
        if self.status_cb:
            try:
                self.status_cb(msg)
            except Exception:  # noqa: BLE001
                pass

    def _wait(self, seconds: float, why: str) -> None:
        end = time.monotonic() + seconds
        while True:
            left = end - time.monotonic()
            if left <= 0:
                return
            self._status(t("be.left", why=why, s=int(left + 0.99)))
            if self.cancel_event is not None:
                if self.cancel_event.wait(min(1.0, left)):
                    raise BackendError(t("be.cancelled"))
            else:
                time.sleep(min(1.0, left))

    def _pace(self) -> None:
        """Ohne API-Key automatisch das Gratis-Limit einhalten, statt abgelehnt zu werden."""
        global _last_request
        if self.s.pollinations_token.strip():
            return
        with _pace_lock:
            wait = _last_request + self.free_interval - time.monotonic()
        if wait > 0:
            self._wait(wait, t("be.free_wait"))
        with _pace_lock:
            _last_request = time.monotonic()

    @staticmethod
    def _retry_seconds(r: requests.Response, default: float) -> float:
        header = r.headers.get("Retry-After", "")
        if header.strip().isdigit():
            return float(header) + 1
        m = re.search(r"[Rr]etry after (\d+)", r.text or "")
        return float(m.group(1)) + 2 if m else default

    # -------------------------------------------------------------- Erzeugen
    def generate(self, fp: FacePrompt) -> Image.Image:
        base = self.s.pollinations_url.rstrip("/") + "/"
        url = base + urllib.parse.quote(fp.prompt, safe="")
        params = {
            "width": self.s.gen_size,
            "height": self.s.gen_size,
            "seed": fp.seed,
            "model": self.s.pollinations_model or "flux",
            "nologo": "true",
            "private": "true",
            "enhance": "false",
            "negative_prompt": fp.negative,
        }
        headers = {"User-Agent": USER_AGENT}
        token = self.s.pollinations_token.strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
            params["token"] = token

        last_err = ""
        for attempt in range(6):
            self._pace()
            self._status(t("be.generating"))
            try:
                r = self.http.get(url, params=params, headers=headers, timeout=self.s.timeout)
            except requests.RequestException as exc:
                last_err = f"Verbindungsfehler: {exc}"
                self._wait(5 * (attempt + 1), t("be.conn_retry"))
                continue
            if r.status_code == 200:
                return _open_image(r.content, "Pollinations")
            limit_hit = r.status_code == 429 or (r.status_code == 402 and "LIMIT" in (r.text or "").upper())
            if limit_hit:
                last_err = f"HTTP {r.status_code}: Limit erreicht"
                self._wait(self._retry_seconds(r, FREE_INTERVAL), t("be.limit"))
                continue
            if r.status_code in (500, 502, 503, 504):
                last_err = f"HTTP {r.status_code} (Server ausgelastet)"
                self._wait(min(10 * (attempt + 1), 60), t("be.busy"))
                continue
            if r.status_code in (401, 402, 403):
                raise BackendError(
                    t("be.rejected", code=r.status_code)
                    + (t("be.check_key") if token else t("be.get_key"))
                    + t("be.answer", text=r.text[:200])
                )
            raise BackendError(f"Pollinations: HTTP {r.status_code}: {r.text[:200]}")
        raise BackendError(t("be.no_image", err=last_err))


FAST_MODEL_TAGS = ("lightning", "turbo", "hyper", "lcm", "dmd")
FAST_PRESET = {"steps": 6, "cfg_scale": 1.5, "sampler_name": "DPM++ SDE", "scheduler": "Karras"}


def is_fast_model(model_name: str) -> bool:
    """Schnell-Modelle (z. B. 'RealVisXL_V5.0_Lightning') brauchen nur ~6 Schritte und CFG 1–2."""
    name = (model_name or "").lower()
    return any(tag in name for tag in FAST_MODEL_TAGS)


class StableDiffusionWebUIBackend:
    name = "Lokal: Stable Diffusion WebUI (A1111/Forge)"
    supports_img2img = True

    def __init__(self, settings: BackendSettings, session: requests.Session | None = None):
        self.s = settings
        self.http = session or requests.Session()
        self._model: str | None = None  # aktives Modell in der WebUI (einmal abgefragt)

    def _active_model(self) -> str:
        if self._model is None:
            try:
                r = self.http.get(self.s.sd_url.rstrip("/") + "/sdapi/v1/options", timeout=8)
                self._model = str(r.json().get("sd_model_checkpoint", "") or "") if r.status_code == 200 else ""
            except Exception:  # noqa: BLE001
                self._model = ""
        return self._model

    def generate(self, fp: FacePrompt) -> Image.Image:
        return self._call("txt2img", fp)

    def img2img(self, fp: FacePrompt, init: Image.Image, strength: float = 0.5) -> Image.Image:
        """Erzeugt das Bild ausgehend von einem vorhandenen Gesicht (für Alterungs-Sets)."""
        buf = io.BytesIO()
        init.convert("RGB").resize((self.s.gen_size, self.s.gen_size)).save(buf, "PNG")
        extra = {"init_images": [base64.b64encode(buf.getvalue()).decode()], "denoising_strength": strength}
        return self._call("img2img", fp, extra)

    def _call(self, mode: str, fp: FacePrompt, extra: dict | None = None) -> Image.Image:
        url = self.s.sd_url.rstrip("/") + f"/sdapi/v1/{mode}"
        payload = {
            "prompt": fp.prompt,
            "negative_prompt": fp.negative,
            "seed": fp.seed,
            "width": self.s.gen_size,
            "height": self.s.gen_size,
            "steps": self.s.sd_steps,
            "cfg_scale": self.s.sd_cfg,
            "sampler_name": self.s.sd_sampler,
            "scheduler": self.s.sd_scheduler,
            "batch_size": 1,
            "n_iter": 1,
            "restore_faces": False,
        }
        # Lightning/Turbo-Modelle mit normalen Werten (30 Schritte, CFG 5) ergeben überzeichnete Bilder
        if is_fast_model(self._active_model()) and self.s.sd_steps > 12:
            payload.update(FAST_PRESET)
        payload.update(extra or {})
        try:
            r = self.http.post(url, json=payload, timeout=self.s.timeout)
        except requests.RequestException as exc:
            raise BackendError(t("be.sd_unreachable", url=self.s.sd_url)) from exc
        if r.status_code == 422 and "scheduler" in r.text:
            payload.pop("scheduler", None)
            r = self.http.post(url, json=payload, timeout=self.s.timeout)
        if r.status_code != 200:
            raise BackendError(f"Stable Diffusion WebUI: HTTP {r.status_code}: {r.text[:200]}")
        try:
            b64 = r.json()["images"][0]
        except Exception as exc:  # noqa: BLE001
            raise BackendError(t("be.unexpected")) from exc
        if "," in b64[:100]:
            b64 = b64.split(",", 1)[1]
        return _open_image(base64.b64decode(b64), "Stable Diffusion WebUI")


def check_sd_webui(settings: BackendSettings, session: requests.Session | None = None) -> dict:
    """Prüft die Verbindung zur lokalen WebUI. Gibt {'model': aktives Modell, 'models': [...]} zurück."""
    http = session or requests.Session()
    base = settings.sd_url.rstrip("/")
    try:
        r = http.get(base + "/sdapi/v1/options", timeout=8)
    except requests.RequestException as exc:
        raise BackendError(t("be.no_conn", url=settings.sd_url)) from exc
    if r.status_code == 404:
        raise BackendError(t("be.no_api"))
    if r.status_code != 200:
        raise BackendError(t("be.webui_http", code=r.status_code, text=r.text[:200]))
    model = str(r.json().get("sd_model_checkpoint", "") or "")
    models: list[str] = []
    try:
        m = http.get(base + "/sdapi/v1/sd-models", timeout=8)
        if m.status_code == 200:
            models = [str(x.get("model_name") or x.get("title")) for x in m.json()]
    except requests.RequestException:
        pass
    return {"model": model, "models": models, "fast": is_fast_model(model)}


BACKENDS = {
    PollinationsBackend.name: PollinationsBackend,
    StableDiffusionWebUIBackend.name: StableDiffusionWebUIBackend,
}


def make_backend(settings: BackendSettings):
    cls = BACKENDS.get(settings.backend, PollinationsBackend)
    return cls(settings)
