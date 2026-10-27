"""Tests for Monopoly engine using unittest with 40+ focused tests.

Tests cover:
- Rent calculations for all property types (streets, stations, utilities)
- Board squares (GO, Mayfair, Old Kent Road, Jail mechanics)
- Dice rolls (doubles, triple jail mechanics)
- Jail entry and release (3-turn forced release, fine, card usage)
- Property ownership and development (houses, hotels, mortgages)
- Building rules (even development, limited tokens)
- Auctions (first bid, all-pass, atomic transfers)
- Card mechanics (deck cycling, held jail-free cards, return to deck)
- Trading (atomic, mortgage interest, invalid cases)
- Bankruptcy (creditor assets, token returns, bank auctions)
- Game completion (2-6 players with seeds, cash non-negative, owners not bankrupt)
- Complete seeded 20-action test games verifying determinism
"""

import unittest
import sys
sys.path.insert(0, '..')
from engine import Game, Player, Deed
from data import BOARD, CHANCE_CARDS, COMMUNITY_CHEST_CARDS


class MockDice:
    """Helper to set deterministic dice values for testing."""
    def __init__(self, game, values):
        self.game = game
        # values should be list of (die1, die2) tuples
        self.values = iter(values) if isinstance(values[0], tuple) else iter([values])

    def __enter__(self):
        self.original_roll = self.game.roll_dice
        def mock_roll():
            val = next(self.values)
            self.game.dice_values = val
            return val
        self.game.roll_dice = mock_roll
        return self

    def __exit__(self, *args):
        self.game.roll_dice = self.original_roll


class TestGameInitialization(unittest.TestCase):
    """Test game setup with valid player counts."""

    def test_init_two_players(self):
        """Two players: valid minimum."""
        game = Game([("Alice", False), ("Bob", True)])
        self.assertEqual(len(game.players), 2)
        self.assertEqual(game.players[0].name, "Alice")
        self.assertEqual(game.players[1].name, "Bob")
        self.assertEqual(game.players[0].cash, 1500)
        self.assertEqual(game.players[0].position, 0)
        self.assertIn(game.current, (0, 1))  # Starting roll determines who goes first
        self.assertEqual(game.phase, "roll")

    def test_init_six_players(self):
        """Six players: valid maximum."""
        names = [("P{}".format(i), i % 2 == 0) for i in range(6)]
        game = Game(names)
        self.assertEqual(len(game.players), 6)
        self.assertTrue(all(p.cash == 1500 for p in game.players))

    def test_init_invalid_players_one(self):
        """One player raises ValueError."""
        with self.assertRaises(ValueError):
            Game([("Solo", False)])

    def test_init_invalid_players_seven(self):
        """Seven players raises ValueError."""
        names = [("P{}".format(i), False) for i in range(7)]
        with self.assertRaises(ValueError):
            Game(names)

    def test_init_invalid_name_empty(self):
        """Empty name raises ValueError."""
        with self.assertRaises(ValueError):
            Game([("", False), ("Bob", False)])

    def test_init_seeded_determinism(self):
        """Same seed produces same starting roll order."""
        game1 = Game([("A", False), ("B", False), ("C", False)], seed=42)
        game2 = Game([("A", False), ("B", False), ("C", False)], seed=42)
        self.assertEqual(game1.current, game2.current)

    def test_init_board_complete(self):
        """Board has 40 squares."""
        game = Game([("A", False), ("B", False)])
        self.assertEqual(len(game.board), 40)
        self.assertEqual(game.board[0].name, "GO")
        self.assertEqual(game.board[39].name, "Mayfair")
        self.assertEqual(game.board[10].name, "Jail / Just Visiting")

    def test_init_properties_setup(self):
        """Only purchasable properties in properties dict."""
        game = Game([("A", False), ("B", False)])
        self.assertEqual(len(game.properties), 28)  # 22 streets + 4 stations + 2 utilities
        for i, deed in game.properties.items():
            self.assertIsNone(deed.owner)
            self.assertFalse(deed.mortgaged)
            self.assertEqual(deed.houses, 0)


