"""Nachbearbeitung: Gesicht finden, zentriert zuschneiden, optional freistellen, auf 250x250 skalieren."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2
except Exception:  # noqa: BLE001  – läuft auch ohne OpenCV (dann ohne Gesichtserkennung)
    cv2 = None

OUTPUT_SIZE = 250


@dataclass
class ProcessOptions:
    size: int = OUTPUT_SIZE
    zoom: float = 1.6           # Bildbreite = Gesichtsbreite * zoom (1.5 = FM-Cut-out-Stil, größer = mehr Schultern)
    face_y: float = 0.56        # vertikale Position der Gesichtsmitte (0 = oben, 1 = unten); 0.59 = Haare reichen bis oben
    transparent: bool = False
    crop_bottom: float = 0.0    # Anteil unten abschneiden (z. B. Wasserzeichen)
    sharpen: bool = True


_cascade = None


def _get_cascade():
    global _cascade
    if _cascade is None:
        if cv2 is None or not hasattr(cv2, "CascadeClassifier"):
            _cascade = False
            return None
        path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        c = cv2.CascadeClassifier(str(path))
        _cascade = c if not c.empty() else False
    return _cascade or None


def detect_face(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Größtes Gesicht als (x, y, w, h) oder None."""
    cascade = _get_cascade()
    if cascade is None:
        return None
    gray = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)
    min_side = max(40, min(gray.shape) // 8)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(min_side, min_side))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return int(x), int(y), int(w), int(h)


def _border_color(arr: np.ndarray) -> np.ndarray:
    band = np.concatenate([arr[:4].reshape(-1, 3), arr[:, :4].reshape(-1, 3), arr[:, -4:].reshape(-1, 3)])
    return np.median(band, axis=0)


def remove_background(img: Image.Image, face: tuple[int, int, int, int] | None) -> Image.Image:
    """Stellt die Person frei. Ergebnis: RGBA.

    Bevorzugt das KI-Freistellmodell (segment.py); ohne Modell einfache Farb-Methode als Notlösung.
    """
    from .segment import person_mask
    mask = person_mask(img)
    if mask is not None:
        alpha = _clean_alpha(img, np.asarray(mask).astype(np.float32) / 255.0, face)
        out = Image.fromarray(defringe(np.asarray(img.convert("RGB")), alpha), "RGB").convert("RGBA")
        out.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
        return out
    return _remove_background_simple(img, face)


def defringe(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Entfernt den grauen Saum: halbtransparente Randpixel (Haarspitzen, Schultern) tragen noch die Farbe des
    alten Hintergrunds. Sie bekommen die Farbe der benachbarten Person (Haar/Haut). Auch unsichtbare Pixel werden
    so eingefärbt, damit beim Verkleinern kein Grau von außen in die Kante läuft."""
    if cv2 is None:
        return rgb
    solid = (alpha > 0.92).astype(np.float32)
    if solid.sum() < 100:
        return rgb
    src = rgb.astype(np.float32)
    fill = np.zeros_like(src)
    have = np.zeros(alpha.shape, np.float32)
    for k in (3, 7, 15, 31, 63, 127):  # von nah nach fern: nächstgelegene Personenfarbe
        w = cv2.GaussianBlur(solid, (k, k), 0)
        c = cv2.GaussianBlur(src * solid[..., None], (k, k), 0)
        new = (w > 1e-3) & (have == 0)
        fill[new] = c[new] / w[new, None]
        have[new] = 1
    fill[have == 0] = src[have == 0]
    out = np.where((alpha > 0.92)[..., None], src, fill)
    return np.clip(out, 0, 255).astype(np.uint8)


def _bg_distance(rgb: np.ndarray, bg_sure: np.ndarray | None = None) -> np.ndarray:
    """Farbabstand (Lab) jedes Pixels zur Hintergrundfarbe.

    Die Hintergrundfarben werden aus sicherem Hintergrund gelernt (``bg_sure``, z. B. vom KI-Modell),
    sonst aus oberem Rand und oberen Seitenrändern.
    """
    h = rgb.shape[0]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    if bg_sure is not None and bg_sure.sum() > 500:
        band = lab[bg_sure]
        if len(band) > 20000:
            band = band[np.random.default_rng(0).choice(len(band), 20000, replace=False)]
    else:
        side_h = int(h * 0.5)
        band = np.concatenate([lab[:6].reshape(-1, 3), lab[:side_h, :6].reshape(-1, 3), lab[:side_h, -6:].reshape(-1, 3)])
    _, _, centers = cv2.kmeans(band.astype(np.float32), 6, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
                               2, cv2.KMEANS_PP_CENTERS)
    return np.min(np.stack([np.linalg.norm(lab - c, axis=2) for c in centers]), axis=0)


def _clean_alpha(img: Image.Image, alpha: np.ndarray, face) -> np.ndarray:
    """Entfernt Hintergrundreste (z. B. zwischen Haaren oder am oberen Rand), die das Modell stehen lässt."""
    if cv2 is None:
        return alpha
    rgb = np.asarray(img.convert("RGB"))
    dist = _bg_distance(rgb)
    keep = np.clip((dist - 7.0) / 9.0, 0.0, 1.0)  # hintergrundfarbig -> 0, deutlich anders -> 1
    if face is not None:  # im Gesicht nie etwas wegnehmen
        fx, fy, fw, fh = face
        keep[max(fy, 0): fy + fh, max(fx, 0): fx + fw] = 1.0
    # Nur an unsicheren Stellen eingreifen: sicher erkannte Person (z. B. Glanzlichter im Haar) bleibt
    alpha = np.where(alpha >= 0.9, alpha, alpha * keep)
    # Neben Haaren und Ohren (oberhalb des Kinns, außerhalb des Gesichts) hält das Modell manchmal ganze Flecken
    # Hintergrund für "Person" – Pixel fast genau in Hintergrundfarbe dort immer entfernen. Unterhalb des Kinns
    # nicht (weißes Trikot kann dem Hintergrund ähneln).
    if face is not None:
        fx, fy, fw, fh = face
        h, w = alpha.shape
        region = np.zeros((h, w), bool)
        region[: min(h, fy + int(fh * 1.02)), :] = True
        mx, my = int(fw * 0.04), int(fh * 0.04)
        region[max(fy + my, 0): fy + fh - my, max(fx + mx, 0): fx + fw - mx] = False
        strict = np.clip((dist - 10.0) / 8.0, 0.0, 1.0)
        alpha = np.where(region, alpha * strict, alpha)
    # kleine abgetrennte Inseln entfernen, Kanten leicht glätten
    binary = (alpha > 0.5).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary)
    if n > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        small = [i + 1 for i, a in enumerate(areas) if a < 0.02 * areas.max()]
        if small:
            alpha[np.isin(labels, small)] = 0.0
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    # Kante minimal enger: kaum sichtbare Reste am Rand (der helle Schimmer) verschwinden ganz
    return np.clip((alpha - 0.06) / 0.9, 0.0, 1.0)


def _remove_background_simple(img: Image.Image, face: tuple[int, int, int, int] | None) -> Image.Image:
    """Notlösung für einfarbige Hintergründe (ohne KI-Modell)."""
    rgb = np.asarray(img.convert("RGB"))
    h, w = rgb.shape[:2]
    if cv2 is None:
        return img.convert("RGBA")

    # Hintergrund-Modell: mehrere Farbcluster aus dem Bildrand (deckt Verläufe/Vignetten ab)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    side_h = int(h * 0.55)  # nur obere Seitenränder – unten sind oft schon die Schultern
    band = np.concatenate([lab[:6].reshape(-1, 3), lab[:side_h, :6].reshape(-1, 3),
                           lab[:side_h, -6:].reshape(-1, 3)])
    k = 6
    _, _, centers = cv2.kmeans(band, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
                               2, cv2.KMEANS_PP_CENTERS)
    dist = np.min(np.stack([np.linalg.norm(lab - c, axis=2) for c in centers]), axis=0)
    similar = (dist < 14).astype(np.uint8)

    # nur Bereiche, die mit dem Rand verbunden sind, gelten sicher als Hintergrund
    n, labels = cv2.connectedComponents(similar)
    edge_labels = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
    edge_labels.discard(0)
    sure_bg = np.isin(labels, list(edge_labels)) & (similar == 1)

    mask = np.full((h, w), cv2.GC_PR_FGD, np.uint8)
    mask[dist < 28] = cv2.GC_PR_BGD
    mask[sure_bg] = cv2.GC_BGD
    if face is not None:
        fx, fy, fw, fh = face
        mask[fy + fh // 6: fy + fh - fh // 8, fx + fw // 6: fx + fw - fw // 6] = cv2.GC_FGD
    try:
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(rgb, mask, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        pass
    alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    # größte zusammenhängende Fläche behalten, Löcher schließen, Kanten weich
    n, labels, stats, _ = cv2.connectedComponentsWithStats(alpha)
    if n > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = [i + 1 for i, a in enumerate(areas) if a >= 0.15 * areas.max()]
        alpha = np.where(np.isin(labels, keep), 255, 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel, iterations=2)
    alpha = cv2.GaussianBlur(alpha, (5, 5), 0)

    out = Image.fromarray(rgb).convert("RGBA")
    out.putalpha(Image.fromarray(alpha))
    return out


def crop_to_face(img: Image.Image, face: tuple[int, int, int, int] | None, opts: ProcessOptions) -> Image.Image:
    w, h = img.size
    if face is None:
        side = min(w, h)
        left, top = (w - side) // 2, max(0, (h - side) // 2 - int(side * 0.03))
        return img.crop((left, top, left + side, top + side))

    fx, fy, fw, fh = face
    side = int(round(max(fw, fh) * opts.zoom))
    cx = fx + fw / 2
    cy = fy + fh / 2
    transparent = img.mode == "RGBA"
    if transparent:
        # Freigestellt: seitlich darf transparent aufgefüllt werden -> Gesicht bleibt mittig.
        # Oben nicht (sonst wären angeschnittene Haare mit leerem Streifen darüber zu sehen),
        # unten nicht (sonst würde der Körper mitten im Bild abbrechen).
        side = max(32, min(side, h))
        left = int(round(cx - side / 2))
        top = min(max(int(round(cy - side * opts.face_y)), 0), h - side)
    else:
        side = max(32, min(side, w, h))  # nie größer als das Bild -> kein grauer Rand
        left = int(round(cx - side / 2))
        top = int(round(cy - side * opts.face_y))
        left = min(max(left, 0), w - side)
        top = min(max(top, 0), h - side)

    if img.mode == "RGBA":
        fill = (0, 0, 0, 0)
    else:
        fill = tuple(int(v) for v in _border_color(np.asarray(img.convert("RGB"))))
    canvas = Image.new(img.mode, (side, side), fill)
    canvas.paste(img.crop((max(left, 0), max(top, 0), min(left + side, w), min(top + side, h))),
                 (max(-left, 0), max(-top, 0)))
    return canvas


def process(img: Image.Image, opts: ProcessOptions) -> Image.Image:
    """Komplette Nachbearbeitung -> fertiges FM-Facepack-Bild."""
    img = img.convert("RGB")
    if opts.crop_bottom > 0:
        w, h = img.size
        img = img.crop((0, 0, w, h - int(h * opts.crop_bottom)))
    face = detect_face(img)
    if opts.transparent:
        img = remove_background(img, face)
    out = crop_to_face(img, face, opts)
    out = out.resize((opts.size, opts.size), Image.Resampling.LANCZOS)
    if opts.sharpen:
        if out.mode == "RGBA":
            # nur die Farben schärfen – geschärfte Transparenz erzeugt einen dunklen/grauen Rand
            a = out.getchannel("A")
            out = out.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
            out.putalpha(a)
        else:
            out = out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
            out = ImageEnhance.Contrast(out).enhance(1.03)
    return out


def save_png(img: Image.Image, path: Path, info: dict[str, str] | None = None) -> Path:
    """Speichert als PNG; ``info`` wird als unsichtbarer Text-Block eingebettet (FM/FaceDrop ignorieren ihn)."""
    from PIL.PngImagePlugin import PngInfo
    path.parent.mkdir(parents=True, exist_ok=True)
    pnginfo = None
    if info:
        pnginfo = PngInfo()
        for key, value in info.items():
            pnginfo.add_itxt(key, value)
    img.save(path, format="PNG", optimize=True, pnginfo=pnginfo)
    return path
