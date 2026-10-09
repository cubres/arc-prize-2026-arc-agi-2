"""Original sealed CPU discovery runner: no solutions/reference arguments. MIT."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import time

HERE = Path(__file__).resolve().parent
CHALLENGE_SHA = "e7c62a4bd211867c6b538f66b8013b81f299663c82ca062f49a52bf439d6e4e8"
PIN_NAMES = ("PROTOCOL.json", "object_dsl.py", "run_predictions.py", "evaluate.py", "positive_controls.py")


def write_new(path, data):
    raw = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    with path.open("xb") as f: f.write(raw)
    return raw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--challenges", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    pins = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in PIN_NAMES}
    write_new(HERE / "PRE_PREDICTION_SOURCE_SEAL.json", {
        "source_pins": pins, "challenge_sha256_expected": CHALLENGE_SHA,
        "discovery_only": True, "solutions_opened_by_runner": False,
        "max_process_cpu_seconds": 180})
    raw = a.challenges.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CHALLENGE_SHA: raise RuntimeError("Frozen cohort mismatch")
    tasks = json.loads(raw)
    if len(tasks) != 120: raise RuntimeError("Cohort count mismatch")
    spec = importlib.util.spec_from_file_location("object_dsl", HERE / "object_dsl.py")
    import sys
    solver = importlib.util.module_from_spec(spec); sys.modules[spec.name] = solver; spec.loader.exec_module(solver)
    start_cpu, start_wall = time.process_time(), time.monotonic()
    outputs = {}; stripped_task_keys = 0; stripped_test_keys = 0; failures = 0
    for join_key, task in sorted(tasks.items()):
        if time.process_time() - start_cpu >= 165: raise RuntimeError("Whole cooperative CPU budget exhausted")
        stripped_task_keys += len(set(task) - {"train", "test"})
        stripped_test_keys += sum(len(set(pair) - {"input"}) for pair in task["test"])
        clean = {"train": [{"input": pair["input"], "output": pair["output"]} for pair in task["train"]],
                 "test": [{"input": pair["input"]} for pair in task["test"]]}
        try: outputs[join_key] = solver.solve_task(clean)
        except ValueError as error:
            failures += 1
            outputs[join_key] = {"attempts": [[] for _ in task["test"]], "fitted_programs": [],
                "distinct_bundles": 0, "timed_out": False, "abstention": "Contract rejection: " + str(error),
                "cpu_seconds": 0.0, "wall_seconds": 0.0, "programs_checked": 0, "chosen_programs": []}
    if time.process_time() - start_cpu >= 165: raise RuntimeError("Whole cooperative CPU budget exhausted")
    result = {"schema": "original-arc2-object-discovery-predictions-v1", "discovery_only": True,
        "source_pins": pins, "challenge_sha256": hashlib.sha256(raw).hexdigest(),
        "prediction_cpu_seconds": time.process_time() - start_cpu,
        "prediction_wall_seconds": time.monotonic() - start_wall,
        "instrumentation": {"solutions_opened_by_runner": False, "reference_opened_by_runner": False,
            "solver_receives_join_keys": False, "stripped_top_level_extra_keys": stripped_task_keys,
            "stripped_test_extra_keys": stripped_test_keys, "contract_rejections": failures}, "tasks": outputs}
    data = write_new(a.output, result)
    write_new(a.output.with_suffix(".seal.json"), {"sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data), "source_pins": pins})
    print(json.dumps({"tasks": len(outputs), "outputs": sum(len(x["attempts"]) for x in outputs.values()),
        "cpu_seconds": result["prediction_cpu_seconds"], "wall_seconds": result["prediction_wall_seconds"],
        "tasks_with_fit": sum(bool(x["fitted_programs"]) for x in outputs.values()),
        "timeout_tasks": sum(x["timed_out"] for x in outputs.values()),
        "prediction_sha256": hashlib.sha256(data).hexdigest()}, indent=2))


if __name__ == "__main__": main()
