# ARC-AGI-2 frontier sweep, 8 October 2026

Competition: arc-prize-2026-arc-agi-2. Deadline 2 November 2026. One submission per day, 12-hour notebook limit on L4 GPUs.

The sweep was read-only. It made no submissions, pushes or model downloads. Leaderboard values were read at about 14:42 UTC and public code pages at about 14:50 UTC on 8 October. Labels follow the README legend.

## 1. Where the scores were

- **[V]** Leaderboard (2,560 teams, 14:42 UTC). Top five: Tufa Labs 83.61, rabbithole 80.56, Yi-Chia Chen 77.22, nvbanana 76.67, ALbert RUehlman 66.81. Rank 15 was 37.36, rank 25 33.89, ranks 100 and 128 32.22, ranks 200 and 256 31.81, rank 300 31.39.
- **[V]** The campaign's only official row at that time was 29.03 (row 55001244, 26 July, public notebook version 3). It ranked 1167 of 2,560.
- **[V]** The top public notebook was koushikrudra/failed-in-aimo version 1, with a displayed best score of 33.89 and an Apache-2.0 licence. The next was chiakazirim/learned-from-aimo, with a best score of 32.22 in version 1. Its current version 7 displays 16.39, so the best and current scores differ.
- **[V]** Nothing on the signed-out code page scored above 32.22 apart from the 33.89 notebook.
- **[V]** The top 50 notebooks by score are forks or re-implementations of one recipe. The recipe uses the Qwen3-4B model sorokin/qwen3_4b_grids15_sft139 with per-task LoRA test-time training: rank 256, alpha 32, rank-stabilised scaling, learning rate 5e-5, one epoch over 128 augmented sequences. Decoding is a batched depth-first search over 16 views with a probability threshold of 0.2. Candidate selection is the recipe's default scoring function, score_kgmon.
- **[V]** The two new LLM notebooks (delongyang, Qwen3.8-27B-FP8 and Qwen3.6-35B-A3B on vLLM) had no score.

## 2. Why the same recipe spans 31 to 34

- **[V]** Identical code, different scores. The solver in rokaiyasomapti version 2 is byte-identical to koushikrudra version 1 and scored 32.22. The only differences are a commit-run task filter and argument parsing. Two other notebooks, from mikelou1 and sankalpsthakur, ran the same code and scored 32.22 and 31.81.
- **[V]** The recipe seeds candidate scoring with the built-in string hash of the puzzle key, modulo 1024 squared. Python salts that hash for each process unless PYTHONHASHSEED is set.
- **[P]** Each run therefore scores against a different augmentation set (forum topic 742027). Batched depth-first decoding is nondeterministic (the NVARC paper, section 3.3). bf16 and flash-attention training give different candidate pools on each run (topic 742027).
- **[V]** The campaign's own bench and public runs of the same code disagreed on one output (task 36a08778, output 2; 76 versus 74 decoded views).
- **[mixed]** Rerun distribution: 24 public or self-reported scores of the recipe, mean 30.7, standard deviation 1.5. The 11 unselected self-reports average 30.0.
- **[I]** The expected maximum of 25 independent draws is about 33.4, so the 33.89 card is consistent with a lucky draw.
- **[I]** Honest expectation for a rerun: 30.5 plus or minus 1.5 per run, with about a 20 percent chance of reaching 31.81 in a run.
- **[P]** A forum participant wrote that a score of 33 needs a lucky seed (topic 733930).

## 3. Runtime and the hidden rerun

- **[V as displayed]** Runtime of new-best submissions in the 29 to 34.5 band, in minutes, from a public monitor shown on the code page (p10 / p50 / p90): June to July, n = 464, 636 / 649 / 665; August to 15 September, n = 604, 637 / 650 / 707; 16 September to 8 October, n = 452, 639 / 654 / 720.
- **[V as displayed]** The score does not vary with runtime. The mean is 30.4 to 30.8 in every runtime bucket.
- **[V]** The campaign's 29.03 run took 717 minutes, which hit the cap.
- **[I]** At these runtimes the recipe stops itself at 12 hours minus 10 minutes. With about 240 hidden tasks, the run has about one hour of slack, so the sweep judged the hidden run nearly time-bound.
- **[I]** The size of the hidden task set is disputed in the sources. The sweep's time estimate assumed about 240 hidden tasks. That count matches the visible placeholder file, whose statistics match the training split. The state note records the question as open.

## 4. Where the recipe loses points

- **[P]** Coverage is the ceiling. A correct candidate exists for about 35 of 120 tasks, and about 30 are selected (a public CC0 analysis). The NVARC authors report 30.5 percent pass@2 against 40 percent pass@10 on the public evaluation set.
- **[V as displayed]** Selector. The recipe's own benchmark scores two selectors on the same candidate pool. Probability-mass selection (probmul) is compared with kgmon in five same-pool runs: rokaiya version 2 public log, 120 tasks, 34.3/115 versus 32.8/115 (+1.5); immu4989 public log, 120 tasks, 35.0/113 versus 34.0/113 (+1.0); dragoctlin public log, 38 tasks, 11.3 for both (0); anvithpothula registry, 35.3/114 versus 33.3/114 (+2.0); anvithpothula registry, 35.3/116 versus 34.8/116 (+0.5). Net +5.0 outputs, none negative.
- **[P]** Caveats on the selector evidence. The NVARC fine-tuning data includes ARC-AGI-2 evaluation puzzles (paper, table 1), so public evaluation is partly exposed. The NVARC authors preferred a count plus log-probability score after their deadline.
- **[V]** The campaign's own pilot on eight tasks found identical top-two sets under both selectors for all 12 outputs that had a candidate pool. That pilot could not measure a one-point effect.
- **[V as displayed]** Induction add-ons gave nothing. The koushikrudra version 2 "Leg C" (Qwen2.5-Coder-7B with verified programs), run on all 120 tasks, verified 0 programs and promoted 0. Other induction variants scored 27.64 and 28.06 (an MCTS fork) **[P]**, and 28.89 (a coder-7B induction card) **[V]**.
- **[P]** TRM adds nothing. NVARC with a 4B model scored 27.22 with and without TRM. TRM alone scored 22 percent on the evaluation set.
- **[P]** Fine-tuning and repair. Continued fine-tuning of the 4B model on 59k tasks gave a paired +6/-3 result, inconclusive. Structural fine-tuning gave +5/-5 and was rejected. Cell voting or repair recovered 0 of 108 cases.
- **[V]** Pooled half-cost passes. luxluxshan version 3 and dalezhong each scored 30.14. luxluxshan version 1, a full pass plus a leftover pass, scored 32.22 once.

