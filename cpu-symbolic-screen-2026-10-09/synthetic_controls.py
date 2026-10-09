"""Invented positive controls, separate from public tasks and their solutions."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("solver", HERE / "symbolic_supplement.py")
solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solver)


def nested(g):
    return [list(row) for row in g]


def main():
    examples = [((1, 2, 0), (0, 1, 2)), ((2, 1), (0, 2), (1, 0)), ((1, 0, 2), (2, 0, 1), (0, 1, 2))]
    held = ((2, 0, 1), (1, 2, 0), (0, 0, 2), (1, 0, 1))
    operations = {"identity": lambda g: g, "rotation90": lambda g: solver.orient(g, 1),
                  "horizontal_reflect": lambda g: solver.orient(g, 4),
                  "scale2x3": lambda g: solver.resize(g, "nearest", 2, 3),
                  "tile2x3": lambda g: solver.resize(g, "tile", 2, 3),
                  "recolor": lambda g: tuple(tuple({0:0, 1:4, 2:7}[c] for c in row) for row in g)}
    def pad(g):
        border = (0,) * (len(g[0]) + 2)
        return (border,) + tuple((0,) + row + (0,) for row in g) + (border,)
    cases = []
    for name, operation in operations.items():
        train = [{"input": nested(g), "output": nested(operation(g))} for g in examples]
        result = solver.solve_task({"train": train, "test": [{"input": nested(held)}]})
        cases.append({"control": name, "passed": nested(operation(held)) in result["attempts"][0],
                      "fit_count": result["fit_count"]})
    train = [{"input": nested(pad(g)), "output": nested(g)} for g in examples]
    result = solver.solve_task({"train": train, "test": [{"input": nested(pad(held))}]})
    cases.append({"control": "foreground_crop", "passed": nested(held) in result["attempts"][0],
                  "fit_count": result["fit_count"]})
    payload = {"status": "PASS" if all(c["passed"] for c in cases) else "FAIL", "cases": cases,
               "scope": "Invented correctness controls only. No public evaluation retuning."}
    with (HERE / "SYNTHETIC_CONTROLS.json").open("x") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(json.dumps(payload, indent=2))
    if payload["status"] != "PASS":
        raise RuntimeError("Synthetic control failed")


if __name__ == "__main__":
    main()
