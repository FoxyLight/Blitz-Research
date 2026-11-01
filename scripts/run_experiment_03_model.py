#!/usr/bin/env python3
"""Run original hand-authored model fixtures. Does not accept a game binary."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from models.refill_model import Board, ScriptedIndices, collect_runs, find_moves, find_moves_by_pairs, validate, spawn, move_exists_geometrically


def run():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixtures', type=Path, default=ROOT / 'tests/fixtures/experiment-03-boards.json')
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    spec = json.loads(args.fixtures.read_text(encoding='utf-8'))
    results = []

    def same_moves(board):
        assert set(find_moves(board)) == set(find_moves_by_pairs(board)), 'Geometric and support-pair models disagree'

    def check(case_id, expected, actual):
        mismatches = {k: {'expected': v, 'actual': actual.get(k)} for k, v in expected.items() if actual.get(k) != v}
        results.append({'id': case_id, 'pass': not mismatches, 'expected': expected, 'actual': actual, 'mismatches': mismatches})

    def make(case):
        board = Board(spec['boards'][case.get('board', 'quiet')])
        for edit in case.get('edits', []):
            gem = board.get(*edit['at'])
            for key, value in edit.items():
                if key != 'at':
                    setattr(gem, key, set(value) if key in ('direct', 'entry') else value)
        return board

    for case in spec['cases']:
        board = make(case)
        same_moves(board)
        op = case['op']
        if op == 'inspect':
            actual = {'has_match': bool(collect_runs(board)), 'has_move': bool(find_moves(board))}
        elif op == 'validate':
            actual = validate(board, case.get('allow_matches', False))
        elif op == 'move':
            actual = {'move': move_exists_geometrically(board, tuple(case['source']), case['direction'])}
        elif op == 'spawn':
            actual = spawn(board, case['replacements'], case['palette'], ScriptedIndices(case['indices']),
                           allow_matches=case.get('allow_matches', False), keep_bulk=case.get('keep_bulk', False),
                           budget=case.get('budget', 4), pending=case.get('pending', False), board_palette=case.get('board_palette'))
            actual['attempt_count'] = len(actual['attempts'])
            actual['reasons'] = [a['reason'] for a in actual['attempts']]
            same_moves(board)
        else:
            raise ValueError(op)
        check(case['id'], case['expected'], actual)

    for case in spec['support_cases']:
        board = Board(spec['boards']['quiet'])
        # Isolate this support pair: no incidental third color-7 supporter.
        for row in board.cells:
            for gem in row:
                if gem and gem.color == 7:
                    gem.color = 6
        for coord in [(3, 3), *case['support']]:
            board.get(*coord).color = 7
        same_moves(board)
        actual = {'move': move_exists_geometrically(board, (3, 3), case['direction'])}
        for index, coord in enumerate(case['support']):
            board.get(*coord).eligible = False
            same_moves(board)
            actual[f'without_support_{index}'] = move_exists_geometrically(board, (3, 3), case['direction'])
            board.get(*coord).eligible = True
        check(case['id'], {'move': True, 'without_support_0': False, 'without_support_1': False}, actual)

    # Original negative-domain cases keep unsupported native rules explicit.
    for label, edit in [('wild_color_outside_model', {'color': 8}), ('type5_outside_model', {'kind': 5})]:
        board = Board(spec['boards']['quiet'])
        for k, v in edit.items():
            setattr(board.get(0, 0), k, v)
        rejected = False
        try:
            find_moves(board)
        except ValueError:
            rejected = True
        check(label, {'rejected': True}, {'rejected': rejected})
    endpoint_rejected = False
    try:
        ScriptedIndices([2]).index(2)
    except ValueError:
        endpoint_rejected = True
    check('out_of_range_rng_index_outside_model', {'rejected': True}, {'rejected': endpoint_rejected})

    passed = sum(x['pass'] for x in results)
    report = {'status': 'PASS' if passed == len(results) else 'FAIL', 'python': sys.version.split()[0],
              'fixtures_sha256': hashlib.sha256(args.fixtures.read_bytes()).hexdigest(),
              'model_sha256': hashlib.sha256((ROOT / 'models/refill_model.py').read_bytes()).hexdigest(),
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'cases_passed': passed, 'cases_total': len(results),
              'comparison': 'Two independently written ordinary-gem geometric/pattern models, checked on every fixture; no native execution or runtime comparison',
              'limits': 'Model budget termination is a harness boundary, not a native return. Special types, wildcard 8, pool/state side effects and override masks are outside the model.',
              'results': results}
    if args.report:
        if args.report.resolve() in (args.fixtures.resolve(), (ROOT / 'models/refill_model.py').resolve()):
            raise ValueError('Cannot overwrite input')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    for result in results:
        if not result['pass']:
            print('FAIL', result['id'], result['mismatches'])
    print(f"{report['status']}: {passed}/{len(results)} original model cases")
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    raise SystemExit(run())
