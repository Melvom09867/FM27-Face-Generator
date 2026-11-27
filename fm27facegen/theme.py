"""Farbschema der Oberfläche: hell oder dunkel, mit dem Grün aus dem Programm-Symbol als Akzent."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

PALETTES = {
    "light": {
        "bg": "#eef1f3", "panel": "#f6f8f9", "field": "#ffffff", "fg": "#1f2328", "sub": "#5c6470",
        "border": "#c6cdd3", "button": "#e2e7eb", "button_hover": "#d5dce1",
        "accent": "#1f8a43", "accent_hover": "#187236", "accent_fg": "#ffffff",
        "select": "#1f8a43", "mark": "#bfe3cb", "canvas": "#f6f8f9", "preview": "#dde2e6", "trough": "#dde2e6",
        "ok": "#1a7f37", "warn": "#b05a00", "err": "#c62828", "tab": "#e2e7eb",
    },
    "dark": {
        "bg": "#1b1f23", "panel": "#22272c", "field": "#2b3137", "fg": "#e6e9ec", "sub": "#9aa4ae",
        "border": "#3a434b", "button": "#313840", "button_hover": "#3b444d",
        "accent": "#2fb35a", "accent_hover": "#279a4d", "accent_fg": "#0d1a12",
        "select": "#2fb35a", "mark": "#24452f", "canvas": "#1f2428", "preview": "#2b3137", "trough": "#2b3137",
        "ok": "#56d37c", "warn": "#f0a24a", "err": "#ff6b6b", "tab": "#2b3137",
    },
}

current: dict = PALETTES["light"]


def colors() -> dict:
    return current


def apply(root: tk.Tk, mode: str = "light") -> dict:
    """Stellt alle ttk-Stile auf das gewählte Schema um und gibt die Farben zurück."""
    global current
    c = current = PALETTES.get(mode, PALETTES["light"])
    st = ttk.Style(root)
    if "clam" in st.theme_names():
        st.theme_use("clam")  # nur 'clam' lässt sich unter Windows vollständig einfärben
    base_font = ("Segoe UI", 9) if sys.platform.startswith("win") else None
    st.configure(".", background=c["bg"], foreground=c["fg"], fieldbackground=c["field"], bordercolor=c["border"],
                 lightcolor=c["bg"], darkcolor=c["bg"], troughcolor=c["trough"], focuscolor=c["accent"],
                 selectbackground=c["accent"], selectforeground=c["accent_fg"], insertcolor=c["fg"],
                 arrowcolor=c["fg"], **({"font": base_font} if base_font else {}))
    st.configure("TFrame", background=c["bg"])
    st.configure("TLabel", background=c["bg"], foreground=c["fg"])
    st.configure("Hint.TLabel", background=c["bg"], foreground=c["sub"])
    st.configure("Head.TLabel", background=c["bg"], foreground=c["accent"], font=("Segoe UI", 10, "bold"))
    st.configure("TNotebook", background=c["bg"], bordercolor=c["border"], tabmargins=(2, 4, 2, 0))
    st.configure("TNotebook.Tab", background=c["tab"], foreground=c["sub"], padding=(10, 4), bordercolor=c["border"])
    st.map("TNotebook.Tab", background=[("selected", c["bg"])], foreground=[("selected", c["accent"])],
           lightcolor=[("selected", c["accent"])])
    st.configure("TButton", background=c["button"], foreground=c["fg"], bordercolor=c["border"], padding=(8, 3))
    st.map("TButton", background=[("disabled", c["bg"]), ("active", c["button_hover"])],
           foreground=[("disabled", c["sub"])])
    for name, font, pad in (("Accent.TButton", None, (10, 3)), ("Big.TButton", ("Segoe UI", 11, "bold"), 8)):
        st.configure(name, background=c["accent"], foreground=c["accent_fg"], bordercolor=c["accent"],
                     padding=pad, **({"font": font} if font else {}))
        st.map(name, background=[("disabled", c["button"]), ("active", c["accent_hover"])],
               foreground=[("disabled", c["sub"])])
    # normaler Knopf mit grünem Rahmen (fällt auf, ohne so laut zu sein wie ein grüner Knopf)
    st.configure("Outline.TButton", background=c["button"], foreground=c["fg"], bordercolor=c["accent"],
                 lightcolor=c["accent"], darkcolor=c["accent"], borderwidth=2, padding=(8, 3))
    st.map("Outline.TButton", background=[("disabled", c["bg"]), ("active", c["button_hover"])],
           foreground=[("disabled", c["sub"])], bordercolor=[("!disabled", c["accent"])],
           lightcolor=[("!disabled", c["accent"])], darkcolor=[("!disabled", c["accent"])])
    for name in ("TEntry", "TCombobox", "TSpinbox"):
        st.configure(name, fieldbackground=c["field"], foreground=c["fg"], background=c["button"],
                     bordercolor=c["border"], arrowcolor=c["fg"], insertcolor=c["fg"])
        st.map(name, fieldbackground=[("readonly", c["field"]), ("disabled", c["bg"])],
               foreground=[("disabled", c["sub"])], bordercolor=[("focus", c["accent"])],
               selectbackground=[("readonly", c["field"])], selectforeground=[("readonly", c["fg"])])
    for name in ("TCheckbutton", "TRadiobutton", "Wrap.TCheckbutton"):
        st.configure(name, background=c["bg"], foreground=c["fg"], indicatorbackground=c["field"],
                     indicatorforeground=c["accent_fg"], bordercolor=c["border"])
        st.map(name, indicatorbackground=[("selected", c["accent"]), ("active", c["button_hover"])],
               background=[("active", c["bg"])])
    st.configure("Wrap.TCheckbutton", wraplength=360)
    st.configure("Horizontal.TProgressbar", background=c["accent"], troughcolor=c["trough"],
                 bordercolor=c["border"], lightcolor=c["accent"], darkcolor=c["accent"])
    st.configure("Horizontal.TScale", background=c["button"], troughcolor=c["trough"], bordercolor=c["border"])
    st.configure("Treeview", background=c["field"], fieldbackground=c["field"], foreground=c["fg"],
                 bordercolor=c["border"])
    st.map("Treeview", background=[("selected", c["accent"])], foreground=[("selected", c["accent_fg"])])
    st.configure("Treeview.Heading", background=c["button"], foreground=c["fg"], bordercolor=c["border"])
    for name in ("TScrollbar", "Vertical.TScrollbar", "Horizontal.TScrollbar"):
        st.configure(name, background=c["button"], troughcolor=c["panel"], bordercolor=c["border"],
                     arrowcolor=c["fg"], lightcolor=c["button"], darkcolor=c["button"])
        st.map(name, background=[("active", c["button_hover"])])
    st.configure("TSeparator", background=c["border"])
    # Aufklapplisten der Comboboxen (klassische Tk-Listbox)
    root.option_add("*TCombobox*Listbox.background", c["field"])
    root.option_add("*TCombobox*Listbox.foreground", c["fg"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", c["accent_fg"])
    root.configure(background=c["bg"])
    dark_title_bar(root, mode == "dark")
    return c


def dark_title_bar(root: tk.Tk, dark: bool) -> None:
    """Windows 10/11: Titelleiste passend dunkel/hell."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (neu/alt)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
    except Exception:  # noqa: BLE001
        pass
