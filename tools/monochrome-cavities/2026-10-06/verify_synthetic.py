"""Synthetic contracts only, using an independent border-flood oracle."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

import monochrome_cavities as api
import reference_cavity_programs as reference
from render_connectivity import render_svg

checks = 0


def require(condition, message):
    global checks
    if not condition:
        raise RuntimeError(message)
    checks += 1


def refuses(call, error=ValueError):
    try:
        call()
    except error:
        require(True, "expected refusal")
    else:
        raise RuntimeError("expected " + error.__name__ + " refusal")


def boundary_oracle(source, color, adjacency):
    """Dual formulation: complement of color cells reachable from a border."""
    h, w = len(source), len(source[0])
    seen = {(r, c) for r in range(h) for c in range(w)
            if source[r][c] == color and (r in (0, h - 1) or c in (0, w - 1))}
    offsets = [v for v in itertools.product((-1, 0, 1), repeat=2)
               if v != (0, 0) and (adjacency == 8 or sum(map(abs, v)) == 1)]
    while True:
        reached = set(seen)
        for r, c in seen:
            for dr, dc in offsets:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and source[rr][cc] == color:
                    reached.add((rr, cc))
        if reached == seen:
            return frozenset((r, c) for r in range(h) for c in range(w)
                             if source[r][c] == color and (r, c) not in seen)
        seen = reached


def main():
    if sys.flags.optimize:
        raise RuntimeError("optimized-mode verifier is intentionally refused")
    began = time.process_time()
    for bits in itertools.product((0, 1), repeat=9):
        source = tuple(tuple(bits[3 * r:3 * r + 3]) for r in range(3))
        for adjacency in (4, 8):
            for color in (0, 1):
                expected = boundary_oracle(source, color, adjacency)
                require(api.enclosed_cells(source, color, adjacency, cpu_seconds=1) == expected, "dual component oracle")
                expected_grid = tuple(tuple(4 if (r, c) in expected else value for c, value in enumerate(row))
                                      for r, row in enumerate(source))
                require(api.recolor_enclosed(source, color, 4, adjacency, cpu_seconds=1) == expected_grid, "dual recoloring oracle")
    ring = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
    colored = [[1, 1, 1], [1, 4, 1], [1, 1, 1]]
    diagonal = [[0, 1, 1], [1, 0, 1], [1, 1, 1]]
    require(api.enclosed_cells(diagonal, 0, 4) == frozenset({(1, 1)}), "cardinal enclosure")
    require(not api.enclosed_cells(diagonal, 0, 8), "diagonal border reachability")
    cases = [
        {"train": [{"input": ring, "output": colored}], "test": [{"input": diagonal}]},
        {"train": [{"input": ring, "output": ring}], "test": [{"input": ring}]},
        {"train": [{"input": ring, "output": [[4]]}], "test": [{"input": diagonal}]},
        {"train": [{"input": ring, "output": colored}, {"input": ring, "output": [[1, 1, 1], [1, 2, 1], [1, 1, 1]]}], "test": [{"input": diagonal}]},
    ]
    for task in cases:
        before = copy.deepcopy(task)
        direct = reference.solve(task, cpu_seconds=1)
        public = api.fit_predict(task, cpu_seconds=1)
        for key in ("candidates", "counts", "stop_reason"):
            require(public[key] == direct[key], "frozen valid-fit semantics: " + key)
        require(task == before, "caller-owned fit input changed")
    fits = api.fit_predict(cases[0], cpu_seconds=1)
    require(len(fits["candidates"]) == 2, "two diagonal hypotheses must remain distinct")
    require([c["program"] for c in fits["candidates"]] == [[4, 0, 4], [8, 0, 4]], "frozen lexical ranking")
    unknown = {"train": [{"input": ring, "output": colored}], "test": [{"input": [[1, 1, 1], [1, 9, 1], [1, 1, 1]]}]}
    unknown_candidates = api.fit_predict(unknown)["candidates"]
    require(bool(unknown_candidates), "unknown-query-color test needs an actual fitted candidate")
    require(all(c["program"][1] == 0 and c["grids"][0][1][1] == 9 for c in unknown_candidates), "query colors expanded grammar")
    all_colors = [list(range(10)), list(range(10))]
    bound_case = {"train": [{"input": all_colors, "output": all_colors}], "test": [{"input": all_colors}]}
    result = api.fit_predict(bound_case, cpu_seconds=1)
    require(result["counts"]["programs_enumerated"] == 180 and not result["candidates"], "maximum grammar/non-vacuity")
    for grid in ([], [[True]], [[1.0]], [[10]], [[-1]], [[0], [0, 1]], [[0] * 31]):
        refuses(lambda grid=grid: api.checked_grid(grid))
    for color in (True, 0.0, -1, 10, None):
        refuses(lambda color=color: api.enclosed_cells(ring, color))
        refuses(lambda color=color: api.recolor_enclosed(ring, 0, color))
    for adjacency in (True, 4.0, 0, 6, None):
        refuses(lambda adjacency=adjacency: api.enclosed_cells(ring, 0, adjacency))
    for budget in (True, 0, -1, float("nan"), float("inf"), "1", None):
        refuses(lambda budget=budget: api.enclosed_cells(ring, 0, cpu_seconds=budget))
        refuses(lambda budget=budget: api.recolor_enclosed(ring, 0, 4, cpu_seconds=budget))
        refuses(lambda budget=budget: api.fit_predict(cases[0], cpu_seconds=budget))
    refuses(lambda: api.fit_predict({**cases[0], "task_id": "synthetic"}))
    refuses(lambda: api.fit_predict({"train": cases[0]["train"], "test": [{"input": ring, "output": colored}]}))
    refuses(lambda: api.fit_predict({"train": [], "test": [{"input": ring}]}))
    refuses(lambda: api.fit_predict({"train": cases[0]["train"] * 21, "test": [{"input": ring}]}))
    # Controlled synthetic clock injection checks each wrapper's finalization
    # boundary. It is a guard contract, not a measured real CPU speed test.
    original_clock = api._clock
    for name in ("enclosed_cells", "recolor_enclosed", "fit_predict"):
        now = time.process_time()
        sequence = iter([now, now + 1e-6, now + 0.3] if name == "fit_predict" else [now, now + 0.3])
        api._clock = lambda: next(sequence)
        try:
            if name == "fit_predict":
                refuses(lambda: api.fit_predict(cases[0]), TimeoutError)
            elif name == "recolor_enclosed":
                refuses(lambda: api.recolor_enclosed(ring, 0, 4), TimeoutError)
            else:
                refuses(lambda: api.enclosed_cells(ring, 0), TimeoutError)
        finally:
            api._clock = original_clock
    parent = [{"grids": [ring], "metadata": {"notes": ["owned"]}}]
    candidate = {"grids": [colored], "program": [4, 0, 4]}
    before_parent, before_candidate = copy.deepcopy(parent), copy.deepcopy(candidate)
    added = api.fill_vacancies(parent, [{"grids": [ring]}, candidate])
    require(added == [parent[0], candidate], "prefix/vacancy/grid dedup")
    added[0]["metadata"]["notes"].append("output mutation")
    added[1]["grids"][0][1][1] = 8
    require(parent == before_parent and candidate == before_candidate, "output aliases caller-owned candidates")
    require(api.fill_vacancies([parent[0], candidate], fits["candidates"]) == [parent[0], candidate], "occupied guesses replaced")
    refuses(lambda: api.fill_vacancies(parent * 3, []))
    refuses(lambda: api.fill_vacancies([], [{"grids": [ring], "bad": float("nan")}]))
    refuses(lambda: api.fill_vacancies([], [{"grids": [[[True]]]}]))
    svg = render_svg()
    require(svg == render_svg(), "nondeterministic vector renderer")
    root = ET.fromstring(svg)
    require(root.tag == "{http://www.w3.org/2000/svg}svg" and "Synthetic connectivity demonstration" in svg, "SVG concept provenance")
    module = Path(__file__).with_name("monochrome_cavities.py")
    pinned = Path(__file__).with_name("reference_cavity_programs.py")
    require(hashlib.sha256(pinned.read_bytes()).hexdigest() == "a38fcff0f83d1f1fee9d91fdf12701f8bf53bf03fdf14e8e7c9f063b091e8d4f", "frozen reference drift")
    print(json.dumps({"status": "PASS_SYNTHETIC_CONTRACTS_ONLY", "checks": checks,
                      "exhaustive_component_oracles": 2048, "exhaustive_recolor_oracles": 2048,
                      "frozen_fit_compatibility_cases": len(cases), "forced_finalization_deadline_cases": 3,
                      "source_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
                      "reference_sha256": hashlib.sha256(pinned.read_bytes()).hexdigest(),
                      "vector_sha256": hashlib.sha256(svg.encode()).hexdigest(),
                      "python": sys.version.split()[0], "process_cpu_seconds": time.process_time() - began,
                      "dataset_model_target_or_submission_files_read": False}, sort_keys=True))


if __name__ == "__main__":
    main()
