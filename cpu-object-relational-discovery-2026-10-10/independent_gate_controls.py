"""Invented object-DSL safety controls; no benchmark data or task identifiers."""
from types import SimpleNamespace


def run_controls(dsl):
    checks = []
    def check(name, condition):
        if not condition:
            raise RuntimeError(name)
        checks.append(name)

    check('unique-mode background tie abstains', dsl.background(((1, 2),), 'unique_mode') is None)
    check('finite grammar has 5248 programs per segmentation', sum(1 for _ in dsl.programs()) == 5248)
    train_grid = [[0] * 5 for _ in range(5)]
    train_grid[2][2] = 1
    train = [{'input': train_grid, 'output': [[1]]} for _ in range(2)]
    ambiguous = [[0] * 5 for _ in range(5)]
    ambiguous[0][0] = 2
    ambiguous[4][2] = 3
    ambiguous[2][4] = 4
    result = dsl.solve_task({'train': train, 'test': [{'input': ambiguous}]})
    check('three distinct fitted bundles abstain completely',
          result['distinct_bundles'] == 3 and result['attempts'] == [[]]
          and result['chosen_programs'] == [] and not result['timed_out']
          and result['abstention'] == 'More than two fitted test bundles')

    # Deliberately simulate budget expiry at the first object extraction check.
    # This tests fail-closed control flow without burning real CPU time.
    original_time = dsl.time
    calls = [0]
    def expired_cpu_clock():
        calls[0] += 1
        return 0.0 if calls[0] == 1 else 2.0
    dsl.time = SimpleNamespace(process_time=expired_cpu_clock, monotonic=lambda: 0.0)
    try:
        timed = dsl.solve_task({'train': train, 'test': [{'input': train_grid}]})
    finally:
        dsl.time = original_time
    check('simulated incomplete search abstains completely',
          timed['timed_out'] and timed['abstention'] == 'Incomplete grammar search'
          and timed['attempts'] == [[]] and timed['chosen_programs'] == [])
    return {'status': 'PASS', 'checks': checks,
            'ambiguity_control': {'distinct_bundles': result['distinct_bundles'],
                                  'attempts': result['attempts'],
                                  'abstention': result['abstention']},
            'incomplete_search_control': {'clock_is_simulated': True,
                                         'timed_out': timed['timed_out'],
                                         'attempts': timed['attempts'],
                                         'abstention': timed['abstention']},
            'limits': ['Invented control cases verify mechanics only.',
                       'Simulated clock checks timeout control flow, not hard wall-clock enforcement.']}
