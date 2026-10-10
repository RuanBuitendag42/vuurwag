"""Make Rich/Textual SVG screenshots render the ASCII art exactly.

* Ligature fonts (Fira Code is the default) would turn `->`, `|=`, `=>` and friends into arrows: switch them off.
* A text span that starts or ends with spaces gets its padding turned into an x offset, so renderers that
  squash non-breaking spaces (librsvg, some browsers) still put every glyph in its own cell.
"""
from __future__ import annotations

import re

_TEXT = re.compile(r'<text([^>]*?) x="([\d.]+)"([^>]*?) textLength="([\d.]+)"([^>]*)>(.*?)</text>')
_NBSP = "&#160;"


def _cells(content: str) -> int:
    """Number of cells in escaped SVG text content."""
    return len(re.sub(r"&#?\w+;", "x", content))


def tidy_svg(svg: str) -> str:
    def repl(m: re.Match[str]) -> str:
        pre, x, mid, tl, post, content = m.groups()
        n = _cells(content)
        if n == 0:
            return m.group(0)
        cw = float(tl) / n
        lead = 0
        while content.startswith(_NBSP):
            content = content[len(_NBSP):]
            lead += 1
        trail = 0
        while content.endswith(_NBSP):
            content = content[: -len(_NBSP)]
            trail += 1
        if not content:
            return ""
        x2 = float(x) + lead * cw
        tl2 = float(tl) - (lead + trail) * cw
        return f'<text{pre} x="{x2:g}"{mid} textLength="{tl2:g}"{post}>{content}</text>'

    svg = _TEXT.sub(repl, svg)
    svg = svg.replace("font-family: Fira Code, monospace;",
                      "font-family: 'DejaVu Sans Mono', Menlo, Consolas, 'Liberation Mono', monospace;", 1)
    svg = svg.replace("font-variant-east-asian: full-width;",
                      "font-variant-east-asian: full-width;\n        font-variant-ligatures: none;\n"
                      "        font-feature-settings: \"liga\" 0, \"calt\" 0;", 1)
    return svg
