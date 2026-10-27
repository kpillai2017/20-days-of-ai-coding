# Learning Python by following a turn

Start the game first. Roll, buy a property, end a turn, then return here. You
learn more easily when a variable refers to something you have just seen.

## 1. A printed board is not the changing game

Open `data.py`. `Property` is a frozen **dataclass**: Python generates a useful
constructor, comparison and representation. `frozen=True` prevents accidental
changes to the printed rent table. `BOARD[39]` is always Mayfair.

Open `engine.py`. `Deed` is a different dataclass: its `owner`, `houses` and
`mortgaged` fields change. `Player` holds cash, position and held cards.

```python
from engine import Game

game = Game([('You', False), ('Computer', True)], seed=42)
print(game.players[0].cash)     # 1500
print(game.board[39].name)     # Mayfair
print(game.properties[39])     # initially unowned
```

A player's list index is their identity. `None` means the bank owns a deed;
**zero is a real player**, so `if deed.owner:` is a bug. Use `is not None`.

## 2. Legal choices are data

Run this in a Python prompt from this folder:

```python
for label, command in game.actions():
    print(label, '=>', command)
game.act('roll')
print(game.phase)
print('\n'.join(game.log[-5:]))
```

`actions()` returns friendly labels and machine-readable command strings.
The UI draws the labels. The AI reads the commands. Both call the same `act()`.
A fabricated command raises `ValueError` **before any state changes**.

This is a small command architecture. It is easier to test than rules buried
inside mouse handlers. A useful extension is replacing strings with typed
command objects once this structure feels familiar.

## 3. The game is a state machine

A state machine has a current state and a finite set of valid transitions:

```text
roll → buy → end → next player's roll
         ↘ auction ↗
roll → effects → debt → raise cash → settle → remaining effects
                      ↘ bankruptcy → estate processing
any completed estate/effects → one survivor → gameover
```

`current` identifies whose turn is in progress. `actor` identifies who must make
the next decision. They differ during an auction, another player's payment,
mortgage inheritance or between-turn management. Confusing them would make a
player pay somebody else's bill. The UI therefore highlights `actor`.

## 4. A queue remembers unfinished business

A `collections.deque` efficiently removes the first queued event with
`popleft()`. `_drain()` processes automatic events until a decision is needed.

Example: a player fails their third jail roll but has only £20:

1. Queue `pay £50` followed by `jailmove(original dice)`.
2. The payment cannot run, so save `debt` and pause.
3. The player mortgages a deed. This is a decision, not automatic processing.
4. `settle` prepends the interrupted payment and drains again.
5. The queued movement still holds the original dice; no accidental reroll.

This same technique is useful for shopping checkout, workflow tools and games
with multi-step spells. The queue is explicit data instead of nested anonymous
callbacks that are difficult to inspect or save.

## 5. Count physical resources, not just money

Buildings have levels 0–5; level 5 means **one hotel**. It is not five physical
houses. Converting level 4 to 5 returns four houses and consumes one hotel.

Two invariants should always hold:

```python
assert game.houses_left + sum(
    deed.houses for deed in game.properties.values() if deed.houses < 5
) == 32
assert game.hotels_left + sum(
    deed.houses == 5 for deed in game.properties.values()
) == 12
```

Python booleans behave as 0/1 when summed. The second expression counts hotels.
Invariants detect bugs after thousands of turns, not merely in one example.

Even building uses `min(levels)`; even selling uses `max(levels)`. Those checks
encode the rule more clearly than enumerating every possible building pattern.
Read RULES.md for remaining contested-shortage limitations.

## 6. Trades are transactions

`trade()` first checks the phase, identities, ownership, duplicate entries,
construction, money, held cards and mortgage interest. Only after **all** checks
pass does it change balances and deeds. This all-or-nothing pattern is called
**atomic validation**. It is not a database transaction, but the idea is similar.

