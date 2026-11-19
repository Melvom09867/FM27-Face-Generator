"""Grafische Oberfläche (tkinter), mehrsprachig.

Alle Auswahlwerte bleiben intern deutsche Schlüssel (siehe i18n.py); angezeigt werden Übersetzungen.
"""

from __future__ import annotations

import copy
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from PIL import Image, ImageTk

from . import APP_NAME, __version__
from . import settings as settings_mod
from .backends import BACKENDS, BackendError, BackendSettings, StableDiffusionWebUIBackend, check_sd_webui
from .data import COUNTRIES, ETHNICITIES, load_user_overrides
from .forge import ForgeManager, api_enabled, find_launcher
from .update import check_latest, should_notify
from .generator import (GeneratedFace, Generator, Job, RenameError, aging_jobs, load_face, parse_ages, rename_face,
                        trash_files)
from .i18n import LANGUAGES, country, ethnicity, get_language, opt, personality, set_language, t
from .personality import NONE as NO_PERS, PERSONALITIES, RANDOM as RANDOM_PERS, STRENGTHS, personality_names
from .playerlist import Player, load_players
from .prompts import (AUTO, BACKGROUNDS, CLOTHING, EXPRESSIONS, FACIAL_HAIR, GENDERS, HAIR_COLORS,
                      HAIR_STYLES_FEMALE, HAIR_STYLES_MALE, NO_SECOND, PARENT_MODES, SHIRT_COLORS, SHIRT_PATTERNS)
from tkinter import simpledialog

THUMB = 125
PREVIEW = 250
KEEP_RAW = 40  # so viele Original-KI-Bilder bleiben für Alterungs-Sets im Speicher
LIST_NAME_MODES = ["Name", "UID", "Name_UID"]
AUTO_ETH = "auto_country"


