"""Render the measured public negative result from its JSON receipt. MIT."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "public_evaluation.json").read_text())
fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
labels = ["Reference recipe", "Original symbolic", "Fill-only merge"]
keys = ["base", "symbolic", "fill_merge"]
values = [result["metrics"][key]["exact_outputs"] for key in keys]
axes[0].barh(labels, values, color=["#355f7a", "#d4854d", "#355f7a"])
axes[0].set_xlim(0, result["outputs"])
axes[0].set_xlabel(f"Exact test outputs out of {result['outputs']}")
for i, value in enumerate(values):
    axes[0].text(value+2, i, str(value), va="center")
axes[0].invert_yaxis()
axes[0].spines[["top", "right"]].set_visible(False)
axes[1].axis("off")
axes[1].text(0, 0.90, "A cheap hypothesis that failed", weight="bold", fontsize=15)
axes[1].text(0, 0.70, "120 tasks predicted in 3.74 CPU seconds.\n0 tasks had an exact demonstration fit\nwithin this finite grammar.", fontsize=12, linespacing=1.6)
axes[1].text(0, 0.36, "No new correct output, even with an oracle union.\nKeep the method as a reproducible negative result.\nDo not spend Kaggle quota on this grammar.", fontsize=11, linespacing=1.6)
axes[1].text(0, 0.06, "Exposed public evaluation; no official-score claim.", fontsize=10, color="#555555")
fig.savefig(HERE / "public_negative_result.png", dpi=170)
fig.savefig(HERE / "public_negative_result.svg")
