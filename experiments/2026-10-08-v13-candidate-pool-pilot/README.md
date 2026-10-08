# 8 public tasks, one solve: the candidate pool held the answer when the recipe found it

On 8 October we ran the first preregistered pilot of the credited control recipe on public-evaluation tasks. The recipe is the [credited control rerun](../../official-submissions/2026-10-08-v12-credited-rerun/README.md) of `koushikrudra/failed-in-aimo` V1 (Apache-2.0). Its recipe cells are unchanged; only the task list is set for the pilot. The pilot asks a narrow question: where does the recipe's final answer come from? It is a descriptive measurement. No competition submission was made, and nothing here is a leaderboard claim.

## What ran

Eight tasks were chosen before anything ran: the first eight of the public-evaluation tasks in the order of `sha256("arc2-v13-pilot-20261008:" + task_id)`, excluding one task used in an earlier run. The panel holds 13 test outputs. The recipe ran unchanged on four L4 GPUs, except that the commit-run task list came from the panel. Every solver line was timestamped. Candidate pools were copied with their file times. Selection then ran in a separate process that could not read the solutions. Its predictions and an alternative ranking were frozen with sha256 hashes. Only after that did a separate evaluator read the public solutions.

| Measurement | Value |
|---|---:|
| Solver elapsed, 4 workers (owned, PASS) | 1,795 s |
| Selection and evaluation (owned, PASS) | 30 s and 1 s |
| Outputs solved exactly | 1 of 13 (one task, `45a5af55`) |
| Candidate samples in the pools | 94 (in 79 pool files) |
| Solutions opened before the freeze | none (`solutions_opened: false`) |

## What the pilot measured

- **Selection headroom.** Only one output, in 45a5af55, had its true grid anywhere in the pool. The recipe's KGMoN rule ranked it first, so no output had the answer in the pool but outside the top two. The probmul alternative (`score_full_probmul_3`, the recipe's own selector) gave the same top two as KGMoN for all 12 outputs with a pool. On these tasks it changes no submitted attempt, so this pilot neither supports nor refutes the public-log gain that motivated it.
- **Time to answer.** The one correct candidate first appeared 241 s after its task started. One solve is too few to say more.
- **Agreement with the public run.** A full public run of the same recipe by rokaiyasomapti (120 tasks) solved only `45a5af55` among these eight tasks. Our run agrees on all 13 outputs. The exact 95% upper bound on the discordance rate is 0.25.

## Time per task

Across the eight tasks the median was 640 s, the 90th percentile about 1,083 s and the mean 699 s. One task ran 1,209 s, just over the 1,200 s per-task budget. The recipe checks that budget between decode batches, so a task can overrun it by one batch. Two more tasks stopped below their budget. The recipe's loop stops a task early only at the global end time, so both were most likely cut by the 1,800 s soft end [inferred from the recipe's loop; the solver log has not been checked].

## Harness notes

- The timeout flag in this pilot lumped together two causes: a task reaching its own budget, and the global end time passing. The next evaluator labels them separately.
- The soft end of 1,800 s was too short for this panel. Two of eight tasks were probably cut by it, and one output produced no candidates. The next pilot uses one 9,000 s session.
- The solver timeline and the candidate pool files are in the kernel output but were not copied into the local record. They need to be fetched before any timing analysis of the next pilot.

## Gate for the next pilot

The plan's gate was "build the next panel if the selection headroom or the time-to-answer result is positive". The time-to-answer condition holds, but only on one solve, so the gate is met weakly. The 24-task continuation (positions 9 to 32 of the same order) is built offline and passed its dry-run check. It has not been run. A public successor with the probmul selector and pinned seeds is also prepared offline. Under the plan, that change is measured on the bench panel before any public version is published.

## Files

- `evaluation.json`: per-task and per-output exact flags, pool counts and ranks. No grids, no ground truth.
- `freeze-manifest.json`: what was frozen before evaluation, with hashes.
- `gate-numbers.json`: the numbers in this note, per output, plus sha256 of the raw receipts the numbers came from. The candidate grids and the solutions are not included.

Credits: the recipe is Koushik Rudra's `failed-in-aimo` V1 (Apache-2.0) on Ivan Sorokin's Apache-2.0 model `sorokin/qwen3_4b_grids15_sft139`. The public comparison run is by rokaiyasomapti (`reproduce-nvarc-2025-results`).
