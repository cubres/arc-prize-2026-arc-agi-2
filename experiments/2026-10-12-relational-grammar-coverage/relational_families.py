"""Original bounded interval-painting and repeated-component programs.

Public demonstrations determine program fit before query applicability is
examined. No task identifiers, query answers, external model, or stored task
program enters solve. Invented controls live separately in controls.py.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import collections
import itertools
import time

import numpy as np
from baseline37 import grid, signature
from object_selector import backgrounds, objects, geometry


class DiagnosticBudgetExceeded(RuntimeError):
    pass


class Inapplicable(ValueError):
    pass


def check_task(task):
    if set(task) != {"train", "test"} or not task["train"] or not task["test"]:
        raise ValueError("challenge-only train/test required")
    if any(set(p) != {"input", "output"} for p in task["train"]):
        raise ValueError("demonstration input/output required")
    if any(set(p) != {"input"} for p in task["test"]):
        raise ValueError("query inputs only required")


def interval_pairs(a, background, axis, anchors, gap_policy):
    """One eligible pair per line; colored obstacles are never overwritten."""
    value = a if axis == "row" else a.T
    pairs = []
    for line_index, line in enumerate(value):
        if anchors == "nonbackground_same":
            positions = np.flatnonzero(line != background)
            if len(positions) != 2 or line[positions[0]] != line[positions[1]]:
                continue
        elif anchors == "nonbackground_any":
            positions = np.flatnonzero(line != background)
            if len(positions) != 2:
                continue
        else:
            color = int(anchors)
            if color == background:
                continue
            positions = np.flatnonzero(line == color)
            if len(positions) != 2:
                continue
        start, end = map(int, positions)
        if end - start < 2:
            continue
        span = line[start + 1:end]
        blanks = np.flatnonzero(span == background) + start + 1
        if not len(blanks) or (gap_policy == "all_blank" and not np.all(span == background)):
            continue
        pairs.append((line_index, start, end, tuple(map(int, blanks)), int(line[start]), int(line[end])))
    return pairs


def paint_intervals(a, pairs, axis, scope, fill):
    if not pairs:
        raise Inapplicable("no_eligible_pair")
    if scope == "unique" and len(pairs) != 1:
        raise Inapplicable("multiple_eligible_pairs")
    out = a.copy()
    value = out if axis == "row" else out.T
    for line, start, end, blanks, left_color, right_color in pairs:
        color = left_color if fill == "left_anchor" else right_color if fill == "right_anchor" else int(fill)
        for column in blanks:
            value[line, column] = color
    return out


def component_key(part, a, kind):
    if kind == "shape":
        return part["shape"]
    if kind == "shape_colors":
        return part["shape"], part["colors"]
    r0, c0, _, _ = part["box"]
    return tuple(sorted((r - r0, c - c0, int(a[r, c])) for r, c in part["cells"]))


def repeated_group(a, parts, kind, member_rule):
    if not 2 <= len(parts) <= 80:
        raise Inapplicable("component_inventory_outside2to80")
    groups = collections.defaultdict(list)
    for part in parts:
        groups[component_key(part, a, kind)].append(part)
    eligible = [members for members in groups.values()
                if 2 <= len(members) <= 4 and (member_rule == "two_to_four" or len(members) == member_rule)]
    if len(eligible) != 1:
        raise Inapplicable("ambiguous_or_missing_repeated_class")
    return eligible[0]


def render_group(a, group, background, mode):
    cells = [cell for part in group for cell in part["cells"]]
    if mode == "erase":
        out = a.copy()
        for r, c in cells:
            out[r, c] = background
        return out
    out = np.full(a.shape, background, dtype=np.uint8)
    for r, c in cells:
        out[r, c] = a[r, c]
    if mode == "retain":
        return out
    rows, columns = zip(*cells)
    return out[min(rows):max(rows) + 1, min(columns):max(columns) + 1]


def solve(task, interval_seconds=0.8, group_seconds=0.4, candidate_cap=16):
    check_task(task)
    if not 0 < interval_seconds <= 2 or not 0 < group_seconds <= 2 or not 1 <= candidate_cap <= 16:
        raise ValueError("invalid registered bounds")
    demos = [grid(p["input"]) for p in task["train"]]
    targets = [grid(p["output"]) for p in task["train"]]
    queries = [grid(p["input"]) for p in task["test"]]
    if all(np.array_equal(a, b) for a, b in zip(demos, targets)):
        return {"families": {name: {"candidates": [], "counts": {"no_demo_behavior_change": 1},
                                   "query_reasons": {}, "stop_reason": "no_demo_change", "seconds_cpu": 0.0}
                             for name in ("interval_paint", "repeated_group")}, "candidates": []}
    demo_bgs = [backgrounds(a) for a in demos]
    query_bgs = [backgrounds(a) for a in queries]
    families = {}
    for family, seconds in (("interval_paint", interval_seconds), ("repeated_group", group_seconds)):
        started = time.process_time()
        counts = collections.Counter()
        reasons = collections.Counter()
        fit_cache = {}
        accepted = {}
        seen_predictions = set()
        stop = "complete"

        def budget():
            if time.process_time() - started >= seconds:
                raise DiagnosticBudgetExceeded(family + " CPU cap")

        def fit(values):
            state = signature(values)
            if state not in fit_cache:
                counts["unique_demo_states"] += 1
                if any(a.shape != b.shape for a, b in zip(values, targets)):
                    counts["unique_demo_shape_reject"] += 1
                    fit_cache[state] = (False, None, None)
                elif all(np.array_equal(a, b) for a, b in zip(values, demos)):
                    counts["unique_demo_noop_reject"] += 1
                    fit_cache[state] = (False, None, None)
                else:
                    # New operators preserve every selected/untouched color.
                    # Only the explicit interval fill may introduce a color.
                    # The frozen baseline's recoloring remains independent.
                    exact = all(np.array_equal(a, b) for a, b in zip(values, targets))
                    table = np.arange(10, dtype=np.uint8)
                    supported = None
                    fit_cache[state] = (exact, table, supported)
                    counts["unique_demo_exact_fit" if exact else "unique_demo_value_reject"] += 1
            return fit_cache[state]

        def accept(program, demo_values, query_function):
            nonlocal stop
            budget()
            counts["demo_applicable_programs"] += 1
            exact, table, supported = fit(demo_values)
            if not exact:
                return
            # Crucially, this counter precedes all query rendering/selection.
            counts["demo_fitting_programs"] += 1
            try:
                query_values = query_function()
            except Inapplicable as error:
                counts["query_inapplicable_programs"] += 1
                reasons[str(error)] += 1
                return
            budget()
            counts["query_supported_programs"] += 1
            predictions = tuple(table[a] for a in query_values)
            key = signature(predictions)
            if key not in seen_predictions:
                seen_predictions.add(key)
                counts["distinct_joint_predictions"] += 1
                if len(accepted) < candidate_cap:
                    accepted[key] = {"family": family, "program": program,
                                     "mapping": table.tolist(), "grids": [a.tolist() for a in predictions]}
                else:
                    counts["prediction_storage_truncated"] += 1

        if family == "interval_paint":
            anchors_values = ["nonbackground_same", "nonbackground_any"] + list(range(10))
            fills = ["left_anchor", "right_anchor"] + list(range(10))
            pair_cache = {}

            def pairs_for(a, background, axis, anchors, gap_policy):
                key = (signature((a,)), background, axis, anchors, gap_policy)
                if key not in pair_cache:
                    pair_cache[key] = interval_pairs(a, background, axis, anchors, gap_policy)
                return pair_cache[key]

            for bg_kind, axis, anchors, gap_policy, scope, fill in itertools.product(
                    range(3), ("row", "column"), anchors_values,
                    ("all_blank", "blank_only"), ("unique", "all"), fills):
                budget()
                counts["programs_attempted"] += 1
                try:
                    rendered = tuple(paint_intervals(a, pairs_for(a, bgs[bg_kind], axis, anchors, gap_policy), axis, scope, fill)
                                     for a, bgs in zip(demos, demo_bgs))
                except Inapplicable:
                    counts["demo_inapplicable_programs"] += 1
                    continue
                program = {"background_kind": bg_kind, "axis": axis, "anchors": anchors,
                           "gap_policy": gap_policy, "scope": scope, "fill": fill}

                def render_queries():
                    return tuple(paint_intervals(a, pairs_for(a, bgs[bg_kind], axis, anchors, gap_policy), axis, scope, fill)
                                 for a, bgs in zip(queries, query_bgs))

                accept(program, rendered, render_queries)
                if stop != "complete":
                    break
        else:
            part_cache = {}

            def parts_for(a, background, diagonal, monochrome):
                key = (signature((a,)), background, diagonal, monochrome)
                if key not in part_cache:
                    part_cache[key] = objects(a, background, diagonal, monochrome)
                return part_cache[key]

            for bg_kind, diagonal, monochrome, kind, member_rule, mode, transform in itertools.product(
                    range(3), (False, True), (False, True), ("shape", "shape_colors", "color_layout"),
                    ("two_to_four", 2, 3, 4), ("isolate_crop", "retain", "erase"), range(8)):
                budget()
                counts["programs_attempted"] += 1
                try:
                    rendered = tuple(geometry(render_group(a, repeated_group(a, parts_for(a, bgs[bg_kind], diagonal, monochrome), kind, member_rule), bgs[bg_kind], mode), transform)
                                     for a, bgs in zip(demos, demo_bgs))
                except Inapplicable:
                    counts["demo_inapplicable_programs"] += 1
                    continue
                program = {"background_kind": bg_kind, "diagonal": diagonal,
                           "monochrome": monochrome, "class_kind": kind,
                           "members": member_rule, "render": mode, "transform": transform}

                def render_queries():
                    return tuple(geometry(render_group(a, repeated_group(a, parts_for(a, bgs[bg_kind], diagonal, monochrome), kind, member_rule), bgs[bg_kind], mode), transform)
                                 for a, bgs in zip(queries, query_bgs))

                accept(program, rendered, render_queries)
                if stop != "complete":
                    break
        budget()
        if counts["unique_demo_states"] != sum(counts[key] for key in (
                "unique_demo_shape_reject", "unique_demo_noop_reject", "unique_demo_value_reject", "unique_demo_exact_fit")):
            raise RuntimeError("demonstration state partition failed")
        if counts["demo_fitting_programs"] != counts["query_inapplicable_programs"] + counts["query_supported_programs"]:
            raise RuntimeError("fit-before-query accounting failed")
        families[family] = {"candidates": list(accepted.values()), "counts": dict(counts),
                            "query_reasons": dict(reasons), "stop_reason": stop,
                            "candidate_storage_truncated": len(seen_predictions) > candidate_cap,
                            "seconds_cpu": time.process_time() - started}
    # Every baseline guess is protected by the driver before supplementation.
    return {"families": families,
            "candidates": [candidate for name in ("interval_paint", "repeated_group")
                           for candidate in families[name]["candidates"]]}
