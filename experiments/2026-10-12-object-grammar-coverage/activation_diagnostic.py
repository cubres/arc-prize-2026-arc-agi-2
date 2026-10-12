"""Original input-only ARC2 object-program predicate audit.

This is a diagnostic, not a solver change or score experiment. The only real
task data accepted are public demonstration input/output and query INPUT from
one byte-pinned challenge file. Separate query solutions are never accepted.
This portable public variant was source-only when prepared; the published
measurements came from the separately reviewed frozen diagnostic. Reproduction
reads a caller-supplied challenge file and writes only aggregate counters to a
new exclusive output directory. It never opens query solutions or a prediction
trace. This command is intended for POSIX Python with NumPy.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import pathlib
import resource
import signal
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
PINS = {
    "baseline37.py": "52141a1eb17b5d33b2c528f8571b16eef9f4e784f7a8873d3f62f59f31d1c2cf",
    "object_selector.py": "9926c66261bd1b97a206ae5808f6208e717fe7544b0cc57c75589d0d39f0d391",
}
REFERENCE_CHALLENGE_PIN = "e7c62a4bd211867c6b538f66b8013b81f299663c82ca062f49a52bf439d6e4e8"
REFERENCE_INVENTORY_PIN = "de177061609276f360f78795a498f7105922bd672581eb629d64ddbe19cf020f"
EXPERIMENT = "arc2-object-predicate-diagnostic-portable-v1"
TASK_CPU_CAP = 1.5
TOTAL_CPU_CAP = 210
WALL_CAP = 240


def need(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned_json(path, pin):
    raw = path.read_bytes()
    need(sha(raw) == pin, "input byte pin drift: " + path.name)
    return json.loads(raw)


def modules():
    # All imports happen before the no-read/no-network runtime audit.
    loaded = {}
    for name in ("baseline37", "object_selector"):
        path = HERE / (name + ".py")
        need(sha(path.read_bytes()) == PINS[path.name], "frozen source drift")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    return loaded["baseline37"], loaded["object_selector"]


def valid_task(task, base):
    need(isinstance(task, dict) and set(task) == {"train", "test"}
         and task["train"] and task["test"], "invalid task contract")
    for demo in task["train"]:
        need(set(demo) == {"input", "output"}, "invalid public demonstration")
        base.grid(demo["input"])
        base.grid(demo["output"])
    for query in task["test"]:
        need(set(query) == {"input"}, "query outputs/identities forbidden")
        base.grid(query["input"])


def selection_reason(parts, rule, obj):
    if not parts:
        return None, "empty_inventory"
    if len(parts) > 80:
        return None, "inventory_over80"
    try:
        return obj.select(parts, rule), None
    except ValueError:
        return None, "ambiguous_selector"


def task_audit(task, base, obj, cpu_cap=TASK_CPU_CAP):
    """Trace frozen grammar, plus demo-only counterfactual gate diagnostics.

    Counterfactuals NEVER create accepted predictions: they only show whether
    query selection prevented a public demonstration fit from being examined.
    Program identities/task IDs do not enter selection, rendering, or fitting.
    """
    started = time.process_time()
    demos = task["train"]
    count = len(demos)
    arrays = [base.grid(p["input"]) for p in demos + task["test"]]
    targets = [base.grid(p["output"]) for p in demos]
    backgrounds = [obj.backgrounds(a) for a in arrays]
    legacy = collections.Counter()
    gates = collections.Counter()
    reasons = collections.Counter()
    seen_full = set()
    seen_demo = set()
    fit_cache = {}
    accepted = set()
    exact_demo_families = set()
    query_blocked_demo_families = set()
    # Metadata only: no real grids, mapped grids, inferred color tables, or
    # task-specific programs are written by this diagnostic.
    inventory_ranges = []

    def budget():
        need(time.process_time() - started < cpu_cap, "per-task diagnostic CPU cap")

    for bg_kind in range(3):
        for diagonal in (False, True):
            for monochrome in (False, True):
                budget()
                gates["decompositions"] += 1
                parts = [obj.objects(a, bg[bg_kind], diagonal, monochrome)
                         for a, bg in zip(arrays, backgrounds)]
                inventory_ranges.append({
                    "background_kind": bg_kind, "diagonal": diagonal,
                    "monochrome": monochrome,
                    "demo_counts": [len(p) for p in parts[:count]],
                    "query_counts": [len(p) for p in parts[count:]],
                })
                if not any(len(p) >= 2 for p in parts[:count]):
                    legacy["no_multi_object_demo"] += 1
                    gates["decomposition_no_multiobject_demo"] += 1
                    continue
                gates["decomposition_multiobject_pass"] += 1
                for selector in obj.SELECTORS:
                    budget()
                    gates["selector_attempts"] += 1
                    choices = [selection_reason(p, selector, obj) for p in parts]
                    demo_errors = [error for _, error in choices[:count] if error]
                    query_errors = [error for _, error in choices[count:] if error]
                    for error in demo_errors:
                        reasons["demo_" + error] += 1
                    for error in query_errors:
                        reasons["query_" + error] += 1
                    if demo_errors or query_errors:
                        legacy["ambiguous_or_inapplicable"] += 1
                    if demo_errors:
                        gates["selector_demo_fail"] += 1
                        continue
                    gates["selector_demo_pass"] += 1
                    if query_errors:
                        gates["selector_query_fail_after_demo_pass"] += 1
                    else:
                        gates["selector_all_inputs_pass"] += 1
                    selected = [choice for choice, _ in choices]
                    for mode in ("crop", "isolate_crop", "retain", "erase"):
                        # Demo rendering is also examined when query selection
                        # fails, to locate the original pre-fit query gate.
                        rendered_demo = [obj.render(a, p, bg[bg_kind], mode)
                                         for a, p, bg in zip(arrays[:count], selected[:count], backgrounds[:count])]
                        rendered_query = None if query_errors else [
                            obj.render(a, p, bg[bg_kind], mode)
                            for a, p, bg in zip(arrays[count:], selected[count:], backgrounds[count:])]
                        for transform in range(8):
                            budget()
                            values_demo = tuple(obj.geometry(a, transform) for a in rendered_demo)
                            demo_state = base.signature(values_demo)
                            demo_new = demo_state not in seen_demo
                            seen_demo.add(demo_state)
                            if demo_new:
                                gates["unique_demo_outputs"] += 1
                            # Count all fitting grammar families before the
                            # original full-state dedup, using a demo-state
                            # cache. Legacy counters still apply that dedup.
                            if demo_state not in fit_cache:
                                shapes_match = all(a.shape == b.shape for a, b in zip(values_demo, targets))
                                if shapes_match:
                                    _, exact, table, supported = base.recoloring(values_demo, targets)
                                else:
                                    exact, table, supported = False, None, None
                                fit_cache[demo_state] = (shapes_match, exact, table, supported)
                            shapes_match, exact, table, supported = fit_cache[demo_state]
                            family = (bg_kind, diagonal, monochrome, selector[0], selector[1], mode, transform)
                            if exact:
                                exact_demo_families.add(family)
                            full_state = None
                            values_query = None
                            if rendered_query is not None:
                                values_query = tuple(obj.geometry(a, transform) for a in rendered_query)
                                full_state = base.signature(values_demo + values_query)
                                if full_state in seen_full:
                                    gates["full_output_dedup"] += 1
                                    continue
                                seen_full.add(full_state)
                                legacy["unique_program_outputs"] += 1
                            if not shapes_match:
                                if demo_new:
                                    gates["demo_unique_shape_reject"] += 1
                                if full_state is not None:
                                    gates["full_unique_shape_reject"] += 1
                                continue
                            if not exact:
                                if demo_new:
                                    gates["demo_unique_recolor_conflict"] += 1
                                if full_state is not None:
                                    gates["full_unique_recolor_conflict"] += 1
                                continue
                            if demo_new:
                                gates["demo_unique_exact_fit"] += 1
                            if query_errors:
                                query_blocked_demo_families.add(family)
                                gates["demo_fit_program_query_blocked"] += 1
                                continue
                            legacy["exact_demonstration_fits"] += 1
                            gates["full_unique_exact_fit"] += 1
                            if not base.query_colors_supported(table, supported, values_query):
                                legacy["unsupported_query_color"] += 1
                                continue
                            predicted_signature = base.signature(tuple(table[a] for a in values_query))
                            accepted.add(predicted_signature)
                            if len(accepted) >= 32:
                                return {"complete": False, "stop": "frozen_candidate_cap",
                                        "legacy_counts": dict(legacy), "gates": dict(gates),
                                        "reason_counts": dict(reasons), "accepted_candidates": len(accepted)}
    budget()
    need(gates["full_unique_shape_reject"] + gates["full_unique_recolor_conflict"]
         + gates["full_unique_exact_fit"] == legacy["unique_program_outputs"],
         "full-state partition accounting failed")
    need(gates["demo_unique_shape_reject"] + gates["demo_unique_recolor_conflict"]
         + gates["demo_unique_exact_fit"] == gates["unique_demo_outputs"],
         "demo-state partition accounting failed")
    return {"complete": True, "stop": "complete", "legacy_counts": dict(legacy),
            "gates": dict(gates), "reason_counts": dict(reasons),
            "accepted_candidates": len(accepted), "seconds_cpu": time.process_time() - started,
            "exact_demo_program_families": len(exact_demo_families),
            "query_blocked_exact_demo_families": len(query_blocked_demo_families),
            "inventory_ranges": inventory_ranges}


def controls(base, obj):
    """Invented tiny grids; assert implementation behavior, never task accuracy."""
    demo_a = [[0, 1, 1, 0, 2], [0, 1, 1, 0, 0], [0, 0, 0, 0, 0]]
    demo_b = [[0, 0, 3, 0, 0], [0, 2, 2, 0, 0], [0, 2, 2, 0, 0]]
    positive = {"train": [{"input": demo_a, "output": [[1, 1], [1, 1]]},
                          {"input": demo_b, "output": [[2, 2], [2, 2]]}],
                "test": [{"input": [[0, 4, 4, 0, 5], [0, 4, 4, 0, 0], [0, 0, 0, 0, 0]]}]}
    conflict = {"train": [{"input": demo_a, "output": [[1, 1], [1, 1]]},
                          {"input": demo_a, "output": [[2, 2], [2, 2]]}],
                "test": positive["test"]}
    no_query_object = {"train": positive["train"], "test": [{"input": [[0] * 5 for _ in range(3)]}]}
    tied_query = [[0] * 7 for _ in range(7)]
    for top in (1, 4):
        for left in (1, 4):
            for r in range(top, top + 2):
                for c in range(left, left + 2):
                    tied_query[r][c] = 4
    query_ties = {"train": positive["train"], "test": [{"input": tied_query}]}
    recolor_train = [{"input": demo_a, "output": [[5, 5], [5, 5]]},
                     {"input": demo_b, "output": [[5, 5], [5, 5]]}]
    recolor_supported = {"train": recolor_train,
                         "test": [{"input": [[0, 1, 1, 0, 3], [0, 1, 1, 0, 0], [0, 0, 0, 0, 0]]}]}
    recolor_unsupported = {"train": recolor_train, "test": positive["test"]}
    one_object = {"train": [{"input": [[0, 0, 0], [0, 1, 0], [0, 0, 0]], "output": [[1]]}],
                  "test": [{"input": [[0, 0, 0], [0, 2, 0], [0, 0, 0]]}]}
    result = {}
    for name, task in (("positive_crop", positive), ("negative_conflicting_demos", conflict),
                       ("negative_empty_query_inventory", no_query_object),
                       ("negative_tied_query_inventory", query_ties),
                       ("positive_supported_nonidentity_recolor", recolor_supported),
                       ("negative_unsupported_query_color", recolor_unsupported),
                       ("negative_single_demo_object_gate", one_object)):
        valid_task(task, base)
        audited = task_audit(task, base, obj, cpu_cap=4.0)
        original = obj.solve(task, seconds=2.0, candidate_cap=32)
        need(audited["complete"] and original["stop_reason"] == "complete", "synthetic control capped")
        need(audited["legacy_counts"] == original["counts"], "synthetic legacy counter parity failed: " + name)
        need(audited["accepted_candidates"] == len(original["candidates"]), "synthetic candidate parity failed")
        if name == "positive_crop":
            need(any(c["grids"] == [[[4, 4], [4, 4]]] for c in original["candidates"]), "synthetic activation failed")
        elif name == "positive_supported_nonidentity_recolor":
            need(any(c["grids"] == [[[5, 5], [5, 5]]] for c in original["candidates"]), "nonidentity activation failed")
        else:
            need(not original["candidates"], "negative control unexpectedly activated: " + name)
        if name in ("negative_empty_query_inventory", "negative_tied_query_inventory"):
            need(audited["query_blocked_exact_demo_families"] > 0, "query-before-fit blindspot control failed")
        if name == "negative_unsupported_query_color":
            need(original["counts"].get("exact_demonstration_fits", 0) > 0
                 and original["counts"].get("unsupported_query_color", 0) > 0,
                 "exact-before-query-color counter control failed")
        result[name] = {"accepted_candidates": audited["accepted_candidates"],
                        "legacy_counts": audited["legacy_counts"], "gates": audited["gates"],
                        "reason_counts": audited["reason_counts"],
                        "query_blocked_exact_demo_families": audited["query_blocked_exact_demo_families"]}
    # Independent tiny known-value controls of the existing color helper.
    _, exact, _, seen = base.recoloring([base.grid([[1, 1]])], [base.grid([[2, 3]])])
    need(not exact and bool(seen[1]), "inconsistent recoloring negative control failed")
    _, exact, table, seen = base.recoloring([base.grid([[1, 1]])], [base.grid([[2, 2]])])
    need(exact and not base.query_colors_supported(table, seen, [base.grid([[3]])]), "unsupported-color negative control failed")
    result["helper_controls"] = {"inconsistent_color_map_rejected": True, "unobserved_color_nonidentity_rejected": True}
    return result


def exclusive_json(path, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
    return sha(raw)


def timeout(signum, frame):
    raise TimeoutError("whole-process diagnostic wall cap")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--challenges", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--expected-challenge-sha256", default=REFERENCE_CHALLENGE_PIN)
    parser.add_argument("--expected-inventory-sha256", default=REFERENCE_INVENTORY_PIN)
    args = parser.parse_args()
    need(args.self_test or args.out is not None, "--out is required with --challenges")
    need(not args.self_test or args.out is None, "self-test does not write outputs")
    started, cpu_started = time.monotonic(), time.process_time()
    resource.setrlimit(resource.RLIMIT_CPU, (TOTAL_CPU_CAP, TOTAL_CPU_CAP + 5))
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, WALL_CAP)
    base, obj = modules()
    control_result = controls(base, obj)
    if args.self_test:
        print(json.dumps({"status": "SYNTHETIC_CONTROLS_PASS", "controls": control_result,
                          "actual_panel_run": False, "quality_claim": False}, sort_keys=True))
        return
    need(len(args.expected_challenge_sha256) == 64 and len(args.expected_inventory_sha256) == 64,
         "expected SHA256 values must contain 64 hexadecimal characters")
    challenge = args.challenges.resolve()
    tasks = pinned_json(challenge, args.expected_challenge_sha256)
    need(isinstance(tasks, dict), "challenge must be a dictionary")
    ids = sorted(tasks)
    need(len(ids) == 120 and sum(len(tasks[k]["test"]) for k in ids) == 172, "complete120/172 panel required")
    inventory_sha = sha(json.dumps(ids, separators=(",", ":")).encode())
    need(inventory_sha == args.expected_inventory_sha256, "panel inventory drift")
    for task in tasks.values():
        valid_task(task, base)
    out = args.out.resolve()
    need(out != challenge and out not in challenge.parents, "output cannot contain/replace the input")
    need(out.parent.is_dir(), "output parent must already exist")
    out.mkdir(exist_ok=False)
    names = ("PUBLIC_PREDICATE_RESULT.json", "PUBLIC_FAILURE.json")
    allowed = {str(out / name) for name in names}
    denied = []

    def audit(event, arguments):
        if event == "open":
            path, mode, flags = arguments
            if not isinstance(path, (str, bytes)) or str(pathlib.Path(path).resolve()) not in allowed or mode not in ("x", "xb"):
                denied.append(event)
                raise PermissionError("runtime file reads/nonexclusive writes forbidden")
        if event.startswith(("socket.", "subprocess.", "os.system")):
            denied.append(event)
            raise PermissionError("runtime network/child processes forbidden")

    sys.addaudithook(audit)
    completed = 0
    try:
        summed = {name: collections.Counter() for name in ("legacy_counts", "gates", "reason_counts")}
        task_counts = collections.Counter()
        candidate_tasks = 0
        for task_id in ids:
            audited = task_audit(tasks[task_id], base, obj)
            need(audited["complete"], "partial/capped diagnostic task")
            for name in summed:
                summed[name].update(audited[name])
            candidate_tasks += audited["accepted_candidates"] > 0
            for name in ("full_unique_shape_reject", "full_unique_recolor_conflict", "full_unique_exact_fit", "demo_unique_exact_fit"):
                task_counts["tasks_" + name] += bool(audited["gates"].get(name, 0))
            task_counts["tasks_query_blocked_exact_demo"] += audited["query_blocked_exact_demo_families"] > 0
            completed += 1
            if completed % 20 == 0:
                print("AUDITED", completed, flush=True)
        need(completed == 120 and not denied, "incomplete diagnostic or prohibited runtime access")
        need(time.monotonic() - started < WALL_CAP and time.process_time() - cpu_started < TOTAL_CPU_CAP, "budget exceeded")
        result = {"experiment_id": EXPERIMENT, "status": "COMPLETE_PORTABLE_INPUT_ONLY_DIAGNOSTIC",
                  "tasks": 120, "queries": 172, "controls": control_result,
                  "counts": {name: dict(value) for name, value in summed.items()}, "task_counts": dict(task_counts),
                  "candidate_tasks": candidate_tasks, "challenge_sha256": args.expected_challenge_sha256,
                  "inventory_sha256": inventory_sha, "source_pins": PINS,
                  "diagnostic_source_sha256": DIAGNOSTIC_PIN,
                  "separate_query_solutions_opened": False, "prediction_trace_opened": False,
                  "prediction_grids_written": False, "official_score": None, "quality_claim": False,
                  "claim_limit": "Public demo input/output and query INPUT only; aggregate predicate accounting, no query accuracy or neural-complementarity claim",
                  "elapsed_cpu_seconds": time.process_time() - cpu_started,
                  "elapsed_wall_seconds": time.monotonic() - started}
        exclusive_json(out / "PUBLIC_PREDICATE_RESULT.json", result)
        print(json.dumps(result, sort_keys=True), flush=True)
    except BaseException as error:
        try:
            exclusive_json(out / "PUBLIC_FAILURE.json", {"experiment_id": EXPERIMENT,
                "status": "FAIL_NO_QUALIFIED_DIAGNOSTIC", "completed_tasks": completed,
                "error_type": type(error).__name__, "error": str(error),
                "audit_denied_events": denied, "official_score": None})
        except BaseException:
            pass
        raise


if __name__ == "__main__":
    DIAGNOSTIC_PIN = sha(pathlib.Path(__file__).read_bytes())
    main()
