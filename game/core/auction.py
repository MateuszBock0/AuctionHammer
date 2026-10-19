"""Full auction offers for catalog v3, retaining the existing bid protocol.

Three DISTINCT archetypes per auction. Rarity is rolled independently;
all cards are acquired with ATK + MAX HP = completed round + 8.
"""
from __future__ import annotations
from dataclasses import dataclass,field,asdict
from .models import Card,CardDefinition,IllegalMove
from .auction_catalog import CATALOG,RARITIES,TRIGGER,stats,stats_v4,stats_v22,v4_variant,live_variant,catalog_for,rarity_from_roll,evolve

PLACEHOLDER_HP=(3,6,12)  # only for compatibility with old saved games
RARITY=RARITIES

@dataclass(frozen=True)
class AuctionOffer:
    uid: str
    hp: int
    atk: int
    rarity: str
    level: int
    archetype: str = ""   # empty for 0.9.19 archived placeholder

@dataclass
class AuctionState:
    number: int
    completed_round: int
    offers: list[AuctionOffer]
    free_first: int
    turn: int
    phase: str="bidding"
    current_bid: int=0
    highest_bidder: int | None=None
    passes: int=0
    winner: int | None=None
    price: int=0
    pick_order: list[int]=field(default_factory=list)
    picks: dict[int,str]=field(default_factory=dict)
    bid_bonus: list[int]=field(default_factory=lambda:[0,0])
    highest_effective: int=0
    guarantees: list[bool]=field(default_factory=lambda:[False,False])


def begin(game):
    assert game.auctions_enabled and game.auction is None
    if game.auction_catalog in ('v4','v22') and len(game.auction_bag)<3:
        # The canonical auction requires three distinct offers. Any remaining
        # one or two archetypes stay in their dedicated bag, never the basic deck.
        game._log('Aukcje: w woreczku są mniej niż trzy dostępne archetypy.')
        return None
    number=len(game.auction_history)+1
    completed=game.round-1
    offers=[]
    if getattr(game,"auction_catalog","v3")=="placeholders":
        # Savegame compatibility: matches started on 0.9.19 retain its
        # original three test defenders for all subsequent auctions.
        for hp in PLACEHOLDER_HP:
            roll=game.rng.random()
            game.rng_draw_index+=1
            rarity=rarity_from_roll(roll)
            offers.append(AuctionOffer(f"AUC{number:03d}H{hp:02d}",hp,3,
                                       rarity,number,""))
    else:
        supply=(game.auction_bag if game.auction_catalog in ('v4','v22') else list(CATALOG))
        archetypes=game.rng.sample(supply,3)
        if game.auction_catalog in ('v4','v22'):
            for aid in archetypes:game.auction_bag.remove(aid)
        for aid in archetypes:
            roll=game.rng.random()
            game.rng_draw_index+=1
            rarity=rarity_from_roll(roll)
            atk,hp=(stats_v22(aid,completed) if game.auction_catalog=='v22'
                    else stats_v4(aid,completed) if game.auction_catalog=='v4'
                    else stats(aid,completed))
            offers.append(AuctionOffer(f"AUC{number:03d}{aid}",hp,atk,rarity,
                                       number,aid))
    free_first=game.first if number%2 else 1-game.first
    game.auction=AuctionState(number,completed,offers,free_first,game.first)
    game.phase='auction'
    if game.auction_catalog=='v22':
        vouchers=game.auction_vouchers
        game.auction.bid_bonus=[sum(int(x.get('bonus',0)) for x in v) for v in vouchers]
        game.auction.guarantees=[any(x.get('guaranteed') for x in v) for v in vouchers]
        game.auction_vouchers=[[],[]]   # Each coupon consumed exactly once.
        if sum(game.auction.guarantees)==2:
            game._log('Dwie gwarancje Licytatora znoszą się: normalna licytacja.')
        elif sum(game.auction.guarantees)==1:
            winner=game.auction.guarantees.index(True)
            game.auction.winner=winner
            game.auction.phase='picking'
            game.auction.pick_order=[winner,1-winner]
            game.auction.turn=winner
            game.auction.price=0
            game._log(f'Licytator: {game.players[winner].name} wygrywa '
                      'automatycznie i wybiera jako pierwszy, za 0 monet.')
    catalogue=catalog_for(game.auction_catalog)
    game._log('AUKCJA '+str(number)+': '+', '.join(
        f'{catalogue[o.archetype].name if o.archetype else "Strażnik"} '
        f'{o.atk}/{o.hp} ({o.rarity})' for o in offers))
    return game.auction