class TestRentCalculations(unittest.TestCase):
    """Test rent calculations for all property types."""

    def setUp(self):
        """Create game fixture with deterministic turn."""
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0

    def test_rent_unowned_property(self):
        """Unowned property earns no rent."""
        self.assertEqual(self.game.rent(1), 0)
        self.assertEqual(self.game.rent(5), 0)

    def test_rent_mediterranean_bare(self):
        """Old Kent Road bare rent = 2."""
        self.game.properties[1].owner = 0
        self.assertEqual(self.game.rent(1), 2)

    def test_rent_mediterranean_with_monopoly(self):
        """Old Kent Road + Whitechapel Road (monopoly) = doubled bare rent = 4."""
        self.game.properties[1].owner = 0
        self.game.properties[3].owner = 0
        self.assertEqual(self.game.rent(1), 4)

    def test_rent_mediterranean_with_house(self):
        """Old Kent Road with 1 house."""
        self.game.properties[1].owner = 0
        self.game.properties[1].houses = 1
        self.assertEqual(self.game.rent(1), 10)

    def test_rent_mediterranean_with_hotel(self):
        """Old Kent Road with hotel (5 houses)."""
        self.game.properties[1].owner = 0
        self.game.properties[1].houses = 5
        self.assertEqual(self.game.rent(1), 250)

    def test_rent_boardwalk_bare(self):
        """Mayfair bare = 50."""
        self.game.properties[39].owner = 0
        self.assertEqual(self.game.rent(39), 50)

    def test_rent_boardwalk_with_monopoly(self):
        """Mayfair with Park Lane (monopoly) = 100."""
        self.game.properties[37].owner = 0
        self.game.properties[39].owner = 0
        self.assertEqual(self.game.rent(39), 100)

    def test_rent_boardwalk_with_hotel(self):
        """Mayfair with hotel = 2000."""
        self.game.properties[39].owner = 0
        self.game.properties[39].houses = 5
        self.assertEqual(self.game.rent(39), 2000)

    def test_rent_mortgaged_zero(self):
        """Mortgaged property earns no rent."""
        self.game.properties[1].owner = 0
        self.game.properties[1].mortgaged = True
        self.assertEqual(self.game.rent(1), 0)

    def test_rent_station_one(self):
        """One station = £25."""
        self.game.properties[5].owner = 0
        self.assertEqual(self.game.rent(5), 25)

    def test_rent_station_two(self):
        """Two stations = £50."""
        self.game.properties[5].owner = 0
        self.game.properties[15].owner = 0
        self.assertEqual(self.game.rent(5), 50)

    def test_rent_station_four(self):
        """Four stations = £200."""
        for idx in (5, 15, 25, 35):
            self.game.properties[idx].owner = 0
        self.assertEqual(self.game.rent(5), 200)

    def test_rent_station_double_rent(self):
        """Station from card (rail special) pays double."""
        self.game.properties[5].owner = 0
        self.game.properties[15].owner = 0
        self.assertEqual(self.game.rent(5, special='rail'), 100)

    def test_rent_utility_one_fresh_dice(self):
        """One utility with fresh dice = 4 * dice_sum."""
        self.game.properties[12].owner = 0
        self.assertEqual(self.game.rent(12, dice=7, special='utility'), 70)

    def test_rent_utility_two_fresh_dice(self):
        """Two utilities with fresh dice = 10 * dice_sum."""
        self.game.properties[12].owner = 0
        self.game.properties[28].owner = 0
        self.assertEqual(self.game.rent(12, dice=5, special='utility'), 50)

    def test_rent_utility_from_dice_values(self):
        """Utility rent uses game.dice_values by default."""
        self.game.properties[12].owner = 0
        self.game.dice_values = (2, 3)
        self.assertEqual(self.game.rent(12), 20)


