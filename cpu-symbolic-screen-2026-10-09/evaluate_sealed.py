"""Post-seal public evaluation only; never imported by the solver. MIT."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--solutions", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.predictions.read_bytes()
    seal = json.loads(args.predictions.with_suffix(".seal.json").read_text())
    if hashlib.sha256(raw).hexdigest() != seal["prediction_sha256"]:
        raise RuntimeError("Prediction seal mismatch")
    prediction = json.loads(raw)
    here = Path(__file__).resolve().parent
    for name, sha in seal["sources"].items():
        if hashlib.sha256((here/name).read_bytes()).hexdigest() != sha:
            raise RuntimeError("Source changed after sealing")
    solution_raw = args.solutions.read_bytes()
    reference_raw = args.reference.read_bytes()
    solutions, reference = json.loads(solution_raw), json.loads(reference_raw)
    if set(prediction["tasks"]) != set(solutions) or set(reference) != set(solutions):
        raise RuntimeError("Require exact public task coverage")
    rows = []
    for task_id, truths in solutions.items():
        predicted = prediction["tasks"][task_id]
        if len(predicted["attempts"]) != len(truths) or len(reference[task_id]) != len(truths):
            raise RuntimeError("Output coverage mismatch")
        own, strict, base, fill_merge = [], [], [], []
        for i, truth in enumerate(truths):
            own.append(truth in predicted["attempts"][i])
            strict.append(truth in predicted["strict"][i])
            main = [reference[task_id][i]["attempt_1"], reference[task_id][i]["attempt_2"]]
            base.append(truth in main)
            # Fixed fill-only policy: retain both distinct valid reference
            # grids; if duplicated/empty, add the first distinct symbolic grid.
            distinct = []
            for g in main:
                if g and g not in distinct:
                    distinct.append(g)
            for g in predicted["attempts"][i]:
                if len(distinct) < 2 and g not in distinct:
                    distinct.append(g)
            fill_merge.append(truth in distinct)
        rows.append({"task": task_id, "outputs": len(truths), "base": base, "symbolic": own,
                     "strict": strict, "fill_merge": fill_merge,
                     "oracle_union": [a or b for a, b in zip(base, own)],
                     "programs": predicted.get("chosen", []), "fits": predicted["fit_count"]})
    metrics = {}
    for name in ("base", "symbolic", "strict", "fill_merge", "oracle_union"):
        metrics[name] = {"exact_outputs": sum(sum(row[name]) for row in rows),
                         "fully_solved_tasks": sum(all(row[name]) for row in rows),
                         "fractional_task_credit": sum(sum(row[name])/row["outputs"] for row in rows)}
    result = {"schema": "arc2-symbolic-public-evaluation-v1", "official_score": None,
              "tasks": len(rows), "outputs": sum(row["outputs"] for row in rows), "metrics": metrics,
              "prediction_sha256": seal["prediction_sha256"],
              "solutions_sha256": hashlib.sha256(solution_raw).hexdigest(),
              "reference_sha256": hashlib.sha256(reference_raw).hexdigest(),
              "new_exact_outputs_vs_recipe": sum(sum(s and not b for s, b in zip(row["symbolic"], row["base"])) for row in rows),
              "new_fill_exact_outputs_vs_recipe": sum(sum(s and not b for s, b in zip(row["fill_merge"], row["base"])) for row in rows),
              "limitations": ["Public evaluation is exposed; no hidden leaderboard claim.",
                              "Oracle union cannot be deployed within two attempts without a selection rule.",
                              "No tuning after this evaluation."], "rows": rows}
    with args.output.open("x") as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
