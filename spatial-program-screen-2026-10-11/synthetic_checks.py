"""Invented controls, separate from public-task solve evidence. MIT."""
import copy
import importlib.util
import pathlib
import time


def module():
    path = pathlib.Path(__file__).with_name("spatial_program.py")
    spec = importlib.util.spec_from_file_location("spatial_program", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def run():
    s = module()
    results = []
    def check(name, condition):
        if not condition:
            raise ValueError("Invented control failed: " + name)
        results.append(name)
    def reject(name, call):
        try:
            call()
        except ValueError:
            check(name, True)
        else:
            check(name, False)
    rejects = ([], [[1, 2], [3]], [[True]], [[10]], [[1.0]], [(1,)])
    for i, g in enumerate(rejects):
        reject("malformed_grid_%s" % i, lambda g=g: s.grid(g))
    x, y = [[1]], [[2]]
    check("full_main_unchanged", s.fill_only([x, y], [[[3]]]) == [x, y])
    check("one_main_preserved", s.fill_only([x], [x, y]) == [x, y])
    check("duplicated_main_fill", s.fill_only([x, x], [y]) == [x, y])
    check("empty_main_fill", s.fill_only([], [x, y]) == [x, y])
    check("both_empty", s.fill_only([], []) == [])
    reject("invalid_supplement_rejected", lambda: s.fill_only([x], [[[True]]]))
    task = {"train": [{"input": [[1, 0], [0, 2]], "output": [[1, 0], [0, 2]]},
                      {"input": [[3, 3, 0], [0, 4, 0]], "output": [[3, 3, 0], [0, 4, 0]]}],
            "test": [{"input": [[8, 9], [7, 6]]}]}
    before = copy.deepcopy(task)
    solved = s.solve_task(task, cpu_seconds=0.75)
    check("identity_unseen_colors", solved["attempts"] == [[[[8, 9], [7, 6]]]])
    check("identity_crossvalidated", all(m["leave_one_demo_out_exact"] == 2 for m in solved["models"]))
    check("inputs_unchanged", task == before)
    bad = copy.deepcopy(task); bad["test"][0]["output"] = [[1]]
    reject("query_outputs_forbidden", lambda: s.solve_task(bad))
    bad = copy.deepcopy(task); bad["id"] = "anything"
    reject("task_identifiers_forbidden", lambda: s.solve_task(bad))
    bad = copy.deepcopy(task); bad["train"][0]["output"] = [[1]]
    check("shape_change_abstains", s.solve_task(bad)["attempts"] == [[]])
    for cap in (float("nan"), float("inf"), -1, 0, True, 11):
        reject("invalid_cpu_cap_%s" % repr(cap), lambda cap=cap: s.solve_task(task, cap))
    for g in ([[1]], [[1, 2], [3, 4]], [[0]*30 for _ in range(30)]):
        fs, bg = s.features(s.grid(g))
        check("feature_count_%sx%s" % (len(g), len(g[0])),
              len(fs) == len(g)*len(g[0]) and all(len(v) == len(s.FEATURE_NAMES) for v in fs))
    ring = [[0]*6 for _ in range(6)]
    for r in range(1, 5):
        for c in range(1, 5):
            if r in (1, 4) or c in (1, 4): ring[r][c] = 2
    fs, bg = s.features(s.grid(ring)); idx = s.FEATURE_NAMES.index("enclosed_background")
    check("enclosure_interior", all(fs[r*6+c][idx] == 1 for r in (2, 3) for c in (2, 3)))
    check("enclosure_exterior", all(fs[r*6+c][idx] == 0 for r in (0, 5) for c in range(6)))
    # Repeated copies provide enough support for min_leaf=4; different object
    # colors and sizes make this a small spatial rule rather than a color lookup.
    rings = []
    for n, color in ((7, 2), (8, 3), (9, 4)):
        a = [[0]*n for _ in range(n)]; b = [[0]*n for _ in range(n)]
        for r in range(1, n-1):
            for c in range(1, n-1):
                a[r][c] = color if r in (1, n-2) or c in (1, n-2) else 0
                b[r][c] = color if a[r][c] else 8
        rings.append((a, b))
    demo = {"train": [{"input": a, "output": b} for a, b in rings[:2]],
            "test": [{"input": rings[2][0]}]}
    sol = s.solve_task(demo, 0.75)
    check("enclosure_rule_generalizes_invented", rings[2][1] in sol["attempts"][0])
    check("fit_tree_pure_label", s.fit_tree([(0,)*len(s.FEATURE_NAMES)]*4, [10]*4, 4, 4, time.process_time()+1) == {"label": 10})
    return {"status": "PASS_INVENTED_CONTROLS", "count": len(results), "controls": results}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), sort_keys=True))
