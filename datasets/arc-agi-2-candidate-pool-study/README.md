# ARC-AGI-2 TTT Candidate Pools: an 8-task pilot

## What

This dataset holds every candidate grid, score and selection from one pilot run of a test-time training (TTT) solver on eight ARC-AGI-2 public evaluation tasks. The solver is the public recipe `koushikrudra/failed-in-aimo` (version 1) on Kaggle. It fine-tunes a small LoRA adapter on each task's own examples, then decodes the test outputs with beam search. Each decoded grid is re-scored on eight augmented queries.

The files are a flat CSV and JSON Lines form of the candidate pools, the two selection rules compared on identical pools, the evaluator's per-output scoring, the solver's timeline, and a fill-calibration table for a planned second pass over weak outputs. The run solved one of 13 test outputs. It is a descriptive pilot, not a leaderboard or benchmark result.

The dataset contains no ARC-AGI-2 task inputs and no public answers. Task ids are included so that each row can be matched to the public tasks on the competition page.

## Why

- **Candidate pools with scores.** Every decoded grid, with its beam score and its eight augmented-query scores, in flat CSV and in nested JSON. Each grid has a SHA-256 hash, so a grid can be matched to a public answer by anyone who holds that answer.
- **Two selection rules on identical pools.** KGMoN and `score_full_probmul_3` are recorded for the same pools. In this pilot they agree on every decoded output, so the run cannot tell them apart. It is a template for a larger panel, not a verdict on either rule.
- **Timing of TTT on L4 GPUs.** Per-task seconds, per-batch timelines and the two stop causes (per-task cap and global end time), with the stop rule and the clock bracket written out.
- **A fill-calibration template.** The weak-output rule, the second-slot hit rate with a Wilson interval, and a Beta prior for a fill pass. The public-run counts come from a third-party public run, named under Provenance.
- **A restricted pickle reader.** `code__pool_to_jsonl.py` loads numpy-in-pickle files while allowing only the numpy array constructors. It is provenance code; see Files.

## Files

Every file sits at the top level of the dataset. Sub-folders were flattened, so a file that was `data/outputs.csv` is `data__outputs.csv`. Paths below are relative to the dataset root.

Tables (columns are listed in the Columns section):

- `data__candidate_pool_samples.csv`: one row per decoded grid (94 rows, 21 columns). The easiest table to load.
- `data__candidate_pools.jsonl`: the same samples nested by pool file (79 lines), with every field of the original pool files.
- `data__candidate_pools_index.csv`: one row per pool file (79 rows, 11 columns).
- `data__outputs.csv`: one row per test output (13 rows, 27 columns): solved flags, selector ranks, timings and the weak-output flag.
- `data__predictions.jsonl`: the final two attempts for each of the 13 test outputs (13 lines).
- `data__selection_alternatives.jsonl`: the top four candidates under each selector, for the 12 decoded outputs (12 lines).
- `data__solver_log.jsonl`: the solver's log lines with unix timestamps and GPU rank, so the timeline can be rebuilt (183 lines).
- `data__decode_batches.csv`: one row per decode batch (42 rows, 7 columns).
- `data__task_summary.csv`: one row per panel task (8 rows, 13 columns): timing, decode batches, evaluator score and stop cause.

Records (JSON objects, not tables):

- `data__evaluation.json`: the evaluator's frozen output, unmodified. Top-level keys: `schema`, `scope`, `evaluated_unix`, `solutions_sha256`, `freeze_manifest`, `summary`, `tasks`.
- `data__freeze_manifest.json`: the freeze record, unmodified. Keys: `alternatives_sha256`, `decoded_base_keys`, `frozen_unix`, `panel`, `predictions_sha256`, `solutions_opened`.
- `data__run_summary.json`: stage statuses and elapsed times, deadlines, hardware and a note. Keys: `schema`, `source_schema`, `panel`, `pool_files`, `stages`, `solver_started_after_seconds`, `finished_after_seconds`, `deadlines_seconds`, `hardware`, `note`.
- `data__fill_calibration.json`: the weak-output counts, second-slot hit rate and Beta prior for a fill pass. Keys: `note`, `p_fill_prior`, `public_run` (counts from a third-party public run, with its source), `pilot_outputs` (the 13 pilot outputs), `schema`, `views_per_output`.
- `data__analysis_extra.json`: output of the analysis script, byte-identical to its source (only the file name was changed). Keys: `end_offset_from_last_line_s`, `end_time_estimate_stamp`, `log_lines`, `per_output`, `pool_files`, `pool_rows`, `pool_samples_total`, `schema`, `solver_last_stamp`, `timeline`.

Code and documentation:

