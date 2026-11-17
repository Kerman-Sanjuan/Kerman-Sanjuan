#!/usr/bin/env python3
"""Animated profile header, in Kerman's own voice: gruvbox paper, IBM Plex, a
mono eyebrow, the headline typed one character at a time and the portrait cut
into a circle on the right. SVG + SMIL, so it plays inside GitHub's <img>, and
every font and photo is embedded.

Everything personal comes from profile.json.

    python scripts/header.py [--config profile.json] [--assets assets]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kit import (ROOT, attr, colour, esc, font_face, jpeg_b64, load_config,
                 reduced_motion_css, resolve, warn, write)

# Layout. Two headline lines of about 30 characters fit next to the portrait.
W, H = 1100, 280
TEXT_X, EYEBROW_BASELINE = 62, 78
FIRST_BASELINE, LINE_HEIGHT, TITLE_GAP = 134, 54, 46
EYEBROW_FONT = "11.5px IBM_PLEX_MONO_PLACEHOLDER"
HEADLINE_FONT = "44px IBM_PLEX_SANS_PLACEHOLDER"
TITLE_FONT = "12.5px IBM_PLEX_MONO_PLACEHOLDER"
TITLE_CHAR_W = 7.95       # 12.5px mono advance (7.5) plus the .4 letter-spacing: one step of the typing clip
PHOTO_SCALE, PHOTO_QUALITY = 3, 82
GRID_STEP = 46            # the faint paper grid, same rhythm as the platform site
START, PER_CHAR, LINE_PAUSE = 0.5, 0.045, 0.35      # seconds
TITLE_CLIP = '[clip-path^="url(#rc"]'               # removed under reduced motion

SANS_FALLBACK = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO_FALLBACK = "Menlo,Consolas,monospace"


def words(cfg: dict) -> list[list[tuple[str, str, bool]]]:
    """The headline as lines of (word, colour, italic). A run's text can hold several words."""
    lines = []
    for line in cfg["header"]["headline"]:
        lines.append([(word, colour(cfg, run.get("color")), bool(run.get("italic")))
                      for run in line for word in run["text"].split()])
    return lines


def alt_text(cfg: dict) -> str:
    h = cfg["header"]
    headline = " ".join(word for line in words(cfg) for word, _, _ in line)
    return h.get("alt") or f'{headline} {h["title"].rstrip(".")}.'


def fonts_css(cfg: dict) -> tuple[str, str, str]:
    """(@font-face rules, sans stack, mono stack) — the stacks carry fallbacks so a
    missing file still renders something readable."""
    sans_rule, sans = font_face(cfg, "sans")
    mono_rule, mono = font_face(cfg, "mono")
    return (sans_rule + mono_rule,
            f"{sans},{SANS_FALLBACK}" if sans else SANS_FALLBACK,
            f"{mono},{MONO_FALLBACK}" if mono else MONO_FALLBACK)


def portrait(cfg: dict) -> tuple[str, str]:
    """The photo, cropped square, cut into a circle with a hairline ring.
    Returns (defs, body): the clip path belongs in <defs>, the group on the canvas."""
    p = cfg["header"].get("photo") or {}
    path = resolve(cfg, p.get("path"))
    diameter = p.get("width", 184)
    if not path:
        return "", ""
    if not path.exists():
        warn(f"header photo not found ({path}); building the header without it")
        return "", ""
    r = diameter / 2
    cx, cy = W - 62 - r, H / 2
    b64 = jpeg_b64(path, (diameter * PHOTO_SCALE, diameter * PHOTO_SCALE), PHOTO_QUALITY)
    ring = cfg["palette"].get("header", {}).get("ring", "#c9b98c")
    defs = f'<clipPath id="face"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/></clipPath>'
    body = (f'<g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="0s" dur="1.6s" fill="freeze"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{ring}" opacity=".28"/>'
            f'<image href="data:image/jpeg;base64,{b64}" x="{cx - r:.1f}" y="{cy - r:.1f}" '
            f'width="{diameter}" height="{diameter}" preserveAspectRatio="xMidYMid slice" clip-path="url(#face)"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - .75:.1f}" fill="none" stroke="{ring}" stroke-width="1.5"/>'
            f'</g>')
    return defs, body


