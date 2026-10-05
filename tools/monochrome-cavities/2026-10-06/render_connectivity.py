"""Reproducible synthetic SVG; no dataset/model/prediction files are read."""
import argparse
from html import escape
from pathlib import Path

from monochrome_cavities import recolor_enclosed

SOURCE = [[0, 1, 1], [1, 0, 1], [1, 1, 1]]
PALETTE = {0: "#101827", 1: "#3d8bfd", 4: "#ffd166"}


def grid_svg(source, x, y, caption):
    size = 54
    pieces = [f'<text x="{x + 81}" y="{y - 17}" text-anchor="middle" class="small">{escape(caption)}</text>']
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            pieces.append(f'<rect x="{x + c * size}" y="{y + r * size}" width="{size}" height="{size}" rx="5" fill="{PALETTE[color]}" stroke="#ffffff" stroke-width="3"/>')
            pieces.append(f'<text x="{x + c * size + size // 2}" y="{y + r * size + 34}" text-anchor="middle" fill="{("#101827" if color == 4 else "#ffffff")}" class="cell">{color}</text>')
    return "\n".join(pieces)


def render_svg():
    four = recolor_enclosed(SOURCE, 0, 4, 4, cpu_seconds=1.0)
    eight = recolor_enclosed(SOURCE, 0, 4, 8, cpu_seconds=1.0)
    panels = []
    for adjacency, offset, output, explanation in ((4, 38, four, "The center is enclosed: recolor it."),
                                                   (8, 598, eight, "The diagonal reaches the border: keep it.")):
        panels.append(f'<rect x="{offset}" y="135" width="524" height="325" rx="18" fill="#ffffff" stroke="#dce4ef"/>')
        panels.append(f'<text x="{offset + 28}" y="175" class="panel">{adjacency} neighbours</text>')
        panels.append(grid_svg(SOURCE, offset + 28, 228, "Constructed input"))
        panels.append(grid_svg(output, offset + 326, 228, "Generic rule output"))
        panels.append(f'<path d="M {offset + 225} 310 H {offset + 285}" stroke="#61758e" stroke-width="3" marker-end="url(#arrow)"/>')
        panels.append(f'<text x="{offset + 28}" y="430" class="small">{escape(explanation)}</text>')
        if adjacency == 8:
            panels.append(f'<path d="M {offset + 407} 310 L {offset + 353} 256" stroke="#ff8170" stroke-width="4" stroke-dasharray="6 4" marker-end="url(#arrowCoral)"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="540" viewBox="0 0 1160 540" role="img" aria-labelledby="title description">
<title id="title">Four versus eight neighbours: synthetic cavity connectivity</title>
<desc id="description">Two independent executions of a generic recoloring rule on a constructed 3x3 grid. With four neighbours the center zero is enclosed and becomes color4. With eight neighbours it connects diagonally to a border zero and remains zero. This is a synthetic concept demonstration, not a dataset or model result.</desc>
<defs><style>text{{font-family:system-ui,sans-serif}} .heading{{font-size:34px;font-weight:700;fill:#16263c}} .panel{{font-size:23px;font-weight:650;fill:#16263c}} .small{{font-size:16px;fill:#52657d}} .cell{{font-size:22px;font-weight:650}}</style>
<marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#61758e"/></marker>
<marker id="arrowCoral" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#ff8170"/></marker></defs>
<rect width="1160" height="540" fill="#f3f6fa"/>
<text x="38" y="61" class="heading">A diagonal can change what counts as a cavity</text>
<text x="38" y="95" class="small">Synthetic connectivity demonstration · no dataset, trained model or held answers</text>
{''.join(panels)}
<text x="38" y="506" class="small">The program is shared across demonstrations; every non-cavity cell keeps its original color.</text>
</svg>\n'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Fresh .svg path; existing files are preserved")
    args = parser.parse_args()
    path = Path(args.output)
    if path.suffix.lower() != ".svg":
        raise ValueError("output must be a new .svg file")
    svg = render_svg()
    with path.open("x", encoding="utf-8") as stream:
        stream.write(svg)


if __name__ == "__main__":
    main()