- `code__pool_to_jsonl.py`: restricted pickle reader and converter (provenance). It produced `data__candidate_pools.jsonl` from the 79 pickles. The pickles, the public answers and the index are not in this dataset, so the script cannot be run from this folder alone.
- `README.md`: this card. `NOTICE.md`: per-file terms and third-party inputs. `LICENSE`: the Apache License 2.0 text. `MANIFEST.json`: the SHA-256 and byte size of every other file in this dataset. `dataset-metadata.json`: the Kaggle metadata.

## Columns

Every column of every table is listed below. The types and meanings are the same as the Kaggle schema in `dataset-metadata.json`. Booleans are written as `true` and `false`; blank cells mean "not applicable or not recorded", as described for each column.

### `data__candidate_pool_samples.csv` (21 columns)

- `pool_file` (string): Pool file name: the output_id, then the geometric chain, then permute and ten colour digits, then ex and the example-order digits, joined by dots
- `output_id` (string): Test output id: task_id plus test_output_index
- `task_id` (string): ARC-AGI-2 public evaluation task id
- `test_output_index` (integer): Which test input of the task, 0 or 1
- `rank_in_file` (integer): 0-based position of the sample in its pool file
- `beam_score` (number): Recipe beam score for the decoded grid, unitless; lower is more confident
- `score_aug_1` (number): Augmented-query score 1 of 8 for the grid, unitless; lower is more confident
- `score_aug_2` (number): Augmented-query score 2 of 8, unitless
- `score_aug_3` (number): Augmented-query score 3 of 8, unitless
- `score_aug_4` (number): Augmented-query score 4 of 8, unitless
- `score_aug_5` (number): Augmented-query score 5 of 8, unitless
- `score_aug_6` (number): Augmented-query score 6 of 8, unitless
- `score_aug_7` (number): Augmented-query score 7 of 8, unitless
- `score_aug_8` (number): Augmented-query score 8 of 8, unitless
- `grid_rows` (integer): Grid height in cells
- `grid_cols` (integer): Grid width in cells
- `grid` (string): JSON text of the grid, a list of rows of digits 0 to 9; blank when redacted
- `grid_sha256` (string): SHA-256 of the compact JSON of the grid (kept when redacted)
- `matches_public_solution` (boolean): The grid equals the ARC public answer for this output
- `grid_redacted` (boolean): The grid is blank because it equals the public answer
- `written_by_batch_end_after_task_start_s` (number): Seconds after task start when the pool file was written (end of its decode batch)

### `data__candidate_pools.jsonl` (10 top-level keys, one JSON object per line)

- `pool_file` (string): Pool file name as written by the recipe
- `output_id` (string): Test output id: task_id plus test_output_index
- `task_id` (string): ARC-AGI-2 public evaluation task id
- `test_output_index` (integer): Which test input of the task, 0 or 1
- `geometric_chain` (string): Dot-separated geometric ops (transpose, rot90) before decoding; empty means identity
- `colour_permutation` (string): Ten digits naming the colour permutation (recipe naming)
- `example_order` (string): Digits naming the sequence of training examples (recipe naming)
- `written_by_batch_end_after_task_start_s` (number): Seconds after task start when the file was written (end of its decode batch)
- `sample_count` (integer): Number of decoded samples in the file
- `samples` (array): One object per decoded sample: rank_in_file (integer), beam_score (number), score_aug (array of 8 numbers), grid_rows, grid_cols (integer), grid (array of rows of integers, or null when redacted), grid_sha256 (string), matches_public_solution and grid_redacted (boolean)

Each element of `samples` (one per decoded grid) has these keys:
- `rank_in_file` (integer): 0-based position of the sample in its pool file.
- `beam_score` (number): recipe beam score for the grid, unitless; lower is more confident.
- `score_aug` (array of 8 numbers): the eight augmented-query scores, in order, unitless; lower is more confident.
- `grid_rows` (integer), `grid_cols` (integer): grid height and width in cells.
- `grid` (array of rows of integers, or `null` when redacted): the grid, rows of digits 0 to 9.
- `grid_sha256` (string): SHA-256 of the compact JSON of the grid; kept when redacted.
- `matches_public_solution` (boolean): the grid equals the ARC public answer for its test output.
- `grid_redacted` (boolean): the grid is `null` because it equals the public answer.

### `data__candidate_pools_index.csv` (11 columns)

- `pool_file` (string): Pool file name as written by the recipe
- `output_id` (string): Test output id: task_id plus test_output_index
- `task_id` (string): ARC-AGI-2 public evaluation task id
- `test_output_index` (integer): Which test input of the task, 0 or 1
- `geometric_chain` (string): Dot-separated geometric ops before decoding; empty means identity
- `colour_permutation` (string): Ten digits naming the colour permutation (recipe naming)
- `example_order` (string): Digits naming the sequence of training examples (recipe naming)
- `sample_count` (integer): Number of decoded samples in the file
- `distinct_grids_in_file` (integer): Number of distinct grid hashes in the file
- `truth_in_file` (boolean): The file contains the ARC public answer
- `written_by_batch_end_after_task_start_s` (number): Seconds after task start when the file was written; blank if not recorded

