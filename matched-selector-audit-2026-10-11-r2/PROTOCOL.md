# JSON contracts and evidence boundaries

`matched-selector-registration/1` is a new selector study, separate from an earlier five-arm speed/deep/guard registration. It requires status REGISTERED, study id, a declared pre-export registration, the exact four identity fields, all three selectors and complete ordered challenge-only query descriptors. Each descriptor has query id, task id, index and input SHA256; all query indices of a registered task must be present. It accepts invented or exposed-development evidence only. It rejects an unregistered proposal.

The control binds notebook source, decoder, generator, challenge and environment SHA256 values, source role, model instance and seed policy. These are claims to be independently matched to receipts; the tool does not authenticate a server, inspect model weights or verify that a description of a recipe is true.

`matched-candidate-export/2` binds that registration, identical control/identity, all query descriptors in exact order, and source-bound native/version/run receipts. Every occurrence records its unique id, whole grid, beam score, augmentation score list and ordered unique view identifiers. Candidate groups are reconstructed from the whole grids. Native full kgmon/probmul order and the unchanged kgmon top-two prefix are mandatory. Extra export/query fields are refused.

All registered queries must have an explicit source-bound generation state. Complete with candidates and empty-complete are accepted only when their state agrees with the occurrence list. Missing state, timeout, failed or unadmitted queries cannot be relabelled empty-complete. The caller's generation receipt must prove which state is warranted; its hash alone does not prove its content or completeness.

`matched-selector-seal/1` binds the actual tool source digest, registration, candidate export, run binding, query inventory and all three ordered selector pairs. The library never mutates the export. All phase outputs use exclusive creation and preserve earlier files. A selector's full ranking is compared to the exported full ranking; a submitted pair is compared only to a two-slot prefix. Neither comparison is a truth test.

`query-truth-mask/1` must declare every registered query once. Known items contain a whole grid. Unknown items contain an explicit reason. Missing or extra keys are HOLD. Known truths are tested against every selector pair, with losses and gains both retained. Query-denominator and per-puzzle bounds include all registered queries, even absent candidate support or unknown truths. A lower or upper bound is not an official score.

The separate CLI evaluation verifies every truth-blind binding before opening the truth-mask file. This is source-level ordering and a reproducible process contract, not proof of historical access, model non-exposure or a blinded scientific experiment. Human review, source/rights validation, actual owned-process/native receipts and an exact completed official submission row remain separate requirements.

The shadow legacy G2 function intentionally retains12 and its exact old registration pin. Its full-five mode refuses missing C/D. Its partial mode remains diagnostic. It never rewrites old registrations or completes the other gates.

The field baseline_submitted_pair is the canonical distinct candidate prefix only, not actual two serialized attempts. See SUBMISSION_BOUNDARY.md for the inspected zero-grid constructor padding and the separate native constructor/repair parity HOLD.
