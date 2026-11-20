"""Beim Start prüfen, ob es eine neuere Version gibt (GitHub-Releases des öffentlichen Repositorys).

Gefragt wird nur 'releases/latest' – das sind ausschließlich fertige Versionen, keine Test-Versionen
(Pre-Releases). Gesendet wird nur die Anfrage selbst, keine persönlichen Daten.
"""

from __future__ import annotations

import re

import requests

REPO = "Melvom09867/FM27-Face-Generator"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
ALL_URL = f"https://api.github.com/repos/{REPO}/releases?per_page=20"
RELEASES_URL = f"https://github.com/{REPO}/releases/latest"


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.7.2' -> (1, 7, 2); ungültig -> ()."""
    nums = re.findall(r"\d+", str(text or ""))
    return tuple(int(n) for n in nums[:4])


def _release_info(data: dict) -> dict | None:
    version = str(data.get("tag_name", "")).lstrip("vV")
    if data.get("draft") or not parse_version(version):
        return None
    asset = next((a.get("browser_download_url") for a in data.get("assets") or []
                  if str(a.get("name", "")).lower().endswith("windows.zip")), None)
    return {"version": version, "url": data.get("html_url") or RELEASES_URL, "asset": asset}


def check_latest(timeout: float = 5, include_prereleases: bool = False) -> dict | None:
    """Neueste veröffentlichte Version oder None (offline, Fehler, Limit …).

    include_prereleases=True (Testschalter): auch Testversionen anbieten – dann zählt die höchste Versionsnummer."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "FM27-FaceGenerator"}
    try:
        if include_prereleases:
            r = requests.get(ALL_URL, timeout=timeout, headers=headers)
            if r.status_code != 200:
                return None
            infos = [i for i in (_release_info(d) for d in r.json() or []) if i and i["asset"]]
            return max(infos, key=lambda i: parse_version(i["version"]), default=None)
        r = requests.get(API_URL, timeout=timeout, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("prerelease"):
            return None
        return _release_info(data)
    except Exception:  # noqa: BLE001 – Update-Prüfung darf nie stören
        return None


def should_notify(current: str, latest: str, skipped: str = "") -> bool:
    """Nur bei wirklich neuerer Version – und nicht, wenn genau diese Version ausgeblendet wurde.

    Beispiel: aktuell 1.7.0, 1.7.1 ausgeblendet -> kein Hinweis für 1.7.1, aber wieder für 1.7.2.
    """
    new, cur = parse_version(latest), parse_version(current)
    if not new or new <= cur:
        return False
    return not (skipped and parse_version(skipped) == new)