### `data__decode_batches.csv` (7 columns)

- `task_id` (string): ARC-AGI-2 public evaluation task id
- `worker_rank` (integer): GPU rank (0 to 3) that ran the task
- `batch_index` (integer): Decode batch number within the task, 1-based
- `subkeys_in_batch` (integer): Subkeys decoded in the batch; 4 in every batch of this run
- `start_after_task_start_seconds` (number): Batch start, seconds after task start
- `end_after_task_start_seconds` (number): Batch end, seconds after task start
- `duration_seconds` (number): Batch duration in seconds

### `data__outputs.csv` (27 columns)

- `output_id` (string): Test output id: task_id plus test_output_index
- `task_id` (string): ARC-AGI-2 public evaluation task id
- `test_output_index` (integer): Which test input of the task, 0 or 1
- `pool_files` (integer): Pool files for this output (0 to 16)
- `pool_samples` (integer): Decoded samples for this output
- `distinct_candidates` (integer): Distinct decoded grids; blank if nothing was decoded
- `truth_in_pool` (boolean): The ARC public answer is in the pool
- `solved` (boolean): Exact attempt 1 or attempt 2
- `exact_attempt_1` (boolean): Attempt 1 equals the ARC public answer
- `exact_attempt_2` (boolean): Attempt 2 equals the ARC public answer
- `truth_rank_kgmon` (integer): Rank of the public answer under KGMoN (score_kgmon); blank if absent
- `truth_rank_probmul` (integer): Rank of the public answer under score_full_probmul_3; blank if absent
- `first_seen_seconds_after_task_start` (number): Seconds after task start when the public answer first appeared in a pool; blank if never
- `weak_output` (boolean): At most one distinct grid in the main pool, so the second slot is empty or duplicated
- `top1_support_views` (integer): Number of pool files (of 16 planned views) that contain the top-1 grid
- `views_per_output` (integer): Planned views per output, always 16
- `attempt_1_rows` (integer): Attempt 1 grid height
- `attempt_1_cols` (integer): Attempt 1 grid width
- `attempt_1_is_placeholder` (boolean): Attempt 1 is the placeholder [[0]]
- `attempt_1_redacted` (boolean): Attempt 1 grid is redacted
- `attempt_2_rows` (integer): Attempt 2 grid height
- `attempt_2_cols` (integer): Attempt 2 grid width
- `attempt_2_is_placeholder` (boolean): Attempt 2 is the placeholder [[0]]
- `attempt_2_redacted` (boolean): Attempt 2 grid is redacted
- `task_seconds` (number): Wall time of the task in seconds, repeated for each of its outputs
- `hit_task_timeout` (boolean): The task stopped at a stop line
- `panel_position` (integer): Order of the task in the panel, 1 to 8

### `data__predictions.jsonl` (5 top-level keys, one JSON object per line)

- `output_id` (string): Test output id: task_id plus test_output_index
- `task_id` (string): ARC-AGI-2 public evaluation task id
- `test_output_index` (integer): Which test input of the task, 0 or 1
- `attempt_1` (object): Attempt 1: grid_rows, grid_cols (integer), grid (array of rows, or null when redacted), grid_sha256 (string), matches_public_solution, grid_redacted, is_placeholder (boolean)
- `attempt_2` (object): Attempt 2, same keys as attempt_1

`attempt_1` and `attempt_2` are objects with these keys:
- `grid_rows` (integer), `grid_cols` (integer): attempt shape.
- `grid` (array of rows, or `null` when redacted): the attempt grid.
- `grid_sha256` (string): SHA-256 of the compact JSON of the grid.
- `matches_public_solution` (boolean): the attempt equals the public answer.
- `grid_redacted` (boolean): the grid is `null` because it equals the public answer.
- `is_placeholder` (boolean): the attempt is the placeholder `[[0]]`.

### `data__selection_alternatives.jsonl` (8 top-level keys, one JSON object per line)

- `output_id` (string): Test output id: task_id plus test_output_index
- `task_id` (string): ARC-AGI-2 public evaluation task id
- `test_output_index` (integer): Which test input of the task, 0 or 1
- `distinct_candidates` (integer): Distinct decoded grids for the output
- `kgmon_top4` (array): Up to four candidates ranked by KGMoN; each has rank (integer, 1 best), grid_rows, grid_cols, grid, grid_sha256, matches_public_solution, grid_redacted
- `probmul_top4` (array): Up to four candidates ranked by score_full_probmul_3; same keys as kgmon_top4
- `kgmon_top2_set_equals_probmul_top2_set` (boolean): The two selectors pick the same top-2 set
- `kgmon_top1_equals_probmul_top1` (boolean): The two selectors pick the same top-1

