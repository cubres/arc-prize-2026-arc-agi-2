"""Portable offline candidate CLI. Synthetic example; no official task bundle."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from program_search import grid, solve


def example():
    return {"train": [{"input": [[1, 2], [0, 1]],
                       "output": [[1, 2], [0, 1]]}],
            "test": [{"input": [[9, 2], [0, 9]]}]}


def challenge_only(value):
    if type(value) is not dict or set(value) != {"train", "test"}:
        raise ValueError("a single challenge needs train and test only")
    for name, keys in (("train", {"input", "output"}), ("test", {"input"})):
        rows = value[name]
        if type(rows) is not list or not 1 <= len(rows) <= 16:
            raise ValueError("one through sixteen demonstration or query records required")
        for row in rows:
            if type(row) is not dict or set(row) != keys:
                raise ValueError("query output fields and unknown record fields are forbidden")
            for field in keys:
                grid(row[field])
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--example", action="store_true")
    modes.add_argument("--challenge", type=Path)
    parser.add_argument("--seconds", type=float, default=1.8)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--beam", type=int, default=96)
    parser.add_argument("--state-cap", type=int, default=10000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not 0 < args.seconds <= 60 or not 0 <= args.max_depth <= 3:
        parser.error("seconds must be in (0,60] and depth in [0,3]")
    if not 1 <= args.beam <= 1000 or not 1 <= args.state_cap <= 100000:
        parser.error("beam and state cap must be bounded positive integers")
    if args.example:
        value = example()
    else:
        if args.challenge.suffix != ".json" or args.challenge.stat().st_size > 2 * 1024**2:
            parser.error("a bounded challenge JSON file is required")
        value = json.loads(args.challenge.read_text())
    if args.output is not None and args.output.suffix != ".json":
        parser.error("an exclusive JSON output file is required")
    value = challenge_only(value)
    result = solve(value, seconds=args.seconds, max_depth=args.max_depth,
                   beam=args.beam, state_cap=args.state_cap)
    payload = json.dumps({"status": "SOLVER_CANDIDATES_ONLY", "synthetic_example": args.example,
                          "official_score": None, "result": result}, sort_keys=True, indent=2) + "\n"
    if args.output is None:
        sys.stdout.write(payload)
    else:
        with args.output.open("x") as handle:
            handle.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
