"""Stammdaten: Ethnien (mit typischen Haarfarben/-strukturen) und Länder (mit Ethnien-Verteilung).

Die Verteilungen sind bewusst grobe Näherungen dafür, wie Nachwuchsspieler eines
Landes typischerweise aussehen. Sie können über eine eigene ``laender.json``
überschrieben bzw. ergänzt werden (siehe README).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .i18n import t

# ---------------------------------------------------------------------------
# Ethnien
#   label   : Anzeige in der Oberfläche
#   prompt  : Beschreibung für das Bild-KI-Modell (englisch)
#   hair    : Gewichtung der natürlichen Haarfarben
#   texture : Gewichtung der Haarstruktur (straight / wavy / curly / coily)
#   freckles: Wahrscheinlichkeit für Sommersprossen (wenn Hautdetails aktiv)
# ---------------------------------------------------------------------------
ETHNICITIES: dict[str, dict] = {
    "EUR_N": {
        "label": "Nordeuropäisch / Skandinavisch",
        "prompt": "Scandinavian Northern European, fair skin",
        "hair": {"blonde": 35, "light brown": 30, "brown": 25, "red": 5, "dark brown": 5},
        "texture": {"straight": 70, "wavy": 30},
        "freckles": 0.25,
    },
    "EUR_W": {
        "label": "West-/Mitteleuropäisch",
        "prompt": "white Western European, light skin",
        "hair": {"brown": 35, "dark brown": 25, "light brown": 20, "blonde": 12, "black": 5, "red": 3},
        "texture": {"straight": 60, "wavy": 35, "curly": 5},
        "freckles": 0.15,
    },
    "EUR_S": {
        "label": "Südeuropäisch / Mediterran",
        "prompt": "Southern European Mediterranean, olive skin",
        "hair": {"dark brown": 45, "black": 35, "brown": 18, "light brown": 2},
        "texture": {"straight": 40, "wavy": 45, "curly": 15},
        "freckles": 0.04,
    },
    "EUR_E": {
        "label": "Osteuropäisch / Slawisch",
        "prompt": "Eastern European Slavic, light skin",
        "hair": {"light brown": 30, "brown": 30, "dark brown": 20, "blonde": 18, "red": 2},
        "texture": {"straight": 70, "wavy": 30},
        "freckles": 0.1,
    },
    "BALKAN": {
        "label": "Balkan / Südosteuropäisch",
        "prompt": "Balkan Southeastern European, light olive skin",
        "hair": {"dark brown": 45, "black": 30, "brown": 22, "light brown": 3},
        "texture": {"straight": 55, "wavy": 40, "curly": 5},
        "freckles": 0.03,
    },
    "CAUCASUS": {
        "label": "Kaukasisch (Georgien, Armenien, Aserbaidschan)",
        "prompt": "Caucasus region (Georgian/Armenian), light olive skin",
        "hair": {"black": 50, "dark brown": 45, "brown": 5},
        "texture": {"straight": 50, "wavy": 45, "curly": 5},
        "freckles": 0.02,
    },
    "MIDEAST": {
        "label": "Nahöstlich / Türkisch / Arabisch",
        "prompt": "Middle Eastern, light brown olive skin",
        "hair": {"black": 60, "dark brown": 38, "brown": 2},
        "texture": {"straight": 40, "wavy": 45, "curly": 15},
        "freckles": 0.01,
    },
    "AFR_N": {
        "label": "Nordafrikanisch / Maghreb",
        "prompt": "North African Maghrebi Arab, light brown skin",
        "hair": {"black": 70, "dark brown": 30},
        "texture": {"wavy": 35, "curly": 55, "straight": 10},
        "freckles": 0.0,
    },
    "AFR_W": {
        "label": "Westafrikanisch",
        "prompt": "Black West African, dark skin",
        "hair": {"black": 100},
        "texture": {"coily": 100},
        "freckles": 0.0,
    },
    "AFR_C": {
        "label": "Zentral-/Südafrikanisch",
        "prompt": "Black Central African, dark brown skin",
        "hair": {"black": 100},
        "texture": {"coily": 100},
        "freckles": 0.0,
    },
    "AFR_E": {
        "label": "Ostafrikanisch / Horn von Afrika",
        "prompt": "Black East African, dark brown skin, slender facial features",
        "hair": {"black": 100},
        "texture": {"coily": 85, "curly": 15},
        "freckles": 0.0,
    },
    "AFRO_DIA": {
        "label": "Afrokaribisch / Afroamerikanisch / Afrolateinamerikanisch",
        "prompt": "Black, of African diaspora descent, brown skin",
        "hair": {"black": 95, "dark brown": 5},
        "texture": {"coily": 85, "curly": 15},
        "freckles": 0.0,
    },
    "LAT": {
        "label": "Lateinamerikanisch (Mestizo)",
        "prompt": "Latin American mestizo, tan skin",
        "hair": {"black": 60, "dark brown": 38, "brown": 2},
        "texture": {"straight": 55, "wavy": 35, "curly": 10},
        "freckles": 0.01,
    },
    "INDIG": {
        "label": "Indigen (Anden / Mittelamerika)",
        "prompt": "Indigenous Andean South American, brown skin",
        "hair": {"black": 100},
        "texture": {"straight": 90, "wavy": 10},
        "freckles": 0.0,
    },
    "ASIA_E": {
        "label": "Ostasiatisch",
        "prompt": "East Asian, light skin",
        "hair": {"black": 85, "dark brown": 15},
        "texture": {"straight": 95, "wavy": 5},
        "freckles": 0.01,
    },
    "ASIA_SE": {
        "label": "Südostasiatisch",
        "prompt": "Southeast Asian, light brown skin",
        "hair": {"black": 90, "dark brown": 10},
        "texture": {"straight": 85, "wavy": 15},
        "freckles": 0.0,
    },
    "ASIA_S": {
        "label": "Südasiatisch (Indien, Pakistan, Bangladesch)",
        "prompt": "South Asian, brown skin",
        "hair": {"black": 85, "dark brown": 15},
        "texture": {"straight": 50, "wavy": 45, "curly": 5},
        "freckles": 0.0,
    },
    "ASIA_C": {
        "label": "Zentralasiatisch",
        "prompt": "Central Asian (Kazakh/Uzbek), light tan skin",
        "hair": {"black": 80, "dark brown": 20},
        "texture": {"straight": 90, "wavy": 10},
        "freckles": 0.01,
    },
    "PACIFIC": {
        "label": "Pazifisch / Polynesisch / Maori",
        "prompt": "Pacific Islander Polynesian, brown skin",
        "hair": {"black": 90, "dark brown": 10},
        "texture": {"wavy": 45, "curly": 45, "straight": 10},
        "freckles": 0.0,
    },
    "MIXED": {
        "label": "Gemischt (z. B. afrikanisch-europäisch)",
        "prompt": "mixed-race, of African and European descent, light brown skin",
        "hair": {"black": 60, "dark brown": 35, "brown": 5},
        "texture": {"curly": 70, "coily": 25, "wavy": 5},
        "freckles": 0.05,
    },
}

# ---------------------------------------------------------------------------
# Länder:  Anzeigename -> (englischer Name für den Prompt, {Ethnie: Gewicht})
# ---------------------------------------------------------------------------
_BALKAN = {"BALKAN": 95, "EUR_E": 3, "MIXED": 2}
_SLAV = {"EUR_E": 95, "MIXED": 3, "AFR_W": 2}
_NORDIC = {"EUR_N": 76, "AFR_E": 6, "MIDEAST": 6, "MIXED": 7, "AFR_W": 5}
_WEST_AFR = {"AFR_W": 100}
_CENT_AFR = {"AFR_C": 100}
_EAST_AFR = {"AFR_E": 100}
_MAGHREB = {"AFR_N": 100}
_ARAB = {"MIDEAST": 100}
_EAST_ASIA = {"ASIA_E": 100}
_SE_ASIA = {"ASIA_SE": 100}
_SOUTH_ASIA = {"ASIA_S": 100}
_CARIB = {"AFRO_DIA": 88, "MIXED": 12}

COUNTRIES: dict[str, tuple[str, dict[str, int]]] = {
    # --- Deutschsprachig ---
    "Deutschland": ("Germany", {"EUR_W": 55, "MIDEAST": 12, "BALKAN": 6, "EUR_E": 5, "AFR_W": 8, "AFR_N": 4, "MIXED": 8, "ASIA_S": 2}),
    "Österreich": ("Austria", {"EUR_W": 60, "BALKAN": 15, "MIDEAST": 10, "AFR_W": 6, "MIXED": 6, "EUR_E": 3}),
    "Schweiz": ("Switzerland", {"EUR_W": 50, "BALKAN": 18, "EUR_S": 8, "AFR_W": 8, "AFR_E": 4, "MIXED": 8, "MIDEAST": 4}),
    # --- Britische Inseln ---
    "England": ("England", {"EUR_W": 55, "AFR_W": 12, "AFRO_DIA": 10, "MIXED": 12, "ASIA_S": 6, "AFR_N": 2, "EUR_E": 3}),
    "Schottland": ("Scotland", {"EUR_W": 85, "MIXED": 5, "AFR_W": 4, "ASIA_S": 3, "EUR_E": 3}),
    "Wales": ("Wales", {"EUR_W": 85, "MIXED": 7, "AFR_W": 4, "ASIA_S": 4}),
    "Nordirland": ("Northern Ireland", {"EUR_W": 92, "MIXED": 4, "AFR_W": 4}),
    "Irland": ("Ireland", {"EUR_W": 85, "AFR_W": 6, "MIXED": 6, "EUR_E": 3}),
    # --- Westeuropa ---
    "Frankreich": ("France", {"EUR_W": 40, "AFR_W": 25, "AFR_C": 8, "AFR_N": 12, "AFRO_DIA": 5, "MIXED": 10}),
    "Belgien": ("Belgium", {"EUR_W": 50, "AFR_C": 15, "AFR_N": 15, "AFR_W": 7, "MIXED": 10, "MIDEAST": 3}),
    "Niederlande": ("Netherlands", {"EUR_W": 55, "AFRO_DIA": 12, "AFR_N": 12, "MIXED": 12, "ASIA_SE": 3, "MIDEAST": 6}),
    "Luxemburg": ("Luxembourg", {"EUR_W": 70, "EUR_S": 15, "AFR_W": 5, "BALKAN": 5, "MIXED": 5}),
    # --- Südeuropa ---
    "Spanien": ("Spain", {"EUR_S": 70, "AFR_N": 8, "AFR_W": 8, "LAT": 6, "MIXED": 8}),
    "Portugal": ("Portugal", {"EUR_S": 70, "AFR_W": 6, "AFR_C": 10, "MIXED": 12, "LAT": 2}),
    "Italien": ("Italy", {"EUR_S": 80, "AFR_W": 8, "AFR_N": 4, "MIXED": 5, "EUR_E": 3}),
    "Griechenland": ("Greece", {"EUR_S": 85, "BALKAN": 10, "AFR_W": 3, "MIXED": 2}),
    "Türkei": ("Turkey", {"MIDEAST": 88, "BALKAN": 6, "CAUCASUS": 6}),
    "Zypern": ("Cyprus", {"EUR_S": 80, "MIDEAST": 20}),
    "Malta": ("Malta", {"EUR_S": 95, "MIXED": 5}),
    # --- Balkan ---
    "Kroatien": ("Croatia", _BALKAN),
    "Serbien": ("Serbia", _BALKAN),
    "Bosnien und Herzegowina": ("Bosnia and Herzegovina", _BALKAN),
    "Slowenien": ("Slovenia", {"BALKAN": 70, "EUR_W": 25, "MIXED": 5}),
    "Albanien": ("Albania", _BALKAN),
    "Kosovo": ("Kosovo", _BALKAN),
    "Nordmazedonien": ("North Macedonia", _BALKAN),
    "Montenegro": ("Montenegro", _BALKAN),
    "Rumänien": ("Romania", {"EUR_E": 75, "BALKAN": 22, "MIXED": 3}),
    "Bulgarien": ("Bulgaria", {"BALKAN": 80, "EUR_E": 15, "MIDEAST": 5}),
    # --- Osteuropa ---
    "Polen": ("Poland", _SLAV),
    "Tschechien": ("Czech Republic", _SLAV),
    "Slowakei": ("Slovakia", _SLAV),
    "Ungarn": ("Hungary", {"EUR_E": 85, "EUR_W": 10, "MIXED": 5}),
    "Ukraine": ("Ukraine", _SLAV),
    "Russland": ("Russia", {"EUR_E": 88, "ASIA_C": 6, "CAUCASUS": 6}),
    "Belarus": ("Belarus", _SLAV),
    "Litauen": ("Lithuania", {"EUR_E": 70, "EUR_N": 30}),
    "Lettland": ("Latvia", {"EUR_E": 70, "EUR_N": 30}),
    "Estland": ("Estonia", {"EUR_N": 60, "EUR_E": 40}),
    "Georgien": ("Georgia (country)", {"CAUCASUS": 100}),
    "Armenien": ("Armenia", {"CAUCASUS": 100}),
    "Aserbaidschan": ("Azerbaijan", {"CAUCASUS": 85, "MIDEAST": 15}),
    "Kasachstan": ("Kazakhstan", {"ASIA_C": 70, "EUR_E": 30}),
    "Usbekistan": ("Uzbekistan", {"ASIA_C": 100}),
    # --- Skandinavien ---
    "Dänemark": ("Denmark", _NORDIC),
    "Schweden": ("Sweden", {"EUR_N": 65, "AFR_E": 10, "MIDEAST": 10, "MIXED": 8, "AFR_W": 4, "BALKAN": 3}),
    "Norwegen": ("Norway", _NORDIC),
    "Finnland": ("Finland", {"EUR_N": 90, "AFR_E": 5, "MIXED": 5}),
    "Island": ("Iceland", {"EUR_N": 97, "MIXED": 3}),
    # --- Nordamerika / Karibik ---
    "USA": ("United States", {"EUR_W": 40, "AFRO_DIA": 18, "LAT": 25, "MIXED": 10, "ASIA_E": 4, "ASIA_S": 3}),
    "Kanada": ("Canada", {"EUR_W": 50, "AFRO_DIA": 12, "ASIA_S": 10, "ASIA_E": 8, "MIXED": 12, "MIDEAST": 4, "AFR_W": 4}),
    "Mexiko": ("Mexico", {"LAT": 82, "EUR_S": 10, "INDIG": 8}),
    "Costa Rica": ("Costa Rica", {"LAT": 80, "EUR_S": 10, "AFRO_DIA": 10}),
    "Honduras": ("Honduras", {"LAT": 80, "AFRO_DIA": 15, "INDIG": 5}),
    "Panama": ("Panama", {"LAT": 55, "AFRO_DIA": 35, "MIXED": 10}),
    "Jamaika": ("Jamaica", _CARIB),
    "Haiti": ("Haiti", {"AFRO_DIA": 95, "MIXED": 5}),
    "Trinidad und Tobago": ("Trinidad and Tobago", {"AFRO_DIA": 60, "ASIA_S": 25, "MIXED": 15}),
    "Curaçao": ("Curacao", _CARIB),
    # --- Südamerika ---
    "Brasilien": ("Brazil", {"MIXED": 40, "EUR_S": 30, "AFRO_DIA": 30}),
    "Argentinien": ("Argentina", {"EUR_S": 75, "LAT": 20, "MIXED": 5}),
    "Uruguay": ("Uruguay", {"EUR_S": 80, "LAT": 10, "AFRO_DIA": 5, "MIXED": 5}),
    "Kolumbien": ("Colombia", {"LAT": 60, "AFRO_DIA": 25, "EUR_S": 10, "MIXED": 5}),
    "Chile": ("Chile", {"LAT": 75, "EUR_S": 20, "INDIG": 5}),
    "Peru": ("Peru", {"LAT": 55, "INDIG": 40, "EUR_S": 5}),
    "Bolivien": ("Bolivia", {"LAT": 50, "INDIG": 47, "EUR_S": 3}),
    "Ecuador": ("Ecuador", {"LAT": 55, "AFRO_DIA": 30, "INDIG": 15}),
    "Paraguay": ("Paraguay", {"LAT": 85, "EUR_S": 10, "INDIG": 5}),
    "Venezuela": ("Venezuela", {"LAT": 60, "AFRO_DIA": 20, "EUR_S": 15, "MIXED": 5}),
    # --- Afrika ---
    "Nigeria": ("Nigeria", _WEST_AFR),
    "Ghana": ("Ghana", _WEST_AFR),
    "Senegal": ("Senegal", _WEST_AFR),
    "Elfenbeinküste": ("Ivory Coast", _WEST_AFR),
    "Mali": ("Mali", _WEST_AFR),
    "Guinea": ("Guinea", _WEST_AFR),
    "Burkina Faso": ("Burkina Faso", _WEST_AFR),
    "Gambia": ("Gambia", _WEST_AFR),
    "Sierra Leone": ("Sierra Leone", _WEST_AFR),
    "Kap Verde": ("Cape Verde", {"MIXED": 60, "AFR_W": 40}),
    "Guinea-Bissau": ("Guinea-Bissau", _WEST_AFR),
    "Liberia": ("Liberia", _WEST_AFR),
    "Benin": ("Benin", _WEST_AFR),
    "Togo": ("Togo", _WEST_AFR),
    "Niger": ("Niger", _WEST_AFR),
    "Mauretanien": ("Mauritania", {"AFR_N": 50, "AFR_W": 50}),
    "Kongo": ("Republic of the Congo", _CENT_AFR),
    "Äquatorialguinea": ("Equatorial Guinea", _CENT_AFR),
    "Mosambik": ("Mozambique", _CENT_AFR),
    "Ruanda": ("Rwanda", _EAST_AFR),
    "Burundi": ("Burundi", _EAST_AFR),
    "Eritrea": ("Eritrea", _EAST_AFR),
    "Sudan": ("Sudan", {"AFR_E": 60, "AFR_N": 40}),
    "Kamerun": ("Cameroon", _CENT_AFR),
    "DR Kongo": ("DR Congo", _CENT_AFR),
    "Angola": ("Angola", _CENT_AFR),
    "Gabun": ("Gabon", _CENT_AFR),
    "Sambia": ("Zambia", _CENT_AFR),
    "Simbabwe": ("Zimbabwe", _CENT_AFR),
    "Südafrika": ("South Africa", {"AFR_C": 75, "MIXED": 10, "EUR_W": 15}),
    "Kenia": ("Kenya", _EAST_AFR),
    "Äthiopien": ("Ethiopia", _EAST_AFR),
    "Uganda": ("Uganda", _EAST_AFR),
    "Tansania": ("Tanzania", _EAST_AFR),
    "Somalia": ("Somalia", _EAST_AFR),
    "Marokko": ("Morocco", _MAGHREB),
    "Algerien": ("Algeria", _MAGHREB),
    "Tunesien": ("Tunisia", _MAGHREB),
    "Ägypten": ("Egypt", _MAGHREB),
    "Libyen": ("Libya", _MAGHREB),
    # --- Naher Osten ---
    "Saudi-Arabien": ("Saudi Arabia", _ARAB),
    "Katar": ("Qatar", _ARAB),
    "VAE": ("United Arab Emirates", _ARAB),
    "Irak": ("Iraq", _ARAB),
    "Iran": ("Iran", {"MIDEAST": 100}),
    "Syrien": ("Syria", _ARAB),
    "Jordanien": ("Jordan", _ARAB),
    "Libanon": ("Lebanon", _ARAB),
    "Israel": ("Israel", {"MIDEAST": 70, "EUR_E": 20, "AFR_E": 5, "MIXED": 5}),
    # --- Asien ---
    "Japan": ("Japan", _EAST_ASIA),
    "Südkorea": ("South Korea", _EAST_ASIA),
    "China": ("China", _EAST_ASIA),
    "Indien": ("India", _SOUTH_ASIA),
    "Pakistan": ("Pakistan", _SOUTH_ASIA),
    "Bangladesch": ("Bangladesh", _SOUTH_ASIA),
    "Indonesien": ("Indonesia", _SE_ASIA),
    "Vietnam": ("Vietnam", _SE_ASIA),
    "Thailand": ("Thailand", _SE_ASIA),
    "Malaysia": ("Malaysia", {"ASIA_SE": 75, "ASIA_E": 18, "ASIA_S": 7}),
    "Philippinen": ("Philippines", {"ASIA_SE": 90, "MIXED": 10}),
    # --- Ozeanien ---
    "Australien": ("Australia", {"EUR_W": 65, "ASIA_E": 8, "ASIA_S": 5, "MIXED": 10, "AFR_E": 4, "MIDEAST": 4, "PACIFIC": 4}),
    "Neuseeland": ("New Zealand", {"EUR_W": 60, "PACIFIC": 25, "ASIA_E": 8, "MIXED": 7}),
}


# FIFA-/FM-Kürzel (FM zeigt Nationalitäten oft als 3-Buchstaben-Code)
FIFA_CODES: dict[str, str] = {
    "GER": "Deutschland", "AUT": "Österreich", "SUI": "Schweiz", "ENG": "England", "SCO": "Schottland",
    "WAL": "Wales", "NIR": "Nordirland", "IRL": "Irland", "FRA": "Frankreich", "BEL": "Belgien",
    "NED": "Niederlande", "LUX": "Luxemburg", "ESP": "Spanien", "POR": "Portugal", "ITA": "Italien",
    "GRE": "Griechenland", "TUR": "Türkei", "CYP": "Zypern", "CRO": "Kroatien", "SRB": "Serbien",
    "BIH": "Bosnien und Herzegowina", "SVN": "Slowenien", "ALB": "Albanien", "KOS": "Kosovo",
    "MKD": "Nordmazedonien", "MNE": "Montenegro", "ROU": "Rumänien", "BUL": "Bulgarien", "POL": "Polen",
    "CZE": "Tschechien", "SVK": "Slowakei", "HUN": "Ungarn", "UKR": "Ukraine", "RUS": "Russland",
    "BLR": "Belarus", "LTU": "Litauen", "LVA": "Lettland", "EST": "Estland", "GEO": "Georgien",
    "ARM": "Armenien", "AZE": "Aserbaidschan", "KAZ": "Kasachstan", "UZB": "Usbekistan", "DEN": "Dänemark",
    "SWE": "Schweden", "NOR": "Norwegen", "FIN": "Finnland", "ISL": "Island", "USA": "USA", "CAN": "Kanada",
    "MEX": "Mexiko", "CRC": "Costa Rica", "HON": "Honduras", "PAN": "Panama", "JAM": "Jamaika",
    "HAI": "Haiti", "TRI": "Trinidad und Tobago", "CUW": "Curaçao", "BRA": "Brasilien", "ARG": "Argentinien",
    "URU": "Uruguay", "COL": "Kolumbien", "CHI": "Chile", "PER": "Peru", "BOL": "Bolivien", "ECU": "Ecuador",
    "PAR": "Paraguay", "VEN": "Venezuela", "NGA": "Nigeria", "GHA": "Ghana", "SEN": "Senegal",
    "CIV": "Elfenbeinküste", "MLI": "Mali", "GUI": "Guinea", "BFA": "Burkina Faso", "GAM": "Gambia",
    "SLE": "Sierra Leone", "GNB": "Guinea-Bissau", "LBR": "Liberia", "BEN": "Benin", "TOG": "Togo",
    "NIG": "Niger", "MTN": "Mauretanien", "CGO": "Kongo", "EQG": "Äquatorialguinea", "MOZ": "Mosambik",
    "RWA": "Ruanda", "BDI": "Burundi", "ERI": "Eritrea", "SDN": "Sudan", "MLT": "Malta", "CPV": "Kap Verde", "CMR": "Kamerun", "COD": "DR Kongo", "ANG": "Angola",
    "GAB": "Gabun", "ZAM": "Sambia", "ZIM": "Simbabwe", "RSA": "Südafrika", "KEN": "Kenia",
    "ETH": "Äthiopien", "UGA": "Uganda", "TAN": "Tansania", "SOM": "Somalia", "MAR": "Marokko",
    "ALG": "Algerien", "TUN": "Tunesien", "EGY": "Ägypten", "LBY": "Libyen", "KSA": "Saudi-Arabien",
    "QAT": "Katar", "UAE": "VAE", "IRQ": "Irak", "IRN": "Iran", "SYR": "Syrien", "JOR": "Jordanien",
    "LBN": "Libanon", "ISR": "Israel", "JPN": "Japan", "KOR": "Südkorea", "CHN": "China", "IND": "Indien",
    "PAK": "Pakistan", "BAN": "Bangladesch", "IDN": "Indonesien", "VIE": "Vietnam", "THA": "Thailand",
    "MAS": "Malaysia", "PHI": "Philippinen", "AUS": "Australien", "NZL": "Neuseeland",
}

# Weitere Schreibweisen (deutsch/englisch), wie sie in FM-Exporten vorkommen können
COUNTRY_ALIASES: dict[str, str] = {
    "Türkiye": "Türkei", "Turkiye": "Türkei", "Republic of Ireland": "Irland", "Rep. of Ireland": "Irland",
    "Holland": "Niederlande", "Czechia": "Tschechien", "Tschechische Republik": "Tschechien",
    "Bosnia": "Bosnien und Herzegowina", "Bosnien-Herzegowina": "Bosnien und Herzegowina",
    "FYR Macedonia": "Nordmazedonien", "Mazedonien": "Nordmazedonien",
    "Côte d'Ivoire": "Elfenbeinküste", "Cote d'Ivoire": "Elfenbeinküste",
    "Congo DR": "DR Kongo", "DR Congo": "DR Kongo", "Kongo DR": "DR Kongo", "Demokratische Republik Kongo": "DR Kongo",
    "Korea Republic": "Südkorea", "Korea": "Südkorea", "Republik Korea": "Südkorea",
    "USA": "USA", "United States of America": "USA", "Vereinigte Staaten": "USA",
    "Cabo Verde": "Kap Verde", "Vereinigte Arabische Emirate": "VAE", "UAE": "VAE",
    "Großbritannien": "England", "Weißrussland": "Belarus", "Saudi Arabia": "Saudi-Arabien",
    "Bosnien": "Bosnien und Herzegowina", "Kapverden": "Kap Verde", "Trinidad & Tobago": "Trinidad und Tobago",
}


def app_dir() -> Path:
    """Ordner der .exe (bzw. des Projekts beim Start aus dem Quellcode)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def load_user_overrides(path: Path | None = None) -> list[str]:
    """Lädt optionale ``laender.json`` neben der .exe und ergänzt/überschreibt Länder.

    Format::

        {
          "Färöer": {"en": "Faroe Islands", "mix": {"EUR_N": 100}},
          "Deutschland": {"en": "Germany", "mix": {"EUR_W": 70, "MIDEAST": 30}}
        }

    Gibt eine Liste von Warnungen zurück (unbekannte Ethnien, Formatfehler).
    """
    path = path or (app_dir() / "laender.json")
    warnings: list[str] = []
    if not path.exists():
        return warnings
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [t("data.read_error", e=exc)]
    for name, entry in raw.items():
        try:
            en = str(entry["en"])
            mix = {str(k): int(v) for k, v in entry["mix"].items()}
        except Exception:  # noqa: BLE001
            warnings.append(t("data.bad_entry", name=name))
            continue
        unknown = [k for k in mix if k not in ETHNICITIES]
        if unknown:
            warnings.append(t("data.unknown_eth", name=name, keys=unknown))
            mix = {k: v for k, v in mix.items() if k in ETHNICITIES}
        if mix and sum(mix.values()) > 0:
            COUNTRIES[name] = (en, mix)
    return warnings


