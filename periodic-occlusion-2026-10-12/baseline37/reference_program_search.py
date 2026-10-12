"""Original bounded grid-program search; public demonstration pairs only.

No task identifiers, persistent task memory, external model, or query answers
enter solve(). Observational equivalence includes every query input so programs
that agree on examples but disagree on queries stay distinct.
"""
from __future__ import annotations

import collections
import time
import numpy as np


def grid(value):
    a = np.asarray(value)
    if a.ndim != 2 or not all(1 <= n <= 30 for n in a.shape):
        raise ValueError("invalid dimensions")
    if not np.issubdtype(a.dtype, np.integer) or np.any(a < 0) or np.any(a > 9):
        raise ValueError("invalid colors")
    return a.astype(np.uint8)


def signature(arrays):
    return tuple((a.shape, a.tobytes()) for a in arrays)


def crop(a, background):
    b = int(np.bincount(a.ravel(), minlength=10).argmax()) if background is None else background
    rows, cols = np.nonzero(a != b)
    if len(rows) == 0:
        return a
    return a[rows.min():rows.max() + 1, cols.min():cols.max() + 1]


def contract(a, axis, uniform):
    if uniform:
        if axis == 0:
            keep = np.any(a != a[:, :1], axis=1)
        else:
            keep = np.any(a != a[:1, :], axis=0)
    else:
        if axis == 0:
            keep = np.r_[True, np.any(a[1:] != a[:-1], axis=1)]
        else:
            keep = np.r_[True, np.any(a[:, 1:] != a[:, :-1], axis=0)]
    if not keep.any():
        raise ValueError("empty contraction")
    return a[keep] if axis == 0 else a[:, keep]


def repeat(a, h, w, tiling):
    if a.shape[0] * h > 30 or a.shape[1] * w > 30:
        raise ValueError("oversize repeat")
    return np.tile(a, (h, w)) if tiling else np.repeat(np.repeat(a, h, axis=0), w, axis=1)


def downsample(a, factor):
    h, w = a.shape
    if h % factor or w % factor:
        raise ValueError("nonintegral blocks")
    small = a[::factor, ::factor]
    if not np.array_equal(a, repeat(small, factor, factor, False)):
        raise ValueError("nonuniform blocks")
    return small


def panel(a, axis, operator):
    n = a.shape[axis]
    if n % 2:
        raise ValueError("unequal panels")
    lhs, rhs = np.split(a != 0, 2, axis=axis)
    if operator == "or":
        value = lhs | rhs
    elif operator == "and":
        value = lhs & rhs
    else:
        value = lhs ^ rhs
    return value.astype(np.uint8)


def operations():
    ops = []
    for k in (1, 2, 3):
        ops.append(("rot" + str(k), lambda a, k=k: np.rot90(a, k)))
    ops += [("flip_h", np.fliplr), ("flip_v", np.flipud),
            ("transpose", np.transpose), ("anti_transpose", lambda a: np.rot90(a, 2).T)]
    ops += [("crop_majority", lambda a: crop(a, None)), ("crop_zero", lambda a: crop(a, 0))]
    for axis in (0, 1):
        for uniform in (False, True):
            ops.append((f"contract_{axis}_{int(uniform)}", lambda a, axis=axis, uniform=uniform: contract(a, axis, uniform)))
    for factor in (2, 3):
        ops.append((f"uniform_down_{factor}", lambda a, factor=factor: downsample(a, factor)))
    for tiling in (False, True):
        for h in (1, 2, 3):
            for w in (1, 2, 3):
                if h != 1 or w != 1:
                    ops.append((f"{'tile' if tiling else 'scale'}_{h}_{w}", lambda a, h=h, w=w, tiling=tiling: repeat(a, h, w, tiling)))
    for axis in (0, 1):
        for operator in ("or", "and", "xor"):
            ops.append((f"panel_{axis}_{operator}", lambda a, axis=axis, operator=operator: panel(a, axis, operator)))
    return ops


