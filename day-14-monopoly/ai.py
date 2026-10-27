"""Small, transparent computer strategy, not a learning model or perfect player.

The engine decides legality; this module only chooses among legal commands.
Keeping those roles separate prevents the computer from cheating accidentally.
"""
from data import BOARD


def accept_trade(game, proposer, other, give_indices, take_indices,
                 cash_offer=0, cash_request=0, give_card=False, take_card=False):
    """The recipient values deeds at face value and completing sets highly."""
    def value(indices, owner):
        """Value incoming deeds and reward completing the recipient's set."""
        total = 0
        for i in indices:
            deed = game.properties[i]
            total += BOARD[i].price - (BOARD[i].mortgage_value * 1.1 if deed.mortgaged else 0)
            group = game.group(i)
            if group and all(game.properties[j].owner == owner or j in indices for j in group):
                total += BOARD[i].price
        return total
    receive = value(give_indices, other) + cash_offer + 40 * bool(give_card)
    lose = sum(BOARD[i].price * (2 if game.owns_group(other, i) else 1)
               - (BOARD[i].mortgage_value * 1.1 if game.properties[i].mortgaged else 0)
               for i in take_indices) + cash_request + 40 * bool(take_card)
    return receive > 0 and receive >= lose * 1.10


def proposal(game):
    """Offer a cash premium for missing deeds that would complete a colour set.

    Computers negotiate only with computers; a human never silently consents.
    The seller will not dismantle an existing monopoly. This simple policy
    avoids the common all-bot stalemate where no one ever completes a set.
    """
    buyer = game.actor
    for index, deed in game.properties.items():
        if BOARD[index].kind != 'street' or deed.owner != buyer:
            continue
        missing = [i for i in game.group(index) if game.properties[i].owner != buyer]
        if not missing or any(game.properties[i].owner is None for i in missing):
            continue
        owners = {game.properties[i].owner for i in missing}
        if len(owners) != 1:
            continue
        seller = owners.pop()
        if not game.players[seller].is_ai or game.owns_group(seller, missing[0]):
            continue
        price = sum(BOARD[i].price for i in missing) * 5 // 4
        args = (buyer, seller, [], missing, price, 0, False, False)
        if game.players[buyer].cash >= price + 180 and accept_trade(game, *args):
            return args
    return None


def choose_action(game):
    """Choose exactly one action, leaving the event loop free to render."""
    options = game.actions()
    if not options:
        raise ValueError('No action is available.')
    commands = [command for _, command in options]
    player = game.players[game.actor]
    if 'manage_done' in commands:
        # A human may hand this AI a between-turn management opportunity.
        return 'manage_done'
    if game.phase == 'auction':
        index = game.auction['index']
        budget = min(player.cash, BOARD[index].price + (100 if game.owns_group(game.actor, index) else 0))
        bids = [cmd for cmd in commands if cmd.startswith('bid:') and int(cmd.split(':')[1]) <= budget]
        return min(bids, key=lambda cmd: int(cmd.split(':')[1])) if bids else 'pass'
    if game.phase == 'transfer':
        index = game.transfer[1]
        return 'transfer_redeem' if player.cash > BOARD[index].mortgage_value + 250 else 'transfer_keep'
    if game.phase == 'debt':
        if 'settle' in commands:
            return 'settle'
        # Liquidate before surrendering; mortgages do not lose a building's
        # half-price resale value, so prefer them to demolition when possible.
        for prefix in ('mortgage:', 'sell:', 'sellgroup:'):
            eligible = [cmd for cmd in commands if cmd.startswith(prefix)]
            if eligible:
                return eligible[0]
        return 'bankrupt'
    if game.phase == 'buy':
        return 'buy' if 'buy' in commands else 'auction'
    # Keep a cash buffer rather than putting every last dollar into buildings.
    for prefix in ('unmortgage:', 'build:'):
        for cmd in commands:
            if cmd.startswith(prefix):
                index = int(cmd.split(':')[1])
                cost = BOARD[index].house_cost if prefix == 'build:' else (BOARD[index].mortgage_value * 110 + 99) // 100
                if player.cash - cost >= 180:
                    return cmd
    if 'jailcard' in commands:
        return 'jailcard'
    if 'jailpay' in commands and player.cash >= 250:
        return 'jailpay'
    return 'roll' if 'roll' in commands else 'end'
