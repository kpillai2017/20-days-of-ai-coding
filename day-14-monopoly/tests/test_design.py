"""Layout regressions for the redesigned desktop board-game interface.

These test geometry and input routing, not whether a design is beautiful.
Visual inspection is still necessary after changing colours or typography.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import pygame
from engine import Game
from ui import GameUI, WHITE, MUTED, BACKGROUND, INK, PAPER


class DesignTests(unittest.TestCase):
    """Check that visual changes cannot silently break the shared hit targets."""

    def tearDown(self):
        pygame.quit()

    def test_all_board_targets_at_multiple_window_sizes(self):
        for size in ((1320, 940), (1100, 800), (1600, 1000), (900, 700)):
            ui = GameUI(*size)
            game = Game([(str(i), False) for i in range(6)], 42)
            ui.render(game)
            for index, rect in ui.square_rects.items():
                physical = (rect.centerx * ui.scale + ui.offset[0],
                            rect.centery * ui.scale + ui.offset[1])
                ui.command_at(physical)
                self.assertEqual(index, ui.selected, (size, index))

    def test_corner_spaces_are_larger_than_streets(self):
        ui = GameUI()
        self.assertGreater(ui.square_rects[0].width, ui.square_rects[1].width)
        self.assertGreater(ui.square_rects[10].height, ui.square_rects[11].height)

    def test_six_player_buttons_do_not_overlap_actions(self):
        ui = GameUI()
        game = Game([(str(i), False) for i in range(6)], 1)
        ui.render(game)
        targets = dict((cmd, rect) for rect, cmd in ui.buttons)
        for i in range(6):
            self.assertIn(f'player:{i}', targets)
            for command, rect in targets.items():
                if command.startswith('game:'):
                    self.assertFalse(targets[f'player:{i}'].colliderect(rect))

    def test_all_interactive_targets_fit_inside_logical_surface(self):
        ui = GameUI()
        game = Game([(str(i), False) for i in range(6)], 1)
        for modal in (None, 'help', 'new', 'quit', 'deck', 'journal', 'trade', 'holdings'):
            ui.holdings_player = 0
            if modal == 'trade':
                ui.start_trade(game)
            ui.modal = modal
            ui.render(game)
            for rect, command in ui.buttons:
                self.assertTrue(ui.surface.get_rect().contains(rect), (modal, command))

    def test_journal_opens_read_only_overlay(self):
        ui = GameUI()
        game = Game([('A', False), ('B', False)], 1)
        before = list(game.log)
        self.assertTrue(ui.handle_local('journal', game))
        self.assertEqual('journal', ui.modal)
        ui.render(game)
        self.assertEqual(before, game.log)
        self.assertEqual(['close'], [cmd for _, cmd in ui.buttons])

    def test_original_symbols_stay_inside_their_reserved_box(self):
        from icons import draw_icon, icon_kind
        from data import BOARD
        ui = GameUI()
        found = set()
        for square in BOARD:
            kind = icon_kind(square.index, square.kind)
            if kind is None:
                self.assertEqual('street', square.kind)
                continue
            found.add(kind)
            image = pygame.Surface((80, 80), pygame.SRCALPHA)
            box = pygame.Rect(25, 25, 24, 24)
            draw_icon(image, kind, box)
            self.assertFalse(image.get_bounding_rect().size == (0, 0))
            self.assertTrue(box.contains(image.get_bounding_rect()), kind)
        self.assertEqual({'go', 'jail', 'parking', 'to_jail', 'station',
                          'chance', 'chest', 'bulb', 'tap', 'tax'}, found)

    def test_go_arrow_head_points_left_towards_old_kent_road(self):
        from icons import draw_icon
        pygame.init()
        image = pygame.Surface((64, 64), pygame.SRCALPHA)
        draw_icon(image, 'go', image.get_rect())
        # Above the horizontal shaft, the arrowhead is on the LEFT, not right.
        self.assertGreater(image.get_at((25, 20)).a, 0)
        self.assertEqual(0, image.get_at((40, 20)).a)

    def test_core_text_pairs_have_at_least_four_point_five_contrast(self):
        def luminance(rgb):
            """WCAG relative luminance, used as guidance for these UI colours."""
            channels = [v / 255 for v in rgb]
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
            return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
        for foreground, background in ((WHITE, BACKGROUND), (MUTED, BACKGROUND),
                                       (INK, PAPER), (WHITE, (31, 86, 72)),
                                       (MUTED, (31, 40, 48))):
            high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
            self.assertGreaterEqual((high + .05) / (low + .05), 4.5)


if __name__ == '__main__':
    unittest.main()
