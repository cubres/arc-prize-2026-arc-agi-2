# Freeze first, score second: a small public-development TTT harness

This original standard-library package orchestrates one fixed before/after adaptation experiment and verifies its complete prediction packet before evaluation. The reusable pieces are strict token parsing, source hashing, exclusive output creation and separate-process scoring. The shipped protocol is specialized: public task `3dc255db`, query 0, 32 requested adaptation steps, 128 views, fixed seeds, greedy identity/transpose attempts and a 930-token cap.

It is not a neural solver or a completed quality result. The example below is entirely invented and performs no learning. No real challenge grids, solution files, predictions, model weights or private notebook sources are included.

## Run the working toy example

Python 3.10+ on POSIX macOS/Linux is sufficient; there are no third-party dependencies. The immutable-file helper uses `os.fchmod` and POSIX permission bits. Windows support has not been established. Keep all Python files together in this directory; sibling imports are intentional.

```sh
python -B verify_source_and_demo.py --output /tmp/arc2-source-check-001
python -B run_synthetic_demo.py --output /tmp/arc2-demo-001
```

Use a **new directory each time**. Existing outputs are preserved and refused. The demo first runs a scientific worker that emits four invented attempts, freezes them, and exits. Only then does the parent create an invented truth file and launch the evaluator in a second process. Its expected `False → True` exact-match comparison is a control-flow fixture, not ARC accuracy or training evidence. The synthetic adapter's model/view hashes and gradient/update numbers are explicitly invented.

One invented attempt is incomplete and remains invalid. Malformed predictions are retained and scored as invalid; incomplete, altered or missing packets are refused before the evaluator touches a solution file.

## Attach your own engine

Implement `build_adapter()` in a sibling `.py` file following `adapter_interface.Adapter`. `prepare` must complete model/checkpoint/tokenizer/initialization/head/actual-optimizer checks before decoding and return identity hashes. `decode` returns the **entire** generated token suffix, exact decoded bytes, actual prompt token hash and stage state hash. `adapt` requests exactly 32 steps and reports the required finite first-step/head-gradient/positive-coordinate-update summary, later finite state, membership and count checks.

```sh
python -B run_experiment.py \
  --output /tmp/arc2-real-study-001 \
  --adapter-file my_engine.py \
  --challenge-file /path/to/arc-agi_evaluation_challenges.json
```

The challenge file must match the preregistered hash. Only public training demonstrations and the public test **input** enter the adapter. The driver pins itself, the helpers and your sibling adapter, establishes the protocol, decodes twice, adapts, decodes twice, and freezes all four outputs. The driver itself never opens a solution file or imports the evaluator; an arbitrary external backend's non-access is not attested.

The engine's numerical summaries are **backend reported**. A source hash plus a boolean or step counter does not attest live compiled Torch execution, correct initialization, GPU cleanup or dataset origin. Supply and review real native evidence separately. This source-only driver contains no GPU quota launcher, submission operation, network request, dependency installer, or process-group supervisor. Set compute limits outside it before running your model.

Once the worker exits and your own GPU/process teardown is confirmed, pass the printed protocol and manifest hashes to the separate evaluator:

```sh
python -B evaluate_frozen_predictions.py \
  --output-dir /tmp/arc2-real-study-001 --source-dir . \
  --protocol-sha256 YOUR_PROTOCOL_SHA256 \
  --manifest-sha256 YOUR_MANIFEST_SHA256 \
  --public-solutions /path/to/arc-agi_evaluation_solutions.json \
  --receipt /tmp/arc2-real-study-001/publicdev-comparison.json
```

The evaluator verifies every source, protocol, token artifact, decoded artifact and read-only mode before it even stats or reads the solution file. It writes parse-validity and exact-match booleans; it never writes the truth grid. Hashes/read-only modes are a procedural freeze, not OS isolation from a privileged actor or protection against another process reading answers independently.

## Parsing and HOLD behavior

The canonical vocabulary uses digit IDs 0..9, newline 10 and EOS 15. Token IDs 11..14, role/pad tokens, missing EOS, extra tokens after EOS, trailing newlines, ragged rows and oversized grids remain invalid. No tokens are dropped to make a grid pass. Transpose attempts are inverted before comparison. See `grid_tokens.py` for the exact error-code set.

`ValueError` messages beginning with `HOLD` mean the packet or protocol cannot be trusted: wrong source hash, changed protocol, missing artifact, writable artifact, changed prompt hash, changed attempt order, unsafe path or source/manifest mismatch. Preserve that output directory, inspect the issue and rerun into a new directory. An ordinary malformed prediction is different: it stays in the sealed packet with a parser error and a false exact-match flag.

## Source checks and scope

`SOURCE_MANIFEST.json` binds the listed package source/docs/license inputs. The verifier checks hashes, runs the synthetic demo in a new directory, confirms two-stage truth ordering and scope labels, and tests strict malformed-token and false first-update refusals. It uses no official data, models, GPUs or network. Both normal and optimized Python use explicit checks rather than removable assertions.

The three core helpers are retained byte-exact from the independently reviewed original study tooling. The runner, engine interface and toy adapter are new, original code. [The experiment note](../../../experiments/2026-10-07-native-head-update/README.md) distinguishes the actual one-step native evidence from this source-only package and the pending 32-step study.

Apache-2.0 applies to these original files; the complete license and scope are in `LICENSE` and `NOTICE`. Official data, checkpoints, Unsloth, Torch and upstream neural recipes are linked separately and are not bundled or relicensed here.
