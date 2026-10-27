"""Independent edge cases and full seeded games, not just short action samples."""
import unittest
from engine import Game
from ai import choose_action, proposal
from data import BOARD


class Regressions(unittest.TestCase):
    """Explicit arrangements make each financial consequence easy to inspect."""
    def game(self, count=3):
        game = Game([(str(i), True) for i in range(count)], 42)
        game.current = game.actor = 0
        return game

    def test_all_street_rent_tables(self):
        expected = {
            1:(2,10,30,90,160,250),3:(4,20,60,180,320,450),
            6:(6,30,90,270,400,550),8:(6,30,90,270,400,550),9:(8,40,100,300,450,600),
            11:(10,50,150,450,625,750),13:(10,50,150,450,625,750),14:(12,60,180,500,700,900),
            16:(14,70,200,550,750,950),18:(14,70,200,550,750,950),19:(16,80,220,600,800,1000),
            21:(18,90,250,700,875,1050),23:(18,90,250,700,875,1050),24:(20,100,300,750,925,1100),
            26:(22,110,330,800,975,1150),27:(22,110,330,800,975,1150),29:(24,120,360,850,1025,1200),
            31:(26,130,390,900,1100,1275),32:(26,130,390,900,1100,1275),34:(28,150,450,1000,1200,1400),
            37:(35,175,500,1100,1300,1500),39:(50,200,600,1400,1700,2000),
        }
        for index, rents in expected.items():
            self.assertEqual(rents, BOARD[index].rents)

    def test_back_three_chains_to_chest(self):
        game = self.game()
        game.players[0].position = 36
        game.decks['chance'] = [('back3', 'Back three')]
        game.decks['chest'] = [('error', 'Bank error')]
        game._card('chance')
        game._drain()
        self.assertEqual(33, game.players[0].position)
        self.assertEqual(1700, game.players[0].cash)

    def test_nearest_station_passes_go_and_doubles_rent(self):
        game = self.game()
        game.players[0].position = 36
        game.properties[5].owner = 1
        game.decks['chance'] = [('rail1', 'Station')]
        game._card('chance')
        game._drain()
        self.assertEqual(5, game.players[0].position)
        self.assertEqual(1650, game.players[0].cash)
        self.assertEqual(1550, game.players[1].cash)

    def test_nearest_utility_uses_fresh_dice(self):
        game = self.game()
        game.players[0].position = 7
        game.properties[12].owner = 1
        game.decks['chance'] = [('utility', 'Utility')]
        def fresh():
            game.dice_values = (4, 5)
            return game.dice_values
        game.roll_dice = fresh
        game._card('chance')
        game._drain()
        self.assertEqual(1410, game.players[0].cash)

    def test_third_jail_roll_debt_preserves_original_dice(self):
        game = self.game()
        game.players[0].jailed = 3
        game.players[0].position = 10
        game.players[0].cash = 0
        game.properties[39].owner = 0
        def dice():
            game.dice_values = (1, 2)
            return game.dice_values
        game.roll_dice = dice
        game.act('roll')
        self.assertEqual('debt', game.phase)
        game.act('mortgage:39')
        game.act('settle')
        self.assertEqual(13, game.players[0].position)
        self.assertEqual('buy', game.phase)
        self.assertEqual(150, game.players[0].cash)
        self.assertFalse(game.extra_roll)

    def test_bankrupt_jail_fine_cancels_pending_movement(self):
        game = self.game()
        game.players[0].jailed = 3
        game.players[0].position = 10
        game.players[0].cash = 0
        def dice():
            game.dice_values = (1, 2)
            return game.dice_values
        game.roll_dice = dice
        game.act('roll')
        game.act('bankrupt')
        self.assertTrue(game.players[0].bankrupt)
        self.assertEqual(10, game.players[0].position)
        self.assertEqual(1, game.current)
        self.assertEqual('roll', game.phase)

    def test_park_place_transfer_rounds_up(self):
        game = self.game()
        game.properties[37].owner = 0
        game.properties[37].mortgaged = True
        self.assertTrue(game.trade(0, 1, [37], []))
        self.assertEqual(1482, game.players[1].cash)

    def test_unmortgaged_group_member_still_collects_double_base(self):
        game = self.game()
        for index in (1, 3):
            game.properties[index].owner = 0
        game.properties[3].mortgaged = True
        self.assertEqual(4, game.rent(1))
        self.assertEqual(0, game.rent(3))

    def test_bad_command_is_atomic(self):
        game = self.game()
        before = repr(game.players), repr(game.properties), list(game.log)
        with self.assertRaises(ValueError):
            game.act('build:39')
        self.assertEqual(before, (repr(game.players), repr(game.properties), list(game.log)))

    def test_twenty_complete_ai_games_conserve_resources(self):
        for seed in range(20):
            game = Game([(str(i), True) for i in range(4)], seed)
            for step in range(10000):
                if game.phase == 'gameover':
                    break
                offer = proposal(game) if game.phase in ('roll', 'end') else None
                if offer is None or not game.trade(*offer):
                    game.act(choose_action(game))
                self.assertTrue(all(p.cash >= 0 for p in game.players), (seed, step))
                self.assertEqual(32, game.houses_left + sum(d.houses for d in game.properties.values() if d.houses < 5))
                self.assertEqual(12, game.hotels_left + sum(d.houses == 5 for d in game.properties.values()))
                self.assertTrue(all(d.owner is None or not game.players[d.owner].bankrupt for d in game.properties.values()))
            self.assertEqual('gameover', game.phase, seed)
            self.assertEqual(1, sum(not p.bankrupt for p in game.players))


if __name__ == '__main__':
    unittest.main()
