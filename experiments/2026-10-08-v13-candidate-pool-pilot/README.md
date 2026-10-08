# 8 public tasks, one solve: the candidate pool held the answer when the recipe found it

On 8 October we ran the first preregistered pilot of the credited control recipe on public-evaluation tasks. The recipe is the [credited control rerun](../../official-submissions/2026-10-08-v12-credited-rerun/README.md) of `koushikrudra/failed-in-aimo` V1 (Apache-2.0). Its recipe cells are unchanged; only the task list is set for the pilot. The pilot asks a narrow question: where does the recipe's final answer come from? It is a descriptive measurement. No competition submission was made, and nothing here is a leaderboard claim.

*Updated 2026-10-08 after the solver timeline and the candidate pool files were fetched. The stop causes and timings below replace the first draft's inferences.*

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

- **Selection headroom (U1 = 0 of 13).** Only one output, in 45a5af55, had its true grid anywhere in the pool. The recipe's KGMoN rule ranked it first, so no output had the answer in the pool but outside the top two. The probmul alternative (`score_full_probmul_3`, the recipe's own selector) gave the same top two as KGMoN for all 12 outputs with a pool. On these tasks it changes no submitted attempt, so this pilot neither supports nor refutes the public-log gain that motivated it.
- **Time to answer (U2).** The one correct candidate first appeared 240.8 s after its task started, at the end of the task's first decode batch (that batch ran from 168.5 s to 240.8 s). Sixteen pool files hold its true grid. The earliest was written at 240.8 s, and later copies at 308.4, 376.2 and 444.4 s. U2 holds on one solve, which is too few to say more.
- **Agreement with the public run.** A full public run of the same recipe by rokaiyasomapti (120 tasks) solved only `45a5af55` among these eight tasks. Our run agrees on all 13 outputs. The exact 95% upper bound on the discordance rate is 0.25.

## Time per task

Across the eight tasks the median was 640 s, the 90th percentile about 1,083 s and the mean 699 s. Five tasks ran to completion. Three stopped early, and the log shows why:

- **221dfab4 stopped at its per-task budget.** It stopped at 1,208.8 s, about 290 s before the pilot's estimated global end time, so the budget, not the global end, stopped it. The budget is checked only between decode batches. The last batch overran it by 8.8 s.
- **a32d8b75 (1,029 s) and cb2d8a2c (310 s) stopped at the global end.** Both stopped below the per-task budget, so the global soft end of 1,800 s stopped them.

## Harness notes

- The pilot's timeout flag lumped two causes together: a task reaching its own budget, and the global end time passing. The next evaluator labels each stop by its cause.
- The global soft end of 1,800 s cut two of eight tasks, and each of the four workers had room for only two tasks in that window. The second output of cb2d8a2c produced no candidates. If a next pilot runs, it uses one 9,000 s session.
- The solver timeline and the candidate pool files were fetched after the first draft of this note. They confirm the stop causes and timings above. The pool files hold candidate grids, so they are not published.

## Gate, and what follows

The plan's gate was: build the next panel if the selection headroom (U1) or the time-to-answer result (U2) is positive. U2 is positive on one solve, so the gate is met weakly. The 24-task continuation (positions 9 to 32 of the same order) is built offline and has passed its dry-run check. It has not been run. It is parked until after the 2026-10-10 00:00 UTC quota reset. The pilot suggests pool generation, not selection, is the bottleneck, because U1 is 0 of 13 [inferred].

**Version 19b of the public notebook (prepared, not run).** Both submitted attempts come from `score_full_probmul_3` over the same pools, instead of the top two of KGMoN. The scoring seed is pinned: `zlib.crc32` of the puzzle key, `PYTHONHASHSEED=0`, and a per-puzzle reseed of the random generators. A full commit run is planned after the 2026-10-10 reset; it has not been run. Version 18 stays the public version until a Version 19b run validates. The paired public runs average about +1.0 points in favour of the probmul selector, as their authors display them. Our pilot found identical top-two sets, so the expected effect is small, and we have not measured it.

## Files

- `evaluation.json`: per-task and per-output exact flags, pool counts and ranks. No grids, no ground truth.
- `freeze-manifest.json`: what was frozen before evaluation, with hashes.
- `gate-numbers.json`: the numbers in this note, per output, plus sha256 of the raw receipts the numbers came from. The candidate grids and the solutions are not included.

Credits: the recipe is Koushik Rudra's `failed-in-aimo` V1 (Apache-2.0) on Ivan Sorokin's Apache-2.0 model `sorokin/qwen3_4b_grids15_sft139`. The public comparison run is by rokaiyasomapti (`reproduce-nvarc-2025-results`).
