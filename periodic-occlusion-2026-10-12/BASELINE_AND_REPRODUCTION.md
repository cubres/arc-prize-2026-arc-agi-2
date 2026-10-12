# Reproduce with the included exact baseline

The owned corrected37 baseline is included at [`baseline37/program_search.py`](baseline37/program_search.py). Its SHA256 is **`52141a1eb17b5d33b2c528f8571b16eef9f4e784f7a8873d3f62f59f31d1c2cf`**, exactly the source used in both measured periodic comparisons. This removes the original recipe's dependency on a separately available baseline file.

From the repository's `periodic-occlusion-2026-10-12/` directory, on Unix with Python 3.10+:

```sh
python3 -m pip install -r requirements.txt
python3 -B -m unittest discover -s baseline37 -p test_program_search.py -v
python3 -B baseline37/run_solver.py --example --max-depth 0

python3 -B reproduce.py prepare --arm background --baseline ./baseline37/program_search.py --work ./my-background-run
nice -n 5 python3 -B reproduce.py predict --arm background --work ./my-background-run
python3 -B reproduce.py evaluate --arm background --work ./my-background-run
```

For the first experiment, replace `--arm background` with `--arm strict` and choose a different fresh work directory. Preparation rejects a baseline whose exact source hash differs. Source/panel freezing precedes data downloads; the prediction worker gets demonstrations and query inputs, seals predictions, and does not open held answers. Existing output directories/files remain preserved. Run without Python `-O`, which the reproduction adapter explicitly rejects.

The full results are documented in [the experiment guide](README.md): no natural activation and no gain in either the 200-task or 400-task comparison. The baseline control measures one complete joint candidate against every task query, so its endpoint can be stricter than a per-query competition score.

## What is included and verified

The baseline, its preceding reference, the CLI and eight meaningful semantic controls are preserved byte-for-byte from the owned original component. The reference is present solely to reproduce the identity-color regression checks; `reproduce.py` uses the corrected baseline. The controls cover unseen query colors, unsupported learned recolorings, observational query-state deduplication, invalid grids, query-output rejection, candidate limits and input immutability. All eight ran successfully in this additive layout, and the CLI's invented identity example ran successfully.

These are **synthetic mechanism checks**, separate from the actual 600 public-training comparisons. Adding the missing baseline did not rerun those comparisons or create native/official score evidence. The publication adapter's separate staged invented smoke test also used this included exact baseline successfully; its full 600-task reproduction remains unexecuted.

The software is original campaign code under the component's [MIT license](baseline37/LICENSE). Source hashes and ownership/provenance are in [BASELINE_PROVENANCE.json](BASELINE_PROVENANCE.json); validation is in [BASELINE_VALIDATION.json](BASELINE_VALIDATION.json). NumPy and Requests retain their own licenses. No puzzle files, query answers, model weights, private neural code or notebooks are included in the baseline addition.
