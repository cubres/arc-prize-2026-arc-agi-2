# Connected-object rules: two measured new solves

An original object-selection supplement solved **4 of 200 public-training
tasks**, against **2 of 200** for the exact owned `baseline37`. The paired result
is **2 gains, 0 losses**, with two natural object activations and no caps. The
complete screen included 214 queries and took 33.341669 CPU seconds, of which
7.016316 were spent on object rules. No native Kaggle run or official submission
was made for this successor. Complementarity with the credited 31.11 neural
control remains unmeasured.

![Measured complete-panel result](measured-object-screen.svg)

We froze source, baseline, protocol and a private filename/hash manifest before
downloading grids. The panel contains the 200 official public-training tasks
left after excluding 800 previously screened tasks. This is a process-disjoint
screen, not a guarantee of historical human or model non-exposure. The worker
received demonstration outputs and query inputs only; task IDs were withheld
from the solver. A separate evaluator opened query truths after all predictions
and their hash seal were saved. No task identifiers, grids, held answers or
per-task results are distributed in this public packet.

The baseline searches whole-grid geometry, cropping, contraction, scaling and
simple panel logic. It has no connected-object selection. The new finite
grammar finds foreground components under zero/majority/border backgrounds,
four/eight connectivity and monochrome/multicolor grouping. A rule selects a
unique extremal area/extent, unique shape/color group or geometric extremum;
ties abstain. It crops, isolates, retains or erases the selected object, applies
a dihedral transform, and fits an observed-key color mapping. Every surviving
rule must fit every demonstration exactly. Query colors must be supported by
the fitted mapping, except for the color-identity mapping. Programs are ordered
by a fixed enumeration and deduplicated by their complete joint query outputs.

The winning rules were largest multicolor-component crop and smallest
monochrome-component crop. This is a descriptive post-screen summary, not a
change to the frozen grammar or evidence of hidden-set performance. Two paired
wins are small evidence; the result qualifies a subsequent controlled native
diagnostic, not an official-score improvement.

Use Python and NumPy. `object_selector.solve(task, seconds=0.4)` accepts exactly
`train` demonstration pairs and `test` input-only pairs. It rejects query
outputs and metadata. It returns complete demonstration-consistent joint
candidate grids, counters, CPU time and stop reason. The object budget is
cooperative; our screening worker additionally used POSIX CPU limits and an
access-audit hook after imports and challenge reads. That hook is an inspected
process boundary, not an OS sandbox or authentication proof.

```bash
python -B invented_controls.py
python -B adapter_controls.py
python -B make_plot.py
```

Fourteen invented object controls and five native-pair controls passed. Those
establish implemented behavior only, separately from the real 200-task result.
`PUBLIC_AGGREGATE_RESULT.json` and `FROZEN_PROTOCOL.json` contain measured
aggregate results and source/budget/provenance pins, with no real task data.

`native_overlay.py` is a **source-only integration proposal** for the existing
strong-reference campaign. It reuses only a current run's owned native pools,
requires the unchanged KGMoN control to reproduce its sealed JSON exactly, and
uses exactly the control's hash-bound registered query inventory. A normal
non-rerun smoke control cannot add object guesses to the other evaluation
tasks' constructor placeholders. An official rerun must register the whole
challenge inventory. Its pair adapter preserves both
existing slots, including a duplicate pair and a legitimate `[[0]]` grid. It
uses actual ranking cardinality to identify missing slots. At most two guesses
remain per query. It writes a separate complete private treatment JSON and
receipt; it has no official object-export path. The full native function was
not executed in this experiment. Its 120-second leftover wall budget must fit
the existing build deadline and whole-machine quota gate, with all skipped
tasks reported. A full native pair, exact truth evaluation, loaded-source
checks and root review are required before any official adoption.

The conceptual object-selection strategy is credited to
[BlackCat V2](https://www.kaggle.com/code/lucifer19/arc-agi-2-blackcat-raw-signal-challenger?scriptVersionId=341435188),
source SHA256 `a2f3b8d07805cffecf57e15711ab75f9cd866f471aa0e4256b8abb04e12328fc`,
with Apache 2.0 notebook terms in the retained 11 October primary-source audit.
Its hybrid score does not isolate the effect of its object rules. This object
implementation and native wrapper are independently written; no third-party
solver, model weights or attached corpus code are redistributed or executed.
The owned baseline37 retains its prior MIT terms in `BASELINE_LICENSE`.
New original files are Apache-2.0. Official ARC public-training source was
pinned to commit `f3283f727488ad98fe575ea6a5ac981e4a188e49` and checked against
Git blob hashes; its [Apache 2.0 license](https://raw.githubusercontent.com/arcprize/ARC-AGI-2/f3283f727488ad98fe575ea6a5ac981e4a188e49/LICENSE)
was verified. No evaluation or hidden competition task data was used.
