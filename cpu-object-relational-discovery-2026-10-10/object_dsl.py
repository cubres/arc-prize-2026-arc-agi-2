"""Original finite object/relational ARC grammar. MIT, cubres 2026.

The runtime consumes demonstrations and test grids only. It never reads files,
task identifiers, solutions, prior predictions or benchmark metadata.
"""
from collections import Counter
from dataclasses import dataclass
import time

SELECTORS = ("largest_area", "smallest_area", "largest_box", "smallest_box",
             "widest", "narrowest", "tallest", "shortest", "topmost",
             "bottommost", "leftmost", "rightmost", "unique_shape",
             "unique_color", "outer_container", "inner_contained")
TRANSLATIONS = ("align_top_left", "align_center", "above_left", "below_left",
                "left_top", "right_top", "align_center_row", "align_center_column")


def grid(a):
    if not isinstance(a, list) or not 1 <= len(a) <= 30:
        raise ValueError("Grid height outside 1..30")
    if not isinstance(a[0], list) or not 1 <= len(a[0]) <= 30:
        raise ValueError("Grid width outside 1..30")
    if any(not isinstance(row, list) or len(row) != len(a[0]) for row in a):
        raise ValueError("Ragged grid")
    if any(type(c) is not int or not 0 <= c <= 9 for row in a for c in row):
        raise ValueError("Color outside integer 0..9")
    return tuple(tuple(row) for row in a)


@dataclass(frozen=True)
class Object:
    pixels: tuple
    bounds: tuple
    colors: tuple
    shape: tuple

    @property
    def area(self): return len(self.pixels)

    @property
    def height(self): return self.bounds[2] - self.bounds[0] + 1

    @property
    def width(self): return self.bounds[3] - self.bounds[1] + 1


def background(g, kind):
    if kind == "zero": return 0
    counts = Counter(c for row in g for c in row)
    winners = [c for c, count in counts.items() if count == max(counts.values())]
    return winners[0] if len(winners) == 1 else None


def objects(g, bg, connectivity, monochrome, deadline):
    todo = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != bg}
    offsets = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        offsets += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    out = []
    while todo:
        if time.process_time() >= deadline: raise TimeoutError("Task CPU cap")
        origin = min(todo); todo.remove(origin); stack = [origin]; cells = []
        while stack:
            r, c = stack.pop(); cells.append((r, c))
            for dr, dc in offsets:
                p = r + dr, c + dc
                if p in todo and (not monochrome or g[p[0]][p[1]] == g[r][c]):
                    todo.remove(p); stack.append(p)
        bounds = (min(r for r, c in cells), min(c for r, c in cells),
                  max(r for r, c in cells), max(c for r, c in cells))
        out.append(Object(tuple(sorted(cells)), bounds,
                          tuple(sorted({g[r][c] for r, c in cells})),
                          tuple(sorted((r - bounds[0], c - bounds[1]) for r, c in cells))))
        if len(out) > 40: return None
    return tuple(out)


def contains(a, b):
    return (a != b and a.bounds[0] <= b.bounds[0] and a.bounds[1] <= b.bounds[1]
            and a.bounds[2] >= b.bounds[2] and a.bounds[3] >= b.bounds[3])


def select(obs, kind):
    if not obs: return None
    shape_counts = Counter(o.shape for o in obs)
    color_counts = Counter(c for o in obs for c in o.colors)
    if kind == "unique_shape": candidates = [o for o in obs if shape_counts[o.shape] == 1]
    elif kind == "unique_color":
        candidates = [o for o in obs if len(o.colors) == 1 and color_counts[o.colors[0]] == 1]
    elif kind == "outer_container": candidates = [o for o in obs if any(contains(o, q) for q in obs)]
    elif kind == "inner_contained": candidates = [o for o in obs if any(contains(q, o) for q in obs)]
    else:
        values = {"largest_area": lambda o: -o.area, "smallest_area": lambda o: o.area,
                  "largest_box": lambda o: -o.width * o.height, "smallest_box": lambda o: o.width * o.height,
                  "widest": lambda o: -o.width, "narrowest": lambda o: o.width,
                  "tallest": lambda o: -o.height, "shortest": lambda o: o.height,
                  "topmost": lambda o: o.bounds[0], "bottommost": lambda o: -o.bounds[2],
                  "leftmost": lambda o: o.bounds[1], "rightmost": lambda o: -o.bounds[3]}
        key = values[kind]; best = min(key(o) for o in obs)
        candidates = [o for o in obs if key(o) == best]
    return candidates[0] if len(candidates) == 1 else None


