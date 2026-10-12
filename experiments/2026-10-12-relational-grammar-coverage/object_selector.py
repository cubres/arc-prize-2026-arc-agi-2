"""Original exact-demonstration connected-object programs, no stored task data.

The idea of object-selection symbolic supplementation is credited to the
Apache-2.0 BlackCat V2 Kaggle notebook. This implementation is independently
written and imports only NumPy and the owned baseline's grid/recolor helpers.
"""
from __future__ import annotations

import collections
import time
import numpy as np
from baseline37 import grid, recoloring, query_colors_supported, signature


def backgrounds(a):
    border = np.concatenate((a[0], a[-1], a[:, 0], a[:, -1]))
    return [0, int(np.bincount(a.ravel(), minlength=10).argmax()),
            int(np.bincount(border, minlength=10).argmax())]


def objects(a, background, diagonal, monochrome):
    """Connected foreground components with explicit 4/8 connectivity."""
    foreground = a != background
    done = np.zeros(a.shape, dtype=bool)
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    if diagonal:
        directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    result = []
    for rr, cc in zip(*np.nonzero(foreground)):
        if done[rr, cc]:
            continue
        stack = [(int(rr), int(cc))]
        done[rr, cc] = True
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in directions:
                r2, c2 = r + dr, c + dc
                if (0 <= r2 < a.shape[0] and 0 <= c2 < a.shape[1]
                        and foreground[r2, c2] and not done[r2, c2]
                        and (not monochrome or a[r2, c2] == a[r, c])):
                    done[r2, c2] = True
                    stack.append((r2, c2))
        rows, cols = zip(*cells)
        r0, c0, r1, c1 = min(rows), min(cols), max(rows) + 1, max(cols) + 1
        colors = tuple(sorted({int(a[r, c]) for r, c in cells}))
        shape = tuple(sorted((r - r0, c - c0) for r, c in cells))
        result.append({"cells": cells, "box": (r0, c0, r1, c1),
                       "area": len(cells), "width": c1 - c0, "height": r1 - r0,
                       "box_area": (r1 - r0) * (c1 - c0), "colors": colors,
                       "shape": shape, "color_count": len(colors)})
    return result


SELECTORS = [("area", -1), ("area", 1), ("box_area", -1), ("box_area", 1),
             ("width", -1), ("height", -1), ("color_count", -1),
             ("unique_shape", 0), ("unique_colors", 0),
             ("top", 1), ("left", 1), ("bottom", -1), ("right", -1)]


def select(parts, rule):
    if not 1 <= len(parts) <= 80:
        raise ValueError("requires a bounded nonempty object inventory")
    key, direction = rule
    if key.startswith("unique_"):
        field = "shape" if key == "unique_shape" else "colors"
        counts = collections.Counter(p[field] for p in parts)
        chosen = [p for p in parts if counts[p[field]] == 1]
    else:
        if key in ("top", "left", "bottom", "right"):
            ix = ("top", "left", "bottom", "right").index(key)
            scores = [p["box"][ix] for p in parts]
        else:
            scores = [p[key] for p in parts]
        extreme = min(scores) if direction == 1 else max(scores)
        chosen = [p for p, score in zip(parts, scores) if score == extreme]
    if len(chosen) != 1:
        raise ValueError("ambiguous object selector")
    return chosen[0]


def render(a, part, background, mode):
    r0, c0, r1, c1 = part["box"]
    if mode == "crop":
        return a[r0:r1, c0:c1].copy()
    masked = np.full(a.shape, background, dtype=np.uint8)
    for r, c in part["cells"]:
        masked[r, c] = a[r, c]
    if mode == "isolate_crop":
        return masked[r0:r1, c0:c1]
    if mode == "retain":
        return masked
    value = a.copy()
    for r, c in part["cells"]:
        value[r, c] = background
    return value


def geometry(a, transform):
    value = np.rot90(a, transform % 4)
    return np.fliplr(value) if transform >= 4 else value


