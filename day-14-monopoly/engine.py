"""Testable, event-driven rules for a classic British Monopoly game.

The window never changes cash or ownership itself. It asks actions() for legal
commands, then sends one to act(). A queue preserves unfinished card payments
when a player must stop to raise money. No pygame import is needed here.
"""
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional
from data import BOARD, CHANCE_CARDS, COMMUNITY_CHEST_CARDS, TAX_AMOUNTS, GO_SALARY


@dataclass
class Player:
    """Mutable information belonging to one seat at the table."""
    name: str
    is_ai: bool
    cash: int = 1500
    position: int = 0
    jailed: int = 0  # 0 means free; 1 means no unsuccessful jail rolls yet.
    bankrupt: bool = False
    jail_cards: list = field(default_factory=list)  # deck names, not just a count


@dataclass
class Deed:
    """Ownership is not part of the immutable printed board data."""
    owner: Optional[int] = None
    houses: int = 0  # 5 is one hotel, NOT five physical houses.
    mortgaged: bool = False


class Game:
    """One local game. All random choices use a private, seedable generator."""

    def __init__(self, names, seed=None):
        if not 2 <= len(names) <= 6:
            raise ValueError('Choose two to six players.')
        if any(not isinstance(n, str) or not n.strip() for n, _ in names):
            raise ValueError('Every player needs a name.')
        self.rng = random.Random(seed)
        self.players = [Player(n.strip(), bool(ai)) for n, ai in names]
        self.board = BOARD
        self.properties = {p.index: Deed() for p in BOARD if p.price}
        self.decks = {'chance': list(CHANCE_CARDS), 'chest': list(COMMUNITY_CHEST_CARDS)}
        for deck in self.decks.values():
            self.rng.shuffle(deck)
        self.log = []
        # Public draw history is separate from shuffled deck order. The GUI can
        # inspect this without exposing a future card or parsing journal text.
        self.last_cards = {'chance': None, 'chest': None}
        # Highest starting roll goes first; ties roll off. This is done once,
        # before play, rather than confusing the first turn with a normal roll.
        candidates = list(range(len(names)))
        while len(candidates) > 1:
            scores = {i: sum(self.roll_dice()) for i in candidates}
            best = max(scores.values())
            self.log.append('Starting rolls: ' + ', '.join(f'{self.players[i].name} {v}' for i, v in scores.items()))
            candidates = [i for i in candidates if scores[i] == best]
        self.current = candidates[0]
        self.actor = self.current
        self.phase = 'roll'
        self.dice_values = (0, 0)
        self.doubles_count = 0
        self.extra_roll = False
        self.events = deque()
        self.debt = None
        self.auction = None
        self.transfer = None
        self.manager_return = None
        self.winner = None
        self.houses_left = 32
        self.hotels_left = 12
        self.log.append(f'{self.players[self.current].name} starts. All seats receive £1500.')

    def roll_dice(self):
        """Return two independent fair dice; tests may replace this method."""
        self.dice_values = (self.rng.randint(1, 6), self.rng.randint(1, 6))
        return self.dice_values

    def group(self, index):
        """Return streets in this colour group (stations are not a monopoly)."""
        square = BOARD[index]
        return [p.index for p in BOARD if p.kind == 'street' and p.group == square.group]

    def owns_group(self, owner, index):
        """A complete set is needed to build and doubles bare-site rent."""
        group = self.group(index)
        return bool(group) and all(self.properties[i].owner == owner for i in group)

    def rent(self, index, dice=None, special=None):
        """Calculate rent without moving money. Mortgaged sites earn nothing."""
        deed = self.properties[index]
        square = BOARD[index]
        if deed.owner is None or deed.mortgaged:
            return 0
        if square.kind == 'street':
            result = square.rents[deed.houses]
            if not deed.houses and self.owns_group(deed.owner, index):
                result *= 2
            return result
        count = sum(1 for i, d in self.properties.items()
                    if d.owner == deed.owner and BOARD[i].kind == square.kind)
        if square.kind == 'station':
            return 25 * 2 ** (count - 1) * (2 if special == 'rail' else 1)
        return (dice if dice is not None else sum(self.dice_values)) * (10 if count == 2 or special == 'utility' else 4)

    def _say(self, message):
        """Keep a readable event history; the renderer wraps the visible tail."""
        self.log.append(message)

    def _move(self, destination, salary=True):
        """Move forward to an absolute square. Back-three calls opt out of GO."""
        player = self.players[self.current]
        if salary and destination < player.position:
            player.cash += GO_SALARY
            self._say(f'{player.name} passes GO: +£{GO_SALARY}.')
        player.position = destination
        self._say(f'{player.name} lands on {BOARD[destination].name}.')

    def _jail(self):
        """Going to jail ends the turn, including any doubles entitlement."""
        player = self.players[self.current]
        player.position = 10
        player.jailed = 1
        self.extra_roll = False
        self.doubles_count = 0
        self._say(f'{player.name} goes directly to jail; no GO salary.')

    def _land(self, special=None):
        """Queue financial consequences instead of hiding a debt in a callback."""
        player = self.players[self.current]
        index = player.position
        square = BOARD[index]
        if index == 30:
            self._jail()
        elif square.price:
            deed = self.properties[index]
            if deed.owner is None:
                self.phase = 'buy'
                self.actor = self.current
                return
            if deed.owner != self.current:
                dice = sum(self.roll_dice()) if special == 'utility' else sum(self.dice_values)
                self.events.appendleft(('pay', self.current, self.rent(index, dice, special), deed.owner))
        elif square.kind in ('chance', 'chest'):
            self._card(square.kind)
        elif square.kind == 'tax':
            self.events.appendleft(('pay', self.current, TAX_AMOUNTS[index], None))
        # GO, Just Visiting and Free Parking do not have extra effects.

    def _card(self, deck_name):
        """Draw from the front, replace underneath unless this is a held card."""
        deck = self.decks[deck_name]
        code, text = deck.pop(0)
        self.last_cards[deck_name] = {'code': code, 'text': text, 'player': self.current}
        self._say(f'{deck_name.title()}: {text}.')
        if code == 'jailfree':
            self.players[self.current].jail_cards.append(deck_name)
            return
        deck.append((code, text))
        player = self.players[self.current]
        if code == 'jail':
            self._jail()
        elif code == 'back3':
            self._move((player.position - 3) % 40, False)
            self.events.appendleft(('land', None))
        elif code == 'go' or code.startswith('move') or code.startswith('rail') or code == 'utility':
            special = None
            if code == 'go':
                destination = 0
            elif code.startswith('move'):
                destination = int(code[4:])
            else:
                choices = (5, 15, 25, 35) if code.startswith('rail') else (12, 28)
                destination = min(choices, key=lambda i: (i - player.position) % 40 or 40)
                special = 'rail' if code.startswith('rail') else 'utility'
            self._move(destination)
            self.events.appendleft(('land', special))
        elif code == 'repairs':
            houses = sum(d.houses for d in self.properties.values() if d.owner == self.current and d.houses < 5)
            hotels = sum(d.houses == 5 for d in self.properties.values() if d.owner == self.current)
            rates = (25, 100) if deck_name == 'chance' else (40, 115)
            self.events.appendleft(('pay', self.current, houses * rates[0] + hotels * rates[1], None))
        elif code in ('chairman', 'birthday'):
            # Put each participant on the queue separately. If one goes bankrupt,
            # subsequent payments still happen, with their own proper creditor.
            events = []
            for i, other in enumerate(self.players):
                if i != self.current and not other.bankrupt:
                    events.append(('pay', self.current, 50, i) if code == 'chairman' else ('pay', i, 10, self.current))
            self.events.extendleft(reversed(events))
        else:
            gains = {'dividend': 50, 'loan': 150, 'error': 200, 'stock': 50,
                     'holiday': 100, 'refund': 20, 'insurance': 100,
                     'consultancy': 25, 'beauty': 10, 'inherit': 100}
            losses = {'speed': 15, 'doctor': 50, 'hospital': 100, 'school': 50}
            if code in gains:
                player.cash += gains[code]
            else:
                self.events.appendleft(('pay', self.current, losses[code], None))

    def _drain(self):
        """Run queued automatic effects until a human/AI decision is needed."""
        self.phase = 'resolving'
        while self.events:
            event = self.events.popleft()
            kind = event[0]
            if kind == 'pay':
                _, debtor, amount, creditor = event
                if self.players[debtor].bankrupt or amount == 0:
                    continue
                if creditor is not None and self.players[creditor].bankrupt:
                    creditor = None
                if self.players[debtor].cash < amount:
                    self.debt = (debtor, amount, creditor)
                    self.actor = debtor
                    self.phase = 'debt'
                    self._say(f'{self.players[debtor].name} must raise £{amount}; cash £{self.players[debtor].cash}.')
                    return
                self.players[debtor].cash -= amount
                if creditor is not None:
                    self.players[creditor].cash += amount
                self._say(f'{self.players[debtor].name} pays £{amount} to ' + ('bank.' if creditor is None else self.players[creditor].name + '.'))
            elif kind == 'land':
                if self.players[self.current].bankrupt:
                    continue
                self._land(event[1])
                if self.phase == 'buy':
                    return
            elif kind == 'jailmove':
                if self.players[self.current].bankrupt:
                    continue
                self.players[self.current].jailed = 0
                self._move((10 + event[1]) % 40)
                self.events.appendleft(('land', None))
            elif kind == 'released':
                if self.players[self.current].bankrupt:
                    continue
                self.players[self.current].jailed = 0
                self.phase = 'roll'
                self.actor = self.current
                return
            elif kind == 'transfer':
                _, owner, index = event
                if not self.players[owner].bankrupt and self.properties[index].owner == owner:
                    self.transfer = (owner, index)
                    self.actor = owner
                    self.phase = 'transfer'
                    return
            elif kind == 'auction':
                self._start_auction(event[1])
                return
        self._finish_resolution()

    def _finish_resolution(self):
        """Restore the interrupted turn or declare the sole survivor winner."""
        survivors = [i for i, p in enumerate(self.players) if not p.bankrupt]
        if len(survivors) == 1:
            self.winner = survivors[0]
            self.phase = 'gameover'
            self.actor = self.winner
            return
        if self.players[self.current].bankrupt:
            self._next_turn()
        else:
            self.phase = 'roll' if self.extra_roll else 'end'
            self.actor = self.current

    def _next_turn(self):
        """Skip eliminated seats; surviving jailed players still take turns."""
        self.current = (self.current + 1) % len(self.players)
        while self.players[self.current].bankrupt:
            self.current = (self.current + 1) % len(self.players)
        self.actor = self.current
        self.extra_roll = False
        self.doubles_count = 0
        self.phase = 'roll'
        self._say(f'Turn: {self.players[self.current].name}.')

    def _roll(self):
        """Roll normally or attempt jail release, preserving third-roll dice."""
        player = self.players[self.current]
        a, b = self.roll_dice()
        self._say(f'{player.name} rolls {a} + {b}.')
        if player.jailed:
            self.extra_roll = False
            if a == b:
                player.jailed = 0
                self._move((10 + a + b) % 40)
                self.events.append(('land', None))
            elif player.jailed == 3:
                self.events.extend([('pay', self.current, 50, None), ('jailmove', a + b)])
            else:
                player.jailed += 1
        else:
            self.extra_roll = a == b
            self.doubles_count = self.doubles_count + 1 if self.extra_roll else 0
            if self.doubles_count == 3:
                self._jail()
            else:
                self._move((player.position + a + b) % 40)
                self.events.append(('land', None))
        self._drain()

    def _start_auction(self, index):
        """A rising public auction. Passing withdraws; even the decliner bids."""
        eligible = [i for i, p in enumerate(self.players) if not p.bankrupt and p.cash > 0]
        self.auction = {'index': index, 'active': eligible, 'high': 0, 'leader': None}
        if not eligible:
            self.auction = None
            self._drain()
            return
        self.actor = eligible[0]
        self.phase = 'auction'
        self._say(f'Auction: {BOARD[index].name}; opening bid £1 or higher.')

    def _auction_step(self, command):
        """Award only after every other bidder withdraws or cannot outbid."""
        auction = self.auction
        old_actor = self.actor
        if command == 'pass':
            auction['active'].remove(old_actor)
        else:
            bid = int(command.split(':')[1])
            self.players[old_actor]  # actor's cash was checked by actions()
            auction['high'] = bid
            auction['leader'] = old_actor
        leader = auction['leader']
        active = [i for i in auction['active'] if i == leader or self.players[i].cash > auction['high']]
        auction['active'] = active
        challengers = [i for i in active if i != leader]
        if not challengers:
            if leader is not None:
                self.players[leader].cash -= auction['high']
                self.properties[auction['index']].owner = leader
                self._say(f'{self.players[leader].name} wins {BOARD[auction["index"]].name} for £{auction["high"]}.')
            self.auction = None
            self._drain()
            return
        self.actor = min(challengers, key=lambda i: (i - old_actor) % len(self.players) or len(self.players))

    def _management(self, owner):
        """List one-step legal property operations, enforcing even development."""
        result = []
        player = self.players[owner]
        for i, deed in self.properties.items():
            if deed.owner != owner:
                continue
            square = BOARD[i]
            group = self.group(i)
            developed = any(self.properties[j].houses for j in group)
            if not deed.mortgaged and not developed:
                result.append((f'Mortgage {square.name}: +£{square.mortgage_value}', f'mortgage:{i}'))
            cost = (square.mortgage_value * 110 + 99) // 100
            if deed.mortgaged and player.cash >= cost and self.phase != 'debt':
                result.append((f'Redeem {square.name}: £{cost}', f'unmortgage:{i}'))
            if square.kind != 'street':
                continue
            levels = [self.properties[j].houses for j in group]
            if (self.phase != 'debt' and self.owns_group(owner, i)
                    and not any(self.properties[j].mortgaged for j in group)
                    and deed.houses == min(levels) and deed.houses < 5
                    and player.cash >= square.house_cost
                    and (self.hotels_left if deed.houses == 4 else self.houses_left) > 0):
                result.append((f'Build on {square.name}: £{square.house_cost}', f'build:{i}'))
            if deed.houses and deed.houses == max(levels):
                if deed.houses < 5 or self.houses_left >= 4:
                    result.append((f'Sell building on {square.name}: +£{square.house_cost // 2}', f'sell:{i}'))
                # If four houses are unavailable, liquidate the whole group at
                # half cost; do not conjure nonexistent houses to break a hotel.
                if deed.houses == 5 and self.houses_left < 4:
                    result.append((f'Sell all buildings in {square.group} group', f'sellgroup:{i}'))
        return result

    def actions(self):
        """Return labelled commands. Invalid commands must never mutate state."""
        if self.phase == 'gameover':
            return []
        player = self.players[self.actor]
        result = []
        if self.phase == 'auction':
            high = self.auction['high']
            for bid in sorted(set((high + 1, high + 10, high + 50, high + 100, player.cash))):
                if high < bid <= player.cash:
                    result.append((f'Bid £{bid}', f'bid:{bid}'))
            return result + [('Withdraw from auction', 'pass')]
        if self.phase == 'transfer':
            _, index = self.transfer
            value = BOARD[index].mortgage_value
            interest = (value + 9) // 10
            return [(f'Keep mortgage; pay £{interest} interest now', 'transfer_keep'),
                    (f'Redeem inherited mortgage: £{value + interest}', 'transfer_redeem')]
        if self.manager_return is not None:
            result.append(('Finish property management', 'manage_done'))
        elif self.phase == 'roll':
            result.append(('Roll dice / attempt doubles' if player.jailed else 'Roll dice', 'roll'))
            if player.jailed:
                result.append(('Pay £50 to leave jail before rolling', 'jailpay'))
                if player.jail_cards:
                    result.append(('Use a Get Out of Jail Free card', 'jailcard'))
        elif self.phase == 'end':
            result.append(('End turn', 'end'))
        elif self.phase == 'buy':
            square = BOARD[player.position]
            if player.cash >= square.price:
                result.append((f'Buy {square.name} for £{square.price}', 'buy'))
            result.append(('Decline purchase: auction to ALL players', 'auction'))
        elif self.phase == 'debt':
            if player.cash >= self.debt[1]:
                result.append((f'Pay outstanding £{self.debt[1]}', 'settle'))
            # Bankruptcy is only legal after raising all possible bank funds;
            # trades can still rescue an otherwise insolvent estate.
            if self.liquidation_value(self.actor) < self.debt[1]:
                result.append(('Declare bankruptcy to creditor', 'bankrupt'))
        result.extend(self._management(self.actor))
        if self.phase in ('roll', 'end') and self.manager_return is None:
            for i, other in enumerate(self.players):
                if i != self.current and not other.bankrupt:
                    result.append((f'{other.name}: manage property / trade between turns', f'manage:{i}'))
        return result

    def liquidation_value(self, owner):
        """Maximum cash from selling all buildings and mortgaging all deeds."""
        value = self.players[owner].cash
        for i, deed in self.properties.items():
            if deed.owner == owner:
                value += (0 if deed.mortgaged else BOARD[i].mortgage_value)
                value += deed.houses * BOARD[i].house_cost // 2
        return value

    def _building(self, i, direction):
        """Exchange physical tokens with the finite bank when developing."""
        deed = self.properties[i]
        if direction == 1:
            if deed.houses == 4:
                self.houses_left += 4
                self.hotels_left -= 1
            else:
                self.houses_left -= 1
        elif deed.houses == 5:
            self.hotels_left += 1
            self.houses_left -= 4
        else:
            self.houses_left += 1
        deed.houses += direction
        player = self.players[deed.owner]
        player.cash += -BOARD[i].house_cost if direction == 1 else BOARD[i].house_cost // 2

    def act(self, command):
        """Validate first, then perform exactly one legal decision."""
        if command not in {cmd for _, cmd in self.actions()}:
            raise ValueError(f'Action is not legal now: {command}')
        player = self.players[self.actor]
        if command.startswith('manage:'):
            self.manager_return = (self.phase, self.actor)
            self.actor = int(command.split(':')[1])
        elif command == 'manage_done':
            self.phase, self.actor = self.manager_return
            self.manager_return = None
        elif command == 'roll':
            self._roll()
        elif command in ('jailpay', 'jailcard'):
            if command == 'jailcard':
                deck = player.jail_cards.pop(0)
                original = CHANCE_CARDS if deck == 'chance' else COMMUNITY_CHEST_CARDS
                self.decks[deck].append(next(card for card in original if card[0] == 'jailfree'))
                player.jailed = 0
            else:
                self.events.extend([('pay', self.actor, 50, None), ('released',)])
                self._drain()
        elif command == 'buy':
            index = player.position
            player.cash -= BOARD[index].price
            self.properties[index].owner = self.actor
            self._say(f'{player.name} buys {BOARD[index].name}.')
            self._drain()
        elif command == 'auction':
            self._start_auction(player.position)
        elif self.phase == 'auction':
            self._auction_step(command)
        elif command == 'end':
            self._next_turn()
        elif command == 'settle':
            debtor, amount, creditor = self.debt
            self.debt = None
            self.events.appendleft(('pay', debtor, amount, creditor))
            self._drain()
        elif command == 'bankrupt':
            self._bankrupt()
        elif command.startswith('transfer_'):
            owner, index = self.transfer
            value = BOARD[index].mortgage_value
            amount = (value + 9) // 10
            if command == 'transfer_redeem':
                amount += value
                self.properties[index].mortgaged = False
            self.transfer = None
            self.events.appendleft(('pay', owner, amount, None))
            self._drain()
        else:
            operation, text = command.split(':')
            index = int(text)
            deed = self.properties[index]
            if operation == 'mortgage':
                deed.mortgaged = True
                player.cash += BOARD[index].mortgage_value
            elif operation == 'unmortgage':
                deed.mortgaged = False
                player.cash -= (BOARD[index].mortgage_value * 110 + 99) // 100
            elif operation == 'build':
                self._building(index, 1)
            elif operation == 'sell':
                self._building(index, -1)
            elif operation == 'sellgroup':
                for i in self.group(index):
                    d = self.properties[i]
                    player.cash += d.houses * BOARD[i].house_cost // 2
                    if d.houses == 5:
                        self.hotels_left += 1
                    else:
                        self.houses_left += d.houses
                    d.houses = 0
            self._say(f'{player.name}: {operation} {BOARD[index].name}.')

    def _bankrupt(self):
        """Transfer an estate, with mortgage interest and bank auctions queued."""
        owner, amount, creditor = self.debt
        player = self.players[owner]
        player.bankrupt = True
        self.debt = None
        # A player's buildings are sold back at half price before an estate
        # passes to another player. Unpaid remaining debt is then written off.
        cash = player.cash
        inherited = []
        for i, deed in self.properties.items():
            if deed.owner != owner:
                continue
            cash += deed.houses * BOARD[i].house_cost // 2
            if deed.houses == 5:
                self.hotels_left += 1
            else:
                self.houses_left += deed.houses
            deed.houses = 0
            deed.owner = creditor
            if creditor is None:
                deed.mortgaged = False
                inherited.append(('auction', i))
            elif deed.mortgaged:
                inherited.append(('transfer', creditor, i))
        if creditor is not None:
            self.players[creditor].cash += cash
            self.players[creditor].jail_cards.extend(player.jail_cards)
        else:
            for deck in player.jail_cards:
                original = CHANCE_CARDS if deck == 'chance' else COMMUNITY_CHEST_CARDS
                self.decks[deck].append(next(card for card in original if card[0] == 'jailfree'))
        player.cash = 0
        player.jail_cards.clear()
        self._say(f'{player.name} is bankrupt; estate goes to ' + ('bank.' if creditor is None else self.players[creditor].name + '.'))
        self.events.extendleft(reversed(inherited))
        self._drain()

    def trade(self, proposer, other, give_indices, take_indices,
              cash_offer=0, cash_request=0, give_card=False, take_card=False):
        """Execute a CONSENTED exchange atomically; UI obtains consent first.

        Properties in a developed colour group cannot be traded. A mortgaged
        deed immediately costs its recipient 10% interest; keeping the loan
        does not waive the later redemption interest. This method pays that
        initial interest atomically (the editor requires sufficient cash).
        """
        if self.phase not in ('roll', 'end', 'debt') or proposer != self.actor:
            return False
        if not (0 <= other < len(self.players)) or proposer == other:
            return False
        a, b = self.players[proposer], self.players[other]
        if a.bankrupt or b.bankrupt:
            return False
        if any(type(value) is not int or value < 0 for value in (cash_offer, cash_request)):
            return False
        give, take = list(give_indices), list(take_indices)
        if len(set(give + take)) != len(give + take):
            return False
        for indices, owner in ((give, proposer), (take, other)):
            for i in indices:
                if i not in self.properties or self.properties[i].owner != owner:
                    return False
                if any(self.properties[j].houses for j in self.group(i)):
                    return False
        if (give_card and not a.jail_cards) or (take_card and not b.jail_cards):
            return False
        fee_a = sum((BOARD[i].mortgage_value + 9) // 10 for i in take if self.properties[i].mortgaged)
        fee_b = sum((BOARD[i].mortgage_value + 9) // 10 for i in give if self.properties[i].mortgaged)
        if (a.cash < cash_offer or b.cash < cash_request
                or a.cash - cash_offer + cash_request < fee_a
                or b.cash - cash_request + cash_offer < fee_b):
            return False
        a.cash += cash_request - cash_offer - fee_a
        b.cash += cash_offer - cash_request - fee_b
        for i in give:
            self.properties[i].owner = other
        for i in take:
            self.properties[i].owner = proposer
        # Snapshot the physical card identity before swapping two cards.
        card_a = a.jail_cards.pop(0) if give_card else None
        card_b = b.jail_cards.pop(0) if take_card else None
        if card_a:
            b.jail_cards.append(card_a)
        if card_b:
            a.jail_cards.append(card_b)
        self._say(f'{a.name} and {b.name} agree a trade; bank interest £{fee_a + fee_b}.')
        return True