def orient(g, turn):
    if turn >= 4: g = tuple(tuple(reversed(row)) for row in g); turn -= 4
    for _ in range(turn): g = tuple(tuple(row) for row in zip(*g[::-1]))
    return g


def crop(g, bounds):
    r0, c0, r1, c1 = bounds
    return tuple(tuple(row[c0:c1 + 1]) for row in g[r0:r1 + 1])


def displacement(source, anchor, kind):
    r, c, rr, cc = source.bounds; ar, ac, arr, acc = anchor.bounds
    if kind == "align_top_left": return ar - r, ac - c
    if kind == "above_left": return ar - 1 - rr, ac - c
    if kind == "below_left": return arr + 1 - r, ac - c
    if kind == "left_top": return ar - r, ac - 1 - cc
    if kind == "right_top": return ar - r, acc + 1 - c
    dr, dc = ar + arr - r - rr, ac + acc - c - cc
    if kind == "align_center":
        return (dr // 2, dc // 2) if dr % 2 == dc % 2 == 0 else None
    if kind == "align_center_row": return (dr // 2, 0) if dr % 2 == 0 else None
    if kind == "align_center_column": return (0, dc // 2) if dc % 2 == 0 else None
    raise ValueError("Unknown translation")


def apply(g, bg, selections, program):
    selector, op, option, anchor_name = program
    source = selections[selector]
    if source is None: return None
    if op in ("crop_raw", "crop_isolated"):
        image = g
        if op == "crop_isolated":
            cells = set(source.pixels)
            image = tuple(tuple(v if (r, c) in cells else bg for c, v in enumerate(row)) for r, row in enumerate(g))
        return orient(crop(image, source.bounds), option)
    out = [list(row) for row in g]
    if op == "keep":
        cells = set(source.pixels)
        return tuple(tuple(v if (r, c) in cells else bg for c, v in enumerate(row)) for r, row in enumerate(g))
    if op in ("erase", "recolor_fixed"):
        for r, c in source.pixels: out[r][c] = bg if op == "erase" else option
        return tuple(tuple(row) for row in out)
    anchor = selections[anchor_name]
    if anchor is None or anchor == source: return None
    if op == "crop_pair":
        a, b = source.bounds, anchor.bounds
        return crop(g, (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])))
    if op == "recolor_to_anchor":
        if len(anchor.colors) != 1: return None
        for r, c in source.pixels: out[r][c] = anchor.colors[0]
    elif op in ("move", "copy"):
        delta = displacement(source, anchor, option)
        if delta is None: return None
        dr, dc = delta; moved = [(r + dr, c + dc, g[r][c]) for r, c in source.pixels]
        if not all(0 <= r < len(g) and 0 <= c < len(g[0]) for r, c, v in moved): return None
        source_set = set(source.pixels)
        if any(g[r][c] != bg and (r, c) not in source_set for r, c, v in moved): return None
        if op == "move":
            for r, c in source.pixels: out[r][c] = bg
        for r, c, v in moved: out[r][c] = v
    elif op == "axis_bridge":
        if len(source.colors) != 1 or len(anchor.colors) != 1: return None
        a, b = source.bounds, anchor.bounds
        if any(v % 2 for v in (a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3])): return None
        r, c, ar, ac = (a[0] + a[2]) // 2, (a[1] + a[3]) // 2, (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
        if r != ar and c != ac: return None
        cells = [(r, x) for x in range(min(c, ac), max(c, ac) + 1)] if r == ar else [(x, c) for x in range(min(r, ar), max(r, ar) + 1)]
        color = source.colors[0] if option == "source" else anchor.colors[0]
        for rr, cc in cells:
            if out[rr][cc] == bg: out[rr][cc] = color
    else: raise ValueError("Unknown operation")
    return tuple(tuple(row) for row in out)


