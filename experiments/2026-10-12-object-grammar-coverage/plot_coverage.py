"""Render the measured ARC2 rejection partition from aggregate evidence only."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(data_path, svg_path, png_path=None):
    raw = data_path.read_bytes()
    data = json.loads(raw)
    assert data["measurement_status"] == "ACTUAL_COMPLETE_FROZEN_DIAGNOSTIC"
    assert data["panel"]["tasks"] == 120 and data["panel"]["queries"] == 172
    assert data["task_counts"]["tasks_frozen_counter_parity"] == 120
    gates = data["counts"]["gates"]
    groups = [
        ("Demonstration states\nQuery selection gate relaxed", gates["unique_demo_outputs"],
         [gates["demo_unique_shape_reject"], gates["demo_unique_recolor_conflict"], gates.get("demo_unique_exact_fit", 0)]),
        ("Full states\nOriginal query selection gate", data["counts"]["legacy_counts"]["unique_program_outputs"],
         [gates["full_unique_shape_reject"], gates["full_unique_recolor_conflict"], gates.get("full_unique_exact_fit", 0)]),
    ]
    for _, denominator, values in groups:
        assert sum(values) == denominator
    assert groups[0][1] == 20101 and groups[1][1] == 20019
    assert all(values[2] == 0 for _, _, values in groups)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                         "svg.fonttype": "none", "axes.spines.top": False,
                         "axes.spines.right": False, "axes.spines.left": False})
    fig, ax = plt.subplots(figsize=(12, 5.8))
    fig.patch.set_facecolor("#f7f9fc")
    ax.set_facecolor("#f7f9fc")
    colors = ["#315f88", "#db8b36", "#36846b"]
    labels = ["Shape mismatch", "Color map conflict", "Exact fit"]
    for y, (_, denominator, values) in enumerate(groups):
        left = 0
        for value, color, label in zip(values, colors, labels):
            width = 100 * value / denominator
            ax.barh(y, width, left=left, height=0.43, color=color,
                    label=label if y == 0 else None)
            if value:
                ax.text(left + width / 2, y, f"{value:,}\n{width:.1f}%",
                        color="white", ha="center", va="center", fontweight="bold")
            left += width
        ax.text(102, y, f"0 exact\n/{denominator:,} states", va="center", color="#24433b")
    ax.set_yticks(range(len(groups)), [label for label, _, _ in groups])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Fraction of distinct rendered states within each stated denominator")
    ax.tick_params(axis="y", length=0, pad=12)
    ax.legend(ncols=3, loc="upper left", bbox_to_anchor=(0, -0.23), frameon=False)
    fig.suptitle("No exact demonstration fits under the tested object grammar",
                 x=0.06, ha="left", y=0.97, fontsize=18, fontweight="bold", color="#19364e")
    fig.text(0.06, 0.875, "All 120 exposed evaluation tasks · 172 query inputs · query answers unopened",
             fontsize=12, color="#41586a")
    digest = hashlib.sha256(raw).hexdigest()
    fig.text(0.06, 0.065, "Actual frozen diagnostic: 120/120 counter matches; 0/120 tasks with a demo-only fit.\n"
             "These are grammar-coverage counts, not accuracy, GPU performance, or an official score.",
             color="#41586a", fontsize=10)
    fig.text(0.06, 0.022, "Aggregate data SHA256 " + digest, color="#5b6d7d", fontsize=8)
    fig.subplots_adjust(left=0.33, right=0.83, top=0.79, bottom=0.33)
    for path, format_name in ((svg_path, "svg"), (png_path, "png")):
        if path is None:
            continue
        buffer = io.BytesIO()
        metadata = {"Date": None, "Description": "Measured aggregate predicate counts; input data SHA256 " + digest} if format_name == "svg" else None
        fig.savefig(buffer, format=format_name, dpi=180, metadata=metadata)
        with path.open("xb") as stream:
            stream.write(buffer.getvalue())
    plt.close(fig)
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=pathlib.Path)
    parser.add_argument("--svg", required=True, type=pathlib.Path)
    parser.add_argument("--png", type=pathlib.Path)
    args = parser.parse_args()
    print("aggregate_data_sha256", render(args.data, args.svg, args.png))


if __name__ == "__main__":
    main()
