"""Cheap, public-information decision to buy tavern beer (v0.9.96).

This is NOT a new combat simulator: inspect <=10 on-board units and
their actual shields/armor. Hand, deck and RNG are never read. No changes
to the player's price, engine rules, or signed archive fields.
"""


def _estimated_three_turn_loss(game,owner):
    """Estimated 3-tick exposure; avoid pretending to simulate reactions."""
    total=0.0
    for uid in game.players[owner].board[:5]:
        unit=game.units[uid]
        definition=game.cards[uid].definition
        # Damage is distributed over 3 turn completions: one shield charge
        # absorbs a tick; permanent and temporary armor absorb damage first.
        exposure=max(0,3-int(bool(unit.shield))-max(0,unit.armor))
        injury=min(max(0,unit.hp),exposure)
        if injury==0:
            continue
        total+=injury*(0.8+min(15,unit.atk)*0.25)
        if injury>=unit.hp:
            # Destroying a key support card matters more than chip damage.
            value=7.0+min(15,unit.atk)*0.8
            if definition.id in ('A002','S34','S35','S105'):
                value+=9.0
            if definition.faction=='Potwory' or definition.id in ('A001','A003'):
                value-=6.0  # possible death triggers: don't assume benefits
            total+=value
    return total


def should_ai_order_beer(game,player,difficulty):
    """At most one purchase per near-expired brawl, only when advantageous.

    No additional gameplay price and no hard-coded number-of-orders cap for
    human players. AI voluntarily keeps coins for upcoming auctions.
    """
    if difficulty=='łatwy' or not game.can_order_beer(player):
        return False
    # Avoid paying twice before the previous purchase has nearly expired.
    if game.beer_turns_remaining>1:
        return False
    own=game.players[player]
    enemy=game.players[1-player]
    if not enemy.board:
        return False
    cost=game.beer_price(player)
    future_auction=(game.auctions_enabled and len(game.auction_bag)>=3)
    reserve=(min(6,own.coins//4) if future_auction else 0)
    if own.coins-cost<reserve:
        return False
    # Better enemy exposure is a necessary condition, not just abundant coins.
    own_loss=_estimated_three_turn_loss(game,player)
    enemy_loss=_estimated_three_turn_loss(game,1-player)
    advantage=enemy_loss-own_loss
    return advantage>=(10.0 if difficulty=='trudny' else 14.0)
