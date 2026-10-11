"""Original bounded, demo-cross-validated spatial decision programs. MIT.

Inputs are demonstration pairs and query inputs only. No task IDs, pretrained
model, stored answers, network, or filesystem is consulted by solve_task.
This small grammar applies only to same-shape input/output transformations.
"""
from collections import Counter, deque
import time

FEATURE_NAMES = (
    "color", "is_background", "majority_color", "rarest_color",
    "row_nonbackground", "column_nonbackground", "global_color_rank",
    "component_area", "component_height", "component_width", "component_solid",
    "component_top", "component_bottom", "component_left", "component_right",
    "enclosed_background", "on_grid_border", "row_quartile", "column_quartile",
    "mirror_horizontal", "mirror_vertical", "rotate_half", "diagonal_transpose",
) + tuple(f"neighbor_{dr}_{dc}" for dr, dc in
          ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))) + (
    "neighbor_foreground_4", "neighbor_foreground_8", "neighbor_same_4", "neighbor_same_8",
) + tuple(f"ray_{d}_{kind}" for d in ("north", "south", "west", "east")
          for kind in ("nearest_color", "distance", "foreground_count"))


def grid(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 30:
        raise ValueError("Grid height must be 1..30")
    if any(not isinstance(row, list) for row in value):
        raise ValueError("Grid rows must be lists")
    if not 1 <= len(value[0]) <= 30 or any(len(row) != len(value[0]) for row in value):
        raise ValueError("Grid width must be 1..30 and rectangular")
    if any(type(c) is not int or not 0 <= c <= 9 for row in value for c in row):
        raise ValueError("Grid colors must be integer 0..9")
    return tuple(tuple(row) for row in value)


def features(g):
    h, w = len(g), len(g[0])
    counts = Counter(c for row in g for c in row)
    order = sorted(counts, key=lambda c: (-counts[c], c))
    bg, rare = order[0], min(counts, key=lambda c: (counts[c], c))
    rank = {c: i for i, c in enumerate(order)}
    row_n = [sum(c != bg for c in row) for row in g]
    col_n = [sum(g[r][c] != bg for r in range(h)) for c in range(w)]
    parts, unseen = {}, {(r, c) for r in range(h) for c in range(w) if g[r][c] != bg}
    dirs = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        stack, group = [seed], [seed]
        while stack:
            r, c = stack.pop()
            for dr, dc in dirs:
                q = r + dr, c + dc
                if q in unseen and g[q[0]][q[1]] == g[r][c]:
                    unseen.remove(q)
                    stack.append(q)
                    group.append(q)
        r0, r1 = min(r for r, c in group), max(r for r, c in group)
        c0, c1 = min(c for r, c in group), max(c for r, c in group)
        for r, c in group:
            parts[r, c] = (len(group), r1-r0+1, c1-c0+1,
                           int(len(group) == (r1-r0+1)*(c1-c0+1)),
                           int(r == r0), int(r == r1), int(c == c0), int(c == c1))
    exterior, queue = set(), deque()
    for r in range(h):
        for c in range(w):
            if g[r][c] == bg and (r in (0, h-1) or c in (0, w-1)):
                exterior.add((r, c)); queue.append((r, c))
    while queue:
        r, c = queue.popleft()
        for dr, dc in dirs:
            q = r+dr, c+dc
            if (0 <= q[0] < h and 0 <= q[1] < w and g[q[0]][q[1]] == bg
                    and q not in exterior):
                exterior.add(q); queue.append(q)
    records = []
    all_dirs = dirs + ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(h):
        for c in range(w):
            neighbors = [g[r+dr][c+dc] if 0 <= r+dr < h and 0 <= c+dc < w else -1
                         for dr, dc in all_dirs]
            f = [g[r][c], int(g[r][c] == bg), bg, rare, row_n[r], col_n[c], rank[g[r][c]]]
            f += list(parts.get((r, c), (0,)*8))
            f += [int(g[r][c] == bg and (r, c) not in exterior),
                  int(r in (0, h-1) or c in (0, w-1)), min(3, 4*r//h), min(3, 4*c//w),
                  g[r][w-1-c], g[h-1-r][c], g[h-1-r][w-1-c], g[c][r] if h == w else -1]
            f += neighbors
            f += [sum(v not in (-1, bg) for v in neighbors[:4]),
                  sum(v not in (-1, bg) for v in neighbors),
                  sum(v == g[r][c] for v in neighbors[:4]), sum(v == g[r][c] for v in neighbors)]
            for dr, dc in dirs:
                nr, nc, near, distance, n = r+dr, c+dc, -1, 31, 0
                step = 1
                while 0 <= nr < h and 0 <= nc < w:
                    if g[nr][nc] != bg:
                        n += 1
                        if near == -1:
                            near, distance = g[nr][nc], step
                    nr += dr; nc += dc; step += 1
                f += [near, distance, n]
            records.append(tuple(f))
    return records, bg


class Capped(Exception):
    pass


def check_time(deadline):
    if time.process_time() > deadline:
        raise Capped("CPU task cap reached")


def fit_tree(xs, ys, depth, min_leaf, deadline):
    """Greedy integer threshold tree, exact impurity comparisons, stable ties."""
    check_time(deadline)
    labels = Counter(ys)
    if len(labels) == 1:
        return {"label": ys[0]}
    if depth == 0 or len(ys) < 2*min_leaf:
        return {"label": min(labels, key=lambda y: (-labels[y], y))}
    best = None
    n = len(ys)
    for j in range(len(FEATURE_NAMES)):
        check_time(deadline)
        ordered = sorted(zip(xs, ys), key=lambda q: q[0][j])
        left, right = Counter(), labels.copy()
        left_squares, right_squares = 0, sum(v*v for v in right.values())
        for k, (x, y) in enumerate(ordered[:-1], 1):
            left_squares += 2*left[y]+1
            right_squares -= 2*right[y]-1
            left[y] += 1; right[y] -= 1
            if k < min_leaf or n-k < min_leaf or x[j] == ordered[k][0][j]:
                continue
            # Maximize sum of squared class proportions; avoid floating tie drift.
            num, den = left_squares*(n-k) + right_squares*k, k*(n-k)
            candidate = (num, den, j, x[j])
            if (best is None or num*best[1] > best[0]*den
                    or (num*best[1] == best[0]*den and (j, x[j]) < (best[2], best[3]))):
                best = candidate
    if best is None:
        return {"label": min(labels, key=lambda y: (-labels[y], y))}
    num, den, j, cut = best
    # A zero-gain split only memorizes, so abstain via the later exact-fit check.
    if num*n <= sum(v*v for v in labels.values())*den:
        return {"label": min(labels, key=lambda y: (-labels[y], y))}
    li = [i for i, x in enumerate(xs) if x[j] <= cut]
    ri = [i for i, x in enumerate(xs) if x[j] > cut]
    return {"feature": j, "at_most": cut,
            "left": fit_tree([xs[i] for i in li], [ys[i] for i in li], depth-1, min_leaf, deadline),
            "right": fit_tree([xs[i] for i in ri], [ys[i] for i in ri], depth-1, min_leaf, deadline)}


def predict_label(tree, x):
    while "label" not in tree:
        tree = tree["left"] if x[tree["feature"]] <= tree["at_most"] else tree["right"]
    return tree["label"]


def tree_size(tree):
    return 1 if "label" in tree else 1+tree_size(tree["left"])+tree_size(tree["right"])


def labels_for(g, target, mode):
    bg = Counter(c for row in g for c in row)
    bg = min(bg, key=lambda c: (-bg[c], c))
    return [10 if mode == "actions" and wanted == color else
            11 if mode == "actions" and wanted == bg else wanted
            for row, out in zip(g, target) for color, wanted in zip(row, out)]


def apply_tree(tree, xs, g, bg):
    flat = []
    for x, c in zip(xs, (v for row in g for v in row)):
        label = predict_label(tree, x)
        flat.append(c if label == 10 else bg if label == 11 else label)
    w = len(g[0])
    return [flat[r:r+w] for r in range(0, len(flat), w)]


CONFIGS = ((4, 4, "actions"), (6, 4, "actions"), (6, 4, "literal"))


def solve_task(task, cpu_seconds=1.5):
    if type(cpu_seconds) not in (int, float) or not 0 < cpu_seconds <= 10:
        raise ValueError("Positive CPU cap <=10 seconds required")
    if not isinstance(task, dict) or set(task) != {"train", "test"}:
        raise ValueError("Only train/test challenges are accepted")
    if not isinstance(task["train"], list) or not 2 <= len(task["train"]) <= 10:
        raise ValueError("2..10 demonstrations required")
    if not isinstance(task["test"], list) or not 1 <= len(task["test"]) <= 10:
        raise ValueError("1..10 query inputs required")
    if any(not isinstance(p, dict) or set(p) != {"input", "output"} for p in task["train"]):
        raise ValueError("Demonstrations require input/output only")
    if any(not isinstance(p, dict) or set(p) != {"input"} for p in task["test"]):
        raise ValueError("Query outputs and metadata are forbidden")
    inputs = [grid(p["input"]) for p in task["train"]]
    targets = [grid(p["output"]) for p in task["train"]]
    tests = [grid(p["input"]) for p in task["test"]]
    abstain = {"attempts": [[] for _ in tests], "models": [], "status": "ABSTAIN"}
    if any((len(a), len(a[0])) != (len(b), len(b[0])) for a, b in zip(inputs, targets)):
        return dict(abstain, reason="Grammar is same-shape only")
    deadline = time.process_time() + float(cpu_seconds)
    record = []
    try:
        train_f = [features(g) for g in inputs]
        test_f = [features(g) for g in tests]
        for depth, min_leaf, mode in CONFIGS:
            check_time(deadline)
            ys = [labels_for(g, t, mode) for g, t in zip(inputs, targets)]
            all_x, all_y = [x for xs, bg in train_f for x in xs], [y for group in ys for y in group]
            model = fit_tree(all_x, all_y, depth, min_leaf, deadline)
            if any(apply_tree(model, xs, g, bg) != [list(row) for row in target]
                   for (xs, bg), g, target in zip(train_f, inputs, targets)):
                continue
            cv = True
            for held in range(len(inputs)):
                keep_x = [x for i, (xs, bg) in enumerate(train_f) if i != held for x in xs]
                keep_y = [y for i, group in enumerate(ys) if i != held for y in group]
                sub = fit_tree(keep_x, keep_y, depth, min_leaf, deadline)
                if apply_tree(sub, train_f[held][0], inputs[held], train_f[held][1]) != [list(r) for r in targets[held]]:
                    cv = False; break
            if cv:
                predictions = [apply_tree(model, xs, g, bg) for (xs, bg), g in zip(test_f, tests)]
                record.append({"depth": depth, "min_leaf": min_leaf, "label_mode": mode,
                               "nodes": tree_size(model), "tree": model, "predictions": predictions,
                               "leave_one_demo_out_exact": len(inputs)})
        record.sort(key=lambda x: (x["nodes"], x["depth"], x["label_mode"]))
        attempts = []
        for i in range(len(tests)):
            distinct = []
            for model in record:
                prediction = model["predictions"][i]
                if prediction not in distinct:
                    distinct.append(prediction)
            attempts.append(distinct[:2])
        return {"attempts": attempts, "models": record, "status": "FIT" if record else "ABSTAIN"}
    except Capped:
        # Keep completed, cross-validated models only; never a partial tree.
        attempts = []
        record.sort(key=lambda x: (x["nodes"], x["depth"], x["label_mode"]))
        for i in range(len(tests)):
            distinct = []
            for model in record:
                p = model["predictions"][i]
                if p not in distinct:
                    distinct.append(p)
            attempts.append(distinct[:2])
        return {"attempts": attempts, "models": record, "status": "CAPPED"}


def fill_only(main, supplement):
    """Validated ordered grids in; existing distinct attempts remain unchanged."""
    def unique(values):
        out = []
        for value in values:
            canonical = grid(value)
            if canonical not in out:
                out.append(canonical)
        return out
    before, extra = unique(main), unique(supplement)
    merged = before[:2]
    for candidate in extra:
        if len(merged) == 2:
            break
        if candidate not in merged:
            merged.append(candidate)
    return [[list(row) for row in value] for value in merged]