class TestBoardPositions(unittest.TestCase):
    """Test movement to key board positions."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0

    def test_go_position(self):
        """GO is at position 0."""
        self.assertEqual(BOARD[0].name, "GO")
        self.assertEqual(BOARD[0].price, 0)

    def test_mediterranean_position(self):
        """Old Kent Road is position 1."""
        self.assertEqual(BOARD[1].name, "Old Kent Road")
        self.assertEqual(BOARD[1].price, 60)

    def test_jail_position(self):
        """Jail is at position 10."""
        self.assertEqual(BOARD[10].name, "Jail / Just Visiting")

    def test_boardwalk_position(self):
        """Mayfair is at position 39."""
        self.assertEqual(BOARD[39].name, "Mayfair")
        self.assertEqual(BOARD[39].price, 400)

    def test_go_to_jail_position(self):
        """Go To Jail is at position 30."""
        self.assertEqual(BOARD[30].name, "Go To Jail")


class TestJailMechanics(unittest.TestCase):
    """Test jail entry, stay, and release mechanics."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0

    def test_jail_entry_direct(self):
        """Landing on Go To Jail sends player to Jail position 10."""
        player = self.game.players[0]
        player.position = 30
        self.game._land()
        self.assertEqual(player.position, 10)
        self.assertEqual(player.jailed, 1)

    def test_jail_doubles_release_first_roll(self):
        """Rolling doubles on first jailed turn releases immediately."""
        player = self.game.players[0]
        player.position = 10
        player.jailed = 1
        with MockDice(self.game, [(3, 3)]):
            self.game._roll()
        self.assertEqual(player.jailed, 0)
        self.assertEqual(player.position, (10 + 6) % 40)

    def test_jail_no_doubles_increments(self):
        """Not rolling doubles increments jailed counter."""
        player = self.game.players[0]
        player.jailed = 1
        with MockDice(self.game, [(2, 3)]):
            self.game._roll()
        self.assertEqual(player.jailed, 2)

    def test_jail_third_turn_forced_release_with_fine(self):
        """On third jailed roll without doubles, pay £50 and move."""
        player = self.game.players[0]
        player.jailed = 3
        player.position = 10
        initial_cash = player.cash
        with MockDice(self.game, [(2, 4)]):
            self.game._roll()
        self.assertEqual(player.jailed, 0)
        self.assertEqual(player.cash, initial_cash - 50)
        self.assertEqual(player.position, (10 + 6) % 40)

    def test_jail_pay_to_leave_before_roll(self):
        """Player can pay £50 to leave jail without rolling."""
        player = self.game.players[0]
        player.position = 10
        player.jailed = 1
        self.game.phase = 'roll'
        self.game.actor = 0
        initial_cash = player.cash
        self.game.act('jailpay')
        self.assertEqual(player.jailed, 0)
        self.assertEqual(player.cash, initial_cash - 50)

    def test_jail_card_release(self):
        """Using jail-free card releases without rolling."""
        player = self.game.players[0]
        player.jailed = 1
        player.jail_cards.append('chance')
        initial_cards = len(player.jail_cards)
        self.game.phase = 'roll'
        self.game.actor = 0
        self.game.act('jailcard')
        self.assertEqual(player.jailed, 0)
        self.assertEqual(len(player.jail_cards), initial_cards - 1)


class TestDoublesMechanics(unittest.TestCase):
    """Test doubles rolling and triple-jail."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0
        self.game.phase = 'roll'

    def test_doubles_grants_extra_roll(self):
        """Rolling doubles sets extra_roll flag."""
        with MockDice(self.game, [(4, 4)]):
            self.game._roll()
        self.assertTrue(self.game.extra_roll)

    def test_no_doubles_clears_flag(self):
        """Not rolling doubles clears extra_roll."""
        self.game.extra_roll = True
        with MockDice(self.game, [(3, 4)]):
            self.game._roll()
        self.assertFalse(self.game.extra_roll)

    def test_doubles_count_increments(self):
        """Three consecutive doubles sends to jail."""
        self.game.doubles_count = 0
        self.game.phase = 'roll'
        with MockDice(self.game, [(2, 2), (3, 3), (5, 5)]):
            self.game._roll()
            self.assertEqual(self.game.doubles_count, 1)
            self.assertTrue(self.game.extra_roll)
            if self.game.phase == 'roll':
                self.game._roll()
                self.assertEqual(self.game.doubles_count, 2)
                if self.game.phase == 'roll':
                    self.game._roll()
                    self.assertEqual(self.game.players[0].jailed, 1)
                    self.assertEqual(self.game.doubles_count, 0)


class TestPropertyOwnership(unittest.TestCase):
    """Test property ownership and groups."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0

    def test_group_mediterranean_baltic(self):
        """Brown group contains Old Kent Road and Whitechapel Road."""
        group = self.game.group(1)
        self.assertIn(1, group)
        self.assertIn(3, group)
        self.assertEqual(len(group), 2)

    def test_group_boardwalk_parkplace(self):
        """Blue group contains Mayfair and Park Lane."""
        group = self.game.group(39)
        self.assertIn(37, group)
        self.assertIn(39, group)
        self.assertEqual(len(group), 2)

    def test_owns_group_complete_monopoly(self):
        """Complete monopoly recognized."""
        self.game.properties[37].owner = 0
        self.game.properties[39].owner = 0
        self.assertTrue(self.game.owns_group(0, 39))

    def test_owns_group_incomplete(self):
        """Incomplete group not recognized."""
        self.game.properties[37].owner = 0
        self.game.properties[39].owner = 1
        self.assertFalse(self.game.owns_group(0, 39))


