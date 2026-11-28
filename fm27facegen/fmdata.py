"""Zuletzt geladener FM-Export (Spielerliste) – damit Alterung und fremde Bilder die echten Daten aus FM kennen.

Gespeichert wird nur, was im Export steht: Name, UID, Alter, Land, 2. Nationalität, Persönlichkeit.
Zuordnung zu einem Bild: zuerst über die Spieler-ID im FaceDrop-Dateinamen (newgen_123 / dbperson_123),
sonst über den Dateinamen = Spielername (Bilder aus der Spielerliste).
"""
from __future__ import annotations

import json
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

from .playerlist import Player

FILE_NAME = "fm_export.json"


def _path() -> Path:
    from .settings import config_dir
    return config_dir() / FILE_NAME


def _norm(name: str) -> str:
    plain = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return " ".join(plain.casefold().replace("_", " ").split())


@dataclass
class ExportPlayer:
    name: str
    uid: str = ""
    age: int | None = None
    country: str | None = None
    country2: str | None = None
    personality: str | None = None


class FMExport:
    def __init__(self, players: list[ExportPlayer], stamp: float = 0.0, source: str = ""):
        self.players = players
        self.stamp = stamp
        self.source = source
        self._by_uid = {p.uid: p for p in players if p.uid}
        self._by_name = {_norm(p.name): p for p in players if p.name}

    def __len__(self) -> int:
        return len(self.players)

    def find(self, path: str | Path | None = None, name: str | None = None) -> ExportPlayer | None:
        """Spieler zu einem Bild: Spieler-ID im FaceDrop-Namen, sonst Dateiname/Name = Spielername."""
        if path is not None:
            from .facedrop import player_id
            pid = player_id(Path(path))
            if pid and pid in self._by_uid:
                return self._by_uid[pid]
            stem = Path(path).stem
            hit = self._by_name.get(_norm(stem))
            if hit:
                return hit
        if name:
            return self._by_name.get(_norm(name))
        return None

    @property
    def date_text(self) -> str:
        return time.strftime("%d.%m.%Y %H:%M", time.localtime(self.stamp)) if self.stamp else ""


def save_export(players: list[Player], source: str = "") -> FMExport:
    items = [ExportPlayer(name=p.name, uid=p.uid or "", age=p.age, country=p.country,
                          country2=p.country2, personality=p.personality) for p in players]
    exp = FMExport(items, time.time(), source)
    try:
        f = _path()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"time": exp.stamp, "source": source, "players": [asdict(p) for p in items]},
                                ensure_ascii=False, indent=0), encoding="utf-8")
    except OSError:
        pass
    return exp


def load_export() -> FMExport | None:
    try:
        data = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    names = set(ExportPlayer.__dataclass_fields__)
    players = []
    for raw in data.get("players", []):
        try:
            players.append(ExportPlayer(**{k: v for k, v in raw.items() if k in names}))
        except TypeError:
            continue
    return FMExport(players, float(data.get("time", 0) or 0), str(data.get("source", "")))
