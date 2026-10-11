# SPDX-License-Identifier: MIT
"""Original native insertion candidate; NOT executed or adopted by this packet.

Consumes an already loaded, same-run trusted decoder. Never loads a model,
pickle, notebook, task program or file. Source and runtime approval are separate.
The coordinator calls this only before its separate development-truth process.
"""
from __future__ import annotations

import copy
from selector_audit import Hold, digest, grid_id, prepare, registration_check, require


def plain_grid(value):
    # Native adapter's narrow ndarray conversion is resolved only when called.
    # Imported code is not used in the CPU invented witness; no numpy needed there.
    if type(value) is list:
        grid = copy.deepcopy(value)
    else:
        import numpy as np
        require(type(value) is np.ndarray and value.ndim == 2 and value.dtype.kind in ("i", "u"),
                "NATIVE_GRID_TYPE")
        grid = value.tolist()
    grid_id(grid)
    return grid


def plain_score(value):
    if type(value) in (int, float):
        return value
    # Numeric scalar conversion is limited to numpy scalar types in the native adapter.
    import numpy as np
    require(isinstance(value, (np.floating, np.integer)), "NATIVE_SCORE_TYPE")
    return float(value)


def normalize(decoded, registration, generation_states):
    ids = registration_check(registration)
    require(type(generation_states) is dict and set(generation_states) == set(ids), "GENERATION_STATE_COVERAGE")
    require(all(state in ("complete", "empty_complete") for state in generation_states.values()), "INCOMPLETE_GENERATION")
    require(type(decoded) is dict and set(decoded).issubset(set(ids)), "UNREGISTERED_NATIVE_QUERY")
    queries = []
    for descriptor in registration["queries"]:
        qid = descriptor["query_id"]
        entries = decoded.get(qid, {})
        require(type(entries) is dict, "NATIVE_POOL_TYPE")
        occurrences = []
        for occurrence_id, sample in entries.items():
            require(type(sample) is dict and type(occurrence_id) is str, "NATIVE_SAMPLE_TYPE")
            views = sample.get("score_aug")
            if type(views) is not list:
                import numpy as np
                require(type(views) is np.ndarray and views.ndim == 1, "NATIVE_AUGMENTATION_TYPE")
                views = views.tolist()
            occurrences.append({"occurrence_id": occurrence_id, "grid": plain_grid(sample["solution"]),
                                "beam_score": plain_score(sample["beam_score"]),
                                "score_aug": [plain_score(x) for x in views],
                                "view_ids": ["recorded_position_%d" % i for i in range(len(views))]})
        require(bool(occurrences) == (generation_states[qid] == "complete"), "EMPTY_STATE_MISMATCH")
        queries.append({"query_id": qid, "descriptor": copy.deepcopy(descriptor),
                        "generation_state": generation_states[qid],
                        "occurrences": occurrences})
    return queries


def capture(decoder, registration, native_kgmon, native_probmul, *, generation_states, run_binding):
    """Return JSON-safe immutable export and seal; caller creates NEW artifacts.

    View positions preserve the native list order; they do not attest the semantic
    augmentation identities. Those require the separately bound source/seed log.
    Empty pool ≠ proof that its query was generated: source/run receipt must bind
    admitted, finished, failed and timed-out inventory separately.
    """
    dataset = getattr(decoder, "dataset", None)
    require(not getattr(dataset, "replies", {}), "TRUTH_ATTACHED_TO_DECODER")
    before = normalize(decoder.decoded_results, registration, generation_states)
    rankings = {"kgmon": decoder.run_selection_algo(native_kgmon),
                "probmul": decoder.run_selection_algo(native_probmul)}
    require(before == normalize(decoder.decoded_results, registration, generation_states), "NATIVE_SELECTOR_MUTATED_POOL")
    queries = copy.deepcopy(before)
    for query in queries:
        qid = query["query_id"]
        native = {name: [grid_id(plain_grid(g)) for g in values.get(qid, [])]
                  for name, values in rankings.items()}
        query["native_rankings"] = native
        query["baseline_submitted_pair"] = native["kgmon"][:2]
    export = {"schema": "matched-candidate-export/2", "registration_sha256": digest(registration),
              "identity": copy.deepcopy(registration["identity"]), "control": copy.deepcopy(registration["control"]),
              "queries": queries, "run_binding": copy.deepcopy(run_binding)}
    # This checks full stable ranking parity, prefix fidelity and complete scope.
    seal = prepare(registration, export)
    return export, seal