def grid(cfg: dict) -> str:
    """The whisper-quiet paper grid from platform.k3rman.com."""
    line = cfg["palette"].get("header", {}).get("grid", "#e3d7ae")
    vertical = "".join(f"M{x} {EYEBROW_BASELINE - 16}V{H}" for x in range(GRID_STEP, W, GRID_STEP))
    horizontal = "".join(f"M0 {y}H{W}" for y in range(GRID_STEP, H, GRID_STEP))
    return (f'<path d="{vertical}{horizontal}" stroke="{line}" stroke-width="1" fill="none" opacity=".75"/>')


def render(cfg: dict) -> str:
    h = cfg["header"]
    hp = cfg["palette"].get("header", {})
    left, right = hp.get("paper_gradient", ["#f2e5bc", "#fbf1c7"])
    fonts, sans, mono = fonts_css(cfg)
    headline_font = HEADLINE_FONT.replace("IBM_PLEX_SANS_PLACEHOLDER", sans)
    eyebrow_font = EYEBROW_FONT.replace("IBM_PLEX_MONO_PLACEHOLDER", mono)
    title_font = TITLE_FONT.replace("IBM_PLEX_MONO_PLACEHOLDER", mono)
    eyebrow_colour = colour(cfg, "eyebrow", "muted")
    photo_defs, photo_body = portrait(cfg)

    parts = [
        '<defs>'
        f'<linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="{left}"/><stop offset="1" stop-color="{right}"/></linearGradient>'
        f'<clipPath id="r"><rect width="{W}" height="{H}" rx="12"/></clipPath>'
        f'{photo_defs}'
        '</defs>',
        f'<style>{fonts}{reduced_motion_css(TITLE_CLIP)}.eyebrow{{letter-spacing:2.6px}}</style>',
        f'<g clip-path="url(#r)"><rect width="{W}" height="{H}" fill="url(#pg)"/>{grid(cfg)}{photo_body}</g>',
    ]

    # The eyebrow: small, mono, tracked out, sage. It labels the headline.
    eyebrow = h.get("eyebrow")
    if eyebrow:
        parts.append(f'<text class="eyebrow" x="{TEXT_X}" y="{EYEBROW_BASELINE}" '
                     f'style="font:{eyebrow_font}" fill="{eyebrow_colour}" opacity="0">{esc(eyebrow.upper())}'
                     f'<animate attributeName="opacity" from="0" to="1" begin="0.15s" dur="0.9s" fill="freeze"/></text>')

    # Type the headline one character at a time: each character is a <tspan> that a
    # <set> reveals, so proportional fonts never show half a letter.
    t = START
    y = FIRST_BASELINE
    for line in words(cfg):
        spans = []
        for wi, (word, fill, italic) in enumerate(line):
            style = ' font-style="italic"' if italic else ""
            for ch in word + (" " if wi < len(line) - 1 else ""):
                spans.append(f'<tspan fill="{fill}"{style} opacity="0">{esc(ch)}<set attributeName="opacity" to="1" begin="{t:.2f}s"/></tspan>')
                t += PER_CHAR
        parts.append(f'<text x="{TEXT_X}" y="{y}" xml:space="preserve" style="font:{headline_font}">{"".join(spans)}</text>')
        t += LINE_PAUSE
        y += LINE_HEIGHT

    # The title types out behind a clip that widens in steps of one average character.
    title = h["title"]
    ty = y - LINE_HEIGHT + TITLE_GAP
    steps = ";".join(f"{j * TITLE_CHAR_W:.1f}" for j in range(len(title) + 1))
    parts.append(f'<clipPath id="rc"><rect x="{TEXT_X}" y="{ty - 16}" height="22" width="0">'
                 f'<animate attributeName="width" values="{steps}" calcMode="discrete" begin="{t + .25:.2f}s" dur="1.5s" fill="freeze"/></rect></clipPath>'
                 f'<g clip-path="url(#rc)"><text x="{TEXT_X}" y="{ty}" style="font:{title_font}" '
                 f'fill="{colour(cfg, "muted")}" letter-spacing=".4">{esc(title)}</text></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{attr(alt_text(cfg))}">' + "".join(parts) + "</svg>\n")


def build(cfg: dict, assets: Path) -> Path:
    out = assets / f'{cfg["header"].get("file", "header")}.svg'
    write(out, render(cfg))
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--assets", type=Path, default=ROOT / "assets", help="output folder (default: assets/)")
    a = ap.parse_args()
    build(load_config(a.config), a.assets)
