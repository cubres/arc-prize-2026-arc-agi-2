"""Standalone reproduction adapter; staged preparation/prediction/evaluation.

The archived measured worker is distinct from this readable publication adapter.
Supply the unchanged corrected37 component; it is not duplicated in this pack.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import resource
import sys
import time

if not __debug__:
    raise RuntimeError("Run without -O: reproduction integrity checks must stay enabled")

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    raw = (json.dumps(value, sort_keys=True) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
    return sha(raw)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(args, meta, panel):
    import requests
    args.work.mkdir(exist_ok=False)
    baseline = args.baseline.resolve()
    assert sha(baseline.read_bytes()) == meta["baseline_source_sha256"]
    solver = HERE / panel["solver_module"]
    assert sha(solver.read_bytes()) == panel["solver_sha256"]
    save(args.work / "SOURCE_AND_PANEL_FREEZE.json", {
        "arm": args.arm, "baseline_path": str(baseline),
        "baseline_sha256": meta["baseline_source_sha256"],
        "solver_sha256": panel["solver_sha256"],
        "adapter_sha256": sha(pathlib.Path(__file__).read_bytes()),
        "panel_metadata_sha256": sha((HERE / "PUBLIC_PANEL_METADATA.json").read_bytes()),
        "selected_filenames_and_blob_ids_frozen": panel["selected"],
        "publication_adapter_not_original_executed_worker": True})
    challenges, answers = [], {}
    total = 0
    for entry in panel["selected"]:
        path = entry["path"]
        assert path.startswith("data/training/") and path.endswith(".json")
        response = requests.get("https://raw.githubusercontent.com/arcprize/ARC-AGI-2/" +
                                meta["source_revision"] + "/" + path,
                                timeout=20, allow_redirects=False)
        assert response.status_code == 200
        raw = response.content
        total += len(raw)
        assert total <= 4_000_000 and len(raw) == entry["size"]
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == entry["sha"]
        task = json.loads(raw)
        key = pathlib.PurePosixPath(path).stem
        assert set(task) == {"train", "test"} and task["train"] and task["test"]
        challenges.append({"task_id": key, "train": task["train"],
                           "test": [{"input": q["input"]} for q in task["test"]]})
        answers[key] = [q["output"] for q in task["test"]]
    csha = save(args.work / "CHALLENGES.json", challenges)
    asha = save(args.work / "HELD_ANSWERS.json", answers)
    save(args.work / "PREPARED.json", {"tasks": len(challenges),
         "challenge_sha256": csha, "answers_sha256": asha, "raw_bytes": total})
    print("Prepared", len(challenges), "official public training tasks")


def predict(args, meta, panel):
    freeze = json.loads((args.work / "SOURCE_AND_PANEL_FREEZE.json").read_bytes())
    assert freeze["arm"] == args.arm
    assert freeze["panel_metadata_sha256"] == sha((HERE / "PUBLIC_PANEL_METADATA.json").read_bytes())
    assert freeze["adapter_sha256"] == sha(pathlib.Path(__file__).read_bytes())
    baseline_path = pathlib.Path(freeze["baseline_path"])
    assert sha(baseline_path.read_bytes()) == freeze["baseline_sha256"] == meta["baseline_source_sha256"]
    assert sha((HERE / panel["solver_module"]).read_bytes()) == freeze["solver_sha256"] == panel["solver_sha256"]
    baseline = load_module(baseline_path, "baseline37")
    periodic = load_module(HERE / panel["solver_module"], "periodic")
    prep = json.loads((args.work / "PREPARED.json").read_bytes())
    raw = (args.work / "CHALLENGES.json").read_bytes()
    assert sha(raw) == prep["challenge_sha256"]
    records = json.loads(raw)
    assert len(records) == len({r["task_id"] for r in records}) == len(panel["selected"])
    allowed_outputs = {str((args.work / name).resolve()) for name in ["PREDICTIONS.json", "PREDICTION_SEAL.json"]}

    def audit(event, values):
        if event == "open" and isinstance(values[0], (str, bytes)):
            assert str(pathlib.Path(values[0]).resolve()) in allowed_outputs, "unexpected later file access"
        assert not event.startswith(("socket.", "subprocess.", "os.system")), "network/child processes forbidden"

    started, cpu_started = time.monotonic(), time.process_time()
    resource.setrlimit(resource.RLIMIT_CPU, (450, 455))
    sys.addaudithook(audit)
    results = []
    for row in records:
        assert time.monotonic() - started < 470, "incomplete run is not a result"
        task = {"train": row["train"], "test": row["test"]}
        control = baseline.solve(task, seconds=1.8, max_depth=3, beam=96, state_cap=10000)
        extra = periodic.solve(task, seconds=0.25, max_period=10)
        treatment = periodic.second_guess_overlay(control["expanded"], extra["candidates"])
        assert len(treatment) <= 2
        assert not control["expanded"] or treatment[0] == control["expanded"][0]
        results.append({"task_id": row["task_id"], "baseline": control["expanded"],
                        "treatment": treatment, "periodic": extra,
                        "baseline_stop": control["stop_reason"]})
    result_sha = save(args.work / "PREDICTIONS.json", results)
    save(args.work / "PREDICTION_SEAL.json", {"tasks": len(results), "prediction_sha256": result_sha,
         "challenge_sha256": sha(raw), "elapsed_wall_seconds": time.monotonic() - started,
         "elapsed_cpu_seconds": time.process_time() - cpu_started,
         "query_labels_read_by_predictor": False, "audit_scope": "later Python file/network accesses only"})
    print("Sealed", len(results), "paired predictions")


def evaluate(args, meta, panel):
    seal = json.loads((args.work / "PREDICTION_SEAL.json").read_bytes())
    raw = (args.work / "PREDICTIONS.json").read_bytes()
    assert sha(raw) == seal["prediction_sha256"]
    records = json.loads(raw)
    expected = {pathlib.PurePosixPath(e["path"]).stem for e in panel["selected"]}
    assert len(records) == len(expected) == seal["tasks"]
    assert {r["task_id"] for r in records} == expected
    assert all(len(r["baseline"]) <= 2 and len(r["treatment"]) <= 2 for r in records)
    prep = json.loads((args.work / "PREPARED.json").read_bytes())
    assert sha((args.work / "CHALLENGES.json").read_bytes()) == prep["challenge_sha256"] == seal["challenge_sha256"]
    # First held-answer read occurs after the complete prediction gate above.
    answer_raw = (args.work / "HELD_ANSWERS.json").read_bytes()
    assert sha(answer_raw) == prep["answers_sha256"]
    answers = json.loads(answer_raw)
    counts = dict.fromkeys(["baseline_top1", "treatment_top1", "baseline_any2", "treatment_any2",
                           "wins", "losses", "ties", "periodic_activation", "prediction_changes"], 0)
    for row in records:
        truth = answers[row["task_id"]]
        b, t = row["baseline"], row["treatment"]
        bs, ts = any(c["grids"] == truth for c in b), any(c["grids"] == truth for c in t)
        counts["baseline_top1"] += bool(b and b[0]["grids"] == truth)
        counts["treatment_top1"] += bool(t and t[0]["grids"] == truth)
        counts["baseline_any2"] += bs
        counts["treatment_any2"] += ts
        counts["wins"] += ts and not bs
        counts["losses"] += bs and not ts
        counts["ties"] += bs == ts
        counts["periodic_activation"] += bool(row["periodic"]["candidates"])
        counts["prediction_changes"] += [c["grids"] for c in b] != [c["grids"] for c in t]
    save(args.work / "RESULT.json", {"counts": counts, "tasks": len(records), "runtime": seal,
         "scope": "public training only; no neural/native/official score evidence"})
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "predict", "evaluate"])
    parser.add_argument("--arm", choices=["strict", "background"], required=True)
    parser.add_argument("--work", type=pathlib.Path, required=True)
    parser.add_argument("--baseline", type=pathlib.Path)
    args = parser.parse_args()
    args.work = args.work.resolve()
    meta = json.loads((HERE / "PUBLIC_PANEL_METADATA.json").read_bytes())
    panel = meta["panels"][args.arm]
    if args.stage == "prepare":
        parser.error("prepare requires --baseline") if args.baseline is None else None
    {"prepare": prepare, "predict": predict, "evaluate": evaluate}[args.stage](args, meta, panel)
