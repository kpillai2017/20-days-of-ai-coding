"""Real press/move/release tests for safe rack and provisional-board dragging."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from collections import Counter
import pygame
from ai import Lexicon
from engine import Tile, Placed
from ui import ScrabbleApp


class DragTests(unittest.TestCase):
    """Dragging changes a draft or rack order, never committed rules state."""

    def setUp(self):
        self.app = ScrabbleApp(Lexicon(words=["CAT", "AT"]), 42)
        self.app.start([("Alice", False), ("Bob", False)])
        self.app.game.current = 0
        self.app.dispatch("ready")
        self.app.game.players[0].rack = [Tile(c) for c in "CAT?XYZ"]
        self.app.render()

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def physical(self, pos):
        """Map a logical target into real mouse pixels after window resizing."""
        return (
            round(pos[0] * self.app.scale + self.app.offset[0]),
            round(pos[1] * self.app.scale + self.app.offset[1]),
        )

    def drag(self, start, end):
        """Send the same event sequence as a real held-left-button drag."""
        self.app.render()
        self.app.event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, pos=self.physical(start), button=1
            )
        )
        self.app.event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=self.physical(end),
                rel=(20, 20),
                buttons=(1, 0, 0),
            )
        )
        self.app.render()
        self.app.event(
            pygame.event.Event(pygame.MOUSEBUTTONUP, pos=self.physical(end), button=1)
        )

    def stage(self, index, cell):
        self.app.selected = index
        self.app.board_click(cell)

    def test_rack_to_board_stages_without_committing(self):
        self.drag(self.app.rack_rects[0].center, self.app.cells[7, 7].center)
        self.assertEqual({(7, 7): (0, "C")}, self.app.pending)
        self.assertFalse(self.app.game.board)
        self.assertEqual(0, self.app.game.current)

    def test_rack_reorder_preserves_inventory(self):
        before = Counter(t.letter for t in self.app.game.players[0].rack)
        self.drag(self.app.rack_rects[0].center, self.app.rack_rects[2].center)
        self.assertEqual(
            "ATC?XYZ", "".join(t.letter for t in self.app.game.players[0].rack)
        )
        self.assertEqual(
            before, Counter(t.letter for t in self.app.game.players[0].rack)
        )

    def test_reorder_remaps_pending_physical_identity(self):
        self.stage(0, (7, 7))
        self.drag(self.app.rack_rects[2].center, self.app.rack_rects[0].center)
        index, letter = self.app.pending[7, 7]
        self.assertEqual("C", self.app.game.players[0].rack[index].letter)
        self.assertEqual("C", letter)
        self.assertEqual(1, index)

    def test_draft_can_move_and_swap_other_draft(self):
        self.stage(0, (7, 7))
        self.stage(1, (7, 8))
        self.drag(self.app.cells[7, 7].center, self.app.cells[7, 9].center)
        self.assertNotIn((7, 7), self.app.pending)
        self.assertEqual((0, "C"), self.app.pending[7, 9])
        self.drag(self.app.cells[7, 9].center, self.app.cells[7, 8].center)
        self.assertEqual((0, "C"), self.app.pending[7, 8])
        self.assertEqual((1, "A"), self.app.pending[7, 9])

    def test_board_to_rack_recalls_and_reorders(self):
        self.stage(0, (7, 7))
        self.drag(self.app.cells[7, 7].center, self.app.rack_rects[2].center)
        self.assertFalse(self.app.pending)
        self.assertEqual(
            "ATC?XYZ", "".join(t.letter for t in self.app.game.players[0].rack)
        )

    def test_blank_drop_asks_letter_then_keeps_assignment_when_moved(self):
        self.drag(self.app.rack_rects[3].center, self.app.cells[7, 7].center)
        self.assertEqual("blank", self.app.modal)
        self.app.dispatch("blank:C")
        self.drag(self.app.cells[7, 7].center, self.app.cells[7, 8].center)
        self.assertEqual((3, "C"), self.app.pending[7, 8])
        self.assertEqual(0, self.app.game.players[0].rack[3].value)

    def test_outside_drop_does_not_lose_or_move_tile(self):
        self.stage(0, (7, 7))
        before = dict(self.app.pending)
        self.drag(self.app.cells[7, 7].center, (10, 10))
        self.assertEqual(before, self.app.pending)
        self.assertEqual(7, len(self.app.game.players[0].rack))

    def test_committed_tiles_cannot_move_or_be_overwritten(self):
        self.app.game.board[7, 7] = Placed(Tile("A"), "A")
        self.drag(self.app.rack_rects[0].center, self.app.cells[7, 7].center)
        self.assertFalse(self.app.pending)
        self.drag(self.app.cells[7, 7].center, self.app.cells[7, 8].center)
        self.assertEqual("A", self.app.game.board[7, 7].letter)
        self.assertNotIn((7, 8), self.app.game.board)

    def test_escape_cancels_active_drag_not_game(self):
        point = self.app.rack_rects[0].center
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=1))
        self.app.event(
            pygame.event.Event(
                pygame.MOUSEMOTION, pos=(300, 300), rel=(10, 10), buttons=(1, 0, 0)
            )
        )
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIsNone(self.app.drag)
        self.assertIsNone(self.app.modal)
        self.assertFalse(self.app.pending)

    def test_focus_loss_cancels_drag(self):
        self.app.begin_drag("rack", 0, (180, 800))
        self.app.event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertIsNone(self.app.drag)

    def test_scaled_drag_uses_same_coordinate_transform(self):
        self.app.screen = pygame.display.set_mode((900, 700))
        self.app.render()
        self.drag(self.app.rack_rects[0].center, self.app.cells[7, 7].center)
        self.assertEqual((0, "C"), self.app.pending[7, 7])

    def test_short_click_on_draft_retains_click_to_recall(self):
        self.stage(0, (7, 7))
        point = self.app.cells[7, 7].center
        self.app.render()
        for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.app.event(pygame.event.Event(kind, pos=point, button=1))
        self.assertFalse(self.app.pending)


if __name__ == "__main__":
    unittest.main()
