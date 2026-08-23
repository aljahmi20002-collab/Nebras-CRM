#!/usr/bin/env python3
"""NebrasCRM visual identity generator.

Concept — نِبراس means "lamp / beacon of light": the source that guides.
The mark is a geometric flame (the light) resting inside a rounded tile (the lamp),
with the inner core rendered in warm gold against a deep indigo night. It reads as
a flame, an upward arrow (growth), and a guiding beacon — all fitting for a CRM.

Everything is generated from this single file so the identity stays consistent.
"""
import os, json, shutil
import cairosvg
from PIL import Image
import textpath as TP

HERE = os.path.dirname(os.path.abspath(__file__))
def P(*a): return os.path.join(HERE, *a)

for d in ("logo", "favicon", "social", "assets"):
    os.makedirs(P(d), exist_ok=True)

# ---------------------------------------------------------------- palette
BRAND = {
    "indigo":  "#2B4ACB",   # الليل — the lamp body
    "indigo2": "#4F7CFF",
    "violet":  "#7C3AED",
    "cyan":    "#06B6D4",
    "gold":    "#FFC53D",   # النور — the light
    "gold2":   "#FF9F1C",
    "ink":     "#0F1420",
    "paper":   "#F7F9FC",
    "slate":   "#5A6B85",
    "ok":      "#15803D",
    "warn":    "#B45309",
    "danger":  "#DC2626",
}

# ---------------------------------------------------------------- geometry
# Flame drawn inside a 64×64 tile. Tip at top, teardrop body, gentle shoulders.
# Asymmetric silhouette: the tip leans and curls like a real flame, with a
# shoulder notch on the left — this is what separates a flame from a teardrop.
FLAME_OUTER = ("M33.4 8.2 "
               "C 33.9 15.6 40.1 18.6 43.6 24.4 "
               "C 46.9 29.9 47.0 36.0 45.1 40.7 "
               "C 42.6 47.0 37.6 51.4 31.6 51.4 "
               "C 24.0 51.4 17.4 45.6 17.0 37.4 "
               "C 16.7 31.3 20.0 27.6 22.6 24.9 "
               "C 24.2 27.4 25.9 28.6 27.4 28.8 "
               "C 26.2 22.0 28.6 14.2 33.4 8.2 Z")
# Inner core — the burning heart, offset slightly down.
FLAME_CORE = ("M32.6 26.0 "
              "C 33.0 30.4 37.2 32.6 38.6 36.6 "
              "C 39.8 40.1 38.4 44.0 35.3 45.9 "
              "C 32.0 47.9 27.4 47.0 25.3 43.9 "
              "C 23.2 40.8 23.8 37.2 25.6 34.6 "
              "C 26.6 36.0 27.6 36.6 28.5 36.7 "
              "C 28.0 32.6 29.8 28.9 32.6 26.0 Z")
# Beacon rays (full logo only)
RAYS = [(32, 3.2, 32, 7.2), (12.5, 12.5, 15.4, 15.4), (51.5, 12.5, 48.6, 15.4),
        (4.0, 33.5, 8.0, 33.5), (60.0, 33.5, 56.0, 33.5)]


def defs(idp=""):
    """Shared gradient defs; idp namespaces ids so multiple SVGs can inline safely."""
    return f'''<defs>
    <linearGradient id="{idp}tile" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BRAND['indigo2']}"/>
      <stop offset="0.52" stop-color="{BRAND['indigo']}"/>
      <stop offset="1" stop-color="{BRAND['violet']}"/>
    </linearGradient>
    <linearGradient id="{idp}flame" x1="0.5" y1="0" x2="0.5" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/>
      <stop offset="0.55" stop-color="#FFF3D6"/>
      <stop offset="1" stop-color="{BRAND['gold']}"/>
    </linearGradient>
    <linearGradient id="{idp}core" x1="0.5" y1="0" x2="0.5" y2="1">
      <stop offset="0" stop-color="{BRAND['gold']}"/>
      <stop offset="1" stop-color="{BRAND['gold2']}"/>
    </linearGradient>
    <radialGradient id="{idp}glow" cx="0.5" cy="0.62" r="0.55">
      <stop offset="0" stop-color="{BRAND['gold']}" stop-opacity="0.55"/>
      <stop offset="1" stop-color="{BRAND['gold']}" stop-opacity="0"/>
    </radialGradient>
  </defs>'''


