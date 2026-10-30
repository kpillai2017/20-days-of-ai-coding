"""Pure classic-English tile-game mechanics, with no Pygame dependency.

A preview is a transaction plan: validate everything, calculate every word,
then commit only if the whole move is legal. The window cannot partly place an
invalid word or consume tiles before learning that a cross-word is invalid.
"""

import random
from dataclasses import dataclass, field

LETTER_VALUES = dict(
    zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        (
            1,
            3,
            3,
            2,
            1,
            4,
            2,
            4,
            1,
            8,
            5,
            1,
            3,
            1,
            1,
            3,
            10,
            1,
            1,
            1,
            1,
            4,
            4,
            8,
            4,
            10,
        ),
    )
)
LETTER_VALUES["?"] = 0
LETTER_COUNTS = dict(
    zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        (9, 2, 2, 4, 12, 2, 3, 2, 9, 1, 1, 4, 2, 6, 8, 2, 1, 6, 4, 6, 4, 2, 2, 1, 2, 1),
    )
)
LETTER_COUNTS["?"] = 2
# 1 = double letter; 2 = triple letter; 3 = double word; 4 = triple word.
# Keep an explicit, symmetric board rather than guessing premiums by distance.
PREMIUMS = {}
for r, c in ((0, 0), (0, 7), (0, 14), (7, 0), (7, 14), (14, 0), (14, 7), (14, 14)):
    PREMIUMS[r, c] = 4
for n in range(1, 5):
    for r, c in ((n, n), (n, 14 - n), (14 - n, n), (14 - n, 14 - n)):
        PREMIUMS[r, c] = 3
PREMIUMS[7, 7] = 3
for r, c in (
    (1, 5),
    (1, 9),
    (5, 1),
    (5, 5),
    (5, 9),
    (5, 13),
    (9, 1),
    (9, 5),
    (9, 9),
    (9, 13),
    (13, 5),
    (13, 9),
):
    PREMIUMS[r, c] = 2
for r, c in (
    (0, 3),
    (0, 11),
    (2, 6),
    (2, 8),
    (3, 0),
    (3, 7),
    (3, 14),
    (6, 2),
    (6, 6),
    (6, 8),
    (6, 12),
    (7, 3),
    (7, 11),
    (8, 2),
    (8, 6),
    (8, 8),
    (8, 12),
    (11, 0),
    (11, 7),
    (11, 14),
    (12, 6),
    (12, 8),
    (14, 3),
    (14, 11),
):
    PREMIUMS[r, c] = 1


@dataclass(frozen=True)
class Tile:
    """Physical tile identity. A blank stays '?' even when assigned a letter."""

    letter: str

    def __post_init__(self):
        """Validate physical tile identity as soon as a tile is constructed."""
        if self.letter not in LETTER_VALUES:
            raise ValueError("Tile must be A–Z or ?. ")

    @property
    def value(self):
        """Blanks always score zero, including on letter premiums."""
        return LETTER_VALUES[self.letter]

    @property
    def blank(self):
        """A convenient physical-blank flag for drawing and move generation."""
        return self.letter == "?"


@dataclass(frozen=True)
class Placed:
    """A board tile and its permanent declared letter, which may differ for '?' ."""

    tile: Tile
    letter: str

    @property
    def value(self):
        """Read the physical tile value, not the value of a blank's assignment."""
        return self.tile.value

    @property
    def blank(self):
        """Keep blanks visually distinguishable for the rest of the game."""
        return self.tile.blank


@dataclass
class Player:
    """One persistent seat; turn order never reorders this list."""

    name: str
    is_ai: bool
    score: int = 0
    rack: list = field(default_factory=list)


@dataclass
class MoveResult:
    """All validated words, their total and the resolved newly placed tiles."""

    score: int
    words: list
    placements: dict
    breakdown: list = field(default_factory=list)
    bingo: int = 0


