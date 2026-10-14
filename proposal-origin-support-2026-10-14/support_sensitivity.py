# SPDX-License-Identifier: MIT
"""Original bounded synthetic selector probe; no data files, labels or models.

This rewrites only the documented kgmon arithmetic as a standard-library
function. It does not import, execute or transplant a notebook decoder.
Candidate names represent distinct whole outputs. An origin is an explicitly
declared independent proposal source, not an inferred statistical guarantee.
"""
from __future__ import annotations

import json
import math
from collections import OrderedDict
from typing import Any

MAX_RECORDS = 256
MAX_AUGMENTATIONS = 32


def validate(records: Any) -> tuple[dict[str, Any], ...]:
    """Own a bounded caller-detached snapshot; refuse conflicting origin reuse."""
    if type(records) not in (list, tuple) or not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError("records must be a bounded nonempty list or tuple")
    out = []
    origins = {}
    for item in records:
        if type(item) is not dict or set(item) != {"candidate", "origin", "score_aug"}:
            raise ValueError("exact candidate/origin/score_aug fields required")
        candidate, origin = item["candidate"], item["origin"]
        for text in (candidate, origin):
            if type(text) is not str or not 1 <= len(text) <= 64 or not text.isascii():
                raise ValueError("candidate and origin must be short ASCII names")
            if not all(33 <= ord(char) <= 126 for char in text):
                raise ValueError("candidate and origin must be printable names")
        aug = item["score_aug"]
        if type(aug) not in (list, tuple) or not 1 <= len(aug) <= MAX_AUGMENTATIONS:
            raise ValueError("bounded nonempty augmented-score sequence required")
        values = []
        for value in aug:
            if type(value) not in (int, float):
                raise ValueError("scores must be finite nonnegative numbers")
            try:
                value = float(value)
            except (OverflowError, ValueError) as exc:
                raise ValueError("score is outside finite binary64 range") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError("scores must be finite nonnegative numbers")
            values.append(value)
        owned = {"candidate": candidate, "origin": origin, "score_aug": tuple(values)}
        signature = (candidate, owned["score_aug"])
        prior = origins.setdefault(origin, signature)
        if prior != signature:
            raise ValueError("one origin cannot name conflicting proposals or scores")
        out.append(owned)
    return tuple(out)


def rank(records: Any, *, deduplicate_origins: bool = False) -> list[dict[str, Any]]:
    """Descending count-minus-mean-of-means, stable first-seen tie handling.

    With deduplicate_origins=False this preserves the public decoder's scoring
    arithmetic and stable ordering for this restricted finite synthetic domain.
    The alternative discards exact repeated declared origins only. It neither
    deduplicates independent equal outputs nor changes augmented-score pooling.
    """
    if type(deduplicate_origins) is not bool:
        raise ValueError("deduplicate_origins must be a bool")
    owned = validate(records)
    grouped: OrderedDict[str, list[float]] = OrderedDict()
    seen = set()
    for item in owned:
        if deduplicate_origins and item["origin"] in seen:
            continue
        seen.add(item["origin"])
        per_proposal = sum(item["score_aug"]) / len(item["score_aug"])
        grouped.setdefault(item["candidate"], []).append(per_proposal)
    result = []
    for candidate, means in grouped.items():
        score = len(means) - sum(means) / len(means)
        if not math.isfinite(score):
            raise ValueError("score aggregation exceeded finite arithmetic range")
        result.append({"candidate": candidate, "support": len(means), "score": score})
    return sorted(result, key=lambda item: item["score"], reverse=True)


def proposal(candidate: str, origin: str, *scores: float) -> dict[str, Any]:
    return {"candidate": candidate, "origin": origin, "score_aug": list(scores)}


