# SPDX-License-Identifier: MIT
"""Narrow original in-memory controls, no ARC data/model/native/tool API work."""
from __future__ import annotations

import copy
import hashlib
import json
import resource
import time
from pathlib import Path

import selector_audit as tool
import capture_loaded_pool as adapter


def expect(reason, action):
    try:
        action()
    except tool.Hold as exc:
        if str(exc) != reason:
            raise RuntimeError("WRONG_HOLD_REASON") from exc
        return True
    raise RuntimeError("EXPECTED_HOLD_NOT_RETURNED")


def registration(count=5):
    h = tool.digest("invented source bytes")
    return {"schema": "matched-selector-registration/1", "status": "REGISTERED",
            "evidence_class": "invented", "study_id": "invented-matched-pool-control",
            "registered_before_candidate_export": True, "coverage_policy": "all_queries_present_empty_explicit",
            "selectors": list(tool.SELECTORS),
            "identity": {"id": "invented/worker", "id_no": 1, "title": "Invented worker", "code_file": "invented.py"},
            "control": {"source_sha256": h, "decoder_sha256": h, "generator_sha256": h,
                        "challenge_sha256": h, "environment_sha256": h,
                        "source_role": "credited_control_recipe", "seed_policy": "invented fixed order",
                        "model_instance": "none-invented", "scientific_exposure": "invented"},
            "queries": [{"query_id": "invented_q%d" % i, "task_id": "invented_task", "query_index": i,
                         "input_sha256": tool.grid_id([[i]])} for i in range(count)]}


def occurrence(name, color, beam=2.95, aug=(1.0,)):
    return {"occurrence_id": name, "grid": [[color]], "beam_score": beam,
            "score_aug": list(aug), "view_ids": ["v%d" % i for i in range(len(aug))]}


