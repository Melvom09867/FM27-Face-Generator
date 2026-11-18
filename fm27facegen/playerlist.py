"""Import einer Spielerliste aus Football Manager.

Unterstützt:
* FM "Bildschirm drucken" -> **Webseite (.html)**
* FM "Bildschirm drucken" -> **Textdatei (.txt)**  (Spalten mit | getrennt)
* eigene **CSV**-Dateien (Trennzeichen ; , Tab oder |), z. B. aus Excel

Erkannte Spalten (deutsch oder englisch, Groß-/Kleinschreibung egal):
Name · Nat/Nation/Nationalität · 2. Nat/Zweite Nationalität · Alter/Age · UID/Unique ID ·
Persönlichkeit/Personality
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from .data import norm_text, resolve_country
from .i18n import t
from .personality import resolve_personality


@dataclass
class Player:
    name: str
    nation_raw: str = ""
    country: str | None = None
    nation2_raw: str = ""
    country2: str | None = None
    age: int | None = None
    uid: str = ""
    image: Path | None = None  # erzeugtes Bild
    personality: str | None = None

    @property
    def country_display(self) -> str:
        return self.country or (f"? {self.nation_raw}" if self.nation_raw else "?")


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _norm(h: str) -> str:
    return norm_text(h)


# Spaltennamen in allen 8 Sprachen (in Vergleichsform: klein, ohne Akzente)
_NAME_COLS = {"name", "spieler", "player", "spielername", "playername", "nome", "nom", "nombre", "giocatore",
              "joueur", "jugador", "jogador", "名前", "選手名", "選手", "이름", "선수명", "선수"}
_UID_COLS = {"uid", "uniqueid", "id", "eindeutigeid", "spielerid", "playerid", "固有id", "고유id"}
_AGE_COLS = {"alter", "age", "eta", "edad", "idade", "年齢", "나이"}
_PERS_COLS = {"personlichkeit", "persoenlichkeit", "personality", "charakter", "personalita", "personnalite",
              "personalidad", "personalidade", "性格", "個性", "성격"}
_NAT_PARTS = ("nat", "naz", "nac", "国籍", "국적")
_COUNTRY_COLS = {"land", "country", "paese", "pays", "pais", "国", "국가"}
_SECOND_PARTS = ("2", "zweit", "second", "sec", "other", "weitere", "andere", "seconda", "seconde", "segunda",
                 "第2", "두번째", "제2")

# in dieselbe Vergleichsform bringen wie die Spaltenköpfe (wichtig u. a. für Koreanisch/Japanisch)
_NAME_COLS, _UID_COLS, _AGE_COLS, _PERS_COLS, _COUNTRY_COLS = (
    {norm_text(x) for x in group} for group in (_NAME_COLS, _UID_COLS, _AGE_COLS, _PERS_COLS, _COUNTRY_COLS))
_NAT_PARTS = tuple(norm_text(x) for x in _NAT_PARTS)
_SECOND_PARTS = tuple(norm_text(x) for x in _SECOND_PARTS)


def _column_role(header: str) -> str | None:
    h = _norm(header)
    if not h:
        return None
    if h in _NAME_COLS:
        return "name"
    if h in _UID_COLS:
        return "uid"
    if h in _AGE_COLS:
        return "age"
    if h in _PERS_COLS:
        return "pers"
    if any(part in h for part in _NAT_PARTS) or h in _COUNTRY_COLS:
        if any(x in h for x in _SECOND_PARTS):
            return "nat2"
        return "nat"
    return None


def _rows_from_text(text: str, suffix: str) -> list[list[str]]:
    if suffix in (".html", ".htm") or "<table" in text[:5000].lower():
        p = _TableParser()
        p.feed(text)
        return p.rows

    lines = [ln for ln in text.splitlines() if ln.strip()]
    pipe_lines = sum(1 for ln in lines[:20] if ln.count("|") >= 2)
    if pipe_lines >= 2:  # FM-Textexport
        rows = []
        for ln in lines:
            if ln.count("|") < 2:
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r"[-=+: ]*", c) for c in cells):
                continue  # Trennlinie
            rows.append(cells)
        return rows

    sample = "\n".join(lines[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    return [[c.strip() for c in row] for row in csv.reader(io.StringIO("\n".join(lines)), dialect)]


def _parse_age(text: str) -> int | None:
    m = re.search(r"\d{1,2}", text or "")
    if not m:
        return None
    age = int(m.group())
    return age if 10 <= age <= 50 else None


def parse_players(text: str, suffix: str = ".csv") -> tuple[list[Player], list[str]]:
    rows = _rows_from_text(text, suffix.lower())
    warnings: list[str] = []

    header_idx, roles = None, {}
    for i, row in enumerate(rows[:30]):
        r = {}
        for col, cell in enumerate(row):
            role = _column_role(cell)
            if role and role not in r:
                r[role] = col
        if "name" in r and ("nat" in r or "age" in r):
            header_idx, roles = i, r
            break
    if header_idx is None:
        return [], [t("pl.no_header")]
    if "nat" not in roles:
        warnings.append(t("pl.no_nat"))
    if "age" not in roles:
        warnings.append(t("pl.no_age"))

    def cell(row: list[str], role: str) -> str:
        col = roles.get(role)
        return row[col].strip() if col is not None and col < len(row) else ""

    players: list[Player] = []
    for row in rows[header_idx + 1:]:
        name = cell(row, "name")
        if not name or _column_role(name) == "name":
            continue  # leere oder wiederholte Kopfzeile
        nat, nat2 = cell(row, "nat"), cell(row, "nat2")
        # FM schreibt manchmal beide Nationen in eine Zelle, z. B. "GER / GHA"
        if nat and not nat2 and re.search(r"\s*[/,]\s*", nat):
            parts = [p.strip() for p in re.split(r"\s*[/,]\s*", nat) if p.strip()]
            if len(parts) == 2 and all(resolve_country(p) for p in parts):
                nat, nat2 = parts
        players.append(Player(
            name=name, nation_raw=nat, country=resolve_country(nat),
            nation2_raw=nat2, country2=resolve_country(nat2),
            age=_parse_age(cell(row, "age")), uid=re.sub(r"\D", "", cell(row, "uid")),
            personality=resolve_personality(cell(row, "pers")),
        ))

    unknown = sorted({p.nation_raw for p in players if p.nation_raw and not p.country})
    if unknown:
        warnings.append(t("pl.unknown", names=", ".join(unknown)))
    return players, warnings


def load_players(path: str | Path) -> tuple[list[Player], list[str]]:
    path = Path(path)
    data = path.read_bytes()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = data.decode("utf-16")
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1252", "replace")
    return parse_players(text, path.suffix)