def _check_actor(game,player,stage):
    state=game.auction
    if (not game.auctions_enabled or game.phase!='auction' or state is None
        or state.phase!=stage or player!=state.turn or player not in (0,1)):
        raise IllegalMove('Nie Twoja kolej lub nieodpowiednia faza aukcji')
    return state


def bid(game,player,amount):
    state=_check_actor(game,player,'bidding')
    if isinstance(amount,bool) or not isinstance(amount,int):
        raise IllegalMove('Oferta musi być liczbą całkowitą')
    minimum=(max(1,state.highest_effective+1-state.bid_bonus[player])
             if game.auction_catalog=='v22' else max(1,state.current_bid+1))
    if amount<minimum:
        raise IllegalMove('Skuteczna oferta musi przebić poprzednią o 1 monetę')
    if amount>game.players[player].coins:
        raise IllegalMove('Za mało monet')
    state.current_bid=amount;state.highest_bidder=player;state.turn=1-player
    state.highest_effective=(amount+state.bid_bonus[player]
                             if game.auction_catalog=='v22' else amount)
    state.passes=0
    if game.auction_catalog=='v22':
        game._log(f'Aukcja {state.number}: {game.players[player].name} '
                  f'licytuje {amount}, bonus +{state.bid_bonus[player]}, '
                  f'skuteczna oferta {state.highest_effective}.')
    else:
        game._log(f'Aukcja {state.number}: {game.players[player].name} licytuje {amount} monet.')


def _close_bidding(game,state):
    state.winner=(state.highest_bidder if state.highest_bidder is not None
                  else state.free_first)
    if state.highest_bidder is not None:
        state.price=state.current_bid
        game.players[state.winner].coins-=state.price
        game._log(f'Aukcja {state.number}: {game.players[state.winner].name} '
                  f'płaci {state.price} monet.')
    else:
        game._log(f'Aukcja {state.number}: bez ofert. Pierwszy wybiera '
                  f'{game.players[state.winner].name}.')
    state.phase='picking'
    state.pick_order=[state.winner,1-state.winner]
    state.turn=state.winner


def pass_bid(game,player):
    state=_check_actor(game,player,'bidding')
    game._log(f'Aukcja {state.number}: {game.players[player].name} pasuje.')
    if state.highest_bidder is not None:
        _close_bidding(game,state)
    else:
        state.passes+=1
        if state.passes>=2:_close_bidding(game,state)
        else:state.turn=1-player


