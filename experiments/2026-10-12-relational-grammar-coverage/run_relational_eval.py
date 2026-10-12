"""Exposed ARC2 evaluation: frozen grid search plus original relational families.

Prediction and evaluation are separate invocations. Prediction never accepts a
solution path. All output files are exclusive; failures and partial files stay
preserved. Original solver bodies and license files remain unchanged.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import math
import pathlib
import platform
import resource
import signal
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
EXPERIMENT = "arc2-original-relational-families-evaluation120-20261012-v1"
EXPECTED_TASKS = 120
EXPECTED_QUERIES = 172


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def need(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def read_json(path):
    raw = pathlib.Path(path).read_bytes()
    return raw, json.loads(raw)


def exclusive_json(path, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    with pathlib.Path(path).open("xb") as stream:
        stream.write(raw)
    return digest(raw)


def wall_expired(signum, frame):
    raise TimeoutError("registered 420-second whole-process wall limit")


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (400, 410))
    signal.signal(signal.SIGALRM, wall_expired)
    signal.setitimer(signal.ITIMER_REAL, 420.0)


def protocol(path):
    raw, value = read_json(path)
    need(value["experiment_id"] == EXPERIMENT, "wrong experiment")
    need(value["tasks"] == EXPECTED_TASKS and value["queries"] == EXPECTED_QUERIES, "wrong complete panel")
    need(value["baseline"] == {"seconds": 1.8, "max_depth": 3, "beam": 96, "state_cap": 10000}, "baseline delta")
    need(value["structural"] == {"interval_seconds": 0.8, "group_seconds": 0.4, "candidate_cap": 16}, "structural delta")
    need(value["limits"] == {"process_cpu_soft_seconds": 400, "process_cpu_hard_seconds": 410,
                             "whole_process_wall_seconds": 420, "native_server_seconds": 480,
                             "gpu_seconds": 0, "tpu_seconds": 0}, "budget delta")
    for name, pin in value["source_files"].items():
        need(pathlib.PurePath(name).name == name, "source name must be a basename")
        body = (HERE / name).read_bytes()
        need(digest(body) == pin["sha256"] and len(body) == pin["bytes"], "source pin drift: " + name)
    need(set(value["source_files"]) == {"run_relational_eval.py", "baseline37.py", "object_selector.py",
                                      "relational_families.py", "controls.py", "LICENSE", "BASELINE_LICENSE"}, "incomplete source pins")
    return raw, value


def load_solvers():
    # Imports only the already byte-verified exact original module files.
    modules = {}
    for name in ("baseline37", "object_selector", "relational_families", "controls"):
        spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        modules[name] = module
    return modules["baseline37"], modules["relational_families"], modules["controls"]


def output_directory(path):
    out = pathlib.Path(path).resolve()
    out.mkdir(parents=True, exist_ok=False)
    return out


def validate_grid(grid):
    need(isinstance(grid, list) and 1 <= len(grid) <= 30, "invalid grid height")
    width = len(grid[0]) if isinstance(grid[0], list) else 0
    need(1 <= width <= 30, "invalid grid width")
    need(all(isinstance(row, list) and len(row) == width
             and all(type(color) is int and 0 <= color <= 9 for color in row)
             for row in grid), "invalid grid values")


def validate_joint_candidates(candidates, query_count):
    need(isinstance(candidates, list) and len(candidates) <= 2, "invalid two-attempt candidates")
    for candidate in candidates:
        need(isinstance(candidate, dict) and isinstance(candidate.get("grids"), list)
             and len(candidate["grids"]) == query_count, "incomplete joint prediction")
        for grid in candidate["grids"]:
            validate_grid(grid)



def input_only_coverage(records):
    result = collections.Counter()
    for record in records:
        for name, arm in record["structural"]["families"].items():
            result[name + "_demo_fit_tasks"] += arm["counts"].get("demo_fitting_programs", 0) > 0
            result[name + "_candidate_tasks"] += bool(arm["candidates"])
            result[name + "_demo_fitting_programs"] += arm["counts"].get("demo_fitting_programs", 0)
            result[name + "_query_inapplicable_programs"] += arm["counts"].get("query_inapplicable_programs", 0)
            result[name + "_prediction_storage_truncated_tasks"] += arm.get("candidate_storage_truncated", False)
        result["any_family_demo_fit_tasks"] += any(arm["counts"].get("demo_fitting_programs", 0) > 0
                                                     for arm in record["structural"]["families"].values())
    return dict(result)


def predict(args):
    started, cpu_started = time.monotonic(), time.process_time()
    limits()
    protocol_raw, registered = protocol(args.protocol)
    challenge_raw, tasks = read_json(args.challenges)
    need(digest(challenge_raw) == registered["challenge"]["sha256"]
         and len(challenge_raw) == registered["challenge"]["bytes"], "challenge drift")
    need(isinstance(tasks, dict) and len(tasks) == EXPECTED_TASKS, "missing full challenge panel")
    ordered = sorted(tasks)
    inventory_raw = json.dumps(ordered, separators=(",", ":")).encode()
    need(digest(inventory_raw) == registered["challenge"]["sorted_task_inventory_sha256"], "inventory drift")
    need(sum(len(task["test"]) for task in tasks.values()) == EXPECTED_QUERIES, "query inventory drift")
    for task in tasks.values():
        need(set(task) == {"train", "test"} and task["train"] and task["test"], "malformed challenge")
        need(all(set(query) == {"input"} for query in task["test"]), "query truth forbidden")
        need(all(set(demo) == {"input", "output"} for demo in task["train"]), "demonstration fields drift")
        for demo in task["train"]:
            validate_grid(demo["input"])
            validate_grid(demo["output"])
        for query in task["test"]:
            validate_grid(query["input"])
    baseline, structural, controls = load_solvers()
    control_receipt = controls.run(structural)
    environment = {"python": sys.version, "platform": platform.platform(), "numpy": baseline.np.__version__}
    out = output_directory(args.out)
    names = ("PRIVATE_PREDICTIONS.json", "PRIVATE_PREDICTION_SEAL.json", "PRIVATE_FAILURE.json",
             "PUBLIC_INPUT_ONLY_COVERAGE.json", "PRIVATE_PREDICTION_COMPLETE.json")
    allowed = {str(out / name) for name in names}
    denied = []

    def audit(event, event_args):
        if event == "open":
            path = event_args[0]
            if isinstance(path, (str, bytes)):
                if str(pathlib.Path(path).resolve()) not in allowed:
                    denied.append({"event": event, "path": str(path)})
                    raise PermissionError("prediction filesystem access outside exclusive outputs")
            else:
                denied.append({"event": event, "path_kind": type(path).__name__})
                raise PermissionError("prediction file-descriptor access forbidden")
        if event.startswith(("socket.", "subprocess.", "os.system")):
            denied.append({"event": event})
            raise PermissionError("prediction network and child processes forbidden")

    sys.addaudithook(audit)
    records = []
    try:
        for position, task_id in enumerate(ordered):
            need(time.monotonic() - started < 420.0, "whole-process wall deadline")
            # No task ID, query truth, source path or metadata enters either solver.
            task = {"train": tasks[task_id]["train"], "test": tasks[task_id]["test"]}
            base = baseline.solve(task, **registered["baseline"])
            raw_extra = structural.solve(task, **registered["structural"])
            family_counts = collections.Counter()
            for arm in raw_extra["families"].values():
                family_counts.update(arm["counts"])
            extra = {**raw_extra, "counts": dict(family_counts),
                     "seconds_cpu": sum(a["seconds_cpu"] for a in raw_extra["families"].values()),
                     "stop_reason": "complete"}
            need(all(arm["stop_reason"] in ("complete", "no_demo_change") for arm in raw_extra["families"].values()),
                 "structural search incomplete")
            need(len(extra["candidates"]) <= 32, "structural candidate bound")
            for candidate in extra["candidates"]:
                validate_joint_candidates([candidate], len(task["test"]))
            treatment = sys.modules["object_selector"].fill_only(base["expanded"], extra["candidates"])
            query_count = len(task["test"])
            validate_joint_candidates(base["expanded"], query_count)
            validate_joint_candidates(treatment, query_count)
            key = lambda candidate: baseline.signature(tuple(baseline.grid(g) for g in candidate["grids"]))
            original_keys = {key(candidate) for candidate in base["expanded"]}
            treatment_keys = {key(candidate) for candidate in treatment}
            need(original_keys <= treatment_keys, "protected original guess changed")
            records.append({"task_id": task_id, "queries": query_count,
                            "baseline": base["expanded"], "treatment": treatment, "structural": extra,
                            "baseline_seconds": base["seconds"], "baseline_stop": base["stop_reason"],
                            "baseline_guesses_preserved": True,
                            "added_joint_guesses": len(treatment_keys - original_keys)})
            if position % 20 == 19:
                print("PREDICTED", position + 1, flush=True)
        need(len(records) == EXPECTED_TASKS, "partial prediction panel")
        prediction_sha = exclusive_json(out / "PRIVATE_PREDICTIONS.json", records)
        elapsed_wall, elapsed_cpu = time.monotonic() - started, time.process_time() - cpu_started
        total_process_cpu = time.process_time()
        need(elapsed_wall < 420.0 and elapsed_cpu < 400.0 and total_process_cpu < 400.0,
             "completion exceeds registered prediction budget")
        seal_sha = exclusive_json(out / "PRIVATE_PREDICTION_SEAL.json",
                       {"experiment_id": EXPERIMENT, "complete_tasks": len(records),
                        "queries": sum(record["queries"] for record in records),
                        "prediction_sha256": prediction_sha, "protocol_sha256": digest(protocol_raw),
                        "challenge_sha256": digest(challenge_raw),
                        "sorted_task_inventory_sha256": digest(inventory_raw),
                        "query_answers_read": False, "task_ids_passed_to_solvers": False,
                        "audit_denied_events": denied, "environment": environment,
                        "elapsed_wall_seconds": elapsed_wall, "elapsed_cpu_seconds": elapsed_cpu,
                        "total_process_cpu_seconds": total_process_cpu,
                        "budget_timing_scope": "whole prediction process from predict entry through prediction write; wall timer remains active through seal write",
                        "official_score": None, "neural_complementarity_measured": False,
                        "synthetic_controls_pass": control_receipt["status"] == "INVENTED_CONTROLS_PASS"})
        coverage = input_only_coverage(records)
        coverage_sha = exclusive_json(out / "PUBLIC_INPUT_ONLY_COVERAGE.json", {
            "experiment_id": EXPERIMENT, "status": "COMPLETE_SEALED_INPUT_ONLY_COVERAGE",
            "tasks": EXPECTED_TASKS, "queries": EXPECTED_QUERIES, "counts": coverage,
            "prediction_sha256": prediction_sha, "protocol_sha256": digest(protocol_raw),
            "challenge_sha256": digest(challenge_raw), "query_answers_read": False,
            "official_score": None, "quality_claim": False,
            "claim_limit": "Public demonstration coverage and query-input applicability only; predictions sealed, no query answers opened"})
        final_wall, final_cpu, final_process_cpu = time.monotonic() - started, time.process_time() - cpu_started, time.process_time()
        need(final_wall < 420.0 and final_cpu < 400.0 and final_process_cpu < 400.0,
             "final prediction artifacts exceed registered budget")
        exclusive_json(out / "PRIVATE_PREDICTION_COMPLETE.json", {
            "status": "COMPLETE_ALL_PREDICTION_ARTIFACTS", "experiment_id": EXPERIMENT,
            "tasks": EXPECTED_TASKS, "queries": EXPECTED_QUERIES,
            "prediction_sha256": prediction_sha, "seal_sha256": seal_sha,
            "coverage_sha256": coverage_sha, "protocol_sha256": digest(protocol_raw),
            "elapsed_wall_seconds": final_wall, "elapsed_cpu_seconds": final_cpu,
            "total_process_cpu_seconds": final_process_cpu, "query_answers_read": False})
        print("SEALED", EXPECTED_TASKS, prediction_sha, flush=True)
    except BaseException as error:
        try:
            exclusive_json(out / "PRIVATE_FAILURE.json",
                           {"experiment_id": EXPERIMENT, "status": "FAIL_PREDICTION_NO_QUALIFIED_RESULT",
                            "error_type": type(error).__name__, "error": str(error),
                            "completed_tasks": len(records), "audit_denied_events": denied,
                            "official_score": None})
        except BaseException:
            pass
        raise


def evaluate(args):
    started, cpu_started = time.monotonic(), time.process_time()
    limits()
    protocol_raw, registered = protocol(args.protocol)
    out = pathlib.Path(args.out).resolve()
    need(not (out / "PRIVATE_FAILURE.json").exists(), "failed prediction cannot qualify")
    _, completion = read_json(out / "PRIVATE_PREDICTION_COMPLETE.json")
    need(completion["status"] == "COMPLETE_ALL_PREDICTION_ARTIFACTS"
         and completion["experiment_id"] == EXPERIMENT and completion["tasks"] == EXPECTED_TASKS
         and completion["queries"] == EXPECTED_QUERIES and completion["query_answers_read"] is False,
         "prediction completion marker missing or invalid")
    seal_raw, seal = read_json(out / "PRIVATE_PREDICTION_SEAL.json")
    need(seal["experiment_id"] == EXPERIMENT and seal["complete_tasks"] == EXPECTED_TASKS
         and seal["queries"] == EXPECTED_QUERIES and not seal["query_answers_read"]
         and not seal["task_ids_passed_to_solvers"] and not seal["audit_denied_events"]
         and seal.get("synthetic_controls_pass") is True, "unqualified prediction seal")
    for key, cap in (("elapsed_wall_seconds", 420.0), ("elapsed_cpu_seconds", 400.0),
                     ("total_process_cpu_seconds", 400.0)):
        value = seal.get(key)
        need(type(value) in (int, float) and math.isfinite(value) and 0.0 <= value < cap,
             "prediction timing gate failed: " + key)
        final_value = completion.get(key)
        need(type(final_value) in (int, float) and math.isfinite(final_value) and 0.0 <= final_value < cap,
             "final prediction timing gate failed: " + key)
    coverage_raw, coverage = read_json(out / "PUBLIC_INPUT_ONLY_COVERAGE.json")
    need(completion["seal_sha256"] == digest(seal_raw)
         and completion["coverage_sha256"] == digest(coverage_raw)
         and completion["prediction_sha256"] == seal["prediction_sha256"]
         and completion["protocol_sha256"] == digest(protocol_raw)
         and coverage["status"] == "COMPLETE_SEALED_INPUT_ONLY_COVERAGE"
         and coverage["tasks"] == EXPECTED_TASKS and coverage["queries"] == EXPECTED_QUERIES
         and coverage["query_answers_read"] is False, "prediction completion artifact binding failed")
    need(seal["protocol_sha256"] == digest(protocol_raw)
         and seal["challenge_sha256"] == registered["challenge"]["sha256"]
         and seal["sorted_task_inventory_sha256"] == registered["challenge"]["sorted_task_inventory_sha256"], "seal/protocol mismatch")
    prediction_raw, records = read_json(out / "PRIVATE_PREDICTIONS.json")
    need(digest(prediction_raw) == seal["prediction_sha256"] and len(records) == EXPECTED_TASKS, "prediction seal mismatch")
    ids = [record["task_id"] for record in records]
    need(ids == sorted(ids) and len(set(ids)) == EXPECTED_TASKS, "duplicate or reordered panel")
    need(digest(json.dumps(ids, separators=(",", ":")).encode()) ==
         registered["challenge"]["sorted_task_inventory_sha256"], "prediction inventory mismatch")
    need(sum(record["queries"] for record in records) == EXPECTED_QUERIES, "incomplete prediction queries")
    for record in records:
        need(record["baseline_guesses_preserved"], "preservation assertion missing")
        validate_joint_candidates(record["baseline"], record["queries"])
        validate_joint_candidates(record["treatment"], record["queries"])
        original = {json.dumps(candidate["grids"], separators=(",", ":")) for candidate in record["baseline"]}
        treatment = {json.dumps(candidate["grids"], separators=(",", ":")) for candidate in record["treatment"]}
        need(original <= treatment, "evaluator protected guess check failed")

    # First solution file access in this process occurs after all complete prediction gates above.
    solution_raw, solutions = read_json(args.solutions)
    need(digest(solution_raw) == registered["solution"]["sha256"]
         and len(solution_raw) == registered["solution"]["bytes"], "solution bytes drift")
    need(set(solutions) == set(ids), "solution panel mismatch")
    counts = collections.Counter()
    rows = []
    for record in records:
        truth = solutions[record["task_id"]]
        need(len(truth) == record["queries"], "truth query count drift")
        for answer in truth:
            validate_grid(answer)
        hits = {arm: any(candidate["grids"] == truth for candidate in record[arm])
                for arm in ("baseline", "treatment")}
        for arm in hits:
            counts[arm + "_task_solves"] += int(hits[arm])
        query_hits = {arm: [any(candidate["grids"][index] == answer for candidate in record[arm])
                            for index, answer in enumerate(truth)] for arm in ("baseline", "treatment")}
        for arm in query_hits:
            counts[arm + "_query_solves"] += sum(query_hits[arm])
        counts["paired_query_wins"] += sum(treatment and not baseline
                                            for baseline, treatment in zip(query_hits["baseline"], query_hits["treatment"]))
        counts["paired_query_losses"] += sum(baseline and not treatment
                                              for baseline, treatment in zip(query_hits["baseline"], query_hits["treatment"]))
        counts["paired_task_wins"] += int(hits["treatment"] and not hits["baseline"])
        counts["paired_task_losses"] += int(hits["baseline"] and not hits["treatment"])
        counts["natural_structural_activation_tasks"] += bool(record["structural"]["candidates"])
        counts["added_joint_guesses"] += record["added_joint_guesses"]
        counts["new_guess_tasks"] += int(record["added_joint_guesses"] > 0)
        counts["structural_prediction_storage_truncated_tasks"] += any(
            arm.get("candidate_storage_truncated", False) for arm in record["structural"]["families"].values())
        counts["structural_search_incomplete_tasks"] += any(
            arm["stop_reason"] not in ("complete", "no_demo_change") for arm in record["structural"]["families"].values())
        counts["baseline_time_cap_tasks"] += int(record["baseline_stop"] == "time_cap")
        counts["queries"] += record["queries"]
        rows.append({"task_id": record["task_id"], "queries": record["queries"], "hits": hits,
                     "query_hits": query_hits,
                     "added_joint_guesses": record["added_joint_guesses"]})
    result = {"experiment_id": EXPERIMENT, "status": "COMPLETE_EXPOSED_DEVELOPMENT_COMPARISON",
              "complete_tasks": EXPECTED_TASKS, "counts": dict(counts), "input_only_coverage": input_only_coverage(records),
              "prediction_sha256": seal["prediction_sha256"], "prediction_seal_sha256": digest(seal_raw),
              "protocol_sha256": digest(protocol_raw), "challenge_sha256": registered["challenge"]["sha256"],
              "solution_sha256": digest(solution_raw), "source_files": registered["source_files"],
              "environment": seal["environment"], "prediction_elapsed_wall_seconds": seal["elapsed_wall_seconds"],
              "prediction_elapsed_cpu_seconds": seal["elapsed_cpu_seconds"],
              "prediction_total_process_cpu_seconds": seal["total_process_cpu_seconds"],
              "evaluation_elapsed_wall_seconds": time.monotonic() - started,
              "evaluation_elapsed_cpu_seconds": time.process_time() - cpu_started,
              "structural_cpu_seconds": sum(record["structural"]["seconds_cpu"] for record in records),
              "baseline_wall_seconds": sum(record["baseline_seconds"] for record in records),
              "primary_endpoint": "per-query exact-at-two with independently matched attempt for each query",
              "secondary_task_endpoint": "all queries of a task equal one of the two joint guesses; stricter than contest per-query metric",
              "positive_local_signal": counts["paired_query_wins"] > 0 and counts["paired_query_losses"] == 0,
              "official_score": None, "neural_complementarity_measured": False,
              "claim_limit": "All120 official exposed evaluation tasks/172queries; new structural-family comparison, historical exposure unknown; no hidden, neural-control or official-score claim",
              "query_answers_first_opened_after_complete_prediction_seal": True}
    exclusive_json(out / "PRIVATE_ACTUAL_RESULT.json", {**result, "per_task": rows})
    exclusive_json(out / "PUBLIC_AGGREGATE_RESULT.json", result)
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("predict", "evaluate"):
        command = sub.add_parser(name)
        command.add_argument("--protocol", required=True)
        command.add_argument("--out", required=True)
        if name == "predict":
            command.add_argument("--challenges", required=True)
        else:
            command.add_argument("--solutions", required=True)
    args = parser.parse_args()
    (predict if args.mode == "predict" else evaluate)(args)


if __name__ == "__main__":
    main()

