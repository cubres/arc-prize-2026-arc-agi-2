"""Original bounded cavity recoloring induced only from demonstration pairs.

Conceptual inspiration: Michael Hodel's ARC-DSL README (MIT), pinned commit
635de4902a5fb4e376f27333feaa396d3f5dfdcb. No DSL or solved task code is imported.
This independent implementation enumerates a shared adjacency/source/ink
program, requires exact demonstration fit and non-vacuous changed support,
and preserves every other cell. No task identity or I/O enters this module.
"""
from __future__ import annotations

import time
from collections import deque


def checked_grid(value):
    if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 30:
        raise ValueError("rows must be 1..30")
    rows = []
    width = None
    for row in value:
        if not isinstance(row, (list, tuple)) or not 1 <= len(row) <= 30:
            raise ValueError("columns must be 1..30")
        if width is None:
            width = len(row)
        if len(row) != width or any(type(c) is not int or not 0 <= c <= 9 for c in row):
            raise ValueError("invalid ARC grid")
        rows.append(tuple(row))
    return tuple(rows)


def cavity_mask(source, color, adjacency, deadline=None):
    """Find complete monochrome components which touch no grid border."""
    if adjacency not in (4, 8) or type(color) is not int or not 0 <= color <= 9:
        raise ValueError("invalid component parameters")
    h, w = len(source), len(source[0])
    neighbors = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if adjacency == 8:
        neighbors += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen, enclosed = set(), set()
    steps = 0
    for r in range(h):
        for c in range(w):
            if source[r][c] != color or (r, c) in seen:
                continue
            todo, component = deque([(r, c)]), []
            seen.add((r, c))
            borders = False
            while todo:
                rr, cc = todo.popleft()
                component.append((rr, cc))
                borders |= rr in (0, h - 1) or cc in (0, w - 1)
                for dr, dc in neighbors:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and source[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
                steps += 1
                if deadline is not None and steps % 64 == 0 and time.process_time() >= deadline:
                    raise TimeoutError("cavity CPU cap")
            if not borders:
                enclosed.update(component)
    return frozenset(enclosed)


def render(source, mask, ink):
    return tuple(tuple(ink if (r, c) in mask else value for c, value in enumerate(row))
                 for r, row in enumerate(source))


def solve(task, cpu_seconds=0.20):
    started_cpu, started_wall = time.process_time(), time.monotonic()
    if not isinstance(task, dict) or set(task) != {"train", "test"}:
        raise ValueError("solver accepts fitting pairs and query inputs only")
    if not 1 <= len(task["train"]) <= 20 or len(task["test"]) != 1:
        raise ValueError("bounded study requires 1..20 fitting pairs and one query")
    if any(set(p) != {"input", "output"} for p in task["train"]) or any(set(p) != {"input"} for p in task["test"]):
        raise ValueError("unexpected task fields")
    inputs = [checked_grid(p["input"]) for p in task["train"]]
    outputs = [checked_grid(p["output"]) for p in task["train"]]
    queries = [checked_grid(p["input"]) for p in task["test"]]
    counters = {"programs_enumerated": 0, "exact_nonvacuous_programs": 0, "distinct_predictions": 0}
    if any((len(a), len(a[0])) != (len(b), len(b[0])) for a, b in zip(inputs, outputs)):
        return {"candidates": [], "stop_reason": "shape_change_abstain", "counts": counters,
                "cpu_seconds": time.process_time() - started_cpu, "seconds": time.monotonic() - started_wall}
    source_colors = sorted({c for a in inputs for row in a for c in row})
    ink_colors = sorted({c for a in outputs for row in a for c in row})
    deadline = started_cpu + cpu_seconds
    candidates, seen_predictions = [], set()
    stop = "grammar_complete"
    try:
        for adjacency in (4, 8):
            for color in source_colors:
                if time.process_time() >= deadline:
                    raise TimeoutError("cavity CPU cap")
                masks = [cavity_mask(a, color, adjacency, deadline) for a in inputs]
                query_masks = None
                for ink in ink_colors:
                    if color == ink:
                        continue
                    if time.process_time() >= deadline:
                        raise TimeoutError("cavity CPU cap")
                    counters["programs_enumerated"] += 1
                    if counters["programs_enumerated"] > 180:
                        raise RuntimeError("frozen 180-program bound exceeded")
                    if not any(masks) or any(render(a, m, ink) != b for a, m, b in zip(inputs, masks, outputs)):
                        continue
                    counters["exact_nonvacuous_programs"] += 1
                    if query_masks is None:
                        query_masks = [cavity_mask(a, color, adjacency, deadline) for a in queries]
                    predictions = tuple(render(a, m, ink) for a, m in zip(queries, query_masks))
                    if predictions in seen_predictions:
                        continue
                    seen_predictions.add(predictions)
                    candidates.append({"program": [adjacency, color, ink],
                                       "grids": [[list(row) for row in a] for a in predictions]})
        counters["distinct_predictions"] = len(candidates)
    except TimeoutError:
        # Partial enumeration may change lexical selection. Abstain on the
        # entire family rather than retaining a deadline-dependent prefix.
        candidates = []
        stop = "cpu_cap_abstain"
    return {"candidates": candidates, "stop_reason": stop, "counts": counters,
            "cpu_seconds": time.process_time() - started_cpu, "seconds": time.monotonic() - started_wall}


def augment(parent, cavity):
    """Preserve every original guess, then fill vacant slots by joint grid."""
    if len(parent) > 2:
        raise ValueError("parent top-two contract exceeded")
    chosen = list(parent)
    keys = {tuple(checked_grid(a) for a in p["grids"]) for p in parent}
    for candidate in cavity:
        key = tuple(checked_grid(a) for a in candidate["grids"])
        if key not in keys and len(chosen) < 2:
            chosen.append(candidate)
            keys.add(key)
    return chosen
