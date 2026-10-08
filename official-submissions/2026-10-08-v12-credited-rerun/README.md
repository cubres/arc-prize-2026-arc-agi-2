# 2026-10-08: credited control rerun of the strongest public recipe

On 8 October we submitted, from our private research worker, an attributed rerun of **koushikrudra/failed-in-aimo V1** (Apache-2.0; public score 33.89 on its author's card). The recipe is the public NVARC line: the Apache-2.0 model `sorokin/qwen3_4b_grids15_sft139` with per-task LoRA test-time training, run on four L4 GPUs. It is **not our method**; it is a control row so that our own additions can later be measured against the current public frontier under our account.

What we changed, and nothing else ([recipe-v1-to-v12.diff](recipe-v1-to-v12.diff)): an attribution header on every recipe file, a mount-path fallback that tries the recipe's original paths first, and an owned watchdog that stops the solver before the 12-hour notebook limit (soft end 11 h 30 m, hard stop 11 h 40 m, export by 11 h 46 m), with a schema check against the sample submission and atomic export. Our own test-time-training work was deliberately not added.

Commit run (not the scored rerun): 1766 s, solver exit 0, 344 valid attempts kept, no default fills ([commit-run-receipt.json](commit-run-receipt.json)). Submission accepted at 11:23:58 UTC as row 56951295 ([submission-accepted.json](submission-accepted.json)); its status was absent at acceptance, which means unknown. Public reruns of this recipe by others scored 31.4–32.2, so an honest expectation is that band, not 33.89, and about 2–3 points above our only prior row (29.03). A completed row and score will be recorded in a separately dated note.

Documentation here is MIT like its siblings. The recipe and model remain their authors' under Apache-2.0; the competition data is used under its rules.

## Update, 12:55 UTC: the same recipe now lives in the public notebook

Version 18 of the public notebook [ARC-AGI-2 Public Frontier Perfpatch Evidence Lab](https://www.kaggle.com/code/prvsiyan/arc-agi-2-public-frontier-perfpatch-evidence-lab) is an in-place update that carries this credited recipe with the explanation, credits and deadlines written for readers; the 72 distinct cells of its 17 earlier versions are preserved as inactive cells. Its commit run completed in 1675 s with a schema-valid export ([public-v18-commit-run-receipt.json](public-v18-commit-run-receipt.json)). The next official submission will be made from that public version, so that the notebook's own card reflects the result; the bench row 56951295 above remains the first measurement.
