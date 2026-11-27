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
from . import facedrop, ingame, theme
from . import selfupdate, winclip
from . import settings as settings_mod
from .backends import BACKENDS, BackendError, BackendSettings, StableDiffusionWebUIBackend, check_sd_webui
from .data import COUNTRIES, ETHNICITIES, load_user_overrides
from .forge import ForgeManager, api_enabled, find_launcher
from .update import check_latest, should_notify
from .generator import (GeneratedFace, Generator, Job, RenameError, aging_jobs, face_age, list_folder_images,
                        load_face, parse_ages, rename_face, safe_filename, search_key, trash_files)
from .i18n import LANGUAGES, country, ethnicity, get_language, language_label, opt, personality, set_language, t
from .personality import NONE as NO_PERS, PERSONALITIES, RANDOM as RANDOM_PERS, STRENGTHS, personality_names
from .playerlist import Player, load_players
from .prompts import (AUTO, BACKGROUNDS, CLOTHING, EXPRESSIONS, FACIAL_HAIR, GENDERS, HAIR_COLORS,
                      HAIR_STYLES_FEMALE, HAIR_STYLES_MALE, NO_SECOND, PARENT_MODES, SHIRT_COLORS, SHIRT_PATTERNS)
from tkinter import simpledialog

FOLDER_MAX = 2000  # so viele Bilder zeigt die Ordner-Galerie höchstens (die neuesten)
THUMB = 125
PREVIEW = 250
KEEP_RAW = 40  # so viele Original-KI-Bilder bleiben für Alterungs-Sets im Speicher
EXPORTER_URL = "https://www.fmscout.com/a-fm27-exporter.html"
EXPORTER_TITLE = "FM27 Exporter - Export Data: FM27 Print Screen Export | FM Scout"
LIST_NAME_MODES = ["Name", "UID", "Name_UID"]
AUTO_ETH = "auto_country"


