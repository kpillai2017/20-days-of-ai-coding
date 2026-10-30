"""Presentation regressions: classic board layout and usable panel geometry."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from unittest.mock import patch
import pygame
from ai import Lexicon
from engine import PREMIUMS
from ui import ScrabbleApp, INK, IVORY, WHITE, BG, MUTED, GREEN


class DesignTests(unittest.TestCase):
    """Geometry and contrast checks supplement, not replace, visual inspection."""

    def setUp(self):
        self.app = ScrabbleApp(Lexicon(words=["AT", "CAT"]), 42)
        self.app.start(
            [
                ("Alice", False),
                ("Bob", False),
                ("Computer 3", True),
                ("Computer 4", True),
            ]
        )
        self.app.game.current = 0
        self.app.dispatch("ready")

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def test_classic_premiums_and_vector_star_are_drawn(self):
        with patch.object(self.app, "star", wraps=self.app.star) as star:
            self.app.render()
        star.assert_called_once()
        for pos, premium in PREMIUMS.items():
            self.assertIn(pos, self.app.cells)
        self.assertEqual(225, len(self.app.cells))

    def test_physical_rack_uses_square_nonoverlapping_tiles(self):
        for i, rect in enumerate(self.app.rack_rects):
            self.assertEqual(rect.width, rect.height)
            self.assertFalse(
                any(
                    rect.colliderect(other)
                    for j, other in enumerate(self.app.rack_rects)
                    if i != j
                )
            )
            self.assertTrue(self.app.surface.get_rect().contains(rect))

    def test_board_does_not_overlap_score_and_control_panel(self):
        self.app.render()
        for rect, command in self.app.buttons:
            if not command.startswith("rack:"):
                self.assertFalse(
                    any(rect.colliderect(cell) for cell in self.app.cells.values()),
                    command,
                )

    def test_empty_word_control_is_disabled_with_explanation(self):
        self.app.render()
        self.assertNotIn("play", [command for rect, command in self.app.buttons])
        self.assertTrue(
            any("valid word" in reason for rect, reason in self.app.disabled_reasons)
        )

    def test_endgame_replaces_preview_instead_of_overprinting(self):
        self.app.game.finish()
        with patch.object(self.app, "text", wraps=self.app.text) as text:
            self.app.render()
        messages = [call.args[0] for call in text.call_args_list]
        self.assertIn("FINAL RESULT", messages)
        self.assertNotIn("MOVE PREVIEW", messages)

    def test_typography_roles_are_cached_separately(self):
        """A tile and a heading must not accidentally share the body font."""
        body = self.app.font(22, "body")
        heading = self.app.font(22, "heading")
        tile = self.app.font(22, "tile")
        self.assertIs(body, self.app.font(22, "body"))
        self.assertIsNot(body, heading)
        self.assertIsNot(body, tile)

    def test_missing_system_fonts_use_bundled_fallback(self):
        with patch("pygame.font.match_font", return_value=None):
            for role in ("body", "heading", "tile"):
                self.assertGreater(self.app.font(21, role).size("Scrabble")[0], 0)

    def test_fitted_heading_keeps_its_role_when_shrunk(self):
        with patch.object(self.app, "font", wraps=self.app.font) as font:
            self.app.fit("A very long player's name", (0, 0, 100, 34), 27)
        self.assertTrue(all(call.args[1] == "heading" for call in font.call_args_list))
        self.assertLess(font.call_args_list[-1].args[0], 27)

    def test_core_text_color_contrast(self):
        def luminance(color):
            """WCAG luminance formula used as desktop design guidance only."""
            channels = [v / 255 for v in color]
            linear = [
                v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                for v in channels
            ]
            return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))

        for foreground, background in (
            (WHITE, BG),
            (MUTED, BG),
            (INK, IVORY),
            (WHITE, GREEN),
        ):
            high, low = sorted(
                (luminance(foreground), luminance(background)), reverse=True
            )
            self.assertGreaterEqual((high + 0.05) / (low + 0.05), 4.5)


if __name__ == "__main__":
    unittest.main()
