#!/usr/bin/env python3
"""Run a local game, keeping input, rendering and AI decisions non-blocking."""
import argparse
import pygame
from engine import Game
from ai import choose_action, proposal
from ui import GameUI


def parse_args(argv=None):
    """A frame limit is for smoke tests, not a different animation speed."""
    parser = argparse.ArgumentParser(description='Day 14: classic British Monopoly with original graphics')
    parser.add_argument('--seed', type=int, help='Reproduce dice, deck and starting-roll randomness')
    parser.add_argument('--frames', type=int, default=0, help='Exit after N frames; zero means no limit')
    parser.add_argument('--demo', action='store_true', help='Start four computer seats without setup')
    args = parser.parse_args(argv)
    if args.frames < 0:
        parser.error('--frames must be nonnegative')
    return args


class MonopolyApp:
    """The controller dispatches legal commands; engine.py owns the actual rules."""
    def __init__(self, args):
        self.args = args
        self.ui = GameUI()
        self.clock = pygame.time.Clock()
        self.game = None
        self.running = True
        self.next_ai = 0
        if args.demo:
            self.game = Game([(f'Computer {i + 1}', True) for i in range(4)], args.seed)

    def dispatch(self, command):
        """Handle button commands in one place, also callable by UI tests."""
        if not command:
            return
        if command.startswith('seat:'):
            i = int(command.split(':')[1])
            modes = ['Human', 'Computer', 'Off']
            self.ui.modes[i] = modes[(modes.index(self.ui.modes[i]) + 1) % 3]
        elif command == 'start':
            players = [(f'{mode} {i + 1}', mode == 'Computer')
                       for i, mode in enumerate(self.ui.modes) if mode != 'Off']
            if len(players) < 2:
                self.ui.notice = 'Choose at least two active seats.'
            else:
                self.game = Game(players, self.args.seed)
                self.ui.notice = ''
                self.ui.scroll = 0
        elif command == 'quit_confirm':
            self.running = False
        elif command == 'close':
            # This must work in the lobby too, before a Game exists.
            self.ui.modal = None
        elif command == 'new':
            self.ui.modal = 'new'
        elif command == 'new_confirm':
            self.game = None
            self.ui.modal = None
            self.ui.selected = None
            self.ui.notice = ''
        elif self.game and self.ui.handle_local(command, self.game):
            pass
        elif command.startswith('game:') and self.game:
            if not self.game.players[self.game.actor].is_ai:
                try:
                    self.game.act(command[5:])
                    self.ui.scroll = 0
                    self.ui.notice = ''
                except ValueError as error:
                    self.ui.notice = str(error)

    def event(self, event):
        """Undo scaling for clicks; wheel scrolling changes only the action view."""
        if event.type == pygame.QUIT:
            self.ui.modal = 'quit'
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.ui.modal:
                    self.ui.modal = None
                elif self.ui.selected is not None:
                    # Dismiss the nearest visible inspection layer first.
                    self.ui.selected = None
                else:
                    self.ui.modal = 'quit'
            elif event.key == pygame.K_F1 and self.game:
                self.ui.modal = None if self.ui.modal == 'help' else 'help'
            elif event.key == pygame.K_n and self.game:
                self.ui.modal = 'new'
        elif event.type == pygame.MOUSEWHEEL:
            self.ui.scroll = max(0, self.ui.scroll - event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dispatch(self.ui.command_at(event.pos))

    def update(self, now):
        """One AI action per delay, never a whole unresponsive AI game loop."""
        if (self.game and self.game.phase != 'gameover' and not self.ui.modal
                and self.game.players[self.game.actor].is_ai and now >= self.next_ai):
            offer = proposal(self.game) if self.game.phase in ('roll', 'end') else None
            if offer is None or not self.game.trade(*offer):
                self.game.act(choose_action(self.game))
            self.ui.scroll = 0
            self.next_ai = now + 350

    def run(self):
        """Pump events even on computer turns, render, then cap at sixty FPS."""
        frames = 0
        try:
            while self.running:
                for event in pygame.event.get():
                    self.event(event)
                self.update(pygame.time.get_ticks())
                self.ui.render(self.game)
                frames += 1
                if self.args.frames and frames >= self.args.frames:
                    break
                self.clock.tick(60)
        finally:
            pygame.quit()


if __name__ == '__main__':
    MonopolyApp(parse_args()).run()
