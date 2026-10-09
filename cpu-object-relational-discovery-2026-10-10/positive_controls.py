"""Invented positive/metamorphic controls; no ARC task payloads or IDs. MIT."""
import json
from pathlib import Path
from object_dsl import objects, select, solve_task, grid
import time


def canvas(shape, color, position, distractor, bg=0, height=10, width=12):
    g = [[bg] * width for _ in range(height)]
    for r, c in shape: g[r + position[0]][c + position[1]] = color
    g[distractor[0]][distractor[1]] = distractor[2]
    return g


def cut(shape, color, bg=0):
    g = [[bg] * (max(c for r, c in shape) + 1) for _ in range(max(r for r, c in shape) + 1)]
    for r, c in shape: g[r][c] = color
    return g


def pairs_copy(bg, source_color, anchor_color, sr, sc, ar, ac, height=12, width=16):
    g = [[bg] * width for _ in range(height)]
    for r, c in ((0, 0), (0, 1)): g[sr + r][sc + c] = source_color
    for r, c in ((0, 0), (1, 0), (2, 0), (2, 1), (3, 0)): g[ar + r][ac + c] = anchor_color
    out = [row[:] for row in g]
    for c in range(2): out[ar][ac + 2 + c] = source_color
    return g, out


def main():
    checks = []
    def check(name, condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    shape_a = ((0, 0), (1, 0), (1, 1))
    shape_b = ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))
    train = [{"input": canvas(shape_a, 2, (1, 2), (8, 10, 6)), "output": cut(shape_a, 2)},
             {"input": canvas(shape_b, 3, (6, 8), (1, 1, 7)), "output": cut(shape_b, 3)}]
    test = canvas(shape_b, 4, (3, 4), (10, 14, 9), height=13, width=17)
    result = solve_task({"train": train, "test": [{"input": test}]})
    check("unique largest object crop under translated resized canvas", cut(shape_b, 4) in result["attempts"][0])
    palette = {0: 5, 2: 8, 3: 1, 4: 7, 6: 0, 7: 6, 9: 2}
    perm = lambda g: [[palette[c] for c in row] for row in g]
    changed = {"train": [{"input": perm(p["input"]), "output": perm(p["output"])} for p in train], "test": [{"input": perm(test)}]}
    result_perm = solve_task(changed)
    check("crop prediction equivariant under palette permutation with changed background", perm(cut(shape_b, 4)) in result_perm["attempts"][0])
    relation_train = [pairs_copy(0, 2, 3, 8, 1, 2, 7), pairs_copy(0, 4, 8, 1, 11, 6, 3)]
    relation_test = pairs_copy(5, 1, 7, 10, 1, 3, 8, height=15, width=18)
    result_copy = solve_task({"train": [{"input": a, "output": b} for a, b in relation_train], "test": [{"input": relation_test[0]}]})
    # Background changed between training and test: only unique-mode segmentation is viable.
    check("copy smallest object adjacent to largest anchor with changed colors and canvas", relation_test[1] in result_copy["attempts"][0])
    def bridge(h, w, row, left, right, color, anchor):
        g = [[0] * w for _ in range(h)]; g[row][left] = color; g[row][right] = anchor
        out = [x[:] for x in g]
        for c in range(left + 1, right): out[row][c] = color
        return g, out
    bridge_pairs = [bridge(6, 9, 2, 1, 6, 2, 3), bridge(8, 12, 5, 3, 10, 4, 7)]
    bridge_test = bridge(11, 15, 7, 2, 12, 6, 8)
    result_bridge = solve_task({"train": [{"input": a, "output": b} for a, b in bridge_pairs], "test": [{"input": bridge_test[0]}]})
    check("axis bridge extends across new distance and color", bridge_test[1] in result_bridge["attempts"][0])
    tied = grid([[0, 0, 0, 0, 0], [0, 2, 0, 3, 0], [0, 0, 0, 0, 0]])
    obs = objects(tied, 0, 4, True, time.process_time() + 1)
    check("equal-area object selector abstains rather than choosing coordinate order", select(obs, "largest_area") is None)
    for name, task in (("test truth", {"train": train, "test": [{"input": test, "output": test}]}),
                       ("top-level identifier", {"train": train, "test": [{"input": test}], "task_id": "invented"}),
                       ("nested identifier", {"train": train, "test": [{"input": test, "uid": "invented"}]})):
        try: solve_task(task)
        except ValueError: checks.append("reject " + name)
        else: raise AssertionError("Accepted " + name)
    for name, value in (("31-column grid", [[0] * 31]), ("ragged grid", [[0, 0], [0]]), ("bool color", [[True]])):
        try: grid(value)
        except ValueError: checks.append("reject " + name)
        else: raise AssertionError("Accepted " + name)
    summary = {"schema": "invented-object-dsl-controls-v1", "passed": len(checks), "checks": checks,
               "limits": "Synthetic controls establish mechanics only; no benchmark or official score claims."}
    with (Path(__file__).resolve().parent / "POSITIVE_CONTROLS.json").open("x") as f:
        json.dump(summary, f, indent=2); f.write("\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
