"""Versioned JSON saves: data only, never pickle or executable Python.

A save contains PRIVATE racks and the remaining bag. Treat it like a face-up
physical game, not a tamper-proof tournament record. Validation catches corrupt
files and incompatible dictionaries; it is not an anti-cheating system.
"""

import hashlib
import json
import os
import random
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from engine import Game, LETTER_COUNTS, Placed, Player, Tile

DEFAULT_SAVE = Path(__file__).parent / "saves" / "game.json"
MAX_BYTES = 5 * 1024 * 1024


def dictionary_hash(lexicon):
    """Identify the actual word set, not a filename that could later change."""
    words = getattr(lexicon, "words", lexicon)
    return hashlib.sha256("\n".join(sorted(words)).encode("utf-8")).hexdigest()


def snapshot(game):
    """Copy committed model data; drafts, animations and worker jobs aren't rules."""
    return {
        "format": "day15-scrabble",
        "version": 1,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "dictionary": dictionary_hash(game.lexicon),
        "players": [
            {
                "name": p.name,
                "is_ai": p.is_ai,
                "score": p.score,
                "rack": [t.letter for t in p.rack],
            }
            for p in game.players
        ],
        "board": [
            {"row": r, "col": c, "tile": t.tile.letter, "letter": t.letter}
            for (r, c), t in sorted(game.board.items())
        ],
        # Bag order and PRNG state preserve future draws/exchanges on resuming.
        "bag": [t.letter for t in game.bag],
        "rng": game.rng.getstate(),
        "current": game.current,
        "phase": game.phase,
        "scoreless_turns": game.scoreless_turns,
        "winner": list(game.winner),
        "last_move": list(game.last_move),
        "last_turn": game.last_turn,
        "last_play": game.last_play,
        "turn_history": game.turn_history,
        "starting_draws": game.starting_draws,
        "log": game.log,
    }


