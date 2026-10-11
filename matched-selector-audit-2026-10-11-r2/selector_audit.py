# SPDX-License-Identifier: MIT
"""Original bounded JSON-only selector diagnostic. No model/pickle/network code.

The arithmetic hypotheses are credited to the permitted Failed in AIMO V1
decoder: count minus mean view NLL, and baseline-three beam/view aggregation.
This independent implementation requires exported native ranking parity before
sealing selections. A truth mask is opened only by the separate evaluate phase.
All output files are created exclusively; existing artifacts remain intact.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

RELEASE = "original-matched-selector-audit/2"
MAX_BYTES = 64 * 1024 * 1024
LEGACY_GATE_SHA256 = "37db933a5d803b6b66235070d8fc3ba460113e599ddfc704f2e36214f2c696f6"
SELECTORS = ("kgmon2", "probmul2", "anchored_distinct2")


class Hold(ValueError):
    """A named failed contract, never a candidate promotion."""


def require(condition, reason):
    if not condition:
        raise Hold(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=True).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def source_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def grid_id(grid):
    require(type(grid) is list and 1 <= len(grid) <= 30, "BAD_GRID_ROWS")
    require(all(type(row) is list for row in grid), "BAD_GRID_ROW_TYPE")
    width = len(grid[0])
    require(1 <= width <= 30 and all(len(row) == width for row in grid), "BAD_GRID_COLUMNS")
    require(all(type(x) is int and 0 <= x <= 9 for row in grid for x in row), "BAD_GRID_COLOR")
    return digest(grid)


def finite(value):
    require(type(value) in (int, float), "NONFINITE_OR_NONNUMERIC_SCORE")
    try:
        number = float(value)
    except OverflowError as exc:
        raise Hold("NONFINITE_OR_NONNUMERIC_SCORE") from exc
    require(math.isfinite(number), "NONFINITE_OR_NONNUMERIC_SCORE")
    return number


def sha(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "BAD_SHA256")
    return value


def registration_check(reg):
    require(reg.get("schema") == "matched-selector-registration/1", "REGISTRATION_SCHEMA")
    require(reg.get("status") == "REGISTERED", "UNREGISTERED_PROPOSAL")
    require(reg.get("evidence_class") in ("invented", "exposed_development"), "EVIDENCE_CLASS")
    require(reg.get("study_id") and reg.get("registered_before_candidate_export") is True,
            "STUDY_REGISTRATION_REQUIRED")
    require(reg.get("coverage_policy") == "all_queries_present_empty_explicit", "COVERAGE_POLICY")
    require(reg.get("selectors") == list(SELECTORS), "SELECTOR_SET_CHANGED")
    identity = reg.get("identity", {})
    require(set(identity) == {"id", "id_no", "title", "code_file"}, "IDENTITY_FIELDS")
    require(type(identity["id_no"]) is int and identity["id_no"] > 0
            and all(type(identity[k]) is str and identity[k] for k in ("id", "title", "code_file")),
            "IDENTITY_VALUE")
    control = reg.get("control", {})
    for k in ("source_sha256", "decoder_sha256", "generator_sha256", "challenge_sha256", "environment_sha256"):
        sha(control.get(k))
    require(control.get("source_role") == "credited_control_recipe", "STRONG_CONTROL_ROLE_REQUIRED")
    require(control.get("seed_policy") and control.get("model_instance")
            and control.get("scientific_exposure") == reg["evidence_class"], "CONTROL_CONTRACT")
    queries = reg.get("queries")
    require(type(queries) is list and 1 <= len(queries) <= 4096, "QUERY_INVENTORY_SIZE")
    ids = [q.get("query_id") for q in queries]
    require(all(type(k) is str and k for k in ids) and len(set(ids)) == len(ids), "QUERY_ID_DUPLICATE_OR_MISSING")
    for q in queries:
        require(set(q) == {"query_id", "task_id", "query_index", "input_sha256"}, "QUERY_DESCRIPTOR_FIELDS")
        require(type(q["task_id"]) is str and q["task_id"] and type(q["query_index"]) is int
                and q["query_index"] >= 0, "QUERY_DESCRIPTOR_VALUE")
        sha(q["input_sha256"])
    by_task = {}
    for q in queries:
        by_task.setdefault(q["task_id"], []).append(q["query_index"])
    require(all(sorted(v) == list(range(len(v))) for v in by_task.values()), "INCOMPLETE_TASK_QUERY_INVENTORY")
    return ids


def rank_occurrences(occurrences):
    """Preserve first occurrence group order as the declared stable-tie policy.

    Occurrences of the same complete grid contribute independently. Augmentation
    means are first taken per occurrence, not over a flattened variable-length
    view list. Summation uses Python floats; native parity is a mandatory guard.
    """
    require(type(occurrences) is list and len(occurrences) <= 100000, "POOL_OCCURRENCE_SIZE")
    groups = {}
    occurrence_ids = set()
    for occurrence in occurrences:
        require(type(occurrence) is dict, "OCCURRENCE_TYPE")
        require(set(occurrence) == {"occurrence_id", "grid", "beam_score", "score_aug", "view_ids"},
                "OCCURRENCE_FIELDS")
        oid = occurrence["occurrence_id"]
        require(type(oid) is str and oid and oid not in occurrence_ids, "OCCURRENCE_ID_DUPLICATE")
        occurrence_ids.add(oid)
        cid = grid_id(occurrence["grid"])
        beam = finite(occurrence["beam_score"])
        aug = occurrence["score_aug"]
        require(type(aug) is list and 1 <= len(aug) <= 256, "AUGMENTATION_VIEW_COUNT")
        aug = [finite(v) for v in aug]
        views = occurrence["view_ids"]
        require(type(views) is list and len(views) == len(aug)
                and all(type(v) is str and v for v in views) and len(set(views)) == len(views), "AUGMENTATION_VIEW_IDS")
        group = groups.setdefault(cid, {"grid": occurrence["grid"], "beams": [], "aug": [], "occurrences": []})
        group["beams"].append(beam)
        group["aug"].append(aug)
        group["occurrences"].append(oid)
    scores = {}
    for cid, group in groups.items():
        n = len(group["beams"])
        kg = n - sum(sum(v) / len(v) for v in group["aug"]) / n
        pm = sum(3.0 - b for b in group["beams"]) + sum(sum(3.0 - x for x in v) for v in group["aug"]) / n
        finite(kg)
        finite(pm)
        scores[cid] = {"kgmon": kg, "probmul": pm, "occurrence_count": n}
    kg_order = sorted(groups, key=lambda cid: scores[cid]["kgmon"], reverse=True)
    pm_order = sorted(groups, key=lambda cid: scores[cid]["probmul"], reverse=True)
    anchor = kg_order[:1]
    if anchor:
        alternative = next((cid for cid in pm_order if cid != anchor[0]), None)
        if alternative is None:
            alternative = next((cid for cid in kg_order[1:] if cid != anchor[0]), None)
        if alternative is not None:
            anchor.append(alternative)
    return {"native_order_expectations": {"kgmon": kg_order, "probmul": pm_order},
            "pairs": {"kgmon2": kg_order[:2], "probmul2": pm_order[:2], "anchored_distinct2": anchor},
            "candidate_ids_in_first_seen_order": list(groups), "scores": scores}


def prepare(reg, export):
    ids = registration_check(reg)
    before = digest(export)
    require(export.get("schema") == "matched-candidate-export/2", "EXPORT_SCHEMA")
    require(set(export) == {"schema", "registration_sha256", "identity", "control", "queries", "run_binding"}, "EXPORT_FIELDS")
    run = export.get("run_binding", {})
    require(set(run) == {"native_id", "kernel_version", "notebook_source_sha256", "generation_receipt_sha256", "loaded_module_manifest_sha256"}, "RUN_BINDING_FIELDS")
    require(type(run["native_id"]) is str and run["native_id"].isdigit()
            and type(run["kernel_version"]) is int and run["kernel_version"] > 0, "RUN_ID_OR_VERSION")
    for key in ("notebook_source_sha256", "generation_receipt_sha256", "loaded_module_manifest_sha256"):
        sha(run[key])
    require(run["notebook_source_sha256"] == reg["control"]["source_sha256"], "RUN_SOURCE_DRIFT")
    require(export.get("registration_sha256") == digest(reg), "REGISTRATION_BINDING")
    require(export.get("identity") == reg["identity"] and export.get("control") == reg["control"],
            "IDENTITY_OR_CONTROL_DRIFT")
    queries = export.get("queries")
    require(type(queries) is list and [q.get("query_id") for q in queries] == ids, "EXACT_QUERY_ORDER_OR_COVERAGE")
    selections = []
    for descriptor, query in zip(reg["queries"], queries):
        require(set(query) == {"query_id", "descriptor", "generation_state", "occurrences", "native_rankings", "baseline_submitted_pair"}, "QUERY_EXPORT_FIELDS")
        require(query.get("descriptor") == descriptor, "QUERY_INPUT_DESCRIPTOR_DRIFT")
        require(query.get("generation_state") in ("complete", "empty_complete"), "INCOMPLETE_GENERATION")
        ranking = rank_occurrences(query.get("occurrences"))
        require(bool(query["occurrences"]) == (query["generation_state"] == "complete"), "EMPTY_STATE_MISMATCH")
        require(query.get("native_rankings") == ranking["native_order_expectations"], "NATIVE_SELECTOR_PARITY_MISMATCH")
        require(query.get("baseline_submitted_pair") == ranking["pairs"]["kgmon2"], "BASELINE_TOP2_PREFIX_MISMATCH")
        selections.append({"query_id": descriptor["query_id"], "task_id": descriptor["task_id"],
                           "candidate_pool_sha256": digest(query["occurrences"]),
                           "candidate_count": len(ranking["candidate_ids_in_first_seen_order"]),
                           **ranking})
    require(before == digest(export), "INPUT_MUTATED")
    return {"schema": "matched-selector-seal/1", "release": RELEASE,
            "tool_source_sha256": source_sha256(), "registration_sha256": digest(reg),
            "candidate_export_sha256": before, "run_binding": copy.deepcopy(run), "query_inventory_sha256": digest(reg["queries"]),
            "selections": selections, "truth_access": "NONE_IN_PREPARE",
            "evidence_class": reg["evidence_class"], "adoption": "HOLD_SEPARATE_NATIVE_AND_SCIENTIFIC_REVIEW"}


def evaluate(reg, export, seal, truth_mask):
    require(seal == prepare(reg, export), "SEALED_SELECTION_CHANGED")
    ids = [q["query_id"] for q in reg["queries"]]
    require(truth_mask.get("schema") == "query-truth-mask/1", "TRUTH_MASK_SCHEMA")
    require(truth_mask.get("registration_sha256") == digest(reg), "TRUTH_REGISTRATION_BINDING")
    truths = truth_mask.get("queries", {})
    require(set(truths) == set(ids), "TRUTH_MASK_MISSING_OR_EXTRA_QUERY")
    truth_ids, unknown = {}, []
    for qid in ids:
        item = truths[qid]
        require(item.get("state") in ("known", "unknown"), "TRUTH_STATE")
        if item["state"] == "known":
            require(set(item) == {"state", "grid"}, "KNOWN_TRUTH_FIELDS")
            truth_ids[qid] = grid_id(item["grid"])
        else:
            require(set(item) == {"state", "reason"} and type(item["reason"]) is str and item["reason"],
                    "UNKNOWN_TRUTH_REASON")
            unknown.append(qid)
    task_counts = {}
    for q in reg["queries"]:
        task_counts[q["task_id"]] = task_counts.get(q["task_id"], 0) + 1
    result = {}
    baseline_hits = {q["query_id"]: truth_ids[q["query_id"]] in q["pairs"]["kgmon2"]
                     for q in seal["selections"] if q["query_id"] in truth_ids}
    for name in SELECTORS:
        hits, gains, losses, shared_hits, shared_misses = [], [], [], [], []
        weighted_hits = weighted_unknown = weighted_gain = weighted_loss = 0.0
        for q in seal["selections"]:
            qid = q["query_id"]
            weight = 1.0 / task_counts[q["task_id"]] / len(task_counts)
            if qid not in truth_ids:
                weighted_unknown += weight
                continue
            hit = truth_ids[qid] in q["pairs"][name]
            old = baseline_hits[qid]
            if hit:
                hits.append(qid)
                weighted_hits += weight
            if hit and not old:
                gains.append(qid)
                weighted_gain += weight
            elif old and not hit:
                losses.append(qid)
                weighted_loss += weight
            elif hit:
                shared_hits.append(qid)
            else:
                shared_misses.append(qid)
        result[name] = {"known_hits": hits, "gains": gains, "losses": losses,
                        "shared_hits": shared_hits, "shared_misses": shared_misses,
                        "net_known_query_change": len(gains) - len(losses),
                        "query_hit_fraction_bounds": [len(hits) / len(ids), (len(hits) + len(unknown)) / len(ids)],
                        "puzzle_mean_fraction_bounds": [weighted_hits, weighted_hits + weighted_unknown],
                        "puzzle_mean_gain": weighted_gain, "puzzle_mean_loss": weighted_loss}
    return {"schema": "matched-selector-diagnostic/1", "query_denominator": len(ids),
            "known_truth_queries": len(truth_ids), "unknown_truth_queries": unknown,
            "empty_pool_queries": [q["query_id"] for q in seal["selections"] if not q["candidate_count"]],
            "truth_coverage": "COMPLETE_KNOWN" if not unknown else "HOLD_UNKNOWN_TRUTHS",
            "selectors": result, "seal_sha256": digest(seal), "truth_mask_sha256": digest(truth_mask),
            "evidence_class": reg["evidence_class"], "official_score": None,
            "adoption": "HOLD_SEPARATE_NATIVE_AND_SCIENTIFIC_REVIEW"}


def repaired_legacy_g2(inventory, arms, truth_mask, *, mode="full_five", gate_sha256=LEGACY_GATE_SHA256):
    """Shadow repair candidate; never rewrites the frozen registration/receipts.

    Opaque legacy grid tokens are diagnostic only, not full grid-identity proof.
    Missing C/D is explicit; G2-only does not qualify full five-arm registration.
    Every known shared-control truth is checked, including A/A-flipped outputs.
    """
    require(gate_sha256 == LEGACY_GATE_SHA256, "FROZEN_REGISTRATION_PIN_MISMATCH")
    require(mode in ("full_five", "g2_only"), "GATE_MODE")
    require(type(inventory) is list and len(set(inventory)) == len(inventory) and inventory, "GATE_INVENTORY")
    required = {"A0", "A1", "B", "C", "D"} if mode == "full_five" else {"A0", "A1", "B"}
    missing = sorted(required - set(arms))
    if missing:
        return {"status": "HOLD_INCOMPLETE_REGISTERED_ARMS", "missing_arms": missing, "full_qualification": False}
    require(set(truth_mask) == set(inventory), "TRUTH_MASK_MISSING_OR_EXTRA_QUERY")
    for name in required:
        require(set(arms[name]) == set(inventory), "ARM_QUERY_COVERAGE")
        for item in arms[name].values():
            require(type(item.get("pair")) is list and len(item["pair"]) <= 2
                    and len(set(item["pair"])) == len(item["pair"]), "ARM_TOP2_INVALID")
            require(type(item.get("pool_distinct")) is int and item["pool_distinct"] >= len(item["pair"]),
                    "ARM_POOL_COUNT_INVALID")
    pool = [q for q in inventory if arms["A0"][q]["pool_distinct"] > 0]
    aa = [q for q in pool if arms["A0"][q]["pair"] != arms["A1"][q]["pair"]]
    ab = [q for q in pool if arms["A0"][q]["pair"] != arms["B"][q]["pair"]]
    gains, losses, unknown = [], [], []
    for q in inventory:
        truth = truth_mask[q]
        require(truth.get("state") in ("known", "unknown"), "TRUTH_STATE")
        if truth["state"] == "unknown":
            require(truth.get("reason"), "UNKNOWN_TRUTH_REASON")
            unknown.append(q)
            continue
        token = truth.get("token")
        require(type(token) is str and token, "KNOWN_TRUTH_TOKEN")
        a0, a1, b = (token in arms[a][q]["pair"] for a in ("A0", "A1", "B"))
        if a0 and a1 and not b:
            losses.append(q)
        if b and not a0:
            gains.append(q)
    identity = len(pool) == 12 and len(ab) <= len(aa)
    return {"status": "FAIL_DISCREPANCY" if len(pool) != 12 else "SHADOW_G2_DIAGNOSTIC",
            "frozen_expected_pool_count": 12, "actual_pool_count": len(pool),
            "aa_flips": aa, "b_flips": ab, "gains_vs_A0": gains, "shared_control_truth_losses": losses,
            "unknown_truth_queries": unknown, "registered_query_denominator": len(inventory),
            "G2_shadow_pass": identity and not losses and not unknown,
            "full_qualification": False, "old_registration_edited": False,
            "note": "G3-G10/native/independent-review absent; this shadow never qualifies adoption."}


def duplicate_guard(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "DUPLICATE_JSON_KEY")
        out[key] = value
    return out


def read_bound(path, expected):
    sha(expected)
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, "JSON_INPUT_BYTE_BOUND")
    require(hashlib.sha256(raw).hexdigest() == expected, "EXTERNAL_FILE_PIN_MISMATCH")
    return json.loads(raw, object_pairs_hook=duplicate_guard,
                      parse_constant=lambda value: (_ for _ in ()).throw(Hold("NONFINITE_JSON")))


def create_only(path, value):
    payload = canonical(value) + b"\n"
    require(len(payload) <= MAX_BYTES, "OUTPUT_BYTE_BOUND")
    with Path(path).open("xb") as handle:
        handle.write(payload)
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "evaluate"))
    for name in ("registration", "export"):
        parser.add_argument("--" + name, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    for name in ("seal", "truth-mask"):
        parser.add_argument("--" + name)
        parser.add_argument("--" + name + "-sha256")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        reg = read_bound(args.registration, args.registration_sha256)
        export = read_bound(args.export, args.export_sha256)
        prepared = prepare(reg, export)
        if args.phase == "prepare":
            require(not any((args.seal, args.seal_sha256, args.truth_mask, args.truth_mask_sha256)),
                    "TRUTH_OR_SEAL_ARGUMENT_NOT_ALLOWED_IN_PREPARE")
            result = prepared
        else:
            require(all((args.seal, args.seal_sha256, args.truth_mask, args.truth_mask_sha256)), "SEALED_EVALUATION_ARGUMENTS")
            sealed = read_bound(args.seal, args.seal_sha256)
            require(sealed == prepared, "SEALED_SELECTION_CHANGED")
            # Truth-mask bytes are first opened only after the sealed comparison.
            truth = read_bound(args.truth_mask, args.truth_mask_sha256)
            result = evaluate(reg, export, sealed, truth)
        written = create_only(args.out, result)
    except (Hold, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "HOLD", "reason": str(exc) if isinstance(exc, Hold) else "INPUT_OR_OUTPUT_CONTRACT_ERROR"}))
        return 2
    print(json.dumps({"status": "CREATED_NEW_DIAGNOSTIC", "sha256": written, "official_score": None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
