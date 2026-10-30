"""Human names are entered in setup, not hard-coded into game turns."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
import pygame
from ai import Lexicon
from ui import ScrabbleApp


class NameTests(unittest.TestCase):
    def setUp(self):
        self.app = ScrabbleApp(Lexicon(words=["AT", "CAT"]), 42)

    def tearDown(self):
        self.app.executor.shutdown(wait=True, cancel_futures=True)
        self.app.definition_executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()

    def enter(self, text):
        self.app.event(pygame.event.Event(pygame.TEXTINPUT, text=text))

    def test_name_is_used_in_game_and_handoff(self):
        self.app.dispatch("name:0")
        self.enter("Kiran")
        self.app.dispatch("name_save")
        self.app.dispatch("start")
        self.assertEqual("Kiran", self.app.game.players[0].name)
        self.assertEqual("Computer 2", self.app.game.players[1].name)

    def test_enter_saves_and_escape_cancels(self):
        self.app.dispatch("name:0")
        self.enter("Alice")
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual("Alice", self.app.human_names[0])
        self.app.dispatch("name:0")
        self.enter("Discard")
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual("Alice", self.app.human_names[0])
        self.assertIsNone(self.app.modal)

    def test_blank_and_duplicate_names_rejected(self):
        self.app.dispatch("name:0")
        self.enter("   ")
        self.app.dispatch("name_save")
        self.assertEqual("name", self.app.modal)
        self.app.name_draft = "computer 2"
        self.app.dispatch("name_save")
        self.assertEqual("name", self.app.modal)
        self.assertIn("distinct", self.app.notice)

    def test_unicode_length_limit_and_backspace(self):
        self.app.dispatch("name:0")
        self.enter("Élodie")
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertEqual("Élodi", self.app.name_draft)
        self.enter("x" * 50)
        self.assertEqual(20, len(self.app.name_draft))

    def test_only_human_setup_seats_have_name_controls(self):
        self.app.render()
        commands = [command for rect, command in self.app.buttons]
        self.assertIn("name:0", commands)
        self.assertNotIn("name:1", commands)
        self.app.dispatch("name:1")
        self.assertIsNone(self.app.modal)

    def test_name_survives_controller_cycle(self):
        self.app.human_names[0] = "Alice"
        for _ in range(3):
            self.app.dispatch("seat:0")
        self.assertEqual("Human", self.app.modes[0])
        self.assertEqual("Alice", self.app.human_names[0])


if __name__ == "__main__":
    unittest.main()
