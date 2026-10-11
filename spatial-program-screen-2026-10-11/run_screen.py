"""Two-process-phase public screen. Predict/seal first; evaluate second. MIT."""
import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import resource
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    data = pathlib.Path(path).read_bytes()
    if len(data) > 8_000_000:
        raise ValueError("Input JSON exceeds 8 MB")
    return json.loads(data), digest(data)


def write_new(path, value):
    data = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    with pathlib.Path(path).open("xb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    return digest(data)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def predict(args):
    here, out = pathlib.Path(__file__).resolve().parent, pathlib.Path(args.out)
    protocol, protocol_sha = read_json(args.protocol)
    challenges, data_sha = read_json(args.challenges)
    solver = load_module("spatial_program", here / "spatial_program.py")
    controls = load_module("synthetic_checks", here / "synthetic_checks.py").run()
    pins = {n: digest((here/n).read_bytes()) for n in ("spatial_program.py", "synthetic_checks.py", "run_screen.py")}
    if pins != protocol["source_sha256"] or data_sha != protocol["challenges_sha256"]:
        raise ValueError("Source/data pins changed")
    if sorted(challenges) != protocol["task_ids_sorted"]:
        raise ValueError("Task inventory changed")
    resource.setrlimit(resource.RLIMIT_CPU, (140, 145))
    cpu, wall = time.process_time(), time.monotonic()
    rows = {}
    for task_id in sorted(challenges):
        begin = time.process_time()
        result = solver.solve_task(challenges[task_id], protocol["cpu_seconds_per_task"])
        rows[task_id] = dict(result, cpu_seconds=time.process_time()-begin)
    artifact = {"schema": "arc2-spatial-program-predictions-v1", "protocol_sha256": protocol_sha,
                "source_sha256": pins, "challenges_sha256": data_sha, "task_count": len(rows),
                "tasks": rows, "cpu_seconds": time.process_time()-cpu, "wall_seconds": time.monotonic()-wall,
                "synthetic_controls": controls, "evaluation_targets_read": False}
    pred_sha = write_new(out / "sealed_predictions.json", artifact)
    write_new(out / "PREDICTION_SEAL.json", {"schema": "arc2-spatial-program-seal-v1", "predictions_sha256": pred_sha,
              "protocol_sha256": protocol_sha, "source_sha256": pins, "challenges_sha256": data_sha,
              "targets_read_before_seal": False, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "official_score": None})
    print(json.dumps({"status": "PREDICTIONS_SEALED", "tasks": len(rows), "predictions_sha256": pred_sha,
                      "cpu_seconds": artifact["cpu_seconds"], "wall_seconds": artifact["wall_seconds"]}, sort_keys=True))


def evaluate(args):
    out = pathlib.Path(args.out)
    seal, seal_sha = read_json(out / "PREDICTION_SEAL.json")
    pred, pred_sha = read_json(out / "sealed_predictions.json")
    if pred_sha != seal["predictions_sha256"]:
        raise ValueError("Prediction seal mismatch")
    truth, truth_sha = read_json(args.solutions)
    if set(truth) != set(pred["tasks"]):
        raise ValueError("Truth/task inventory mismatch")
    rows = []
    for task, item in pred["tasks"].items():
        attempts = item["attempts"]
        if len(attempts) != len(truth[task]):
            raise ValueError("Query inventory mismatch")
        hit = [wanted in candidates for wanted, candidates in zip(truth[task], attempts)]
        rows.append({"task": task, "test_outputs": len(hit), "outputs_solved": sum(hit),
                     "all_outputs_solved": all(hit), "fractional_task_credit": sum(hit)/len(hit),
                     "outputs_with_candidate": sum(bool(x) for x in attempts), "fit_models": len(item["models"]),
                     "status": item["status"], "cpu_seconds": item["cpu_seconds"]})
    summary = {"schema": "arc2-spatial-program-development-result-v1", "status": "COMPLETE_PUBLIC_DEVELOPMENT_ONLY",
               "source_sha256": seal["source_sha256"], "protocol_sha256": seal["protocol_sha256"],
               "predictions_sha256": pred_sha, "prediction_seal_sha256": seal_sha,
               "challenges_sha256": seal["challenges_sha256"], "solutions_sha256": truth_sha,
               "tasks": len(rows), "test_outputs": sum(r["test_outputs"] for r in rows),
               "tasks_with_candidate": sum(r["outputs_with_candidate"] > 0 for r in rows),
               "outputs_with_candidate": sum(r["outputs_with_candidate"] for r in rows),
               "all_output_task_solves": sum(r["all_outputs_solved"] for r in rows),
               "outputs_solved": sum(r["outputs_solved"] for r in rows),
               "fractional_task_credit_sum": sum(r["fractional_task_credit"] for r in rows),
               "capped_tasks": sum(r["status"] == "CAPPED" for r in rows),
               "cpu_seconds": pred["cpu_seconds"], "wall_seconds": pred["wall_seconds"],
               "rows": rows, "official_score": None,
               "promotion": "HOLD_PENDING_NATIVE_BASELINE_COMPLEMENTARITY_AND_FROZEN_UNSEEN_PANEL",
               "limitations": ["Public evaluation is an exposed development panel, including historical human/model/solver exposure.",
                               "Leave-one-demonstration-out exactness is a grammar filter, not independent task validation.",
                               "Same-shape grammar only; at most two attempts per query; CPU caps are censoring, not proof of no fitting program.",
                               "Fill-only adapter preserves its supplied main grids, not the stronger 31.11 recipe across different execution versions."]}
    write_new(out / "PUBLIC_RESULTS.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("rows", "source_sha256", "limitations")}, sort_keys=True))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("phase", choices=("predict", "evaluate"))
    p.add_argument("--out", required=True); p.add_argument("--protocol"); p.add_argument("--challenges"); p.add_argument("--solutions")
    a = p.parse_args()
    if a.phase == "predict":
        if a.solutions or not a.protocol or not a.challenges:
            p.error("Prediction phase requires protocol/challenges and forbids solutions")
        predict(a)
    else:
        if a.protocol or a.challenges or not a.solutions:
            p.error("Evaluation phase requires solutions only")
        evaluate(a)
