#!/usr/bin/env python3
"""Deterministic daily news image generator — PURE PYTHON STDLIB ONLY.

Produces exactly one file: /output/entry.png (PNG, 1024x1024).
Sums up the world news of Monday 23 November 2026 as a newspaper
front page: one main story (COP31 collapses) plus three supporting
stories (EU sanctions, Ukraine-Libya, markets rebound).

All news content hardcoded. No network access. Byte-identical output
on every run (no timestamps, no randomness, no embedded metadata).

No third-party imports. PNG chunks (IHDR/IDAT/IEND) written manually
with struct + zlib. Text rendered from a bitmap font defined inline in
this file. Single file on purpose: the grader runs `python3 -P -s`,
which drops the script directory from sys.path, so sibling imports
would fail.
"""

import os
import struct
import zlib

# Bitmap font: 5x7 grid per glyph, defined purely in code (no external font files).
# Each glyph is a tuple of 7 integers (5 bits each; bit 4 = leftmost pixel).
# CELL_W = 6 (5 glyph columns + 1 space column), CELL_H = 7.

GLYPHS = {
    ' ':   (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000),
    'A':   (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B':   (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C':   (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D':   (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E':   (0b11111, 0b10000, 0b10000, 0b11111, 0b10000, 0b10000, 0b11111),
    'F':   (0b11111, 0b10000, 0b10000, 0b11111, 0b10000, 0b10000, 0b10000),
    'G':   (0b01110, 0b10001, 0b10000, 0b10110, 0b10001, 0b10001, 0b01110),
    'H':   (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I':   (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111),
    'J':   (0b11111, 0b00100, 0b00100, 0b00100, 0b00101, 0b01010, 0b01110),
    'K':   (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L':   (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b00001, 0b11111),
    'M':   (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N':   (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O':   (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P':   (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q':   (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01110),
    'R':   (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10101, 0b10001),
    'S':   (0b01110, 0b10000, 0b10000, 0b01110, 0b00001, 0b10001, 0b01110),
    'T':   (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U':   (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V':   (0b10001, 0b10001, 0b10001, 0b01010, 0b01010, 0b01010, 0b00100),
    'W':   (0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b11011, 0b10001),
    'X':   (0b10001, 0b10101, 0b00100, 0b00100, 0b00100, 0b10101, 0b10001),
    'Y':   (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z':   (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '0':   (0b01110, 0b10001, 0b10101, 0b10101, 0b10101, 0b10001, 0b01110),
    '1':   (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2':   (0b01110, 0b10001, 0b00001, 0b01110, 0b10000, 0b10000, 0b01110),
    '3':   (0b01110, 0b10001, 0b00001, 0b01100, 0b00001, 0b10001, 0b01110),
    '4':   (0b10001, 0b10001, 0b10001, 0b11111, 0b00001, 0b00001, 0b00001),
    '5':   (0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b10001, 0b01110),
    '6':   (0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7':   (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8':   (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9':   (0b01110, 0b10001, 0b10001, 0b01110, 0b00001, 0b00001, 0b01110),
    '.':   (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100),
    ',':   (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b01000),
    '-':   (0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000),
    '&':   (0b01110, 0b10001, 0b10011, 0b01010, 0b10101, 0b10001, 0b01110),
    '/':   (0b10000, 0b10000, 0b01000, 0b01000, 0b00100, 0b00010, 0b00001),
    ':':   (0b00000, 0b00000, 0b00100, 0b00000, 0b00100, 0b00000, 0b00000),
    ';':   (0b00000, 0b00100, 0b00000, 0b00100, 0b00000, 0b00100, 0b00100),
    '%':   (0b10101, 0b01010, 0b00100, 0b01010, 0b10101, 0b00000, 0b00000),
    '·':   (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100),
    '"':   (0b00000, 0b01010, 0b01010, 0b00000, 0b00000, 0b00000, 0b00000),
    "'":   (0b00000, 0b00100, 0b00100, 0b00000, 0b00000, 0b00000, 0b00000),
    '!':   (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100),
    '?':   (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b00100, 0b00100),
}

CELL_W = 6
CELL_H = 7

def cell_w(scale):
    return CELL_W * scale

def line_h(scale):
    return CELL_H * scale

def text_w(text, scale):
    return len(text) * cell_w(scale)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WIDTH = 1024
HEIGHT = 1024
OUTPUT_FILE = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")

# High-contrast limited palette.
BG_COLOR = (14, 17, 23)          # near-black background
INK_COLOR = (245, 245, 245)      # near-white text
ACCENT_COLOR = (231, 76, 60)     # strong red accent for main story
MUTED_COLOR = (139, 145, 155)    # muted grey for secondary text
BLUE_COLOR = (62, 142, 222)      # supporting story 1 marker
GREEN_COLOR = (67, 168, 90)      # supporting story 2 marker
AMBER_COLOR = (232, 161, 60)     # supporting story 3 marker

PAD = 40

DATE_LINE_MAIN = "THE WORLD IN ONE DAY"
DATE_LINE_SUB = "MONDAY 23 NOVEMBER 2026"

# Hardcoded news content (no network access at runtime).
NEWS = {
    "main": {
        "headline": "COP31 COLLAPSES WITHOUT DEAL",
        "sub": "EU rejects draft with no fossil fuels; longest climate talks ever end empty.",
    },
    "supporting": [
        {
            "headline": "EU UNVEILS 22ND RUSSIA SANCTIONS",
            "sub": "60 banks off SWIFT; crypto, shadow fleet, sports bans.",
            "color": BLUE_COLOR,
        },
        {
            "headline": "UKRAINE SINKS RUSSIAN WARSHIP",
            "sub": "Drone strike in Libya port; cargo ship hit in Finland gulf.",
            "color": GREEN_COLOR,
        },
        {
            "headline": "MARKETS REBOUND AFTER FRIDAY CRASH",
            "sub": "Nasdaq futures up 3%; SK hynix up 20% on Huang return.",
            "color": AMBER_COLOR,
        },
    ],
}

FOOTER = 'Sources: AP · Reuters · BBC · Euronews'

# Scales per element.
SCALE_MAIN_TITLE = 6
SCALE_MAIN_SUB = 4
SCALE_MAIN_HEAD = 8
SCALE_MAIN_SUBHEAD = 4
SCALE_SUPPORT_HEAD = 4
SCALE_SUPPORT_SUB = 3
SCALE_FOOTER = 3


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        r, g, b = color
        self.pix = bytearray([r, g, b] * (w * h))

    def idx(self, x, y):
        return (y * self.w + x) * 3

    def rect(self, x0, y0, x1, y1, color):
        r, g, b = color
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            for x in range(x0, x1):
                self.pix[base] = r
                self.pix[base + 1] = g
                self.pix[base + 2] = b
                base += 3

    def put_glyph(self, ch, x, y, scale, color):
        g = GLYPHS.get(ch)
        if g is None:
            return
        r, g2, b = color
        for bitrow in g:
            col = x
            for bitpos in range(4, -1, -1):
                if bitrow & (1 << bitpos):
                    for dy in range(scale):
                        py = y + dy
                        if py >= self.h:
                            continue
                        base = (py * self.w + col) * 3
                        for dx in range(scale):
                            px = col + dx
                            if px >= self.w:
                                break
                            self.pix[base] = r
                            self.pix[base + 1] = g2
                            self.pix[base + 2] = b
                            base += 3
                col += scale
            y += scale

    def put_text(self, text, x, y, scale, color):
        text = text.upper()
        cx = x
        for ch in text:
            self.put_glyph(ch, cx, y, scale, color)
            cx += cell_w(scale)
        return cx

    def save_png(self, path):
        w, h = self.w, self.h
        row_bytes = bytearray()
        for y in range(h):
            row_bytes.append(0)  # filter type 0
            base = y * w * 3
            row_bytes.extend(self.pix[base:base + w * 3])

        compressed = zlib.compress(row_bytes, 6)

        def chunk(ctype, data):
            c = ctype if isinstance(ctype, bytes) else ctype.encode("ascii")
            crc = zlib.crc32(c + data) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + c + data + struct.pack(">I", crc)

        png = bytearray()
        png.extend(b"\x89PNG\r\n\x1a\n")
        png.extend(chunk("IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        png.extend(chunk("IDAT", compressed))
        png.extend(chunk("IEND", b""))

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(png)
        print(f"Wrote {path}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def wrap_text(text, scale, max_w):
    """Word-wrap text so each line fits within max_w (in pixels)."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        tw = text_w(trial, scale)
        if tw <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def put_lines(canvas, lines, x, y, scale, color, gap=4):
    """Draw multiple wrapped lines; returns final y cursor."""
    for ln in lines:
        canvas.put_text(ln, x, y, scale, color)
        y += line_h(scale) + gap
    return y


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    c = Canvas(WIDTH, HEIGHT, BG_COLOR)
    pad = PAD
    col_w = WIDTH - 2 * pad

    # ---- Masthead (top, centered) ----
    y = pad + 6
    c.put_text(DATE_LINE_MAIN, (WIDTH - text_w(DATE_LINE_MAIN, SCALE_MAIN_TITLE)) // 2,
               y, SCALE_MAIN_TITLE, INK_COLOR)
    y += line_h(SCALE_MAIN_TITLE) + 22
    c.put_text(DATE_LINE_SUB, (WIDTH - text_w(DATE_LINE_SUB, SCALE_MAIN_SUB)) // 2,
               y, SCALE_MAIN_SUB, MUTED_COLOR)
    y += line_h(SCALE_MAIN_SUB) + 30

    # Accent rule under masthead (thick red bar)
    rule_w = 340
    c.rect((WIDTH - rule_w) // 2, y, (WIDTH - rule_w) // 2 + rule_w, y + 12, ACCENT_COLOR)
    y += 52

    # ---- Main story panel ----
    # Red block accent on the left of headline
    block_w = 16
    block_h = line_h(SCALE_MAIN_HEAD) + 16
    c.rect(pad - 10, y - 8, pad - 10 + block_w, y - 8 + block_h, ACCENT_COLOR)

    # Wrap main headline into lines with gap between them
    head_lines = wrap_text(NEWS["main"]["headline"], SCALE_MAIN_HEAD, col_w - block_w - 24)
    cx = pad + block_w + 24
    cy = y - 8 + 8
    for ln in head_lines:
        c.put_text(ln, cx, cy, SCALE_MAIN_HEAD, ACCENT_COLOR)
        cy += line_h(SCALE_MAIN_HEAD) + 16   # gap between wrapped lines
    y = cy + 36

    # Sub-headline (wrapped, larger gap between lines)
    sub_lines = wrap_text(NEWS["main"]["sub"], SCALE_MAIN_SUBHEAD, col_w)
    y = put_lines(c, sub_lines, pad, y, SCALE_MAIN_SUBHEAD, INK_COLOR, gap=8)
    y += 56

    # ---- Supporting items (three rows, full width) ----
    for idx, item in enumerate(NEWS["supporting"]):
        # small color-block square marking the row
        sq = 20
        c.rect(pad, y, pad + sq, y + sq, item["color"])
        tx = pad + sq + 12
        tw = col_w - sq - 12
        # headline (may wrap)
        h_lines = wrap_text(item["headline"], SCALE_SUPPORT_HEAD, tw)
        y = put_lines(c, h_lines, tx, y, SCALE_SUPPORT_HEAD, INK_COLOR, gap=4)
        # sub (wrapped)
        s_lines = wrap_text(item["sub"], SCALE_SUPPORT_SUB, tw)
        y = put_lines(c, s_lines, tx, y, SCALE_SUPPORT_SUB, MUTED_COLOR, gap=6)
        # gap between supporting blocks (larger for last one)
        y += 36 if idx < len(NEWS["supporting"]) - 1 else 28

    # ---- Footer (bottom, with breathing room) ----
    footer_y = HEIGHT - pad - line_h(SCALE_FOOTER) - 8
    # Push footer down if content ended too early
    if footer_y < y + 30:
        footer_y = y + 20
    # Thin muted rule closing the page above the footer
    c.rect(pad, footer_y - 26, pad + col_w, footer_y - 24, (60, 64, 72))
    c.put_text(FOOTER, pad, footer_y, SCALE_FOOTER, MUTED_COLOR)

    c.save_png(OUTPUT_FILE)


if __name__ == "__main__":
    main()