def mark(size=64, idp="", tile=True, radius=14.5, rays=False, glow=True):
    """The icon mark on its own."""
    body = []
    if tile:
        body.append(f'<rect width="64" height="64" rx="{radius}" fill="url(#{idp}tile)"/>')
        body.append(f'<rect x="0.6" y="0.6" width="62.8" height="62.8" rx="{radius-0.6}" '
                    f'fill="none" stroke="#FFFFFF" stroke-opacity="0.16" stroke-width="1.2"/>')
    if glow:
        body.append(f'<ellipse cx="31.5" cy="38.5" rx="19" ry="19" fill="url(#{idp}glow)"/>')
    if rays:
        for x1, y1, x2, y2 in RAYS:
            body.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{BRAND["gold"]}" '
                        f'stroke-width="2.6" stroke-linecap="round" stroke-opacity="0.9"/>')
    body.append(f'<path d="{FLAME_OUTER}" fill="url(#{idp}flame)"/>')
    body.append(f'<path d="{FLAME_CORE}" fill="url(#{idp}core)"/>')
    return "\n  ".join(body)


def svg_mark(size=64, rays=False, tile=True, radius=14.5):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}"
     role="img" aria-label="NebrasCRM">
  <title>NebrasCRM — نبراس</title>
  {defs()}
  {mark(idp="", tile=tile, radius=radius, rays=rays)}
</svg>
'''


def svg_mono(color="#FFFFFF"):
    """Single-colour mark for stamps, engraving, one-colour print."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64"
     role="img" aria-label="NebrasCRM">
  <path d="{FLAME_OUTER}" fill="{color}"/>
  <path d="{FLAME_CORE}" fill="{color}" fill-opacity="0.42"/>
</svg>
'''


def svg_lockup(lang="en", theme="dark", w=360):
    """Mark + wordmark, with all text converted to outlines (font-independent)."""
    txt = "#EAF0FF" if theme == "dark" else "#101828"
    sub = "#93A4C4" if theme == "dark" else "#5A6B85"
    if lang == "ar":
        name, tag, fs, ts = "نبراس سي آر إم", "منصة إدارة علاقات العملاء", 27, 12
    else:
        name, tag, fs, ts = "NebrasCRM", "Customer Relationship Platform", 27, 11

    nw = TP.measure(name, fs, "bold")
    tw = TP.measure(tag, ts, "regular")
    text_w = max(nw, tw)
    gap, mark_s, pad = 18, 64, 10
    total = mark_s + gap + text_w + pad * 2
    H = 76

    if lang == "ar":
        # RTL: mark sits on the right, text flows leftwards from it
        mx = total - mark_s - pad
        tx = mx - gap
        anchor = "end"
    else:
        mx = pad
        tx = mx + mark_s + gap
        anchor = "start"

    g_name, _ = TP.text_svg_group(name, fs, "bold", txt, tx, 40, anchor)
    g_tag, _ = TP.text_svg_group(tag, ts, "regular", sub, tx, 59, anchor)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total:.0f} {H}"
     width="{w}" height="{w*H/total:.0f}" role="img" aria-label="NebrasCRM">
  <title>NebrasCRM \u2014 \u0646\u0650\u0628\u0631\u0627\u0633</title>
  {defs("lk")}
  <g transform="translate({mx:.1f},6)">
    {mark(idp="lk")}
  </g>
  {g_name}
  {g_tag}