The UI adds another separate concern: **consent**. Submitting an offer does not
transfer it. A human recipient sees accept/reject; an AI recipient evaluates it.
Tests should check rejection leaves both cash and ownership unchanged.

## 7. A simple computer opponent

Read `ai.py`. It chooses from engine-approved commands. In debt it settles when
possible, then tries mortgages and sales. Normally it keeps a building cash
buffer. Its auction valuation uses face prices, not a deep probability model.

`proposal()` looks for a missing colour set and offers a premium to another
computer. The seller will not dismantle an existing monopoly. This is important:
without trading, all-bot games can circulate GO money for a very long time.

Heuristics are explainable but imperfect. Improve them with tests rather than
adding secret cash, manipulated dice or information unavailable to a human.

## 8. The Pygame event loop

`main.py` repeats input → one possible AI action → render → frame limit.
`pygame.time.Clock().tick(60)` caps drawing at 60 frames per second. A separate
350 ms delay controls computer decision pacing; there is no blocking `sleep()`.
This keeps window movement, help and quitting responsive on computer turns.

`--frames 30` is a **test exit count**, not a frame-rate option.

The visual system is documented in [DESIGN.md](DESIGN.md). Reusable `panel()`,
`button()`, `fit_text()` and `dice()` helpers keep styling separate from rules.
The journal is a read-only modal, just like the collection view. System fonts
are cached; no font files or commercial game artwork are shipped.

The UI draws to a 1320 × 940 logical surface. Window resizing scales it uniformly
and adds black borders. A mouse point is transformed back with:

```text
logical_x = (physical_x - horizontal_border) / scale
logical_y = (physical_y - vertical_border) / scale
```

Drawing and hit testing share the same square/button rectangles. See
`tests/test_ui.py`: it finds a drawn button, creates a real mouse event at that
button, dispatches it, and checks the resulting game state.

### Availability and read-only player cards

A button's visual state must match its behaviour. `button(..., enabled=False)`
uses a muted palette and LOCKED text, and **does not** add an input target to
`buttons`. Human actions use a green outline and READY text. The HUD derives
availability from both `game.actions()` (rules legality) and the actor's
controller (human versus computer). Disabled rectangles consume clicks instead
of letting them fall through to the board. The engine still validates every
command: UI styling is not a substitute for rule validation.

Player rows are separate read-only inspection controls. Clicking a name sets
`holdings_player`, resets the page and opens the holdings modal. `holdings()`
reads ownership from the engine rather than maintaining a second, stale list.
Fourteen deeds per page covers all 28 purchasable squares in two pages. Utility
rent is shown as a dice multiplier, not a misleading fixed amount.

A modal clears background hit targets, dims the board and pauses AI updates.
Closing it changes no cash, ownership or turn state. Ordinary Chance and Chest
cards are not retained: only jail-free cards appear in a player's held cards.

## 9. Test the rule, not the code's self-description

```sh
python -m unittest discover -s tests -v
```

A test saying "there are 40 spaces" is useful, but weak. Stronger examples:
- Mayfair's hotel rent is independently expected to be £2000.
- Jail doubles release does not grant another roll.
- Rejecting a trade changes nothing.
- Every board rectangle selects its exact square, at scaled coordinates.
- Complete seeded AI games conserve building tokens and never go negative.

A seed produces reproducible randomness; it does not mean a strong strategy.
Tests do not prove all rules perfect. Read the explicitly listed gaps before
assuming an untested edge case is supported.

## Try these exercises

1. Add a second named AI strategy without changing `engine.py`.
2. Highlight a complete colour set on the board.
3. Add an expected rent-table test for every printed street value.
4. Design proper building-shortage auctions and tests before changing the UI.
5. Design mortgage-transfer immediate-redemption choices as an atomic trade.
6. Add versioned save/load for queued effects, deck order and RNG state.

Keep rules, strategy and presentation separate as you experiment. That separation
is the main reusable software-design lesson in this project.