class Game:
    """A seedable local game using a caller-supplied adjudication lexicon.

    Invalid words are rejected automatically; challenge penalties are not
    simulated. Six consecutive scoreless turns end this chosen digital variant.
    These edition/household choices are explicit in RULES.md.
    """

    def __init__(self, names, lexicon, seed=None):
        if not 2 <= len(names) <= 4:
            raise ValueError("Choose two to four players.")
        if any(not isinstance(n, str) or not n.strip() for n, _ in names):
            raise ValueError("Every seat needs a name.")
        if not lexicon:
            raise ValueError("The dictionary must contain words.")
        self.lexicon = lexicon
        self.rng = random.Random(seed)
        self.players = [Player(name.strip(), bool(ai)) for name, ai in names]
        self.board = {}
        self.bag = [
            Tile(letter)
            for letter, count in LETTER_COUNTS.items()
            for _ in range(count)
        ]
        self.log = []
        self.phase = "play"
        self.scoreless_turns = 0
        self.scoreless_limit = 6
        self.winner = []
        self.last_move = []
        # Structured public history survives handoffs and final-score logging.
        self.turn_history = []
        self.last_turn = None
        self.last_play = None
        self.starting_draws = []
        self.current = self._starting_player()
        self.rng.shuffle(self.bag)
        for player in self.players:
            self._refill(player)
        self.log.append(
            f"{self.players[self.current].name} starts. Seven tiles per rack."
        )

    def _starting_player(self):
        """Closest letter to A starts; blanks precede A; tied seats redraw.

        This is alphabetical order, NOT point value. Other seats keep their
        relative clockwise order. Drawing tiles are returned before racks fill.
        """
        candidates = list(range(len(self.players)))
        while True:
            drawn = self.rng.sample(self.bag, len(candidates))
            values = {
                i: (0 if tile.blank else ord(tile.letter) - 64)
                for i, tile in zip(candidates, drawn)
            }
            self.starting_draws.append({i: t.letter for i, t in zip(candidates, drawn)})
            self.log.append(
                "Starting draw: "
                + ", ".join(
                    f"{self.players[i].name} {t.letter}"
                    for i, t in zip(candidates, drawn)
                )
            )
            lowest = min(values.values())
            candidates = [i for i in candidates if values[i] == lowest]
            if len(candidates) == 1:
                return candidates[0]

    def _refill(self, player):
        """Draw only until seven; a nearly empty bag yields a shorter rack."""
        while len(player.rack) < 7 and self.bag:
            player.rack.append(self.bag.pop())

    def _ensure_play(self):
        """Every state-changing turn operation checks the game is still live."""
        if self.phase != "play":
            raise ValueError("The game has finished.")

    def _word(self, board, position, direction):
        """Walk backwards to a word start, then forwards to its final tile."""
        r, c = position
        dr, dc = direction
        while (r - dr, c - dc) in board:
            r, c = r - dr, c - dc
        cells = []
        while (r, c) in board:
            cells.append((r, c))
            r, c = r + dr, c + dc
        return cells

    def preview(self, placements):
        """Validate geometry, rack identity and ALL words without any mutation."""
        self._ensure_play()
        if not isinstance(placements, dict) or not placements:
            raise ValueError("Place at least one tile.")
        rack = self.players[self.current].rack
        used = set()
        resolved = {}
        for position, choice in placements.items():
            if (
                not isinstance(position, tuple)
                or len(position) != 2
                or any(type(n) is not int or not 0 <= n < 15 for n in position)
            ):
                raise ValueError("Tiles must stay on the 15 × 15 board.")
            if position in self.board:
                raise ValueError("A square already holds a tile.")
            if not isinstance(choice, (tuple, list)) or len(choice) != 2:
                raise ValueError("Each placement needs a rack index and letter.")
            index, letter = choice
            if type(index) is not int or not 0 <= index < len(rack) or index in used:
                raise ValueError("Use each real rack tile at most once.")
            if (
                not isinstance(letter, str)
                or len(letter) != 1
                or letter not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ):
                raise ValueError("Assign one uppercase A–Z letter.")
            tile = rack[index]
            if not tile.blank and tile.letter != letter:
                raise ValueError("A non-blank tile cannot change its letter.")
            used.add(index)
            resolved[position] = Placed(tile, letter)
        rows = {r for r, c in resolved}
        columns = {c for r, c in resolved}
        if len(rows) > 1 and len(columns) > 1:
            raise ValueError("New tiles must lie in a single row or column.")
        merged = dict(self.board)
        merged.update(resolved)
        axis = (0, 1) if len(rows) == 1 else (1, 0)
        if len(resolved) > 1:
            all_cells = self._word(merged, next(iter(resolved)), axis)
            if not set(resolved).issubset(all_cells):
                raise ValueError("The word has a gap.")
        if not self.board:
            if (7, 7) not in resolved:
                raise ValueError("The first word must cover the centre star.")
        elif not any(
            (r + dr, c + dc) in self.board
            for r, c in resolved
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            raise ValueError("Connect to an existing tile.")
        # A one-tile play can create BOTH a horizontal and a vertical word.
        # Deduplicate coordinate sequences so a main word is counted once.
        sequences = set()
        for position in resolved:
            for direction in ((0, 1), (1, 0)):
                cells = tuple(self._word(merged, position, direction))
                if len(cells) > 1:
                    sequences.add(cells)
        if not sequences:
            raise ValueError("A word must contain at least two letters.")
        words = []
        breakdown = []
        for cells in sorted(sequences):
            word = "".join(merged[pos].letter for pos in cells)
            if word not in self.lexicon:
                raise ValueError(f"{word} is not in the selected dictionary.")
            subtotal = 0
            multiplier = 1
            terms = []
            word_bonuses = []
            for pos in cells:
                tile = merged[pos]
                value = tile.value
                term = (
                    f"{tile.letter}[blank=0]"
                    if tile.blank
                    else f"{tile.letter}[{value}]"
                )
                if pos in resolved:
                    premium = PREMIUMS.get(pos)
                    if premium == 1:
                        value *= 2
                        term += "×2 DL"
                    elif premium == 2:
                        value *= 3
                        term += "×3 TL"
                    elif premium == 3:
                        multiplier *= 2
                        word_bonuses.append("DW ×2")
                    elif premium == 4:
                        multiplier *= 3
                        word_bonuses.append("TW ×3")
                terms.append(term)
                subtotal += value
            words.append((word, subtotal * multiplier))
            breakdown.append(
                {
                    "word": word,
                    "terms": terms,
                    "subtotal": subtotal,
                    "word_bonuses": word_bonuses,
                    "multiplier": multiplier,
                    "score": subtotal * multiplier,
                }
            )
        bingo = 50 if len(resolved) == 7 else 0
        score = sum(value for word, value in words) + bingo
        return MoveResult(score, words, resolved, breakdown, bingo)

    def play(self, placements):
        """Commit only a validated preview; remove rack entries back-to-front."""
        result = self.preview(placements)
        player = self.players[self.current]
        self.board.update(result.placements)
        for index in sorted(
            (index for index, letter in placements.values()), reverse=True
        ):
            player.rack.pop(index)
        player.score += result.score
        self.last_move = list(result.placements)
        self.last_play = {
            "player": self.current,
            "words": list(result.words),
            "score": result.score,
            "bingo": result.bingo,
        }
        self._record_turn("played", result.words, result.score, result.bingo)
        self.last_turn = {"player": self.current, "action": "played"}
        self.log.append(
            f"{player.name}: "
            + ", ".join(f"{word} ({score})" for word, score in result.words)
            + f" = {result.score} points."
        )
        self._refill(player)
        self.scoreless_turns = self.scoreless_turns + 1 if result.score == 0 else 0
        if not player.rack and not self.bag:
            self.finish(self.current)
        elif self.scoreless_turns >= self.scoreless_limit:
            self.finish()
        else:
            self.current = (self.current + 1) % len(self.players)
        return result.score

    def _record_turn(self, action, words=(), score=0, bingo=0):
        """Snapshot public results BEFORE advancing players or adjusting end scores.

        A structured list is safer than parsing display strings later. It stores
        no rack tiles, so the interface can display it to every player. Invalid
        previews never reach this method and therefore never create log entries.
        """
        self.turn_history.append(
            {
                "turn": len(self.turn_history) + 1,
                "player": self.current,
                "action": action,
                "words": tuple(words),
                "score": score,
                "bingo": bingo,
                "total": self.players[self.current].score,
            }
        )

    def _scoreless(self, message):
        """Pass and exchange consume a turn, but cannot leak staged tiles."""
        self._record_turn(message)
        self.log.append(f"{self.players[self.current].name}: {message}.")
        self.last_turn = {"player": self.current, "action": message}
        self.last_move = []
        self.scoreless_turns += 1
        if self.scoreless_turns >= self.scoreless_limit:
            self.finish()
        else:
            self.current = (self.current + 1) % len(self.players)

    def pass_turn(self):
        """A pass is always allowed during a live game."""
        self._ensure_play()
        self._scoreless("passes")

    def exchange(self, indices):
        """Require seven in bag BEFORE exchange; draw before returning tiles."""
        self._ensure_play()
        rack = self.players[self.current].rack
        if len(self.bag) < 7:
            raise ValueError("At least seven tiles must remain in the bag to exchange.")
        if (
            not isinstance(indices, (list, tuple))
            or not indices
            or any(type(i) is not int or not 0 <= i < len(rack) for i in indices)
            or len(set(indices)) != len(indices)
        ):
            raise ValueError("Choose distinct tiles from your rack.")
        returned = [rack[i] for i in indices]
        for i in sorted(indices, reverse=True):
            rack.pop(i)
        self._refill(self.players[self.current])
        self.bag.extend(returned)
        self.rng.shuffle(self.bag)
        self._scoreless(f"exchanges {len(indices)} tiles")

    def shuffle_rack(self):
        """A cosmetic rearrangement does not use a turn or change the bag."""
        self._ensure_play()
        self.rng.shuffle(self.players[self.current].rack)

    def finish(self, finisher=None):
        """Subtract rack leftovers, then award their sum to a player going out."""
        if self.phase == "gameover":
            return
        penalties = [sum(tile.value for tile in p.rack) for p in self.players]
        for player, penalty in zip(self.players, penalties):
            player.score -= penalty
        if finisher is not None:
            self.players[finisher].score += sum(penalties) - penalties[finisher]
        highest = max(p.score for p in self.players)
        self.winner = [i for i, p in enumerate(self.players) if p.score == highest]
        self.phase = "gameover"
        self.log.append(
            "Game over: " + ", ".join(f"{p.name} {p.score}" for p in self.players)
        )