def programs():
    for selector in SELECTORS:
        for op in ("crop_raw", "crop_isolated"):
            for turn in range(8): yield selector, op, turn, None
        for op in ("keep", "erase"): yield selector, op, None, None
        for color in range(10): yield selector, "recolor_fixed", color, None
        for anchor in SELECTORS:
            if anchor == selector: continue
            for op in ("recolor_to_anchor", "crop_pair"): yield selector, op, None, anchor
            for op in ("move", "copy"):
                for kind in TRANSLATIONS: yield selector, op, kind, anchor
            for side in ("source", "anchor"): yield selector, "axis_bridge", side, anchor


def solve_task(task):
    start_cpu, start_wall = time.process_time(), time.monotonic(); deadline = start_cpu + 1.2
    if not isinstance(task, dict) or set(task) != {"train", "test"}:
        raise ValueError("Only demonstrations and test inputs accepted")
    if not isinstance(task["train"], list) or not isinstance(task["test"], list): raise ValueError("Pairs must be lists")
    if not 2 <= len(task["train"]) <= 10 or not 1 <= len(task["test"]) <= 8: raise ValueError("Pair count outside bounds")
    if any(not isinstance(p, dict) or set(p) != {"input", "output"} for p in task["train"]): raise ValueError("Training pair extras")
    if any(not isinstance(p, dict) or set(p) != {"input"} for p in task["test"]): raise ValueError("Test truth or identifier forbidden")
    inputs = [grid(p["input"]) for p in task["train"]]; targets = [grid(p["output"]) for p in task["train"]]
    tests = [grid(p["input"]) for p in task["test"]]; all_grids = inputs + tests
    result = {"attempts": [[] for _ in tests], "fitted_programs": [], "distinct_bundles": 0,
              "timed_out": False, "abstention": None, "programs_checked": 0}
    bundles = []; names = []
    try:
        for bg_kind in ("unique_mode", "zero"):
            for connectivity in (4, 8):
                for monochrome in (True, False):
                    contexts = []
                    for g in all_grids:
                        bg = background(g, bg_kind)
                        obs = objects(g, bg, connectivity, monochrome, deadline) if bg is not None else None
                        if obs is None: break
                        contexts.append((bg, {name: select(obs, name) for name in SELECTORS}))
                    if len(contexts) != len(all_grids): continue
                    segment = (bg_kind, connectivity, monochrome)
                    for program in programs():
                        if time.process_time() >= deadline: raise TimeoutError("Task CPU cap")
                        result["programs_checked"] += 1
                        if not all(apply(g, bg, picks, program) == target for g, target, (bg, picks) in zip(inputs, targets, contexts)):
                            continue
                        predictions = [apply(g, bg, picks, program) for g, (bg, picks) in zip(tests, contexts[len(inputs):])]
                        if any(g is None for g in predictions): continue
                        name = repr((segment, program)); result["fitted_programs"].append(name)
                        bundle = tuple(predictions)
                        if bundle not in bundles: bundles.append(bundle); names.append(name)
                        if len(bundles) > 2:
                            result["abstention"] = "More than two fitted test bundles"
                            break
                    if result["abstention"]: break
                if result["abstention"]: break
            if result["abstention"]: break
    except TimeoutError:
        result["timed_out"] = True; result["abstention"] = "Incomplete grammar search"
    result["distinct_bundles"] = len(bundles)
    if not result["abstention"]:
        for i in range(len(tests)):
            for bundle in bundles:
                image = [list(row) for row in bundle[i]]
                if image not in result["attempts"][i]: result["attempts"][i].append(image)
        if not bundles: result["abstention"] = "No demonstration-exact fitted program"
    result["chosen_programs"] = names if not result["abstention"] else []
    result["cpu_seconds"] = time.process_time() - start_cpu
    result["wall_seconds"] = time.monotonic() - start_wall
    return result
