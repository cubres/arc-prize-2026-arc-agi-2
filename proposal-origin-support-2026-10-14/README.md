# Check whether one proposal is being counted twice

A small, dependency-free tool for inspecting a selector's sensitivity to copied
proposal records. It uses invented candidate names and scores, so you can fork
it and inspect the mechanics without a model or ARC answer labels.

![Synthetic proposal-support illustration](duplicate-proposal-support.svg)

The diagram's event-a/b/c names are readable aliases for the frozen control
panel's independent-A/B/C names; the scores and copied-event mechanics agree.

## Run the fixed controls

```sh
python3 -B support_sensitivity.py
```

The recorded execution passed **95 checks across 24 duplicate trials**. Repeated
copies changed the ordered first two candidates in **16 trials**, and changed
the set of retained candidates in **8**. Counting each declared proposal event
once produced **zero changes**. [The compact result](SYNTHETIC_RESULT.json) pins
the executed source and full-stdout hashes. These are measured synthetic
mechanics, not accuracy results or a runtime speedup.

## Use the two selectors

```python
from support_sensitivity import rank

records = [
    {"candidate": "A", "origin": "event-a", "score_aug": [0.2]},
    {"candidate": "B", "origin": "event-b", "score_aug": [0.1]},
    {"candidate": "C", "origin": "event-c", "score_aug": [0.3]},
]
records.append(dict(records[-1]))  # a copy of event-c

raw = rank(records)
unique_events = rank(records, deduplicate_origins=True)
print([row["candidate"] for row in raw[:2]])           # C, B
print([row["candidate"] for row in unique_events[:2]]) # B, A
```

The equation is `support count − mean(per-record mean augmented NLL)`. Lower
augmented NLL favors a candidate; another record raises its support. The raw
selector follows that documented kgmon equation and keeps first-seen order for
ties. The variant ignores exact repeated event identities; different events
producing the same candidate still contribute separately. Conflicting reuse of
an event identity is rejected.

`origin` must identify an individual proposal event, such as a task/run/view/
candidate-index tuple serialized into a stable short name. A whole run or view
can produce multiple distinct proposals and is too broad for this field. Equal
outputs alone do not establish copied events. The tool cannot infer statistical
independence or reconstruct missing provenance.

The controls establish that distinct declared events retain their support. They
do not measure whether that support is useful: "useful signal" in the tool's
printed interpretation describes the motivation, not a measured accuracy result.

Inputs contain exactly `candidate`, `origin`, and `score_aug`. The limits are
256 records, 32 augmented scores per record, and printable ASCII names up to
64 characters. Scores must be finite, nonnegative numbers. The tool copies caller
data, rejects booleans, malformed inputs and conflicting origins, and raises if
aggregation becomes nonfinite. Its arithmetic does not claim NumPy bit parity.

## Why we checked this

[Koushik Rudra's Failed in AIMO](https://www.kaggle.com/code/koushikrudra/failed-in-aimo)
has an indexed public best **33.89 associated with Version 1** in the inspected
public evidence. Its retained Version 1 source already implements kgmon and
probmul3. This tool is an original rewrite of the kgmon equation for a restricted
synthetic interface; it does not import the notebook or claim its public score.
The later induction version cannot inherit the older version's score.

The recipe's [Sorokin Qwen3-4B bfloat16 model variation](https://www.kaggle.com/models/sorokin/qwen3_4b_grids15_sft139/transformers/bfloat16)
lists Version 1 and Apache 2.0. A separate reference audit matched eight actually
hashed JSON files to the saved historical model manifest; the two shard
hashes/sizes were matched using advertised pointers at
[immutable mirror commit a9d1ff8](https://huggingface.co/Grusmannen97/qwen3_4b_grids15_sft139-transformers-bfloat16-v1/commit/a9d1ff829835a19afc633366f5ef50a5ea02a777).
No weight payload was read. That establishes a public reference identity, not
current Kaggle mounts, native compatibility, checkpoint training independence,
or competition admission. The mirror's MIT label is not used to relicense the
original model. Model and utility payloads are absent from this folder.

For a real candidate pool, first freeze its plain-JSON export and individual
proposal-event mapping. Compare selectors on the same ordered queries and
candidates, seal selections before any authorized target reads, and report
retained-output-set changes separately from mere reordering. This fixture alone
does not justify changing a competition selector.

Original tool and documentation: MIT. Baseline equation attribution: Koushik
Rudra, Apache-2.0 Version 1 notebook. See [LICENSE](LICENSE).
