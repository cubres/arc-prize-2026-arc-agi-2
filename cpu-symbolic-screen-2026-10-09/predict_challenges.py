"""Seal predictions before a separate evaluator may open solutions. MIT."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("symbolic_supplement", HERE / "symbolic_supplement.py")
solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solver)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--challenges", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError("Refusing to overwrite an earlier experiment")
    raw = args.challenges.read_bytes()
    challenges = json.loads(raw)
    start = time.monotonic()
    results, total = {}, len(challenges)
    for number, (task_id, task) in enumerate(sorted(challenges.items()), 1):
        # Task identifiers key the output only; the solver never receives them.
        clean = {"train": task["train"], "test": [{"input": p["input"]} for p in task["test"]]}
        task_start = time.monotonic()
        results[task_id] = solver.solve_task(clean)
        results[task_id]["seconds"] = time.monotonic() - task_start
        if number % 20 == 0:
            print(f"Predicted {number}/{total}", flush=True)
    payload = {"schema": "arc2-symbolic-predictions-v1", "solutions_opened": False,
               "challenge_sha256": hashlib.sha256(raw).hexdigest(), "seconds": time.monotonic() - start,
               "sources": {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                           for name in ("PROTOCOL.json", "symbolic_supplement.py", "predict_challenges.py")},
               "tasks": results}
    serialized = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    with args.output.open("xb") as f:
        f.write(serialized)
    seal = {"prediction_sha256": hashlib.sha256(serialized).hexdigest(),
            "bytes": len(serialized), "solutions_opened": False, "sources": payload["sources"]}
    with args.output.with_suffix(".seal.json").open("x") as f:
        json.dump(seal, f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps({"tasks": total, "seconds": payload["seconds"], **seal}, indent=2))


if __name__ == "__main__":
    main()
