"""Draw the measured aggregate and prediction/answer boundary.

Only aggregate_result.json is read. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, help="new output directory; existing paths are refused")
    args = parser.parse_args()
    raw = (pathlib.Path(__file__).resolve().parent / "aggregate_result.json").read_bytes()
    data = json.loads(raw)
    result = data["result"]
    counts, coverage = result["counts"], result["input_only_coverage"]
    tasks, queries = result["complete_tasks"], counts["queries"]
    if tasks != 120 or queries != 172 or not result["query_answers_first_opened_after_complete_prediction_seal"]:
        raise ValueError("figure requires the qualified complete panel and answer boundary")
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "font.size": 10})
    fig = plt.figure(figsize=(12.2, 8.3), facecolor="#f8fafc")
    pipeline = fig.add_axes([0.045, 0.49, 0.91, 0.41])
    pipeline.set(xlim=(-0.1, 10), ylim=(0, 4.8))
    pipeline.axis("off")
    fig.suptitle("Two finite relational grammars: zero natural activation", x=0.045, ha="left",
                 y=0.975, fontsize=19, weight="bold", color="#0f172a")
    fig.text(0.045, 0.92, "Completed exposed development panel • 120 tasks / 172 queries • 12 October 2026",
             color="#475569", fontsize=11)

    def box(x, y, width, height, title, body, color="#e2e8f0"):
        pipeline.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.06,rounding_size=0.1",
                                         linewidth=1, edgecolor="#94a3b8", facecolor=color))
        pipeline.text(x + 0.15, y + height - 0.30, title, weight="bold", color="#0f172a", va="top", fontsize=11)
        pipeline.text(x + 0.15, y + height - 0.82, body, color="#334155", va="top", fontsize=10, linespacing=1.5)

    def arrow(x1, y1, x2, y2, color="#64748b"):
        pipeline.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=15,
                                          linewidth=1.5, color=color))

    box(0.0, 2.9, 2.2, 1.5, "Challenge only", "Public demo input/output\nQuery INPUTS only", "#dbeafe")
    box(2.6, 2.9, 3.05, 1.5, "Finite demonstration fit", "Interval: 0 / 120 tasks\nRepeated group: 0 / 120", "#e0e7ff")
    box(6.1, 2.9, 3.65, 1.5, "Query applicability", "Checked only after demo fit\nNew candidate tasks: 0 / 120", "#e0e7ff")
    arrow(2.25, 3.65, 2.53, 3.65)
    arrow(5.72, 3.65, 6.03, 3.65)
    box(0.0, 0.55, 2.9, 1.6, "Invented controls", "13 positive / negative checks pass\nSemantic + storage guards pass", "#dcfce7")
    box(3.4, 0.55, 2.65, 1.6, "Complete prediction freeze", "120 tasks / 172 queries\nNo caps, incomplete search,\nor storage truncation", "#dbeafe")
    box(6.55, 0.55, 3.2, 1.6, "Separate answer stage", "Seal verified before answer read\nExact at two: 0 / 172 in both arms\nPaired wins / losses: 0 / 0", "#ffedd5")
    arrow(2.98, 1.3, 3.32, 1.3)
    arrow(6.12, 1.3, 6.47, 1.3)
    arrow(7.9, 2.82, 4.75, 2.24)
    pipeline.plot([6.30, 6.30], [0.28, 2.45], color="#c2410c", linestyle="--", linewidth=1.5)
    pipeline.text(6.3, 0.0, "ANSWER BOUNDARY", ha="center", color="#9a3412", fontsize=9, weight="bold")

    axes = fig.add_axes([0.27, 0.13, 0.58, 0.31])
    labels = ["Interval demo fit", "Repeated-group demo fit", "New-family candidates", "Baseline query solves", "Treatment query solves"]
    values = [coverage["interval_paint_demo_fit_tasks"], coverage["repeated_group_demo_fit_tasks"],
              counts["natural_structural_activation_tasks"], counts["baseline_query_solves"], counts["treatment_query_solves"]]
    denominators = [tasks, tasks, tasks, queries, queries]
    for index, (value, denominator) in enumerate(zip(values, denominators)):
        axes.barh(index, 1, color="#e2e8f0", height=0.52)
        axes.barh(index, value / denominator, color="#2563eb", height=0.52)
        axes.scatter([value / denominator], [index], color="#2563eb", s=24, zorder=4)
        axes.text(1.04, index, f"{value} / {denominator}", va="center", weight="bold", color="#0f172a")
    axes.set(yticks=range(len(labels)), yticklabels=labels, xlim=(-0.025, 1.03),
             xticks=[0, 0.25, 0.5, 0.75, 1], xticklabels=["0%", "25%", "50%", "75%", "100%"])
    axes.invert_yaxis()
    axes.set_title("Observed fraction of each complete denominator", loc="left", fontsize=11, weight="bold", pad=13)
    axes.tick_params(axis="both", length=0)
    axes.grid(axis="x", color="white", linewidth=1.5)
    axes.set_axisbelow(False)
    for spine in axes.spines.values():
        spine.set_visible(False)
    axes.set_facecolor("#f8fafc")
    fig.text(0.045, 0.067, "Controls validate implementation. Zero real demonstration fits stop this grammar route; neural/TTA remains unmeasured.",
             fontsize=10, color="#334155")
    short_hash = hashlib.sha256(raw).hexdigest()
    fig.text(0.045, 0.035, "Data SHA-256: " + short_hash, fontsize=7.5, color="#64748b")
    description = "Original plot of qualified public aggregate; data SHA-256 " + short_hash
    fig.savefig(out / "relational_coverage.svg", metadata={"Creator": "cubres original aggregate plot", "Description": description}, facecolor=fig.get_facecolor())
    fig.savefig(out / "relational_coverage.png", dpi=160, metadata={"Software": "cubres original aggregate plot", "Description": description}, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
