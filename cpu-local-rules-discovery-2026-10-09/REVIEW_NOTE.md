# Independent reproduction and timing limits

An independent reviewer replayed all 120 public tasks and reproduced all 172
substantive predictions and the evaluation bytes. The review passed 746 checks:
15 tasks had a demonstration-fitted configuration, 29 configurations fitted in
total, and one output was exactly correct. That output was already covered by
the frozen reference. Both unique incremental outputs and deployable fill-only
improvements remain zero. Promotion remains on hold.

The six original positive controls reproduced byte for byte. A separately
invented local-rule control also passed across a changed color palette and grid
size. These results check mechanics; they establish no hidden-task performance.

The recorded maximum of 0.031998 seconds applies only to records carrying timing
fields. Thirty-nine early shape-mismatch or insufficient-demonstration
abstentions omit per-task timing and timeout fields. The whole prediction run
was measured at 0.440171 seconds. No recorded task timed out.

The two-second task and 90-second whole-run budgets are cooperative. Stamping,
application, grid validation and serialization include unchecked sections;
demonstration and test counts are not bounded, and the runner lacks a final
whole-run deadline check. They are not hard execution limits.

The actual challenge file contained test inputs without test truth. The solver
received demonstrations and test inputs without identifiers. This remains an
already-exposed public discovery experiment. Unsigned source and prediction
seals bind the current bytes and support reproduction; they do not independently
prove chronology or historical non-exposure. The evaluator source is outside
the pre-prediction seal.

The full local review receipt is intentionally excluded because it contains
task-level details. Its SHA256 is
`4b92969f29f85235fb62631fe1a7c96158d4ce0e47fb39317d3eb1d66e06d7c6`.
No official score, external submission, GPU run, or notebook mutation was made
by this experiment or its review.