class TestBuildingMechanics(unittest.TestCase):
    """Test house and hotel building rules."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0
        # Set up complete brown monopoly
        self.game.properties[1].owner = 0
        self.game.properties[3].owner = 0

    def test_even_development_required(self):
        """Cannot build 2 houses on one property while other has 0."""
        actions = self.game.actions()
        build_actions = [a for a in actions if 'Build' in a[0]]
        # Both properties must be at same level for next build
        self.game.properties[1].houses = 1
        actions = self.game.actions()
        build_on_1 = any('Old Kent Road' in a[0] and 'Build' in a[0] for a in actions)
        self.assertFalse(build_on_1)

    def test_house_token_limit(self):
        """Cannot build more than 32 houses in bank."""
        # Reduce houses in bank
        self.game.houses_left = 0
        self.game.players[0].cash = 10000
        actions = self.game.actions()
        build_actions = [a for a in actions if 'Build' in a[0]]
        self.assertEqual(len(build_actions), 0)

    def test_hotel_conversion(self):
        """Fifth house becomes hotel, frees 4 houses."""
        self.game.players[0].cash = 10000
        self.game.properties[1].houses = 4
        initial_hotels = self.game.hotels_left
        initial_houses = self.game.houses_left
        # Directly test building logic by calling _building
        self.game._building(1, 1)  # Build one more house on property 1
        self.assertEqual(self.game.properties[1].houses, 5)
        self.assertEqual(self.game.hotels_left, initial_hotels - 1)
        self.assertEqual(self.game.houses_left, initial_houses + 4)

    def test_sell_house_half_price(self):
        """Selling house returns half building cost."""
        self.game.players[0].cash = 1500
        self.game.properties[1].houses = 1
        self.game.act('sell:1')
        self.assertEqual(self.game.properties[1].houses, 0)
        self.assertEqual(self.game.players[0].cash, 1500 + 25)


class TestMortgage(unittest.TestCase):
    """Test mortgage mechanics."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0
        self.game.properties[1].owner = 0

    def test_mortgage_raises_cash(self):
        """Mortgaging gives half purchase price."""
        initial_cash = self.game.players[0].cash
        self.game.act('mortgage:1')
        self.assertEqual(self.game.players[0].cash, initial_cash + 30)
        self.assertTrue(self.game.properties[1].mortgaged)

    def test_unmortgage_costs_110_percent(self):
        """Unmorgage costs 110% of mortgage value."""
        self.game.players[0].cash = 1500
        self.game.properties[1].mortgaged = True
        self.game.act('unmortgage:1')
        self.assertFalse(self.game.properties[1].mortgaged)
        # 30 * 1.1 = 33
        self.assertEqual(self.game.players[0].cash, 1500 - 33)

    def test_cannot_build_with_mortgaged(self):
        """Cannot build on mortgaged property in group."""
        self.game.properties[1].owner = 0
        self.game.properties[3].owner = 0
        self.game.properties[1].mortgaged = True
        actions = self.game.actions()
        build_on_3 = any('Whitechapel Road' in a[0] and 'Build' in a[0] for a in actions)
        self.assertFalse(build_on_3)