def run_synthetic_probe() -> dict[str, Any]:
    """A fixed invented panel. No correctness labels or evaluation targets."""
    base = [proposal("A", "independent-A", 0.2),
            proposal("B", "independent-B", 0.1),
            proposal("C", "independent-C", 0.3)]
    base_owned_json = json.dumps(base, sort_keys=True)
    control = rank(base)
    invariant = rank(base, deduplicate_origins=True)
    trials = []
    checks = 0

    def require(condition: bool, description: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise RuntimeError(description)

    require(control == invariant, "unique-origin control must match exactly")
    require([row["candidate"] for row in control] == ["B", "A", "C"],
            "hand-calculated control order")
    for duplicates in (1, 2, 4, 8, 16, 32, 64, 128):
        for duplicated in base:
            panel = base + [duplicated] * duplicates
            raw = rank(panel)
            origin_unique = rank(panel, deduplicate_origins=True)
            require(origin_unique == invariant, "exact origin copies must not alter alternative")
            require(raw[0]["candidate"] == duplicated["candidate"],
                    "at least one copied proposal must take first in invented fixture")
            require(raw[0]["support"] == duplicates + 1, "raw vote multiplicity")
            trials.append({"repeated_candidate": duplicated["candidate"],
                           "extra_identical_origin_copies": duplicates,
                           "raw_top_two": [row["candidate"] for row in raw[:2]],
                           "deduplicated_top_two": [row["candidate"] for row in origin_unique[:2]],
                           "raw_top_two_identity_changed":
                               [row["candidate"] for row in raw[:2]] !=
                               [row["candidate"] for row in control[:2]],
                           "raw_two_output_set_changed":
                               {row["candidate"] for row in raw[:2]} !=
                               {row["candidate"] for row in control[:2]}})
    independent = base + [proposal("C", "genuinely-distinct-declared-origin", 0.3)]
    require(rank(independent) == rank(independent, deduplicate_origins=True),
            "alternative must preserve declared independent support")
    require(rank(independent)[0]["candidate"] == "C", "distinct origin may change rank")
    ragged = [proposal("A", "A-1", 0.0), proposal("A", "A-2", 2.0, 2.0, 2.0),
              proposal("B", "B-1", 1.1), proposal("B", "B-2", 1.1)]
    require(rank(ragged)[0]["candidate"] == "A", "per-proposal means are equally weighted")
    require(2 - 1.5 < 2 - 1.1, "flat augmented-score pooling would reverse this witness")
    tied = [proposal("Z", "Z-1", 0.2), proposal("A", "A-1", 0.2)]
    require(rank(tied)[0]["candidate"] == "Z", "baseline tie policy is first-seen")
    require(rank(tied[::-1])[0]["candidate"] == "A", "input order controls exact ties")
    require(json.dumps(base, sort_keys=True) == base_owned_json, "input ownership preserved")
    invalid = [[], True, base * 86,
               [proposal("A", "same", 0.1), proposal("B", "same", 0.1)],
               [proposal("A", "same", 0.1), proposal("A", "same", 0.2)],
               [proposal("A", "a", True)], [proposal("A", "a", -1.0)],
               [proposal("A", "a", float("nan"))],
               [proposal("A", "a", float("inf"))],
               [proposal("A", "a", 10**1000)],
               [proposal("A", "a")], [proposal("A", "a", *([0.1] * 33))],
               [proposal("A", "a b", 0.1)],
               [{**proposal("A", "a", 0.1), "target": "forbidden-extra-field"}]]
    for item in invalid:
        try:
            rank(item)
        except ValueError:
            checks += 1
        else:
            raise RuntimeError("invalid invented input was admitted")
    return {"schema": "arc2.original.synthetic-origin-support-probe.v1",
            "scope": "invented candidate names and scalar scores only",
            "status": "PASS", "checks_passed": checks,
            "fixed_trials": len(trials), "max_trial_records": 131,
            "control_top_two": [row["candidate"] for row in control[:2]],
            "raw_pair_identity_changes": sum(row["raw_top_two"] != ["B", "A"] for row in trials),
            "raw_two_output_set_changes": sum(row["raw_two_output_set_changed"] for row in trials),
            "alternative_pair_identity_changes": sum(row["deduplicated_top_two"] != ["B", "A"] for row in trials),
            "trial_receipts": trials,
            "competition_data_read": False, "models_loaded": False,
            "targets_or_truth_labels_used": False,
            "baseline_numpy_bit_parity_claim": False,
            "native_runtime_or_official_accuracy_claim": None,
            "interpretation": "Duplicate-origin sensitivity is a mechanism witness, not evidence of better accuracy. Distinct genuine proposal support remains useful signal."}


if __name__ == "__main__":
    print(json.dumps(run_synthetic_probe(), indent=2, sort_keys=True, allow_nan=False))