`kgmon_top4` and `probmul_top4` are lists of up to four objects, ranked by each selector, with these keys:
- `rank` (integer): 1 is best; rank 1 is attempt 1.
- `grid_rows` (integer), `grid_cols` (integer): grid height and width in cells.
- `grid` (array of rows, or `null` when redacted): the grid.
- `grid_sha256` (string): SHA-256 of the compact JSON of the grid.
- `matches_public_solution` (boolean): the grid equals the public answer.
- `grid_redacted` (boolean): the grid is `null` because it equals the public answer.

### `data__solver_log.jsonl` (4 keys)

- `seconds_since_first_line` (number): Seconds since the first solver log line
- `unix_time` (number): Unix time of the log line
- `rank` (integer): GPU rank 0 to 3, or null for library banners
- `text` (string): Raw log line

### `data__task_summary.csv` (13 columns)

- `task_id` (string): ARC-AGI-2 public evaluation task id
- `panel_position` (integer): Order of the task in the panel, 1 to 8
- `worker_rank` (integer): GPU rank (0 to 3) that ran the task
- `outputs` (integer): Test outputs in the task
- `reached` (boolean): The task ran
- `task_score` (number): Evaluator score for the task, 0 to 1
- `task_seconds` (number): Wall time of the task in seconds
- `train_seconds` (number): LoRA training time of the task in seconds
- `decode_batches` (integer): Decode batches run
- `hit_task_timeout` (boolean): The task stopped at a stop line
- `timeout_spend_seconds` (number): Solver time at the stop line in seconds; blank if no stop
- `timeout_cause` (string): Blank if no stop; 'per-task cap (spend above 1200 s)' or 'global end time (spend below 1200 s)'
- `break_unix_time` (number): Unix time of the stop line in the solver log; blank if no stop

## How to load

These snippets were run on the files as published. They use pandas and NumPy.

```python
import pandas as pd

samples = pd.read_csv("data__candidate_pool_samples.csv")   # one row per decoded grid
print(samples.groupby("output_id")["grid_sha256"].nunique())  # distinct grids per output
```

```python
import json
import numpy as np
import pandas as pd

samples = pd.read_csv("data__candidate_pool_samples.csv")
row = samples[samples["grid"].notna()].iloc[0]            # redacted grids are blank
grid = np.array(json.loads(row["grid"]))                  # grid is JSON text: a list of rows
print(row["pool_file"], row["beam_score"], grid.shape)
```

```python
import pandas as pd

outputs = pd.read_csv("data__outputs.csv")                # true/false columns load as booleans
print(outputs.loc[outputs["solved"], ["output_id", "pool_samples", "first_seen_seconds_after_task_start"]])
```

```python
import json

with open("data__selection_alternatives.jsonl", encoding="utf-8") as f:
    rows = [json.loads(line) for line in f]
same = sum(r["kgmon_top2_set_equals_probmul_top2_set"] for r in rows)
print(f"top-2 sets identical for {same} of {len(rows)} decoded outputs")
```

The task ids are ARC-AGI-2 public evaluation ids. The tasks themselves are on the ARC Prize 2026 competition page, `kaggle.com/competitions/arc-prize-2026-arc-agi-2`. This dataset contains no task inputs and no public answers.

## Headline numbers (pilot run, frozen 2026-10-08)

| Quantity | Value |
|---|---|
| Panel | 8 public evaluation tasks, 13 test outputs, 12 with a candidate pool |
| Pool files / decoded samples | 79 / 94 |
| Solved outputs (exact attempt 1 or 2) | 1 of 13 (`45a5af55_0`); its first correct candidate was written 240.8 s after its task started |
| Correct grid in a pool but outside the KGMoN top 2 | 0 of 13 |
| KGMoN and `score_full_probmul_3` top-2 sets identical | 12 of 12 decoded outputs; in 5 of them there are at most two distinct grids, so agreement is automatic |
| Panel score (pilot evaluator, not a leaderboard score) | 1.0 of 8 tasks (`45a5af55` only) |
| Task seconds per task | median 640.3, p90 1083.2, mean 699.0, sum 5,592.3 |
| Decode batches | 42 batches of 4 subkeys each; median 68.0 s, longest 368.5 s |
| Stopped by the per-task cap | 1 task (`221dfab4`, 1208.8 s, cap 1200 s) |
| Stopped by the global end time | 2 tasks (`a32d8b75` at 1029.3 s, `cb2d8a2c` at 310.2 s) |
| Fill calibration, third-party public run `rokaiyasomapti/reproduce-nvarc-2025-results` version 2 (not an official row; see Provenance) | 172 outputs of 120 tasks: 25 weak (14.5%); 4 of 25 solved; second-slot hit 5 of 111 (4.5%; Wilson 95% 1.9% to 10.1%) |