def recoloring(inputs, outputs):
    counts = np.zeros((10, 10), dtype=np.int64)
    shape_error = 0
    pixels = 0
    for a, b in zip(inputs, outputs):
        shape_error += abs(a.shape[0] - b.shape[0]) + abs(a.shape[1] - b.shape[1])
        if a.shape != b.shape:
            continue
        counts += np.bincount((10 * a.astype(np.int64) + b).ravel(), minlength=100).reshape(10, 10)
        pixels += a.size
    conflict = pixels - counts.max(axis=1).sum()
    score = (shape_error, float(conflict / max(pixels, 1)))
    exact = shape_error == 0 and conflict == 0
    table = np.arange(10, dtype=np.uint8)
    seen = counts.sum(axis=1) > 0
    table[seen] = counts.argmax(axis=1)[seen]
    return score, exact, table, seen


def solve(task, seconds=1.8, max_depth=3, beam=96, state_cap=10000):
    start = time.monotonic()
    demos = task["train"]
    targets = [grid(p["output"]) for p in demos]
    arrays = tuple([grid(p["input"]) for p in demos] + [grid(p["input"]) for p in task["test"]])
    count = len(demos)
    if count < 1 or count == len(arrays):
        raise ValueError("empty demonstration or query")
    primitive_ops = operations()
    visited = {signature(arrays)}
    frontier = [((), arrays)]
    accepted = {}
    counters = collections.Counter()
    baseline = None
    stop_reason = "depth_complete"
    for depth in range(max_depth + 1):
        future = []
        for program, values in frontier:
            if time.monotonic() - start >= seconds or len(visited) >= state_cap:
                stop_reason = "time_cap" if time.monotonic() - start >= seconds else "state_cap"
                break
            priority, exact, table, seen = recoloring(values[:count], targets)
            counters["states_evaluated"] += 1
            if exact:
                query_values = values[count:]
                # No invented color mapping for previously unseen query symbols.
                if all(np.all(seen[np.unique(a)]) for a in query_values):
                    result = tuple(table[a] for a in query_values)
                    key = signature(result)
                    if key not in accepted:
                        accepted[key] = {"program": list(program), "mapping": table.tolist(),
                                         "grids": [a.tolist() for a in result], "depth": depth}
            if depth == max_depth:
                continue
            for name, op in primitive_ops:
                try:
                    transformed = tuple(grid(op(a)) for a in values)
                except (ValueError, IndexError):
                    counters["invalid_operations"] += 1
                    continue
                counters["operations_attempted"] += 1
                key = signature(transformed)
                if key in visited:
                    counters["equivalent_states"] += 1
                    continue
                visited.add(key)
                score = recoloring(transformed[:count], targets)[0]
                future.append((score, program + (name,), transformed))
        if depth == 1:
            baseline = list(accepted.values())[:2]
        if stop_reason != "depth_complete":
            break
        # Depth one enumerates every primitive: beam pruning starts at depth two.
        future.sort(key=lambda e: (e[0], e[1]))
        frontier = [(program, values) for _, program, values in (future if depth == 0 else future[:beam])]
        if not frontier:
            break
    if baseline is None:
        baseline = [v for v in accepted.values() if v["depth"] <= 1][:2]
    baseline_keys = {tuple((len(a), len(a[0]), tuple(map(tuple, a))) for a in v["grids"]) for v in baseline}
    extra = []
    for v in accepted.values():
        key = tuple((len(a), len(a[0]), tuple(map(tuple, a))) for a in v["grids"])
        if key not in baseline_keys:
            extra.append(v)
    expanded = (baseline + extra)[:2]
    return {"baseline": baseline, "expanded": expanded, "all_candidate_count": len(accepted),
            "counts": dict(counters), "visited": len(visited), "seconds": time.monotonic() - start,
            "stop_reason": stop_reason}
