"""Save files use real conserved games; no private fixtures escape the workspace."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame
from ai import Lexicon
from engine import Game
from persistence import load_game, restore, save_game, snapshot
from ui import ScrabbleApp

ROOT = Path(__file__).resolve().parents[2]


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tmp_rovo_", dir=ROOT)
        self.path = Path(self.temp.name) / "saves" / "game.json"
        self.lexicon = Lexicon(
            words=["AT", "CAT", "TO", "ON", "NO", "IN", "IT", "AS", "IS", "AN"]
        )
        self.game = Game([("Alice", False), ("Robot", True)], self.lexicon, 42)

    def tearDown(self):
        self.temp.cleanup()

    def json_state(self):
        return json.loads(json.dumps(snapshot(self.game)))

    def test_new_game_round_trip_and_exact_future_draws(self):
        save_game(self.game, self.path)
        restored = load_game(self.lexicon, self.path)
        before, after = snapshot(self.game), snapshot(restored)
        before.pop("saved_at")
        after.pop("saved_at")
        self.assertEqual(before, after)
        self.game.exchange([0, 1])
        restored.exchange([0, 1])
        self.assertEqual(self.game.bag, restored.bag)
        self.assertEqual(self.game.players, restored.players)
        self.assertEqual(self.game.rng.getstate(), restored.rng.getstate())

    def test_play_history_and_blank_assignment_round_trip(self):
        # Transfer real bag tiles, rather than inventing extra physical tiles.
        g = self.game
        for player in g.players:
            g.bag.extend(player.rack)
            player.rack.clear()
        for letter in "?ATEEEE":
            tile = next(t for t in g.bag if t.letter == letter)
            g.bag.remove(tile)
            g.players[g.current].rack.append(tile)
        g.play({(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")})
        g.pass_turn()
        save_game(g, self.path)
        restored = load_game(self.lexicon, self.path)
        self.assertEqual(g.board, restored.board)
        self.assertTrue(restored.board[7, 7].blank)
        self.assertEqual("C", restored.board[7, 7].letter)
        self.assertEqual(g.turn_history, restored.turn_history)
        self.assertEqual(g.last_play, restored.last_play)
        self.assertEqual(g.last_turn, restored.last_turn)
        self.assertEqual(g.scoreless_turns, restored.scoreless_turns)

    def test_gameover_does_not_deduct_racks_twice(self):
        for _ in range(6):
            self.game.pass_turn()
        save_game(self.game, self.path)
        restored = load_game(self.lexicon, self.path)
        scores = [p.score for p in restored.players]
        restored.finish()
        self.assertEqual("gameover", restored.phase)
        self.assertEqual(scores, [p.score for p in restored.players])
        self.assertEqual(self.game.winner, restored.winner)

    def test_bad_files_and_dictionary_mismatch(self):
        self.path.parent.mkdir()
        for raw in (b"broken JSON", b"[]", b"{}", b"null"):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                load_game(self.lexicon, self.path)
        save_game(self.game, self.path)
        with self.assertRaisesRegex(ValueError, "different word list"):
            load_game(Lexicon(words=["ZZ"]), self.path)
        with patch("persistence.MAX_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "too large"):
                load_game(self.lexicon, self.path)

    def test_corrupt_structures_inventory_and_rng_rejected(self):
        changes = [
            ("version", 99),
            ("players", []),
            ("board", [{"row": 90, "col": 0, "tile": "A", "letter": "A"}]),
            ("bag", []),
            ("current", True),
            ("phase", "nonsense"),
            ("winner", [0]),
            ("last_move", [[0, 0]]),
            ("rng", [3, [], None]),
            (
                "turn_history",
                [
                    {
                        "turn": 1,
                        "player": 0,
                        "action": "played",
                        "words": [["CAT", 5]],
                        "score": 99,
                        "bingo": 0,
                        "total": 99,
                    }
                ],
            ),
        ]
        for key, value in changes:
            with self.subTest(key=key):
                data = self.json_state()
                data[key] = value
                with self.assertRaises(ValueError):
                    restore(data, self.lexicon)

    def test_failed_replace_preserves_previous_save_and_cleans_temp(self):
        save_game(self.game, self.path)
        previous = self.path.read_bytes()
        with patch("persistence.os.replace", side_effect=OSError("Disk unavailable")):
            with self.assertRaises(OSError):
                save_game(self.game, self.path)
        self.assertEqual(previous, self.path.read_bytes())
        self.assertEqual([], list(self.path.parent.glob("tmp_rovo_*")))


class SaveInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tmp_rovo_", dir=ROOT)
        self.app = ScrabbleApp(Lexicon(words=["CAT", "AT"]), 42)
        self.app.save_path = Path(self.temp.name) / "game.json"
        self.app.start([("Alice", False), ("Bob", False)])
        self.app.dispatch("ready")

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        self.app.definition_executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()
        self.temp.cleanup()

    def click(self, command):
        self.app.render()
        rect = next(r for r, cmd in self.app.buttons if cmd == command)
        pos = tuple(
            round(rect.center[i] * self.app.scale + self.app.offset[i]) for i in (0, 1)
        )
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))

    def test_save_confirm_load_from_lobby_and_private_handoff(self):
        self.app.pending = {
            (7, 7): (0, self.app.game.players[self.app.game.current].rack[0].letter)
        }
        self.click("save")
        self.assertFalse(self.app.save_path.exists())
        self.click("save_confirm")
        self.assertTrue(self.app.save_path.exists())
        self.app.dispatch("new_confirm")
        self.click("load")
        self.click("load_confirm")
        self.assertIsNotNone(self.app.game)
        self.assertEqual({}, self.app.pending)
        self.assertEqual({}, self.app.game.board)
        self.assertEqual("handoff", self.app.modal)
        self.assertFalse(self.app.rack_revealed)

    def test_load_error_preserves_live_game_and_draft(self):
        game = self.app.game
        self.app.pending = {(7, 7): (0, "A")}
        self.click("load")
        self.click("load_confirm")
        self.assertIs(game, self.app.game)
        self.assertTrue(self.app.pending)
        self.assertIn("Load failed", self.app.notice)
        self.assertEqual("load", self.app.modal)

    def test_cancel_does_not_write_or_replace(self):
        game = self.app.game
        self.click("save")
        self.click("close")
        self.assertFalse(self.app.save_path.exists())
        self.click("load")
        self.click("close")
        self.assertIs(game, self.app.game)

    def test_loading_invalidates_old_search_results(self):
        from concurrent.futures import Future

        save_game(self.app.game, self.app.save_path)
        previous_generation = self.app.generation
        future = Future()
        self.app.future = future
        self.click("load")
        self.click("load_confirm")
        self.assertTrue(future.cancelled())
        self.assertIsNone(self.app.future)
        self.assertGreater(self.app.generation, previous_generation)

    def test_save_during_flight_restores_committed_board_without_replay(self):
        game = self.app.game
        for player in game.players:
            game.bag.extend(player.rack)
            player.rack.clear()
        for letter in "CATEEEE":
            tile = next(t for t in game.bag if t.letter == letter)
            game.bag.remove(tile)
            game.players[game.current].rack.append(tile)
        self.app.commit_animated({(7, 7): (0, "C"), (7, 8): (1, "A"), (7, 9): (2, "T")})
        self.click("save")
        self.click("save_confirm")
        self.assertIsNotNone(self.app.animation)
        self.click("load")
        self.click("load_confirm")
        self.assertIsNone(self.app.animation)
        self.assertEqual(3, len(self.app.game.board))
        self.assertEqual(1, len(self.app.game.turn_history))
        self.assertEqual(10, self.app.game.last_play["score"])
        self.assertEqual("handoff", self.app.modal)

    def test_save_write_error_is_reported(self):
        with patch("ui.save_game", side_effect=OSError("Read only")):
            self.click("save")
            self.click("save_confirm")
        self.assertIn("Save failed", self.app.notice)
        self.assertEqual("save", self.app.modal)


if __name__ == "__main__":
    unittest.main()