</svg>
'''


# ---------------------------------------------------------------- write SVGs
files = {
    "logo/nebras-mark.svg":            svg_mark(),
    "logo/nebras-mark-rays.svg":       svg_mark(rays=True),
    "logo/nebras-mark-bare.svg":       svg_mark(tile=False),
    "logo/nebras-mark-mono-white.svg": svg_mono("#FFFFFF"),
    "logo/nebras-mark-mono-ink.svg":   svg_mono(BRAND["ink"]),
    "logo/nebras-lockup-en-dark.svg":  svg_lockup("en", "dark"),
    "logo/nebras-lockup-en-light.svg": svg_lockup("en", "light"),
    "logo/nebras-lockup-ar-dark.svg":  svg_lockup("ar", "dark"),
    "logo/nebras-lockup-ar-light.svg": svg_lockup("ar", "light"),
    "favicon/favicon.svg":             svg_mark(radius=13),
}
for path, content in files.items():
    open(P(path), "w", encoding="utf-8").write(content)

# ---------------------------------------------------------------- rasterise
def png(src, out, size, pad=0, bg=None):
    tmp = P("assets", "_t.png")
    cairosvg.svg2png(url=P(src), write_to=tmp, output_width=size, output_height=size)
    im = Image.open(tmp).convert("RGBA")
    if pad or bg:
        canvas = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
        inner = size - pad * 2
        im = im.resize((inner, inner), Image.LANCZOS)
        canvas.paste(im, (pad, pad), im)
        im = canvas
    im.save(P(out))
    os.remove(tmp)
    return im


ICONS = [16, 32, 48, 64, 96, 128, 152, 167, 180, 192, 256, 384, 512, 1024]
for s in ICONS:
    png("favicon/favicon.svg", f"favicon/icon-{s}.png", s)

# apple touch icon: opaque background, no transparency
png("favicon/favicon.svg", "favicon/apple-touch-icon.png", 180)
# maskable: 20% safe padding so Android's mask never clips the flame
png("logo/nebras-mark-bare.svg", "favicon/maskable-512.png", 512, pad=74,
    bg=(43, 74, 203, 255))

# multi-resolution .ico
ico = [Image.open(P(f"favicon/icon-{s}.png")).convert("RGBA") for s in (16, 32, 48, 64)]
ico[0].save(P("favicon/favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

# ---------------------------------------------------------------- social card
OG = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  {defs("og")}
  <defs>
    <linearGradient id="ogbg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0F1420"/><stop offset="0.55" stop-color="#141C33"/>
      <stop offset="1" stop-color="#1A1533"/>
    </linearGradient>
    <radialGradient id="og1" cx="0.15" cy="0.1" r="0.6">
      <stop offset="0" stop-color="{BRAND['indigo2']}" stop-opacity="0.5"/>
      <stop offset="1" stop-color="{BRAND['indigo2']}" stop-opacity="0"/></radialGradient>
    <radialGradient id="og2" cx="0.88" cy="0.85" r="0.6">
      <stop offset="0" stop-color="{BRAND['violet']}" stop-opacity="0.45"/>
      <stop offset="1" stop-color="{BRAND['violet']}" stop-opacity="0"/></radialGradient>
    <radialGradient id="og3" cx="0.5" cy="0.35" r="0.42">
      <stop offset="0" stop-color="{BRAND['gold']}" stop-opacity="0.22"/>
      <stop offset="1" stop-color="{BRAND['gold']}" stop-opacity="0"/></radialGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#ogbg)"/>
  <rect width="1200" height="630" fill="url(#og1)"/>
  <rect width="1200" height="630" fill="url(#og2)"/>
  <rect width="1200" height="630" fill="url(#og3)"/>
  <g opacity="0.10" stroke="#8FA6D8" stroke-width="1">
    {''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="630"/>' for x in range(0, 1201, 60))}
    {''.join(f'<line x1="0" y1="{y}" x2="1200" y2="{y}"/>' for y in range(0, 631, 60))}
  </g>
  <g transform="translate(500,96) scale(3.1)">{mark(idp="og")}</g>
  {TP.text_svg_group("NebrasCRM", 74, "bold", "#FFFFFF", 600, 424, "middle")[0]}
  {TP.text_svg_group("نبراس سي آر إم", 44, "bold", BRAND['gold'], 600, 494, "middle")[0]}
  {TP.text_svg_group("منصة إدارة علاقات العملاء للمؤسسات", 24, "regular", "#93A4C4", 600, 552, "middle")[0]}
</svg>
'''
open(P("social/og-image.svg"), "w", encoding="utf-8").write(OG)
cairosvg.svg2png(url=P("social/og-image.svg"), write_to=P("social/og-image.png"),
                 output_width=1200, output_height=630)