def pick(game,player,uid):
    state=_check_actor(game,player,'picking')
    offered={o.uid:o for o in state.offers}
    if uid not in offered or uid in state.picks.values():
        raise IllegalMove('Nieprawidłowa lub już wybrana karta aukcyjna')
    offer=offered[uid]
    archetype=catalog_for(game.auction_catalog).get(offer.archetype)
    if archetype:
        name=archetype.name
        trigger=TRIGGER[archetype.trigger]
        family=archetype.family
        if game.auction_catalog in ('v4','v22'):
            text=live_variant(game.auction_catalog,offer.archetype,offer.rarity)
        else:
            text="NIEAKTYWNA (planowana): "+archetype.abilities[RARITIES.index(offer.rarity)]
        definition_id=archetype.id
    else:
        name=f'Strażnik aukcji {offer.hp} PŻ'
        trigger='Pasywna'
        family='Prowokacja'
        text='Prowokacja i jedna Tarcza na wejściu.'
        definition_id=uid
    definition=CardDefinition(
        id=definition_id,name=name,faction='Ludzie',
        family=family,trigger=trigger,atk=offer.atk,hp=offer.hp,
        effect=text,scaling=f'POZIOM {offer.level} · {offer.rarity.upper()} · NIE SKALUJE SIĘ',
        growth_atk=0,growth_hp=0)
    card=Card(uid,definition,owner=player,zone='hand')
    game.cards[uid]=card
    game.defs[uid]=definition
    metadata={
        'number':state.number,'level':offer.level,
        'rarity':offer.rarity,'initial_rarity':offer.rarity,
        'atk':offer.atk,'hp':offer.hp,
        'archetype':offer.archetype,'purchase_round':state.completed_round,
        'last_evolve_round':state.completed_round,
        'ability_implemented':not bool(offer.archetype) or game.auction_catalog in ('v4','v22')}
    if not archetype:metadata['abilities']=('Prowokacja','Tarcza')
    game.auction_awards[uid]=metadata
    game.players[player].hand.append(uid)
    state.picks[player]=uid
    game._log(f'Aukcja {state.number}: {game.players[player].name} wybiera '
              f'{name} ({offer.rarity}, poziom {offer.level}).')
    if len(state.picks)<2:
        state.turn=state.pick_order[1]
        return
    unchosen=[o.uid for o in state.offers if o.uid not in state.picks.values()]
    if game.auction_catalog in ('v4','v22'):
        # Keep unbought archetypes exclusively in the auction supply, not the
        # 70-card bank. A future offer rerolls rarity and R-based stats, per v4.
        for offer in state.offers:
            if offer.uid in unchosen:
                assert offer.archetype not in game.auction_bag
                game.auction_bag.append(offer.archetype)
        # Historical offer IDs are not instantiated as cards; this list is
        # the audit trail, NOT a pile of permanently lost archetypes.
        game.auction_discarded.extend(unchosen)
        game._log(f'Aukcja {state.number}: niewykupiony archetyp '
                  f'{catalog_for(game.auction_catalog)[offered[unchosen[0]].archetype].name} wraca '
                  'WYŁĄCZNIE do woreczka aukcyjnego na przyszłe aukcje.')
    else:
        game._log(f'Aukcja {state.number}: niewybrany archetyp {unchosen[0]} wraca do puli.')
    game.auction_history.append({
        'number':state.number,'completed_round':state.completed_round,
        'offers':[asdict(o) for o in state.offers],
        'winner':state.winner,'price':state.price,
        'picks':dict(state.picks),'unpicked':unchosen[0]
    })
    game.auction=None
    game.phase='turn'
    game._drain()


def advance_rarity(game,completed_round):
    """Evolve owned cards after each third complete round since acquisition.

    No scaling of ATK/HP. Identity/rarity are attached to the physical card;
    evolution while in hand, on board or in graveyard is intentional.
    """
    for uid,meta in sorted(game.auction_awards.items()):
        archetype=meta.get('archetype')
        if not archetype or archetype not in catalog_for(game.auction_catalog) or uid not in game.cards or meta.get('ephemeral'):
            continue
        purchased=meta['purchase_round']
        if completed_round<=purchased or (completed_round-purchased)%3:
            continue
        if meta.get('last_evolve_round',purchased)>=completed_round:
            continue
        old=meta['rarity']
        new=evolve(old)
        meta['last_evolve_round']=completed_round
        if old==new:continue
        meta['rarity']=new
        card=game.cards[uid]
        old_def=card.definition
        from dataclasses import replace
        card.definition=replace(old_def,
                                effect=(live_variant(game.auction_catalog,archetype,new) if game.auction_catalog in ('v4','v22')
                                        else "NIEAKTYWNA (planowana): "+
                                        catalog_for(game.auction_catalog)[archetype].abilities[RARITIES.index(new)]),
                                scaling=f'POZIOM {meta["level"]} · {new.upper()} · NIE SKALUJE SIĘ')
        game.defs[uid]=card.definition
        game._log(f'{card.definition.name} ewoluuje: {old} → {new}.')
        if (game.auction_catalog in ('v4','v22') and archetype=='A002'
                and uid in game.units and new=='rzadka' and
                not game._disabled(game.units[uid])):
            game._queue(uid,'auction_evolve')
    # v4 effects are implemented by auction_abilities; legacy v3 stays inert.
