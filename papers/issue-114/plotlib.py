#!/usr/bin/env python3
"""Dependency-free raster plotting for issue #114.

WHY NOT MATPLOTLIB
------------------
The journal's reproducibility bar is "one command reproduces the core results".  A figure
pipeline that needs a package index at verification time is not one command, and a figure
whose bytes depend on the plotting library's version is not reproducible either.  Everything
here is the standard library: a raster canvas, a 3x5 bitmap font, and a zlib PNG writer.

Determinism: the PNG carries no timestamp, no text chunk and no metadata, and zlib is used at
a fixed level, so the bytes are a function of the series alone.  `figures/manifest.json` pins
each file by sha256 and `reproduce.sh` requires a rerun to match it -- which is only possible
because there is nothing nondeterministic in the writer.

Design: coarser than a plotting library on purpose.  What the six figures in this paper need is
axes, tick labels, lines, polyline bands, bars and points; anything more would be unused
surface area on a tool whose correctness is part of the evidence.
"""

from __future__ import annotations

import struct
import zlib

# --------------------------------------------------------------------------
# a 3x5 bitmap font (uppercase only: figure labels are drawn in capitals)
# --------------------------------------------------------------------------

_GLYPHS = {
    "0": ["###", "# #", "# #", "# #", "###"],
    "1": [" # ", "## ", " # ", " # ", "###"],
    "2": ["###", "  #", "###", "#  ", "###"],
    "3": ["###", "  #", "###", "  #", "###"],
    "4": ["# #", "# #", "###", "  #", "  #"],
    "5": ["###", "#  ", "###", "  #", "###"],
    "6": ["###", "#  ", "###", "# #", "###"],
    "7": ["###", "  #", "  #", "  #", "  #"],
    "8": ["###", "# #", "###", "# #", "###"],
    "9": ["###", "# #", "###", "  #", "###"],
    "A": ["###", "# #", "###", "# #", "# #"],
    "B": ["## ", "# #", "## ", "# #", "## "],
    "C": ["###", "#  ", "#  ", "#  ", "###"],
    "D": ["## ", "# #", "# #", "# #", "## "],
    "E": ["###", "#  ", "###", "#  ", "###"],
    "F": ["###", "#  ", "###", "#  ", "#  "],
    "G": ["###", "#  ", "# #", "# #", "###"],
    "H": ["# #", "# #", "###", "# #", "# #"],
    "I": ["###", " # ", " # ", " # ", "###"],
    "J": ["  #", "  #", "  #", "# #", "###"],
    "K": ["# #", "# #", "## ", "# #", "# #"],
    "L": ["#  ", "#  ", "#  ", "#  ", "###"],
    "M": ["# #", "###", "###", "# #", "# #"],
    "N": ["## ", "# #", "# #", "# #", "# #"],
    "O": ["###", "# #", "# #", "# #", "###"],
    "P": ["###", "# #", "###", "#  ", "#  "],
    "Q": ["###", "# #", "# #", "###", "  #"],
    "R": ["###", "# #", "###", "## ", "# #"],
    "S": ["###", "#  ", "###", "  #", "###"],
    "T": ["###", " # ", " # ", " # ", " # "],
    "U": ["# #", "# #", "# #", "# #", "###"],
    "V": ["# #", "# #", "# #", "# #", " # "],
    "W": ["# #", "# #", "###", "###", "# #"],
    "X": ["# #", "# #", " # ", "# #", "# #"],
    "Y": ["# #", "# #", " # ", " # ", " # "],
    "Z": ["###", "  #", " # ", "#  ", "###"],
    " ": ["   ", "   ", "   ", "   ", "   "],
    ".": ["   ", "   ", "   ", "   ", " # "],
    ",": ["   ", "   ", "   ", " # ", "#  "],
    "-": ["   ", "   ", "###", "   ", "   "],
    "+": ["   ", " # ", "###", " # ", "   "],
    "=": ["   ", "###", "   ", "###", "   "],
    "/": ["  #", "  #", " # ", "#  ", "#  "],
    ":": ["   ", " # ", "   ", " # ", "   "],
    "(": [" # ", "#  ", "#  ", "#  ", " # "],
    ")": [" # ", "  #", "  #", "  #", " # "],
    "%": ["# #", "  #", " # ", "#  ", "# #"],
    "<": ["  #", " # ", "#  ", " # ", "  #"],
    ">": ["#  ", " # ", "  #", " # ", "#  "],
    "_": ["   ", "   ", "   ", "   ", "###"],
    "*": ["# #", " # ", "###", " # ", "# #"],
    "[": ["## ", "#  ", "#  ", "#  ", "## "],
    "]": [" ##", "  #", "  #", "  #", " ##"],
}
_GLYPH_W, _GLYPH_H, _GLYPH_GAP = 3, 5, 1

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GREY = (150, 150, 150)
LIGHT = (225, 225, 225)
# a small, colour-blind-safe-ish palette: blue / orange / green / red / purple
BLUE = (31, 106, 178)
ORANGE = (222, 124, 34)
GREEN = (39, 145, 80)
RED = (192, 45, 45)
PURPLE = (117, 76, 160)


