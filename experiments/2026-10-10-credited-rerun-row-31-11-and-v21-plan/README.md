# The credited rerun scored 31.11; public V19 is pending; V21 is the 10 October draw

On 8 October we submitted, from our private bench worker, a credited rerun of [koushikrudra/failed-in-aimo V1](../../official-submissions/2026-10-08-v12-credited-rerun/README.md). That note said a completed score would be recorded in a separately dated note. This is that note. It records measurements and decisions only.

## Row 56951295: the credited rerun

| Measurement | Value |
|---|---:|
| Row | 56951295 (bench rerun of the recipe, with the infrastructure changes listed on 8 October) |
| Status | COMPLETE |
| Public score | 31.11 |
| Previous best ARC2 row (public version 3) | 29.03 (row 55001244) |
| Rerun distribution of the same recipe | mean 30.7, SD 1.5 (24 reruns, frontier sweep); recount of 25 listed values: mean 30.6, SD 1.7 |
| Position in the distribution | +0.4 points; z = +0.27 (z = +0.32 on the recount) |
| Source of the status | live submissions snapshot, observed 2026-10-10 10:24 UTC |

The score falls inside the 31.4 to 32.2 band that the 8 October note cited for public reruns of this recipe. It is 0.4 points above the mean of the reruns, well within one SD. A single row is one draw from that distribution, so it cannot separate the recipe from a rerun on our account. The row runs the public recipe. It does not contain our own additions.

## Public version 19 (row 57016777): pending

- Pushed to the public notebook as version 19 on 8 October. Its commit run reached COMPLETE after 1,586 s. The commit run decodes only the four smoke tasks: its submission file has 172 output slots, of which 5 hold a real candidate.
- The recipe is unchanged, with two changes in one documented code cell. Both submitted attempts are the top two of `score_full_probmul_3` over the same pools; the recipe's default is `score_kgmon`. The scoring seed is `zlib.crc32` of the puzzle key, with `PYTHONHASHSEED=0`.
- Submitted 2026-10-09 17:56 UTC. No score in the snapshot taken 2026-10-10 10:24 UTC.
- No paired hidden-set comparison with row 56951295 exists yet. The public paired runs of other authors average about +1.0 points for the probmul selector, as displayed on their pages. Our 13-output pilot found identical top-two sets for all 12 outputs with a pool, so the expected effect is small.

## V21: the 10 October draw

Decision: V21 is submitted as the 10 October ARC2 draw if its commit output validates.

- The same public notebook; identity and visibility unchanged.
- Contents: the public V19 pipeline, plus behaviour-neutral per-task logging and a fill-only leftover deep pass. The deep pass is on by default, through a configuration cell that sets `ARC_V20_DEEP` to 1 unless the environment sets it. The recipe cells are unchanged.
- Candidate sha256 `4a7b62d3…`, 640,011 bytes. Wire body 617,143 bytes against a limit of 1,036,069. 113 cells.
- Offline: 262 of 262 checks pass in both normal and optimised mode. With the flag off, the submission on the 79 V13 pool files is byte-identical to the V19 submission. With the flag on, no V19 solve is lost in any case tested: deep candidates set to a mix of true and wrong grids, to random grids, and to nothing.
- Dry run: `DRY_RUN_OK`, public visibility kept.
- Commit run: the deep pass is expected to be skipped by its time gate. The V19 commit run's solver finished at 1,471 s, and the gate needs more than 1,500 s before the 2,100 s soft end. The commit output therefore validates the logging, the knob reads and the merge with no deep candidates. It does not exercise the deep pass.
- Hidden rerun: the first run of the deep pass on a GPU. It runs only if the main queue drains with more than 1,500 s left before 41,400 s. A failure in the deep phase is caught, and the submission then equals the V19 submission.
- Expected effect: +0.3 points at the prior (mean probability of a fill of 0.03 per weak unsolved output, Beta(1.2, 38.8)). One run cannot detect an effect of that size, given a run-to-run SD of about 1.6.

## Decisions

1. Row 56951295 is recorded as our best public ARC2 result, 31.11, inside the rerun distribution of the same recipe.
2. Public version 19 (row 57016777) stays the scored version of record for 9 October until its status resolves.
3. V21 is the 10 October draw if its commit output validates. The deep pass is measured on the hidden rerun, not on the commit run.
4. V21 leaves the recipe cells unchanged. Its additions are logging and the default-on deep pass.

## Files

- `row-status.json`: the ARC2 rows and their status and public score, as read from the live snapshot.

Credits: the recipe is Koushik Rudra's `failed-in-aimo` V1 (Apache-2.0) on Ivan Sorokin's Apache-2.0 model `sorokin/qwen3_4b_grids15_sft139`. The probmul selector is in the recipe's own `arc_decoder.py`. The seed idea comes from luxluxshan's public notebook `luxluxshan/arc2-nvarc-v1`.
