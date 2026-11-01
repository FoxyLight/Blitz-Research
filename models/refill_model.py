"""Original, independent model for the Experiment 03 ordinary-gem subset.

This is a research model, not game code, an emulator, or a complete game clone.
Only non-wild colors 1..7, ordinary kind 0, and barriers kind 4 are supported.
Eligibility and directional permissions are explicit fixture inputs. Pooling,
animation, native result flags, wildcard handling and match-set merging are omitted.
"""
from dataclasses import dataclass, field

DIRECTIONS = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}
# Supporting cells, relative to the source, in native 8-wide index notation.
SUPPORT_PAIRS = {
    'U': ((-10, -9), (-9, -7), (-7, -6), (-16, -24)),
    'R': ((-15, -7), (-7, 9), (9, 17), (2, 3)),
    'D': ((6, 7), (7, 9), (9, 10), (16, 24)),
    'L': ((-17, -9), (-9, 7), (7, 15), (-2, -3)),
}


@dataclass
class Gem:
    color: int
    kind: int = 0
    eligible: bool = True
    scan: bool = True
    entry: set = field(default_factory=lambda: set(DIRECTIONS))
    direct: set = field(default_factory=set)


def match_eligible(gem):
    return gem is not None and gem.kind != 4 and gem.eligible


class Board:
    def __init__(self, rows):
        if len(rows) != 8 or any(len(row) != 8 for row in rows):
            raise ValueError('This comparison model requires an 8 by 8 board')
        self.cells = [[Gem(int(x)) if x not in ('.', None) else None for x in row] for row in rows]

    def get(self, r, c):
        return self.cells[r][c] if 0 <= r < 8 and 0 <= c < 8 else None

    def validate_domain(self):
        for row in self.cells:
            for gem in row:
                if gem and (gem.kind not in (0, 4) or gem.color not in range(1, 8)):
                    raise ValueError('Outside the ordinary-gem model domain')

    def colors(self):
        return [[g.color if g else None for g in row] for row in self.cells]


def collect_runs(board):
    """Return raw horizontal/vertical runs; use only existence for native comparison.

    The first position in each scan uses the native start test (nonzero color,
    kind != 4), which omits the later eligibility predicate. This asymmetry is
    intentional. Wild color 8 and nonzero Board +0x58 overrides are unsupported.
    """
    board.validate_domain()
    result = []
    lines = [[(r, c) for c in range(8)] for r in range(8)]
    lines += [[(r, c) for r in range(8)] for c in range(8)]
    for line in lines:
        run, color = [], None
        for i, position in enumerate(line):
            gem = board.get(*position)
            good = gem is not None and gem.kind != 4 and (i == 0 or gem.eligible)
            if good and gem.color == color:
                run.append(position)
            else:
                if len(run) >= 3:
                    result.append(tuple(run))
                run, color = ([position], gem.color) if good else ([], None)
        if len(run) >= 3:
            result.append(tuple(run))
    return result


def move_exists_geometrically(board, source, direction):
    """Independent geometric interpretation of the ordinary support-pair rule.

    Place the anchor at the adjacent destination and vacate its original cell.
    Check a line of three through that destination. The destination's old color
    does not supply one of the two supporting cells. This is not a full swap
    simulator and intentionally does not require that the destination color differ.
    """
    r, c = source
    anchor = board.get(r, c)
    dr, dc = DIRECTIONS[direction]
    dest = (r + dr, c + dc)
    target = board.get(*dest)
    if not anchor or not anchor.scan or not target or direction not in target.entry:
        return False
    if direction in anchor.direct:
        return True
    for ar, ac in ((1, 0), (0, 1)):
        for start in (-2, -1, 0):
            triple = [(dest[0] + (start + k) * ar, dest[1] + (start + k) * ac) for k in range(3)]
            if source in triple:
                continue
            support = [p for p in triple if p != dest]
            if all(match_eligible(board.get(*p)) and board.get(*p).color == anchor.color for p in support):
                return True
    return False


