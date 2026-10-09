"""Original CPU-only demonstration-fitted grid programs. MIT, 2026 cubres.

No task identifier, reference prediction, file path, or evaluation solution is
accepted by the solver. Abstention is [] and must never overwrite a good answer.
The finite grammar and ranking were fixed before this study's evaluation.
"""
from collections import Counter


def grid(value):
    if not isinstance(value, list) or not value or len(value) > 30:
        raise ValueError("Expected a nonempty ARC grid")
    rows = tuple(tuple(row) for row in value)
    if not rows[0] or len(rows[0]) > 30 or any(len(r) != len(rows[0]) for r in rows):
        raise ValueError("Expected a rectangular 1..30 grid")
    if any(type(c) is not int or not 0 <= c <= 9 for r in rows for c in r):
        raise ValueError("ARC colors must be integers 0..9")
    return rows


def mode(g):
    counts = Counter(c for row in g for c in row)
    return min(counts, key=lambda c: (-counts[c], c))


def bbox(g, cells):
    if not cells:
        return None
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return tuple(row[c0:c1+1] for row in g[r0:r1+1])


def orient(g, n):
    if n >= 4:
        g = tuple(row[::-1] for row in g)
    for _ in range(n % 4):
        g = tuple(tuple(row) for row in zip(*g[::-1]))
    return g


def components(g, bg, diagonal, monochrome):
    remaining = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != bg}
    found = []
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                  if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        group, stack = [seed], [seed]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                nxt = r + dr, c + dc
                if nxt in remaining and (not monochrome or g[nxt[0]][nxt[1]] == g[r][c]):
                    remaining.remove(nxt)
                    stack.append(nxt)
                    group.append(nxt)
        found.append(group)
    return found


def extract(g, kind, arg):
    h, w = len(g), len(g[0])
    if kind == "identity":
        return g
    if kind in ("foreground_bbox", "color_bbox"):
        color = mode(g) if arg == "mode" else arg
        cells = [(r, c) for r in range(h) for c in range(w)
                 if (g[r][c] != color if kind == "foreground_bbox" else g[r][c] == color)]
        return bbox(g, cells)
    if kind == "component":
        bg_name, diagonal, monochrome, smallest = arg
        bg = mode(g) if bg_name == "mode" else bg_name
        groups = components(g, bg, diagonal, monochrome)
        if not groups:
            return None
        sizes = [len(group) for group in groups]
        wanted = min(sizes) if smallest else max(sizes)
        winners = [group for group in groups if len(group) == wanted]
        # Abstain on equal-size objects: location is not an inferred rule.
        if len(winners) != 1:
            return None
        return bbox(g, winners[0])
    if kind == "panel_boolean":
        axis, separator, operation, bg_name = arg
        bg = mode(g) if bg_name == "mode" else bg_name
        if axis == "vertical":
            if (w - separator) % 2:
                return None
            half = (w - separator) // 2
            if half < 1:
                return None
            if separator and len({row[half] for row in g}) != 1:
                return None
            a = tuple(row[:half] for row in g)
            b = tuple(row[half+separator:] for row in g)
        else:
            if (h - separator) % 2:
                return None
            half = (h - separator) // 2
            if half < 1:
                return None
            if separator and len(set(g[half])) != 1:
                return None
            a, b = g[:half], g[half+separator:]
        truth = {"and": lambda x, y: x and y,
                 "or": lambda x, y: x or y,
                 "xor": lambda x, y: x != y}
        return tuple(tuple(int(truth[operation](x != bg, y != bg)) for x, y in zip(ar, br))
                     for ar, br in zip(a, b))
    raise ValueError("Unknown extraction")


def resize(g, kind, rows, cols):
    if kind == "nearest":
        return tuple(tuple(c for c in row for _ in range(cols)) for row in g for _ in range(rows))
    if kind == "tile":
        return tuple(row * cols for _ in range(rows) for row in g)
    raise ValueError("Unknown resize")


