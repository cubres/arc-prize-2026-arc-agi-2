"""Invented handwritten expectations for the new structural families.

No benchmark grid, task ID or query answer is stored here.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations


def canvas(height, width, cells):
    value = [[0] * width for _ in range(height)]
    for row, column, color in cells:
        value[row][column] = color
    return value


def need(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def run(m):
    interval_a = canvas(3, 7, [(1, 1, 2), (1, 5, 2)])
    interval_b = canvas(4, 8, [(2, 2, 3), (2, 6, 3)])
    target_a = canvas(3, 7, [(1, c, 2) for c in range(1, 6)])
    target_b = canvas(4, 8, [(2, c, 3) for c in range(2, 7)])
    query = canvas(4, 6, [(1, 0, 4), (1, 4, 4)])
    expected_query = canvas(4, 6, [(1, c, 4) for c in range(5)])
    horizontal = {"train": [{"input": interval_a, "output": target_a},
                            {"input": interval_b, "output": target_b}],
                  "test": [{"input": query}]}
    transpose = lambda a: [list(row) for row in zip(*a)]
    vertical = {"train": [{"input": transpose(p["input"]), "output": transpose(p["output"])}
                          for p in horizontal["train"]], "test": [{"input": transpose(query)}]}
    conflicting = {"train": [horizontal["train"][0],
                             {"input": interval_a, "output": canvas(3, 7, [(1, 1, 2), (1, 2, 2), (1, 5, 2)])}],
                   "test": horizontal["test"]}
    empty = {"train": horizontal["train"], "test": [{"input": canvas(4, 6, [])}]}
    adjacent = {"train": horizontal["train"], "test": [{"input": canvas(4, 6, [(1, 1, 4), (1, 2, 4)])}]}
    obstacles_input = canvas(5, 4, [(0, 1, 3), (4, 1, 3), (2, 1, 7)])
    obstacles_target = canvas(5, 4, [(r, 1, 7 if r == 2 else 3) for r in range(5)])
    obstacle_task = {"train": [{"input": obstacles_input, "output": obstacles_target}],
                     "test": [{"input": obstacles_input}]}
    overwrite_task = {"train": [{"input": obstacles_input,
                                  "output": canvas(5, 4, [(r, 1, 3) for r in range(5)])}],
                      "test": [{"input": obstacles_input}]}
    query_pairs = canvas(5, 7, [(1, 1, 4), (1, 5, 4), (3, 0, 4), (3, 4, 4)])
    query_pairs_expected = canvas(5, 7, [(1, c, 4) for c in range(1, 6)] + [(3, c, 4) for c in range(5)])
    multiple_pairs = {"train": horizontal["train"], "test": [{"input": query_pairs}]}
    group_a = canvas(5, 8, [(1, 1, 1), (2, 1, 1), (1, 5, 1), (2, 5, 1), (0, 7, 2)])
    group_b = canvas(6, 9, [(2, 2, 3), (3, 2, 3), (2, 6, 3), (3, 6, 3), (2, 4, 4)])
    group_query = canvas(4, 7, [(1, 0, 5), (2, 0, 5), (1, 4, 5), (2, 4, 5), (0, 6, 6)])
    grouped = {"train": [{"input": group_a, "output": [[1, 0, 0, 0, 1], [1, 0, 0, 0, 1]]},
                          {"input": group_b, "output": [[3, 0, 0, 0, 3], [3, 0, 0, 0, 3]]}],
               "test": [{"input": group_query}]}
    ambiguous_group_query = canvas(9, 10, [(1, 1, 5), (2, 1, 5), (1, 5, 5), (2, 5, 5),
                                         (6, 1, 6), (6, 2, 6), (6, 6, 6), (6, 7, 6)])
    ambiguous = {"train": grouped["train"], "test": [{"input": ambiguous_group_query}]}
    joint_bad = {"train": grouped["train"], "test": [{"input": group_query}, {"input": ambiguous_group_query}]}
    omitted = {"train": [{"input": group_a, "output": [[1, 0, 0, 0, 0], [1, 0, 0, 0, 0]]}],
               "test": grouped["test"]}
    five = canvas(5, 12, [(r, c, 5) for c in (1, 3, 5, 7, 9) for r in (1, 2)])
    five_only = {"train": grouped["train"], "test": [{"input": five}]}
    summaries = {}

    def tested(name, task, family, expectation=None, reject=False, demo_fit=True):
        result = m.solve(task, interval_seconds=2.0, group_seconds=2.0, candidate_cap=16)
        arm = result["families"][family]
        need(arm["stop_reason"] == "complete", name + " did not complete finite search")
        if demo_fit:
            need(arm["counts"].get("demo_fitting_programs", 0) > 0, name + " lacks demonstration activation")
        else:
            need(not arm["counts"].get("demo_fitting_programs", 0), name + " unexpectedly fits demonstrations")
        if reject:
            need(not arm["candidates"], name + " unexpectedly predicts")
        if expectation is not None:
            need(any(c["grids"] == [expectation] for c in arm["candidates"]), name + " handwritten expected prediction absent")
        summaries[name] = {"family": family, "counts": arm["counts"],
                           "query_reasons": arm["query_reasons"],
                           "candidates": len(arm["candidates"]), "stop": arm["stop_reason"]}
        return arm

    tested("horizontal_interval", horizontal, "interval_paint", expected_query)
    tested("vertical_interval", vertical, "interval_paint", transpose(expected_query))
    tested("preserve_intervening_obstacle", obstacle_task, "interval_paint", obstacles_target)
    tested("reject_obstacle_overwrite", overwrite_task, "interval_paint", reject=True, demo_fit=False)
    tested("reject_conflicting_demonstrations", conflicting, "interval_paint", reject=True, demo_fit=False)
    tested("fit_before_empty_query", empty, "interval_paint", reject=True)
    tested("fit_before_adjacent_query", adjacent, "interval_paint", reject=True)
    all_arm = tested("explicit_all_intervals", multiple_pairs, "interval_paint", query_pairs_expected)
    need(all(c["program"]["scope"] == "all" for c in all_arm["candidates"]), "unique-pair program survived ambiguity")
    need(all_arm["query_reasons"].get("multiple_eligible_pairs", 0) > 0, "query ambiguity counter absent")
    tested("isolated_repeated_union_crop", grouped, "repeated_group", [[5, 0, 0, 0, 5], [5, 0, 0, 0, 5]])
    tested("fit_before_ambiguous_group_query", ambiguous, "repeated_group", reject=True)
    tested("reject_partial_joint_prediction", joint_bad, "repeated_group", reject=True)
    tested("reject_same_color_member_omission", omitted, "repeated_group", reject=True, demo_fit=False)
    tested("reject_five_member_query_class", five_only, "repeated_group", reject=True)
    # Direct semantic assertions complement full-grammar controls.
    a = m.grid(obstacles_input)
    need(not m.interval_pairs(a, 0, "column", 3, "all_blank"), "all-blank gap accepted an obstacle")
    parts = m.objects(m.grid(five), 0, False, False)
    try:
        m.repeated_group(m.grid(five), parts, "shape", "two_to_four")
    except m.Inapplicable:
        pass
    else:
        raise RuntimeError("five-member class was truncated")
    identity_task = {"train": [{"input": interval_a, "output": interval_a}], "test": horizontal["test"]}
    need(not m.solve(identity_task)["candidates"], "uninformative identity demonstrations admitted")
    divergent = {"train": grouped["train"],
                 "test": [{"input": canvas(7, 8, [(1, 1, 5), (2, 1, 5), (4, 5, 6), (5, 5, 6), (0, 7, 7)])}]}
    full = m.solve(divergent, interval_seconds=2.0, group_seconds=2.0, candidate_cap=16)["families"]["repeated_group"]
    small = m.solve(divergent, interval_seconds=2.0, group_seconds=2.0, candidate_cap=1)["families"]["repeated_group"]
    need(full["stop_reason"] == small["stop_reason"] == "complete", "storage test stopped enumeration")
    need(full["counts"].get("distinct_joint_predictions", 0) > 1, "storage test lacks divergent predictions")
    need(small["candidate_storage_truncated"] and len(small["candidates"]) == 1, "storage bound not exercised")
    need(full["counts"]["distinct_joint_predictions"] == small["counts"]["distinct_joint_predictions"], "storage cap lost distinct-prediction accounting")
    need(full["counts"]["demo_fitting_programs"] == small["counts"]["demo_fitting_programs"], "query storage cap changed demonstration-fit accounting")
    return {"status": "INVENTED_CONTROLS_PASS", "controls": summaries,
            "direct_semantics_pass": True, "prediction_storage_independence_pass": True,
            "benchmark_run": False, "quality_claim": False}
