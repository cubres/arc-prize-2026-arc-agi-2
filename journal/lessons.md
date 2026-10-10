# Lessons from the ARC-AGI-2 campaign

Each lesson gives the situation, the rule adopted, the evidence (a ledger row, a date or a source note), and how the rule was checked. Labels follow the README legend.

## 1. A training worker failed on its first training-mode forward

- **Situation.** The bench worker's version 10 raised an AttributeError at about 338 seconds, on the first training-mode forward after the baseline decodes (ledger inventory, 8 October).
- **Root cause (pinned library sources) [V].** The trainer's constructor leaves the model in inference mode. A later training-mode call with the library's default checkpointing flag switched checkpointing on for every module, with no checkpoint function installed. The first training forward then failed.
- **Fix and rule.** Pass the checkpointing flag explicitly at every mode switch. Add a preflight gate that asserts training mode and no checkpointing flags before the first manual forward. Restore the decode-time logits flag after training, because the training wrapper resets it. The second bug was found by replaying the mode writers in order.
- **Evidence.** The version 10 error (inventory). Version 11 then ran all 32 steps in 362 seconds, with the gate passing.
- **Check.** An offline replay reproduced the exact version 10 error text, and the version 11 order passed. A counterfactual with the flag at zero reproduced the adapted-decode failure. The offline suites had 37 and 24 checks **[V]**. Version 11 was a null result on one task, so it proves mechanics only.

## 2. Pin the environment and the kernel overrides on every push

- **Situation.** The recipe's original model mount path no longer existed. A public version that predated the pinned image ran a different container image (prefix 37c64f7d) from the pinned one (prefix 320043e1) **[V]**.
- **Rule adopted.** Every push states the container image, the utility script that installs the library versions, the model source, the machine type and the competition source. Add a fallback path resolver.
- **Evidence.** The 8 October push overrides. The credited-rerun note (official-submissions/2026-10-08-v12-credited-rerun), which records a watchdog pass on the pinned image.
- **Check.** A dry run before each push, comparing candidate cells with the server copy.

## 3. A credited rerun is one draw from a wide distribution

- **Situation.** Reruns of the public recipe, including near-identical copies, scored from 28.06 to 33.89 **[V as displayed, P]**.
- **Rule adopted.** Report one rerun as one draw. Compare it with the distribution of reruns, not with the best public card.
- **Evidence.** Row 56951295 scored 31.11 (COMPLETE), recorded on 10 October. Across 24 reruns the mean is 30.7 and the standard deviation 1.5 **[mixed]**. The 33.89 card is a lucky draw **[I]**.
- **Check.** A recount of the 25 listed values gave mean 30.57 and standard deviation 1.69 **[V]**. The conclusion did not change.

## 4. Find the salted hash and pin it

- **Situation.** The recipe seeded candidate scoring with the built-in string hash of the puzzle key. Python salts that hash per process unless PYTHONHASHSEED is set **[V, code]**, so each run may use a different augmentation set **[P, topic 742027]**.
- **Rule adopted.** Use a stable hash (crc32) of the puzzle key, fix PYTHONHASHSEED, and reseed per puzzle. The crc32 is over the puzzle key, not the candidate bytes. That was a design decision and was not measured.
- **Evidence.** Version 19 (row 57016777, pending) carries the change.
- **Check.** 33 of 33 offline checks, normal and optimised mode. The new seed is invariant to PYTHONHASHSEED and the old one is not. The pin lowers variance but does not remove bf16 or attention nondeterminism **[V, I]**.

## 5. Plan with the hidden run's duration, not the commit run's

- **Situation.** Public commit runs took 1,586 to 1,902 seconds. The campaign's 29.03 run took 717 minutes and hit the cap. A public runtime monitor shows a band median near 650 minutes **[V as displayed]**.
- **Rule adopted.** Plan with the hidden-run runtime. Set the notebook's own soft end and hard stop below the 12-hour limit, and leave the session timeout unset for the scored rerun. The credited rerun used a soft end of 11 hours 30 minutes and a hard stop at 11 hours 40 minutes **[V]**.
- **Evidence.** Row 55001244 (717 minutes). The credited-rerun note. A correction of 8 October: the version 12 and 18 pushes carried "session timeout None", although a 1,800-second value had appeared in a preflight file.
- **Check.** Arithmetic: 240 tasks at about 640 seconds each over 4 workers is about 640 minutes **[I]**. The hidden task count is still open, and it changes this conclusion.

## 6. A commit run checks the plumbing, not the answers

