# Public V19 is the 10-09 submission; V20 is a flagged candidate, and the fill pass is unmeasured

This note records what was pushed and committed on 8 October, what was built offline on 9 October, and the decisions that follow. It states measurements and decisions only. Nothing here is a leaderboard result.

## Public V19 (pushed and committed clean, 8 October)

Version 19 of the public notebook carries the credited recipe from [the 8 October control rerun](../../official-submissions/2026-10-08-v12-credited-rerun/README.md). Two changes are added, both in one documented code cell:

- **Final attempts.** Both attempts are the top two grids of `score_full_probmul_3` over the same candidate pools. Version 18 used `score_kgmon`. Both selectors are in the recipe's own `arc_decoder.py`.
- **Scoring seed.** The re-scoring seed is `zlib.crc32` of the puzzle key. The cell also sets `PYTHONHASHSEED=0` and reseeds Python, NumPy and PyTorch per puzzle.

Measurements:

- The push was accepted as version 19, with `cells_identical: true` against the local candidate.
- The commit run reached status COMPLETE after 1,586 s.
- The commit run decodes only the four smoke tasks. Its submission file has 172 output slots and 5 real candidates, all in those four tasks. The other 167 slots are placeholders. The commit run therefore checks that the pipeline works; it is not a score.
- The hidden rerun decodes the hidden test set. The size of that set is not settled: the local test file lists 240 tasks, and the strategy notes list the 120-versus-240 question as open.
- Version 19 is the 10-09 submission.

## V20 candidate (built offline, 9 October; not pushed)

Version 20 is Version 19 plus two additions:

1. **Per-task logging, behaviour-neutral.** Each task writes one JSON line: wall time, whether the 1,200 s budget was hit, whether the global end passed, decode batches, decoder forward steps and peak GPU memory. A receipt summarises the lines. The logging only reads counters and writes files, and it never raises.
2. **A fill-only leftover deep pass, default OFF.** It runs only if the environment flag is set, only after the main queue drains, and only if more than 1,500 s remain. Its merge can change only a slot the main pass left empty or duplicated.

Measurements:

- Candidate sha256 `58c9bf76…`, 632,059 bytes, 109 cells. The Kaggle client's wire body is 609,937 bytes, against a limit of 1,036,069.
- Dry run: `DRY_RUN_OK`, public visibility kept, prepush copy equal to the pushed version 19.
- Offline checks: 143 of 143 pass, in normal and optimised modes. They include a 20,000-case merge invariant with no lost main answer, the time gate, the trigger, logging, and an end-to-end `make_submission` on the 79 V13 pool files.
- With the flag off, the submission on those pool files is byte-identical to Version 19's.
- With the flag on, no output that Version 19 solves is lost, and the fills touch only empty or duplicated slots.
- The deep pass has not run on a GPU.
- A loader defect found before any push (a truncated pool file would have stopped `make_submission`) was fixed in the candidate.

## Fill calibration (CPU only)

- **Weak outputs.** 25 of 172 public-run outputs (14.5%) have one candidate or none in the second slot. Weak outputs are solved in 4 of 25 (0.160), against 0.279 for the rest. The difference is not significant (Fisher p = 0.32).
- **Second-slot anchor.** When the first attempt is wrong and a second candidate exists, the second attempt is correct in 5 of 111 outputs: 4.5% (Wilson 95% interval 1.9% to 10.1%).
- **Trigger.** An output is triggered when it is weak and its top grid appears in at most 4 of 16 views. On the 13 V13 outputs, the one solved weak output has its top grid in all 16 views. The three unsolved weak outputs have 0, 1 and 1 views. Thresholds from 1 to 15 fire on the same three unsolved outputs.
- **Limit.** The public run has no pool files, so the view-support condition cannot be checked on it. It rests on four V13 outputs.
- **Prior.** P(fill) per weak-unsolved output is Beta(1.2, 38.8), with mean 0.030 and a 5% to 95% range of 0.0024 to 0.083.
- **Expected gain.** At the prior mean, about +0.3 to +0.4 score points: +0.38 if all 21 weak-unsolved public outputs were covered, and +0.32 under the capacity bound for the hidden set.
- **Detectability.** The probability of at least one fill in a run is about 0.47. A single run has a standard deviation of about 1.6 points, so this effect cannot be detected in one run.

## Decisions

1. Version 19 is the 10-09 submission.
2. The V20 candidate is not pushed. The deep pass stays default OFF.
3. Any bench run of the deep pass is a decision for after the 10 October quota reset. Its analysis uses the trigger as written here, so the rule is not fitted after the fact.
4. The support threshold of 4 of 16 views is provisional. Any run should record support for every triggered output, so the threshold can be re-fitted.
5. The fill study does not change the next submission choice.

## Files

- `fill-calibration.json`: the calibration numbers above. It contains per-output V13 rows (distinct grids, top-grid support, solved flag), the public-run counts, the prior, and the expected-gain table. It contains no grids.

Credits: as in the 8 October notes. The recipe is Koushik Rudra's `failed-in-aimo` V1 (Apache-2.0). The seed idea comes from luxluxshan's public notebook `luxluxshan/arc2-nvarc-v1`. The probmul selector is in the recipe's own `arc_decoder.py`.
