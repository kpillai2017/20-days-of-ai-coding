"""Dictionary loading and a trie-based, cross-checking computer opponent.

A trie shares prefixes: CAT and CATS follow the same C→A→T path. Searching
that tree alongside rack tiles avoids testing hundreds of thousands of complete
words at every board position. Every candidate still goes through preview().
"""

import time
from pathlib import Path


class Lexicon:
    """An explicit word set and prefix tree; not an official tournament list."""

    def __init__(self, path=None, words=None):
        self.label = Path(path).name if path else "Test dictionary"
        if words is None:
            words = Path(path).read_text(encoding="utf-8-sig").splitlines()
        self.words = {
            word.strip().upper()
            for word in words
            if 2 <= len(word.strip()) <= 15
            and word.strip().isascii()
            and word.strip().isalpha()
        }
        if not self.words:
            raise ValueError("Dictionary has no A–Z words of length 2–15.")
        self.trie = {}
        for word in sorted(self.words):
            node = self.trie
            for letter in word:
                node = node.setdefault(letter, {})
            node[""] = True  # Empty string is an end-of-word marker, not a letter.

    def __contains__(self, word):
        """Support `word in lexicon` without exposing trie internals to rules."""
        return word in self.words

    def __bool__(self):
        """An empty lexicon is false, allowing a clear setup validation error."""
        return bool(self.words)


def find_move(game, lexicon, time_limit=2.0):
    """Return a legal placement dict, or None; never mutate the game.

    Search anchor squares (empty neighbours of existing tiles), considering
    both orientations and blanks. A monotonic deadline bounds stronger searches;
    this is a heuristic best-found move, not an assertion of exhaustive strength.
    """
    if game.phase != "play":
        return None
    board = game.board
    rack = game.players[game.current].rack
    if not rack:
        return None
    deadline = time.monotonic() + max(0.02, time_limit)
    anchors = (
        {(7, 7)}
        if not board
        else {
            (r + dr, c + dc)
            for r, c in board
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= r + dr < 15 and 0 <= c + dc < 15 and (r + dr, c + dc) not in board
        }
    )
    best = None
    best_key = (-1, "")
    checks = {}

    def cross_allowed(pos, axis):
        """Precompute perpendicular legal letters, including existing blanks."""
        key = pos, axis
        if key in checks:
            return checks[key]
        r, c = pos
        dr, dc = (1, 0) if axis == (0, 1) else (0, 1)
        prefix = ""
        rr, cc = r - dr, c - dc
        while (rr, cc) in board:
            prefix = board[rr, cc].letter + prefix
            rr, cc = rr - dr, cc - dc
        suffix = ""
        rr, cc = r + dr, c + dc
        while (rr, cc) in board:
            suffix += board[rr, cc].letter
            rr, cc = rr + dr, cc + dc
        allowed = (
            set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            if not prefix + suffix
            else {
                letter
                for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                if prefix + letter + suffix in lexicon
            }
        )
        checks[key] = allowed
        return allowed

    starts = set()
    for axis in ((0, 1), (1, 0)):
        dr, dc = axis
        for anchor in sorted(anchors):
            # At most seven empty squares before an anchor can be supplied by
            # this rack; occupied squares cost no rack tile and may be bridged.
            r, c = anchor
            empty = 0
            while 0 <= r < 15 and 0 <= c < 15:
                if (r, c) not in board:
                    empty += 1
                if empty > len(rack):
                    break
                if (r - dr, c - dc) not in board:
                    starts.add((r, c, dr, dc))
                r, c = r - dr, c - dc
    # Centre/anchor-adjacent starts first, rather than spending the whole time
    # exploring an arbitrary set order. Sorting also makes equal-score ties stable.
    ordered = sorted(
        starts,
        key=lambda s: (min(abs(s[0] - r) + abs(s[1] - c) for r, c in anchors), s),
    )

    def visit(r, c, dr, dc, node, used, placements, touches, word):
        """Backtrack rack indices; identical physical letters need one branch."""
        nonlocal best, best_key
        if time.monotonic() >= deadline:
            return
        if "" in node and placements and touches and (r, c) not in board:
            try:
                result = game.preview(placements)
            except ValueError:
                pass
            else:
                key = result.score, word
                if key > best_key:
                    best_key = key
                    best = dict(placements)
        if not 0 <= r < 15 or not 0 <= c < 15:
            return
        pos = r, c
        if pos in board:
            letter = board[pos].letter
            if letter in node:
                visit(
                    r + dr,
                    c + dc,
                    dr,
                    dc,
                    node[letter],
                    used,
                    placements,
                    touches,
                    word + letter,
                )
            return
        allowed = cross_allowed(pos, (dr, dc))
        seen = set()
        for index, tile in enumerate(rack):
            if index in used or tile.letter in seen:
                continue
            seen.add(tile.letter)
            letters = (
                sorted(letter for letter in node if letter and letter in allowed)
                if tile.blank
                else [tile.letter]
            )
            for letter in letters:
                if letter not in node or letter not in allowed:
                    continue
                placements[pos] = (index, letter)
                used.add(index)
                visit(
                    r + dr,
                    c + dc,
                    dr,
                    dc,
                    node[letter],
                    used,
                    placements,
                    touches or pos in anchors,
                    word + letter,
                )
                used.remove(index)
                del placements[pos]

    for r, c, dr, dc in ordered:
        if time.monotonic() >= deadline:
            break
        visit(r, c, dr, dc, lexicon.trie, set(), {}, False, "")
    return best
