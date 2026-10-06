"""Render a schematic from the actual standalone S1 binding; exclusive output."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
from stable_seed_binding import bind_seed


def render() -> str:
    example = bind_seed("00d62c1b_0")
    collision = bind_seed("collision-probe-681_0")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="660" viewBox="0 0 1280 660">',
        '<title>Portable seed binding with a separate full identity digest</title>',
        '<desc>Actual seed values from the standalone tool. Worker and eight-view boxes are schematic; augmentation and model scoring are not implemented.</desc>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#128b87"/></marker></defs>',
        '<rect width="1280" height="660" fill="#f2f6f7"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#16333d}.title{font-size:31px;font-weight:700}.sub{font-size:16px;fill:#45636c}.label{font-size:14px;font-weight:700;fill:#128b87}.body{font-size:17px}.mono{font-family:monospace;font-size:14px}.small{font-size:13px;fill:#45636c}.seed{font-family:monospace;font-size:28px;font-weight:700}</style>',
        '<text x="48" y="53" class="title">One exact key. One portable seed.</text>',
        '<text x="48" y="83" class="sub">A domain-separated SHA-256 rule, with the full payload digest retained beside the 20-bit seed.</text>',
        '<rect x="48" y="110" width="350" height="135" rx="14" fill="white" stroke="#d5e2e5"/>',
        '<text x="68" y="140" class="label">EXACT PAYLOAD BYTES</text>',
        '<text x="68" y="169" class="mono">b"arc2-rescore-seed-v1\\0"</text>',
        '<text x="68" y="194" class="mono">+ original_bk.encode("utf-8")</text>',
        '<text x="68" y="220" class="small">No trimming, normalization, worker ID or score.</text>',
        '<path d="M406 178 H440" stroke="#128b87" stroke-width="3" marker-end="url(#arrow)"/>',
        '<rect x="457" y="110" width="440" height="135" rx="14" fill="white" stroke="#d5e2e5"/>',
        '<text x="477" y="140" class="label">SHA-256 FULL PAYLOAD DIGEST</text>',
        f'<text x="477" y="174" class="mono">{escape(example.payload_sha256[:32])}</text>',
        f'<text x="477" y="198" class="mono">{escape(example.payload_sha256[32:])}</text>',
        '<text x="477" y="225" class="small">Example key: 00d62c1b_0</text>',
        '<path d="M905 178 H940" stroke="#128b87" stroke-width="3" marker-end="url(#arrow)"/>',
        '<rect x="956" y="110" width="276" height="135" rx="14" fill="#e2f4ee" stroke="#95cfc0"/>',
        '<text x="976" y="140" class="label">BIG-ENDIAN INTEGER mod 2²⁰</text>',
        f'<text x="976" y="187" class="seed">{example.seed}</text>',
        '<text x="976" y="222" class="small">Reduced seed is not a unique identity.</text>',
        '<text x="48" y="288" class="label">FRESH WORKERS / DIFFERENT PYTHON HASH SETTINGS</text>',
    ]
    for index, worker in enumerate(("Worker A", "Worker B", "Worker C")):
        y = 310 + index * 62
        parts += [
            f'<rect x="48" y="{y}" width="235" height="47" rx="9" fill="white" stroke="#d5e2e5"/>',
            f'<text x="65" y="{y+29}" class="body">{worker} · exact same key</text>',
            f'<path d="M292 {y+24} H335" stroke="#128b87" stroke-width="2" marker-end="url(#arrow)"/>',
            f'<rect x="352" y="{y}" width="176" height="47" rx="9" fill="#e2f4ee" stroke="#95cfc0"/>',
            f'<text x="377" y="{y+30}" class="mono">seed = {example.seed}</text>',
        ]
    parts += [
        '<path d="M540 396 H592" stroke="#128b87" stroke-width="3" marker-end="url(#arrow)"/>',
        '<rect x="614" y="306" width="618" height="185" rx="14" fill="white" stroke="#d5e2e5" stroke-dasharray="7 5"/>',
        '<text x="636" y="336" class="label">EXTERNAL AUGMENTATION CONTRACT — NOT IMPLEMENTED HERE</text>',
        '<text x="636" y="364" class="body">Keep all eight ordered views, including duplicates.</text>',
    ]
    for index in range(8):
        x = 641 + index * 71
        parts += [
            f'<rect x="{x}" y="384" width="58" height="52" rx="7" fill="#eef4f6" stroke="#d5e2e5"/>',
            f'<text x="{x+11}" y="415" class="mono">v{index}</text>',
        ]
    parts += [
        '<text x="657" y="463" class="small">First four scoring views</text>',
        '<text x="948" y="463" class="small">Second four scoring views</text>',
        '<rect x="48" y="524" width="1184" height="77" rx="12" fill="#fff4df" stroke="#e9d6ae"/>',
        '<text x="67" y="551" class="label">COLLISION WITNESS: A REDUCED SEED MUST NOT KEY AN IDENTITY LEDGER</text>',
        f'<text x="67" y="580" class="mono">collision-probe-681_0 and collision-probe-1298_0 → {collision.seed}; different full payload digests.</text>',
        '<text x="48" y="637" class="small">Schematic only. No native ARC2 execution, model scoring, speed measurement, answer-quality or generalization claim.</text>',
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new SVG file; must not exist")
    args = parser.parse_args()
    with Path(args.output).open("x", encoding="utf-8") as stream:
        stream.write(render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
