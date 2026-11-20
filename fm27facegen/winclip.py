"""Bilddateien in die Windows-Zwischenablage legen – wie Strg+C im Explorer (dann in FM per FaceDrop Strg+V)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

CF_HDROP = 15
GMEM_MOVEABLE = 0x0002
DROPEFFECT_COPY = 1


def dropfiles_bytes(paths: list[str | Path]) -> bytes:
    """DROPFILES-Struktur + Dateiliste (UTF-16, jede Datei mit \\0 beendet, Ende mit \\0\\0)."""
    names = "".join(str(Path(p).resolve()) + "\0" for p in paths) + "\0"
    # DWORD pFiles, POINT pt (x, y), BOOL fNC, BOOL fWide
    return struct.pack("<IiiII", 20, 0, 0, 0, 1) + names.encode("utf-16-le")


def copy_files(paths: list[str | Path]) -> bool:
    """True, wenn die Dateien in der Zwischenablage liegen (nur unter Windows möglich)."""
    if not paths or not sys.platform.startswith("win"):
        return False
    import ctypes
    from ctypes import wintypes

    k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
    k32.GlobalAlloc.restype = wintypes.HGLOBAL
    k32.GlobalAlloc.argtypes = (wintypes.UINT, ctypes.c_size_t)
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = (wintypes.HGLOBAL,)
    k32.GlobalUnlock.argtypes = (wintypes.HGLOBAL,)
    k32.GlobalFree.argtypes = (wintypes.HGLOBAL,)
    u32.OpenClipboard.argtypes = (wintypes.HWND,)
    u32.SetClipboardData.restype = wintypes.HANDLE
    u32.SetClipboardData.argtypes = (wintypes.UINT, wintypes.HANDLE)
    u32.RegisterClipboardFormatW.argtypes = (wintypes.LPCWSTR,)
    u32.RegisterClipboardFormatW.restype = wintypes.UINT

    def global_mem(data: bytes):
        h = k32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h:
            return None
        ptr = k32.GlobalLock(h)
        if not ptr:
            k32.GlobalFree(h)
            return None
        ctypes.memmove(ptr, data, len(data))
        k32.GlobalUnlock(h)
        return h

    h_drop = global_mem(dropfiles_bytes(paths))
    if not h_drop:
        return False
    if not u32.OpenClipboard(None):
        k32.GlobalFree(h_drop)
        return False
    try:
        u32.EmptyClipboard()
        if not u32.SetClipboardData(CF_HDROP, h_drop):
            k32.GlobalFree(h_drop)
            return False
        fmt = u32.RegisterClipboardFormatW("Preferred DropEffect")
        h_eff = global_mem(struct.pack("<I", DROPEFFECT_COPY))
        if fmt and h_eff and not u32.SetClipboardData(fmt, h_eff):
            k32.GlobalFree(h_eff)
        return True
    finally:
        u32.CloseClipboard()