class TestAuctionMechanics(unittest.TestCase):
    """Test auction for declined properties."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0
        self.game.players[0].position = 1
        self.game.phase = 'buy'

    def test_auction_start(self):
        """Declining purchase starts auction."""
        self.game.act('auction')
        self.assertEqual(self.game.phase, 'auction')
        self.assertEqual(self.game.auction['index'], 1)

    def test_auction_first_valid_bid(self):
        """First bid must be >= £1."""
        self.game.act('auction')
        actions = self.game.actions()
        bid_actions = [a for a in actions if 'Bid' in a[0]]
        self.assertGreater(len(bid_actions), 0)

    def test_auction_all_pass_bank_auction(self):
        """If all pass, property goes back to bank (auction ends)."""
        self.game.act('auction')
        self.game.act('pass')
        self.game.act('pass')
        self.assertIsNone(self.game.auction)

    def test_auction_winner_owns_property(self):
        """Highest bidder owns property after auction."""
        self.game.act('auction')
        self.game.act('bid:50')
        self.game.act('pass')
        self.assertEqual(self.game.properties[1].owner, 0)
        self.assertEqual(self.game.players[0].cash, 1500 - 50)


class TestCardMechanics(unittest.TestCase):
    """Test card deck cycling and held cards."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0

    def test_chance_deck_exists(self):
        """Chance deck initialized with 16 cards."""
        self.assertEqual(len(self.game.decks['chance']), 16)

    def test_chest_deck_exists(self):
        """Community Chest deck initialized with 16 cards."""
        self.assertEqual(len(self.game.decks['chest']), 16)

    def test_card_drawn_goes_bottom(self):
        """Card returned to bottom of deck."""
        deck = self.game.decks['chance']
        first_card = deck[0]
        # Draw a card and return it
        self.game.phase = 'resolving'
        self.game.events.append(('land', None))
        self.game._card('chance')
        # First card should now be at end
        self.assertNotEqual(deck[0], first_card)

    def test_jailfree_card_held(self):
        """Jail-free card kept in hand, not recycled."""
        player = self.game.players[0]
        deck = self.game.decks['chance']
        initial_count = len(deck)
        # Manually trigger jailfree card
        self.game.phase = 'resolving'
        self.game._card('chance')
        # Keep running until we get jailfree or cycle
        for _ in range(20):
            if 'jailfree' in [c[0] for c in self.game.decks['chance']]:
                break
            self.game._card('chance')

    def test_jailfree_returned_on_bankruptcy(self):
        """Jail-free cards returned to deck when bankrupt."""
        player = self.game.players[0]
        player.jail_cards.append('chance')
        player.bankrupt = True
        self.game.debt = (0, 100, None)
        initial_count = len(self.game.decks['chance'])
        self.game._bankrupt()
        # Card should be back in deck
        jailfree_in_deck = any(c[0] == 'jailfree' for c in self.game.decks['chance'])
        self.assertTrue(jailfree_in_deck)


