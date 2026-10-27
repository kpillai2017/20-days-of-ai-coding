"""London-edition regressions independent of the US-to-UK conversion code.

The complete expected perimeter catches accidental US labels or swapped London
streets. Currency is presentation: changing it must not multiply cash values.
"""
import unittest
from data import BOARD, CHANCE_CARDS, COMMUNITY_CHEST_CARDS
from engine import Game


class BritishEditionTests(unittest.TestCase):
    """Pin down the exact British configuration, rather than 'any Monopoly'."""

    def game(self):
        """Use named human seats so action labels are easy to inspect."""
        game = Game([('Alice', False), ('Bob', False)], seed=42)
        game.current = game.actor = 0
        return game

    def test_complete_london_board_in_clockwise_order(self):
        expected = [
            'GO', 'Old Kent Road', 'Community Chest', 'Whitechapel Road',
            'Income Tax', 'King’s Cross Station', 'The Angel Islington', 'Chance',
            'Euston Road', 'Pentonville Road', 'Jail / Just Visiting', 'Pall Mall',
            'Electric Company', 'Whitehall', 'Northumberland Avenue',
            'Marylebone Station', 'Bow Street', 'Community Chest',
            'Marlborough Street', 'Vine Street', 'Free Parking', 'Strand',
            'Chance', 'Fleet Street', 'Trafalgar Square', 'Fenchurch Street Station',
            'Leicester Square', 'Coventry Street', 'Water Works', 'Piccadilly',
            'Go To Jail', 'Regent Street', 'Oxford Street', 'Community Chest',
            'Bond Street', 'Liverpool Street Station', 'Chance', 'Park Lane',
            'Super Tax', 'Mayfair',
        ]
        self.assertEqual(expected, [square.name for square in BOARD])

    def test_four_stations_use_station_category(self):
        self.assertEqual([5, 15, 25, 35], [p.index for p in BOARD if p.kind == 'station'])
        for i in (5, 15, 25, 35):
            self.assertEqual(200, BOARD[i].price)
            self.assertEqual((25, 50, 100, 200), BOARD[i].rents)

    def test_station_ownership_rent_is_unchanged(self):
        game = self.game()
        for count, index in enumerate((5, 15, 25, 35), start=1):
            game.properties[index].owner = 1
            self.assertEqual(25 * 2 ** (count - 1), game.rent(5))
        game.properties[5].mortgaged = True
        self.assertEqual(0, game.rent(5))
        self.assertEqual(200, game.rent(15))

    def test_income_and_super_tax_amounts(self):
        for position, cost in ((4, 200), (38, 100)):
            game = self.game()
            game.players[0].position = position
            game._land()
            game._drain()
            self.assertEqual(1500 - cost, game.players[0].cash)

    def test_cards_name_london_destinations(self):
        cards = dict(CHANCE_CARDS)
        self.assertIn('Trafalgar Square', cards['move24'])
        self.assertIn('Pall Mall', cards['move11'])
        self.assertIn('King’s Cross Station', cards['move5'])
        self.assertIn('Mayfair', cards['move39'])
        self.assertEqual(16, len(CHANCE_CARDS))
        self.assertEqual(16, len(COMMUNITY_CHEST_CARDS))
        self.assertFalse(any('$' in text for _, text in CHANCE_CARDS + COMMUNITY_CHEST_CARDS))

    def test_bank_money_and_action_labels_use_pounds(self):
        game = self.game()
        self.assertEqual(1500, game.players[0].cash)
        self.assertIn('£1500', game.log[-1])
        game.properties[1].owner = 0
        labels = [label for label, _ in game.actions()]
        self.assertTrue(any('£30' in label and 'Old Kent Road' in label for label in labels))
        self.assertFalse(any('$' in label for label in labels))

    def test_park_lane_and_mayfair_not_confused(self):
        self.assertEqual(('Park Lane', 350, 175),
                         (BOARD[37].name, BOARD[37].price, BOARD[37].mortgage_value))
        self.assertEqual(('Mayfair', 400, 200),
                         (BOARD[39].name, BOARD[39].price, BOARD[39].mortgage_value))
        self.assertEqual(2000, BOARD[39].rents[5])


if __name__ == '__main__':
    unittest.main()
