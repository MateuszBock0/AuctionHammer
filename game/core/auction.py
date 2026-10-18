"""Auction scaffolding v19: three *temporary* defenders, not the future catalog.

The independent 60/30/10 rarity roll and bidding/pick order follow
Game Master section 12. Placeholder rarity and auction level have no
paid skills, stat multipliers, or other gameplay consequences yet.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from .models import Card, CardDefinition, IllegalMove
from .auction_catalog import CATALOG, BY_ID, stats, tier_text

PLACEHOLDER_HP=(3,6,12)
RARITY=("podstawowa","rzadka","legendarna")


@dataclass(frozen=True)
class AuctionOffer:
    uid: str
    hp: int
    atk: int
    rarity: str
    level: int
    archetype: str = 'PLACEHOLDER'


@dataclass
class AuctionState:
    number: int
    completed_round: int
    offers: list[AuctionOffer]
    free_first: int
    turn: int
    phase: str = "bidding"
    current_bid: int = 0
    highest_bidder: int | None = None
    passes: int = 0
    winner: int | None = None
    price: int = 0
    pick_order: list[int] = field(default_factory=list)
    picks: dict[int,str] = field(default_factory=dict)


def begin(game):
    """Called AFTER round income and fully resolved effects."""
    assert game.auctions_enabled and game.auction is None
    number=len(game.auction_history)+1
    level=number
    offers=[]
    if getattr(game,'auction_catalog_mode','placeholders')=='v3':
        entries=game.rng.sample(CATALOG,3)  # distinct within this auction
        for item in entries:
            roll=game.rng.random()
            game.rng_draw_index+=1
            rarity=RARITY[0 if roll<.60 else 1 if roll<.90 else 2]
            atk,hp=stats(item,game.round-1)
            offers.append(AuctionOffer(f"AUC{number:03d}{item.ident}",hp,atk,
                                       rarity,level,item.ident))
    else:
        for hp in PLACEHOLDER_HP:
            roll=game.rng.random()
            game.rng_draw_index+=1
            rarity=RARITY[0 if roll<.60 else 1 if roll<.90 else 2]
            offers.append(AuctionOffer(f"AUC{number:03d}H{hp:02d}",hp,3,rarity,level))
    free_first=game.first if number%2 else 1-game.first
    game.auction=AuctionState(number,game.round-1,offers,free_first,
                              game.first)
    game.phase="auction"
    game._log(f"AUKCJA {number}: "+', '.join(
        (BY_ID[o.archetype].name if o.archetype!='PLACEHOLDER' else
         f'Strażnik {o.hp} PŻ')+' ('+o.rarity+')' for o in offers)+'.')
    return game.auction


def _check_actor(game,player,stage):
    state=game.auction
    if (not game.auctions_enabled or game.phase!="auction" or state is None
            or state.phase!=stage or player!=state.turn):
        raise IllegalMove("Nie Twoja kolej lub nieodpowiednia faza aukcji")
    if player not in (0,1):
        raise IllegalMove("Nieprawidłowy gracz")
    return state


def bid(game,player,amount):
    state=_check_actor(game,player,"bidding")
    if not isinstance(amount,int) or isinstance(amount,bool):
        raise IllegalMove("Oferta musi być liczbą całkowitą")
    if amount<max(1,state.current_bid+1):
        raise IllegalMove("Podbij licytację o co najmniej 1 monetę")
    if amount>game.players[player].coins:
        raise IllegalMove("Za mało monet")
    state.current_bid=amount
    state.highest_bidder=player
    state.turn=1-player
    state.passes=0
    game._log(f"Aukcja {state.number}: {game.players[player].name} licytuje "
              f"{amount} monet.")


def _close_bidding(game,state):
    state.winner=state.highest_bidder if state.highest_bidder is not None else state.free_first
    if state.highest_bidder is not None:
        state.price=state.current_bid
        game.players[state.winner].coins-=state.price
        game._log(f"Aukcja {state.number}: zwycięzca {game.players[state.winner].name} "
                  f"płaci {state.price} monet.")
    else:
        game._log(f"Aukcja {state.number}: bez ofert; pierwszeństwo bezpłatnego "
                  f"wyboru ma {game.players[state.winner].name}.")
    state.phase="picking"
    state.pick_order=[state.winner,1-state.winner]
    state.turn=state.winner


def pass_bid(game,player):
    state=_check_actor(game,player,"bidding")
    game._log(f"Aukcja {state.number}: {game.players[player].name} pasuje.")
    if state.highest_bidder is not None:
        _close_bidding(game,state)
    else:
        state.passes+=1
        if state.passes>=2:
            _close_bidding(game,state)
        else:
            state.turn=1-player


def pick(game,player,uid):
    state=_check_actor(game,player,"picking")
    offered={o.uid:o for o in state.offers}
    if uid not in offered or uid in state.picks.values():
        raise IllegalMove("Nieprawidłowa lub już wybrana karta aukcyjna")
    offer=offered[uid]
    if offer.archetype!='PLACEHOLDER':
        item=BY_ID[offer.archetype]
        faction={'play':'Elfy','death':'Potwory','end':'Krasnoludy',
                 'passive':'Ludzie'}[item.trigger]
        trigger={'play':'Przy wystawieniu','death':'Przy śmierci',
                 'end':'Na koniec tury','passive':'Pasywna'}[item.trigger]
        family={'A001':'Oczyszczanie','A002':'Podwójny atak',
                'A003':'Regeneracja','A004':'Podwójny atak',
                'A005':'Pancerz','A006':'Ogłuszenie',
                'A007':'Odporność','A008':'Oczyszczanie',
                'A009':'ATK ±','A010':'Regeneracja',
                'A011':'Obrażenia','A012':'Leczenie'}[offer.archetype]
        definition=CardDefinition(offer.uid,item.name,faction,family,trigger,
                                  offer.atk,offer.hp,
                                  tier_text(offer.archetype,offer.rarity),
                                  'Aukcyjna: nie skaluje się na ręce.',
                                  0,0)
    else:
        definition=CardDefinition(
            id=uid,name=f"Strażnik aukcji {offer.hp} PŻ",
            faction="Ludzie",family="Prowokacja",trigger="Pasywna",
            atk=3,hp=offer.hp,
            effect="Prowokacja. Przy wystawieniu zyskuje 1 Tarczę.",
            scaling="Karta aukcyjna: stałe parametry, brak skalowania na ręce.",
            growth_atk=0,growth_hp=0
        )
    card=Card(uid,definition,owner=player,zone="hand")
    game.cards[uid]=card
    game.defs[uid]=definition
    game.auction_awards[uid]={
        "number":state.number,"level":offer.level,
        "rarity":offer.rarity,"atk":offer.atk,"hp":offer.hp,
        "archetype":offer.archetype,
        "completed_round":state.completed_round,
        "abilities":("Prowokacja","Tarcza") if offer.archetype=="PLACEHOLDER"
                    else (offer.archetype,)
    }
    game.players[player].hand.append(uid)
    state.picks[player]=uid
    game._log(f"Aukcja {state.number}: {game.players[player].name} wybiera "
              f"{definition.name} ({offer.rarity}, poziom {offer.level}).")
    if len(state.picks)<2:
        state.turn=state.pick_order[1]
        return
    unchosen=[o.uid for o in state.offers if o.uid not in state.picks.values()]
    game._log(f"Aukcja {state.number}: niewybrana oferta {unchosen[0]} wraca do "
              "puli przyszłych archetypów (placeholder nie jest kopiowany).")
    game.auction_history.append({
        "number":state.number,"completed_round":state.completed_round,
        "offers":[asdict(o) for o in state.offers],
        "winner":state.winner,"price":state.price,
        "picks":dict(state.picks),"unpicked":unchosen[0]
    })
    game.auction=None
    game.phase="turn"
    game._drain()  # resumes the already queued next turn, no skipped draw