def solve(task, seconds=0.4, candidate_cap=32):
    if set(task) != {"train", "test"} or not task["train"] or not task["test"]:
        raise ValueError("challenge-only train/test contract required")
    if any(set(p) != {"input", "output"} for p in task["train"]):
        raise ValueError("invalid demonstration keys")
    if any(set(p) != {"input"} for p in task["test"]):
        raise ValueError("query answers and identities are forbidden")
    if not 0 < seconds <= 2 or not 1 <= candidate_cap <= 32:
        raise ValueError("invalid bounds")
    started = time.process_time()
    demos = task["train"]
    arrays = [grid(p["input"]) for p in demos] + [grid(p["input"]) for p in task["test"]]
    targets = [grid(p["output"]) for p in demos]
    count = len(demos)
    bg_values = [backgrounds(a) for a in arrays]
    seen_states, accepted = set(), {}
    counts = collections.Counter()
    stop = "complete"
    # Fixed finite grammar; runtime never loads task-specific programs.
    for bg_kind in range(3):
        for diagonal in (False, True):
            for monochrome in (False, True):
                if time.process_time() - started >= seconds:
                    stop = "cpu_cap"
                    break
                parts = [objects(a, bg[bg_kind], diagonal, monochrome)
                         for a, bg in zip(arrays, bg_values)]
                if not any(len(p) >= 2 for p in parts[:count]):
                    counts["no_multi_object_demo"] += 1
                    continue
                for selector in SELECTORS:
                    if time.process_time() - started >= seconds:
                        stop = "cpu_cap"
                        break
                    try:
                        selected = [select(p, selector) for p in parts]
                    except ValueError:
                        counts["ambiguous_or_inapplicable"] += 1
                        continue
                    for mode in ("crop", "isolate_crop", "retain", "erase"):
                        rendered = [render(a, p, bg[bg_kind], mode)
                                    for a, p, bg in zip(arrays, selected, bg_values)]
                        for transform in range(8):
                            if time.process_time() - started >= seconds:
                                stop = "cpu_cap"
                                break
                            values = tuple(geometry(a, transform) for a in rendered)
                            state = signature(values)
                            if state in seen_states:
                                continue
                            seen_states.add(state)
                            counts["unique_program_outputs"] += 1
                            if any(a.shape != b.shape for a, b in zip(values[:count], targets)):
                                continue
                            _, exact, table, supported = recoloring(values[:count], targets)
                            if not exact:
                                continue
                            counts["exact_demonstration_fits"] += 1
                            if not query_colors_supported(table, supported, values[count:]):
                                counts["unsupported_query_color"] += 1
                                continue
                            predictions = tuple(table[a] for a in values[count:])
                            output_key = signature(predictions)
                            if output_key not in accepted:
                                accepted[output_key] = {"program": {
                                    "background": bg_kind, "diagonal": diagonal,
                                    "monochrome": monochrome, "selector": list(selector),
                                    "render": mode, "transform": transform},
                                    "mapping": table.tolist(), "grids": [a.tolist() for a in predictions]}
                            if len(accepted) >= candidate_cap:
                                stop = "candidate_cap"
                                break
                        if stop != "complete":
                            break
                    if stop != "complete":
                        break
                if stop != "complete":
                    break
            if stop != "complete":
                break
        if stop != "complete":
            break
    return {"candidates": list(accepted.values()), "counts": dict(counts),
            "seconds_cpu": time.process_time() - started, "stop_reason": stop}


def fill_only(baseline, supplement):
    """Preserve the first two distinct supplied joint guesses; fill spare slots."""
    result, seen = [], set()
    cardinality = None
    for candidate in list(baseline) + list(supplement):
        if not candidate["grids"]:
            raise ValueError("empty joint candidate")
        if cardinality is None:
            cardinality = len(candidate["grids"])
        if len(candidate["grids"]) != cardinality:
            raise ValueError("joint candidate query cardinalities differ")
        key = signature(tuple(grid(a) for a in candidate["grids"]))
        if key not in seen:
            result.append(candidate)
            seen.add(key)
        if len(result) == 2:
            break
    return result
