# Stable seed binding, with an honest receipt

This small, standard-library Python 3.9+ tool binds an exact query key to the
portable S1 rule:

```text
payload = b"arc2-rescore-seed-v1\0" + original_bk.encode("utf-8", errors="strict")
seed = int.from_bytes(SHA256(payload), "big") % 2**20
```

It implements seed binding only. It contains no augmentation, candidate scoring,
model, notebook integration, scheduling, or competition-submission logic.

```sh
python3 stable_seed_binding.py 00d62c1b_0
python3 verify_seed_binding.py --output verification-first-run
```

The example key produces seed **829663**. The CLI prints a JSON receipt to stdout;
it never writes a result file. The verifier writes its receipt into a new output
directory and refuses to reuse an existing one. All checks remain active under
`python3 -O`; no correctness gate relies on an `assert` statement.

For library use:

```python
from stable_seed_binding import bind_seed, binding_receipt

binding = bind_seed("00d62c1b_0")  # immutable record
receipt = binding_receipt("00d62c1b_0")  # detached JSON-compatible dictionary
```

Inputs must be exact `str` objects, containing 1–256 strictly encodable UTF-8
bytes. String subclasses, empty/oversized values and lone surrogates are refused.
Case, spaces, NUL and Unicode normalization forms are preserved exactly. The
library supports NUL; operating-system command-line arguments cannot contain it.
The bound limits tool processing of an input, not memory already allocated by a
caller. No input is executed or used as a filesystem path.

The full payload digest binds the fixed domain and exact key. It does not bind
task contents, weights, a candidate ledger, or an executing model. The receipt
separately fingerprints this implementation's on-disk source bytes. That is not
a signature or proof that those bytes were loaded into an executing process.

## A seed is not an identity

The reduced space has only 1,048,576 values. These two different keys deliberately
demonstrate the distinction:

| Exact key | Reduced seed |
|---|---:|
| `collision-probe-681_0` | 477269 |
| `collision-probe-1298_0` | 477269 |

Their full payload digests differ. Keep the exact domain/key binding and full
digest; never key an identity ledger or scoring cache solely by the reduced seed.

## What a later ARC integration must preserve

The observed public baseline already uses eight common scoring views within a
query. Its `hash(bk)` seed can change between fresh Python interpreters. This
tool replaces that seed rule; it does not add new common views.

A later integration must independently verify original transformation order,
all eight views including symmetric duplicates, demo ordering/context shortening,
the two four-view scoring batches, EOS scoring, exact-grid grouping, candidate
sequence and occurrence-count aggregation. None is implemented or verified here.
Fix NumPy/runtime versions as well. Stable seeds alone do not establish identical
GPU scores or tied ranking order; unsorted filesystem input is a separate issue.

The [seed-binding diagram](seed-binding.svg) is schematic. Its eight-view cards
describe an external integration obligation, not measured augmentation outputs.

## Provenance and claim limits

Code is independently written for this artifact and released under the included
MIT license. The research reference is the Apache-2.0-declared public
[Reproduce NVARC notebook](https://www.kaggle.com/code/rokaiyasomapti/reproduce-nvarc-2025-results).
No upstream implementation code or model assets are bundled. See
[PROVENANCE.json](PROVENANCE.json) for the exact source snapshot and rule scope.
The model's license does not license all code in the author repository.

There is **no native ARC2 execution, speed, answer-quality or generalization
claim**. Cross-process checks cover this tool's receipts, not a complete solver.
Generated verification evidence is excluded from the source manifest so that
new verification runs never overwrite or redefine the original source packet.