This pilot is not a leaderboard submission, and no official leaderboard row is claimed for it. The panel score is the pilot evaluator's score on eight tasks.

## Glossary

- **Test output (`output_id`).** One test input of an ARC-AGI-2 task has one answer grid. `output_id` is `<task_id>_<index>`, with index 0 or 1.
- **Panel.** The eight tasks chosen for the pilot (see Panel).
- **Subkey.** One augmented version of a test output's query: a geometric chain (`transpose`, `rot90`), a ten-digit colour permutation and an example order. The pool file names are subkeys.
- **View.** One of the 16 planned subkeys of an output (8 geometric transforms times 2 augmentations). A view is decoded or not; the pilot decoded between 0 and 16 views per output.
- **Pool file.** The decoded samples for one subkey, written when its decode batch ends.
- **Decode batch.** Four subkeys decoded together by beam search.
- **Sample.** One decoded grid, with its beam score and eight augmented-query scores. One row of `data__candidate_pool_samples.csv`.
- **Beam score (`beam_score`).** The recipe's score for a decoded grid. Lower means more confident. The selectors use 3 minus this value.
- **Augmented-query scores (`score_aug_1` to `score_aug_8`).** The grid re-scored on eight augmented versions of the puzzle's query, computed as four plus four. Lower means more confident.
- **Candidate (distinct grid).** All samples with the same grid, grouped by grid hash.
- **Attempt 1 and attempt 2.** The two answers given for an output: the top-ranked and second-ranked candidate under the selector used.
- **Second slot.** Attempt 2. A **second-slot hit** is an output where attempt 1 is wrong, a second candidate exists, and attempt 2 is correct.
- **Placeholder.** The recipe's default `[[0]]` grid, used when no candidate exists. Flagged by `is_placeholder`.
- **KGMoN.** The recipe's `score_kgmon` selector. The recipe does not expand the acronym.
- **score_full_probmul_3.** The recipe's second selector. It is described under Selection.
- **Weak output.** In the pilot tables, an output whose main pool has at most one distinct grid, so the second slot is empty or duplicated. The third-party public run has no pool files, so there the proxy is an attempt-2 placeholder.
- **Support.** For the top-1 grid, the number of pool files (views) that contain it, out of 16 planned views. Views that were not decoded count as absent.
- **Trigger, deep pass and fill.** The planned second pass. An output triggers when it is weak and its top-1 support is at most 4 of 16 views. A deep pass re-decodes triggered tasks to try to fill the second slot. A fill is a correct second-slot candidate found this way. No deep pass was run in the pilot, so no fill has been measured.
- **Global end time.** The wall-clock time after which the solver starts no new work. It is the setup start plus 1800 s.
- **Per-task cap.** 1200 s of solver time for one task.
- **Task score.** The evaluator's score for a task, from 0 to 1.

## Panel

The eight tasks were fixed before the run. Order the 120 ARC-AGI-2 public evaluation tasks by the SHA-256 of `arc2-v13-pilot-20261008:` followed by the task id, and take the first eight. Doing this over the 120 ids gives exactly the eight panel tasks.

| Position | Task | SHA-256 of `arc2-v13-pilot-20261008:` + task id |
|---|---|---|
| 1 | 45a5af55 | 033cb8205d32c58e1d8c756239f318b474707e03401dd1b7b8ff8da9ae87cc30 |
| 2 | c7f57c3e | 05cdc03673422f832f8b2efad9dc52c14b5ef711f77fad93ad6e61fd4dbc82bf |
| 3 | a32d8b75 | 065aacb223151ceca761744791dc40d1792de25d1a287392eb8bf0c9846213ef |
| 4 | 247ef758 | 0c6ce2ac157b43b8cad172efa21e17dafb2b7397d805e27d45dc6600af4397df |
| 5 | 221dfab4 | 0cd1b23e8f18d636fe31e1b45fc36b7d4591bb7da00ee267a6bc5e76f1f419f4 |
| 6 | b10624e5 | 0f04c785c70793b2a3f6fdc8baebeb3ef00a75784c74d10a3d44140f097d59b2 |
| 7 | cb2d8a2c | 16e320b0e20f30e9e84ceaa352d744ea980b869dd67a7621f520c7b5707176c1 |
| 8 | 581f7754 | 17590e7bf7234476df4b91c685655b84c5491cecab752d84f976fd6d1631c769 |

To check: `sorted(task_ids, key=lambda t: hashlib.sha256(("arc2-v13-pilot-20261008:" + t).encode()).hexdigest())[:8]`, where `task_ids` are the public evaluation ids from the competition's data files.

The salt string keeps `13`, the version number of the publisher's pilot notebook. The string is kept verbatim because the hashes above depend on it.