class Canvas:
    """An RGB raster with the few primitives the figures need."""

    def __init__(self, w: int, h: int, bg=WHITE):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def px(self, x: int, y: int, c) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * (y * self.w + x)
            self.buf[i:i + 3] = bytes(c)

    def rect(self, x0: int, y0: int, x1: int, y1: int, c, fill=True, width=1) -> None:
        xa, xb = sorted((int(x0), int(x1)))
        ya, yb = sorted((int(y0), int(y1)))
        if fill:
            row = bytes(c) * (xb - xa + 1)
            for y in range(max(0, ya), min(self.h - 1, yb) + 1):
                i = 3 * (y * self.w + max(0, xa))
                n = min(self.w - 1, xb) - max(0, xa) + 1
                self.buf[i:i + 3 * n] = row[:3 * n]
        else:
            self.rect(xa, ya, xb, ya + width - 1, c)
            self.rect(xa, yb - width + 1, xb, yb, c)
            self.rect(xa, ya, xa + width - 1, yb, c)
            self.rect(xb - width + 1, ya, xb, yb, c)

    def line(self, x0: float, y0: float, x1: float, y1: float, c, width=1) -> None:
        """Bresenham; `width` stamps a square of that size at every step."""
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        half = max(0, (width - 1) // 2)
        while True:
            for ox in range(-half, width - half):
                for oy in range(-half, width - half):
                    self.px(x0 + ox, y0 + oy, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def text(self, x: int, y: int, s: str, c=BLACK, scale: int = 2) -> int:
        """Draw `s` (uppercased) with its TOP-LEFT at (x, y); returns the width used."""
        cx = x
        for ch in s.upper():
            rows = _GLYPHS.get(ch)
            if rows is None:
                rows = _GLYPHS[" "]
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "#":
                        self.rect(cx + rx * scale, y + ry * scale,
                                  cx + rx * scale + scale - 1, y + ry * scale + scale - 1, c)
            cx += (_GLYPH_W + _GLYPH_GAP) * scale
        return cx - x - _GLYPH_GAP * scale

    def band(self, x0, y0, x1, y1, c) -> None:
        """A filled rectangle used for bands (kept as a named intent, not a synonym)."""
        self.rect(x0, y0, x1, y1, c, fill=True)

    def save(self, path: str) -> bytes:
        """Write a PNG (colour type 2, 8-bit, no ancillary chunks) and return its bytes."""
        raw = bytearray()
        stride = 3 * self.w
        for y in range(self.h):
            raw.append(0)                             # filter type 0 for every scanline
            raw += self.buf[y * stride:(y + 1) * stride]

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
               + chunk(b"IEND", b""))
        with open(path, "wb") as fh:
            fh.write(png)
        return png


class Axes:
    """A plot box: data -> pixel mapping, frame, ticks, and the series primitives."""

    def __init__(self, canvas: Canvas, box, xlim, ylim, xlabel: str = "", ylabel: str = "",
                 xticks=None, yticks=None, xfmt: str = "{:.2f}", yfmt: str = "{:.2f}",
                 scale: int = 1, title: str = ""):
        self.c = canvas
        self.x0, self.y0, self.x1, self.y1 = box           # pixel box, y0 = top
        self.xlim, self.ylim = xlim, ylim
        self.xfmt, self.yfmt, self.scale = xfmt, yfmt, scale
        self.xticks = list(xticks) if xticks is not None else []
        self.yticks = list(yticks) if yticks is not None else []
        self.xlabel, self.ylabel, self.title = xlabel, ylabel, title

    # -- mapping -----------------------------------------------------------
    def X(self, v: float) -> float:
        (a, b) = self.xlim
        return self.x0 + (v - a) / (b - a) * (self.x1 - self.x0)

    def Y(self, v: float) -> float:
        (a, b) = self.ylim
        return self.y1 - (v - a) / (b - a) * (self.y1 - self.y0)

    # -- frame and ticks ---------------------------------------------------
    def frame(self) -> None:
        s = self.scale
        self.c.rect(self.x0, self.y0, self.x1, self.y1, BLACK, fill=False, width=1)
        for t in self.xticks:
            x = int(round(self.X(t)))
            self.c.line(x, self.y1, x, self.y1 + 3 * s, BLACK)
            lab = self.xfmt.format(t)
            w = len(lab) * (_GLYPH_W + _GLYPH_GAP) * s - _GLYPH_GAP * s
            self.c.text(int(x - w / 2), self.y1 + 5 * s, lab, BLACK, s)
        for t in self.yticks:
            y = int(round(self.Y(t)))
            self.c.line(self.x0 - 3 * s, y, self.x0, y, BLACK)
            lab = self.yfmt.format(t)
            w = len(lab) * (_GLYPH_W + _GLYPH_GAP) * s - _GLYPH_GAP * s
            self.c.text(int(self.x0 - 5 * s - w), int(y - _GLYPH_H * s / 2), lab, BLACK, s)
        if self.xlabel:
            w = len(self.xlabel) * (_GLYPH_W + _GLYPH_GAP) * s - _GLYPH_GAP * s
            self.c.text(int((self.x0 + self.x1) / 2 - w / 2), self.y1 + 14 * s,
                        self.xlabel, BLACK, s)
        if self.ylabel:
            # vertical label: draw rotated by stamping the glyphs column-wise
            self._vtext(int(self.x0 - 34 * s), int((self.y0 + self.y1) / 2), self.ylabel, s)
        if self.title:
            self.c.text(self.x0, self.y0 - 12 * s, self.title, BLACK, s)

    def _vtext(self, x: int, y: int, s: str, scale: int) -> None:
        """Draw `s` bottom-to-top at x (a rotated y-axis label)."""
        total = len(s) * (_GLYPH_W + _GLYPH_GAP) * scale - _GLYPH_GAP * scale
        cy = y + total // 2
        for ch in s.upper():
            rows = _GLYPHS.get(ch, _GLYPHS[" "])
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "#":
                        px = x + (4 - ry) * scale          # rotate: rows become columns
                        py = cy - rx * scale - scale
                        self.c.rect(px, py, px + scale - 1, py + scale - 1, BLACK)
            cy -= (_GLYPH_W + _GLYPH_GAP) * scale

    # -- series ------------------------------------------------------------
    def plot(self, xs, ys, color, width: int = 1) -> None:
        pts = [(self.X(x), self.Y(y)) for x, y in zip(xs, ys)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            self.c.line(ax, ay, bx, by, color, width)

    def points(self, xs, ys, color, r: int = 2) -> None:
        for x, y in zip(xs, ys):
            self.c.rect(int(self.X(x)) - r, int(self.Y(y)) - r,
                        int(self.X(x)) + r, int(self.Y(y)) + r, color)

    def vband(self, xs, ylo, yhi, color) -> None:
        """A vertical band between two series (the paper's uncertainty bands)."""
        for x, lo, hi in zip(xs, ylo, yhi):
            self.c.line(self.X(x), self.Y(lo), self.X(x), self.Y(hi), color, 1)

    def hline(self, v, color, dash: bool = False) -> None:
        y = int(round(self.Y(v)))
        if not dash:
            self.c.line(self.x0, y, self.x1, y, color, 1)
        else:
            x = self.x0
            while x < self.x1:
                self.c.line(x, y, min(x + 6, self.x1), y, color, 1)
                x += 12

    def vline(self, v, color, dash: bool = False) -> None:
        x = int(round(self.X(v)))
        if not dash:
            self.c.line(x, self.y0, x, self.y1, color, 1)
        else:
            y = self.y0
            while y < self.y1:
                self.c.line(x, y, x, min(y + 6, self.y1), color, 1)
                y += 12

    def bars(self, centers, heights, color, width_px: int = 10) -> None:
        for c, h in zip(centers, heights):
            x = int(round(self.X(c)))
            y = int(round(self.Y(h)))
            self.c.rect(x - width_px // 2, y, x + width_px // 2, int(self.Y(self.ylim[0])),
                        color, fill=True)

    def legend(self, entries, x: int, y: int, s: int = 1) -> None:
        """entries: [(color, label), ...] stacked under (x, y)."""
        for i, (color, label) in enumerate(entries):
            yy = y + i * 9 * s
            self.c.rect(x, yy + 2 * s, x + 10 * s, yy + 4 * s, color, fill=True)
            self.c.text(x + 14 * s, yy, label, BLACK, s)
