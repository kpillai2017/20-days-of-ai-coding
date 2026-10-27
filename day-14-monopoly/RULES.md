# Rules, edition and implementation boundary

## Which rules?

"Original rules" is ambiguous across editions and decades. We implement the
**classic British London 40-space board with fixed £200 Income Tax and £100 Super Tax**,
no Speed Die or shortened-game rules, and 16-card Chance/Community Chest
queues with London destinations and functional summaries. Card composition
varies across printings: these decks retain the existing classic functional
configuration and do not claim to reproduce a specific vintage British deck.
This is not a literal reproduction of a 1936 vintage edition or every variant.
Property names, stations and utilities reflect the London edition. Player count is
deliberately limited to the requested **2–6**.

The authoritative reference is Hasbro's rulebook linked in REFERENCES.md.
Edition-specific instructions supplied with a physical set take precedence
when playing that set. This implementation is not formally certified perfect.

## Implemented core rules

### Setup, turn order and movement

- Each player starts on GO with £1500; the bank has unlimited money. No cash-note
  denominations are simulated because only pound balances affect these rules.
- Highest two-dice starting roll goes first, with tied seats rolling off.
- Play proceeds in seat order. Dice are independent values from 1 through 6.
- Passing GO in normal forward movement or a forward movement card pays £200.
  Landing on GO does not pay a second bonus. Going directly to jail pays nothing.
- Doubles earn another roll after the landing is resolved. A third consecutive
  doubles sends the player to jail immediately without moving the rolled total.
- Free Parking and Just Visiting have no financial effects.

### Property and rent

- A vacant deed may be bought at printed price. Declining triggers an auction,
  including the decliner. If everyone withdraws, the deed stays with the bank.
- Mortgaged deeds charge no rent. Other unmortgaged properties can still collect
  rent if another deed in the same set is mortgaged.
- A complete colour set doubles the bare-site rent; it does not double building
  rents. Each street has its own six-value rent table, not a generated formula.
- Station rent is £25/£50/£100/£200 for ownership of 1/2/3/4 stations, including
  mortgaged holdings when counting ownership. Landing on a mortgaged site is free.
- Utilities charge four times dice with one owned, ten times with both owned.
  A special utility card rolls fresh dice and charges ten times that total.
- A nearest-station card charges twice the station's normal rent if owned by
  another player; an unowned station is offered for purchase as usual.

### Buildings and mortgages

- Own every street in a colour set, with no mortgages anywhere in it, to build.
- Build evenly: raise a lowest-developed street one step at a time. Sell evenly:
  lower a highest-developed street. A hotel follows four houses and costs one
  further printed building price; its four houses return to the bank.
- There are 32 physical houses and 12 hotels. A hotel is represented by level 5,
  not five physical house tokens. Selling a hotel to four houses requires four
  bank houses; otherwise sell the whole group's buildings back at half cost.
- Buildings sell back at half purchase price. Mortgaging requires all buildings
  in the entire colour group to have been sold first.
- A mortgage pays half the deed price. Redemption costs principal plus 10%,
  rounded up to whole pounds (Park Lane: £175 + £18 = £193).
- Management can be opened for other surviving seats between turns. The active
  decision-maker must finish that window before turn play resumes.

### Jail

Jail does not stop rent collection, trading, building or mortgaging.

- Before attempting a roll, pay £50 or use a held jail-free card, then roll a
  normal turn. The card goes to the bottom of its original deck.
- Alternatively try doubles. Doubles release and move the rolled total, but do
  **not** grant an extra roll. First and second failures leave the player jailed.
- On the third failure, pay £50, then use the dice just rolled. Debt resolution
  can interrupt this fine; it must not lose or reroll those dice.

### Cards, debt, bankruptcy and trades

- Decks are shuffled initially, drawn from the front and replaced underneath.
  A held jail-free card stays out until used, traded or returned by bankruptcy.
- Movement cards resolve the destination normally, including chained draws
  (Chance back-three from 36 lands on Community Chest 33).
- Repair bills count actual houses and hotels, not hotel-as-five-house rent
  levels. Chance charges £25/house and £100/hotel; Chest £40/house and £115/hotel.
- Paying/collecting from every other player queues separate obligations. A
  player unable to pay pauses for liquidation with the correct creditor.
- A player may raise cash through legal sales, mortgages or agreed trades.
  Settling the debt resumes unfinished effects. Bank loans other than mortgages,
  player loans and promises of future payments are not offered.
- Bankruptcy to another player sells buildings back first, transfers remaining
  cash, deeds and jail-free cards, then asks the creditor to keep or redeem each
  inherited mortgage. Bankruptcy to the bank returns held cards and auctions
  cleared, undeveloped deeds individually. One survivor wins after pending
  obligations and bank auctions are resolved.
- Trades require recipient consent. Cash, eligible undeveloped deeds and held
  jail-free cards can be exchanged. Ownership and money are checked atomically;
  an invalid proposal cannot partly mutate the game.

## Explicit remaining differences / limits

These are important: the program is **not yet an exact implementation of every
classic rule**, despite broad rule coverage.

1. **Contested building shortages:** legal construction is first-come within
   explicit management windows. The classic bank auction of the remaining
   houses/hotels when several players want them is not implemented. Property
   auctions are implemented; building auctions are a separate missing mechanism.
2. **Trading mortgaged deeds:** initial 10% interest is paid immediately by each
   recipient. The editor requires enough cash after the exchange to pay it.
   Mortgage redemption is then a separate management action, which charges its
   own 10%. There is not yet a “redeem at transfer instead of keeping the loan”
   choice for negotiated trades. Bankruptcy inheritance **does** offer that
   choice. Do not use a negotiated mortgage transfer to reproduce an immediate
   redemption transaction exactly.
3. **Auction interaction:** a rising auction provides £1/£10/£50/£100 increases
   or an all-cash bid. It does not accept an arbitrary typed opening bid or
   raise mortgages during an auction. Passing withdraws permanently rather than
   acting as a timed “not yet” signal.
4. **Table etiquette:** rent is collected automatically; there is no option to
   forget to claim it before the next player rolls. Other players' management
   windows are opened explicitly rather than interrupting any animation.
5. **Hotel shortage liquidation:** the whole colour group's buildings are sold
   as one action when bank houses are insufficient to break down a hotel. More
   elaborate negotiated orders of partial group liquidation are not modelled.
6. No saving, network play, chat, custom names, sound or undo. Computer players
   use a simple heuristic and are not expert opponents. These are interface or
   strategy limitations rather than changes to rent and movement calculations.

The test suite verifies implemented behaviour, including regression cases and
complete bot games; it cannot honestly prove the stronger claim “original rules
perfectly.” Keep this boundary visible when extending or publishing the project.
