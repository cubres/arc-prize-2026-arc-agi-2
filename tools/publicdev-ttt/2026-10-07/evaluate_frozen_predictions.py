# SPDX-License-Identifier: Apache-2.0
"""Separate-process evaluation of fully frozen public-development predictions.

The public solution file is opened only after the complete freeze gate. No
solution grid, cell, dimensions or alternate task is written to this report.
Never import or call this evaluator from the training/prompt/selection process.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from grid_tokens import validate_grid
from prediction_contract import (TASK_ID, canonical_json, digest, read_bound, require,
                                 verify_frozen_predictions, write_frozen)


def compare_one_query(manifest, truth):
    """Pure comparison; synthetic fixtures may call this without any solution I/O."""
    truth = validate_grid(truth)
    rows = [{"stage":record["stage"], "attempt":record["attempt"],
             "transform":record["transform"], "valid_grid":record["parse"]["valid"],
             "parse_error":record["parse"]["error_code"],
             "exact_match":bool(record["parse"]["valid"] and record["parse"]["base_grid"] == truth)}
            for record in manifest["attempts"]]
    return {"attempt_results":rows,
            "before_any_exact":any(row["exact_match"] for row in rows if row["stage"] == "before"),
            "after_any_exact":any(row["exact_match"] for row in rows if row["stage"] == "after")}


def evaluate(output_dir, protocol_sha256, manifest_sha256, source_dir, solutions_path):
    # IMPORTANT: no access to solutions_path, even stat/resolve, above this gate.
    protocol, manifest = verify_frozen_predictions(output_dir, protocol_sha256, manifest_sha256, source_dir)
    solutions_path = Path(solutions_path)
    require(solutions_path.name == protocol["solution_basename"], "only the public evaluation solutions file is allowed")
    solutions_raw = read_bound(solutions_path)
    solutions = json.loads(solutions_raw)
    require(type(solutions) is dict and TASK_ID in solutions, "preregistered public task is absent")
    task_answers = solutions[TASK_ID]
    require(type(task_answers) is list and len(task_answers) > protocol["test_index"], "public test answer absent")
    compared = compare_one_query(manifest, task_answers[protocol["test_index"]])
    return {"schema":"arc2-publicdev-evaluation-v1", "task_id":TASK_ID, "test_index":0,
            "protocol_sha256":protocol_sha256, "prediction_manifest_sha256":manifest_sha256,
            "solutions_sha256_after_freeze":digest(solutions_raw),
            "prediction_freeze_verified_before_solutions_read":True,
            "prior_public_training_pair_exposure":True,
            "ground_truth_written_to_report":False,
            "scope":"One preregistered public development query; no benchmark or hidden evaluation inference",
            **compared}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--public-solutions', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.output_dir, args.protocol_sha256, args.manifest_sha256,
                      args.source_dir, args.public_solutions)
    seal = write_frozen(args.receipt, canonical_json(report))
    print(json.dumps({'status':'PUBLIC_DEVELOPMENT_COMPARISON_ONLY',
                      'before_any_exact':report['before_any_exact'], 'after_any_exact':report['after_any_exact'],
                      'receipt_sha256':seal['sha256'], 'ground_truth_printed':False}, sort_keys=True))


if __name__ == '__main__':
    main()
