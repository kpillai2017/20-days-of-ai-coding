"""Headless interaction tests: exercise actual rectangles and controller clicks."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import pygame
from main import MonopolyApp, parse_args
from engine import Game
from ui import GameUI


class InterfaceTests(unittest.TestCase):
    """Each test gets a fresh controller; no real display or audio is required."""
    def setUp(self):
        self.app = MonopolyApp(parse_args(['--seed', '42']))
        self.ui = self.app.ui

    def tearDown(self):
        pygame.quit()

    def click(self, command):
        """Find the drawn button and send a real pygame mouse event to it."""
        self.ui.render(self.app.game)
        rect = next(rect for rect, cmd in self.ui.buttons if cmd == command)
        pos = (round(rect.centerx * self.ui.scale + self.ui.offset[0]),
               round(rect.centery * self.ui.scale + self.ui.offset[1]))
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))

    def game(self):
        self.app.game = Game([('Alice', False), ('Bob', False)], 42)
        self.app.game.current = self.app.game.actor = 0
        return self.app.game

    def test_all_forty_squares_have_unique_click_targets(self):
        game = self.game()
        self.ui.render(game)
        self.assertEqual(40, len(self.ui.square_rects))
        for index, rect in self.ui.square_rects.items():
            self.assertFalse(any(rect.colliderect(other) for j, other in self.ui.square_rects.items() if j != index))
            pos = (rect.centerx * self.ui.scale + self.ui.offset[0], rect.centery * self.ui.scale + self.ui.offset[1])
            self.ui.command_at(pos)
            self.assertEqual(index, self.ui.selected)

    def test_setup_cycles_and_creates_six_seats(self):
        for i in range(2, 6):
            self.click(f'seat:{i}')
        self.click('start')
        self.assertEqual(6, len(self.app.game.players))
        self.assertFalse(self.app.game.players[0].is_ai)
        self.assertTrue(self.app.game.players[1].is_ai)

    def test_minimum_seats_validation(self):
        self.ui.modes = ['Human'] + ['Off'] * 5
        self.click('start')
        self.assertIsNone(self.app.game)
        self.assertIn('two', self.ui.notice)

    def test_actual_roll_purchase_and_end_buttons(self):
        game = self.game()
        def dice():
            game.dice_values = (1, 2)
            return game.dice_values
        game.roll_dice = dice
        self.click('game:roll')
        self.assertEqual('buy', game.phase)
        self.click('game:buy')
        self.assertEqual(0, game.properties[3].owner)
        self.click('game:end')
        self.assertEqual(1, game.current)

    def test_trade_requires_recipient_consent(self):
        game = self.game()
        game.properties[1].owner = 0
        self.click('trade')
        self.click('trade_give:1')
        self.click('trade_request:100')
        self.click('trade_submit')
        self.assertEqual('consent', self.ui.modal)
        self.assertEqual(0, game.properties[1].owner)
        self.click('trade_accept')
        self.assertEqual(1, game.properties[1].owner)
        self.assertEqual(1600, game.players[0].cash)

    def test_rejected_trade_is_atomic(self):
        game = self.game()
        game.properties[1].owner = 0
        self.click('trade')
        self.click('trade_give:1')
        self.click('trade_submit')
        self.click('trade_reject')
        self.assertEqual(0, game.properties[1].owner)
        self.assertEqual(1500, game.players[0].cash)

    def test_scroll_exposes_management_actions(self):
        game = self.game()
        for deed in game.properties.values():
            deed.owner = 0
        self.ui.scroll = 999
        self.ui.render(game)
        self.assertGreater(self.ui.scroll, 0)
        self.assertTrue(any(cmd == 'game:manage:1' for _, cmd in self.ui.buttons))

    def test_new_game_confirmation(self):
        self.game()
        self.click('new')
        self.assertIsNotNone(self.app.game)
        self.click('new_confirm')
        self.assertIsNone(self.app.game)

    def test_all_ai_demo_uses_computer_seats(self):
        app = MonopolyApp(parse_args(['--demo', '--seed', '1']))
        self.assertTrue(all(p.is_ai for p in app.game.players))
        app.update(1000)
        app.ui.render(app.game)

    def test_modal_prevents_board_click_through(self):
        game = self.game()
        self.ui.modal = 'help'
        self.ui.render(game)
        self.ui.command_at(self.ui.square_rects[0].center)
        self.assertIsNone(self.ui.selected)

    def test_all_human_ai_slot_combinations(self):
        from itertools import product
        for count in range(2, 7):
            for modes in product((False, True), repeat=count):
                game = Game([(str(i), mode) for i, mode in enumerate(modes)], 1)
                self.assertEqual(list(modes), [p.is_ai for p in game.players])

    def test_human_actions_are_ready_and_clickable(self):
        game = self.game()
        self.ui.render(game)
        self.assertTrue(self.ui.button_states['game:roll'])
        self.assertIn('game:roll', [cmd for _, cmd in self.ui.buttons])
        self.assertTrue(self.ui.button_states['trade'])

    def test_computer_actions_are_locked_and_cannot_be_clicked(self):
        game = self.game()
        game.players[0].is_ai = True
        self.ui.render(game)
        self.assertFalse(self.ui.button_states['game:roll'])
        self.assertFalse(self.ui.button_states['trade'])
        self.assertNotIn('game:roll', [cmd for _, cmd in self.ui.buttons])
        self.assertTrue(any(cmd == 'player:0' for _, cmd in self.ui.buttons))
        before = game.phase, tuple(game.dice_values)
        for rect in self.ui.disabled_buttons:
            self.assertIsNone(self.ui.command_at(rect.center))
        self.assertEqual(before, (game.phase, tuple(game.dice_values)))

    def test_actions_update_after_phase_and_actor_changes(self):
        game = self.game()
        game.phase = 'auction'
        game.auction = {'index': 1, 'high': 0, 'leader': None, 'active': [0, 1]}
        game.actor = 1
        self.ui.render(game)
        self.assertFalse(self.ui.button_states['trade'])
        self.assertNotIn('game:roll', self.ui.button_states)
        self.assertTrue(self.ui.button_states['game:bid:1'])
        game.players[1].is_ai = True
        self.ui.render(game)
        self.assertFalse(self.ui.button_states['game:bid:1'])

    def test_player_name_opens_owned_cards_and_close_returns(self):
        game = self.game()
        game.properties[1].owner = 1
        game.properties[3].owner = 0
        game.players[1].jail_cards = ['chance', 'chest']
        self.click('player:1')
        self.assertEqual('holdings', self.ui.modal)
        self.assertEqual(1, self.ui.holdings_player)
        deeds, cards = self.ui.holdings(game, 1)
        self.assertEqual([1], [i for i, _ in deeds])
        self.assertEqual(['chance', 'chest'], cards)
        self.assertEqual(0, game.properties[3].owner)
        self.ui.render(game)
        self.assertNotIn('game:roll', self.ui.button_states)
        self.click('close')
        self.assertIsNone(self.ui.modal)
        self.ui.render(game)
        self.assertTrue(self.ui.button_states['game:roll'])

    def test_holdings_pages_cover_twenty_eight_deeds(self):
        game = self.game()
        for deed in game.properties.values():
            deed.owner = 0
        self.click('player:0')
        self.ui.render(game)
        self.assertTrue(self.ui.button_states['holdings_page'])
        self.click('holdings_page')
        self.assertEqual(1, self.ui.holdings_page)
        self.click('holdings_page')
        self.assertEqual(0, self.ui.holdings_page)
        self.assertEqual(28, len(self.ui.holdings(game, 0)[0]))

    def test_empty_holdings_has_disabled_page_button(self):
        self.game()
        self.click('player:0')
        self.ui.render(self.app.game)
        self.assertFalse(self.ui.button_states['holdings_page'])
        self.assertEqual(([], []), self.ui.holdings(self.app.game, 0))

    def test_holdings_pauses_computer_without_mutating_game(self):
        game = self.game()
        game.players[0].is_ai = True
        self.click('player:0')
        before = game.phase, list(game.log)
        self.app.update(999999)
        self.assertEqual(before, (game.phase, list(game.log)))

    def test_escape_asks_before_closing(self):
        self.game()
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertTrue(self.app.running)
        self.assertEqual('quit', self.ui.modal)
        self.click('close')
        self.assertTrue(self.app.running)
        self.assertIsNone(self.ui.modal)

    def test_escape_from_dialog_dismisses_without_quitting(self):
        self.game()
        self.ui.modal = 'help'
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIsNone(self.ui.modal)
        self.assertTrue(self.app.running)

    def test_close_confirmation_works_in_setup(self):
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual('quit', self.ui.modal)
        self.click('close')
        self.assertTrue(self.app.running)
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.click('quit_confirm')
        self.assertFalse(self.app.running)

    def test_window_close_also_requires_confirmation(self):
        self.game()
        self.app.event(pygame.event.Event(pygame.QUIT))
        self.assertTrue(self.app.running)
        self.assertEqual('quit', self.ui.modal)
        self.click('quit_confirm')
        self.assertFalse(self.app.running)

    def test_quit_dialog_pauses_computer(self):
        game = self.game()
        game.players[0].is_ai = True
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        before = list(game.log)
        self.app.update(999999)
        self.assertEqual(before, game.log)

    def test_deck_view_is_read_only_before_first_draw(self):
        game = self.game()
        before = list(game.decks['chance'])
        self.click('deck:chance')
        self.assertEqual('deck', self.ui.modal)
        self.assertEqual('chance', self.ui.inspected_deck)
        self.assertIsNone(game.last_cards['chance'])
        self.ui.render(game)
        self.assertEqual(before, game.decks['chance'])
        self.click('close')
        self.assertIsNone(self.ui.modal)

    def test_last_card_records_only_public_draws(self):
        game = self.game()
        game.decks['chest'] = [('error', 'Bank error: collect £200')]
        game._card('chest')
        self.assertEqual({'code': 'error', 'text': 'Bank error: collect £200', 'player': 0},
                         game.last_cards['chest'])
        self.assertIsNone(game.last_cards['chance'])
        before = game.players[0].cash, list(game.decks['chest'])
        self.click('deck:chest')
        self.ui.render(game)
        self.assertEqual(before, (game.players[0].cash, list(game.decks['chest'])))

    def test_monopoly_title_and_printed_payments_are_rendered(self):
        from unittest.mock import patch
        game = self.game()
        with patch.object(self.ui, 'text', wraps=self.ui.text) as text, \
             patch.object(self.ui, 'fit_text', wraps=self.ui.fit_text) as fit:
            self.ui.render(game)
        messages = [str(call.args[0]) for call in text.call_args_list + fit.call_args_list]
        self.assertIn('Monopoly', messages)
        self.assertIn('Pay £200', messages)
        self.assertIn('Pay £100', messages)
        self.assertIn('Collect £200', messages)
        self.assertNotIn('Property Table', messages)

    def test_computer_management_is_hidden_but_human_management_remains(self):
        game = self.game()
        game.players[1].is_ai = True
        self.ui.render(game)
        self.assertNotIn('game:manage:1', self.ui.button_states)
        game.players[1].is_ai = False
        self.ui.render(game)
        self.assertTrue(self.ui.button_states['game:manage:1'])

    def test_optional_mortgage_and_end_turn_have_identical_enabled_fill(self):
        game = self.game()
        game.phase = 'end'
        game.properties[8].owner = 0
        self.ui.render(game)
        targets = {command: rect for rect, command in self.ui.buttons}
        colors = [self.ui.surface.get_at((targets[cmd].right - 6, targets[cmd].centery))
                  for cmd in ('game:end', 'game:mortgage:8')]
        self.assertEqual(colors[0], colors[1])
        self.assertTrue(self.ui.button_states['game:end'])
        self.assertTrue(self.ui.button_states['game:mortgage:8'])
        self.click('game:mortgage:8')
        self.assertTrue(game.properties[8].mortgaged)
        self.assertEqual(1550, game.players[0].cash)

    def test_suggestion_does_not_change_availability(self):
        from unittest.mock import patch
        game = self.game()
        game.phase = 'end'
        game.properties[8].owner = 0
        with patch.object(self.ui, 'button', wraps=self.ui.button) as button:
            self.ui.render(game)
        actions = {call.args[2]: call.kwargs for call in button.call_args_list
                   if len(call.args) >= 3 and str(call.args[2]).startswith('game:')}
        self.assertTrue(actions['game:end']['suggested'])
        self.assertFalse(actions['game:mortgage:8']['suggested'])
        self.assertTrue(actions['game:mortgage:8']['enabled'])

    def test_clicking_locked_trade_explains_reason_without_transition(self):
        game = self.game()
        game.phase = 'buy'
        game.players[0].position = 1
        self.ui.render(game)
        rect = next(rect for rect, command in self.ui.disabled_targets if command == 'trade')
        self.assertIsNone(self.ui.command_at(rect.center))
        self.assertIn('purchase', self.ui.notice)
        self.assertEqual('buy', game.phase)
        self.assertIsNone(self.ui.modal)

    def test_selected_space_has_working_close_button(self):
        game = self.game()
        self.ui.selected = 8
        before = game.phase, list(game.log), game.players[0].cash
        self.click('details_close')
        self.assertIsNone(self.ui.selected)
        self.assertEqual(before, (game.phase, list(game.log), game.players[0].cash))
        self.ui.render(game)
        self.assertNotIn('details_close', self.ui.button_states)

    def test_escape_dismisses_space_details_before_quit(self):
        self.game()
        self.ui.selected = 0
        escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.app.event(escape)
        self.assertIsNone(self.ui.selected)
        self.assertIsNone(self.ui.modal)
        self.assertTrue(self.app.running)
        self.app.event(escape)
        self.assertEqual('quit', self.ui.modal)

    def test_dialog_closes_before_underlying_space_details(self):
        self.game()
        self.ui.selected = 39
        self.ui.modal = 'help'
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIsNone(self.ui.modal)
        self.assertEqual(39, self.ui.selected)

    def test_auction_panel_names_lot_and_updates_bidder_and_high_bid(self):
        from unittest.mock import patch
        game = self.game()
        game._start_auction(8)
        def messages():
            with patch.object(self.ui, 'fit_text', wraps=self.ui.fit_text) as fit:
                self.ui.render(game)
            return [str(call.args[0]) for call in fit.call_args_list]
        before = messages()
        self.assertIn('Euston Road', before)
        self.assertIn('Highest bid: No bids yet', before)
        self.assertIn('Bidding now: Alice', before)
        game.act('bid:50')
        after = messages()
        self.assertIn('Euston Road', after)
        self.assertIn('Highest bid: £50 · Alice', after)
        self.assertIn('Bidding now: Bob', after)
        game.act('pass')
        finished = messages()
        self.assertFalse(any(text.startswith('Highest bid:') for text in finished))

    def test_negative_frame_limit_rejected(self):
        with self.assertRaises(SystemExit):
            parse_args(['--frames', '-1'])


if __name__ == '__main__':
    unittest.main()
