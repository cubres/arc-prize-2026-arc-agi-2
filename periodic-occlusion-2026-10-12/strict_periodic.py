"""Original demonstration-consistent erased-color periodic completion.

Only train input/output pairs and query inputs enter this solver. There are no
task identifiers, stored task solutions, query labels or external model calls.
"""
from __future__ import annotations
import time


def checked_grid(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 30:
        raise ValueError("invalid grid height")
    width = len(value[0]) if isinstance(value[0], list) else 0
    if not 1 <= width <= 30:
        raise ValueError("invalid grid width")
    if any(not isinstance(row, list) or len(row) != width for row in value):
        raise ValueError("ragged grid")
    if any(type(c) is not int or not 0 <= c <= 9 for row in value for c in row):
        raise ValueError("invalid grid color")
    return value


def is_periodic(output, row_period, col_period):
    h, w = len(output), len(output[0])
    p, q = row_period or h, col_period or w
    return all(output[r][c] == output[r % p][c % q]
               for r in range(h) for c in range(w))


def complete(value, erased_color, row_period, col_period):
    """Require a visible, unambiguous observation for every lattice class."""
    h, w = len(value), len(value[0])
    p, q = row_period or h, col_period or w
    if p > h or q > w or (p == h and q == w):
        return None
    known = {}
    for r, row in enumerate(value):
        for c, color in enumerate(row):
            if color == erased_color:
                continue
            key = (r % p, c % q)
            if key in known and known[key] != color:
                return None
            known[key] = color
    if len(known) != p * q:
        return None
    return [[known[r % p, c % q] for c in range(w)] for r in range(h)]


def solve(task, seconds=0.25, max_period=10):
    started = time.monotonic()
    if set(task) != {"train", "test"} or not task["train"] or not task["test"]:
        raise ValueError("requires demonstrations and input-only queries")
    if any(set(pair) != {"input", "output"} for pair in task["train"]):
        raise ValueError("invalid demonstration fields")
    if any(set(pair) != {"input"} for pair in task["test"]):
        raise ValueError("query outputs are forbidden")
    demos = [(checked_grid(pair["input"]), checked_grid(pair["output"]))
             for pair in task["train"]]
    queries = [checked_grid(pair["input"]) for pair in task["test"]]
    if any((len(a), len(a[0])) != (len(b), len(b[0])) for a, b in demos):
        return {"candidates": [], "rules_tested": 0, "stop_reason": "shape_ineligible",
                "seconds": time.monotonic() - started}
    # An erased color must explain every changed pixel in every demonstration.
    changed = {a[r][c] for a, b in demos for r in range(len(a))
               for c in range(len(a[0])) if a[r][c] != b[r][c]}
    if len(changed) != 1:
        return {"candidates": [], "rules_tested": 0, "stop_reason": "erasure_ineligible",
                "seconds": time.monotonic() - started}
    erased = next(iter(changed))
    row_options = [None] + list(range(1, min(max_period, min(len(b) for _, b in demos)) + 1))
    col_options = [None] + list(range(1, min(max_period, min(len(b[0]) for _, b in demos)) + 1))
    rules = [(p, q) for p in row_options for q in col_options if p or q]
    # Prefer shorter descriptions; variable-size axes are explicitly penalized.
    rules.sort(key=lambda x: ((x[0] or 31) * (x[1] or 31), x[0] or 31, x[1] or 31))
    accepted, seen, tested = [], set(), 0
    stop = "rules_complete"
    for p, q in rules:
        if time.monotonic() - started >= seconds:
            stop = "time_cap"
            break
        tested += 1
        if not all(is_periodic(b, p, q) for _, b in demos):
            continue
        if not all(complete(a, erased, p, q) == b for a, b in demos):
            continue
        grids = [complete(a, erased, p, q) for a in queries]
        if any(g is None for g in grids):
            continue
        key = tuple(tuple(map(tuple, g)) for g in grids)
        if key in seen:
            continue
        seen.add(key)
        accepted.append({"rule": {"erased_color": erased, "row_period": p,
                                  "col_period": q}, "grids": grids,
                         "every_demonstration_exact": True})
    return {"candidates": accepted[:2], "distinct_candidates": len(accepted),
            "rules_tested": tested, "stop_reason": stop,
            "seconds": time.monotonic() - started}


def second_guess_overlay(baseline, periodic):
    """Preserve a populated first guess; prefer a distinct fitted periodic second."""
    result = baseline[:2]
    if not periodic:
        return result
    if not baseline:
        return periodic[:2]
    first_key = tuple(tuple(map(tuple, g)) for g in baseline[0]["grids"])
    for candidate in periodic:
        key = tuple(tuple(map(tuple, g)) for g in candidate["grids"])
        if key != first_key:
            return [baseline[0], candidate]
    return result