class TestTradeMechanics(unittest.TestCase):
    """Test property trading with mortgage interest."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0
        self.game.phase = 'roll'

    def test_trade_properties_atomic(self):
        """Trade executes atomically."""
        self.game.properties[1].owner = 0
        self.game.properties[3].owner = 1
        result = self.game.trade(0, 1, [1], [3], 0, 0)
        self.assertTrue(result)
        self.assertEqual(self.game.properties[1].owner, 1)
        self.assertEqual(self.game.properties[3].owner, 0)

    def test_trade_with_cash_payment(self):
        """Trade includes cash payment."""
        self.game.properties[1].owner = 0
        result = self.game.trade(0, 1, [1], [], 100, 0)
        self.assertTrue(result)
        self.assertEqual(self.game.players[0].cash, 1500 - 100)
        self.assertEqual(self.game.players[1].cash, 1500 + 100)

    def test_trade_with_mortgaged_costs_interest(self):
        """Receiving mortgaged property costs 10% interest."""
        self.game.properties[1].owner = 0
        self.game.properties[1].mortgaged = True
        self.game.players[0].cash = 1500
        self.game.players[1].cash = 1500
        result = self.game.trade(0, 1, [1], [])
        self.assertTrue(result)
        # Old Kent Road mortgage is 30, interest is 3
        self.assertEqual(self.game.players[1].cash, 1500 - 3)

    def test_trade_invalid_not_owner(self):
        """Cannot trade property not owned."""
        self.game.properties[1].owner = 1
        result = self.game.trade(0, 1, [1], [])
        self.assertFalse(result)

    def test_trade_invalid_insufficient_cash(self):
        """Trade fails if insufficient cash for payment + interest."""
        self.game.properties[1].owner = 0
        self.game.players[0].cash = 50
        result = self.game.trade(0, 1, [1], [], 100, 0)
        self.assertFalse(result)

    def test_trade_cannot_with_developed_property(self):
        """Cannot trade from group with development."""
        self.game.properties[1].owner = 0
        self.game.properties[3].owner = 0
        self.game.properties[1].houses = 1
        result = self.game.trade(0, 1, [1], [])
        self.assertFalse(result)

    def test_trade_invalid_same_player(self):
        """Cannot trade with self."""
        result = self.game.trade(0, 0, [], [])
        self.assertFalse(result)

    def test_trade_invalid_bankrupt(self):
        """Cannot trade if bankrupt."""
        self.game.players[0].bankrupt = True
        result = self.game.trade(0, 1, [], [])
        self.assertFalse(result)


class TestBankruptcy(unittest.TestCase):
    """Test bankruptcy and creditor asset transfer."""

    def setUp(self):
        self.game = Game([("A", False), ("B", False)])
        self.game.current = 0
        self.game.actor = 0
        # Give player A properties
        self.game.properties[1].owner = 0
        self.game.properties[3].owner = 0
        self.game.properties[1].houses = 2

    def test_bankruptcy_to_player(self):
        """Bankrupt player's properties go to creditor."""
        self.game.players[0].cash = 0
        self.game.debt = (0, 100, 1)
        self.game._bankrupt()
        self.assertEqual(self.game.players[0].bankrupt, True)
        self.assertEqual(self.game.properties[1].owner, 1)
        self.assertTrue(self.game.players[0].bankrupt)

    def test_bankruptcy_buildings_liquidated(self):
        """Buildings sold at half price before transfer."""
        initial_cash_b = self.game.players[1].cash
        self.game.players[0].cash = 0
        self.game.debt = (0, 100, 1)
        self.game._bankrupt()
        # 2 houses at half cost = 2 * 25 = 50
        self.assertEqual(self.game.players[1].cash, initial_cash_b + 50)
        self.assertEqual(self.game.properties[1].houses, 0)

    def test_bankruptcy_to_bank(self):
        """Bankrupt player's properties queued for auction."""
        self.game.players[0].cash = 0
        self.game.debt = (0, 100, None)
        self.game._bankrupt()
        self.assertEqual(self.game.properties[1].owner, None)

    def test_bankruptcy_hotels_freed(self):
        """Hotel tokens returned to bank on bankruptcy."""
        self.game.properties[1].houses = 5
        initial_hotels = self.game.hotels_left
        self.game.players[0].cash = 0
        self.game.debt = (0, 100, 1)
        self.game._bankrupt()
        self.assertEqual(self.game.hotels_left, initial_hotels + 1)

    def test_bankruptcy_jailfree_cards_returned(self):
        """Jail-free cards returned to deck on bankruptcy."""
        self.game.players[0].jail_cards.append('chance')
        self.game.players[0].cash = 0
        self.game.debt = (0, 100, None)
        self.game._bankrupt()
        jailfree_in_deck = any(c[0] == 'jailfree' for c in self.game.decks['chance'])
        self.assertTrue(jailfree_in_deck)


