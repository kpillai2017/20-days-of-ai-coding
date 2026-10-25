"""Readable chess rules/search inspired by Richard Allbert's VICE tutorials.

Original Python rewrite of standard chess-engine techniques, not a line-for-line
C port. Upstream: bluefeversoft/vice, Vice11/src (MIT, copyright 2022
bluefeversoft). See VICE_LICENSE.txt and SOURCE_NOTES.md for attribution.

We use 64 squares (a1=0, h8=63), uppercase White, lowercase Black, '.' empty.
Only this file knows chess; it never imports Pygame or opens a window.
"""

from dataclasses import dataclass
import copy
import math
import time

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# Offsets are (file change, rank change). Explicit bounds prevent h-file wrap.
KNIGHT = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
DIAGONAL = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
STRAIGHT = [(1, 0), (-1, 0), (0, 1), (0, -1)]
KING = DIAGONAL + STRAIGHT
# Evaluation uses centipawns: a pawn is approximately 100, not a rule value.
VALUES = {"p": 100, "n": 320, "b": 335, "r": 500, "q": 900, "k": 0, ".": 0}
MATE = 100000


def sq_to_notation(sq):
    """Convert a validated list index into a human square name, e.g. 28 -> e4."""
    if type(sq) is not int or not 0 <= sq < 64:
        raise ValueError("Square must be an integer from 0 to 63")
    return "abcdefgh"[sq % 8] + str(sq // 8 + 1)


def notation_to_sq(text):
    """Convert an exact a1–h8 coordinate into the 0–63 board index."""
    if (
        not isinstance(text, str)
        or len(text) != 2
        or text[0] not in "abcdefgh"
        or text[1] not in "12345678"
    ):
        raise ValueError("Use a square such as e4")
    return "abcdefgh".index(text[0]) + (int(text[1]) - 1) * 8


def color(piece):
    """Return w/b for a piece letter, or None for an empty square."""
    return None if piece == "." else "w" if piece.isupper() else "b"


def other(side):
    """Swap the side code; search and move generation use this constantly."""
    return "b" if side == "w" else "w"


@dataclass(frozen=True)
class Move:
    """Describe one move without editing a board. Frozen records cannot be changed accidentally."""

    from_sq: int
    to_sq: int
    promotion: str = ""
    en_passant: bool = False
    castle: bool = False

    def uci(self):
        """Write coordinate notation; a promotion adds its lowercase piece letter."""
        return (
            sq_to_notation(self.from_sq) + sq_to_notation(self.to_sq) + self.promotion
        )


class Position:
    """Board plus all state needed to distinguish positions and undo moves.

    Full-board snapshots are deliberately simpler than VICE's incremental
    piece lists/hashes. It costs some speed but makes special-move undo clear.
    push() is an internal primitive: callers choose a move from legal_moves().
    """

    def __init__(self, fen=START_FEN):
        """Read a FEN snapshot, validate its fields, and start independent undo/repetition history.

        FEN ranks arrive from rank eight downward; our list starts at a1. Validation
        checks structure and special metadata, not full historical reachability."""
        if not isinstance(fen, str) or len(fen.split()) != 6:
            raise ValueError("FEN needs six fields")
        layout, self.side, rights, ep, half, full = fen.split()
        ranks = layout.split("/")
        if len(ranks) != 8 or self.side not in ("w", "b"):
            raise ValueError("Invalid ranks or side in FEN")
        self.board = ["."] * 64
        # Expand FEN top-to-bottom, but place rows bottom-to-top in the list.
        for index, row in enumerate(ranks):
            expanded = []
            for char in row:
                if char in "12345678":
                    expanded.extend("." * int(char))
                elif char in "PNBRQKpnbrqk":
                    expanded.append(char)
                else:
                    raise ValueError("Invalid FEN piece or empty-square count")
            if len(expanded) != 8:
                raise ValueError("Each FEN rank must describe eight squares")
            self.board[(7 - index) * 8 : (8 - index) * 8] = expanded
        if self.board.count("K") != 1 or self.board.count("k") != 1:
            raise ValueError("Exactly one king of each colour is required")
        wk, bk = self.board.index("K"), self.board.index("k")
        if max(abs(wk % 8 - bk % 8), abs(wk // 8 - bk // 8)) <= 1:
            raise ValueError("Kings may not be adjacent")
        if any(
            self.board[s].lower() == "p" for s in list(range(8)) + list(range(56, 64))
        ):
            raise ValueError("Unpromoted pawn on the last rank")
        if rights != "-" and (
            any(c not in "KQkq" for c in rights) or len(set(rights)) != len(rights)
        ):
            raise ValueError("Invalid castling rights")
        self.castling = "".join(c for c in "KQkq" if c in rights)
        for right, king, rook, ks, rs in [
            ("K", "K", "R", 4, 7),
            ("Q", "K", "R", 4, 0),
            ("k", "k", "r", 60, 63),
            ("q", "k", "r", 60, 56),
        ]:
            if right in self.castling and (
                self.board[ks] != king or self.board[rs] != rook
            ):
                raise ValueError("Castling rights require home king and rook")
        self.ep = None if ep == "-" else notation_to_sq(ep)
        if self.ep is not None:
            rank = 5 if self.side == "w" else 2
            pawn_sq = self.ep - 8 if self.side == "w" else self.ep + 8
            if (
                self.ep // 8 != rank
                or self.board[self.ep] != "."
                or self.board[pawn_sq] != ("p" if self.side == "w" else "P")
            ):
                raise ValueError(
                    "Invalid en-passant target or missing double-moved pawn"
                )
        try:
            self.halfmove, self.fullmove = int(half), int(full)
        except ValueError as exc:
            raise ValueError("Invalid FEN counters") from exc
        if self.halfmove < 0 or self.fullmove < 1:
            raise ValueError("Invalid FEN counters")
        # Undo snapshots and repetition keys are separate: probes need undo,
        # but a hypothetical legality test must not count as a played position.
        self.history = []
        self.keys = [self.key()]

    @classmethod
    def from_fen(cls, fen=START_FEN):
        """Convenience constructor: a named alternative to Position(fen)."""
        return cls(fen)

    def fen(self):
        """Serialise board and rule metadata, compressing consecutive blanks as digits."""
        rows = []
        for rank in range(7, -1, -1):
            row = ""
            empty = 0
            for piece in self.board[rank * 8 : rank * 8 + 8]:
                if piece == ".":
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    row += piece
            if empty:
                row += str(empty)
            rows.append(row)
        return f"{'/'.join(rows)} {self.side} {self.castling or '-'} {sq_to_notation(self.ep) if self.ep is not None else '-'} {self.halfmove} {self.fullmove}"

    def clone(self):
        """Deep-copy board AND history before a background search can change anything."""
        return copy.deepcopy(self)

    def is_attacked(self, square, by_side):
        """Attack maps are not legal moves: pinned pieces still attack squares."""
        file, rank = square % 8, square // 8
        pawn = "P" if by_side == "w" else "p"
        # Work backward from the attacked square to potential pawn origins.
        source_rank = rank - 1 if by_side == "w" else rank + 1
        if 0 <= source_rank < 8:
            for f in (file - 1, file + 1):
                if 0 <= f < 8 and self.board[source_rank * 8 + f] == pawn:
                    return True
        for dx, dy in KNIGHT:
            f, r = file + dx, rank + dy
            if 0 <= f < 8 and 0 <= r < 8:
                p = self.board[r * 8 + f]
                if p.lower() == "n" and color(p) == by_side:
                    return True
        # Scan eight rays: the FIRST occupied square blocks everything behind.
        for dx, dy in KING:
            f, r = file + dx, rank + dy
            distance = 1
            while 0 <= f < 8 and 0 <= r < 8:
                p = self.board[r * 8 + f]
                if p != ".":
                    if color(p) == by_side:
                        types = "bq" if dx and dy else "rq"
                        if p.lower() in types or (distance == 1 and p.lower() == "k"):
                            return True
                    break
                f += dx
                r += dy
                distance += 1
        return False

    def in_check(self, side=None):
        """Ask whether this side's king square is attacked; default to the current turn."""
        side = side or self.side
        king = "K" if side == "w" else "k"
        return self.is_attacked(self.board.index(king), other(side))

    def pseudo_moves(self):
        """Yield movement/occupancy candidates before filtering exposed kings.

        Pawn movement, promotions and castling need separate branches. A generator
        yields one Move at a time; it does not build a list or play that move."""
        for square, piece in enumerate(self.board):
            if color(piece) != self.side:
                continue
            f, r = square % 8, square // 8
            kind = piece.lower()
            if kind == "p":
                step = 1 if self.side == "w" else -1
                home = 1 if self.side == "w" else 6
                last = 7 if self.side == "w" else 0
                nr = r + step
                if not 0 <= nr < 8:
                    continue
                to = nr * 8 + f
                # A pawn advances only into an empty square, unlike its capture.
                if self.board[to] == ".":
                    for promotion in ("q", "r", "b", "n") if nr == last else ("",):
                        yield Move(square, to, promotion)
                    # The single-step square was already tested above. Both
                    # squares must be free for a starting double-step.
                    if r == home and self.board[(r + 2 * step) * 8 + f] == ".":
                        yield Move(square, (r + 2 * step) * 8 + f)
                for nf in (f - 1, f + 1):
                    if not 0 <= nf < 8:
                        continue
                    to = nr * 8 + nf
                    target = self.board[to]
                    if color(target) == other(self.side) and target.lower() != "k":
                        for promotion in ("q", "r", "b", "n") if nr == last else ("",):
                            yield Move(square, to, promotion)
                    elif to == self.ep and target == ".":
                        captured = self.board[to - step * 8]
                        if captured == ("p" if self.side == "w" else "P"):
                            yield Move(square, to, en_passant=True)
                continue
            directions = (
                KNIGHT
                if kind == "n"
                else KING if kind in "kq" else DIAGONAL if kind == "b" else STRAIGHT
            )
            for dx, dy in directions:
                nf, nr = f + dx, r + dy
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = self.board[to]
                    if color(target) == self.side:
                        break
                    if target.lower() != "k":
                        yield Move(square, to)
                    if target != "." or kind in "nk":
                        break
                    nf += dx
                    nr += dy
            if kind == "k":
                home = 4 if self.side == "w" else 60
                if square != home or self.in_check():
                    continue
                for right, rook, to, between, transit in (
                    (
                        "K" if self.side == "w" else "k",
                        home + 3,
                        home + 2,
                        (home + 1, home + 2),
                        (home + 1, home + 2),
                    ),
                    (
                        "Q" if self.side == "w" else "q",
                        home - 4,
                        home - 2,
                        (home - 1, home - 2, home - 3),
                        (home - 1, home - 2),
                    ),
                ):
                    if right in self.castling and self.board[rook] == (
                        "R" if self.side == "w" else "r"
                    ):
                        if all(self.board[s] == "." for s in between) and all(
                            not self.is_attacked(s, other(self.side)) for s in transit
                        ):
                            yield Move(square, to, castle=True)

    def legal_moves(self):
        """Return only candidate moves that leave the mover's own king safe.

        Remember the original side before push swaps the turn. Temporary
        probes need full undo, but must not enter the repetition history.
        """
        legal = []
        side = self.side
        # Materialise before push: a generator reading a changed board is subtle.
        for move in list(self.pseudo_moves()):
            self.push(move, record=False)
            try:
                if not self.in_check(side):
                    legal.append(move)
            finally:
                self.pop()
        return legal

    def key(self):
        """Repetition ignores a ghost en-passant square nobody can legally use.

        Test EP with temporary board edits, not push/key recursion. A pinned EP
        pawn cannot capture legally, so it must not distinguish repetitions.
        """
        usable_ep = None
        if self.ep is not None:
            to = self.ep
            step = 8 if self.side == "w" else -8
            for start in (to - step - 1, to - step + 1):
                if (
                    0 <= start < 64
                    and abs(start % 8 - to % 8) == 1
                    and self.board[start] == ("P" if self.side == "w" else "p")
                ):
                    captured = to - step
                    saved = (self.board[start], self.board[to], self.board[captured])
                    self.board[to] = self.board[start]
                    self.board[start] = "."
                    self.board[captured] = "."
                    try:
                        if not self.in_check():
                            usable_ep = to
                    finally:
                        self.board[start], self.board[to], self.board[captured] = saved
                    if usable_ep is not None:
                        break
        return (tuple(self.board), self.side, self.castling, usable_ep)

    def push(self, move, record=True):
        """Apply a trusted move, saving everything pop needs to restore.

        This is not the public legality checker: UI/search callers use legal_moves.
        record=False is for temporary probes, which must not count as repetitions."""
        self.history.append(
            (
                self.board[:],
                self.side,
                self.castling,
                self.ep,
                self.halfmove,
                self.fullmove,
                record,
            )
        )
        # Read the original piece/victim BEFORE overwriting either square.
        piece = self.board[move.from_sq]
        capture = self.board[move.to_sq]
        self.board[move.from_sq] = "."
        self.board[move.to_sq] = (
            (move.promotion.upper() if self.side == "w" else move.promotion)
            if move.promotion
            else piece
        )
        if move.en_passant:
            self.board[move.to_sq + (-8 if self.side == "w" else 8)] = "."
        if move.castle:
            rook_from = move.from_sq + (3 if move.to_sq > move.from_sq else -4)
            rook_to = (move.from_sq + move.to_sq) // 2
            self.board[rook_to] = self.board[rook_from]
            self.board[rook_from] = "."
        # Moving a home king/rook OR capturing a home rook loses those rights.
        for square, rights in [
            (4, "KQ"),
            (60, "kq"),
            (0, "Q"),
            (7, "K"),
            (56, "q"),
            (63, "k"),
        ]:
            if square in (move.from_sq, move.to_sq):
                for right in rights:
                    self.castling = self.castling.replace(right, "")
        # EP lasts for exactly the next turn; all other moves clear the target.
        self.ep = (
            (move.from_sq + move.to_sq) // 2
            if piece.lower() == "p" and abs(move.to_sq - move.from_sq) == 16
            else None
        )
        # The fifty-move counter counts PLIES since the last pawn move/capture.
        self.halfmove = (
            0
            if piece.lower() == "p" or capture != "." or move.en_passant
            else self.halfmove + 1
        )
        if self.side == "b":
            self.fullmove += 1
        self.side = other(self.side)
        if record:
            self.keys.append(self.key())

    def pop(self):
        """Undo the last push, including clocks, special rights and optional repetition entry."""
        if not self.history:
            raise ValueError("No move to undo")
        (
            board,
            self.side,
            self.castling,
            self.ep,
            self.halfmove,
            self.fullmove,
            record,
        ) = self.history.pop()
        self.board = board
        if record:
            self.keys.pop()

    def insufficient_material(self):
        """Recognise a conservative subset of material-only dead positions.

        Two knights are deliberately not declared dead: inability to force mate
        is different from impossibility of any legal mating sequence."""
        pieces = [
            (s, p.lower())
            for s, p in enumerate(self.board)
            if p != "." and p.lower() != "k"
        ]
        if not pieces:
            return True
        if len(pieces) == 1 and pieces[0][1] in "bn":
            return True
        if all(p == "b" for _, p in pieces):
            # File+rank parity is the colour of a bishop's square.
            return len({(s % 8 + s // 8) % 2 for s, _ in pieces}) == 1
        return False

    def outcome(self, moves=None):
        """Return a human result message, or None while the game can continue.

        No legal move means mate if checked, otherwise stalemate. Check this before
        draw counters so a mating move is not incorrectly overridden by a draw."""
        moves = self.legal_moves() if moves is None else moves
        if not moves:
            return (
                ("Black" if self.side == "w" else "White") + " wins by checkmate"
                if self.in_check()
                else "Draw: stalemate"
            )
        if self.insufficient_material():
            return "Draw: insufficient material"
        # Friendly-app policy: automatically claim at threefold / 50 moves.
        # Tournament claim-vs-automatic 5-fold/75-move distinctions are omitted.
        if self.halfmove >= 100:
            return "Draw: fifty-move rule (auto-claimed)"
        if self.keys.count(self.key()) >= 3:
            return "Draw: threefold repetition (auto-claimed)"
        return None


def perft(position, depth):
    """Count legal-move leaves; an exact rules regression, not playing strength."""
    if type(depth) is not int or depth < 0:
        raise ValueError("depth must be a nonnegative integer")
    if depth == 0:
        return 1
    moves = position.legal_moves()
    if depth == 1:
        return len(moves)
    count = 0
    for move in moves:
        position.push(move, record=False)
        try:
            count += perft(position, depth - 1)
        finally:
            position.pop()
    return count


def evaluate(position):
    """Centipawns from the SIDE TO MOVE: negamax flips signs at every ply."""
    score = 0
    for square, piece in enumerate(position.board):
        if piece == ".":
            continue
        f, r = square % 8, square // 8
        kind = piece.lower()
        # Manhattan distance from the middle favours central minor pieces.
        centre = 7 - abs(3.5 - f) - abs(3.5 - r)
        bonus = centre * 8 if kind in "nb" else 0
        if kind == "p":
            bonus = (r if piece.isupper() else 7 - r) * 7 + centre * 2
        score += (VALUES[kind] + int(bonus)) * (1 if piece.isupper() else -1)
    return score if position.side == "w" else -score


@dataclass
class SearchResult:
    """Bundle a suggested Move, centipawn score, completed depth and visited-node count."""

    move: object
    score: int
    depth: int
    nodes: int


class SearchStopped(Exception):
    """Internal signal used to unwind recursive search on cancellation or timeout."""

    pass


def search(position, max_depth=3, time_limit=1.5, stop_event=None):
    """VICE-style iterative negamax, alpha-beta and capture quiescence.

    Deadlines are checked INSIDE recursion. Only fully completed iterations
    replace the result; try/finally always restores a made move on interruption.
    """
    if type(max_depth) is not int or not 1 <= max_depth <= 8:
        raise ValueError("depth must be 1..8")
    if (
        not isinstance(time_limit, (int, float))
        or not math.isfinite(time_limit)
        or time_limit <= 0
    ):
        raise ValueError("time limit must be positive and finite")
    # Clone even though recursive moves are undone: callers retain ownership.
    pos = position.clone()
    deadline = time.monotonic() + time_limit
    nodes = 0
    moves = pos.legal_moves()
    if pos.outcome(moves):
        return SearchResult(None, -MATE if not moves and pos.in_check() else 0, 0, 0)
    result = SearchResult(moves[0], evaluate(pos), 0, 0)

    def tick():
        """Count a node and interrupt promptly using monotonic time or the stop Event."""
        nonlocal nodes
        nodes += 1
        if (
            stop_event is not None and stop_event.is_set()
        ) or time.monotonic() >= deadline:
            raise SearchStopped

    def ordered(items):
        """Try promising captures/promotions first to make alpha–beta cutoffs earlier."""

        def value(move):
            """Rank high-value victims above cheap ones; prefer a cheaper capturing piece."""
            victim = "p" if move.en_passant else pos.board[move.to_sq].lower()
            return (
                VALUES[victim] * 10
                - VALUES[pos.board[move.from_sq].lower()]
                + (VALUES.get(move.promotion, 0) if move.promotion else 0)
            )

        return sorted(items, key=value, reverse=True)

    def terminal(items, ply):
        """Return a finished-position score, or None when search should continue."""
        if not items:
            return -MATE + ply if pos.in_check() else 0
        if (
            pos.insufficient_material()
            or pos.halfmove >= 100
            or pos.keys.count(pos.key()) >= 3
        ):
            return 0
        return None

    def quiesce(alpha, beta, ply, qdepth=0):
        """Extend tactical leaves so the evaluation sees likely captures and replies.

        When checked, search ALL evasions; otherwise a side may stand pat and
        only tactical moves are explored. An extension cap bounds checking chains."""
        tick()
        items = pos.legal_moves()
        end = terminal(items, ply)
        if end is not None:
            return end
        checked = pos.in_check()
        stand = evaluate(pos)
        # Bounded extension prevents perpetual checking sequences from recursing
        # forever. Terminal rules above are still checked at the boundary.
        if qdepth >= 8:
            return stand
        # Stand-pat is allowed only when NOT checked: a check needs an evasion.
        if not checked:
            if stand >= beta:
                return beta
            alpha = max(alpha, stand)
            items = [
                m
                for m in items
                if pos.board[m.to_sq] != "." or m.en_passant or m.promotion
            ]
        for move in ordered(items):
            pos.push(move)
            try:
                score = -quiesce(-beta, -alpha, ply + 1, qdepth + 1)
            finally:
                pos.pop()
            # Fail-high: the opponent can already avoid this branch, so stop.
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    def negamax(depth, alpha, beta, ply):
        """Search a bounded number of plies from the side-to-move perspective."""
        if depth <= 0:
            return quiesce(alpha, beta, ply)
        tick()
        items = pos.legal_moves()
        end = terminal(items, ply)
        if end is not None:
            return end
        for move in ordered(items):
            pos.push(move)
            try:
                score = -negamax(depth - 1, -beta, -alpha, ply + 1)
            finally:
                pos.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    # A partial deeper iteration is discarded if time runs out. Keep the last
    # completed answer rather than trusting an incompletely searched root.
    for depth in range(1, max_depth + 1):
        best = None
        best_score = -MATE * 2
        alpha = -MATE * 2
        try:
            for move in ordered(moves):
                tick()
                pos.push(move)
                try:
                    score = -negamax(depth - 1, -MATE * 2, -alpha, 1)
                finally:
                    pos.pop()
                if score > best_score:
                    best, best_score = move, score
                alpha = max(alpha, score)
        except SearchStopped:
            break
        result = SearchResult(best, best_score, depth, nodes)
        moves = [best] + [m for m in moves if m != best]
    result.nodes = nodes
    return result
