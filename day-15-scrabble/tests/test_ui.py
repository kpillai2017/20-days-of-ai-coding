"""Real Pygame input tests with dummy display/audio drivers, not mocked rules."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from itertools import product
from unittest.mock import patch
from concurrent.futures import Future
import pygame
from ai import Lexicon
from engine import Game, Tile
from ui import ScrabbleApp


class InterfaceTests(unittest.TestCase):
    """Click the actual drawn controls and verify the resulting game state."""

    def setUp(self):
        self.app = ScrabbleApp(Lexicon(words=["AT", "CAT", "CATS", "TO", "ON", "NO"]))

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def click(self, command):
        self.app.render()
        rect = next(rect for rect, cmd in self.app.buttons if cmd == command)
        pos = (
            round(rect.centerx * self.app.scale + self.app.offset[0]),
            round(rect.centery * self.app.scale + self.app.offset[1]),
        )
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))

    def game(self):
        self.app.start([("Alice", False), ("Bob", False)])
        self.app.game.current = 0
        self.app.modal = "handoff"
        self.app.game.players[0].rack = [Tile(c) for c in "CATXXXX"]
        self.click("ready")
        return self.app.game

    def test_setup_modes_and_start(self):
        self.click("seat:2")
        self.click("seat:3")
        self.click("start")
        self.assertEqual(4, len(self.app.game.players))
        self.assertEqual(
            [False, True, False, False], [p.is_ai for p in self.app.game.players]
        )

    def test_all_controller_combinations(self):
        for count in (2, 3, 4):
            for modes in product((False, True), repeat=count):
                g = Game(
                    [(str(i), mode) for i, mode in enumerate(modes)],
                    self.app.lexicon,
                    1,
                )
                self.assertEqual(list(modes), [p.is_ai for p in g.players])

    def test_all_two_hundred_twenty_five_cells_route_exactly(self):
        self.game()
        self.app.render()
        with patch.object(self.app, "board_click") as clicked:
            for cell, rect in self.app.cells.items():
                self.app.event(
                    pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1
                    )
                )
                self.assertEqual(cell, clicked.call_args.args[0])

    def test_rack_select_place_recall_and_commit(self):
        g = self.game()
        for index, pos in enumerate(((7, 7), (7, 8), (7, 9))):
            self.click(f"rack:{index}")
            self.app.board_click(pos)
        self.assertFalse(g.board)
        self.assertEqual(10, self.app.preview()[0].score)
        self.click("recall")
        self.assertFalse(self.app.pending)
        for index, pos in enumerate(((7, 7), (7, 8), (7, 9))):
            self.click(f"rack:{index}")
            self.app.board_click(pos)
        self.click("play")
        self.assertEqual(10, g.players[0].score)
        self.assertEqual(1, g.current)
        self.assertIsNotNone(self.app.animation)
        self.assertIsNone(self.app.modal)
        flight = self.app.animation
        with patch(
            "pygame.time.get_ticks",
            return_value=flight.last_tick + len(flight.items) * flight.step_ms,
        ):
            self.app.update()
        self.assertEqual("handoff", self.app.modal)

    def test_clicking_draft_tile_recalls_only_that_tile(self):
        self.game()
        self.click("rack:0")
        self.app.board_click((7, 7))
        self.app.board_click((7, 7))
        self.assertFalse(self.app.pending)

    def test_blank_assignment_zero_value(self):
        g = self.game()
        g.players[0].rack[0] = Tile("?")
        self.click("rack:0")
        self.app.board_click((7, 7))
        self.assertEqual("blank", self.app.modal)
        self.click("blank:C")
        self.assertEqual((0, "C"), self.app.pending[7, 7])
        self.assertEqual(0, g.players[0].rack[0].value)

    def test_handoff_never_draws_private_rack(self):
        self.game()
        self.app.handoff()
        with patch.object(self.app, "tile", wraps=self.app.tile) as tiles:
            self.app.render()
            self.assertFalse(tiles.called)
        self.assertEqual(["ready"], [cmd for rect, cmd in self.app.buttons])

    def test_computer_rack_hidden(self):
        g = self.game()
        g.players[0].is_ai = True
        with patch.object(self.app, "tile", wraps=self.app.tile) as tiles:
            self.app.render()
            self.assertFalse(tiles.called)
        self.assertFalse(any(cmd.startswith("rack:") for rect, cmd in self.app.buttons))

    def test_escape_handoff_does_not_reveal_rack(self):
        self.game()
        self.app.modal = "handoff"
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual("quit_handoff", self.app.modal)
        self.click("return_handoff")
        self.assertEqual("handoff", self.app.modal)

    def test_pass_requires_confirmation_and_advances_once(self):
        g = self.game()
        self.click("pass")
        self.assertEqual(0, g.current)
        self.click("pass_confirm")
        self.assertEqual(1, g.current)
        self.assertEqual(1, g.scoreless_turns)

    def test_exchange_selection_and_turn(self):
        g = self.game()
        self.click("exchange")
        self.click("rack:0")
        self.click("rack:1")
        self.assertEqual({0, 1}, self.app.exchange_selected)
        self.click("exchange")
        self.assertEqual(1, g.current)
        self.assertEqual(1, g.scoreless_turns)

    def test_quit_confirmation(self):
        self.game()
        self.app.event(pygame.event.Event(pygame.QUIT))
        self.assertTrue(self.app.running)
        self.assertEqual("quit", self.app.modal)
        self.click("close")
        self.assertTrue(self.app.running)
        self.app.event(pygame.event.Event(pygame.QUIT))
        self.click("quit_confirm")
        self.assertFalse(self.app.running)

    def test_hint_stages_without_committing(self):
        g = self.game()
        f = Future()
        f.set_result({(7, 7): (1, "A"), (7, 8): (2, "T")})
        self.app.future = f
        self.app.search_kind = ("hint", self.app.generation, 0)
        self.app.update()
        self.assertEqual(2, len(self.app.pending))
        self.assertFalse(g.board)
        self.assertEqual(0, g.current)

    def test_stale_worker_is_discarded(self):
        g = self.game()
        f = Future()
        f.set_result({(7, 7): (1, "A"), (7, 8): (2, "T")})
        self.app.future = f
        self.app.search_kind = ("hint", self.app.generation - 1, 0)
        self.app.update()
        self.assertFalse(self.app.pending)
        self.assertFalse(g.board)

    def test_completed_ai_waits_behind_quit_dialog(self):
        g = self.game()
        g.players[0].is_ai = True
        f = Future()
        f.set_result({(7, 7): (1, "A"), (7, 8): (2, "T")})
        self.app.future = f
        self.app.search_kind = ("ai", self.app.generation, 0)
        self.app.modal = "quit"
        self.app.update()
        self.assertFalse(g.board)
        self.app.modal = None
        self.app.update()
        self.assertEqual(1, g.current)

    def test_window_close_during_handoff_never_reveals_rack(self):
        self.game()
        self.app.handoff()
        self.app.event(pygame.event.Event(pygame.QUIT))
        with patch.object(self.app, "tile", wraps=self.app.tile) as tiles:
            self.app.render()
            self.assertFalse(tiles.called)
        self.click("close")
        self.assertEqual("handoff", self.app.modal)
        self.assertFalse(self.app.rack_revealed)

    def test_scaled_cell_clicks_match_at_smaller_window(self):
        self.game()
        self.app.screen = pygame.display.set_mode((900, 700))
        self.app.render()
        with patch.object(self.app, "board_click") as clicked:
            for cell in ((0, 0), (7, 7), (14, 14)):
                rect = self.app.cells[cell]
                pos = (
                    round(rect.centerx * self.app.scale + self.app.offset[0]),
                    round(rect.centery * self.app.scale + self.app.offset[1]),
                )
                self.app.event(
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)
                )
                self.assertEqual(cell, clicked.call_args.args[0])

    def test_help_button_works(self):
        self.game()
        self.click("help_button")
        self.assertEqual("help", self.app.modal)
        self.click("close")
        self.assertIsNone(self.app.modal)

    def test_modal_controls_fit_and_do_not_click_through(self):
        self.game()
        for modal in ("help", "quit", "pass", "handoff", "new"):
            self.app.modal = modal
            self.app.render()
            for rect, command in self.app.buttons:
                self.assertTrue(
                    self.app.surface.get_rect().contains(rect), (modal, command)
                )
            self.app.board_click((7, 7))
            self.assertFalse(self.app.pending)


if __name__ == "__main__":
    unittest.main()
