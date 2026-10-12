# A source-backed next direction after the zero result

The CPU study establishes zero useful activation for these specific relational grammars on the full exposed panel. It does not evaluate a neural model. The next method direction comes from an inspected saved copy of Koushik Rudra's [Failed in AIMO, version 1](https://www.kaggle.com/code/koushikrudra/failed-in-aimo?scriptVersionId=312063593), rather than from another guessed symbolic operator.

An 11 October 2026 public notebook metadata snapshot reported score 33.89 for that version, native version 312063593 with native status COMPLETE and linked submission identifier 53458525. This packet does not independently establish that submission's exact completed score row. The inspected version-1 source has SHA-256 `5d4080cbd7d3376864197ed061dac342f0f9894ede2f45a458d5263d6021941b` and 41,014 bytes. This is historical public-source metadata, not a fresh current leaderboard claim. A later notebook head is not interchangeable with the version associated with the reported score. The source was read and not executed in this study; the reported score does not establish that a local reproduction will match it.

## What the scored source does

The notebook loads an ARC-specialized Qwen3 4B model in bfloat16 and adapts LoRA parameters separately for each task. It snapshots and restores the default adapter before each task, preventing adaptation from one task from carrying into the next. Its LoRA rank is 256, alpha 32, and its listed training settings include one epoch and learning rate 5e-5.

Training uses the supplied demonstration pairs. Eight geometric orientations are combined with sixteen color permutations and shuffled demonstration orders. In the challenge-only path, formatting treats the last shuffled demonstration as a pseudo-query with its known demonstration output, and a completion-only collator masks user tokens. No query answer is needed to construct these task-specific training samples.

Inference constructs sixteen transformed versions of each query, using eight orientations and two color permutations. It performs bounded token search, parses grid candidates, inverts the transforms, deduplicates original-coordinate grids, and scores candidates under eight augmented prompts. The default selection groups identical grids and ranks them by occurrence count minus mean augmented negative log-likelihood. Its per-task and whole-run time limits can stop later decoding batches. These are source facts; their separate contributions to the observed score have not been measured here.

## A concrete future controlled comparison

First preserve the version's per-task adapter reset, model and tokenizer identity, and demonstrated training/query-answer boundary. Define a fixed full-panel input inventory and record the original process seed and transform schedule; the source uses Python's process-dependent `hash` in one candidate-rescoring seed. Replacing it with a stable explicit seed schedule changes behavior and needs a separate prospective factor rather than being assumed neutral. Log per-task training time, completed decoding batches, valid candidates, and truncations so that a time-capped partial run cannot masquerade as a complete comparison. Test transform inversion on invented rectangular grids and all ten colors, and verify that restoring the adapter reproduces a task's initial state.

Then hold the adapted model and decoded candidate set fixed while comparing the original occurrence-minus-mean-NLL ranking with a preregistered length-normalized augmented score. The latter is a hypothesis: the original rescoring sums token log-probabilities and can vary with candidate dimensions. Use demonstration leave-one-out evidence to define the ranking rule and coefficients before looking at separate query answers; tasks with only one demonstration supply no leave-one-out tuning evidence. Freeze both arms' two predictions for every query before separate scoring. Report complete-panel exact-at-two, paired wins and losses, and runtime rather than selecting a favorable subset.

A stricter rectangular-grid parser and stable transform seeds are sensible contract checks, but their quality effect is also unmeasured. Source development mode selects a small hand-written task subset and can load evaluation answers for benchmarking selection algorithms. A future full-panel experiment should explicitly register its inventory and prediction freeze so those development conveniences cannot affect query-answer-directed choices.

This is a source analysis and a proposed comparison, not a runnable neural preflight, a GPU launch request, or an alternative admission artifact. The previously blocked neural peer-JSON workflow remains stopped. No neural gain, native score, or complementarity claim is supported by this packet.

## Attribution and redistribution

All neural-method credit belongs to Koushik Rudra and the notebook's upstream model/software authors. Its third-party source and weights are not included. Their precise redistribution and model licences have not been established by this packet; method attribution is not a licence grant. The original relational experiment is independent of those model implementations.
