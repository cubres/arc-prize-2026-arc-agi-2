# A candidate pair is not yet a serialized submission

The export field `baseline_submitted_pair` records only the distinct native kgmon ranking prefix of length at most two. Its name is historical protocol wording; this tool does not construct, parse or verify an actual submission. The comparator's hit fractions describe candidate-pair support only.

The inspected credited-recipe loader initializes both serialized attempts to `[[0]]` and fills the first available ranking entries. It does not repeat a single candidate:

| Distinct candidate pool | Canonical pair audited here | Inspected constructor's two attempt values |
| --- | --- | --- |
| Empty | `[]` | `[[0]]`, `[[0]]` |
| One candidate A | `[A]` | `A`, `[[0]]` |
| Two or more | `[A, B]` | `A`, `B` |

This is a static finding from the preserved recipe text. The actual installed loader, runtime validation/repair, fallback behavior and exact final serialization need source/runtime parity qualification. A native callback returning a ranking does not prove those later stages ran that way. No downloaded constructor implementation is included in this original explanation.

Because `[[0]]` is itself a valid grid, padding can supply candidate-independent support when the truth is that grid. The toy's empty-pool truth `[[0]]` counts as a candidate-pair miss; the inspected constructor could match it using a fallback. Do not label the toy's candidate-pair fractions as whole-submission accuracy. A genuine `[[0]]` emitted occurrence is retained as a normal candidate and never mistaken for absence.

The capture adapter verifies full native ranking order and the canonical top-two prefix. It does not qualify final two-attempt padding, repetition, repair or file bytes. A later source-bound native comparison must record the canonical prefix and both actual serialized attempts, including the constructor/repair hashes and any fallback reasons, before a submission-preservation or outcome claim.

All absent/incomplete pool states remain explicit; a padded file does not prove generation completed. Positional view identifiers likewise preserve order only and do not attest which geometric/color augmentations ran. Their semantic identities require source and seed receipts.
