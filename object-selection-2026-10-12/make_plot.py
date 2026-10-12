"""Measured aggregate scientific plot, no task identifiers or grids."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
result=json.loads((HERE/"PUBLIC_AGGREGATE_RESULT.json").read_bytes())
counts=result["counts"]
fig,axes=plt.subplots(1,2,figsize=(8.4,3.5),gridspec_kw={"width_ratios":[1.5,1]})
fig.set_facecolor("#fbfaf7")
for ax in axes:
    ax.set_facecolor("#fbfaf7")
    ax.spines[["top","right"]].set_visible(False)
axes[0].bar(["Exact baseline37","Object fill-only"],[counts["baseline_task_solves"],counts["treatment_task_solves"]],color=["#8995a4","#207c73"],width=.58)
axes[0].set_ylabel("All-query exact task solves / 200")
axes[0].set_ylim(0,5)
axes[0].set_yticks(range(6))
for x,n in enumerate([counts["baseline_task_solves"],counts["treatment_task_solves"]]):
    axes[0].text(x,n+.12,str(n),ha="center",fontweight="bold",fontsize=13)
axes[1].bar(["Gains","Losses"],[counts["paired_task_wins"],counts["paired_task_losses"]],color=["#207c73","#ba6049"],width=.55)
axes[1].set_ylim(0,5); axes[1].set_yticks(range(6)); axes[1].set_ylabel("Paired task outcomes")
for x,n in enumerate([counts["paired_task_wins"],counts["paired_task_losses"]]):
    axes[1].text(x,n+.12,str(n),ha="center",fontweight="bold",fontsize=13)
fig.suptitle("Connected-object rules filled two genuinely spare guesses",fontweight="bold",fontsize=12,y=.98)
fig.text(.5,.018,"200 process-disjoint public-training tasks · 214 queries · 33.34 CPU s · no caps\nHistorical exposure unknown; neural 31.11 complementarity and official score unmeasured.",ha="center",fontsize=8,color="#4b5563")
fig.tight_layout(rect=(0,.11,1,.94))
fig.savefig(HERE/"measured-object-screen.svg")
fig.savefig(HERE/"measured-object-screen.png",dpi=180)
plt.close(fig)
print("SAVED measured aggregate SVG + PNG")