## 5. Operational facts

- **[P]** A submission that queues for too long ends as a Kaggle error. Such submissions do not count against the daily limit. Several teams lost submissions on 6 to 8 October (topics 746520, 747088, 747193). The runtime limit counts running time only.
- **[P]** Leaderboard reruns are not charged to GPU quota (topic 694745). L4 by 4 sessions are billed at 2 times. The campaign used 2 times as a planning factor only.
- **[V]** Rules on the competition page: one submission per day, up to two Final Submissions, the private leaderboard alone decides standing, and unselected finals are chosen automatically by the platform.
- **[P]** The visible test placeholder has 240 tasks with 259 outputs (topic 742790). Its size statistics match the training split, so it says nothing about the hidden set (**[I]**).

## 6. Datasets and models

| Asset | Licence | Usable | Note |
|---|---|---|---|
| sorokin/qwen3_4b_grids15_sft139 | Apache 2.0, fine-tunable **[V]** | Yes | Used by every top notebook |
| sorokin/qwen3_2b_grids15_sft141 | Apache 2.0 **[V]** | Yes | Second NVARC model, not used by top notebooks; too slow next to the 4B model |
| Qwen3.8-27B-FP8 mirrors | Apache 2.0 **[V]** | Yes | No leaderboard evidence of gain; on L4 the FP8 attention needs the Triton backend **[P]** |
| Qwen3.8-Flash-Next | Qwen Community Licence **[V]** | No | Open licence question on the forum (topic 746307) |
| ThinkingCap-Qwen3.8 | PolyForm Small Business **[V]** | No | Not permitted by campaign policy |
| Qwen3.6-35B-A3B mirror | "Other" **[V]** | No | Unless verified |
| qwen-lm/qwen2.5-coder | Apache 2.0 **[V]** | Yes | Measured as useless in Leg C |
| cpmpml/arc-prize-trm-031 | CC0 **[V]** | Yes | TRM evidence is negative |
| yhay81 program corpus | Apache 2.0 **[V]** | Yes | Used by finalsunflower (31.39) |
| sorokin NVARC puzzle sets | unknown **[V]** | No | Fine-tuning evidence negative anyway |

## 7. The campaign's position in numbers

| Row | Score | Note |
|---|---|---|
| Official, 26 July, public version 3 | 29.03 (rank 1167) | **[V]** |
| Expected per run, credited recipe | about 30.5 plus or minus 1.5 | **[I]**; about 20 percent chance of at least 31.81 per run **[I]** |
| Public card, best version | 33.89 | Top of its rerun distribution **[V]** |
| Expected best of N public submissions | about 32.2 (N = 5), about 33.4 (N = 25) | **[I]**; public only, private expectation unchanged |
| Measured selection headroom | +1 to +2 outputs of 115 | **[V as displayed]** |
| Measured oracle headroom | at most about 5 tasks | **[V as displayed]**; coverage is the limit |
| Leftover time | about 1 hour on 4 GPUs | **[I]** |
| Private frontier | 55 to 84 | Different class of method; no public route found **[I]** |

The sweep's realistic target from public evidence was an expected 31 to 31.5 per run from the recipe, the probmul selector and time safety, plus variance upside from daily submissions **[I]**.

## 8. Verified, refuted and open

**Verified [V]:** the leaderboard and public score snapshot as displayed on 8 October; the koushikrudra version 1 source details (hash-derived seed, kgmon default, threshold, per-task cap); the identical-solver pairs; model and notebook licences; the competition rules; the runtime distribution as displayed.

**Refuted or negative, as the sweep recorded them:** induction add-ons (Leg C and the 7B variants, the MCTS fork); TRM ensembles; continued and structural fine-tuning; cell voting and repair; symbolic DSL fallbacks. The sweep put fine-tuning, TRM, cell voting and repair, and symbolic fallbacks on its reject list. It put coder-model induction on a do-not-pursue-without-probe list and pooled half-cost passes on a do-not-prioritise list.

**Verified only as displayed [V as displayed]:** the five selector comparisons and the induction results. They were read from rendered pages, not from raw logs.

**Open or unverified:**
- The hidden task count (120 or 240), which changes the time conclusion.
- The NVARC paper figures, which were not re-checked.
- Several forum claims, which are [P] self-reports (for example, byte-identical code scoring 29.86 and 30.14, topic 742027).
- The claim that 164 teams scored 32 or more. The saved leaderboard snapshot has only 100 rows, so it could not be checked.

**Source gap:** the ARC-AGI-2 sweep folder has no standalone VERIFY document. Its verification log is a separate notes file and is cited here by title.
