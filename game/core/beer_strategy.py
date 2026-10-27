"""Deterministic, board-only tavern beer buying policy.

New scaled-damage games: all three AI difficulties weigh the *marginal*
damage caused by adding three turns, normal defensive absorption, deaths,
monetary cost and auction reserve. Read only visible board/hero/coin data.
Historical fixed-one-damage matches keep the v0.9.96 buying behavior.
No RNG, game mutation, hidden hand/deck, or speculative Match commands.
"""


def _estimated_three_turn_loss(game,owner):
    """Original 0.9.96 approximation, retained for historical AI behavior."""
    total=0.0
    for uid in game.players[owner].board[:5]:
        unit=game.units[uid]
        definition=game.cards[uid].definition
        exposure=max(0,3-int(bool(unit.shield))-max(0,unit.armor))
        injury=min(max(0,unit.hp),exposure)
        if injury==0:
            continue
        total+=injury*(0.8+min(15,unit.atk)*0.25)
        if injury>=unit.hp:
            value=7.0+min(15,unit.atk)*0.8
            if definition.id in ('A002','S34','S35','S105'):
                value+=9.0
            if definition.faction=='Potwory' or definition.id in ('A001','A003'):
                value-=6.0
            total+=value
    return total


def _projected_board_loss(game,owner,turns):
    """Approximate one board's current units' exposure to queued brawl ticks.

    Predict only the CURRENT visible units, not undisclosed future plays.
    Normal defense rules: one shield consumes one entire tick; armor is a
    consumable pool of points; health caps at zero. Other interactions,
    regenerations and death-wave choices are intentionally not simulated.
    """
    if turns<=0:
        return 0.0
    scaled=bool(getattr(game,'tavern_scaled_damage_enabled',False))
    damage_steps=(range(turns,0,-1) if scaled else (1 for _ in range(turns)))
    damage_steps=tuple(damage_steps)
    total=0.0
    for uid in game.players[owner].board[:5]:
        if uid not in game.units:
            continue
        unit=game.units[uid]
        hp=max(0,unit.hp)
        if hp==0:
            continue
        start_hp=hp
        armor=max(0,unit.armor)
        shield=bool(unit.shield)
        for base_hit in damage_steps:
            hit=(max(base_hit,(max(0,unit.max_hp)+9)//10)
                 if getattr(game,'tavern_min_hp_damage_enabled',False)
                 else base_hit)
            if shield:
                shield=False
                continue
            absorbed=min(armor,hit)
            armor-=absorbed
            loss=min(hp,hit-absorbed)
            hp-=loss
            if hp<=0:
                break
        injury=start_hp-hp
        if not injury:
            continue
        atk=max(0,min(15,unit.atk))
        total+=injury*(0.8+atk*0.25)
        if hp==0:
            definition=game.cards[uid].definition
            death_value=7.0+atk*0.8
            if definition.id in ('A002','S34','S35','S105'):
                death_value+=9.0
            if definition.faction=='Potwory' or definition.id in ('A001','A003'):
                death_value-=6.0  # possible beneficial death trigger
            total+=max(0.0,death_value)
    return total


def _visible_immediate_hero_lethal(game,player):
    """Avoid buying a mug instead of an immediately legal winning attack."""
    other=1-player
    foe=game.players[other]
    if foe.hero_shield:
        return False
    target=f'hero:{other}'
    from . import auction_abilities
    for uid in game.players[player].board[:5]:
        if uid not in game.units or target not in game.legal_attacks(uid):
            continue
        raw=game.units[uid].atk
        if (game.auction_catalog in ('v4','v22')
                and auction_abilities.boosted_attack(game,uid)):
            raw*=2
        if raw>=foe.hp+foe.hero_armor:
            return True
    return False


def _legacy_should_ai_order_beer(game,player,difficulty):
    """Keep old purchase decisions stable for old fixed-1-DMG matches."""
    if difficulty=='łatwy' or not game.can_order_beer(player):
        return False
    if game.beer_turns_remaining>1 or not game.players[1-player].board:
        return False
    own=game.players[player]
    cost=game.beer_price(player)
    future_auction=(game.auctions_enabled and len(game.auction_bag)>=3)
    reserve=(min(6,own.coins//4) if future_auction else 0)
    if own.coins-cost<reserve:
        return False
    return (_estimated_three_turn_loss(game,1-player)
            -_estimated_three_turn_loss(game,player)
            >=(10.0 if difficulty=='trudny' else 14.0))


def should_ai_order_beer(game,player,difficulty):
    """Choose one advantageous mug when brawl is absent/nearly expired.

    All three AI levels use the SAME public-board risk model in newly scaled
    matches. Easy needs a clear advantage, normal a good one, hard a narrower
    advantage. Nobody buys when it would sacrifice an immediate hero finish.
    The two-plus-turn anti-stacking gate prevents repeated purchases in one
    AI action loop and avoid needless ruinous 6/9-DMG self-destruct chains.
    """
    if not getattr(game,'tavern_scaled_damage_enabled',False):
        return _legacy_should_ai_order_beer(game,player,difficulty)
    if difficulty not in ('łatwy','normalny','trudny'):
        return False
    if not game.can_order_beer(player):
        return False
    if game.beer_turns_remaining>1:
        return False
    if not game.players[1-player].board:
        return False
    own=game.players[player]
    cost=game.beer_price(player)
    future_auction=(game.auctions_enabled and len(game.auction_bag)>=3)
    reserve=(min(6,own.coins//4) if future_auction else 0)
    if own.coins-cost<reserve:
        return False
    if _visible_immediate_hero_lethal(game,player):
        return False
    current=game.beer_turns_remaining
    new=current+3
    enemy_gain=(_projected_board_loss(game,1-player,new)
                -_projected_board_loss(game,1-player,current))
    own_loss=(_projected_board_loss(game,player,new)
              -_projected_board_loss(game,player,current))
    # Damage-value-to-coin conversion: conservative levels require visibly
    # better trades. A single weak 1-HP unit is rarely worth spending 10-30 M.
    hurdle={'łatwy':8.0,'normalny':6.0,'trudny':4.0}[difficulty]
    coin_rate={'łatwy':0.45,'normalny':0.35,'trudny':0.25}[difficulty]
    return enemy_gain-own_loss>=hurdle+coin_rate*cost
