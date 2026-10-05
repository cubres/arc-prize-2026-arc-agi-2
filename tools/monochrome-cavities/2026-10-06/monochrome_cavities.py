"""Validated public API for an original, demonstration-derived cavity family.

Standard-library only. The exact studied implementation is retained in
reference_cavity_programs.py; this wrapper adds input ownership and public
argument guards, plus a conservative post-render CPU-deadline check. Deadlines
are cooperative process CPU budgets, not wall-time or security sandboxes.
"""
from __future__ import annotations

import json
import math
import time

import reference_cavity_programs as _reference

_clock = time.process_time


def checked_grid(value):
    """Return an owned immutable ARC grid; reject bools, floats and ragged rows."""
    return _reference.checked_grid(value)


def _color(value, name):
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(name + " must be a built-in integer color 0..9")
    return value


def _adjacency(value):
    if type(value) is not int or value not in (4, 8):
        raise ValueError("adjacency must be integer 4 or 8")
    return value


def _budget(value):
    if type(value) not in (int, float):
        raise ValueError("cpu_seconds must be finite and positive")
    try:
        result = float(value)
    except (OverflowError, ValueError):
        raise ValueError("cpu_seconds must be finite and positive") from None
    if not math.isfinite(result) or result <= 0:
        raise ValueError("cpu_seconds must be finite and positive")
    return result


def _finish(deadline):
    if _clock() >= deadline:
        raise TimeoutError("cooperative process CPU budget expired before return")


def enclosed_cells(value, color, adjacency=4, *, cpu_seconds=0.20):
    """Return immutable cells of complete color components touching no border."""
    budget = _budget(cpu_seconds)
    deadline = _clock() + budget
    source = checked_grid(value)
    color, adjacency = _color(color, "color"), _adjacency(adjacency)
    mask = _reference.cavity_mask(source, color, adjacency, deadline)
    _finish(deadline)
    return mask


def recolor_enclosed(value, color, ink, adjacency=4, *, cpu_seconds=0.20):
    """Recolor enclosed components while preserving every other input cell."""
    budget = _budget(cpu_seconds)
    deadline = _clock() + budget
    source = checked_grid(value)
    color, ink, adjacency = _color(color, "color"), _color(ink, "ink"), _adjacency(adjacency)
    mask = _reference.cavity_mask(source, color, adjacency, deadline)
    result = _reference.render(source, mask, ink)
    _finish(deadline)
    return result


def _task(value):
    if type(value) is not dict or set(value) != {"train", "test"}:
        raise ValueError("task accepts train pairs and test input only")
    if type(value["train"]) not in (list, tuple) or not 1 <= len(value["train"]) <= 20:
        raise ValueError("task requires 1..20 fitting pairs")
    if type(value["test"]) not in (list, tuple) or len(value["test"]) != 1:
        raise ValueError("task requires exactly one query input")
    pairs = []
    for pair in value["train"]:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("fitting pair requires input and output only")
        pairs.append({"input": checked_grid(pair["input"]), "output": checked_grid(pair["output"])})
    query = value["test"][0]
    if type(query) is not dict or set(query) != {"input"}:
        raise ValueError("query accepts input only; query targets are forbidden")
    return {"train": pairs, "test": [{"input": checked_grid(query["input"])}]}


def fit_predict(task, *, cpu_seconds=0.20):
    """Enumerate <=180 exact non-vacuous fit programs; return detached results.

Only fitting colors define the grammar. Ranking and whole-family abstention
are exactly those of the frozen family. The wrapper can additionally raise
TimeoutError during validation/finalization instead of returning past budget.
"""
    budget = _budget(cpu_seconds)
    deadline = _clock() + budget
    clean = _task(task)
    remaining = deadline - _clock()
    if remaining <= 0:
        raise TimeoutError("CPU budget expired during argument validation")
    result = _reference.solve(clean, cpu_seconds=remaining)
    if not 0 <= result["counts"]["programs_enumerated"] <= 180:
        raise RuntimeError("frozen program bound violated")
    _finish(deadline)
    return result


def _owned_candidates(value, *, maximum):
    if type(value) not in (list, tuple) or len(value) > maximum:
        raise ValueError("candidate count outside public contract")
    for candidate in value:
        if type(candidate) is not dict or "grids" not in candidate or any(type(k) is not str for k in candidate):
            raise ValueError("candidate must be a dictionary with grids")
        if type(candidate["grids"]) not in (list, tuple) or len(candidate["grids"]) != 1:
            raise ValueError("one joint query grid is required")
        checked_grid(candidate["grids"][0])
    # Detach all JSON metadata as well as grids. This avoids output aliases to
    # caller-owned parent dictionaries and rejects non-JSON/non-finite payloads.
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError, OverflowError):
        raise ValueError("candidate metadata must be finite JSON data") from None


def fill_vacancies(parent, candidates):
    """Return owned top-two guesses with the original parent prefix preserved."""
    original = _owned_candidates(parent, maximum=2)
    additions = _owned_candidates(candidates, maximum=180)
    return _reference.augment(original, additions)
