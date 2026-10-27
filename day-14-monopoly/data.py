"""Classic British board data, separated from the rules that change during play.

A street's six rents mean: bare site, one/two/three/four houses, hotel.
These are tables, not a formula: Mayfair does not follow a geometric series!
Card text below is a short functional description, not scanned card artwork.
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Property:
    """An immutable board square; ownership lives separately in engine.Deed."""
    index: int
    name: str
    kind: str
    price: int = 0
    group: Optional[str] = None
    rents: Tuple[int, ...] = ()
    house_cost: int = 0

    @property
    def mortgage_value(self):
        """The bank lends half the printed purchase price."""
        return self.price // 2


# Order is clockwise from GO. The index is also the player's position.
_NAMES = [
    'GO', 'Old Kent Road', 'Community Chest', 'Whitechapel Road',
    'Income Tax', 'King’s Cross Station', 'The Angel Islington', 'Chance',
    'Euston Road', 'Pentonville Road', 'Jail / Just Visiting',
    'Pall Mall', 'Electric Company', 'Whitehall', 'Northumberland Avenue',
    'Marylebone Station', 'Bow Street', 'Community Chest',
    'Marlborough Street', 'Vine Street', 'Free Parking', 'Strand',
    'Chance', 'Fleet Street', 'Trafalgar Square', 'Fenchurch Street Station',
    'Leicester Square', 'Coventry Street', 'Water Works', 'Piccadilly',
    'Go To Jail', 'Regent Street', 'Oxford Street', 'Community Chest',
    'Bond Street', 'Liverpool Street Station', 'Chance', 'Park Lane', 'Super Tax',
    'Mayfair',
]
# index: (price, colour, building cost, rent table)
_STREETS = {
    1: (60, 'brown', 50, (2, 10, 30, 90, 160, 250)),
    3: (60, 'brown', 50, (4, 20, 60, 180, 320, 450)),
    6: (100, 'light_blue', 50, (6, 30, 90, 270, 400, 550)),
    8: (100, 'light_blue', 50, (6, 30, 90, 270, 400, 550)),
    9: (120, 'light_blue', 50, (8, 40, 100, 300, 450, 600)),
    11: (140, 'pink', 100, (10, 50, 150, 450, 625, 750)),
    13: (140, 'pink', 100, (10, 50, 150, 450, 625, 750)),
    14: (160, 'pink', 100, (12, 60, 180, 500, 700, 900)),
    16: (180, 'orange', 100, (14, 70, 200, 550, 750, 950)),
    18: (180, 'orange', 100, (14, 70, 200, 550, 750, 950)),
    19: (200, 'orange', 100, (16, 80, 220, 600, 800, 1000)),
    21: (220, 'red', 150, (18, 90, 250, 700, 875, 1050)),
    23: (220, 'red', 150, (18, 90, 250, 700, 875, 1050)),
    24: (240, 'red', 150, (20, 100, 300, 750, 925, 1100)),
    26: (260, 'yellow', 150, (22, 110, 330, 800, 975, 1150)),
    27: (260, 'yellow', 150, (22, 110, 330, 800, 975, 1150)),
    29: (280, 'yellow', 150, (24, 120, 360, 850, 1025, 1200)),
    31: (300, 'green', 200, (26, 130, 390, 900, 1100, 1275)),
    32: (300, 'green', 200, (26, 130, 390, 900, 1100, 1275)),
    34: (320, 'green', 200, (28, 150, 450, 1000, 1200, 1400)),
    37: (350, 'blue', 200, (35, 175, 500, 1100, 1300, 1500)),
    39: (400, 'blue', 200, (50, 200, 600, 1400, 1700, 2000)),
}


def make_board():
    """Translate compact reference tables into helpful named objects."""
    board = []
    for i, name in enumerate(_NAMES):
        if i in _STREETS:
            price, group, cost, rents = _STREETS[i]
            square = Property(i, name, 'street', price, group, rents, cost)
        elif i in (5, 15, 25, 35):
            square = Property(i, name, 'station', 200, 'station', (25, 50, 100, 200))
        elif i in (12, 28):
            square = Property(i, name, 'utility', 150, 'utility', (4, 10))
        else:
            kind = 'chance' if i in (7, 22, 36) else 'chest' if i in (2, 17, 33) else 'tax' if i in (4, 38) else 'corner'
            square = Property(i, name, kind)
        board.append(square)
    return board


BOARD = make_board()
# Share fixed board payments with the renderer so printed amounts and the rules
# cannot drift apart. GO is a salary, not a second bonus for landing on it.
TAX_AMOUNTS = {4: 200, 38: 100}
GO_SALARY = 200
# A deck is a queue. A used card goes underneath; a held jail card stays out.
# Two nearest-station cards are deliberately distinct physical cards.
CHANCE_CARDS = [
    ('go', 'Advance to GO'), ('move24', 'Advance to Trafalgar Square'),
    ('move11', 'Advance to Pall Mall'),
    ('rail1', 'Advance to nearest station; pay double rent'),
    ('rail2', 'Advance to nearest station; pay double rent'),
    ('utility', 'Advance to nearest utility; fresh dice times ten'),
    ('dividend', 'Bank dividend: collect £50'),
    ('jailfree', 'Get out of jail free: keep until used or traded'),
    ('back3', 'Go back three spaces'), ('jail', 'Go directly to jail'),
    ('repairs', 'Repairs: £25 per house, £100 per hotel'),
    ('speed', 'Speeding fine: pay £15'),
    ('move5', 'Advance to King’s Cross Station'),
    ('move39', 'Advance to Mayfair'),
    ('chairman', 'Pay each other player £50'),
    ('loan', 'Building loan matures: collect £150'),
]
COMMUNITY_CHEST_CARDS = [
    ('go', 'Advance to GO'), ('error', 'Bank error: collect £200'),
    ('doctor', 'Doctor fee: pay £50'), ('stock', 'Stock sale: collect £50'),
    ('jailfree', 'Get out of jail free: keep until used or traded'),
    ('jail', 'Go directly to jail'), ('holiday', 'Holiday fund: collect £100'),
    ('refund', 'Tax refund: collect £20'),
    ('birthday', 'Collect £10 from each other player'),
    ('insurance', 'Life insurance: collect £100'),
    ('hospital', 'Hospital fee: pay £100'), ('school', 'School fee: pay £50'),
    ('consultancy', 'Consultancy fee: collect £25'),
    ('repairs', 'Street repairs: £40 per house, £115 per hotel'),
    ('beauty', 'Beauty contest: collect £10'),
    ('inherit', 'Inheritance: collect £100'),
]