## How it was produced

1. **Panel.** As above.
2. **Solver.** The recipe's solver cells ran on 4 NVIDIA L4 GPUs, one rank per GPU, with Unsloth 2025.9.7 on Transformers 4.55.4 and PyTorch 2.8.0, the versions in the log banners. The recipe loads the Kaggle model `sorokin/qwen3_4b_grids15_sft139` (see Provenance). Each task trained its LoRA adapter for 128 steps (the log shows `global_step=128` for all eight tasks). Each task then decoded its test outputs in batches of four subkeys with beam search. Each decoded grid was re-scored on eight augmented queries. The solver wrote each pool file when its decode batch ended. The harness changes were a fixed panel selector, timestamped logging, and separate selection and evaluation processes.
3. **Selection.** A separate process ran both selectors on the saved pools without opening the public answers. `data__freeze_manifest.json` records `solutions_opened: false`. The frozen predictions and alternatives carry SHA-256 hashes (see Predictions and Selection below).
4. **Evaluation.** A separate evaluator read the public answers after the freeze and wrote the per-output scoring (`data__evaluation.json`, unmodified).
5. **Analysis.** The restricted reader (`code__pool_to_jsonl.py`) converted the pickles to JSON. The timelines come from the solver log.

### Stop rule and clock

Before each decode batch, the recipe stops a task if its own spend exceeds 1200 s, or if the wall clock has passed the global end time. Inside a batch, the search also stops at the global end time. The per-task cap is therefore overrun by at most one batch. The global end time is the setup start plus 1800 s (the solver soft end).

When the solver stops a task it logs a `timeout after` line. This card calls that line the stop line. The solver log does not record the global end time, so we bracket it from the log's own unix timestamps:

- The solver stage started 25.08 s after setup and ran for 1795.49 s (`data__run_summary.json`). It cannot end before its last log line, which was printed at unix 1791473878.07. That places the global end at or after unix 1791473857.50, which is 20.57 s before the last line.
- The stop line for `a32d8b75` (unix 1791473861.075) is printed only if the wall clock had passed the global end, so the global end is before that time.

The global end therefore lies in [unix 1791473857.50, 1791473861.08), 17.0 to 20.6 s before the solver's last log line. This gives four consequences:

- `221dfab4` stopped at unix 1791473567.8, about 290 s before the global end. Its spend was 1208.8 s, above the cap, so its cause is the **per-task cap**.
- `a32d8b75` (spend 1029.3 s) and `cb2d8a2c` (spend 310.2 s) stopped below the cap, so their cause is the **global end time**. They stopped 0 to 3.6 s and 17.0 to 20.6 s after it.
- The first log line was printed 74 to 77 s after the stage started, so the stage's start-up time is outside the log. Counting that start-up time, the stage ended 0 to 3.6 s after its last log line, which matches its 1795.49 s elapsed time.

The `data__analysis_extra.json` fields named `global_end_passed_at_break` and `seconds_before_end_estimate` use the end estimate of last line minus 20.57 s. That estimate is the lower edge of the bracket, so those fields agree with it but do not test it. `data__task_summary.csv` states each cause and the unix time of its stop line.

## Selection

Candidates are distinct grids, grouped by grid hash.

- **KGMoN (`score_kgmon`).** The number of samples for the grid, minus the mean of its augmented-query scores. Higher ranks first.
- **`score_full_probmul_3`.** The sum over the grid's samples of (3 minus beam score), plus the mean over the samples of the sum of (3 minus each augmented-query score). Higher ranks first.

In this run attempt 1 is the rank-1 grid under KGMoN (12 of 12 outputs) and attempt 2 is its rank-2 grid (9 of 9 outputs with two candidates). Results on the pilot:

- The top-2 sets are identical for 12 of 12 decoded outputs, and the top-1 grids are identical for 12 of 12.
- Only the ordered top-4 list of `221dfab4_1` differs, at rank 4. KGMoN puts a grid with hash prefix `47ca9b2c` there and `score_full_probmul_3` puts one with prefix `4e63493c`. Neither is correct.
- In 5 of 12 decoded outputs there are at most two distinct grids, so top-2 agreement is automatic there.
- The one solved output's correct grid is rank 1 under both selectors.

The pilot therefore cannot separate the two selectors. Its value is the identical pools and the full ranked lists.

## Predictions and placeholders

`data__predictions.jsonl` holds the final attempts for all 13 outputs. An attempt equal to the placeholder `[[0]]` has `is_placeholder: true`. In this pilot one attempt 1 and four attempt 2 are placeholders (5 of 26 attempts). Scripts that score accuracy must exclude placeholders. There is no separate `has_candidate` field.