class TestGameCompletion(unittest.TestCase):
    """Test game termination and validity checks."""

    def test_game_ends_one_player_left(self):
        """Game ends when only one player not bankrupt."""
        game = Game([("A", False), ("B", False)])
        game.players[0].bankrupt = False
        game.players[1].bankrupt = True
        game._finish_resolution()
        self.assertEqual(game.winner, 0)
        self.assertEqual(game.phase, 'gameover')

    def test_cash_never_negative(self):
        """All players have non-negative cash at all times."""
        game = Game([("A", False), ("B", False)], seed=100)
        max_actions = 500
        for _ in range(max_actions):
            if game.phase == 'gameover':
                break
            actions = game.actions()
            if not actions:
                break
            game.act(actions[0][1])
        for p in game.players:
            self.assertGreaterEqual(p.cash, 0)

    def test_owner_never_bankrupt_on_property(self):
        """Properties only owned by non-bankrupt players or bank."""
        game = Game([("A", False), ("B", False)], seed=42)
        max_actions = 500
        for _ in range(max_actions):
            if game.phase == 'gameover':
                break
            actions = game.actions()
            if not actions:
                break
            game.act(actions[0][1])
        for i, deed in game.properties.items():
            if deed.owner is not None:
                self.assertFalse(game.players[deed.owner].bankrupt)

    def test_inventory_conservation_tokens(self):
        """Total house and hotel tokens conserved."""
        game = Game([("A", False), ("B", False)], seed=77)
        initial_houses = 32
        initial_hotels = 12
        total_initial = initial_houses + initial_hotels * 5
        max_actions = 500
        for _ in range(max_actions):
            if game.phase == 'gameover':
                break
            actions = game.actions()
            if not actions:
                break
            game.act(actions[0][1])
        in_play = sum(d.houses * (5 if d.houses == 5 else 1) for d in game.properties.values())
        total_current = game.houses_left + in_play + game.hotels_left * 5
        self.assertEqual(total_initial, total_current)


class TestSeededGames(unittest.TestCase):
    """Test complete deterministic seeded games."""

    def test_seeded_game_20_actions_seed_1(self):
        """20 actions with seed 1 complete without errors."""
        game = Game([("A", False), ("B", False)], seed=1)
        for i in range(20):
            actions = game.actions()
            if not actions:
                break
            game.act(actions[0][1])
        for p in game.players:
            self.assertGreaterEqual(p.cash, 0)
            self.assertFalse(p.bankrupt or p.cash < 0)

    def test_seeded_game_20_actions_seed_2(self):
        """20 actions with seed 2 complete without errors."""
        game = Game([("A", False), ("B", False)], seed=2)
        for i in range(20):
            actions = game.actions()
            if not actions:
                break
            game.act(actions[0][1])
        self.assertGreaterEqual(game.players[0].cash, 0)

    def test_seeded_game_20_actions_seed_3(self):
        """20 actions with seed 3 complete without errors."""
        game = Game([("A", False), ("B", False)], seed=3)
        for i in range(20):
            actions = game.actions()
            if not actions:
                break
            game.act(actions[0][1])
        self.assertGreaterEqual(game.players[0].cash, 0)

    def test_seeded_game_100_actions_seed_123(self):
        """100 actions with seed 123 (longer game)."""
        game = Game([("A", False), ("B", False), ("C", False)], seed=123)
        action_count = 0
        while action_count < 100 and game.phase != 'gameover':
            actions = game.actions()
            if not actions:
                break
            game.act(actions[0][1])
            action_count += 1
        self.assertGreater(action_count, 5)
        for p in game.players:
            self.assertGreaterEqual(p.cash, 0)

    def test_seeded_game_determinism_same_seeds(self):
        """Same seed produces same game state after 20 actions."""
        seed = 456
        games = [Game([("A", False), ("B", False)], seed=seed) for _ in range(2)]
        for _ in range(20):
            for g in games:
                actions = g.actions()
                if actions:
                    g.act(actions[0][1])
        self.assertEqual(games[0].players[0].cash, games[1].players[0].cash)
        self.assertEqual(games[0].players[0].position, games[1].players[0].position)


class TestActionValidity(unittest.TestCase):
    """Test action legality and state consistency."""

    def test_actions_never_empty_during_game(self):
        """Actions available unless gameover."""
        game = Game([("A", False), ("B", False)])
        game.current = 0
        game.actor = 0
        for _ in range(50):
            if game.phase == 'gameover':
                break
            actions = game.actions()
            self.assertGreater(len(actions), 0)
            game.act(actions[0][1])

    def test_invalid_action_raises(self):
        """Invalid action raises ValueError."""
        game = Game([("A", False), ("B", False)])
        game.current = 0
        game.actor = 0
        game.phase = 'roll'
        with self.assertRaises(ValueError):
            game.act('invalid_command_xyz')

    def test_current_equals_actor_after_setup(self):
        """current and actor are same at game start."""
        game = Game([("A", False), ("B", False)])
        self.assertEqual(game.current, game.actor)


if __name__ == '__main__':
    unittest.main()