def save_game(game, path=DEFAULT_SAVE):
    """Replace atomically: a failed write must not destroy an existing save.

    Write a private temporary file in the SAME directory, flush it to disk,
    then rename it over the destination. os.replace is atomic on that filesystem.
    """
    path = Path(path)
    data = json.dumps(snapshot(game), ensure_ascii=False, indent=2).encode("utf-8")
    if len(data) > MAX_BYTES:
        raise ValueError("Game history is too large for this save format.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="tmp_rovo_save_", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _integer(value, low, high):
    """JSON booleans are Python ints too; reject them where numbers are required."""
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Invalid number in saved game.")
    return value


def _text(value, limit=2000):
    if (
        not isinstance(value, str)
        or len(value) > limit
        or any(not c.isprintable() for c in value)
    ):
        raise ValueError("Invalid text in saved game.")
    return value


def _list(value, limit):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError("Invalid list in saved game.")
    return value


def _words(value):
    result = []
    for pair in _list(value, 16):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("Invalid word score in saved game.")
        word = _text(pair[0], 15)
        if (
            not 2 <= len(word) <= 15
            or not word.isascii()
            or not word.isalpha()
            or not word.isupper()
        ):
            raise ValueError("Invalid word in saved game.")
        result.append((word, _integer(pair[1], 0, 100000)))
    return result


def restore(data, lexicon):
    """Validate EVERYTHING before returning a new model; never mutate a live game."""
    try:
        if (
            data["format"] != "day15-scrabble"
            or type(data["version"]) is not int
            or data["version"] != 1
        ):
            raise ValueError("Unsupported saved-game format or version.")
        if data["dictionary"] != dictionary_hash(lexicon):
            raise ValueError(
                "This save uses a different word list. Load its original dictionary first."
            )
        raw_players = _list(data["players"], 4)
        if len(raw_players) < 2:
            raise ValueError("A save needs two to four players.")
        players = []
        inventory = Counter()

        def tiles(values, limit):
            result = []
            for letter in _list(values, limit):
                if letter not in LETTER_COUNTS:
                    raise ValueError("Invalid physical tile in saved game.")
                result.append(Tile(letter))
                inventory[letter] += 1
            return result

        for p in raw_players:
            name = _text(p["name"], 100)
            if not name.strip() or type(p["is_ai"]) is not bool:
                raise ValueError("Invalid player in saved game.")
            players.append(
                Player(
                    name,
                    p["is_ai"],
                    _integer(p["score"], -1000, 1000000),
                    tiles(p["rack"], 7),
                )
            )
        board = {}
        for cell in _list(data["board"], 100):
            pos = (_integer(cell["row"], 0, 14), _integer(cell["col"], 0, 14))
            tile = tiles([cell["tile"]], 1)[0]
            letter = cell["letter"]
            if (
                not isinstance(letter, str)
                or len(letter) != 1
                or letter not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                or (not tile.blank and letter != tile.letter)
                or pos in board
            ):
                raise ValueError("Invalid board tile in saved game.")
            board[pos] = Placed(tile, letter)
        bag = tiles(data["bag"], 100)
        if inventory != Counter(LETTER_COUNTS):
            raise ValueError(
                "Saved game must contain the original 100 tiles exactly once."
            )
        count = len(players)
        current = _integer(data["current"], 0, count - 1)
        phase = data["phase"]
        if phase not in ("play", "gameover"):
            raise ValueError("Invalid game phase.")
        scoreless = _integer(data["scoreless_turns"], 0, 6)
        winner = [_integer(i, 0, count - 1) for i in _list(data["winner"], count)]
        if (
            len(set(winner)) != len(winner)
            or (phase == "play" and (winner or scoreless >= 6))
            or (phase == "gameover" and not winner)
        ):
            raise ValueError("Inconsistent game status in saved game.")
        last_move = []
        for pos in _list(data["last_move"], 7):
            if not isinstance(pos, list) or len(pos) != 2:
                raise ValueError("Invalid last move.")
            key = (_integer(pos[0], 0, 14), _integer(pos[1], 0, 14))
            if key not in board or key in last_move:
                raise ValueError("Invalid last move.")
            last_move.append(key)
        history = []
        for n, entry in enumerate(_list(data["turn_history"], 10000), 1):
            if _integer(entry["turn"], 1, 10000) != n:
                raise ValueError("Turn numbers must be consecutive.")
            words = _words(entry["words"])
            score = _integer(entry["score"], 0, 100000)
            bingo = _integer(entry["bingo"], 0, 50)
            action = _text(entry["action"], 100)
            if bingo not in (0, 50) or score != sum(s for w, s in words) + bingo:
                raise ValueError("Inconsistent turn score.")
            if action != "played" and (words or score or bingo):
                raise ValueError("Invalid non-playing turn.")
            history.append(
                {
                    "turn": n,
                    "player": _integer(entry["player"], 0, count - 1),
                    "action": action,
                    "words": tuple(words),
                    "score": score,
                    "bingo": bingo,
                    "total": _integer(entry["total"], -1000, 1000000),
                }
            )
        last_play = None
        if data["last_play"] is not None:
            p = data["last_play"]
            last_play = {
                "player": _integer(p["player"], 0, count - 1),
                "words": _words(p["words"]),
                "score": _integer(p["score"], 0, 100000),
                "bingo": _integer(p["bingo"], 0, 50),
            }
        last_turn = None
        if data["last_turn"] is not None:
            t = data["last_turn"]
            last_turn = {
                "player": _integer(t["player"], 0, count - 1),
                "action": _text(t["action"], 100),
            }
        draws = []
        for draw in _list(data["starting_draws"], 1000):
            clean = {}
            for i, letter in draw.items():
                seat = int(i)
                _integer(seat, 0, count - 1)
                if letter not in LETTER_COUNTS:
                    raise ValueError("Invalid starting draw.")
                clean[seat] = letter
            draws.append(clean)
        log = [_text(line) for line in _list(data["log"], 20000)]
        # Random.setstate expects tuples, while JSON intentionally uses arrays.
        state = data["rng"]
        if not isinstance(state, list) or len(state) != 3:
            raise ValueError("Invalid random-generator state.")
        rng = random.Random()
        rng.setstate((state[0], tuple(state[1]), state[2]))
        # Bypass __init__: loading must NOT draw starting letters or refill racks.
        game = Game.__new__(Game)
        game.lexicon, game.players, game.board, game.bag = lexicon, players, board, bag
        game.rng, game.current, game.phase = rng, current, phase
        game.scoreless_turns, game.scoreless_limit = scoreless, 6
        game.winner, game.last_move = winner, last_move
        game.turn_history, game.last_turn, game.last_play = (
            history,
            last_turn,
            last_play,
        )
        game.starting_draws, game.log = draws, log
        return game
    except (
        KeyError,
        TypeError,
        AttributeError,
        OverflowError,
        IndexError,
        RecursionError,
    ) as error:
        raise ValueError("Saved game is corrupt or incomplete.") from error


def load_game(lexicon, path=DEFAULT_SAVE):
    """Bound file size before parsing; never evaluate a save as Python code."""
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Saved game is too large.")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Saved game is not valid JSON.") from error
    return restore(data, lexicon)