The JSON Lines files `data__predictions.jsonl` and `data__selection_alternatives.jsonl` are conversions of the frozen `predictions.json` and `selection_alternatives.json`. The grids are identical to the frozen JSON: every grid that is not redacted was checked, 26 attempts in `data__predictions.jsonl` and 64 ranked grids in `data__selection_alternatives.jsonl`. The frozen files have SHA-256 values `2c078f47…` and `173c71aa…`, as recorded in `data__freeze_manifest.json`.

## Grids redacted where they equal the public answer

Where a decoded grid equals the ARC Prize public answer for its test output, the grid is written as `null` and `grid_redacted` is `true`. Its `grid_sha256` is kept. This affects 16 samples, all in the 16 pool files of `45a5af55_0` (one distinct grid), and that output's attempt 1 and its rank-1 entry under both selectors. Checking a redacted grid's hash needs the public ARC answers, which are not included. Other grids are model outputs and are published in full. The redaction keeps the one solved answer from being republished as a grid.

## Limitations

- Eight tasks and 13 outputs, one solved. This is a pilot, not a benchmark. The timing observation that the solved output's correct grid appeared within 600 seconds rests on one output (n = 1).
- Timings are for L4 GPUs with this recipe and this harness, from one run. We did not measure run-to-run variance.
- Support counts views that were decoded before a stop. An output with few decoded views cannot reach a high support, so support mixes calibration with how much was decoded. The threshold of 4 of 16 is not calibrated on public data.
- Weak is defined differently in the two sources: by at most one distinct grid in the pilot pools, and by an attempt-2 placeholder in the third-party public run.
- The fill calibration is a template. The deep pass was not run in the pilot, so no measurement updates the Beta prior. The public-run counts are a third-party run's, not an official row of this account.
- Redaction removes one answer grid and its duplicates. The hash keeps the match checkable only for someone with the public answers.
- The model card of `sorokin/qwen3_4b_grids15_sft139` is empty, as shown on the Kaggle page on 2026-10-10 (not independently re-verified). The data used to fine-tune the model is not documented, so the grids cannot be checked for overlap with any training data. Treat them as unlabelled model outputs.

## Provenance

Each input is listed with its reference, what it provides, and its licence as recorded for this card. The licence column records what each page showed on 2026-10-10. Those statements were not independently re-verified for this revision, and they are labelled that way. The model weights, the recipe's source and the task inputs were not downloaded for this dataset, and none of them is included.

| Input | Reference | What it provides | Licence, as shown on the Kaggle page on 2026-10-10 (not independently re-verified) | Link |
|---|---|---|---|---|
| ARC-AGI-2 public evaluation tasks | GitHub repository `arcprize/ARC-AGI-2`; competition `arc-prize-2026-arc-agi-2` | Task ids only. Task inputs and public answers are not included. | Apache-2.0, as shown on the GitHub page on 2026-10-10 (not independently re-verified) | https://github.com/arcprize/ARC-AGI-2 |
| Model weights | Kaggle model `sorokin/qwen3_4b_grids15_sft139`, variation `Transformers/bfloat16`, version 1. Owner ref `sorokin`; the model page title shows the owner display name `ivan`. | The fine-tuned model that wrote the decoded grids. The placeholder `[[0]]` is the recipe's default, not a model output. Weights are not included. As shown on the Kaggle page on 2026-10-10 (not independently re-verified), the model description is empty, so the fine-tuning data is not documented. | Apache 2.0 | https://www.kaggle.com/models/sorokin/qwen3_4b_grids15_sft139 |
| Base model named by the model name | Hugging Face `Qwen/Qwen3-4B` | Named by `qwen3_4b` in the model name. The Kaggle page does not state the base model. | apache-2.0, as shown on the Hugging Face page on 2026-10-10 (not independently re-verified) | https://huggingface.co/Qwen/Qwen3-4B |
| Recipe notebook | Kaggle notebook `koushikrudra/failed-in-aimo`, version 1 (scriptVersionId 312063593) | The solver code: LoRA training, beam decoding, the selectors and the sample schema. Source is not included. | Apache 2.0 | https://www.kaggle.com/code/koushikrudra/failed-in-aimo?scriptVersionId=312063593 |
| Kernel source | Kaggle notebook `sorokin/pip-install-unsloth-flash-patch` | Attached to the solver run as a kernel source. Source is not included. | Apache 2.0 | https://www.kaggle.com/code/sorokin/pip-install-unsloth-flash-patch |
| Third-party public run (figures only) | Kaggle notebook `rokaiyasomapti/reproduce-nvarc-2025-results`, version 2, commit run over the 120 public evaluation tasks | The per-output counts in `data__fill_calibration.json` (`public_run`), computed from that run's submission file (sha256 431be759…). This is a third-party run, not an official row of this account. No code or data from the run is included. | Not stated here; no content of the notebook is redistributed | https://www.kaggle.com/code/rokaiyasomapti/reproduce-nvarc-2025-results |

