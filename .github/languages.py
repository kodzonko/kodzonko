"""Render GitHub-style "most used languages" cards (light and dark) from a GraphQL repositories response."""

import json
import sys
from collections import Counter
from html import escape

IGNORED = {"batchfile", "css", "dockerfile", "hcl", "html", "makefile", "powershell", "scss", "shell"}
LIMIT = 8
WIDTH = 480
ROW = 22

FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'
# GitHub's own muted and default text colors, as (percentage, name) per theme.
THEMES = {"light": ("#59636e", "#1f2328"), "dark": ("#9198a1", "#f0f6fc")}


def top_languages(data: dict) -> list[tuple[str, int, str]]:
    """Sum language bytes across repositories and return the largest as (name, bytes, color)."""
    sizes: Counter[str] = Counter()
    colors: dict[str, str] = {}
    for repo in data["data"]["viewer"]["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name.lower() not in IGNORED:
                sizes[name] += edge["size"]
                colors[name] = edge["node"]["color"] or "#8b949e"
    return [(name, size, colors[name]) for name, size in sizes.most_common(LIMIT)]


def render(languages: list[tuple[str, int, str]], theme: str) -> str:
    """Return an SVG with one stacked bar and a two-column legend with percentages."""
    muted, strong = THEMES[theme]
    style = f"text {{ font: 12px {FONT}; fill: {muted}; }} .name {{ font-weight: 600; fill: {strong}; }}"
    total = sum(size for _, size, _ in languages)
    bar, legend, x = [], [], 0.0
    for i, (name, size, color) in enumerate(languages):
        width = WIDTH * size / total
        bar.append(f'<rect x="{x:.2f}" width="{width:.2f}" height="8" fill="{color}"/>')
        x += width
        lx, ly = (i % 2) * WIDTH // 2, 34 + (i // 2) * ROW
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 16}" y="{ly}"><tspan class="name">{escape(name)}</tspan> {100 * size / total:.1f}%</text>'
        )
    height = 34 + (len(languages) + 1) // 2 * ROW - ROW + 8
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">'
        f"<style>{style}</style>"
        f'<clipPath id="bar"><rect width="{WIDTH}" height="8" rx="4"/></clipPath>'
        f'<g clip-path="url(#bar)">{"".join(bar)}</g>{"".join(legend)}</svg>\n'
    )


if __name__ == "__main__":
    # Usage: languages.py <response.json> <output prefix>; writes <prefix>-light.svg and <prefix>-dark.svg.
    with open(sys.argv[1]) as f:
        languages = top_languages(json.load(f))
    for theme in THEMES:
        with open(f"{sys.argv[2]}-{theme}.svg", "w") as f:
            f.write(render(languages, theme))
