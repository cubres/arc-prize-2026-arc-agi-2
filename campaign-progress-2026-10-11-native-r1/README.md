# ARC-AGI-2 progress: isolate generation, selection and spare-budget search

The official `prvsiyan` account snapshot at 19:11 UTC on 11 October 2026 distinguishes a strong credited control from a weaker combined change and an unscored successor.

| Official evidence | Exact row | State |
|---|---:|---|
| Best completed credited control | 56951295 | COMPLETE — **31.11** |
| Selector/seed bundle, public Version 19 | 57016777 | COMPLETE — **28.47** |
| Latest accepted successor | 57040312 | UNKNOWN — score absent |

The [31.11 control](https://www.kaggle.com/code/prvsiyan/zz-gpuchk-845399?scriptVersionId=356375763) follows Koushik Rudra's credited `failed-in-aimo` recipe: NVARC Qwen3-4B initialization and per-task LoRA test-time training. That recipe is upstream work. Our [Version 19](https://www.kaggle.com/code/prvsiyan/arc-agi-2-public-frontier-perfpatch-evidence-lab?scriptVersionId=356491928) changes final-attempt selection together with the seed bundle. Its lower completed score argues against adopting the combined behavior; it does not isolate either change's causal effect. The [latest accepted version](https://www.kaggle.com/code/prvsiyan/arc-agi-2-public-frontier-perfpatch-evidence-lab?scriptVersionId=357018998) still needs its exact completed row.

The next useful study freezes candidate pools from the credited generation path and compares final selectors on identical candidates. Seed changes require a separate comparison. This avoids confusing better selection with a different pool, generation coverage or runtime. Time-capped and empty tasks stay in the accounting.

A fill-only supplement can preserve the ordered grids actually supplied to its adapter and fill vacant attempt slots. That software invariant cannot prove preservation of a stronger baseline whose upstream candidates, seeds or timing differ. An original spatial decision-program screen did not establish a useful scoring supplement, so it is published as a small negative baseline rather than a recommended overlay.

For a fork, the original [spatial-program package](https://github.com/cubres/arc-prize-2026-arc-agi-2/tree/9cb879dd2bde144535ef2aeafdc56cb2775c4937/spatial-program-screen-2026-10-11) includes invented controls, a safe fill adapter, separate sealed prediction/evaluation phases and its diagnostic diagram. The [native evidence addendum](https://github.com/cubres/arc-prize-2026-arc-agi-2/tree/2a80a2852556223c7071660c191f42145e4b2a23/native-evidence-2026-10-11) explains why terminal execution and matching source/arm receipts still need qualification. Development exposure and compute limits remain explicit; a fresh seal alone does not make a previously inspected task unseen.

Koushik Rudra, the NVARC model lineage and their original licenses retain their attribution. The original tools here do not redistribute competition grids, reference answers or upstream solver code.