# square social avatar
cairosvg.svg2png(url=P("logo/nebras-mark-rays.svg"), write_to=P("social/avatar-1024.png"),
                 output_width=1024, output_height=1024)

# ---------------------------------------------------------------- tokens
tokens = {
    "name": "NebrasCRM", "name_ar": "نِبراس سي آر إم",
    "meaning_ar": "النِّبراس: المصباح الذي يُهتدى به",
    "colors": BRAND,
    "gradients": {
        "brand": f"linear-gradient(135deg,{BRAND['indigo2']} 0%,{BRAND['indigo']} 52%,{BRAND['violet']} 100%)",
        "light": f"linear-gradient(180deg,#FFFFFF 0%,#FFF3D6 55%,{BRAND['gold']} 100%)",
    },
    "font": "Droid Arabic Kufi",
    "radius": {"tile": "22.6%", "card": "12px", "pill": "999px"},
}
open(P("assets/tokens.json"), "w", encoding="utf-8").write(
    json.dumps(tokens, ensure_ascii=False, indent=2))

css = ":root{\n" + "".join(f"  --nebras-{k}: {v};\n" for k, v in BRAND.items())
css += f"  --nebras-gradient: {tokens['gradients']['brand']};\n"
css += f"  --nebras-light: {tokens['gradients']['light']};\n}}\n"
open(P("assets/brand.css"), "w", encoding="utf-8").write(css)

manifest = {
    "id": "/app",
    "name": "NebrasCRM — نبراس سي آر إم",
    "short_name": "نبراس",
    "description": "منصة إدارة علاقات العملاء للمؤسسات — مبيعات، تسويق، دعم، مخزون ومالية",
    "start_url": "/app?src=pwa",
    "scope": "/",
    "display": "standalone",
    "display_override": ["window-controls-overlay", "standalone", "minimal-ui"],
    "orientation": "any",
    "background_color": BRAND["ink"],
    "theme_color": BRAND["indigo"],
    "lang": "ar",
    "dir": "rtl",
    "categories": ["business", "productivity", "finance"],
    "prefer_related_applications": False,
    "launch_handler": {"client_mode": "navigate-existing"},
    "icons": [
        {"src": "/brand/favicon/icon-96.png",  "sizes": "96x96",   "type": "image/png"},
        {"src": "/brand/favicon/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/brand/favicon/icon-256.png", "sizes": "256x256", "type": "image/png"},
        {"src": "/brand/favicon/icon-384.png", "sizes": "384x384", "type": "image/png"},
        {"src": "/brand/favicon/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/brand/favicon/maskable-512.png", "sizes": "512x512",
         "type": "image/png", "purpose": "maskable"},
        {"src": "/brand/favicon/favicon.svg", "sizes": "any", "type": "image/svg+xml"},
    ],
    "shortcuts": [
        {"name": "لوحة التحكم", "short_name": "اللوحة", "url": "/app?src=shortcut",
         "icons": [{"src": "/brand/favicon/icon-96.png", "sizes": "96x96"}]},
        {"name": "المساعد الذكي", "short_name": "الذكاء", "url": "/app?view=ai",
         "icons": [{"src": "/brand/favicon/icon-96.png", "sizes": "96x96"}]},
        {"name": "بوابة العملاء", "short_name": "العملاء", "url": "/portal",
         "icons": [{"src": "/brand/favicon/icon-96.png", "sizes": "96x96"}]},
        {"name": "بوابة الشركاء", "short_name": "الشركاء", "url": "/agent",
         "icons": [{"src": "/brand/favicon/icon-96.png", "sizes": "96x96"}]},
    ],
    "screenshots": [
        {"src": "/brand/social/og-image.png", "sizes": "1200x630",
         "type": "image/png", "form_factor": "wide", "label": "لوحة التحكم"},
    ],
}
open(P("assets/site.webmanifest"), "w", encoding="utf-8").write(
    json.dumps(manifest, ensure_ascii=False, indent=2))

print("✔ identity generated")
for root, _, fs in sorted(os.walk(HERE)):
    for f in sorted(fs):
        if f.endswith((".py", ".pyc")): continue
        p = os.path.join(root, f)
        print(f"   {os.path.relpath(p, HERE):42} {os.path.getsize(p)/1024:8.1f} KB")