def _checker(size: int, cell: int = 10) -> Image.Image:
    """Schachbrett hinter freigestellten Bildern (im dunklen Schema dunkel)."""
    dark = theme.colors() is theme.PALETTES["dark"]
    c1, c2 = ((58, 64, 70), (47, 52, 57)) if dark else ((255, 255, 255), (220, 220, 220))
    img = Image.new("RGB", (size, size), c1)
    px = img.load()
    for y in range(size):
        for x in range(size):
            if ((x // cell) + (y // cell)) % 2:
                px[x, y] = c2
    return img


def _on_checker(img: Image.Image, size: int) -> Image.Image:
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    if img.mode != "RGBA":
        return img
    bg = _checker(size, max(4, size // 25)).convert("RGBA")
    bg.alpha_composite(img)
    return bg.convert("RGB")


def _ingame_badge(img: Image.Image) -> Image.Image:
    """Kleiner grüner Haken unten rechts: Bild ist schon über FaceDrop im Spiel."""
    from PIL import ImageDraw
    img = img.convert("RGB").copy()
    d = ImageDraw.Draw(img)
    w, h = img.size
    r = max(9, w // 9)
    cx, cy = w - r - 4, h - r - 4
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(34, 160, 70), outline=(255, 255, 255), width=2)
    d.line((cx - r * 0.5, cy, cx - r * 0.1, cy + r * 0.45, cx + r * 0.55, cy - r * 0.4), fill=(255, 255, 255),
           width=max(2, r // 4))
    return img


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


def _fmt_size(size: int) -> str:
    return f"{size / 1_048_576:.1f} MB" if size >= 1_048_576 else f"{max(size // 1024, 1)} KB"


def surname_key(name: str) -> tuple[str, str]:
    """Sortierschlüssel Nachname: 'Merijn van Dijk' -> 'dijk', 'Markús Andri Daníelsson Marti' -> 'marti'."""
    import unicodedata
    plain = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().casefold().strip()
    parts = plain.split()
    return (parts[-1] if parts else "", plain)


class GalleryState:
    """Inhalt eines Galerie-Tabs ('new' = in dieser Sitzung erstellt, 'folder' = alle Bilder im Speicherort)."""

    def __init__(self) -> None:
        self.faces: list[GeneratedFace] = []      # angezeigte (ggf. gefilterte) Bilder
        self.all_faces: list[GeneratedFace] = []  # Ordner-Galerie: alle geladenen Bilder vor dem Suchfilter
        self.selected: int | None = None
        self.marked: set[int] = set()


# ====================================================================== Sprachdialog
class LanguageDialog(tk.Toplevel):
    """Kleines Fenster zur Sprachauswahl. Die Texte wechseln sofort in die gewählte Sprache."""

    def __init__(self, master, current: str, ask_again: bool):
        super().__init__(master)
        self.result: tuple[str, bool] | None = None
        self.resizable(False, False)
        self.codes = list(LANGUAGES)
        self.labels = {code: language_label(code) for code in LANGUAGES}
        self.lang_var = tk.StringVar(self, self.labels.get(current, self.labels["de"]))
        self.dont_ask = tk.BooleanVar(self, not ask_again)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)
        self.title_lbl = ttk.Label(frm, font=("Segoe UI", 11, "bold"))
        self.title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.lang_lbl = ttk.Label(frm)
        self.lang_lbl.grid(row=1, column=0, sticky="w", padx=(0, 8))
        cb = ttk.Combobox(frm, textvariable=self.lang_var, values=list(self.labels.values()), state="readonly",
                          width=max(len(x) for x in self.labels.values()) + 2, height=20)
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
        for code, label in self.labels.items():
            if label == self.lang_var.get():
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
    """Hinweis auf neue Version: 'Jetzt aktualisieren' (tauscht die .exe selbst aus), 'Download-Seite öffnen'
    oder 'Nein, will zocken'."""

    def __init__(self, master, current: str, latest: str, can_update: bool = False):
        super().__init__(master)
        self.title(t("upd.title"))
        self.resizable(False, False)
        self.transient(master)
        self.choice: str | None = None  # "now", "page" oder None
        self.skip = tk.BooleanVar(self, False)
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=t("upd.title"), font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(frm, text=t("upd.text", new=latest, cur=current), justify="left", wraplength=460).pack(anchor="w")
        ttk.Checkbutton(frm, text=t("upd.skip"), variable=self.skip).pack(anchor="w", pady=(12, 0))
        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text=t("upd.no"), command=self.destroy).pack(side="right")
        page = ttk.Button(btns, text=t("upd.page"), command=lambda: self._yes("page"))
        page.pack(side="right", padx=(0, 8))
        default = "page"
        if can_update:
            now = ttk.Button(btns, text=t("upd.now"), command=lambda: self._yes("now"))
            now.pack(side="right", padx=(0, 8))
            now.focus_set()
            default = "now"
        else:
            page.focus_set()
        self.bind("<Return>", lambda e: self._yes(default))
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _yes(self, choice: str) -> None:
        self.choice = choice
        self.destroy()


# ====================================================================== Vorschlagsliste
class ThemeSwitch(tk.Canvas):
    """Schiebeschalter Hell ⇄ Dunkel. Knopf links = hell (freie Fläche dunkel), Knopf rechts = dunkel
    (freie Fläche grau) – die freie Fläche zeigt also, wohin ein Klick umschaltet."""

    W, H = 58, 26
    GRAY = "#b9c1c8"

    def __init__(self, master, dark: bool, command: Callable[[], None]):
        c = theme.colors()
        super().__init__(master, width=self.W, height=self.H, highlightthickness=0, background=c["bg"],
                         cursor="hand2", takefocus=1)
        self.dark = dark
        self.command = command
        self._draw()
        self.bind("<Button-1>", self._click)
        self.bind("<space>", self._click)
        self.bind("<Return>", self._click)

    def _draw(self) -> None:
        self.delete("all")
        w, h, half = self.W, self.H, self.W // 2
        border = theme.colors()["border"]
        fill = self.GRAY if self.dark else theme.PALETTES["dark"]["bg"]
        self.create_rectangle(1, 1, w - 2, h - 2, outline=border, fill="#ffffff", width=1)
        free = (2, 2, half, h - 2) if self.dark else (half, 2, w - 2, h - 2)
        self.create_rectangle(*free, outline="", fill=fill)
        k0 = half if self.dark else 2
        self.create_rectangle(k0 + 1, 3, k0 + half - 3, h - 4, outline="#a7afb6", fill="#f4f6f7")
        cx, cy = k0 + (half - 2) // 2, h // 2
        self.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, outline="#c9cfd4", fill="#eceff1")

    def _click(self, _event=None) -> str:
        self.dark = not self.dark
        self._draw()
        self.update_idletasks()
        self.after(60, self.command)  # Schalter sichtbar umlegen, dann Oberfläche neu einfärben
        return "break"


class SuggestList:
    """Kleine Liste unter einem Eingabefeld (wie die Vorschläge einer Browser-Suchleiste).

    Nimmt nie den Tastatur-Fokus: Man tippt im Feld weiter, ↑/↓ wählt, Enter übernimmt, Esc schließt.
    Höchstens MAX_ROWS Zeilen sind sichtbar, der Rest per Mausrad."""

    MAX_ROWS = 8

    def __init__(self, master: tk.Tk, on_choose: Callable[[ttk.Combobox, str], None]):
        self.master, self.on_choose = master, on_choose
        self.top: tk.Toplevel | None = None
        self.lb: tk.Listbox | None = None
        self.cb: ttk.Combobox | None = None
        self.values: list[str] = []

    def _ensure(self) -> None:
        if self.top is not None and self.top.winfo_exists():
            return
        top = tk.Toplevel(self.master)
        top.withdraw()
        top.overrideredirect(True)
        try:
            top.attributes("-topmost", True)
        except tk.TclError:
            pass
        font = ttk.Style(self.master).lookup("TCombobox", "font") or "TkDefaultFont"
        lb = tk.Listbox(top, takefocus=0, exportselection=False, activestyle="none", relief="solid", borderwidth=1,
                        highlightthickness=0, selectbackground=theme.colors()["accent"], selectforeground=theme.colors()["accent_fg"],
                        background=theme.colors()["field"], foreground=theme.colors()["fg"], font=font)
        lb.pack(fill="both", expand=True)
        lb.bind("<ButtonRelease-1>", self._click)
        lb.bind("<Motion>", lambda e: self._select(lb.nearest(e.y)))
        lb.bind("<MouseWheel>", lambda e: (lb.yview_scroll(int(-e.delta / 120), "units"), "break")[1])
        lb.bind("<Button-4>", lambda e: (lb.yview_scroll(-1, "units"), "break")[1])
        lb.bind("<Button-5>", lambda e: (lb.yview_scroll(1, "units"), "break")[1])
        self.top, self.lb = top, lb
        if sys.platform.startswith("win"):  # Windows: Liste darf beim Anzeigen nicht aktiv werden
            try:
                import ctypes
                top.update_idletasks()
                hwnd = int(top.wm_frame(), 16)
                gwl_exstyle, ws_ex_noactivate, ws_ex_toolwindow = -20, 0x08000000, 0x00000080
                u32 = ctypes.windll.user32
                style = u32.GetWindowLongW(hwnd, gwl_exstyle)
                u32.SetWindowLongW(hwnd, gwl_exstyle, style | ws_ex_noactivate | ws_ex_toolwindow)
            except Exception:  # noqa: BLE001
                pass

    def owns(self, path: str) -> bool:
        return self.top is not None and bool(path) and path.startswith(str(self.top))

    def visible(self) -> bool:
        try:
            return self.top is not None and bool(self.top.winfo_ismapped())
        except tk.TclError:
            return False

    def show(self, cb: ttk.Combobox, values: list[str], highlight: str | None = None) -> None:
        self._ensure()
        assert self.top is not None and self.lb is not None
        self.cb, self.values = cb, list(values)
        self.lb.delete(0, "end")
        self.lb.insert("end", *self.values)
        self.lb.configure(height=min(self.MAX_ROWS, len(self.values)))
        cb.update_idletasks()
        self.top.update_idletasks()
        x, y = cb.winfo_rootx(), cb.winfo_rooty() + cb.winfo_height()
        w, h = max(cb.winfo_width(), 120), self.lb.winfo_reqheight()
        self.top.geometry(f"{w}x{h}+{x}+{y}")
        if not self.top.winfo_ismapped():
            self.top.deiconify()
        self.top.lift()
        self.highlight(highlight)

    def _select(self, i: int) -> None:
        if self.lb is None or not self.values:
            return
        i = max(0, min(len(self.values) - 1, i))
        self.lb.selection_clear(0, "end")
        self.lb.selection_set(i)
        self.lb.activate(i)
        self.lb.see(i)

    def highlight(self, label: str | None) -> None:
        if self.lb is None:
            return
        self.lb.selection_clear(0, "end")
        if label in self.values:
            self._select(self.values.index(label))
        else:
            self.lb.yview_moveto(0)

    def current(self) -> str | None:
        if self.lb is None or not self.visible():
            return None
        sel = self.lb.curselection()
        return self.values[sel[0]] if sel and sel[0] < len(self.values) else None

    def move(self, step: int) -> None:
        cur = self.current()
        if cur in self.values:
            self._select(self.values.index(cur) + step)
        elif self.values:
            self._select(0 if step > 0 else len(self.values) - 1)

    def hide(self) -> None:
        try:
            if self.top is not None and self.top.winfo_exists():
                self.top.withdraw()
        except tk.TclError:
            pass
        self.cb = None

    def _click(self, event) -> None:
        if self.lb is None or self.cb is None or not self.values:
            return
        i = self.lb.nearest(event.y)
        label, cb = self.values[i], self.cb
        self.hide()
        self.on_choose(cb, label)


# ====================================================================== Hauptfenster
class App(tk.Tk):
    # Galerie-Daten des gerade sichtbaren Tabs ('Neu erstellt' oder 'Galerie')
    faces = property(lambda self: self.gal[self.gmode].faces,
                     lambda self, value: setattr(self.gal[self.gmode], "faces", value))
    selected = property(lambda self: self.gal[self.gmode].selected,
                        lambda self, value: setattr(self.gal[self.gmode], "selected", value))
    marked = property(lambda self: self.gal[self.gmode].marked,
                      lambda self, value: setattr(self.gal[self.gmode], "marked", value))

    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {__version__}")
        try:  # Fußball-Symbol für Fenster und Taskleiste
            from .icon import make_icon
            self._icons = [ImageTk.PhotoImage(make_icon(sz)) for sz in (256, 48, 32, 16)]
            self.iconphoto(True, *self._icons)
        except Exception:  # noqa: BLE001
            pass
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
        self.gal = {"new": GalleryState(), "folder": GalleryState()}
        self.gmode = "new"  # welcher Galerie-Tab gerade angezeigt wird
        self.folder_load_id = 0
        self.folder_dirty = True
        self.folder_loaded_dir: str | None = None
        self.thumbs: list[ImageTk.PhotoImage] = []
        self.thumb_widgets: list[tk.Label] = []
        self.preview_img: ImageTk.PhotoImage | None = None
        self.errors = 0
        self.done_ok = 0
        self.players: dict[str, Player] = {}  # Treeview-ID -> Spieler

        self.dnd = self._init_dnd()
        self.forge = ForgeManager(settings_mod.config_dir() / "forge.log")
        # FaceDrop (nur lesen): erkannter Ordner, Inhalt (Hash -> Datei) für "✓ im Spiel" und Aufräumen
        self.gal_src = "own"           # Galerie-Tab zeigt: "own" = Speicherort, "fd" = FaceDrop
        self.fd_dir: Path | None = None
        self.fd_info: facedrop.FaceDropInfo | None = None
        self.fd_index: dict[str, Path] = {}
        self.fd_sizes: set[int] = set()
        self.fd_declined: set[Path] = set()  # "Nein" beim Aufräumen – in dieser Sitzung nicht mehr fragen
        self.fd_asking = False
        self.fd_stop = threading.Event()
        self._detect_facedrop()
        self._build()
        self._load_into_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Delete>", self._on_key_delete)
        if self.cfg.check_updates:
            threading.Thread(target=lambda: self.q.put(("update", 0, 0, None, check_latest(
                include_prereleases=self.cfg.update_prereleases), "", None)),
                             daemon=True).start()
        if self.cfg.forge_autostart and self.cfg.forge_dir \
                and self.cfg.backend.backend == StableDiffusionWebUIBackend.name:
            self.after(800, lambda: self._forge_start(True))
        self.bind("<F2>", self._on_key_rename)
        self.bind("<Button-1>", self._click_anywhere, add="+")
        self.bind("<Configure>", self._on_root_configure, add="+")
        self.bind("<Unmap>", lambda e: self._unpost_list() if e.widget is self else None, add="+")
        self.bind("<Control-c>", self._on_key_copy)
        self.bind("<Control-a>", self._on_key_select_all)
        self.bind("<Control-A>", self._on_key_select_all)
        self.bind("<Control-C>", self._on_key_copy)
        threading.Thread(target=self._fd_watch, daemon=True).start()
        if self.fd_info:
            self.status.config(text=t("fd.found_short", v=self.fd_info.version or "?"))
        self.after(100, self._poll)
        self.after(150, self._bring_to_front)
        if self.warnings:
            self.after(500, lambda: messagebox.showwarning(APP_NAME, "\n".join(self.warnings)))
        if self.cfg.moved_from:  # Speicherort wurde beim Start nach graphics\faces verschoben
            settings_mod.save(self.cfg)
            self.after(700, lambda: messagebox.showinfo(APP_NAME, t("msg.out_moved", old=self.cfg.moved_from,
                                                                     new=self.cfg.output_dir)))

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
        """Farbschema (hell/dunkel) mit dem Grün aus dem Symbol – siehe theme.py."""
        self.c = theme.apply(self, getattr(self.cfg, "theme", "light"))

    def _toggle_theme(self) -> None:
        if self._busy():
            self.theme_switch.dark = self.cfg.theme == "dark"
            self.theme_switch._draw()
            messagebox.showinfo(APP_NAME, t("msg.lang_busy"))
            return
        self.cfg.theme = "light" if self.cfg.theme == "dark" else "dark"
        self._style()
        self._apply_language(get_language())  # Oberfläche mit den neuen Farben neu aufbauen
        theme.dark_title_bar(self, self.cfg.theme == "dark")

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
        """Auswahlfelder: Tippen öffnet die Liste und springt zum passenden Eintrag, Enter übernimmt."""
        state = {"buf": "", "t": 0.0}

        def on_key(e):
            if e.keysym in ("Return", "KP_Enter"):
                picked = self._list_pick(cb)
                if picked:
                    self.v[var].set(picked)
                self._unpost_list(cb)
                cb.event_generate("<<ComboboxSelected>>")
                return "break"
            if e.keysym in ("Down", "Up"):
                return self._list_nav(cb, 1 if e.keysym == "Down" else -1)
            if e.keysym == "Escape":
                self._unpost_list(cb)
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
            self._post_list(cb, hit or self.v[var].get())
            return "break"

        cb.bind("<KeyPress>", on_key)
        cb.bind("<FocusOut>", lambda e: self._list_focus_out(cb, None), add="+")

    def _bind_search_field(self, cb: ttk.Combobox, var: str) -> None:
        """Länder-/Persönlichkeitsfelder: Tippen filtert und öffnet die Liste (bester Treffer markiert),
        ↑/↓ wählt in der Liste, Enter übernimmt, Esc schließt. Ein Klick ins Feld markiert den alten Text,
        damit Tippen ihn ersetzt (sonst entstünde z. B. 'KeineSöl')."""
        cb.bind("<KeyRelease>", lambda e: self._filter_country(e, var))
        cb.bind("<Return>", lambda e: self._confirm_country(var))
        cb.bind("<KP_Enter>", lambda e: self._confirm_country(var))
        cb.bind("<Down>", lambda e: self._list_nav(cb, 1, var))
        cb.bind("<Up>", lambda e: self._list_nav(cb, -1, var))
        cb.bind("<Escape>", lambda e: self._unpost_list(cb) or "break")
        cb.bind("<<ComboboxSelected>>", lambda e: self._country_selected(var), add="+")
        cb.bind("<FocusIn>", lambda e: self._select_all_on_focus(cb))
        cb.bind("<FocusOut>", lambda e: self._list_focus_out(cb, var))

    # ---- Vorschlagsliste beim Tippen (wie bei einer Suchleiste im Browser)
    # Eigene kleine Liste unter dem Feld statt der eingebauten Aufklappliste: Sie nimmt nie den Tastatur-Fokus,
    # daher kann Windows sie nicht sofort wieder schließen (das passierte mit der eingebauten Liste).
    _posted: ttk.Combobox | None = None
    _refocus = False

    def _suggest(self) -> "SuggestList":
        if getattr(self, "_suggest_list", None) is None:
            self._suggest_list = SuggestList(self, self._suggest_chosen)
        return self._suggest_list

    def _post_list(self, cb: ttk.Combobox, highlight: str | None = None) -> None:
        values = list(cb["values"])
        if not values:
            self._unpost_list(cb)
            return
        self._suggest().show(cb, values, highlight)
        self._posted = cb

    def _unpost_list(self, cb: ttk.Combobox | None = None) -> None:
        if cb is None or self._posted is cb:
            if getattr(self, "_suggest_list", None) is not None:
                self._suggest_list.hide()
            self._posted = None

    def _list_pick(self, cb: ttk.Combobox) -> str | None:
        """Markierter Eintrag der offenen Vorschlagsliste (oder None)."""
        if self._posted is not cb:
            return None
        return self._suggest().current()

    def _list_nav(self, cb: ttk.Combobox, step: int, var: str | None = None) -> str:
        if self._posted is not cb:
            current = self.v[var].get() if var else cb.get()
            values = list(cb["values"])
            self._post_list(cb, current if current in values else None)
            return "break"
        self._suggest().move(step)
        return "break"

    def _suggest_chosen(self, cb: ttk.Combobox, label: str) -> None:
        """Eintrag in der Vorschlagsliste angeklickt."""
        self._posted = None
        var = next((k for k, w in self.ocb.items() if w is cb), None)
        if var is None:
            return
        self.v[var].set(label)
        self._refocus = True
        cb.focus_set()
        cb.after(150, lambda: setattr(self, "_refocus", False))
        if str(cb.cget("state")) == "readonly":
            cb.event_generate("<<ComboboxSelected>>")
        else:
            self._confirm_country(var)

    def _select_all_on_focus(self, cb: ttk.Combobox) -> None:
        if self._refocus:
            return
        cb.after_idle(lambda: (cb.selection_range(0, "end"), cb.icursor("end")))

    def _list_focus_out(self, cb: ttk.Combobox, var: str | None) -> None:
        def check():
            try:
                focus = str(cb.tk.call("focus"))
            except tk.TclError:
                focus = ""
            sl = getattr(self, "_suggest_list", None)
            if focus == str(cb) or (sl is not None and sl.owns(focus)):
                if sl is not None and sl.owns(focus):  # Windows hat der Liste den Fokus gegeben – zurückholen
                    self._refocus = True
                    cb.focus_force()
                    cb.after(150, lambda: setattr(self, "_refocus", False))
                return
            self._ui_log(f"Liste geschlossen (Fokus ging zu {focus or 'anderem Programm'})")
            self._unpost_list(cb)
            if var is not None:
                self._validate_country(var)
        cb.after(120, check)

    def _ui_log(self, text: str) -> None:
        """Kleines Protokoll (%APPDATA%\\FM27FaceGenerator\\ui.log) – hilft bei Problemen unter Windows."""
        try:
            log = settings_mod.config_dir() / "ui.log"
            if log.exists() and log.stat().st_size > 100_000:
                log.write_text("", encoding="utf-8")
            with log.open("a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text + "\n")
        except OSError:
            pass

    def _click_anywhere(self, event) -> None:
        """Klick irgendwo anders im Fenster schließt eine beim Tippen geöffnete Liste."""
        cb = self._posted
        if cb is not None and event.widget is not cb:
            self._unpost_list(cb)

    def _on_root_configure(self, event) -> None:
        if event.widget is self and self._posted is not None:  # Fenster verschoben/verkleinert
            self._unpost_list()

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
                    "list_country", "list_country2", "personality", "personality_strength", "list_personality",
                    "facedrop_cleanup", "gal_source", "fd_career"):
            v[key] = tk.StringVar(self)
        for key in ("age_min", "age_max", "count", "gen_size", "sd_steps", "tattoo_min_age"):
            v[key] = tk.IntVar(self)
        for key in ("zoom", "face_y", "delay", "sd_cfg"):
            v[key] = tk.DoubleVar(self)
        v["forge_dir"] = tk.StringVar(self)
        for key in ("skin_details", "sharpen", "subfolder_per_country", "overwrite", "forge_autostart", "check_updates",
                    "update_prereleases", "sd_fast"):
            v[key] = tk.BooleanVar(self)
        # Alterungs-Set: Werte überleben den Neuaufbau (Sprache/Farbschema)
        old = getattr(self, "_aging_vals", (0, False))
        v["aging_plus"] = tk.IntVar(self, old[0])
        v["list_gender"] = tk.StringVar(self, self.cfg.list_gender if self.cfg.list_gender in GENDERS else "Männlich")
        v["replace_ingame"] = tk.BooleanVar(self, old[1])
        v["aging_plus"].trace_add("write", lambda *a: self._update_aging_inputs())

        if getattr(self, "accent_line", None) is None:  # schmaler grüner Streifen oben
            self.accent_line = tk.Frame(self, height=4)
            self.accent_line.pack(side="top", fill="x")
        self.accent_line.configure(background=self.c["accent"])
        root = self.root_frame = ttk.Frame(self, padding=8)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        top = ttk.Frame(root)
        top.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        ttk.Label(top, text=t("theme.light")).pack(side="left")
        self.theme_switch = ThemeSwitch(top, self.cfg.theme == "dark", self._toggle_theme)
        self.theme_switch.pack(side="left", padx=8)
        ttk.Label(top, text=t("theme.dark")).pack(side="left")

        left = ttk.Frame(root)
        left.grid(row=1, column=0, sticky="nsw")
        # Sicherungskopie löschen – unten links, in allen Tabs sichtbar
        self.backup_btn = ttk.Button(left, text=t("btn.clear_backup0"), style="Danger.TButton",
                                     command=self._clear_backup)
        self.backup_btn.pack(side="bottom", fill="x", pady=(8, 0))
        nb = self.left_nb = ttk.Notebook(left, width=410)
        nb.pack(fill="both", expand=True)
        self._build_tab_player(nb)
        self._build_tab_look(nb)
        self._build_tab_output(nb)
        self._build_tab_ai(nb)

        right = ttk.Notebook(root)
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.right_nb = right
        self._build_gallery(right)
        self._build_playerlist(right)
        self._apply_tab_order()
        self._make_tabs_draggable(right)
        self._update_backup_btn()
        self.v["output_dir"].trace_add("write", lambda *a: self._update_backup_btn())

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
        self._row(t_, 0, t("lbl.country"), self.country_cb)

        self.second_cb = self._ocombo(t_, "second_country", [NO_SECOND] + self._countries(), country_or_none,
                                      editable=True)
        self.second_cb.bind("<<ComboboxSelected>>", lambda e: self._update_mix())
        self._row(t_, 2, t("lbl.second"), self.second_cb)
        self.parent_cb = self._ocombo(t_, "parent_mode", PARENT_MODES, lambda k: opt("parent_mode", k))
        self.parent_cb.bind("<<ComboboxSelected>>", lambda e: self._update_mix())
        self._row(t_, 4, t("lbl.parents"), self.parent_cb)

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

        # ---- Persönlichkeit (direkt im Spieler-Tab, spart das Wechseln)
        ttk.Separator(t_).grid(row=11, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        ttk.Label(t_, text=t("tab.personality"), style="Head.TLabel").grid(row=12, column=0, columnspan=2,
                                                                          sticky="w", padx=8)
        self.pers_cb = self._ocombo(t_, "personality", personality_names(), personality, editable=True)
        self.pers_cb.bind("<<ComboboxSelected>>", lambda e: self._update_pers_hint())
        self._row(t_, 13, t("lbl.personality"), self.pers_cb)
        self.pers_hint = ttk.Label(t_, text="", style="Hint.TLabel", wraplength=370, justify="left")
        self.pers_hint.grid(row=14, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 2))
        pf = ttk.Frame(t_)
        self._ocombo(pf, "personality_strength", STRENGTHS, lambda k: opt("strength", k), width=12).pack(side="left")
        self._row(t_, 15, t("lbl.strength"), pf)
        tf = ttk.Frame(t_)  # eigene Zeile: lange Übersetzungen haben so Platz
        ttk.Spinbox(tf, from_=14, to=40, textvariable=self.v["tattoo_min_age"], width=4).pack(side="left")
        self._row(t_, 16, t("lbl.tattoo"), tf, t("hint.pers_short"))

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
        ttk.Checkbutton(t_, style="Wrap.TCheckbutton", text=t("chk.skin"), variable=v["skin_details"]).grid(
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

    # ------------------------------------------------------------------ Tab: Ausgabe
    def _build_tab_output(self, nb) -> None:
        v = self.v
        t_ = ttk.Frame(nb, padding=6)
        t_.columnconfigure(1, weight=1)
        nb.add(t_, text=t("tab.output"))
        ttk.Label(t_, text=t("out.note"), style="Hint.TLabel", wraplength=370, justify="left").grid(row=0, column=0, columnspan=2, sticky="w",
                                                                   padx=8, pady=(0, 6))
        ttk.Checkbutton(t_, style="Wrap.TCheckbutton", text=t("chk.subfolder"), variable=v["subfolder_per_country"]).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Checkbutton(t_, style="Wrap.TCheckbutton", text=t("chk.overwrite"), variable=v["overwrite"]).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))
        self._row(t_, 3, t("lbl.pattern"), ttk.Entry(t_, textvariable=v["pattern"]), t("hint.pattern"))
        self._row(t_, 5, t("lbl.zoom"), ttk.Scale(t_, from_=1.2, to=3.0, variable=v["zoom"]), t("hint.zoom"))
        self._row(t_, 7, t("lbl.face_y"), ttk.Scale(t_, from_=0.35, to=0.7, variable=v["face_y"]), t("hint.face_y"))
        ttk.Checkbutton(t_, style="Wrap.TCheckbutton", text=t("chk.sharpen"), variable=v["sharpen"]).grid(
            row=9, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        ttk.Label(t_, text=t("out.always"), style="Head.TLabel").grid(row=10, column=0, columnspan=2, sticky="w",
                                                                     padx=8, pady=8)
        upd = ttk.Frame(t_)
        upd.grid(row=11, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 0))
        ttk.Checkbutton(upd, style="Wrap.TCheckbutton", text=t("chk.updates"), variable=v["check_updates"]).pack(anchor="w")
        ttk.Checkbutton(upd, style="Wrap.TCheckbutton", text=t("chk.prereleases"), variable=v["update_prereleases"]).pack(anchor="w",
                                                                                              pady=(2, 0))
        ttk.Label(t_, text="FaceDrop", style="Head.TLabel").grid(row=12, column=0, columnspan=2, sticky="w",
                                                                padx=8, pady=(12, 0))
        self.fd_status = ttk.Label(t_, text=self._fd_status_text(), style="Hint.TLabel", wraplength=370,
                                   justify="left")
        self.fd_status.grid(row=13, column=0, columnspan=2, sticky="w", padx=8)
        fb = ttk.Frame(t_)
        fb.grid(row=14, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 0))
        ttk.Button(fb, text=t("btn.fd_choose"), command=self._choose_facedrop).pack(side="left")
        ttk.Button(fb, text=t("btn.fd_auto"), command=self._auto_facedrop).pack(side="left", padx=(4, 0))
        self._row(t_, 15, t("lbl.fd_cleanup"),
                  self._ocombo(t_, "facedrop_cleanup", ["ask", "auto", "off"], {"ask": t("fd.clean_ask"), "auto": t("fd.clean_auto"),
                                                                    "off": t("fd.clean_off")}.get,
                               width=24), t("hint.fd_cleanup"))

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
        ttk.Checkbutton(t_, style="Wrap.TCheckbutton", text=t("chk.forge_auto"), variable=v["forge_autostart"]).grid(
            row=11, column=0, columnspan=2, sticky="w", padx=8, pady=(2, 0))
        self.forge_status = ttk.Label(t_, text=self._forge_status_text(), style="Hint.TLabel", wraplength=370,
                                      justify="left")
        self.forge_status.grid(row=12, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Label(t_, text=t("head.general"), style="Head.TLabel").grid(row=13, column=0, sticky="w", padx=8,
                                                                       pady=(10, 0))
        self._row(t_, 14, t("lbl.gen_size"), ttk.Combobox(t_, textvariable=v["gen_size"], values=[512, 768, 1024],
                                                          width=6), t("hint.gen_size"))
        self._row(t_, 16, t("lbl.delay"), ttk.Spinbox(t_, from_=0, to=60, textvariable=v["delay"], width=6))
        ttk.Checkbutton(t_, style="Wrap.TCheckbutton", text=t("chk.sd_fast"), variable=v["sd_fast"]).grid(
            row=17, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 0))


    # ---- Update-Hinweis
    def _show_update(self, info: dict) -> None:
        can = bool(info.get("asset")) and selfupdate.can_self_update()
        dlg = UpdateDialog(self, __version__, info["version"], can_update=can)
        dlg.grab_set()
        self.wait_window(dlg)
        if dlg.skip.get():
            self.cfg.skip_version = info["version"]
            settings_mod.save(self.cfg)
        if dlg.choice == "page":
            import webbrowser
            webbrowser.open(info["url"])
        elif dlg.choice == "now":
            self._self_update(info)

    def _self_update(self, info: dict) -> None:
        """Neue Version laden, .exe austauschen lassen und neu starten."""
        if self._busy():
            messagebox.showinfo(APP_NAME, t("msg.busy"))
            return
        win = tk.Toplevel(self)
        win.title(t("upd.title"))
        win.resizable(False, False)
        win.transient(self)
        frm = ttk.Frame(win, padding=16)
        frm.pack(fill="both", expand=True)
        lbl = ttk.Label(frm, text=t("upd.downloading", v=info["version"]))
        lbl.pack(anchor="w")
        bar = ttk.Progressbar(frm, mode="determinate", length=360, maximum=100)
        bar.pack(fill="x", pady=(8, 8))
        cancel = threading.Event()
        ttk.Button(frm, text=t("btn.cancel"), command=cancel.set).pack(anchor="e")
        win.protocol("WM_DELETE_WINDOW", cancel.set)
        win.grab_set()
        exe = selfupdate.exe_path()

        def finish(error: str | None, new: tuple[str, Path] | None) -> None:
            if win.winfo_exists():
                win.destroy()
            if cancel.is_set():
                return
            if error or not new:
                if messagebox.askyesno(APP_NAME, t("upd.failed", e=error or "?")):
                    import webbrowser
                    webbrowser.open(info["url"])
                return
            try:
                selfupdate.launch_swap(new[1], new[0])
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror(APP_NAME, t("upd.failed", e=exc))
                return
            self.status.config(text=t("upd.restarting"))
            self.update_idletasks()
            self._on_close()

        def work():
            import tempfile
            zpath = Path(tempfile.gettempdir()) / f"FM27-FaceGenerator-{info['version']}.zip"
            try:
                selfupdate.download(info["asset"], zpath,
                                    progress=lambda f: self.after(0, lambda: bar.winfo_exists() and bar.configure(
                                        value=f * 100)),
                                    cancelled=cancel.is_set)
                new = selfupdate.unpack(zpath, exe.parent, exe.name)
                self.after(0, lambda: finish(None, new))
            except InterruptedError:
                self.after(0, lambda: finish(None, None))
            except Exception as exc:  # noqa: BLE001
                err = str(exc)
                self.after(0, lambda: finish(err, None))
            finally:
                try:
                    zpath.unlink()
                except OSError:
                    pass

        threading.Thread(target=work, daemon=True).start()

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
        # Zwei Tabs teilen sich eine Galerie-Ansicht (self.gal_frame wird beim Tab-Wechsel umgehängt)
        self.tab_new = ttk.Frame(nb)
        self.tab_folder = ttk.Frame(nb)
        nb.add(self.tab_new, text=t("tab.new"))
        nb.add(self.tab_folder, text=t("tab.gallery"))
        tab = self.gal_frame = ttk.Frame(nb, padding=6)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        head = ttk.Frame(tab)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.head_new = ttk.Frame(head)
        ttk.Label(self.head_new, text=t("gal.hint"), style="Hint.TLabel", wraplength=470,
                  justify="left").pack(side="left")
        ttk.Button(self.head_new, text=t("btn.load_images"), command=self._load_images).pack(side="right")
        ttk.Button(self.head_new, text=t("btn.select_all"), command=self._select_all).pack(side="right", padx=(0, 6))
        self.head_folder = ttk.Frame(head)
        src = ttk.Frame(self.head_folder)
        src.pack(fill="x", pady=(0, 4))
        ttk.Label(src, text=t("gal.source")).pack(side="left")
        self.v["gal_source"].set(self.gal_src)
        ttk.Radiobutton(src, text=t("gal.src_own"), value="own", variable=self.v["gal_source"],
                        command=self._on_gal_source).pack(side="left", padx=(6, 0))
        self.fd_radio = ttk.Radiobutton(src, text="FaceDrop", value="fd", variable=self.v["gal_source"],
                                        command=self._on_gal_source)
        self.fd_radio.pack(side="left", padx=(6, 0))
        self.career_cb = ttk.Combobox(src, textvariable=self.v["fd_career"], state="readonly", width=24)
        self.career_cb.bind("<<ComboboxSelected>>", lambda e: self._load_folder())
        self.career_lbl = ttk.Label(src, text=t("gal.career"))
        self.career_open = ttk.Button(src, text=t("btn.open"), command=self._open_career)
        row2 = ttk.Frame(self.head_folder)
        row2.pack(fill="x")
        ttk.Label(row2, text=t("gal.search")).pack(side="left")
        self.v["folder_filter"] = tk.StringVar(self)
        search = ttk.Entry(row2, textvariable=self.v["folder_filter"], width=22)
        search.pack(side="left", padx=(4, 8))
        self.v["folder_filter"].trace_add("write", lambda *a: self._apply_folder_filter())
        ttk.Button(row2, text=t("btn.refresh"), command=self._load_folder).pack(side="left")
        ttk.Button(row2, text=t("btn.select_all"), command=self._select_all).pack(side="left", padx=(6, 0))
        self.folder_info = ttk.Label(row2, text="", style="Hint.TLabel", wraplength=240, justify="left")
        self.folder_info.pack(side="left", padx=(10, 0))
        self._update_fd_widgets()
        nb.bind("<<NotebookTabChanged>>", lambda e: self._on_right_tab())
        gal = ttk.Frame(tab, relief="sunken", borderwidth=1)
        gal.grid(row=1, column=0, sticky="nsew")
        gal.rowconfigure(0, weight=1)
        gal.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(gal, background=self.c["canvas"], highlightthickness=0)
        sb = ttk.Scrollbar(gal, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.grid_frame = tk.Frame(self.canvas, background=self.c["canvas"])
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
        self.blank_img = ImageTk.PhotoImage(Image.new("RGB", (PREVIEW, PREVIEW), self.c["preview"]))
        self.preview = tk.Label(side, image=self.blank_img, width=PREVIEW, height=PREVIEW, background=self.c["preview"],
                                relief="sunken", cursor="hand2")
        self._make_drag_source(self.preview, lambda: self.selected)
        self.preview.pack(pady=4)
        self.sel_info = ttk.Label(side, text="", wraplength=PREVIEW, justify="left", style="Hint.TLabel")
        self.sel_info.pack(anchor="w", fill="x")
        btns = ttk.Frame(side)
        btns.pack(fill="x")
        btns.columnconfigure((0, 1), weight=1)
        for n, (text, cmd) in enumerate(((t("btn.reroll"), self._reroll), (t("btn.rename"), self._rename),
                                         (t("btn.copy_file"), self._copy_files), (t("btn.reveal"), self._reveal),
                                         (t("btn.copy_prompt"), self._copy_prompt), (t("btn.delete"), self._delete))):
            ttk.Button(btns, text=text, command=cmd).grid(row=n // 2, column=n % 2, sticky="ew", padx=1, pady=1)

        aging = ttk.Frame(tab)
        aging.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        row1 = ttk.Frame(aging)
        row1.pack(fill="x")
        ttk.Label(row1, text=t("aging.title"), style="Head.TLabel").pack(side="left")
        self.ages_entry = ttk.Entry(row1, textvariable=self.v["aging_ages"], width=16)
        self.ages_entry.pack(side="left", padx=(6, 0))
        ttk.Label(row1, text=t("aging.years")).pack(side="left", padx=(4, 10))
        # "+ Jahre": jedes markierte Bild wird um so viele Jahre älter (die feste Liste wird dann ausgegraut)
        ttk.Label(row1, text=t("aging.or")).pack(side="left")
        ttk.Spinbox(row1, from_=0, to=20, textvariable=self.v["aging_plus"], width=4).pack(side="left", padx=(4, 0))
        ttk.Label(row1, text=t("aging.plus_years")).pack(side="left", padx=(4, 10))
        ttk.Button(row1, text=t("btn.create"), style="Accent.TButton", command=self._aging).pack(side="left")
        # nur in Galerie → FaceDrop: im Spiel ersetzen, Saison, Rückgängig
        self.aging_fd_row = ttk.Frame(aging)
        ttk.Checkbutton(self.aging_fd_row, text=t("chk.replace_ingame"), variable=self.v["replace_ingame"]).pack(
            side="left")
        ttk.Button(self.aging_fd_row, text=t("btn.season"), command=self._season).pack(side="left", padx=(12, 0))
        self.undo_btn = ttk.Button(self.aging_fd_row, text=t("btn.undo_replace"), command=self._undo_replace)
        self.undo_btn.pack(side="left", padx=(6, 0))
        self._update_aging_inputs()

    # ------------------------------------------------------------------ Spielerliste
    def _build_playerlist(self, nb) -> None:
        v = self.v
        tab = self.tab_list = ttk.Frame(nb, padding=6)
        nb.add(tab, text=t("tab.list"))
        self._show_mode(self.gmode, force=True)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        bar = ttk.Frame(tab)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(bar, text=t("btn.load_list"), command=self._load_list).pack(side="left")
        ttk.Button(bar, text=t("btn.export_help"), command=self._export_help).pack(side="left", padx=6)
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
        self.tree.tag_configure("unknown", foreground=self.c["warn"])
        self.tree.tag_configure("ok", foreground=self.c["ok"])
        self.tree.tag_configure("err", foreground=self.c["err"])
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
                                                personality, width=18, editable=True), "personality"),
        )
        for col, (label, widget, which) in enumerate(widgets):
            ttk.Label(edit, text=label).grid(row=1 + col // 2, column=(col % 2) * 3, sticky="w", padx=(0, 4), pady=2)
            widget.grid(row=1 + col // 2, column=(col % 2) * 3 + 1, sticky="w", pady=2)
            ttk.Button(edit, text=t("btn.set"), width=9, command=lambda w=which: self._set_list_value(w)).grid(
                row=1 + col // 2, column=(col % 2) * 3 + 2, sticky="w", padx=(4, 14), pady=2)
        ttk.Button(edit, text=t("btn.select_all"), style="Outline.TButton", command=self._select_all_players).grid(
            row=2, column=3, columnspan=3, sticky="w", pady=2)

        run = ttk.Frame(tab)
        run.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        run.columnconfigure(0, weight=1)
        ttk.Button(run, text=t("btn.remove"), command=self._remove_players).grid(row=0, column=5, sticky="e",
                                                                                 pady=(0, 14))
        self.list_info = ttk.Label(run, text=t("list.none"), style="Hint.TLabel")
        self.list_info.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 14))
        # FM exportiert kein Geschlecht – deshalb direkt an den Generier-Knöpfen wählen (Standard: Männlich)
        gf = ttk.Frame(run)
        gf.grid(row=1, column=1, padx=(8, 10))
        ttk.Label(gf, text=t("lbl.gender") + ":").pack(side="left", padx=(0, 4))
        for g in GENDERS:
            ttk.Radiobutton(gf, text=opt("gender", g), value=g, variable=v["list_gender"]).pack(side="left", padx=2)
        ttk.Button(run, text=t("btn.gen_selected"), command=lambda: self._generate_list("selected")).grid(row=1,
                                                                                                          column=3)
        ttk.Button(run, text=t("btn.gen_missing"), command=lambda: self._generate_list("missing")).grid(
            row=1, column=4, padx=6)
        ttk.Button(run, text=t("btn.gen_all"), command=lambda: self._generate_list("all")).grid(row=1, column=5)

    # ------------------------------------------------------------------ untere Leiste
    def _build_bottom(self, root) -> None:
        v = self.v
        out = ttk.Frame(root)
        out.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
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
        bottom.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        bottom.columnconfigure(5, weight=1)
        ttk.Label(bottom, text=t("lbl.count")).grid(row=0, column=0)
        ttk.Spinbox(bottom, from_=1, to=500, textvariable=v["count"], width=6).grid(row=0, column=1, padx=(4, 12))
        self.go_btn = ttk.Button(bottom, text=t("btn.generate"), style="Big.TButton", command=self._start)
        self.go_btn.grid(row=0, column=2)
        self.stop_btn = ttk.Button(bottom, text=t("btn.cancel"), command=self._stop, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=8)
        self.progress = ttk.Progressbar(bottom, mode="determinate", length=220)
        self.progress.grid(row=0, column=4, padx=8)
        # Text bekommt den restlichen Platz und bricht bei Bedarf um (nichts wird abgeschnitten)
        self.status = ttk.Label(bottom, text=t("status.ready"), anchor="w", justify="left")
        self.status.grid(row=0, column=5, sticky="ew")
        self.status.bind("<Configure>", lambda e: self.status.configure(wraplength=max(e.width - 4, 100)))

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
        right_tab = self._right_key()
        left_tab = self.left_nb.index("current")
        self._unpost_list()
        self._aging_vals = (self._aging_plus(), bool(self.v["replace_ingame"].get()))
        self.root_frame.destroy()
        self.thumb_widgets, self.thumbs, self.thumb_badge, self.players = [], [], [], {}
        self._build()
        self._load_into_ui()
        for p in players:
            iid = self.tree.insert("", "end")
            self.players[iid] = p
            self._refresh_row(iid)
            if p.image:
                self.tree.set(iid, "status", "✓ " + p.image.name)
                self.tree.item(iid, tags=("ok",))
        self._update_list_info()
        self.right_nb.select(self._right_tabs()[right_tab])
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
        v["update_prereleases"].set(c.update_prereleases)
        self._oset("facedrop_cleanup", c.facedrop_cleanup)
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
        v["sd_fast"].set(b.sd_fast)
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
        c.update_prereleases = bool(v["update_prereleases"].get())
        c.facedrop_cleanup = self._oget("facedrop_cleanup", "ask")
        c.pattern = v["pattern"].get().strip()
        c.count = max(1, num("count", 5))
        c.delay = max(0.0, num("delay", 3.0, float))
        c.subfolder_per_country = bool(v["subfolder_per_country"].get())
        c.overwrite = bool(v["overwrite"].get())
        c.list_name_mode = self._oget("list_name_mode", "Name")
        c.list_parent_mode = self._oget("list_parent_mode", "Zufällig")
        c.list_gender = self.v["list_gender"].get() if self.v["list_gender"].get() in GENDERS else "Männlich"
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
        b.sd_fast = bool(v["sd_fast"].get())
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
        cb = self.ocb[var]
        cb["values"] = ([k2l[NO_SECOND]] if with_none else []) + [k2l[k] for k in hits]
        if event.keysym in ("Control_L", "Control_R", "Alt_L", "Alt_R") or (event.state & 0x4):
            return
        self._post_list(cb, k2l[hits[0]] if text and (starts or contains) else None)

    def _confirm_country(self, var: str) -> str:
        """Enter im Länderfeld: besten Treffer übernehmen."""
        k2l, l2k, keys = self.omap[var]
        cb = self.ocb[var]
        picked = self._list_pick(cb)  # in der offenen Liste markierter Eintrag hat Vorrang
        if picked:
            self.v[var].set(picked)
        self._unpost_list(cb)
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
        elif var == "personality":
            self._update_pers_hint()

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
        self._country_selected(var)

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
        target = settings_mod.fm_output_dir(fm)
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
        # Die Pause zwischen Bildern ist nur fürs Online-Limit da – lokal (Forge) würde sie nur bremsen
        local = self.cfg.backend.backend == StableDiffusionWebUIBackend.name
        return Generator(self.cfg.backend, self.cfg.process, out_dir or self._out_dir(), self.cfg.pattern,
                         0.0 if local else self.cfg.delay,
                         overwrite=self.cfg.overwrite if overwrite is None else overwrite)

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

    def _run(self, gen: Generator, jobs: list[Job], kind: str, replace_idx: tuple[str, int] | None = None,
             retries: int = 0) -> None:
        """Startet die Jobs im Hintergrund. kind: batch | list | aging | reroll"""
        if not jobs:
            return
        self.generator = gen
        self.errors = 0
        self.done_ok = 0
        self.run_started = time.monotonic()
        self.run_timing: list[dict] = []
        self.run_replace: list[tuple[GeneratedFace, Path]] = []  # (fertiges Bild in der Warteschlange, FaceDrop-Ziel)
        self.run_failed: list[str] = []
        if kind != "aging":
            self.run_skipped = []
        total = len(jobs)
        self.progress.configure(maximum=total * 100, value=0)
        self.prog_done, self.prog_sub, self.prog_real = 0, 0.0, False
        if hasattr(gen.backend, "progress_cb"):
            gen.backend.progress_cb = lambda f: self.q.put(("progress", 0, total, None, f, kind, None))
        self.after(200, self._tick_progress)
        self.status.config(text=t("status.generating", total=total))
        self._set_busy(True)
        self.run_pos = (1, total)
        if hasattr(gen.backend, "status_cb"):
            gen.backend.status_cb = lambda msg: self.q.put(("info", 0, total, None, msg, kind, None))

        def work():
            gen.run_jobs(jobs,
                         on_done=lambda i, job, face: self.q.put(("done", i, total, job, face, kind, replace_idx)),
                         on_error=lambda i, job, exc: self.q.put(("error", i, total, job, exc, kind, None)),
                         retries=retries)
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
        self.right_nb.select(self.tab_new)
        self._show_mode("new")
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
                if kind == "fdindex":
                    self._fd_index_update(payload)
                    continue
                if kind == "dups":
                    self._handle_dups(payload)
                    continue
                if kind == "forge":
                    if hasattr(self, "forge_status") and self.forge_status.winfo_exists():
                        self.forge_status.config(text=payload)
                    if not self._busy():
                        self.status.config(text=payload[:140])
                    continue
                if kind == "progress":
                    self.prog_real = True  # echter Fortschritt von Forge: 5 % … 95 % des aktuellen Bildes
                    self.prog_sub = max(self.prog_sub, 5 + 90 * float(payload))
                    self._show_progress()
                    continue
                if kind == "info":
                    pos, tot = getattr(self, "run_pos", (1, total))
                    self.status.config(text=t("status.info", pos=pos, total=tot, msg=payload)[:140])
                    continue
                if kind in ("done", "error"):
                    self.run_pos = (min(i + 1, total), total)
                    self.prog_done, self.prog_sub, self.prog_real = i, 0.0, False
                if kind == "done":
                    self.done_ok += 1
                    if payload.timing:
                        self.run_timing.append(payload.timing)
                    if job.replace is not None:
                        self.run_replace.append((payload, job.replace))
                    if job.tag and job.tag in self.players:
                        payload.player_name = self.players[job.tag].name
                    if replace_idx is not None:
                        self._replace_face(replace_idx, payload)
                    else:
                        self._add_face(payload)
                    self.folder_dirty = True
                    if job.tag and self.tree.exists(job.tag):
                        self.tree.set(job.tag, "status", "✓ " + payload.path.name)
                        self.tree.item(job.tag, tags=("ok",))
                        self.players[job.tag].image = payload.path
                    self._show_progress()
                    self.status.config(text=t("status.done_one", i=i, total=total, name=payload.path.name)
                                       + self._eta_text(i, total))
                elif kind == "error":
                    self.errors += 1
                    if job is not None:
                        self.run_failed.append(job.filename or (job.replace.name if job.replace else f"#{i}"))
                    self._show_progress()
                    if job.tag and self.tree.exists(job.tag):
                        self.tree.set(job.tag, "status", t("list.error", e=payload)[:120])
                        self.tree.item(job.tag, tags=("err",))
                    self.status.config(text=t("status.error", i=i, e=payload)[:120])
                    cancelled = bool(self.generator and self.generator.cancel.is_set())
                    if self.errors == 1 and not cancelled:
                        messagebox.showerror(APP_NAME, t("msg.error", i=i, e=payload))
                elif kind == "finished":
                    self._set_busy(False)
                    self.prog_done, self.prog_sub, self.prog_real = total, 0.0, False
                    self._show_progress()
                    where = self.generator.out_dir if self.generator else self.cfg.output_dir
                    self.status.config(text=t("status.finished", n=self.done_ok, where=where)
                                       + (t("status.finished_err", n=self.errors) if self.errors else "")
                                       + self._timing_text())
                    self._update_list_info()
                    if run_kind in ("aging", "reroll"):
                        self._finish_aging()
                    if self.gmode == "folder":
                        self._load_folder()
                elif kind == "folder":
                    self._folder_batch(i, total, payload, run_kind == "done")
        except queue.Empty:
            pass
        self.after(150, self._poll)

    def _eta_text(self, done: int, total: int) -> str:
        """' · noch ca. 9 Min.' – aus der bisherigen Durchschnittszeit."""
        if done <= 0 or done >= total:
            return ""
        per = (time.monotonic() - getattr(self, "run_started", time.monotonic())) / done
        mins = max(1, round(per * (total - done) / 60))
        return t("status.eta", m=mins)

    def _timing_text(self) -> str:
        tm = getattr(self, "run_timing", [])
        if not tm:
            return ""
        gen = sum(x["gen"] for x in tm) / len(tm)
        post = sum(x["post"] for x in tm) / len(tm)
        total = (time.monotonic() - self.run_started) / max(1, len(tm))
        fmt = lambda v: f"{v:.1f}".replace(".", "," if get_language() == "de" else ".")  # noqa: E731
        return " · " + t("status.timing", total=fmt(total), gen=fmt(gen), post=fmt(post))

    def _finish_aging(self) -> None:
        """Nach dem Durchlauf: fertige Bilder in einem Rutsch ins Spiel schieben (alte vorher sichern)."""
        self.after(300, self._update_backup_btn)  # neue Sicherungskopien
        pairs = getattr(self, "run_replace", [])
        skipped = getattr(self, "run_skipped", [])
        failed_gen = getattr(self, "run_failed", [])
        if pairs:
            cancelled = bool(self.generator and self.generator.cancel.is_set())
            if cancelled and not messagebox.askyesno(APP_NAME, t("msg.replace_cancelled", n=len(pairs))):
                for face, _target in pairs:
                    face.path.unlink(missing_ok=True)
                pairs = []
        done: list[Path] = []
        failed: list[tuple[Path, str]] = []
        if pairs:
            done, failed = ingame.apply_replacements([(f.path, target) for f, target in pairs], self.cfg.output_dir)
            moved = {target for target in done}
            for face, target in pairs:  # Galerie zeigt ab jetzt das Bild im Spiel
                if target in moved:
                    for st in self.gal.values():
                        for f in st.faces + st.all_faces:
                            if f is face:
                                f.path = target
            self._update_aging_inputs()
            self.folder_dirty = True
            if self.gmode == "folder":
                self._load_folder()
        if pairs or skipped or (failed_gen and len(failed_gen) + self.done_ok > 1):
            msg = t("msg.replace_done", n=len(done)) if pairs else t("status.finished", n=self.done_ok,
                                                                        where=self.cfg.output_dir)
            if failed or failed_gen:
                names = [p.name for p, _e in failed] + failed_gen
                msg += t("msg.replace_failed", n=len(names), names=self._name_list(names))
            if skipped:
                msg += t("msg.replace_skipped", n=len(skipped), names=self._name_list(skipped))
            messagebox.showinfo(APP_NAME, msg)
        self.run_replace, self.run_skipped, self.run_failed = [], [], []

    # ---- Ladebalken
    def _show_progress(self) -> None:
        self.progress.configure(value=self.prog_done * 100 + min(self.prog_sub, 99))

    def _tick_progress(self) -> None:
        """Läuft während der Erzeugung: ohne echte Rückmeldung (Pollinations) wandert der Balken gleichmäßig
        weiter und wird zum Ende hin langsamer – er bleibt nie stehen, springt aber auch nicht übers Ziel."""
        if not self._busy():
            return
        if not self.prog_real:
            self.prog_sub += (95 - self.prog_sub) * 0.012
        self._show_progress()
        self.after(200, self._tick_progress)

    # ================================================================== Galerie
    def _add_face(self, face: GeneratedFace) -> None:
        """Neu erzeugte Bilder landen immer im Tab 'Neu erstellt'."""
        st = self.gal["new"]
        st.faces = [f for f in st.faces if f.path != face.path]  # ersetztes Bild (gleicher Name) nicht doppelt
        st.faces.insert(0, face)  # neueste zuerst
        if getattr(face, "player_name", None):
            # Spieler aus der Spielerliste: alphabetisch nach Nachnamen (oben), andere Bilder darunter
            players = sorted((f for f in st.faces if getattr(f, "player_name", None)),
                             key=lambda f: surname_key(f.player_name))
            st.faces = players + [f for f in st.faces if not getattr(f, "player_name", None)]
        idx = st.faces.index(face)
        for old in st.faces[KEEP_RAW:]:
            old.raw = None
        st.marked = set()
        if self.gmode == "new":
            self._rebuild_gallery()
            self._select(idx)
            if idx == 0:
                self.canvas.yview_moveto(0.0)
        else:
            st.selected = idx

    def _replace_face(self, target: tuple[str, int], face: GeneratedFace) -> None:
        mode, idx = target
        st = self.gal[mode]
        if 0 <= idx < len(st.faces):
            old = st.faces[idx]
            st.faces[idx] = face
            if old in st.all_faces:
                st.all_faces[st.all_faces.index(old)] = face
        if mode == self.gmode:
            self._rebuild_gallery()
            self._select(idx)

    # ---- Tabs rechts: per Ziehen mit der Maus umsortieren (Reihenfolge wird gespeichert)
    def _right_tabs(self) -> dict[str, ttk.Frame]:
        return {"new": self.tab_new, "folder": self.tab_folder, "list": self.tab_list}

    def _right_key(self) -> str:
        """Welcher Tab rechts gerade offen ist: 'new', 'folder' oder 'list' (unabhängig von der Reihenfolge)."""
        current = self.right_nb.select()
        return next((k for k, w in self._right_tabs().items() if str(w) == current), "new")

    def _apply_tab_order(self) -> None:
        tabs = self._right_tabs()
        order = [k for k in (self.cfg.tab_order or []) if k in tabs]
        order += [k for k in tabs if k not in order]
        for pos, key in enumerate(order):
            self.right_nb.insert(pos, tabs[key])

    def _make_tabs_draggable(self, nb: ttk.Notebook) -> None:
        drag: dict = {"tab": None}

        def tab_at(x: int, y: int) -> int | None:
            try:
                return nb.index(f"@{x},{y}")
            except tk.TclError:
                return None

        def press(e):
            if nb.identify(e.x, e.y) in ("label", "tab", "padding", "focus") or tab_at(e.x, e.y) is not None:
                idx = tab_at(e.x, e.y)
                drag["tab"] = nb.tabs()[idx] if idx is not None else None

        def motion(e):
            if drag["tab"] is None:
                return
            idx = tab_at(e.x, e.y)
            if idx is None or nb.tabs()[idx] == drag["tab"]:
                return
            nb.insert(idx, drag["tab"])
            nb.configure(cursor="fleur")

        def release(_e):
            if drag["tab"] is not None:
                nb.configure(cursor="")
                names = {str(w): k for k, w in self._right_tabs().items()}
                order = [names[w] for w in nb.tabs() if w in names]
                if order != list(self.cfg.tab_order or []):
                    self.cfg.tab_order = order
                    settings_mod.save(self.cfg)
            drag["tab"] = None

        nb.bind("<ButtonPress-1>", press, add="+")
        nb.bind("<B1-Motion>", motion, add="+")
        nb.bind("<ButtonRelease-1>", release, add="+")

    # ---- Galerie-Tabs umschalten
    def _on_right_tab(self) -> None:
        key = self._right_key()
        if key in ("new", "folder"):
            self._show_mode(key)

    def _show_mode(self, mode: str, force: bool = False) -> None:
        """Hängt die gemeinsame Galerie-Ansicht in den gewählten Tab und zeigt dessen Bilder."""
        tab = self.tab_new if mode == "new" else self.tab_folder
        changed = force or mode != self.gmode or self.gal_frame.winfo_manager() == ""
        self.gmode = mode
        self._update_aging_inputs()
        if changed:
            self.gal_frame.pack_forget()
            self.gal_frame.pack(in_=tab, fill="both", expand=True)
            self.gal_frame.lift()
            (self.head_folder if mode == "new" else self.head_new).pack_forget()
            (self.head_new if mode == "new" else self.head_folder).pack(fill="x")
            self._rebuild_gallery()
            self._select(self.selected if self.selected is not None else -1, keep_marks=True)
        if mode == "folder":
            current_dir = self._folder_key(self.v["output_dir"].get().strip() or self.cfg.output_dir)
            if self.folder_dirty or current_dir != self.folder_loaded_dir:
                self._load_folder()
            elif not self.folder_info.cget("text"):  # z. B. nach Sprachwechsel neu aufgebaut
                n = len(self.gal["folder"].all_faces)
                self.folder_info.config(text=t("gal.count", n=n) if n else t("gal.empty"))

    def _bring_to_front(self) -> None:
        """Beim Start gleich sichtbar im Vordergrund – nicht erst über die Taskleiste holen müssen."""
        try:
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.focus_force()
            self.after(600, lambda: self.attributes("-topmost", False))
        except tk.TclError:
            pass

    # ================================================================== FaceDrop (nur lesen)
    def _detect_facedrop(self) -> None:
        manual = Path(self.cfg.facedrop_dir) if self.cfg.facedrop_dir else None
        d = manual if manual and manual.is_dir() else None
        if d is None:
            try:
                d = facedrop.find_facedrop_dir()
            except Exception:  # noqa: BLE001 – Erkennung darf nie stören
                d = None
        self.fd_dir = d
        self.fd_info = facedrop.read_info(d) if d else None
        if d is None and self.gal_src == "fd":
            self.gal_src = "own"

    def _fd_status_text(self) -> str:
        if not self.fd_info:
            return t("fd.none")
        return t("fd.found", v=self.fd_info.version or "?", path=self.fd_info.folder)

    def _update_fd_widgets(self) -> None:
        if hasattr(self, "fd_status") and self.fd_status.winfo_exists():
            self.fd_status.config(text=self._fd_status_text())
        if not hasattr(self, "fd_radio"):
            return
        self.fd_radio.configure(state="normal" if self.fd_dir else "disabled")
        self.v["gal_source"].set(self.gal_src)
        fd = self.gal_src == "fd"
        if fd:
            self._refresh_careers()
            self.career_lbl.pack(side="left", padx=(12, 4))
            self.career_cb.pack(side="left")
            self.career_open.pack(side="left", padx=(6, 0))
        else:
            self.career_lbl.pack_forget()
            self.career_cb.pack_forget()
            self.career_open.pack_forget()
        self._update_aging_inputs()

    def _refresh_careers(self) -> None:
        """Karrieren aus FaceDrops Ordner (neueste zuerst) + 'Echte Spieler'."""
        if not self.fd_dir:
            return
        self.fd_info = facedrop.read_info(self.fd_dir)
        kdir = self.fd_dir / "karrieren"

        def mtime(key: str) -> float:
            try:
                return (kdir / key).stat().st_mtime
            except OSError:
                return 0.0

        keys = sorted(self.fd_info.careers, key=mtime, reverse=True)
        self.career_map = {self.fd_info.careers[k]: k for k in keys}
        self.career_map[t("fd.real")] = ""
        labels = list(self.career_map)
        self.career_cb["values"] = labels
        if self.v["fd_career"].get() not in self.career_map:
            self.v["fd_career"].set(labels[0])

    def _open_career(self) -> None:
        """Ordner der gewählten Karriere (bzw. bei 'Echte Spieler' den FaceDrop-Ordner) im Explorer öffnen."""
        if not self.fd_dir:
            return
        key = self._career_key()
        folder = self.fd_dir / "karrieren" / key if key else self.fd_dir
        if folder.is_dir():
            open_path(folder)
            self.status.config(text=t("status.fd_open_hint"))

    def _career_key(self) -> str:
        return getattr(self, "career_map", {}).get(self.v["fd_career"].get(), "")

    def _on_gal_source(self) -> None:
        self.gal_src = self.v["gal_source"].get() if self.fd_dir else "own"
        self._update_fd_widgets()
        self._load_folder()

    def _choose_facedrop(self) -> None:
        d = filedialog.askdirectory(title=t("dlg.fd_dir"), initialdir=str(self.fd_dir or Path.home()))
        if not d:
            return
        d = Path(d)
        if d.name.casefold() != "facedrop" and (d / "facedrop").is_dir():
            d = d / "facedrop"  # FM-Benutzerordner gewählt
        if not ((d / "karrieren").is_dir() or (d / "startschutz.txt").exists()):
            if not messagebox.askyesno(APP_NAME, t("msg.fd_not_facedrop", folder=d)):
                return
        self.cfg.facedrop_dir = str(d)
        self._fd_changed()

    def _auto_facedrop(self) -> None:
        self.cfg.facedrop_dir = ""
        self._fd_changed()
        if not self.fd_dir:
            messagebox.showinfo(APP_NAME, t("fd.none"))

    def _fd_changed(self) -> None:
        settings_mod.save(self.cfg)
        self.fd_index, self.fd_sizes = {}, set()
        self._detect_facedrop()
        self._update_fd_widgets()
        self.folder_dirty = True
        if self.gmode == "folder":
            self._load_folder()

    def _in_game(self, face: GeneratedFace) -> bool:
        """Liegt dieses Bild (als identische Kopie) schon bei FaceDrop, ist also im Spiel?"""
        if facedrop.is_facedrop_path(face.path):
            return True
        if not self.fd_index:
            return False
        try:
            return face.path.stat().st_size in self.fd_sizes and facedrop.file_hash(face.path) in self.fd_index
        except OSError:
            return False

    def _fd_watch(self) -> None:
        """Hintergrund: FaceDrops Ordner beobachten (beim Start und dann alle paar Sekunden)."""
        wait = 1.0
        known: set[str] = set()
        while not self.fd_stop.wait(wait):
            wait = 2.0  # alle 2 s – dank Zwischenspeicher (Hash je Datei) kostet das kaum etwas
            fd = self.fd_dir
            if not fd:
                continue
            try:
                index = facedrop.facedrop_index(fd)
                new = [p for h, p in index.items() if h not in known]
                if known and new:
                    self._fd_log(f"neu bei FaceDrop: {', '.join(p.name for p in new[:5])}")
                known = set(index)
                self.q.put(("fdindex", 0, 0, None, index, "", None))
                if self.cfg.facedrop_cleanup != "off" and not self.fd_asking:
                    own = list_folder_images(self.cfg.output_dir, 20000)
                    dups = {k: v for k, v in facedrop.find_duplicates(own, index).items()
                            if k not in self.fd_declined}
                    if dups:
                        self.q.put(("dups", 0, 0, None, dups, "", None))
            except Exception:  # noqa: BLE001 – nie stören
                pass

    def _fd_index_update(self, index: dict[str, Path]) -> None:
        if set(index) == set(self.fd_index):
            return
        self.fd_index = index
        sizes = set()
        for p in index.values():
            try:
                sizes.add(p.stat().st_size)
            except OSError:
                pass
        self.fd_sizes = sizes
        if self._drop_ingame_from_new():
            return
        if self.gmode == "new" or self.gal_src == "own":
            self._refresh_badges()

    def _drop_ingame_from_new(self) -> bool:
        """Bilder aus 'Neu erstellt', die per FaceDrop im Spiel sind, aus 'Neu erstellt' nehmen – sie stehen
        dann in der Galerie. Die Datei selbst bleibt unangetastet."""
        st = self.gal["new"]
        keep = [f for f in st.faces if facedrop.is_facedrop_path(f.path) or not self._in_game(f)]
        if len(keep) == len(st.faces):
            return False
        current = st.faces[st.selected] if self.gmode != "new" and st.selected is not None \
            and 0 <= st.selected < len(st.faces) else (self._current() if self.gmode == "new" else None)
        st.faces = keep
        st.marked = set()
        idx = keep.index(current) if current in keep else (0 if keep else None)
        if self.gmode == "new":
            self._rebuild_gallery()
            if idx is not None:
                self._select(idx)
        else:
            st.selected = idx
        return True

    def _refresh_badges(self) -> None:
        """Nur die Vorschaubilder neu zeichnen, deren Haken (✓ im Spiel) sich geändert hat – nicht die ganze
        Galerie (das dauerte bei vielen Bildern mehrere Sekunden)."""
        if not hasattr(self, "thumb_badge"):
            return
        for idx, lbl in enumerate(self.thumb_widgets):
            if idx >= len(self.faces):
                break
            face = self.faces[idx]
            badge = not facedrop.is_facedrop_path(face.path) and self._in_game(face)
            if idx < len(self.thumb_badge) and self.thumb_badge[idx] != badge:
                thumb = _on_checker(face.image, THUMB)
                photo = ImageTk.PhotoImage(_ingame_badge(thumb) if badge else thumb)
                self.thumbs[idx] = photo
                self.thumb_badge[idx] = badge
                lbl.config(image=photo)
        if self.selected is not None:
            self._select(self.selected, keep_marks=True)

    def _fd_log(self, text: str) -> None:
        """Kleines Protokoll (%APPDATA%\\FM27FaceGenerator\\facedrop.log) – hilft, Verzögerungen nachzuvollziehen."""
        try:
            log = settings_mod.config_dir() / "facedrop.log"
            if log.exists() and log.stat().st_size > 200_000:
                log.write_text("", encoding="utf-8")
            with log.open("a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text + "\n")
        except OSError:
            pass

    def _handle_dups(self, dups: dict[Path, Path]) -> None:
        """Eigene Bilder, die FaceDrop schon (identisch) übernommen hat: nach Rückfrage in den Papierkorb."""
        dups = {k: v for k, v in dups.items() if k.exists() and v.exists() and k not in self.fd_declined}
        if not dups or self.fd_asking or self.cfg.facedrop_cleanup == "off":
            return
        if self.cfg.facedrop_cleanup == "ask":
            names = "\n".join(f"{k.name}  →  {v.parent.name}\\{v.name}" for k, v in list(dups.items())[:8])
            if len(dups) > 8:
                names += "\n…"
            self.fd_asking = True
            self._fd_log(f"Frage gezeigt: {len(dups)} doppelte Bild(er)")
            try:
                # Fenster nach vorn holen, sonst liegt die Frage evtl. unsichtbar hinter FM
                self.deiconify()
                self.lift()
                self.attributes("-topmost", True)
                ok = messagebox.askyesno(APP_NAME, t("msg.fd_dups", n=len(dups), names=names), parent=self)
            finally:
                self.attributes("-topmost", False)
                self.fd_asking = False
            if not ok:
                self.fd_declined |= set(dups)
                return
        failed = set(trash_files(list(dups)))
        moved = {k: v for k, v in dups.items() if k not in failed}
        if not moved:
            return
        for st in self.gal.values():  # Galerie zeigt ab jetzt FaceDrops Kopie (Alterungs-Set geht weiter)
            for f in st.faces + st.all_faces:
                if f.path in moved:
                    f.path = moved[f.path]
        for iid, pl in self.players.items():
            if pl.image in moved:
                pl.image = moved[pl.image]
        if self.gal_src == "own":
            st = self.gal["folder"]
            st.faces = [f for f in st.faces if not facedrop.is_facedrop_path(f.path)]
            st.all_faces = [f for f in st.all_faces if not facedrop.is_facedrop_path(f.path)]
            if self.gmode == "folder":
                st.selected, st.marked = None, set()
        self._rebuild_gallery()
        self._select(self.selected if self.selected is not None and self.selected < len(self.faces) else
                     (0 if self.faces else -1), keep_marks=False)
        self.status.config(text=t("status.fd_cleaned", n=len(moved)))

    # ---- Ordner-Galerie: alle Bilder im Speicherort
    def _folder_key(self, base: str) -> str:
        return f"{self.gal_src}|{self._career_key()}|{base}"

    def _load_folder(self) -> None:
        self._read_from_ui()
        base = self.cfg.output_dir
        use_fd = self.gal_src == "fd" and self.fd_dir is not None
        if use_fd:
            self._refresh_careers()
        career = self._career_key()
        fd_dir = self.fd_dir
        self.folder_load_id += 1
        lid = self.folder_load_id
        st = self.gal["folder"]
        st.faces, st.all_faces, st.selected, st.marked = [], [], None, set()
        self.folder_dirty, self.folder_loaded_dir = False, self._folder_key(base)
        if self.gmode == "folder":
            self._rebuild_gallery()
            self._select(-1)
        self.folder_info.config(text=t("gal.loading_fd") if use_fd else t("gal.loading"))
        fallback = copy.deepcopy(self.cfg.face)

        def work():
            if use_fd:
                files = facedrop.career_images(fd_dir, career or None)[:FOLDER_MAX + 1]
            else:
                files = list_folder_images(base, FOLDER_MAX + 1)
            total = len(files)
            batch: list[GeneratedFace] = []
            for p in files[:FOLDER_MAX]:
                if lid != self.folder_load_id:
                    return  # neuer Ladevorgang gestartet
                try:
                    batch.append(load_face(p, fallback))
                except Exception:  # noqa: BLE001 – keine gültige Bilddatei
                    continue
                if len(batch) >= 24:
                    self.q.put(("folder", lid, total, None, batch, "", None))
                    batch = []
            self.q.put(("folder", lid, total, None, batch, "done", None))

        threading.Thread(target=work, daemon=True).start()

    def _folder_batch(self, lid: int, total: int, faces: list[GeneratedFace], done: bool) -> None:
        if lid != self.folder_load_id:
            return
        st = self.gal["folder"]
        st.all_faces.extend(faces)
        key = search_key(self.v["folder_filter"].get())
        start = len(st.faces)
        st.faces.extend(f for f in faces if key in search_key(f.path.name))
        if self.gmode == "folder" and len(st.faces) > start:
            self._append_thumbs(start)
            if st.selected is None:
                self._select(0)
        n = len(st.all_faces)
        fd = self.gal_src == "fd"
        if not done:
            self.folder_info.config(text=t("gal.loading_fd" if fd else "gal.loading") + f" {n}")
        elif n == 0:
            self.folder_info.config(text=t("gal.empty_fd" if fd else "gal.empty"))
        else:
            self.folder_info.config(text=t("gal.count_fd" if fd else "gal.count", n=n)
                                    + (t("gal.capped", n=FOLDER_MAX) if total > FOLDER_MAX else ""))

    def _apply_folder_filter(self) -> None:
        st = self.gal["folder"]
        key = search_key(self.v["folder_filter"].get())
        st.faces = [f for f in st.all_faces if key in search_key(f.path.name)]
        st.selected, st.marked = None, set()
        if self.gmode == "folder":
            self._rebuild_gallery()
            self._select(0 if st.faces else -1)

    def _rebuild_gallery(self) -> None:
        for w in self.thumb_widgets:
            w.destroy()
        self.thumb_widgets, self.thumbs, self.thumb_badge = [], [], []
        self._append_thumbs(0)

    def _append_thumbs(self, start: int) -> None:
        for idx in range(start, len(self.faces)):
            face = self.faces[idx]
            thumb = _on_checker(face.image, THUMB)
            badge = not facedrop.is_facedrop_path(face.path) and self._in_game(face)
            if badge:
                thumb = _ingame_badge(thumb)
            photo = ImageTk.PhotoImage(thumb)
            if not hasattr(self, "thumb_badge"):
                self.thumb_badge = []
            self.thumb_badge.append(badge)
            lbl = tk.Label(self.grid_frame, image=photo, borderwidth=3, relief="flat", background=self.c["canvas"],
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
            lbl.config(background=self.c["select"] if i == idx else (self.c["mark"] if i in self.marked
                                                                     else self.c["canvas"]))
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
        if facedrop.is_facedrop_path(face.path):
            pid = facedrop.player_id(face.path)
            text += "\n" + (t("sel.fd_id", id=pid) if pid else t("sel.fd_real")) + "\n" + t("sel.fd_safe")
        elif self._in_game(face):
            text += "\n" + t("sel.ingame")
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
        # neues Gesicht im gleichen Alter wie das bisherige Bild (bei gealterten Bildern also das aktuelle Alter)
        job = Job(options=copy.deepcopy(face.options), age=face_age(face), filename=face.path.stem)
        if facedrop.is_facedrop_path(face.path):
            # Bild im Spiel: erst in die Warteschlange, dann mit Sicherungskopie unter gleichem Namen ersetzen
            folder = ingame.backup_root(self.cfg.output_dir)
            if not messagebox.askyesno(APP_NAME, t("msg.reroll_fd", name=face.path.name, folder=folder)):
                return
            job.out_path = ingame.staging_dir() / f"reroll_{face.path.name}"
            job.replace = face.path
            gen = self._make_generator(overwrite=True)
        else:
            # gleicher Dateiname -> Datei wird ersetzt (wichtig für Spielerlisten-Namen)
            gen = self._make_generator(out_dir=face.path.parent, overwrite=True)
        self._run(gen, [job], "reroll", (self.gmode, self.selected))

    def _update_aging_inputs(self) -> None:
        """'+ Jahre' > 0 graut die feste Alters-Liste aus; FaceDrop-Zeile nur in Galerie → FaceDrop."""
        if not hasattr(self, "ages_entry") or not self.ages_entry.winfo_exists():
            return
        try:
            plus = int(self.v["aging_plus"].get() or 0)
        except (tk.TclError, ValueError):
            plus = 0
        self.ages_entry.state(["disabled"] if plus > 0 else ["!disabled"])
        show = self.gmode == "folder" and self.gal_src == "fd" and self.fd_dir is not None
        if show:
            self.aging_fd_row.pack(fill="x", pady=(4, 0))
            out = self.v["output_dir"].get().strip() or self.cfg.output_dir
            self.undo_btn.state(["!disabled"] if ingame.undo_count(out) else ["disabled"])
        else:
            self.aging_fd_row.pack_forget()

    def _aging_plus(self) -> int:
        try:
            return max(0, int(self.v["aging_plus"].get() or 0))
        except (tk.TclError, ValueError):
            return 0

    def _aging(self, faces: list[GeneratedFace] | None = None, plus: int | None = None,
               replace: bool | None = None, confirm: bool = True) -> None:
        """Alterungs-Set für alle markierten Bilder – feste Alter (20, 25 …) oder '+ Jahre'.
        Mit "Im Spiel ersetzen" ersetzt je Spieler das niedrigste neue Alter das FaceDrop-Bild."""
        faces = faces if faces is not None else self._marked_faces()
        if not faces:
            messagebox.showinfo(APP_NAME, t("msg.select_first"))
            return
        plus = self._aging_plus() if plus is None else plus
        ages = [] if plus else parse_ages(self.v["aging_ages"].get())
        if not plus and not ages:
            messagebox.showinfo(APP_NAME, t("msg.enter_ages"))
            return
        if replace is None:
            replace = bool(self.v["replace_ingame"].get()) and self.gmode == "folder" and self.gal_src == "fd"
        if not self._prepare():
            return
        gen = self._make_generator()
        local = getattr(gen.backend, "supports_img2img", False)
        if replace and not local:
            messagebox.showinfo(APP_NAME, t("msg.replace_local_only"))
            return
        stage = ingame.staging_dir() if replace else None
        jobs: list[Job] = []
        skipped: list[str] = []
        replace_faces = 0
        for k, face in enumerate(faces):
            if not local and face.source == "unknown":
                skipped.append(face.path.name)
                continue
            js = aging_jobs(face, ages, relative=plus)
            if not js:
                if plus or face_age(face) is None:
                    skipped.append(face.path.name)
                continue
            is_fd = facedrop.is_facedrop_path(face.path)
            # aus FaceDrop heraus: weitere Alter in den Speicherort, sonst neben das Ausgangsbild
            target_dir = self._out_dir(face.options.country) if is_fd else face.path.parent
            for j in js:
                j.out_dir = target_dir
            if replace and is_fd:
                low = min(js, key=lambda j: j.age or 0)  # das niedrigste neue Alter kommt ins Spiel
                low.out_path = stage / f"{k:05d}_{face.path.name}"
                low.replace = face.path
                replace_faces += 1
            jobs += js
        if not jobs:
            if skipped:
                messagebox.showinfo(APP_NAME, t("msg.no_age", n=len(skipped), names=self._name_list(skipped)))
            else:
                messagebox.showinfo(APP_NAME, t("msg.enter_ages"))
            return
        if replace and confirm:
            folder = ingame.backup_root(self.cfg.output_dir)
            if not messagebox.askyesno(APP_NAME, t("msg.replace_confirm", n=replace_faces, folder=folder)):
                return
        if not local:
            self.after(300, lambda: self.status.config(text=t("status.aging_online")))
        self.run_skipped = skipped
        self._run(gen, jobs, "aging", retries=1 if len(jobs) > 1 else 0)

    @staticmethod
    def _name_list(names: list[str], limit: int = 12) -> str:
        return "\n".join(names[:limit]) + ("\n…" if len(names) > limit else "")

    def _season(self) -> None:
        """Saison-Knopf: alle Spieler der gewählten Karriere +1 Jahr – im Spiel ersetzt, ohne weitere Rückfragen."""
        if self.gal_src != "fd" or not self.fd_dir:
            return
        faces = list(self.gal["folder"].all_faces)
        if not faces:
            messagebox.showinfo(APP_NAME, t("gal.empty_fd"))
            return
        career = self.v["fd_career"].get()
        folder = ingame.backup_root(self.v["output_dir"].get().strip() or self.cfg.output_dir)
        if not messagebox.askyesno(APP_NAME, t("msg.season_confirm", n=len(faces), career=career, folder=folder)):
            return
        self._aging(faces=faces, plus=1, replace=True, confirm=False)

    def _undo_replace(self) -> None:
        out = self.v["output_dir"].get().strip() or self.cfg.output_dir
        n = ingame.undo_count(out)
        if not n or self._busy():
            return
        if not messagebox.askyesno(APP_NAME, t("msg.undo_confirm", n=n)):
            return
        restored, failed = ingame.undo_last(out)
        self._update_backup_btn()
        msg = t("msg.undo_done", n=len(restored))
        if failed:
            msg += t("msg.replace_failed", n=len(failed), names=self._name_list([p.name for p, _e in failed]))
        messagebox.showinfo(APP_NAME, msg)
        self._update_aging_inputs()
        self.folder_dirty = True
        if self.gmode == "folder":
            self._load_folder()

    def _select_all(self) -> None:
        if not self.faces:
            return
        self.marked = set(range(len(self.faces)))
        self._select(self.selected if self.selected is not None else 0, keep_marks=True)
        self.status.config(text=t("status.marked", n=len(self.faces)))

    def _on_key_select_all(self, event) -> None:
        if not isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Text)) \
                and self._right_key() in ("new", "folder"):
            self._select_all()

    def _load_images(self) -> None:
        """Bereits erstellte Bilder in die Galerie holen (z. B. für ein späteres Alterungs-Set)."""
        paths = filedialog.askopenfilenames(
            title=t("dlg.load_images"), initialdir=self.v["output_dir"].get() or str(Path.home()),
            filetypes=[(t("dlg.png"), "*.png"), (t("dlg.allfiles"), "*.*")])
        if not paths:
            return
        self._read_from_ui()
        self.right_nb.select(self.tab_new)
        self._show_mode("new")
        loaded, failed = [], []
        for p in paths:
            try:
                loaded.append(load_face(p, self.cfg.face))
            except Exception:  # noqa: BLE001 – kein Bild, beschädigt …
                failed.append(Path(p).name)
        if loaded:
            self.faces[:0] = loaded  # geladene Bilder oben einreihen (neueste zuerst)
            self.marked = set()
            self._rebuild_gallery()
            self._select(0)
            self.canvas.yview_moveto(0.0)
            self.status.config(text=t("status.loaded", n=len(loaded)))
        if failed:
            messagebox.showwarning(APP_NAME, t("msg.load_failed", names="\n".join(failed[:20])))

    def _delete(self) -> None:
        """Markierte Bilder nach Rückfrage in den Papierkorb verschieben."""
        faces = self._marked_faces()
        if not faces or self._busy():
            return
        names = "\n".join(f.path.name for f in faces[:8]) + ("\n…" if len(faces) > 8 else "")
        in_game = [f for f in faces if facedrop.is_facedrop_path(f.path)]
        out = self.v["output_dir"].get().strip() or self.cfg.output_dir
        if in_game:
            # aus dem Spiel nehmen: vorher in die Sicherungskopie, 'Letzte Ersetzung rückgängig' holt sie zurück
            ok = messagebox.askyesno(APP_NAME, t("msg.fd_delete_confirm", n=len(faces), names=names,
                                                 folder=ingame.backup_root(out)))
        else:
            ok = messagebox.askyesno(APP_NAME, t("msg.delete_confirm", n=len(faces), names=names))
        if not ok:
            return
        failed = set(trash_files([f.path for f in faces if f not in in_game]))
        if in_game:
            _done, fd_failed = ingame.remove_from_game([f.path for f in in_game], out)
            failed |= {p for p, _e in fd_failed}
            self._update_aging_inputs()
            self._update_backup_btn()
        gone = [f for f in faces if f.path not in failed]
        first = min((self.faces.index(f) for f in gone), default=self.selected or 0)
        gone_paths = {f.path for f in gone}
        for mode, st in self.gal.items():  # aus beiden Galerie-Tabs entfernen
            st.faces = [f for f in st.faces if f.path not in gone_paths]
            st.all_faces = [f for f in st.all_faces if f.path not in gone_paths]
            if mode != self.gmode:
                st.selected, st.marked = (0 if st.faces else None), set()
        self.marked = set()
        for f in gone:
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

    # ---- Sicherungskopie
    def _update_backup_btn(self) -> None:
        if not hasattr(self, "backup_btn") or not self.backup_btn.winfo_exists():
            return
        n, size = ingame.backup_stats(self.v["output_dir"].get().strip() or self.cfg.output_dir)
        if n or size:
            self.backup_btn.configure(text=t("btn.clear_backup", n=n, size=_fmt_size(size)), state="normal")
        else:
            self.backup_btn.configure(text=t("btn.clear_backup0"), state="disabled")

    def _clear_backup(self) -> None:
        if self._busy():
            return
        out = self.v["output_dir"].get().strip() or self.cfg.output_dir
        n, size = ingame.backup_stats(out)
        if not (n or size):
            self._update_backup_btn()
            return
        if not messagebox.askyesno(APP_NAME, t("msg.clear_backup_confirm", n=n, size=_fmt_size(size),
                                               folder=ingame.backup_root(out)), icon="warning"):
            return
        failed = ingame.clear_backup(out)
        self._update_backup_btn()
        self._update_aging_inputs()
        if failed:
            messagebox.showwarning(APP_NAME, t("msg.delete_failed", names="\n".join(p.name for p in failed[:20])))
        else:
            self.status.config(text=t("status.backup_cleared", n=n))

    def _rename(self) -> None:
        """Ausgewähltes Bild umbenennen (z. B. in den Spielernamen)."""
        face = self._current()
        if not face or self._busy() or self._fd_readonly([face]):
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
        for st in self.gal.values():  # dasselbe Bild im anderen Galerie-Tab mit umbenennen
            for f in st.all_faces + st.faces:
                if f is not face and f.path == old:
                    f.path = face.path
        for iid, p in self.players.items():
            if p.image == old:
                p.image = face.path
                if self.tree.exists(iid):
                    self.tree.set(iid, "status", "✓ " + face.path.name)
        self._select(self.selected, keep_marks=True)
        self.status.config(text=t("status.renamed", name=face.path.name))

    def _on_key_delete(self, event) -> None:
        if not isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Text)) \
                and self._right_key() in ("new", "folder"):
            self._delete()

    def _on_key_copy(self, event) -> None:
        if not isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Text)) \
                and self._right_key() in ("new", "folder"):
            self._copy_files()

    def _copy_files(self) -> None:
        """Bilddatei(en) wie im Explorer kopieren – in FM dann Maus aufs Porträt und Strg+V (FaceDrop)."""
        paths = [f.path for f in self._marked_faces() if f.path.exists()]
        if not paths:
            return
        if winclip.copy_files(paths):
            self.status.config(text=t("status.copied_file", n=len(paths)))
        else:
            self.clipboard_clear()
            self.clipboard_append("\n".join(str(p) for p in paths))
            self.status.config(text=t("status.copied_path", n=len(paths)))

    def _fd_readonly(self, faces: list[GeneratedFace]) -> bool:
        """Bilder in FaceDrops Ordnern werden nie verändert – True (mit Hinweis), wenn welche dabei sind."""
        if any(facedrop.is_facedrop_path(f.path) for f in faces):
            messagebox.showinfo(APP_NAME, t("msg.fd_rename"))
            return True
        return False

    def _on_key_rename(self, event) -> None:
        if self._right_key() in ("new", "folder"):
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
        self._mark_existing_images()
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
            self.list_info.config(text=t("list.none"))
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

    def _select_all_players(self) -> None:
        self.tree.selection_set(self.tree.get_children())
        self.tree.focus_set()

    def _export_help(self) -> None:
        """Anleitung FM27 Exporter – eigenes Fenster, damit der Download-Link anklickbar ist."""
        import webbrowser
        win = tk.Toplevel(self)
        win.title(t("btn.export_help"))
        win.configure(background=self.c["bg"])
        win.transient(self)
        win.resizable(False, False)
        frm = ttk.Frame(win, padding=16)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=t("help.export2"), justify="left", wraplength=560).pack(anchor="w")
        link = ttk.Label(frm, text=EXPORTER_TITLE + "\n" + EXPORTER_URL, foreground=self.c["accent"],
                         cursor="hand2", font=("Segoe UI", 9, "underline"), justify="left")
        link.pack(anchor="w", pady=(10, 0))
        link.bind("<Button-1>", lambda e: webbrowser.open(EXPORTER_URL))
        ttk.Label(frm, text=t("help.export_csv"), justify="left", wraplength=560, style="Hint.TLabel").pack(
            anchor="w", pady=(10, 0))
        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text=t("btn.ok"), command=win.destroy).pack(side="right")
        ttk.Button(btns, text=t("btn.open_download"), style="Accent.TButton",
                   command=lambda: webbrowser.open(EXPORTER_URL)).pack(side="right", padx=6)
        theme.dark_title_bar(win, self.cfg.theme == "dark")
        win.update_idletasks()  # mittig über dem Programmfenster
        x = self.winfo_rootx() + (self.winfo_width() - win.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - win.winfo_reqheight()) // 3
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        win.bind("<Escape>", lambda e: win.destroy())
        win.grab_set()

    def _remove_players(self) -> None:
        for iid in self.tree.selection():
            self.tree.delete(iid)
            self.players.pop(iid, None)
        self._update_list_info()

    def _existing_image(self, p: Player, fd_uids: dict[str, Path]) -> Path | None:
        """Gibt es für den Spieler schon ein Bild? Speicherort (Name, UID oder Name_UID, auch im Länder-Unterordner)
        oder – über die UID – ein Bild im Spiel bei FaceDrop."""
        base = Path(self.v["output_dir"].get().strip() or self.cfg.output_dir)
        stems = {safe_filename(x) for x in (p.name, p.uid, f"{p.name}_{p.uid}" if p.uid else "") if x}
        dirs = [base] + [base / c for c in {p.country, p.nation_raw} if c]
        for d in dirs:
            for stem in stems:
                f = d / (stem + ".png")
                if f.is_file():
                    return f
        return fd_uids.get(p.uid) if p.uid else None

    def _mark_existing_images(self) -> None:
        fd_uids: dict[str, Path] = {}
        if self.fd_dir and any(p.uid for p in self.players.values()):
            try:
                fd_uids = {facedrop.player_id(f): f for f in facedrop.all_face_images(self.fd_dir)}
            except OSError:
                fd_uids = {}
        for iid, p in self.players.items():
            if p.image and p.image.exists():
                continue
            found = self._existing_image(p, fd_uids)
            p.image = found
            if found and self.tree.exists(iid):
                self.tree.set(iid, "status", "✓ " + found.name)
                self.tree.item(iid, tags=("ok",))

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
            self._mark_existing_images()  # auch Bilder von früher (anderer Start, FaceDrop) zählen
            iids = [i for i in self.tree.get_children() if not self.players[i].image]
            if not iids:
                messagebox.showinfo(APP_NAME, t("msg.all_have_image"))
                return
        else:
            iids = list(self.tree.get_children())
        if not iids or not self._prepare():
            return

        jobs, base = [], self.cfg.face
        gender = self.cfg.list_gender if self.cfg.list_gender in GENDERS else "Männlich"
        for iid in iids:
            p = self.players[iid]
            opts = copy.deepcopy(base)
            opts.country = p.country or p.nation_raw or base.country
            opts.second_country = p.country2 if p.country2 and p.country2 != opts.country else NO_SECOND
            opts.parent_mode = self.cfg.list_parent_mode
            opts.ethnicity = AUTO  # Herkunft kommt aus der Liste
            opts.gender = gender
            if p.personality:
                opts.personality = p.personality
            jobs.append(Job(options=opts, age=p.age, filename=self._player_filename(p), tag=iid))
            self.tree.set(iid, "status", t("list.waiting"))

        out = Path(self.cfg.output_dir)
        # gleicher Spieler = gleicher Dateiname: altes Bild ersetzen statt 'Name_2.png' anzulegen
        self._run(self._make_generator(out_dir=out, overwrite=True), jobs, "list")
        self.status.config(text=t("status.list_gen", n=len(jobs)) + f" ({opt('gender', gender)})")

    def _open_player_image(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        p = self.players.get(iid) if iid else None
        if p and p.image:
            open_path(p.image)

    # ================================================================== Ende
    def _on_close(self) -> None:
        self.fd_stop.set()
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
    set_language("zh")  # zusätzliche Sprachen (fm27facegen/lang) müssen ebenfalls in der .exe sein
    ok = ok and t("btn.ok") == "确定" and country("Deutschland") == "德国"
    from .icon import make_icon  # Programm-Symbol
    ok = ok and make_icon(32).size == (32, 32)
    set_language("pt-PT")
    ok = ok and t("btn.delete") == "Eliminar" and t("btn.ok") == "OK"
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
        try:  # eigene Kennung: Taskleiste zeigt Symbol + Namen des Generators statt "Python"
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FM27.FaceGenerator")
        except Exception:  # noqa: BLE001
            pass
    App().mainloop()