def find_moves(board):
    board.validate_domain()
    return [(r, c, name) for r in range(8) for c in range(8) for name in DIRECTIONS
            if move_exists_geometrically(board, (r, c), name)]


def find_moves_by_pairs(board):
    """Separate static-pattern oracle for comparison against the geometric model."""
    board.validate_domain()
    result = []
    for r in range(8):
        for c in range(8):
            anchor = board.get(r, c)
            if not anchor or not anchor.scan:
                continue
            for name, (dr, dc) in DIRECTIONS.items():
                target = board.get(r + dr, c + dc)
                if not target or name not in target.entry:
                    continue
                good = name in anchor.direct
                for pair in SUPPORT_PAIRS[name]:
                    # Decode offsets relative to the source, preventing row wrap.
                    coords = []
                    for offset in pair:
                        choices = [(rr, cc) for rr in range(-3, 4) for cc in range(-3, 4)
                                   if rr * 8 + cc == offset]
                        assert len(choices) == 1
                        rr, cc = choices[0]
                        coords.append((r + rr, c + cc))
                    good |= all(match_eligible(board.get(*p)) and board.get(*p).color == anchor.color for p in coords)
                if good:
                    result.append((r, c, name))
    return result


def validate(board, allow_matches):
    if not allow_matches and collect_runs(board):
        return {'accepted': False, 'reason': 'immediate_match', 'move_check': False}
    if not find_moves(board):
        return {'accepted': False, 'reason': 'no_moves', 'move_check': True}
    return {'accepted': True, 'reason': 'accepted', 'move_check': True}


class ScriptedIndices:
    """Deterministic fixture inputs, with no attempt to reproduce the game's PRNG."""
    def __init__(self, values):
        self.values = iter(values)
        self.calls = []

    def index(self, n):
        if n <= 0:
            raise ValueError('Empty random-index domain is outside the model')
        value = next(self.values)
        if not 0 <= value < n:
            raise ValueError('Scripted RNG index outside bounds; native endpoint behavior is not modeled')
        self.calls.append({'upper': n, 'index': value})
        return value


def spawn(board, replacements, palette, rng, allow_matches=False, keep_bulk=False, budget=4, pending=False, board_palette=None):
    """Model the control flow after replacement objects have been created.

    Palette is the active configuration palette; board_palette can supply the
    separately cached palette used for bulk assignment. Fixture replacement
    cells must already contain reset/preset gems. The budget
    belongs only to this harness; reaching it is NOT a native failure/return.
    """
    board.validate_domain()
    if any(c not in range(1, 8) for c in palette):
        raise ValueError('Unsupported palette color')
    cached_palette = palette if board_palette is None else board_palette
    if any(c not in range(1, 8) for c in cached_palette):
        raise ValueError('Unsupported cached palette color')
    if len(set(map(tuple, replacements))) != len(replacements):
        raise ValueError('Duplicate replacement coordinate')
    if any(board.get(*p) is None for p in replacements):
        raise ValueError('Replacement objects must be supplied by the fixture')
    attempts = []
    def result(status, accepted=None):
        return {'status': status, 'accepted': accepted, 'attempts': attempts,
                'draws': len(rng.calls), 'replacement_colors': [board.get(*p).color for p in replacements]}
    if pending:
        return result('deferred')
    if not replacements:
        return result('no_replacements')
    if len(replacements) == 1:
        options = list(palette)
        for i in range(len(options)):
            j = rng.index(len(options))
            options[i], options[j] = options[j], options[i]
        for color in options:
            board.get(*replacements[0]).color = color
            verdict = validate(board, allow_matches)
            attempts.append({'colors': [color], **verdict})
            if verdict['accepted']:
                return result('accepted', True)
        return result('candidate_exhausted', False if attempts else None)
    for _ in range(budget):
        if not keep_bulk:
            for p in replacements:
                board.get(*p).color = cached_palette[rng.index(len(cached_palette))]
        verdict = validate(board, allow_matches)
        attempts.append({'colors': [board.get(*p).color for p in replacements], **verdict})
        if verdict['accepted']:
            return result('accepted', True)
    return result('model_budget_reached', None)