def _checker(size: int, cell: int = 10) -> Image.Image:
    img = Image.new("RGB", (size, size), (255, 255, 255))
    px = img.load()
    for y in range(size):
        for x in range(size):
            if ((x // cell) + (y // cell)) % 2:
                px[x, y] = (220, 220, 220)
    return img


def _on_checker(img: Image.Image, size: int) -> Image.Image:
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    if img.mode != "RGBA":
        return img
    bg = _checker(size, max(4, size // 25)).convert("RGBA")
    bg.alpha_composite(img)
    return bg.convert("RGB")


def open_path(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        pass


def reveal(path: Path) -> None:
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", "/select,", str(path)])
    else:
        open_path(path.parent)


def country_or_none(key: str) -> str:
    return "—" if key == NO_SECOND else country(key)


def pers_short(key: str | None) -> str:
    """Persönlichkeit kompakt (deutsch ohne englischen Zusatz)."""
    if not key:
        return ""
    label = personality(key)
    return label.split(" (")[0] if get_language() == "de" else label


# ====================================================================== Sprachdialog
class LanguageDialog(tk.Toplevel):
    """Kleines Fenster zur Sprachauswahl. Die Texte wechseln sofort in die gewählte Sprache."""

    def __init__(self, master, current: str, ask_again: bool):
        super().__init__(master)
        self.result: tuple[str, bool] | None = None
        self.resizable(False, False)
        self.codes = list(LANGUAGES)
        self.lang_var = tk.StringVar(self, LANGUAGES.get(current, LANGUAGES["de"]))
        self.dont_ask = tk.BooleanVar(self, not ask_again)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)
        self.title_lbl = ttk.Label(frm, font=("Segoe UI", 11, "bold"))
        self.title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.lang_lbl = ttk.Label(frm)
        self.lang_lbl.grid(row=1, column=0, sticky="w", padx=(0, 8))
        cb = ttk.Combobox(frm, textvariable=self.lang_var, values=list(LANGUAGES.values()), state="readonly", width=18)
        cb.grid(row=1, column=1, sticky="ew")
        cb.bind("<<ComboboxSelected>>", lambda e: self._retranslate())
        self.chk = ttk.Checkbutton(frm, variable=self.dont_ask)
        self.chk.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.ok_btn = ttk.Button(frm, command=self._ok)
        self.ok_btn.grid(row=3, column=1, sticky="e", pady=(14, 0))
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self._retranslate()
        cb.focus_set()
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 3
        self.geometry(f"+{x}+{y}")

    def _code(self) -> str:
        for code, name in LANGUAGES.items():
            if name == self.lang_var.get():
                return code
        return "de"

    def _retranslate(self) -> None:
        code = self._code()
        self.title(f"{APP_NAME} – {t('lang.title', lang=code)}")
        self.title_lbl.config(text=t("lang.title", lang=code))
        self.lang_lbl.config(text=t("lang.label", lang=code))
        self.chk.config(text=t("lang.dont_ask", lang=code))
        self.ok_btn.config(text=t("btn.ok", lang=code))

    def _ok(self) -> None:
        self.result = (self._code(), not self.dont_ask.get())
        self.destroy()

    @classmethod
    def ask(cls, master, current: str, ask_again: bool) -> tuple[str, bool] | None:
        dlg = cls(master, current, ask_again)
        dlg.grab_set()
        dlg.lift()
        dlg.focus_force()
        master.wait_window(dlg)
        return dlg.result


class UpdateDialog(tk.Toplevel):
    """Hinweis auf neue Version: 'Ja, bitte' öffnet die Download-Seite, 'Nein, will zocken' schließt."""

    def __init__(self, master, current: str, latest: str):
        super().__init__(master)
        self.title(t("upd.title"))
        self.resizable(False, False)
        self.transient(master)
        self.open_page = False
        self.skip = tk.BooleanVar(self, False)
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=t("upd.title"), font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(frm, text=t("upd.text", new=latest, cur=current), justify="left", wraplength=460).pack(anchor="w")
        ttk.Checkbutton(frm, text=t("upd.skip"), variable=self.skip).pack(anchor="w", pady=(12, 0))
        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text=t("upd.no"), command=self.destroy).pack(side="right")
        yes = ttk.Button(btns, text=t("upd.yes"), command=self._yes)
        yes.pack(side="right", padx=(0, 8))
        yes.focus_set()
        self.bind("<Return>", lambda e: self._yes())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _yes(self) -> None:
        self.open_page = True
        self.destroy()


# ====================================================================== Hauptfenster
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {__version__}")
        self.geometry("1240x820")
        self.minsize(1040, 680)

        self.cfg = settings_mod.load()
        set_language(self.cfg.language)
        self._style()
        if self.cfg.ask_language:
            self.withdraw()
            res = LanguageDialog.ask(self, self.cfg.language, True)
            if res:
                self.cfg.language, self.cfg.ask_language = res
                set_language(self.cfg.language)
                settings_mod.save(self.cfg)
            self.deiconify()

        self.warnings = load_user_overrides()
        self.q: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.generator: Generator | None = None
        self.faces: list[GeneratedFace] = []
        self.thumbs: list[ImageTk.PhotoImage] = []
        self.thumb_widgets: list[tk.Label] = []
        self.selected: int | None = None
        self.marked: set[int] = set()  # per Strg/Shift markierte Bilder
        self.preview_img: ImageTk.PhotoImage | None = None
        self.errors = 0
        self.done_ok = 0
        self.players: dict[str, Player] = {}  # Treeview-ID -> Spieler

        self.dnd = self._init_dnd()
        self.forge = ForgeManager(settings_mod.config_dir() / "forge.log")
        self._build()
        self._load_into_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Delete>", self._on_key_delete)
        if self.cfg.check_updates:
            threading.Thread(target=lambda: self.q.put(("update", 0, 0, None, check_latest(), "", None)),
                             daemon=True).start()
        if self.cfg.forge_autostart and self.cfg.forge_dir \
                and self.cfg.backend.backend == StableDiffusionWebUIBackend.name:
            self.after(800, lambda: self._forge_start(True))
        self.bind("<F2>", self._on_key_rename)
        self.after(100, self._poll)
        if self.warnings:
            self.after(500, lambda: messagebox.showwarning(APP_NAME, "\n".join(self.warnings)))

    # ================================================================== Drag and Drop (tkdnd)
    def _init_dnd(self) -> bool:
        """Lädt tkdnd, damit Bilder aus der Galerie in andere Programme gezogen werden können
        (z. B. per FaceDrop in FM oder in den Explorer). Ohne tkdnd läuft alles andere normal weiter."""
        try:
            from tkinterdnd2 import TkinterDnD
            TkinterDnD._require(self)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _make_drag_source(self, widget, index_getter: Callable[[], int | None]) -> None:
        if not self.dnd:
            return
        try:
            from tkinterdnd2 import COPY, DND_FILES
            widget.drag_source_register(1, DND_FILES)

            def init(_event):
                idx = index_getter()
                if idx is None or not (0 <= idx < len(self.faces)):
                    return "refuse_drop"
                faces = self._marked_faces() if idx in self.marked else [self.faces[idx]]
                files = tuple(str(f.path) for f in faces if f.path.exists())
                return (COPY, DND_FILES, files) if files else "refuse_drop"

            widget.dnd_bind("<<DragInitCmd>>", init)
        except Exception:  # noqa: BLE001
            pass

    # ================================================================== Aufbau
    def _style(self) -> None:
        st = ttk.Style(self)
        if "vista" in st.theme_names():
            st.theme_use("vista")
        elif "clam" in st.theme_names():
            st.theme_use("clam")
        st.configure("Big.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        st.configure("Hint.TLabel", foreground="#666")
        st.configure("Head.TLabel", font=("Segoe UI", 10, "bold"))

    def _row(self, parent, r: int, label: str, widget, hint: str | None = None) -> None:
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", padx=(8, 6), pady=4)
        widget.grid(row=r, column=1, sticky="ew", padx=(0, 8), pady=4)
        if hint:
            ttk.Label(parent, text=hint, style="Hint.TLabel", wraplength=340, justify="left").grid(
                row=r + 1, column=0, columnspan=2, sticky="w", padx=8)

    # ---- Auswahlfelder: intern Schlüssel, angezeigt Übersetzung
    def _ocombo(self, parent, var: str, keys, labeler: Callable[[str], str], width: int = 30,
                editable: bool = False) -> ttk.Combobox:
        cb = ttk.Combobox(parent, textvariable=self.v[var], state="normal" if editable else "readonly", width=width)
        self.ocb[var] = cb
        self._set_options(var, keys, labeler)
        if editable:
            self._bind_search_field(cb, var)
        else:
            self._bind_typeahead(cb, var)
        return cb

    # ---- Tastatur: tippen + Enter
    @staticmethod
    def _best_match(labels: list[str], text: str) -> str | None:
        """Bester Treffer: exakt > Anfang > irgendwo enthalten (ohne Groß-/Kleinschreibung)."""
        text = text.strip().casefold()
        if not text:
            return None
        for test in (lambda l: l.casefold() == text, lambda l: l.casefold().startswith(text),
                     lambda l: text in l.casefold()):
            hit = next((l for l in labels if test(l)), None)
            if hit:
                return hit
        return None

    def _bind_typeahead(self, cb: ttk.Combobox, var: str) -> None:
        """Auswahlfelder: Tippen springt zum passenden Eintrag, Enter übernimmt."""
        state = {"buf": "", "t": 0.0}

        def on_key(e):
            if e.keysym in ("Return", "KP_Enter"):
                cb.event_generate("<<ComboboxSelected>>")
                return "break"
            if e.keysym == "BackSpace":
                state["buf"] = state["buf"][:-1]
                return "break"
            ch = e.char
            if not ch or not ch.isprintable() or (e.state & 0x4):  # keine Steuerzeichen / Strg-Kombis
                return None
            now = time.monotonic()
            state["buf"] = (state["buf"] if now - state["t"] < 1.5 else "") + ch
            state["t"] = now
            hit = self._best_match(list(cb["values"]), state["buf"])
            if hit and hit != self.v[var].get():
                self.v[var].set(hit)
                cb.event_generate("<<ComboboxSelected>>")
            return "break"

        cb.bind("<KeyPress>", on_key)

    def _bind_search_field(self, cb: ttk.Combobox, var: str) -> None:
        """Länderfelder: Tippen filtert die Liste, Enter übernimmt den besten Treffer, ↓ öffnet die Liste."""
        cb.bind("<KeyRelease>", lambda e: self._filter_country(e, var))
        cb.bind("<Return>", lambda e: self._confirm_country(var))
        cb.bind("<KP_Enter>", lambda e: self._confirm_country(var))
        cb.bind("<<ComboboxSelected>>", lambda e: self._country_selected(var), add="+")
        cb.bind("<FocusOut>", lambda e: self._validate_country(var))

    def _set_options(self, var: str, keys, labeler: Callable[[str], str]) -> None:
        keys = list(keys)
        labels = [labeler(k) for k in keys]
        self.omap[var] = (dict(zip(keys, labels)), dict(zip(labels, keys)), keys)
        self.ocb[var]["values"] = labels

    def _oset(self, var: str, key: str) -> None:
        k2l, _, keys = self.omap[var]
        self.v[var].set(k2l.get(key, k2l[keys[0]] if keys else ""))

    def _oget(self, var: str, default: str = "") -> str:
        _, l2k, _ = self.omap[var]
        return l2k.get(self.v[var].get(), default)

    def _build(self) -> None:
        v = self.v = {}
        self.omap: dict[str, tuple[dict, dict, list]] = {}
        self.ocb: dict[str, ttk.Combobox] = {}
        for key in ("country", "second_country", "parent_mode", "ethnicity", "gender", "hair_color", "hair_style",
                    "facial_hair", "expression", "clothing", "shirt_color", "background", "extra_prompt",
                    "shirt_color2", "shirt_pattern", "club_preset",
                    "output_dir", "pattern", "backend", "pollinations_url", "pollinations_model",
                    "pollinations_token", "sd_url", "list_name_mode", "list_parent_mode", "aging_ages",
                    "list_country", "list_country2", "personality", "personality_strength", "list_personality"):
            v[key] = tk.StringVar(self)
        for key in ("age_min", "age_max", "count", "gen_size", "sd_steps", "tattoo_min_age"):
            v[key] = tk.IntVar(self)
        for key in ("zoom", "face_y", "delay", "sd_cfg"):
            v[key] = tk.DoubleVar(self)
        v["forge_dir"] = tk.StringVar(self)
        for key in ("skin_details", "sharpen", "subfolder_per_country", "overwrite", "forge_autostart", "check_updates"):
            v[key] = tk.BooleanVar(self)

        root = self.root_frame = ttk.Frame(self, padding=8)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root)
        left.grid(row=0, column=0, sticky="nsw")
        nb = self.left_nb = ttk.Notebook(left, width=410)
        nb.pack(fill="both", expand=True)
        self._build_tab_player(nb)
        self._build_tab_look(nb)
        self._build_tab_personality(nb)
        self._build_tab_output(nb)
        self._build_tab_ai(nb)

        right = ttk.Notebook(root)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.right_nb = right
        self._build_gallery(right)
        self._build_playerlist(right)

        self._build_bottom(root)

    def _countries(self) -> list[str]:
        return sorted(COUNTRIES, key=lambda k: country(k).casefold())

    # ------------------------------------------------------------------ Tab: Spieler
    def _build_tab_player(self, nb) -> None:
        v = self.v
        t_ = ttk.Frame(nb, padding=6)
        t_.columnconfigure(1, weight=1)
        nb.add(t_, text=t("tab.player"))
        self.country_cb = self._ocombo(t_, "country", self._countries(), country, editable=True)
        self.country_cb.bind("<<ComboboxSelected>>", lambda e: self._update_mix())
        self._row(t_, 0, t("lbl.country"), self.country_cb, t("hint.country"))

        self.second_cb = self._ocombo(t_, "second_country", [NO_SECOND] + self._countries(), country_or_none,
                                      editable=True)
        self.second_cb.bind("<<ComboboxSelected>>", lambda e: self._update_mix())
        self._row(t_, 2, t("lbl.second"), self.second_cb, t("hint.second"))
        self.parent_cb = self._ocombo(t_, "parent_mode", PARENT_MODES, lambda k: opt("parent_mode", k))
        self.parent_cb.bind("<<ComboboxSelected>>", lambda e: self._update_mix())
        self._row(t_, 4, t("lbl.parents"), self.parent_cb, t("hint.parents"))

        self.eth_cb = self._ocombo(t_, "ethnicity", [AUTO_ETH] + list(ETHNICITIES),
                                   lambda k: opt("_common", k) if k == AUTO_ETH else ethnicity(k))
        self.eth_cb.bind("<<ComboboxSelected>>", lambda e: self._update_mix())
        self._row(t_, 6, t("lbl.ethnicity"), self.eth_cb)
        self.mix_label = ttk.Label(t_, text="", style="Hint.TLabel", wraplength=370, justify="left")
        self.mix_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))

        gf = ttk.Frame(t_)
        for g in GENDERS:
            ttk.Radiobutton(gf, text=opt("gender", g), value=g, variable=v["gender"],
                            command=self._update_styles).pack(side="left", padx=(0, 12))
        self._row(t_, 8, t("lbl.gender"), gf)

        af = ttk.Frame(t_)
        ttk.Spinbox(af, from_=14, to=45, textvariable=v["age_min"], width=5).pack(side="left")
        ttk.Label(af, text=t("word.to")).pack(side="left")
        ttk.Spinbox(af, from_=14, to=45, textvariable=v["age_max"], width=5).pack(side="left")
        ttk.Label(af, text=t("word.years")).pack(side="left")
        self._row(t_, 9, t("lbl.age"), af, t("hint.age"))

    # ------------------------------------------------------------------ Tab: Aussehen
    def _build_tab_look(self, nb) -> None:
        v = self.v
        t_ = ttk.Frame(nb, padding=6)
        t_.columnconfigure(1, weight=1)
        nb.add(t_, text=t("tab.look"))
        self._row(t_, 0, t("lbl.hair_color"), self._ocombo(t_, "hair_color", HAIR_COLORS, lambda k: opt("hair_color", k)))
        self.style_cb = self._ocombo(t_, "hair_style", HAIR_STYLES_MALE, lambda k: opt("hair_style", k))
        self._row(t_, 1, t("lbl.hair_style"), self.style_cb)
        self.beard_cb = self._ocombo(t_, "facial_hair", FACIAL_HAIR, lambda k: opt("facial_hair", k))
        self._row(t_, 2, t("lbl.beard"), self.beard_cb, t("hint.beard"))
        self._row(t_, 4, t("lbl.expression"), self._ocombo(t_, "expression", EXPRESSIONS, lambda k: opt("expression", k)))
        self._row(t_, 5, t("lbl.clothing"), self._ocombo(t_, "clothing", CLOTHING, lambda k: opt("clothing", k)))
        self._row(t_, 6, t("lbl.shirt"), self._ocombo(t_, "shirt_color", SHIRT_COLORS, lambda k: opt("shirt_color", k)))
        pat_cb = self._ocombo(t_, "shirt_pattern", SHIRT_PATTERNS, lambda k: opt("shirt_pattern", k))
        pat_cb.bind("<<ComboboxSelected>>", lambda e: self._update_pattern(), add="+")
        self._row(t_, 7, t("lbl.shirt_pattern"), pat_cb)
        self.color2_cb = self._ocombo(t_, "shirt_color2", SHIRT_COLORS, lambda k: opt("shirt_color", k))
        self._row(t_, 8, t("lbl.shirt2"), self.color2_cb)
        cf = ttk.Frame(t_)
        cf.columnconfigure(0, weight=1)
        self.club_cb = ttk.Combobox(cf, textvariable=v["club_preset"], state="readonly", width=28)
        self.club_cb.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.club_cb.bind("<<ComboboxSelected>>", lambda e: self._apply_club_preset())
        ttk.Button(cf, text=t("btn.save_preset"), command=self._save_club_preset).grid(row=1, column=0, sticky="ew",
                                                                                       pady=(3, 0))
        ttk.Button(cf, text=t("btn.delete"), command=self._delete_club_preset).grid(row=1, column=1, sticky="ew",
                                                                                 padx=(4, 0), pady=(3, 0))
        cf.columnconfigure(1, weight=1)
        self._row(t_, 9, t("lbl.club"), cf, t("hint.club"))
        self._row(t_, 11, t("lbl.background"), self._ocombo(t_, "background", BACKGROUNDS, lambda k: opt("background", k)),
                  t("hint.background"))
        ttk.Checkbutton(t_, text=t("chk.skin"), variable=v["skin_details"]).grid(
            row=13, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        self._row(t_, 14, t("lbl.extra"), ttk.Entry(t_, textvariable=v["extra_prompt"]), t("hint.extra"))

    # ---- Trikot: Muster und Vereins-Vorlagen
    def _update_pattern(self) -> None:
        plain = self._oget("shirt_pattern", "Einfarbig") == "Einfarbig"
        self.color2_cb.configure(state="disabled" if plain else "readonly")

    def _refresh_club_presets(self, select: str = "") -> None:
        names = sorted(self.cfg.club_presets, key=str.casefold)
        self.club_cb["values"] = names
        self.v["club_preset"].set(select if select in names else "")

    def _apply_club_preset(self) -> None:
        preset = self.cfg.club_presets.get(self.v["club_preset"].get())
        if not preset:
            return
        for var, valid in (("clothing", CLOTHING), ("shirt_color", SHIRT_COLORS), ("shirt_color2", SHIRT_COLORS),
                           ("shirt_pattern", SHIRT_PATTERNS)):
            if preset.get(var) in valid:
                self._oset(var, preset[var])
        self._update_pattern()

    def _save_club_preset(self) -> None:
        name = simpledialog.askstring(APP_NAME, t("dlg.preset_name"), parent=self,
                                      initialvalue=self.v["club_preset"].get())
        name = (name or "").strip()
        if not name:
            return
        self.cfg.club_presets[name] = {var: self._oget(var) for var in
                                       ("clothing", "shirt_color", "shirt_color2", "shirt_pattern")}
        settings_mod.save(self.cfg)
        self._refresh_club_presets(name)

    def _delete_club_preset(self) -> None:
        name = self.v["club_preset"].get()
        if name in self.cfg.club_presets:
            del self.cfg.club_presets[name]
            settings_mod.save(self.cfg)
        self._refresh_club_presets()

    # ------------------------------------------------------------------ Tab: Persönlichkeit
    def _build_tab_personality(self, nb) -> None:
        v = self.v
        t_ = ttk.Frame(nb, padding=6)
        t_.columnconfigure(1, weight=1)
        nb.add(t_, text=t("tab.personality"))
        ttk.Label(t_, text=t("pers.intro"), style="Hint.TLabel", wraplength=370, justify="left").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))
        self.pers_cb = self._ocombo(t_, "personality", personality_names(), personality)
        self.pers_cb.bind("<<ComboboxSelected>>", lambda e: self._update_pers_hint())
        self._row(t_, 1, t("lbl.personality"), self.pers_cb)
        self.pers_hint = ttk.Label(t_, text="", style="Hint.TLabel", wraplength=370, justify="left")
        self.pers_hint.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))
        self._row(t_, 3, t("lbl.strength"),
                  self._ocombo(t_, "personality_strength", STRENGTHS, lambda k: opt("strength", k), width=12),
                  t("hint.strength"))
        self._row(t_, 5, t("lbl.tattoo"), ttk.Spinbox(t_, from_=14, to=40, textvariable=v["tattoo_min_age"], width=5),
                  t("hint.tattoo"))
        ttk.Label(t_, text=t("pers.list_note"), style="Hint.TLabel", wraplength=370, justify="left").grid(
            row=7, column=0, columnspan=2, sticky="w", padx=8, pady=(12, 0))

    # ------------------------------------------------------------------ Tab: Ausgabe
    def _build_tab_output(self, nb) -> None:
        v = self.v
        t_ = ttk.Frame(nb, padding=6)
        t_.columnconfigure(1, weight=1)
        nb.add(t_, text=t("tab.output"))
        ttk.Label(t_, text=t("out.note"), style="Hint.TLabel").grid(row=0, column=0, columnspan=2, sticky="w",
                                                                   padx=8, pady=(0, 6))
        ttk.Checkbutton(t_, text=t("chk.subfolder"), variable=v["subfolder_per_country"]).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Checkbutton(t_, text=t("chk.overwrite"), variable=v["overwrite"]).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))
        self._row(t_, 3, t("lbl.pattern"), ttk.Entry(t_, textvariable=v["pattern"]), t("hint.pattern"))
        self._row(t_, 5, t("lbl.zoom"), ttk.Scale(t_, from_=1.2, to=3.0, variable=v["zoom"]), t("hint.zoom"))
        self._row(t_, 7, t("lbl.face_y"), ttk.Scale(t_, from_=0.35, to=0.7, variable=v["face_y"]), t("hint.face_y"))
        ttk.Checkbutton(t_, text=t("chk.sharpen"), variable=v["sharpen"]).grid(
            row=9, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        ttk.Label(t_, text=t("out.always"), style="Head.TLabel").grid(row=10, column=0, columnspan=2, sticky="w",
                                                                     padx=8, pady=8)
        ttk.Checkbutton(t_, text=t("chk.updates"), variable=v["check_updates"]).grid(
            row=11, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 0))

    # ------------------------------------------------------------------ Tab: KI
    def _build_tab_ai(self, nb) -> None:
        v = self.v
        t_ = ttk.Frame(nb, padding=6)
        t_.columnconfigure(1, weight=1)
        nb.add(t_, text=t("tab.ai"))
        backend_cb = self._ocombo(t_, "backend", BACKENDS, lambda k: opt("backend", k), width=34)
        backend_cb.bind("<<ComboboxSelected>>", lambda e: self._on_backend_changed())
        self._row(t_, 0, t("lbl.backend"), backend_cb, t("hint.backend"))
        ttk.Label(t_, text="Pollinations", style="Head.TLabel").grid(row=2, column=0, sticky="w", padx=8, pady=(10, 0))
        self._row(t_, 3, t("lbl.address"), ttk.Entry(t_, textvariable=v["pollinations_url"]))
        self._row(t_, 4, t("lbl.model"), ttk.Combobox(t_, textvariable=v["pollinations_model"],
                                                      values=["flux", "turbo", "kontext", "gptimage"]))
        self._row(t_, 5, t("lbl.apikey"), ttk.Entry(t_, textvariable=v["pollinations_token"], show="•"),
                  t("hint.apikey"))
        ttk.Label(t_, text=t("head.local"), style="Head.TLabel").grid(row=7, column=0, columnspan=2, sticky="w",
                                                                     padx=8, pady=(10, 0))
        sdf = ttk.Frame(t_)
        sdf.columnconfigure(0, weight=1)
        ttk.Entry(sdf, textvariable=v["sd_url"]).grid(row=0, column=0, sticky="ew")
        self.sd_test_btn = ttk.Button(sdf, text=t("btn.test"), command=self._test_sd)
        self.sd_test_btn.grid(row=0, column=1, padx=(4, 0))
        self._row(t_, 8, t("lbl.address"), sdf)
        sp = ttk.Frame(t_)
        ttk.Spinbox(sp, from_=4, to=80, textvariable=v["sd_steps"], width=5).pack(side="left")
        ttk.Label(sp, text="   CFG").pack(side="left")
        ttk.Spinbox(sp, from_=1, to=15, increment=0.5, textvariable=v["sd_cfg"], width=5).pack(side="left", padx=4)
        self._row(t_, 9, t("lbl.steps"), sp)
        ff = ttk.Frame(t_)
        ff.columnconfigure(0, weight=1)
        ttk.Entry(ff, textvariable=v["forge_dir"]).grid(row=0, column=0, sticky="ew")
        ttk.Button(ff, text="…", width=3, command=self._choose_forge_dir).grid(row=0, column=1, padx=(4, 0))
        ttk.Button(ff, text=t("btn.forge_start"), command=lambda: self._forge_start(False)).grid(row=0, column=2,
                                                                                               padx=(4, 0))
        self._row(t_, 10, t("lbl.forge_dir"), ff)
        ttk.Checkbutton(t_, text=t("chk.forge_auto"), variable=v["forge_autostart"]).grid(
            row=11, column=0, columnspan=2, sticky="w", padx=8, pady=(2, 0))
        self.forge_status = ttk.Label(t_, text=self._forge_status_text(), style="Hint.TLabel", wraplength=370,
                                      justify="left")
        self.forge_status.grid(row=12, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Label(t_, text=t("head.general"), style="Head.TLabel").grid(row=13, column=0, sticky="w", padx=8,
                                                                       pady=(10, 0))
        self._row(t_, 14, t("lbl.gen_size"), ttk.Combobox(t_, textvariable=v["gen_size"], values=[512, 768, 1024],
                                                          width=6), t("hint.gen_size"))
        self._row(t_, 16, t("lbl.delay"), ttk.Spinbox(t_, from_=0, to=60, textvariable=v["delay"], width=6))


    # ---- Update-Hinweis
    def _show_update(self, info: dict) -> None:
        dlg = UpdateDialog(self, __version__, info["version"])
        dlg.grab_set()
        self.wait_window(dlg)
        if dlg.skip.get():
            self.cfg.skip_version = info["version"]
            settings_mod.save(self.cfg)
        if dlg.open_page:
            import webbrowser
            webbrowser.open(info["url"])

    # ---- Forge automatisch starten/beenden
    def _forge_status_text(self) -> str:
        state = getattr(self, "forge", None) and self.forge.state
        return {"starting": t("forge.starting_short"), "ready": t("forge.ready"), "external": t("forge.already"),
                "failed": t("forge.failed_short")}.get(state or "", t("hint.forge"))

    def _choose_forge_dir(self) -> None:
        d = filedialog.askdirectory(title=t("dlg.forge_dir"), initialdir=self.v["forge_dir"].get() or "C:\\")
        if d:
            self.v["forge_dir"].set(str(Path(d)))
            if not find_launcher(d):
                messagebox.showwarning(APP_NAME, t("forge.not_found", folder=d))

    def _forge_msg(self, text: str) -> None:
        self.q.put(("forge", 0, 0, None, text, "", None))

    def _forge_start(self, auto: bool) -> None:
        """Startet Forge im Hintergrund (auto = beim Programmstart, ohne Fehlermeldungs-Fenster bei 'läuft schon')."""
        self._read_from_ui()
        settings_mod.save(self.cfg)
        folder, url = self.cfg.forge_dir, self.cfg.backend.sd_url
        if self.forge.state == "starting":
            return
        if not find_launcher(folder):
            if not auto or folder:
                messagebox.showwarning(APP_NAME, t("forge.not_found", folder=folder or "—"))
            return
        if api_enabled(folder) is False:
            messagebox.showwarning(APP_NAME, t("be.no_api"))

        def work():
            from .forge import api_state
            if api_state(url) == "ready":
                self.forge.state = "external"
                self._forge_msg(t("forge.already"))
                return
            try:
                self.forge.start(folder)
            except Exception as exc:  # noqa: BLE001
                self.forge.state = "failed"
                self._forge_msg(t("forge.failed", log=exc))
                return
            self._forge_msg(t("forge.starting", s=0))
            res = self.forge.wait_ready(url, on_tick=lambda s: self._forge_msg(t("forge.starting", s=s)))
            if res == "ready":
                self._forge_msg(t("forge.ready"))
            elif res == "no_api":
                self._forge_msg(t("be.no_api").split("\n")[0])
            elif res != "cancelled":
                self._forge_msg(t("forge.failed", log=self.forge.log_path))

        threading.Thread(target=work, daemon=True).start()

    def _on_backend_changed(self) -> None:
        """Beim Wechsel auf lokales SD passende Werte für SDXL-Modelle (z. B. RealVisXL) setzen."""
        if self._oget("backend") != StableDiffusionWebUIBackend.name:
            return
        try:
            if int(self.v["gen_size"].get()) < 1024:
                self.v["gen_size"].set(1024)
        except (tk.TclError, ValueError):
            self.v["gen_size"].set(1024)
        self.v["delay"].set(0)
        self.status.config(text=t("status.local_set"))

    def _test_sd(self) -> None:
        self._read_from_ui()
        settings = BackendSettings(**self.cfg.backend.__dict__)
        self.sd_test_btn.configure(state="disabled", text=t("btn.testing"))

        def work():
            try:
                info = check_sd_webui(settings)
                model = info["model"] or t("sd.none")
                msg = t("sd.ok", model=model)
                if info["models"]:
                    msg += "\n\n" + t("sd.models") + "\n• " + "\n• ".join(info["models"][:10])
                if info.get("fast"):
                    msg += "\n\n" + t("sd.fast")
                if "xl" not in model.lower():
                    msg += "\n\n" + t("sd.not_xl")
                self.after(0, lambda: messagebox.showinfo(APP_NAME, msg))
            except BackendError as exc:
                err = str(exc)
                self.after(0, lambda: messagebox.showerror(APP_NAME, err))
            finally:
                self.after(0, lambda: self.sd_test_btn.configure(state="normal", text=t("btn.test")))

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------ Galerie
    def _build_gallery(self, nb) -> None:
        tab = self.gallery_tab = ttk.Frame(nb, padding=6)
        nb.add(tab, text=t("tab.gallery"))
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        head = ttk.Frame(tab)
        head.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(head, text=t("gal.hint"), style="Hint.TLabel", wraplength=390, justify="left").pack(side="left")
        ttk.Button(head, text=t("btn.load_images"), command=self._load_images).pack(side="right")
        gal = ttk.Frame(tab, relief="sunken", borderwidth=1)
        gal.grid(row=1, column=0, sticky="nsew")
        gal.rowconfigure(0, weight=1)
        gal.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(gal, background="#f4f4f4", highlightthickness=0)
        sb = ttk.Scrollbar(gal, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.grid_frame = tk.Frame(self.canvas, background="#f4f4f4")
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self._relayout())
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all(
            "<MouseWheel>", lambda ev: self.canvas.yview_scroll(int(-ev.delta / 120), "units")))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        side = ttk.Frame(tab)
        side.grid(row=1, column=1, sticky="n", padx=(10, 0))
        ttk.Label(side, text=t("gal.selection"), style="Head.TLabel").pack(anchor="w")
        # leeres Platzhalterbild: ohne Bild würde Tk width/height in Zeichen statt Pixeln messen
        self.blank_img = ImageTk.PhotoImage(Image.new("RGB", (PREVIEW, PREVIEW), (221, 221, 221)))
        self.preview = tk.Label(side, image=self.blank_img, width=PREVIEW, height=PREVIEW, background="#ddd",
                                relief="sunken", cursor="hand2")
        self._make_drag_source(self.preview, lambda: self.selected)
        self.preview.pack(pady=4)
        self.sel_info = ttk.Label(side, text="", wraplength=PREVIEW, justify="left", style="Hint.TLabel")
        self.sel_info.pack(anchor="w", fill="x")
        btns = ttk.Frame(side)
        btns.pack(fill="x")
        btns.columnconfigure((0, 1), weight=1)
        for n, (text, cmd) in enumerate(((t("btn.reroll"), self._reroll), (t("btn.rename"), self._rename),
                                         (t("btn.reveal"), self._reveal), (t("btn.copy_prompt"), self._copy_prompt),
                                         (t("btn.delete"), self._delete))):
            ttk.Button(btns, text=text, command=cmd).grid(row=n // 2, column=n % 2, sticky="ew", padx=1, pady=1)

        aging = ttk.Frame(tab)
        aging.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(aging, text=t("aging.title"), style="Head.TLabel").pack(side="left")
        ttk.Label(aging, text=t("aging.with")).pack(side="left", padx=(6, 4))
        ttk.Entry(aging, textvariable=self.v["aging_ages"], width=22).pack(side="left")
        ttk.Label(aging, text=t("aging.years")).pack(side="left", padx=(4, 8))
        ttk.Button(aging, text=t("btn.create"), command=self._aging).pack(side="left")

    # ------------------------------------------------------------------ Spielerliste
    def _build_playerlist(self, nb) -> None:
        v = self.v
        tab = ttk.Frame(nb, padding=6)
        nb.add(tab, text=t("tab.list"))
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        bar = ttk.Frame(tab)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(bar, text=t("btn.load_list"), command=self._load_list).pack(side="left")
        ttk.Button(bar, text=t("btn.export_help"),
                   command=lambda: messagebox.showinfo(APP_NAME, t("help.export"))).pack(side="left", padx=6)
        ttk.Label(bar, text=t("lbl.filename")).pack(side="left", padx=(12, 4))
        self._ocombo(bar, "list_name_mode", LIST_NAME_MODES, lambda k: opt("list_name", k), width=10).pack(side="left")
        ttk.Label(bar, text=t("lbl.second_nat")).pack(side="left", padx=(12, 4))
        self._ocombo(bar, "list_parent_mode", PARENT_MODES, lambda k: opt("parent_mode", k), width=26).pack(side="left")

        tf = ttk.Frame(tab)
        tf.grid(row=1, column=0, sticky="nsew")
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)
        cols = {"name": (t("col.name"), 170), "land": (t("col.country"), 110), "land2": (t("col.country2"), 90),
                "alter": (t("col.age"), 45), "pers": (t("lbl.personality"), 120), "uid": ("UID", 85),
                "status": (t("col.status"), 170)}
        self.tree = ttk.Treeview(tf, columns=list(cols), show="headings", selectmode="extended")
        for key, (title, width) in cols.items():
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w", stretch=key in ("name", "status"))
        ysb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        self.tree.tag_configure("unknown", foreground="#b05a00")
        self.tree.tag_configure("ok", foreground="#1a7f37")
        self.tree.tag_configure("err", foreground="#c62828")
        self.tree.bind("<Double-1>", self._open_player_image)

        edit = ttk.Frame(tab)
        edit.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Label(edit, text=t("list.change"), style="Head.TLabel").grid(row=0, column=0, columnspan=6, sticky="w")
        widgets = (
            (t("col.country"), self._ocombo(edit, "list_country", self._countries(), country, width=18,
                                            editable=True), "country"),
            (t("col.country2"), self._ocombo(edit, "list_country2", [NO_SECOND] + self._countries(), country_or_none,
                                             width=18, editable=True), "country2"),
            (t("lbl.personality"), self._ocombo(edit, "list_personality", [NO_PERS] + list(PERSONALITIES),
                                                personality, width=18), "personality"),
        )
        for col, (label, widget, which) in enumerate(widgets):
            ttk.Label(edit, text=label).grid(row=1 + col // 2, column=(col % 2) * 3, sticky="w", padx=(0, 4), pady=2)
            widget.grid(row=1 + col // 2, column=(col % 2) * 3 + 1, sticky="w", pady=2)
            ttk.Button(edit, text=t("btn.set"), width=9, command=lambda w=which: self._set_list_value(w)).grid(
                row=1 + col // 2, column=(col % 2) * 3 + 2, sticky="w", padx=(4, 14), pady=2)
        ttk.Button(edit, text=t("btn.remove"), command=self._remove_players).grid(row=2, column=3, columnspan=3,
                                                                                  sticky="w", pady=2)

        run = ttk.Frame(tab)
        run.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.list_info = ttk.Label(run, text=t("list.none"), style="Hint.TLabel")
        self.list_info.pack(side="left")
        ttk.Button(run, text=t("btn.gen_all"), command=lambda: self._generate_list("all")).pack(side="right")
        ttk.Button(run, text=t("btn.gen_missing"), command=lambda: self._generate_list("missing")).pack(side="right",
                                                                                                        padx=6)
        ttk.Button(run, text=t("btn.gen_selected"), command=lambda: self._generate_list("selected")).pack(side="right")

    # ------------------------------------------------------------------ untere Leiste
    def _build_bottom(self, root) -> None:
        v = self.v
        out = ttk.Frame(root)
        out.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        out.columnconfigure(1, weight=1)
        ttk.Label(out, text=t("lbl.save_in"), style="Head.TLabel").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(out, textvariable=v["output_dir"]).grid(row=0, column=1, sticky="ew")
        ttk.Button(out, text=t("btn.choose_dir"), command=self._choose_dir).grid(row=0, column=2, padx=(6, 0))
        ttk.Button(out, text=t("btn.find_fm"), command=self._find_fm).grid(row=0, column=3, padx=(6, 0))
        ttk.Button(out, text=t("btn.open"), command=self._open_out).grid(row=0, column=4, padx=(6, 0))
        self.lang_btn = ttk.Button(out, text=f"{t('btn.language')}: {LANGUAGES[get_language()]}",
                                   command=self._change_language)
        self.lang_btn.grid(row=0, column=5, padx=(12, 0))

        bottom = ttk.Frame(root)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        bottom.columnconfigure(4, weight=1)
        ttk.Label(bottom, text=t("lbl.count")).grid(row=0, column=0)
        ttk.Spinbox(bottom, from_=1, to=500, textvariable=v["count"], width=6).grid(row=0, column=1, padx=(4, 12))
        self.go_btn = ttk.Button(bottom, text=t("btn.generate"), style="Big.TButton", command=self._start)
        self.go_btn.grid(row=0, column=2)
        self.stop_btn = ttk.Button(bottom, text=t("btn.cancel"), command=self._stop, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=8)
        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.grid(row=0, column=4, sticky="ew", padx=8)
        self.status = ttk.Label(bottom, text=t("status.ready"), width=62)
        self.status.grid(row=0, column=5, sticky="e")

    # ================================================================== Sprache
    def _change_language(self) -> None:
        if self._busy():
            messagebox.showinfo(APP_NAME, t("msg.lang_busy"))
            return
        res = LanguageDialog.ask(self, get_language(), self.cfg.ask_language)
        if not res:
            return
        code, ask_again = res
        self.cfg.ask_language = ask_again
        if code != get_language():
            self._apply_language(code)
        else:
            settings_mod.save(self.cfg)

    def _apply_language(self, code: str) -> None:
        """Oberfläche in neuer Sprache neu aufbauen – Einstellungen, Galerie und Spielerliste bleiben erhalten."""
        self._read_from_ui()
        self.cfg.language = code
        set_language(code)
        settings_mod.save(self.cfg)
        players = list(self.players.values())
        selected = self.selected
        right_tab = self.right_nb.index("current")
        left_tab = self.left_nb.index("current")
        self.root_frame.destroy()
        self.thumb_widgets, self.thumbs, self.players = [], [], {}
        self._build()
        self._load_into_ui()
        self._rebuild_gallery()
        if selected is not None:
            self._select(selected)
        for p in players:
            iid = self.tree.insert("", "end")
            self.players[iid] = p
            self._refresh_row(iid)
            if p.image:
                self.tree.set(iid, "status", "✓ " + p.image.name)
                self.tree.item(iid, tags=("ok",))
        self._update_list_info()
        self.right_nb.select(right_tab)
        self.left_nb.select(left_tab)

    # ================================================================== Daten <-> UI
    def _load_into_ui(self) -> None:
        c, v = self.cfg, self.v
        f, b, p = c.face, c.backend, c.process
        self._oset("country", f.country if f.country in COUNTRIES else "Deutschland")
        self._oset("second_country", f.second_country if f.second_country in COUNTRIES else NO_SECOND)
        self._oset("parent_mode", f.parent_mode if f.parent_mode in PARENT_MODES else "Zufällig")
        self._oset("ethnicity", f.ethnicity if f.ethnicity in ETHNICITIES else AUTO_ETH)
        v["gender"].set(f.gender if f.gender in GENDERS else "Männlich")
        v["age_min"].set(f.age_min)
        v["age_max"].set(f.age_max)
        self._oset("hair_color", f.hair_color if f.hair_color in HAIR_COLORS else AUTO)
        self._oset("facial_hair", f.facial_hair if f.facial_hair in FACIAL_HAIR else AUTO)
        self._oset("expression", f.expression if f.expression in EXPRESSIONS else next(iter(EXPRESSIONS)))
        self._oset("clothing", f.clothing if f.clothing in CLOTHING else next(iter(CLOTHING)))
        self._oset("shirt_color", f.shirt_color if f.shirt_color in SHIRT_COLORS else "Zufällig")
        self._oset("shirt_color2", f.shirt_color2 if f.shirt_color2 in SHIRT_COLORS else "Zufällig")
        self._oset("shirt_pattern", f.shirt_pattern if f.shirt_pattern in SHIRT_PATTERNS else "Einfarbig")
        self._update_pattern()
        self._refresh_club_presets()
        self._oset("background", f.background if f.background in BACKGROUNDS else next(iter(BACKGROUNDS)))
        v["skin_details"].set(f.skin_details)
        v["extra_prompt"].set(f.extra_prompt)
        self._oset("personality", f.personality if f.personality in personality_names() else NO_PERS)
        self._oset("personality_strength", f.personality_strength if f.personality_strength in STRENGTHS else "Normal")
        v["tattoo_min_age"].set(f.tattoo_min_age)
        v["list_personality"].set("")
        self._update_styles()
        styles = HAIR_STYLES_FEMALE if f.gender == "Weiblich" else HAIR_STYLES_MALE
        self._oset("hair_style", f.hair_style if f.hair_style in styles else AUTO)
        self._update_pers_hint()

        v["output_dir"].set(c.output_dir)
        v["forge_dir"].set(c.forge_dir)
        v["forge_autostart"].set(c.forge_autostart)
        v["check_updates"].set(c.check_updates)
        v["pattern"].set(c.pattern)
        v["count"].set(c.count)
        v["delay"].set(c.delay)
        v["subfolder_per_country"].set(c.subfolder_per_country)
        v["overwrite"].set(c.overwrite)
        self._oset("list_name_mode", c.list_name_mode if c.list_name_mode in LIST_NAME_MODES else "Name")
        self._oset("list_parent_mode", c.list_parent_mode if c.list_parent_mode in PARENT_MODES else "Zufällig")
        v["aging_ages"].set(c.aging_ages)
        v["zoom"].set(p.zoom)
        v["face_y"].set(p.face_y)
        v["sharpen"].set(p.sharpen)

        self._oset("backend", b.backend if b.backend in BACKENDS else next(iter(BACKENDS)))
        v["pollinations_url"].set(b.pollinations_url)
        v["pollinations_model"].set(b.pollinations_model)
        v["pollinations_token"].set(b.pollinations_token)
        v["sd_url"].set(b.sd_url)
        v["sd_steps"].set(b.sd_steps)
        v["sd_cfg"].set(b.sd_cfg)
        v["gen_size"].set(b.gen_size)
        self._update_mix()

    def _read_from_ui(self) -> None:
        c, v = self.cfg, self.v

        def num(key, default, cast=int):
            try:
                return cast(v[key].get())
            except (tk.TclError, ValueError):
                return default

        f = c.face
        f.country = self._oget("country", f.country)
        f.second_country = self._oget("second_country", NO_SECOND)
        f.parent_mode = self._oget("parent_mode", "Zufällig")
        eth = self._oget("ethnicity", AUTO_ETH)
        f.ethnicity = eth if eth in ETHNICITIES else AUTO
        f.gender = v["gender"].get() if v["gender"].get() in GENDERS else "Männlich"
        f.age_min, f.age_max = sorted((num("age_min", 15), num("age_max", 17)))
        f.hair_color = self._oget("hair_color", AUTO)
        f.hair_style = self._oget("hair_style", AUTO)
        f.facial_hair = self._oget("facial_hair", AUTO)
        f.expression = self._oget("expression", next(iter(EXPRESSIONS)))
        f.clothing = self._oget("clothing", next(iter(CLOTHING)))
        f.shirt_color = self._oget("shirt_color", "Zufällig")
        f.shirt_color2 = self._oget("shirt_color2", "Zufällig")
        f.shirt_pattern = self._oget("shirt_pattern", "Einfarbig")
        f.background = self._oget("background", next(iter(BACKGROUNDS)))
        f.skin_details = bool(v["skin_details"].get())
        f.extra_prompt = v["extra_prompt"].get()
        f.personality = self._oget("personality", NO_PERS)
        f.personality_strength = self._oget("personality_strength", "Normal")
        f.tattoo_min_age = num("tattoo_min_age", 16)

        c.output_dir = v["output_dir"].get().strip() or str(settings_mod.default_output_dir())
        c.forge_dir = v["forge_dir"].get().strip()
        c.forge_autostart = bool(v["forge_autostart"].get())
        c.check_updates = bool(v["check_updates"].get())
        c.pattern = v["pattern"].get().strip()
        c.count = max(1, num("count", 5))
        c.delay = max(0.0, num("delay", 3.0, float))
        c.subfolder_per_country = bool(v["subfolder_per_country"].get())
        c.overwrite = bool(v["overwrite"].get())
        c.list_name_mode = self._oget("list_name_mode", "Name")
        c.list_parent_mode = self._oget("list_parent_mode", "Zufällig")
        c.aging_ages = v["aging_ages"].get()
        p = c.process
        p.zoom = round(num("zoom", 1.6, float), 2)
        p.face_y = round(num("face_y", 0.56, float), 2)
        p.sharpen = bool(v["sharpen"].get())

        b = c.backend
        b.backend = self._oget("backend", next(iter(BACKENDS)))
        b.pollinations_url = v["pollinations_url"].get().strip() or b.pollinations_url
        b.pollinations_model = v["pollinations_model"].get().strip() or "flux"
        b.pollinations_token = v["pollinations_token"].get().strip()
        b.sd_url = v["sd_url"].get().strip() or b.sd_url
        b.sd_steps = num("sd_steps", 30)
        b.sd_cfg = num("sd_cfg", 5.0, float)
        b.gen_size = num("gen_size", 768)

    # ================================================================== Helfer
    def _filter_country(self, event, var: str) -> None:
        if event.keysym in ("Up", "Down", "Return", "KP_Enter", "Escape", "Tab", "Shift_L", "Shift_R"):
            return
        k2l, _, keys = self.omap[var]
        text = self.v[var].get().strip().casefold()
        with_none = NO_SECOND in keys
        real = [k for k in keys if k != NO_SECOND]
        starts = [k for k in real if k2l[k].casefold().startswith(text)]
        contains = [k for k in real if text in k2l[k].casefold() and k not in starts]
        hits = (starts + contains) or real
        self.ocb[var]["values"] = ([k2l[NO_SECOND]] if with_none else []) + [k2l[k] for k in hits]

    def _confirm_country(self, var: str) -> str:
        """Enter im Länderfeld: besten Treffer übernehmen."""
        k2l, l2k, keys = self.omap[var]
        cb = self.ocb[var]
        text = self.v[var].get().strip()
        if text in l2k:
            key = l2k[text]
        elif NO_SECOND in keys and text in ("", "-", "—"):
            key = NO_SECOND
        else:
            hit = self._best_match([k2l[k] for k in keys if k != NO_SECOND], text)
            key = l2k[hit] if hit else None
        if key is not None:
            self._oset(var, key)
        else:
            self._validate_country(var)
        cb["values"] = [k2l[k] for k in keys]
        cb.icursor("end")
        cb.selection_range(0, "end")
        self._country_selected(var)
        return "break"

    def _country_selected(self, var: str) -> None:
        if var in ("country", "second_country"):
            self._update_mix()

    def _validate_country(self, var: str) -> None:
        k2l, l2k, keys = self.omap[var]
        text = self.v[var].get().strip()
        allow_none = NO_SECOND in keys
        if not text and not allow_none and var != "country":
            return  # leeres Feld der Spielerliste bleibt leer
        if text not in l2k:
            hit = self._best_match([k2l[k] for k in keys if k != NO_SECOND], text)
            if hit:
                self.v[var].set(hit)
            elif allow_none:
                self._oset(var, NO_SECOND)
            else:
                self._oset(var, self.cfg.face.country if var == "country" else keys[0])
        self.ocb[var]["values"] = [k2l[k] for k in keys]
        self._update_mix()

    def _update_mix(self) -> None:
        name = self._oget("country")
        if name not in COUNTRIES:
            return
        second = self._oget("second_country", NO_SECOND)
        has_second = second in COUNTRIES and second != name
        self.parent_cb.configure(state="readonly" if has_second else "disabled")
        if self._oget("ethnicity", AUTO_ETH) != AUTO_ETH:
            self.mix_label.config(text=t("mix.fixed"))
            return

        def fmt(mix):
            total = sum(mix.values())
            return " · ".join(f"{ethnicity(k)} {round(100 * w / total)} %"
                              for k, w in sorted(mix.items(), key=lambda kv: -kv[1]))

        text = t("mix.dist", country=country(name)) + fmt(COUNTRIES[name][1])
        if has_second:
            mode = self._oget("parent_mode", "Zufällig")
            text += "\n" + t("mix.parents", country=country(second)) + fmt(COUNTRIES[second][1])
            key = {"Beide Eltern aus diesem Land": "mix.both", "Ein Elternteil (gemischt)": "mix.one"}.get(mode,
                                                                                                         "mix.random")
            text += "\n" + t(key, country=country(name), second=country(second))
        self.mix_label.config(text=text)

    def _update_pers_hint(self) -> None:
        name = self._oget("personality", NO_PERS)
        if name in PERSONALITIES:
            p = PERSONALITIES[name]
            cues = ", ".join(c[0] for c in p["cues"])
            self.pers_hint.config(text=t("pers.expr", expr=p["expr"], cues=cues))
        elif name == RANDOM_PERS:
            self.pers_hint.config(text=t("pers.random_hint"))
        else:
            self.pers_hint.config(text=t("pers.none_hint"))

    def _update_styles(self) -> None:
        female = self.v["gender"].get() == "Weiblich"
        current = self._oget("hair_style", AUTO) if "hair_style" in self.omap else AUTO
        styles = HAIR_STYLES_FEMALE if female else HAIR_STYLES_MALE
        self._set_options("hair_style", styles, lambda k: opt("hair_style", k))
        self._oset("hair_style", current if current in styles else AUTO)
        self.beard_cb.configure(state="disabled" if female else "readonly")

    def _choose_dir(self, initial: str | None = None) -> None:
        d = filedialog.askdirectory(title=t("dlg.choose_dir"),
                                    initialdir=initial or self.v["output_dir"].get() or str(Path.home()))
        if d:
            self.v["output_dir"].set(str(Path(d)))

    def _find_fm(self) -> None:
        found = settings_mod.find_fm_folders()
        if not found:
            messagebox.showinfo(APP_NAME, t("msg.no_fm"))
            self._choose_dir()
            return
        fm = found[0]
        target = fm / "graphics" / "FM27 Faces"
        ans = messagebox.askyesnocancel(APP_NAME, t("msg.fm_found", fm=fm, target=target))
        if ans is None:
            return
        if ans:
            self.v["output_dir"].set(str(target))
        else:
            self._choose_dir(str(fm))

    def _open_out(self) -> None:
        d = Path(self.v["output_dir"].get())
        if not d.exists():
            try:
                d.mkdir(parents=True, exist_ok=True)
            except OSError:
                return
        open_path(d)

    def _out_dir(self, country_key: str | None = None) -> Path:
        base = Path(self.cfg.output_dir)
        return base / (country_key or self.cfg.face.country) if self.cfg.subfolder_per_country else base

    def _make_generator(self, out_dir: Path | None = None, overwrite: bool | None = None) -> Generator:
        return Generator(self.cfg.backend, self.cfg.process, out_dir or self._out_dir(), self.cfg.pattern,
                         self.cfg.delay, overwrite=self.cfg.overwrite if overwrite is None else overwrite)

    # ================================================================== Generieren (gemeinsam)
    def _busy(self) -> bool:
        return bool(self.worker and self.worker.is_alive())

    def _set_busy(self, busy: bool) -> None:
        self.go_btn.configure(state="disabled" if busy else "normal")
        self.stop_btn.configure(state="normal" if busy else "disabled")

    def _prepare(self) -> bool:
        if self._busy():
            messagebox.showinfo(APP_NAME, t("msg.busy"))
            return False
        self._read_from_ui()
        settings_mod.save(self.cfg)
        if self.forge.state == "starting" and self.cfg.backend.backend == StableDiffusionWebUIBackend.name:
            messagebox.showinfo(APP_NAME, t("msg.forge_starting"))
            return False
        try:
            Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, t("msg.dir_error", e=exc))
            return False
        return True

    def _run(self, gen: Generator, jobs: list[Job], kind: str, replace_idx: int | None = None) -> None:
        """Startet die Jobs im Hintergrund. kind: batch | list | aging | reroll"""
        if not jobs:
            return
        self.generator = gen
        self.errors = 0
        self.done_ok = 0
        total = len(jobs)
        self.progress.configure(maximum=total, value=0)
        self.status.config(text=t("status.generating", total=total))
        self._set_busy(True)
        self.run_pos = (1, total)
        if hasattr(gen.backend, "status_cb"):
            gen.backend.status_cb = lambda msg: self.q.put(("info", 0, total, None, msg, kind, None))

        def work():
            gen.run_jobs(jobs,
                         on_done=lambda i, job, face: self.q.put(("done", i, total, job, face, kind, replace_idx)),
                         on_error=lambda i, job, exc: self.q.put(("error", i, total, job, exc, kind, None)))
            self.q.put(("finished", total, total, None, None, kind, None))

        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()

    def _start(self) -> None:
        if not self._prepare():
            return
        gen = self._make_generator()
        try:
            gen.out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self.right_nb.select(0)
        jobs = [Job(options=copy.deepcopy(self.cfg.face)) for _ in range(self.cfg.count)]
        self._run(gen, jobs, "batch")

    def _stop(self) -> None:
        if self.generator:
            self.generator.cancel.set()
            self.status.config(text=t("status.cancelling"))

    def _poll(self) -> None:
        try:
            while True:
                kind, i, total, job, payload, run_kind, replace_idx = self.q.get_nowait()
                if kind == "update":
                    if payload and should_notify(__version__, payload["version"], self.cfg.skip_version):
                        self._show_update(payload)
                    continue
                if kind == "forge":
                    if hasattr(self, "forge_status") and self.forge_status.winfo_exists():
                        self.forge_status.config(text=payload)
                    if not self._busy():
                        self.status.config(text=payload[:140])
                    continue
                if kind == "info":
                    pos, tot = getattr(self, "run_pos", (1, total))
                    self.status.config(text=t("status.info", pos=pos, total=tot, msg=payload)[:140])
                    continue
                if kind in ("done", "error"):
                    self.run_pos = (min(i + 1, total), total)
                if kind == "done":
                    self.done_ok += 1
                    if replace_idx is not None and replace_idx < len(self.faces):
                        self._replace_face(replace_idx, payload)
                    else:
                        self._add_face(payload)
                    if job.tag and self.tree.exists(job.tag):
                        self.tree.set(job.tag, "status", "✓ " + payload.path.name)
                        self.tree.item(job.tag, tags=("ok",))
                        self.players[job.tag].image = payload.path
                    self.progress.configure(value=i)
                    self.status.config(text=t("status.done_one", i=i, total=total, name=payload.path.name))
                elif kind == "error":
                    self.errors += 1
                    self.progress.configure(value=i)
                    if job.tag and self.tree.exists(job.tag):
                        self.tree.set(job.tag, "status", t("list.error", e=payload)[:120])
                        self.tree.item(job.tag, tags=("err",))
                    self.status.config(text=t("status.error", i=i, e=payload)[:120])
                    cancelled = bool(self.generator and self.generator.cancel.is_set())
                    if self.errors == 1 and not cancelled:
                        messagebox.showerror(APP_NAME, t("msg.error", i=i, e=payload))
                elif kind == "finished":
                    self._set_busy(False)
                    where = self.generator.out_dir if self.generator else self.cfg.output_dir
                    self.status.config(text=t("status.finished", n=self.done_ok, where=where)
                                       + (t("status.finished_err", n=self.errors) if self.errors else ""))
                    self._update_list_info()
        except queue.Empty:
            pass
        self.after(150, self._poll)

    # ================================================================== Galerie
    def _add_face(self, face: GeneratedFace) -> None:
        self.faces.append(face)
        for old in self.faces[:-KEEP_RAW]:
            old.raw = None
        self._rebuild_gallery()
        self._select(len(self.faces) - 1)
        self.canvas.yview_moveto(1.0)

    def _replace_face(self, idx: int, face: GeneratedFace) -> None:
        self.faces[idx] = face
        self._rebuild_gallery()
        self._select(idx)

    def _rebuild_gallery(self) -> None:
        for w in self.thumb_widgets:
            w.destroy()
        self.thumb_widgets, self.thumbs = [], []
        for idx, face in enumerate(self.faces):
            photo = ImageTk.PhotoImage(_on_checker(face.image, THUMB))
            lbl = tk.Label(self.grid_frame, image=photo, borderwidth=3, relief="flat", background="#f4f4f4",
                           cursor="hand2")
            lbl.bind("<Button-1>", lambda e, i=idx: self._click_thumb(e, i))
            lbl.bind("<Double-Button-1>", lambda e, i=idx: open_path(self.faces[i].path))
            self._make_drag_source(lbl, lambda i=idx: i)
            self.thumbs.append(photo)
            self.thumb_widgets.append(lbl)
        self._relayout()

    def _click_thumb(self, event, idx: int) -> None:
        """Klick = auswählen, Strg+Klick = hinzufügen/entfernen, Shift+Klick = Bereich."""
        ctrl, shift = bool(event.state & 0x4), bool(event.state & 0x1)
        if shift and self.selected is not None:
            lo, hi = sorted((self.selected, idx))
            self.marked = set(range(lo, hi + 1))
        elif ctrl:
            self.marked = set(self.marked) ^ {idx}
            if not self.marked:
                self.marked = {idx}
        else:
            self.marked = {idx}
        self._select(idx, keep_marks=True)
        try:
            event.widget.focus_set()
        except tk.TclError:
            pass

    def _marked_faces(self) -> list[GeneratedFace]:
        idxs = sorted(i for i in self.marked if 0 <= i < len(self.faces)) or (
            [self.selected] if self.selected is not None and self.selected < len(self.faces) else [])
        return [self.faces[i] for i in idxs]

    def _relayout(self) -> None:
        cols = max(1, self.canvas.winfo_width() // (THUMB + 12))
        for idx, lbl in enumerate(self.thumb_widgets):
            lbl.grid(row=idx // cols, column=idx % cols, padx=3, pady=3)

    def _select(self, idx: int, keep_marks: bool = False) -> None:
        if not keep_marks:
            self.marked = {idx} if 0 <= idx < len(self.faces) else set()
        if not (0 <= idx < len(self.faces)):
            self.selected = None
            self.marked = set()
            self.preview.config(image=self.blank_img)
            self.sel_info.config(text="")
            return
        self.selected = idx
        for i, lbl in enumerate(self.thumb_widgets):
            lbl.config(background="#2f7de1" if i == idx else ("#9cc3f2" if i in self.marked else "#f4f4f4"))
        face = self.faces[idx]
        self.preview_img = ImageTk.PhotoImage(_on_checker(face.image, PREVIEW))
        self.preview.config(image=self.preview_img, width=PREVIEW, height=PREVIEW)
        m = face.prompt.meta
        roots = ""
        if m.get("herkunft") and m["herkunft"] != m["land"]:
            roots = t("sel.roots", roots=" + ".join(country(x) for x in m["herkunft"].split(" and ")))
        eth = (" + ".join(ethnicity(k) for k in m.get("ethnie_key", "").split("+") if k in ETHNICITIES)
               or m.get("ethnie") or "—")
        text = (f"{face.path.name}\n{country(m['land'])}{roots}\n{eth}\n"
                + t("sel.age", gender=opt("gender", m["geschlecht"]), age=m["alter"]) + f"\n{m['haare']}")
        if m.get("persoenlichkeit"):
            text += "\n" + t("sel.pers", p=pers_short(m["persoenlichkeit"]))
        if face.source == "log":
            text += "\n" + t("sel.from_log")
        elif face.source == "unknown":
            text += "\n" + t("sel.unknown")
        self.sel_info.config(text=text)

    def _current(self) -> GeneratedFace | None:
        return self.faces[self.selected] if self.selected is not None and self.selected < len(self.faces) else None

    def _reroll(self) -> None:
        face = self._current()
        if not face or not self._prepare():
            return
        # gleicher Dateiname -> Datei wird ersetzt (wichtig für Spielerlisten-Namen)
        gen = self._make_generator(out_dir=face.path.parent, overwrite=True)
        self._run(gen, [Job(options=copy.deepcopy(face.options), filename=face.path.stem)], "reroll", self.selected)

    def _aging(self) -> None:
        face = self._current()
        if not face:
            messagebox.showinfo(APP_NAME, t("msg.select_first"))
            return
        ages = parse_ages(self.v["aging_ages"].get())
        jobs = aging_jobs(face, ages)
        if not jobs:
            messagebox.showinfo(APP_NAME, t("msg.enter_ages"))
            return
        if not self._prepare():
            return
        gen = self._make_generator(out_dir=face.path.parent)
        if not getattr(gen.backend, "supports_img2img", False):
            if face.source == "unknown":
                messagebox.showinfo(APP_NAME, t("msg.aging_need_local"))
                return
            self.after(300, lambda: self.status.config(text=t("status.aging_online")))
        self._run(gen, jobs, "aging")

    def _load_images(self) -> None:
        """Bereits erstellte Bilder in die Galerie holen (z. B. für ein späteres Alterungs-Set)."""
        paths = filedialog.askopenfilenames(
            title=t("dlg.load_images"), initialdir=self.v["output_dir"].get() or str(Path.home()),
            filetypes=[(t("dlg.png"), "*.png"), (t("dlg.allfiles"), "*.*")])
        if not paths:
            return
        self._read_from_ui()
        loaded, failed = 0, []
        for p in paths:
            try:
                self.faces.append(load_face(p, self.cfg.face))
                loaded += 1
            except Exception:  # noqa: BLE001 – kein Bild, beschädigt …
                failed.append(Path(p).name)
        if loaded:
            self._rebuild_gallery()
            self._select(len(self.faces) - 1)
            self.canvas.yview_moveto(1.0)
            self.right_nb.select(0)
            self.status.config(text=t("status.loaded", n=loaded))
        if failed:
            messagebox.showwarning(APP_NAME, t("msg.load_failed", names="\n".join(failed[:20])))

    def _delete(self) -> None:
        """Markierte Bilder nach Rückfrage in den Papierkorb verschieben."""
        faces = self._marked_faces()
        if not faces or self._busy():
            return
        if not messagebox.askyesno(APP_NAME, t("msg.delete_confirm", n=len(faces),
                                               names="\n".join(f.path.name for f in faces[:8])
                                               + ("\n…" if len(faces) > 8 else ""))):
            return
        failed = set(trash_files([f.path for f in faces]))
        gone = [f for f in faces if f.path not in failed]
        first = min((self.faces.index(f) for f in gone), default=self.selected or 0)
        for f in gone:
            self.faces.remove(f)
            for iid, p in self.players.items():
                if p.image == f.path:
                    p.image = None
                    if self.tree.exists(iid):
                        self.tree.set(iid, "status", "")
                        self.tree.item(iid, tags=())
        self._rebuild_gallery()
        self._select(min(first, len(self.faces) - 1))
        self._update_list_info()
        self.status.config(text=t("status.deleted", n=len(gone)))
        if failed:
            messagebox.showwarning(APP_NAME, t("msg.delete_failed", names="\n".join(p.name for p in failed)))

    def _rename(self) -> None:
        """Ausgewähltes Bild umbenennen (z. B. in den Spielernamen)."""
        face = self._current()
        if not face or self._busy():
            return
        new = simpledialog.askstring(APP_NAME, t("dlg.rename"), parent=self, initialvalue=face.path.stem)
        if not new or not new.strip() or new.strip() == face.path.stem:
            return
        old = face.path
        try:
            rename_face(face, new)
        except RenameError as exc:
            messagebox.showerror(APP_NAME, t("msg.rename_exists", name=str(exc)))
            return
        except OSError as exc:
            messagebox.showerror(APP_NAME, t("msg.rename_failed", e=exc))
            return
        for iid, p in self.players.items():
            if p.image == old:
                p.image = face.path
                if self.tree.exists(iid):
                    self.tree.set(iid, "status", "✓ " + face.path.name)
        self._select(self.selected, keep_marks=True)
        self.status.config(text=t("status.renamed", name=face.path.name))

    def _on_key_delete(self, event) -> None:
        if not isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Text)) \
                and str(self.right_nb.select()) == str(self.gallery_tab):
            self._delete()

    def _on_key_rename(self, event) -> None:
        if str(self.right_nb.select()) == str(self.gallery_tab):
            self._rename()

    def _reveal(self) -> None:
        face = self._current()
        if face:
            reveal(face.path)

    def _copy_prompt(self) -> None:
        face = self._current()
        if face:
            self.clipboard_clear()
            self.clipboard_append(face.prompt.prompt)
            self.status.config(text=t("status.copied"))

    # ================================================================== Spielerliste
    def _load_list(self) -> None:
        path = filedialog.askopenfilename(
            title=t("dlg.load_title"),
            filetypes=[(t("dlg.filetypes"), "*.html *.htm *.txt *.csv *.rtf"), (t("dlg.allfiles"), "*.*")])
        if not path:
            return
        try:
            players, warnings = load_players(path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, t("msg.read_error", e=exc))
            return
        if not players:
            messagebox.showerror(APP_NAME, "\n".join(warnings) or t("msg.no_players"))
            return
        self.tree.delete(*self.tree.get_children())
        self.players.clear()
        for p in players:
            iid = self.tree.insert("", "end")
            self.players[iid] = p
            self._refresh_row(iid)
        self._update_list_info()
        if warnings:
            messagebox.showwarning(APP_NAME, "\n\n".join(warnings))

    def _refresh_row(self, iid: str) -> None:
        p = self.players[iid]
        land = country(p.country) if p.country else (f"? {p.nation_raw}" if p.nation_raw else "?")
        land2 = country(p.country2) if p.country2 else (f"? {p.nation2_raw}" if p.nation2_raw else "")
        status = self.tree.set(iid, "status") if self.tree.set(iid, "status") else ""
        self.tree.item(iid, values=(p.name, land, land2, p.age or "", pers_short(p.personality), p.uid, status),
                       tags=("unknown",) if not p.country else ())

    def _update_list_info(self) -> None:
        n = len(self.players)
        if not n:
            return
        done = sum(1 for p in self.players.values() if p.image)
        unknown = sum(1 for p in self.players.values() if not p.country)
        text = t("list.info", n=n, done=done)
        if unknown:
            text += t("list.unknown", n=unknown)
        self.list_info.config(text=text)

    def _set_list_value(self, which: str) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, t("msg.mark_first"))
            return
        var = {"country": "list_country", "country2": "list_country2"}.get(which, "list_personality")
        value = self._oget(var, "")
        if which == "country" and value not in COUNTRIES:
            return
        for iid in sel:
            p = self.players[iid]
            if which == "personality":
                p.personality = value if value in PERSONALITIES else None
            elif which == "country":
                p.country, p.nation_raw = value, value
            else:
                p.country2 = value if value in COUNTRIES else None
                p.nation2_raw = p.country2 or ""
            self._refresh_row(iid)
        self._update_list_info()

    def _remove_players(self) -> None:
        for iid in self.tree.selection():
            self.tree.delete(iid)
            self.players.pop(iid, None)
        self._update_list_info()

    def _player_filename(self, p: Player) -> str:
        mode = self.cfg.list_name_mode
        if mode == "UID" and p.uid:
            return p.uid
        if mode == "Name_UID" and p.uid:
            return f"{p.name}_{p.uid}"
        return p.name

    def _generate_list(self, which: str) -> None:
        if not self.players:
            messagebox.showinfo(APP_NAME, t("msg.load_first"))
            return
        if which == "selected":
            iids = list(self.tree.selection())
            if not iids:
                messagebox.showinfo(APP_NAME, t("msg.mark_players"))
                return
        elif which == "missing":
            iids = [i for i in self.tree.get_children() if not self.players[i].image]
        else:
            iids = list(self.tree.get_children())
        if not iids or not self._prepare():
            return

        jobs, base = [], self.cfg.face
        for iid in iids:
            p = self.players[iid]
            opts = copy.deepcopy(base)
            opts.country = p.country or p.nation_raw or base.country
            opts.second_country = p.country2 if p.country2 and p.country2 != opts.country else NO_SECOND
            opts.parent_mode = self.cfg.list_parent_mode
            opts.ethnicity = AUTO  # Herkunft kommt aus der Liste
            if p.personality:
                opts.personality = p.personality
            jobs.append(Job(options=opts, age=p.age, filename=self._player_filename(p), tag=iid))
            self.tree.set(iid, "status", t("list.waiting"))

        out = Path(self.cfg.output_dir)
        self._run(self._make_generator(out_dir=out), jobs, "list")
        self.status.config(text=t("status.list_gen", n=len(jobs)))

    def _open_player_image(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        p = self.players.get(iid) if iid else None
        if p and p.image:
            open_path(p.image)

    # ================================================================== Ende
    def _on_close(self) -> None:
        try:
            self._read_from_ui()
            settings_mod.save(self.cfg)
        finally:
            if self.generator:
                self.generator.cancel.set()
            if self.forge.started_by_us:
                self.status.config(text=t("forge.stopping"))
                self.update_idletasks()
                self.forge.stop()
            self.destroy()


def selftest() -> int:
    """Wird vom Build geprüft: Bildverarbeitung inkl. Gesichtserkennung muss in der .exe funktionieren."""
    from .imaging import ProcessOptions, _get_cascade, process
    img = Image.new("RGB", (512, 512), (200, 200, 200))
    out = process(img, ProcessOptions(transparent=True))
    ok = out.size == (250, 250) and _get_cascade() is not None
    # Übersetzungen müssen in der .exe enthalten sein
    from .data import resolve_country
    set_language("ko")
    ok = ok and t("btn.ok") == "확인" and country("Deutschland") == "독일" and resolve_country("Allemagne") == "Deutschland"
    set_language("de")
    # Drag and Drop (tkdnd) muss in der .exe enthalten sein – nur prüfbar, wenn ein Fenster erzeugt werden kann
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception:  # noqa: BLE001 – z. B. ohne Bildschirm
        root = None
    if root is not None:
        try:
            from tkinterdnd2 import TkinterDnD
            TkinterDnD._require(root)
        except Exception:  # noqa: BLE001
            ok = False
        finally:
            root.destroy()
    return 0 if ok else 1


def main() -> None:
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001
            pass
    App().mainloop()