Software that the solver run used is in the dependency table under Credits.

**Licence decision.** The Kaggle licence field is `apache-2.0`. The decoded grids are model outputs on ARC-AGI-2 public evaluation tasks, and each model, notebook and task input in the table is recorded above with an Apache-2.0 licence as shown on its page. The code file is the publisher's own code. The third-party public run contributes counts only, which are labelled as third-party, and no code or data from that notebook is redistributed.

**Competition terms.** This card does not restate the ARC Prize 2026 competition rules, and this revision did not re-read them. The dataset contains no task inputs and no public answers. Users who reuse the grids should read the competition terms themselves.

## Credits

### Dependencies

Each component below is imported by the shipped code, appears in the solver log banners of the measured run, or is used by the README snippets. Versions are those recorded in this dataset, where recorded. Licences are the projects' upstream licences.

| Component | Where it appears | Version recorded | Licence |
|---|---|---|---|
| NumPy | `code__pool_to_jsonl.py` (imported); README snippets | not recorded | BSD-3-Clause |
| pandas | README snippets | not recorded | BSD-3-Clause |
| PyTorch | solver run (log banner) | 2.8.0 | BSD-3-Clause |
| Transformers | solver run (log banner) | 4.55.4 | Apache-2.0 |
| Unsloth | solver run (log banner) | 2025.9.7 | Apache-2.0 |
| Triton | solver run (log banner) | 3.4.0 | MIT (upstream licence; not independently re-verified) |
| xFormers | solver run (log banner) | 0.0.32.post2 | BSD-3-Clause (upstream licence; not independently re-verified) |

### People and sources

- **Recipe.** `koushikrudra` (Kaggle), for the notebook `koushikrudra/failed-in-aimo`.
- **Model and kernel.** `sorokin` (Kaggle), for the model `sorokin/qwen3_4b_grids15_sft139` (the model page title shows the owner display name `ivan`) and the kernel `sorokin/pip-install-unsloth-flash-patch`.
- **Third-party public run.** `rokaiyasomapti` (Kaggle), for the notebook `rokaiyasomapti/reproduce-nvarc-2025-results`, whose version 2 commit run supplies the public-run counts in `data__fill_calibration.json`.
- **Tasks.** The ARC Prize Foundation, for ARC-AGI-2 and the ARC Prize 2026 competition.
- **Base model.** The Qwen team, for the Qwen3 model family named in the model name.
- **Libraries.** The authors of the packages in the dependency table.
- **Publisher.** `prvsiyan` (Kaggle account).

## Licence

- **Dataset licence (Kaggle field):** `apache-2.0`. The same licence is in `LICENSE`, and `NOTICE.md` states the per-file terms and the third-party inputs. This dataset contains no content offered under another licence.
- **Per-file terms.** Every file in this dataset is released under Apache-2.0 by the publisher, including the tables, records and documentation. `NOTICE.md` lists the terms file by file. The code file is the publisher's own code. The licence of each third-party input is in the Provenance table, and the licence of each dependency is in the Credits table.
- **Third-party text.** `data__solver_log.jsonl` holds the run's console lines, including banner text from the training libraries. Those lines are copied from the log. The libraries themselves are not redistributed.
- **Not included.** ARC-AGI-2 task inputs, public answers, model weights, the recipe's source, the kernel source, the pool pickles, the third-party run's code and data, and any credentials.

## How to cite

> prvsiyan (2026). *ARC-AGI-2 TTT Candidate Pools: an 8-task pilot* [Dataset]. Kaggle. Candidate pools from the recipe `koushikrudra/failed-in-aimo` (version 1) on ARC-AGI-2 public evaluation tasks.

Please also credit `koushikrudra/failed-in-aimo`, the model `sorokin/qwen3_4b_grids15_sft139`, the third-party public run `rokaiyasomapti/reproduce-nvarc-2025-results` (for its counts), and the ARC Prize 2026 competition.

## Changelog

- **v1, 2026-10-10:** first release. Frozen pilot outputs (pilot notebook version 13), a flat sample table, stop rule and clock bracket, selection comparison, fill calibration and analysis. Before upload the files were flattened to the top level (`data__`, `code__` prefixes), every column was listed, and the licence was set to `apache-2.0` with each input's licence documented.
- **v1, revision 3, 2026-10-10:** the third-party public run is named and attributed; each input's licence is labelled as shown on its page (not independently re-verified); dependency credits with licences were added; the attribution to a recipe family and the statements about the competition rules were removed; the projections in the fill calibration file were removed; two files were renamed (`data__analysis_extra.json`, `data__fill_calibration.json`); the schema tags of the fill calibration and run summary files were changed. The byte-identical records keep their original tags.