def export(reg):
    records = [occurrence("a0", 1), occurrence("a1", 1), occurrence("a2", 1),
               occurrence("b0", 2), occurrence("b1", 2), occurrence("c0", 3, 0.0)]
    queries = []
    for i, descriptor in enumerate(reg["queries"]):
        pool = [] if i == 4 else copy.deepcopy(records)
        r = tool.rank_occurrences(pool)
        queries.append({"query_id": descriptor["query_id"], "descriptor": copy.deepcopy(descriptor),
                        "generation_state": "complete" if pool else "empty_complete", "occurrences": pool,
                        "native_rankings": r["native_order_expectations"],
                        "baseline_submitted_pair": r["pairs"]["kgmon2"]})
    return {"schema": "matched-candidate-export/2", "registration_sha256": tool.digest(reg),
            "identity": copy.deepcopy(reg["identity"]), "control": copy.deepcopy(reg["control"]), "queries": queries,
            "run_binding": {"native_id": "1", "kernel_version": 1, "notebook_source_sha256": reg["control"]["source_sha256"],
                            "generation_receipt_sha256": tool.digest("invented generation state receipt"),
                            "loaded_module_manifest_sha256": tool.digest("invented loaded module manifest")}}


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (10, 12))
    started = time.process_time()
    reg = registration()
    pools = export(reg)
    before = tool.digest(pools)
    seal = tool.prepare(reg, pools)
    mask = {"schema": "query-truth-mask/1", "registration_sha256": tool.digest(reg),
            "queries": {"invented_q%d" % i: {"state": "known", "grid": [[color]]}
                        for i, color in enumerate([1, 2, 3, 9, 0])}}
    diagnostic = tool.evaluate(reg, pools, seal, mask)
    controls = {}
    for name in ("probmul2", "anchored_distinct2"):
        d = diagnostic["selectors"][name]
        controls[name + "_one_gain_and_one_loss"] = d["gains"] == ["invented_q2"] and d["losses"] == ["invented_q1"] and d["net_known_query_change"] == 0
    controls["all_query_denominator_retained"] = diagnostic["query_denominator"] == 5 and diagnostic["empty_pool_queries"] == ["invented_q4"]
    controls["inputs_unchanged"] = before == tool.digest(pools)
    missing = copy.deepcopy(mask); del missing["queries"]["invented_q3"]
    controls["missing_truth_is_hold"] = expect("TRUTH_MASK_MISSING_OR_EXTRA_QUERY", lambda: tool.evaluate(reg, pools, seal, missing))
    unknown = copy.deepcopy(mask); unknown["queries"]["invented_q3"] = {"state": "unknown", "reason": "invented withheld truth"}
    d = tool.evaluate(reg, pools, seal, unknown)
    controls["unknown_truth_keeps_denominator_and_hold"] = d["truth_coverage"] == "HOLD_UNKNOWN_TRUTHS" and d["query_denominator"] == 5 and d["unknown_truth_queries"] == ["invented_q3"] and d["selectors"]["kgmon2"]["query_hit_fraction_bounds"] == [0.4, 0.6]
    changed = copy.deepcopy(pools); changed["queries"][0]["occurrences"][0]["grid"] = [[8]]
    controls["changed_native_pool_rejected"] = expect("NATIVE_SELECTOR_PARITY_MISMATCH", lambda: tool.prepare(reg, changed))
    reordered = copy.deepcopy(pools); reordered["queries"].reverse()
    controls["query_order_change_rejected"] = expect("EXACT_QUERY_ORDER_OR_COVERAGE", lambda: tool.prepare(reg, reordered))
    dropped = copy.deepcopy(pools); dropped["queries"].pop()
    controls["missing_pool_record_rejected"] = expect("EXACT_QUERY_ORDER_OR_COVERAGE", lambda: tool.prepare(reg, dropped))
    stale = copy.deepcopy(pools); stale["control"]["seed_policy"] = "second factor changed"
    controls["source_or_seed_drift_rejected"] = expect("IDENTITY_OR_CONTROL_DRIFT", lambda: tool.prepare(reg, stale))
    changed_seal = copy.deepcopy(seal); changed_seal["selections"][0]["pairs"]["kgmon2"].reverse()
    controls["seal_edit_rejected"] = expect("SEALED_SELECTION_CHANGED", lambda: tool.evaluate(reg, pools, changed_seal, mask))
    badscore = [occurrence("x", 0, float("nan"))]
    controls["nonfinite_score_rejected"] = expect("NONFINITE_OR_NONNUMERIC_SCORE", lambda: tool.rank_occurrences(badscore))
    controls["zero_is_valid_candidate_not_timeout"] = tool.grid_id([[0]]) in tool.rank_occurrences([occurrence("zero", 0)])["pairs"]["kgmon2"]
    duplicate = [occurrence("same", 1), occurrence("same", 1)]
    controls["duplicate_occurrence_identity_rejected"] = expect("OCCURRENCE_ID_DUPLICATE", lambda: tool.rank_occurrences(duplicate))
    variable = tool.rank_occurrences([occurrence("view0", 4, 1, (0, 0)), occurrence("view1", 4, 1, (4,))])
    score = variable["scores"][tool.grid_id([[4]])]
    controls["per_occurrence_mean_not_flattened"] = score["kgmon"] == 0.0 and score["probmul"] == 6.5
    tie = tool.rank_occurrences([occurrence("first", 8, 1, (1,)), occurrence("second", 7, 1, (1,))])
    controls["first_seen_tie_order_preserved"] = tie["pairs"]["kgmon2"] == [tool.grid_id([[8]]), tool.grid_id([[7]])]
    controls["full_ranking_compared_as_two_slot_prefix"] = len(seal["selections"][0]["native_order_expectations"]["kgmon"]) == 3 and len(seal["selections"][0]["pairs"]["kgmon2"]) == 2
    emptyaug = [occurrence("empty", 0, 1, ())]
    controls["missing_aug_views_rejected"] = expect("AUGMENTATION_VIEW_COUNT", lambda: tool.rank_occurrences(emptyaug))
    # Frozen old expected12 among13 remains literal. All12 controls flip while
    # retaining a shared truth; B loses it everywhere. The old skip is defeated.
    ids = ["invented_legacy_%d" % i for i in range(13)]
    arms = {a: {q: {"pair": (["shared_truth", a + "_second"] if i < 12 else []), "pool_distinct": (3 if i < 12 else 0)}
                for i, q in enumerate(ids)} for a in ("A0", "A1", "B", "C", "D")}
    for q in ids[:12]: arms["B"][q]["pair"] = ["other", "B_second"]
    truths = {q: {"state": "known", "token": "shared_truth"} for q in ids}
    g = tool.repaired_legacy_g2(ids, arms, truths)
    controls["truth_loss_checked_on_AA_flips"] = len(g["aa_flips"]) == 12 and g["shared_control_truth_losses"] == ids[:12] and g["G2_shadow_pass"] is False
    partial = tool.repaired_legacy_g2(ids, {k: arms[k] for k in ("A0", "A1", "B")}, truths)
    controls["missing_C_D_full_gate_hold"] = partial["status"] == "HOLD_INCOMPLETE_REGISTERED_ARMS" and partial["missing_arms"] == ["C", "D"]
    diagnostic_only = tool.repaired_legacy_g2(ids, {k: arms[k] for k in ("A0", "A1", "B")}, truths, mode="g2_only")
    controls["three_arm_diagnostic_not_full_qualification"] = diagnostic_only["full_qualification"] is False
    allpools = copy.deepcopy(arms)
    for name in allpools: allpools[name][ids[-1]] = {"pair": ["zero"], "pool_distinct": 1}
    discrepancy = tool.repaired_legacy_g2(ids, allpools, truths)
    controls["observed13_does_not_widen_frozen12"] = discrepancy["status"] == "FAIL_DISCREPANCY" and discrepancy["frozen_expected_pool_count"] == 12
    controls["legacy_missing_truth_is_hold"] = expect("TRUTH_MASK_MISSING_OR_EXTRA_QUERY", lambda: tool.repaired_legacy_g2(ids, arms, {q: truths[q] for q in ids[:-1]}))
    # JSON-safe fake already-loaded decoder tests adapter binding, not native parity.
    class Fake:
        dataset = None
        def __init__(self):
            self.decoded_results = {q["query_id"]: {v["occurrence_id"]: {"solution": v["grid"], "beam_score": v["beam_score"], "score_aug": v["score_aug"]} for v in q["occurrences"]} for q in pools["queries"]}
        def run_selection_algo(self, function):
            return function(self.decoded_results)
    def fake_rank(name):
        def rank(decoded):
            answer = {}
            for qid, samples in decoded.items():
                rows = [{"occurrence_id": k, "grid": v["solution"], "beam_score": v["beam_score"], "score_aug": v["score_aug"], "view_ids": ["recorded_position_%d" % i for i in range(len(v["score_aug"]))]} for k, v in samples.items()]
                byid = {tool.grid_id(v["grid"]): v["grid"] for v in rows}
                answer[qid] = [byid[c] for c in tool.rank_occurrences(rows)["native_order_expectations"][name]]
            return answer
        return rank
    states = {q["query_id"]: q["generation_state"] for q in pools["queries"]}
    captured, capture_seal = adapter.capture(Fake(), reg, fake_rank("kgmon"), fake_rank("probmul"), generation_states=states, run_binding=pools["run_binding"])
    controls["missing_generation_state_rejected"] = expect("GENERATION_STATE_COVERAGE", lambda: adapter.capture(Fake(), reg, fake_rank("kgmon"), fake_rank("probmul"), generation_states={}, run_binding=pools["run_binding"]))
    unfinished = dict(states, invented_q4="not_admitted")
    controls["absent_pool_is_not_automatically_complete"] = expect("INCOMPLETE_GENERATION", lambda: adapter.capture(Fake(), reg, fake_rank("kgmon"), fake_rank("probmul"), generation_states=unfinished, run_binding=pools["run_binding"]))
    controls["numeric_overflow_is_hold"] = expect("NONFINITE_OR_NONNUMERIC_SCORE", lambda: tool.finite(10**400))
    controls["loaded_invented_pool_adapter_complete_and_unmutated"] = len(captured["queries"]) == 5 and captured["queries"][-1]["generation_state"] == "empty_complete" and capture_seal["truth_access"] == "NONE_IN_PREPARE"
    all_passed = all(controls.values())
    result = {"status": "PASS_INVENTED_CONTROLS" if all_passed else "FAIL_INVENTED_CONTROLS",
              "controls": controls, "checks": len(controls), "cpu_seconds": time.process_time() - started,
              "toy_diagnostic": diagnostic, "legacy_shared_truth_loss_witness": g,
              "native_parity": "NOT_TESTED; fake ranker is deliberately generated by same arithmetic",
              "actual_baseline_export": "ABSENT_HOLD", "model_or_competition_data_execution": False,
              "native_jobs": 0, "official_score": None,
              "sources": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                          for name in ("selector_audit.py", "capture_loaded_pool.py", "invented_controls.py")}}
    with (Path(__file__).parent / "INVENTED_RESULT.json").open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True); handle.write("\n")
    print(json.dumps({"status": result["status"], "checks": len(controls), "cpu_seconds": result["cpu_seconds"]}))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
