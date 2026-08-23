"""Convert text to SVG outline paths using the brand font.

Logos must never depend on a font being installed on the viewer's machine, and
SVG renderers do not shape Arabic. So we shape with arabic_reshaper + bidi, then
extract real glyph outlines from the TTF/WOFF and emit pure <path> data.
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import arabic_reshaper
from bidi.algorithm import get_display

HERE = os.path.dirname(os.path.abspath(__file__))
# Arabic wordmark -> Droid Arabic Kufi (the product's official face)
# Latin  wordmark -> Montserrat (geometric, pairs cleanly with Kufi)
FONTS = {
    "ar_regular": os.path.join(HERE, "..", "static", "fonts", "DroidKufi-Regular.woff"),
    "ar_bold":    os.path.join(HERE, "..", "static", "fonts", "DroidKufi-Bold.woff"),
    "la_regular": os.path.join(HERE, "_fonts", "Montserrat-SemiBold.ttf"),
    "la_bold":    os.path.join(HERE, "_fonts", "Montserrat-ExtraBold.ttf"),
}
_cache = {}


def _font(key):
    if key not in _cache:
        f = TTFont(FONTS[key])
        _cache[key] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)
    return _cache[key]


def _pick(text, weight):
    script = "ar" if is_arabic(text) else "la"
    return f"{script}_{weight}"


def is_arabic(s):
    return any("\u0600" <= c <= "\u06FF" or "\uFB50" <= c <= "\uFEFF" for c in s)


def shape(text):
    """Arabic: reshape to presentation forms + apply bidi. Latin: unchanged."""
    if not is_arabic(text):
        return text
    return get_display(arabic_reshaper.reshape(text))


def text_to_path(text, size=32, weight="bold", letter_spacing=0.0):
    """Return (svg_group, advance_width), baseline at y=0, growing to the right.

    Every glyph is drawn from a font that genuinely contains it; unknown
    characters advance a space instead of disappearing.
    """
    shaped = shape(text)
    parts, x = [], 0.0
    prev_key = prev_gname = None
    for ch in shaped:
        o = ord(ch)
        arabic = (0x0600 <= o <= 0x06FF) or (0xFB50 <= o <= 0xFEFF)
        order = ("ar", "la") if arabic else ("la", "ar")
        placed = False
        for scr in order:
            key = f"{scr}_{weight}"
            if key not in FONTS:
                key = f"{scr}_regular"
            font, gs, cmap, upem = _font(key)
            gname = cmap.get(o)
            if gname is None:
                continue
            scale = size / upem
            kern = font["kern"].kernTables[0].kernTable if "kern" in font else None
            if kern and prev_gname and prev_key == key:
                x += kern.get((prev_gname, gname), 0) * scale
            glyph = gs[gname]
            pen = SVGPathPen(gs)
            glyph.draw(pen)
            d = pen.getCommands()
            if d:
                parts.append(
                    f'<g transform="translate({x:.3f},0) scale({scale:.6f},{-scale:.6f})">'
                    f'<path d="{d}"/></g>')
            x += glyph.width * scale + letter_spacing
            prev_key, prev_gname = key, gname
            placed = True
            break
        if not placed:
            x += size * 0.28          # unknown glyph -> blank space, never silent loss
            prev_key = prev_gname = None
    return "".join(parts), x


def text_svg_group(text, size=32, weight="bold", fill="#fff", x=0, y=0,
                   anchor="start", letter_spacing=0.0, opacity=None):
    """A positioned <g> containing outlined text."""
    group, w = text_to_path(text, size, weight, letter_spacing)
    dx = {"start": 0, "middle": -w / 2, "end": -w}[anchor]
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return (f'<g fill="{fill}"{op} transform="translate({x+dx:.2f},{y:.2f})">{group}</g>', w)


def measure(text, size=32, weight="bold", letter_spacing=0.0):
    return text_to_path(text, size, weight, letter_spacing)[1]
