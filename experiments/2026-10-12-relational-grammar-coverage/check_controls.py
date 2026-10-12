"""Run only the thirteen invented controls against the byte-pinned source.

No benchmark file is accepted or read. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import time


def main():
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("relational_driver", here / "run_relational_eval.py")
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.protocol(here / "PROTOCOL.json")
    _, structural, controls = driver.load_solvers()
    started = time.process_time()
    result = controls.run(structural)
    print(json.dumps({"status": result["status"], "invented_controls": len(result["controls"]),
                      "direct_semantics_pass": result["direct_semantics_pass"],
                      "prediction_storage_independence_pass": result["prediction_storage_independence_pass"],
                      "elapsed_cpu_seconds": time.process_time() - started,
                      "benchmark_run": False, "quality_claim": False}, sort_keys=True))


if __name__ == "__main__":
    main()