def norm_text(text: str) -> str:
    """Vergleichsform: Kleinbuchstaben, ohne Akzente/Satzzeichen – funktioniert auch für 日本語/한국어."""
    import unicodedata
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(ch for ch in text if ch.isalnum() and not unicodedata.combining(ch)).casefold()


_norm = norm_text
_lookup: dict[str, str] = {}


def _country_lookup() -> dict[str, str]:
    """Alle bekannten Schreibweisen (deutsch, englisch, Übersetzungen, Aliasse) -> deutscher Schlüssel."""
    if not _lookup:
        from .country_names import NAMES
        for alias, name in COUNTRY_ALIASES.items():
            _lookup[norm_text(alias)] = name
        for name, row in NAMES.items():
            for label in row:
                _lookup.setdefault(norm_text(label), name)
        from .country_names_extra import NAMES as EXTRA
        for names in EXTRA.values():
            for name, label in names.items():
                _lookup.setdefault(norm_text(label), name)
        for name, (en, _mix) in COUNTRIES.items():
            _lookup[norm_text(en)] = name
            _lookup[norm_text(name)] = name
    return _lookup


def resolve_country(raw: str) -> str | None:
    """Ordnet 'GER', 'Germany', 'Deutschland', 'Côte d'Ivoire' … einem Land aus COUNTRIES zu."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw in COUNTRIES:
        return raw
    if raw.upper() in FIFA_CODES:
        return FIFA_CODES[raw.upper()]
    key = norm_text(raw)
    for name, (en, _mix) in COUNTRIES.items():  # zuerst exakt (auch eigene Länder aus laender.json)
        if key in (norm_text(name), norm_text(en)):
            return name
    found = _country_lookup().get(key)
    return found if found in COUNTRIES else None