def extractors(palette):
    yield (0, "identity", None)
    for bg in ("mode", 0):
        yield (2, "foreground_bbox", bg)
    for color in sorted(palette):
        yield (3, "color_bbox", color)
    for bg in ("mode", 0):
        for diagonal in (False, True):
            for monochrome in (True, False):
                for smallest in (False, True):
                    yield (4, "component", (bg, diagonal, monochrome, smallest))
    for axis in ("vertical", "horizontal"):
        for separator in (0, 1):
            for operation in ("and", "or", "xor"):
                for bg in ("mode", 0):
                    yield (4, "panel_boolean", (axis, separator, operation, bg))


def color_fit(intermediate, targets):
    mapping = {}
    for g, target in zip(intermediate, targets):
        if len(g) != len(target) or len(g[0]) != len(target[0]):
            return None
        for row, target_row in zip(g, target):
            for color, wanted in zip(row, target_row):
                if color in mapping and mapping[color] != wanted:
                    return None
                mapping[color] = wanted
    return mapping


def color_apply(g, mapping):
    # Identity is allowed on previously unseen colors only when the entire
    # learned map is identity. A nonidentity map must cover every test color.
    identity = all(c == v for c, v in mapping.items())
    if not identity and any(c not in mapping for row in g for c in row):
        return None
    return tuple(tuple(mapping.get(c, c) for c in row) for row in g)


def solve_task(task):
    if set(task) != {"train", "test"}:
        raise ValueError("Only demonstration pairs and test inputs are accepted")
    if len(task["train"]) < 2 or not task["test"]:
        return {"attempts": [[] for _ in task["test"]], "strict": [[] for _ in task["test"]],
                "fit_count": 0, "reason": "At least two demonstrations required"}
    if any(set(pair) != {"input", "output"} for pair in task["train"]):
        raise ValueError("Demonstrations require input/output only")
    if any(set(pair) != {"input"} for pair in task["test"]):
        raise ValueError("Test outputs are forbidden")
    inputs = [grid(pair["input"]) for pair in task["train"]]
    targets = [grid(pair["output"]) for pair in task["train"]]
    tests = [grid(pair["input"]) for pair in task["test"]]
    palette = {c for g in inputs for row in g for c in row}
    fits = []
    for extraction_cost, kind, arg in extractors(palette):
        extracted = [extract(g, kind, arg) for g in inputs + tests]
        if any(g is None for g in extracted):
            continue
        for orientation in range(8):
            oriented = [orient(g, orientation) for g in extracted]
            # Size relations derive solely from the demonstrations.
            ratio = None
            for g, target in zip(oriented, targets):
                if len(target) % len(g) or len(target[0]) % len(g[0]):
                    ratio = None
                    break
                current = len(target) // len(g), len(target[0]) // len(g[0])
                if current[0] not in (1, 2, 3) or current[1] not in (1, 2, 3):
                    ratio = None
                    break
                if ratio is not None and ratio != current:
                    ratio = None
                    break
                ratio = current
            if ratio is None:
                continue
            for resize_kind in ("nearest", "tile"):
                transformed = [resize(g, resize_kind, *ratio) for g in oriented]
                if any(len(g) > 30 or len(g[0]) > 30 for g in transformed):
                    continue
                mapping = color_fit(transformed[:len(inputs)], targets)
                if mapping is None:
                    continue
                predicted = [color_apply(g, mapping) for g in transformed[len(inputs):]]
                if any(g is None for g in predicted):
                    continue
                name = repr((kind, arg, orientation, resize_kind, ratio, sorted(mapping.items())))
                cost = (extraction_cost + int(orientation != 0) + int(ratio != (1, 1)) * 2
                        + int(any(c != v for c, v in mapping.items())))
                fits.append((cost, name, predicted))
    fits.sort(key=lambda item: (item[0], item[1]))
    attempts, strict, chosen = [], [], []
    for i in range(len(tests)):
        unique, programs = {}, []
        for cost, name, predictions in fits:
            candidate = predictions[i]
            if candidate not in unique:
                unique[candidate] = (cost, name)
                programs.append({"cost": cost, "program": name})
        all_candidates = list(unique)
        attempts.append([[list(row) for row in g] for g in all_candidates[:2]])
        strict.append([[list(row) for row in all_candidates[0]]] if len(all_candidates) == 1 else [])
        chosen.append({"unique_predictions": len(all_candidates), "top2": programs[:2]})
    return {"attempts": attempts, "strict": strict, "fit_count": len(fits), "chosen": chosen}