- **Situation.** The commit run decodes only the four smoke tasks. The rest of the submission file holds placeholders until the hidden rerun. In version 19's file, 5 of 172 output slots held a real candidate **[V]**.
- **Rule adopted.** Judge a commit run by status, schema, the four decoded tasks and cell identity, not by score or answer count.
- **Evidence.** Rows 57016777 and 57040312, and the version 19 and version 20 candidate notes.
- **Check.** The earlier V20 candidate passed 143 of 143 offline checks in both modes. The candidate published as public version 20 (the V21 build) passed 262 of 262. With its flag off, it was byte-identical to version 19 on the 79 pool files **[V]**.

## 7. Keep the bench record and the public record apart

- **Situation.** The same recipe ran on a private bench worker (row 56951295) and on the public notebook (versions 18, 19 and 20).
- **Rule adopted.** The owner's instruction of 8 October: update existing notebooks only, and submit from the public notebook. Validate on the bench, then submit from the public version. Never present a bench row as the public notebook's result.
- **Evidence.** Row 56951295 (bench, 31.11). Row 57016777 (public version 19, pending). Version 18 was never submitted, because its scheduled runner did not run.
- **Check.** The 10 October row-status snapshot lists both rows with their roles.

## 8. Label each timeout's cause, and check the cap between batches

- **Situation.** The V13 harness flagged three of eight tasks as timed out. Two stopped below the 1,200-second cap, so the 1,800-second global end was the cause. One label covered both causes **[V]**.
- **Rule adopted.** Record each stop's cause separately. The per-task cap is checked only between decode batches, so a task can overrun by one batch. In V13, task 221dfab4 stopped at 1,208.8 seconds, an overrun of 8.8 seconds.
- **Evidence.** The V13 result note, section 5 and appendix A.
- **Check.** The solver log and pool-file times bracket the end-time estimate. The split labels are in an evaluator change that was built but not pushed. It awaits independent review **[V]**.

## 9. Operations: scheduled runners and push limits

- **Situation.** A midnight runner armed on 8 October did not run, because the session restarted and every detached runner died **[V]** (ledger, 9 October 17:54 UTC). Separately, a push to another notebook was refused at 12:30 UTC on 8 October with "Maximum batch GPU session count of 2 reached"; no version was created **[V]**.
- **Rule adopted.** Keep the slot check and the submit step in a process that can be re-run from state on disk. Check the day's slot count before each submission. Count the account's queued batch GPU sessions before a push, and on refusal retry later without assuming a version exists.
- **Evidence.** Row 57016777, submitted at 17:56:28 UTC on 9 October after the check showed 0 of 1 slots used.
- **Check.** The submission log records the slot count before each call.

## 10. Check the numbers before building the gate

- **Situation.** A two-final hedge was justified by a standard deviation of 1.69, taken from 25 public scores of many codebases. Same-code evidence gave 0.25 to 0.71 as a plausible range **[V, I]**. An fp32 adapter change was proposed to recover updates that bf16 rounding loses. A CPU product check showed bf16 keeps 87 to 96 percent of the nominal update **[V]**.
- **Rule adopted.** Estimate run-to-run variance only from repeated runs of one frozen version. Compute a mechanism's magnitude before building a gate for it. Write each test's power calculation next to the test, and do not claim an effect the test cannot detect.
- **Evidence.** The hedge and fp32 verification notes, in the strategy folder. Corrected gains: the hedge +0.1 to +0.4 points, not +0.3 to +0.9; the fp32 change at most about +0.03 to +0.11 per run, sign not established **[I]**. A 24-task panel can only detect at least five discordant outputs at p 0.05 **[I]**.
- **Check.** The 25-value mean and standard deviation were recomputed (30.573 and 1.688). The two-draw factor 0.5642 matches 1 over the square root of pi.

## 11. Report negative results with their counts and their reference

- **Situation.** Several lines of work gave zero or negative results: a symbolic grammar, an object grammar, a local-rule family, a pilot with one solved output, an induction add-on with no verified programs, and TRM with no gain.
- **Rule adopted.** Publish each negative result with its count, its reference and its limits. Keep it out of score claims. Do not spend quota on a grammar that scores zero on the public set.
- **Evidence.** Public READMEs: cpu-object-relational-discovery-2026-10-10, cpu-symbolic-screen-2026-10-09 and cpu-local-rules-discovery-2026-10-09. The V13 result note. The sweep's induction check (0 verified programs, 0 promoted, 120 tasks).
- **Check.** The local-rule study's independent review passed 746 checks. The object grammar's positive controls are in its folder.
