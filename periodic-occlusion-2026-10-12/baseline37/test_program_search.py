"""Original synthetic semantic regressions; no downloaded ARC task is included."""
import unittest
import numpy as np
import program_search as corrected
import reference_program_search as reference
from run_solver import challenge_only, example


class SolverSemantics(unittest.TestCase):
    def test_frozen_grammar_has_thirty_seven_unique_names(self):
        names = [name for name, _ in corrected.operations()]
        self.assertEqual(len(names), 37)
        self.assertEqual(len(set(names)), 37)
        self.assertEqual(names, [name for name, _ in reference.operations()])

    def test_identity_preserves_unseen_query_colors(self):
        task = example()
        new = corrected.solve(task, max_depth=0)
        old = reference.solve(task, max_depth=0)
        self.assertEqual(new["expanded"][0]["grids"], [task["test"][0]["input"]])
        self.assertEqual(new["expanded"][0]["program"], [])
        self.assertEqual(old["expanded"], [])

    def test_nonidentity_recoloring_refuses_unseen_query_key(self):
        task = {"train": [{"input": [[1, 0]], "output": [[2, 0]]}],
                "test": [{"input": [[9, 0]]}]}
        self.assertEqual(corrected.solve(task, max_depth=0)["expanded"], [])

    def test_nonidentity_recoloring_accepts_demonstrated_query_keys(self):
        task = {"train": [{"input": [[1, 0]], "output": [[2, 0]]}],
                "test": [{"input": [[0, 1]]}]}
        self.assertEqual(corrected.solve(task, max_depth=0)["expanded"][0]["grids"], [[[0, 2]]])

    def test_deduplication_observes_query_input(self):
        demonstration = corrected.grid([[1, 0]])
        a = corrected.signature((demonstration, corrected.grid([[9, 0]])))
        b = corrected.signature((demonstration, corrected.grid([[0, 9]])))
        self.assertNotEqual(a, b)

    def test_invalid_grid_contract(self):
        for value in ([[1.0]], [[10]], [[-1]], [[]], [1, 2], [[True]]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    corrected.grid(value)

    def test_cli_challenge_rejects_query_outputs(self):
        value = example()
        value["test"][0]["output"] = [[9, 2], [0, 9]]
        with self.assertRaises(ValueError):
            challenge_only(value)

    def test_candidate_limit_and_input_immutability(self):
        value = example()
        before = repr(value)
        result = corrected.solve(value, max_depth=1)
        self.assertLessEqual(len(result["expanded"]), 2)
        self.assertEqual(repr(value), before)


if __name__ == "__main__":
    unittest.main()
