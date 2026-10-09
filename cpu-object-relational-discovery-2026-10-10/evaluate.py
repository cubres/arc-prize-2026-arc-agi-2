"""Separate sealed public-discovery evaluator. Inputs remain private local files. MIT."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOLUTION_SHA = "84be4f4f39b79e82c36d565fc878830988b094917f052ee7069aef30b33ca8f1"
REFERENCE_SHA = "431be75903b9aa1458ceee95524e34c703c6ab931f49fb2a673ce25894af20f0"


def write_new(path, value):
    with path.open("x") as f: json.dump(value, f, indent=2, sort_keys=True); f.write("\n")


def main():
    p = argparse.ArgumentParser()
    for name in ("predictions", "solutions", "reference", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    raw = a.predictions.read_bytes(); seal = json.loads(a.predictions.with_suffix(".seal.json").read_text())
    if hashlib.sha256(raw).hexdigest() != seal["sha256"] or len(raw) != seal["bytes"]: raise RuntimeError("Prediction seal mismatch")
    for name, pin in seal["source_pins"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != pin: raise RuntimeError("Source seal mismatch")
    predictions = json.loads(raw)
    solution_raw = a.solutions.read_bytes(); reference_raw = a.reference.read_bytes()
    if hashlib.sha256(solution_raw).hexdigest() != SOLUTION_SHA: raise RuntimeError("Solution cohort mismatch")
    if hashlib.sha256(reference_raw).hexdigest() != REFERENCE_SHA: raise RuntimeError("Reference mismatch")
    solutions, reference = json.loads(solution_raw), json.loads(reference_raw)
    if set(predictions["tasks"]) != set(solutions) or set(reference) != set(solutions): raise RuntimeError("Task coverage mismatch")
    rows = []
    for key, truths in sorted(solutions.items()):
        own = predictions["tasks"][key]
        if len(own["attempts"]) != len(truths) or len(reference[key]) != len(truths): raise RuntimeError("Output coverage mismatch")
        row = {"task": key, "outputs": len(truths), "reference": [], "object_dsl": [], "fill_only": [], "oracle_union": []}
        for i, truth in enumerate(truths):
            originals = [reference[key][i]["attempt_1"], reference[key][i]["attempt_2"]]
            candidates = own["attempts"][i]
            if len(candidates) > 2 or len({json.dumps(g) for g in candidates}) != len(candidates): raise RuntimeError("Invalid attempt count")
            merged = []
            for g in originals:
                if g and g not in merged: merged.append(g)
            for g in candidates:
                if len(merged) < 2 and g not in merged: merged.append(g)
            base_hit, own_hit = truth in originals, truth in candidates
            row["reference"].append(base_hit); row["object_dsl"].append(own_hit)
            row["fill_only"].append(truth in merged); row["oracle_union"].append(base_hit or own_hit)
        rows.append(row)
    metrics = {}
    for name in ("reference", "object_dsl", "fill_only", "oracle_union"):
        credit = sum((Fraction(sum(row[name]), row["outputs"]) for row in rows), Fraction())
        metrics[name] = {"exact_outputs": sum(sum(row[name]) for row in rows),
            "fully_solved_tasks": sum(all(row[name]) for row in rows),
            "fractional_task_credit_exact": str(credit), "mean_task_credit_exact": str(credit / len(rows)),
            "mean_fractional_credit_percent": float(100 * credit / len(rows))}
    tasks = list(predictions["tasks"].values())
    summary = {"schema": "original-arc2-object-discovery-result-v1", "discovery_only": True, "official_score": None,
        "tasks": len(rows), "outputs": sum(row["outputs"] for row in rows), "metrics": metrics,
        "unique_incremental_outputs": sum(sum(b and not a for a, b in zip(row["reference"], row["object_dsl"])) for row in rows),
        "fill_only_incremental_outputs": metrics["fill_only"]["exact_outputs"] - metrics["reference"]["exact_outputs"],
        "prediction_cpu_seconds": predictions["prediction_cpu_seconds"], "prediction_wall_seconds": predictions["prediction_wall_seconds"],
        "maximum_recorded_task_cpu_seconds": max(x["cpu_seconds"] for x in tasks), "timed_records": sum("cpu_seconds" in x for x in tasks),
        "timeout_tasks": sum(x["timed_out"] for x in tasks), "ambiguous_tasks": sum(x["distinct_bundles"] > 2 for x in tasks),
        "tasks_with_fit": sum(bool(x["fitted_programs"]) for x in tasks),
        "nonempty_output_slots": sum(bool(attempts) for x in tasks for attempts in x["attempts"]),
        "total_programs_checked": sum(x["programs_checked"] for x in tasks),
        "prediction_sha256": seal["sha256"], "solution_sha256": SOLUTION_SHA, "reference_sha256": REFERENCE_SHA,
        "instrumentation": predictions["instrumentation"],
        "limits": ["Already-exposed public discovery; not held-out evidence or an official score.",
            "Task and whole-run budgets are cooperative; process CPU resource limit is 180 seconds.",
            "Timed-out and more-than-two-bundle tasks abstain.", "Oracle union is an upper bound, not a deployable selector.",
            "Unsigned seals bind current bytes, not independently proven chronology or historical non-exposure."]}
    write_new(a.output, {**summary, "rows": rows})
    write_new(a.output.with_name("PUBLIC_RESULT_SUMMARY.json"), summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
