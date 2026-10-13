#!/usr/bin/env python3
"""Original standard-library language experiment; no notebook/model imports.

This independently models the published V1 grid acceptance contract, including
ignored blank rows and truncation to the first 30 nonempty rows. It does not run
the published parser, tokenization, logits, batched DFS, or a competition task.
SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import itertools
import json
import pathlib
import time

NEWLINE = 10
EOS = 15


def reference_grid(body):
    rows, current = [], []
    for token in body:
        if token == NEWLINE:
            if current:
                rows.append(current)
            current = []
        elif 0 <= token <= 9:
            current.append(token)
        else:
            raise ValueError("body outside declared ARC token alphabet")
    if current:
        rows.append(current)
    rows = rows[:30]
    if not rows or not 1 <= len(rows[0]) <= 30:
        return None
    if any(len(row) != len(rows[0]) for row in rows):
        return None
    return tuple(map(tuple, rows))


def step(state, token):
    """None means no suffix can ever produce an accepted V1 grid."""
    count, width, run = state
    if count >= 30:
        # V1 discards later nonempty rows; do not silently tighten its language.
        return state
    if token == NEWLINE:
        if run == 0:
            return state
        if width and run != width:
            return None
        return (count + 1, width or run, 0)
    if not 0 <= token <= 9:
        raise ValueError("invalid body token")
    run += 1
    if run > (width or 30):
        return None
    return (count, width, run)


def accepts_eos(state):
    count, width, run = state
    if count >= 30:
        return True
    if run:
        return not width or run == width
    return count > 0


def state_for(body):
    state = (0, 0, 0)
    for token in body:
        state = step(state, token)
        if state is None:
            return None
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    started_wall, started_cpu = time.monotonic(), time.process_time()
    cases = 0
    accepted = 0
    irreparable = 0
    digest = hashlib.sha256()
    # 29,524 EOS-terminated paths, all body lengths 0..9 over two digits+NL.
    # Scores are unchanged invented path costs, not measured model NLLs.
    for length in range(10):
        for body in itertools.product((0, 1, NEWLINE), repeat=length):
            reference = reference_grid(body)
            state = state_for(body)
            actual = state is not None and accepts_eos(state)
            if actual != (reference is not None):
                raise RuntimeError("language acceptance mismatch")
            cases += 1
            accepted += actual
            irreparable += state is None
            if actual:
                record = [body, reference, sum((i+1)*(t+1) for i,t in enumerate(body))]
                digest.update(json.dumps(record, separators=(",", ":")).encode())
    edges = [
        ([], False),
        ([NEWLINE, 0, NEWLINE, NEWLINE], True),
        ([0, NEWLINE, 1, 1, NEWLINE], False),
        ([0] * 30, True),
        ([0] * 31, False),
        ([0, NEWLINE] * 30 + [1] * 31, True),
        ([0, NEWLINE] * 29 + [1] * 31, False),
        ([0, 1, NEWLINE, 1], False),
        ([0, 1, NEWLINE, 1, 0], True),
        ([0, NEWLINE] * 31, True),
    ]
    for body, expected in edges:
        state = state_for(body)
        actual = state is not None and accepts_eos(state)
        if actual != expected or (reference_grid(body) is not None) != expected:
            raise RuntimeError("boundary acceptance mismatch")
    # Exhaustive traversal records nonterminal node expansions only. A dead
    # prefix may still be visited once, but its descendant model calls vanish.
    def traversal(prune):
        calls = 0
        valid = []
        stack = [((), (0,0,0))]
        while stack:
            body, state = stack.pop()
            if len(body) == 9:
                continue
            calls += 1
            for token in (0,1,NEWLINE):
                child = body + (token,)
                child_state = step(state,token) if state is not None else None
                if prune and child_state is None:
                    continue
                if reference_grid(child) is not None:
                    valid.append(child)
                stack.append((child,child_state))
        return calls, sorted(valid)
    baseline_calls, baseline_valid = traversal(False)
    treatment_calls, treatment_valid = traversal(True)
    if baseline_valid != treatment_valid:
        raise RuntimeError("candidate occurrence/order mismatch")
    source = pathlib.Path(__file__).read_bytes()
    receipt = {
        "schema": "arc2-prefix-viability-cpu-language-experiment/1",
        "status": "PASS_INVENTED_LANGUAGE_FIXTURES_ONLY",
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "exhaustive_paths": cases,
        "accepted_occurrences": accepted,
        "irreparable_paths": irreparable,
        "edge_controls": len(edges),
        "baseline_synthetic_nonterminal_expansions": baseline_calls,
        "treatment_synthetic_nonterminal_expansions": treatment_calls,
        "accepted_occurrences_identical": baseline_valid == treatment_valid,
        "invented_path_cost_and_grid_seal_sha256": digest.hexdigest(),
        "cpu_seconds": time.process_time()-started_cpu,
        "wall_seconds": time.monotonic()-started_wall,
        "official_tasks_used": 0,
        "model_calls": 0,
        "foreign_imports": 0,
        "candidate_grid_gain": None,
        "gpu_speedup": None,
        "official_score": None,
        "qualification_limit": "Original invented token-language parity only; no execution of the foreign parser, native logits, tokenizer, batch/cache semantics, real search savings, accuracy, or scientific/native admission."
    }
    with args.out.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(receipt,sort_keys=True))


if __name__ == "__main__":
    main()
