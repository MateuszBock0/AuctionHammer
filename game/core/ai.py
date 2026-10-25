"""AI dla offline MVP: deterministyczne decyzje i ocena bieżącego stanu.
Nie modyfikuje stanu poza publicznymi komendami Match.
"""
from __future__ import annotations
from .models import IllegalMove

class ComputerOpponent:
    def __init__(self,player=1,difficulty='normalny'):
        self.player=player
        self.difficulty=difficulty

    def auction_offer_value(self,game,offer):
        """Deterministic evaluation of v22 ATK, durability and abilities.

        All input is visible on the table; no hidden hand or deck peek.
        """
        tier={'podstawowa':0,'rzadka':1,'legendarna':2}[offer.rarity]
        value=1.35*offer.atk + .48*offer.hp + (0,2.5,5.5)[tier]
        ability={
            'A001':4.0,'A002':3.0,'A003':2.7,'A004':3.5,
            'A005':1.5,'A006':4.0,'A007':4.5,'A008':4.0,
            'A009':2.2,'A010':5.0,'A011':7.5,'A012':5.5,
            'A013':4.5,'A014':3.0,'A015':4.8,'A016':4.5,
            'A018':2.5,
        }.get(offer.archetype,0.0)
        foe=game.players[1-self.player]
        own=game.players[self.player]
        if offer.archetype=='A011':
            ability+=min(3,len(foe.board))*1.2
        elif offer.archetype in ('A006','A008','A013'):
            ability+=min(2,len(foe.board))*1.0
        elif offer.archetype=='A003':
            ability+=min(3,len(own.grave))*.7
        elif offer.archetype in ('A004','A010'):
            ability+=min(3,len(own.board))*.5
        elif offer.archetype=='A007':
            ability+=max(0,100-own.hp)/25
        elif offer.archetype=='A012':
            ability+=max(0,foe.hp-own.hp)/15
        elif offer.archetype=='A018' and len(game.auction_bag)<3:
            ability-=6  # no further auction with three distinct offers
        return value+ability*(1+.22*tier)

    def auction_first_pick_advantage(self,game):
        """Calculate first-choice advantage for both sides from public offers.

        Auction winner pays for priority, not for a card: the losing side
        always gets its preferred card from the remaining two, for free.
        Both players value the same publicly visible three offers, but their
        board/graveyard/hero state may change their preferences.
        """
        offers=tuple(game.auction.offers)
        if len(offers)<2:
            return (0.,0.)
        other=ComputerOpponent(1-self.player,'normalny')
        own={o.uid:self.auction_offer_value(game,o) for o in offers}
        foe={o.uid:other.auction_offer_value(game,o) for o in offers}
        # Deterministic tie-breaking based only on the visible offer list.
        first_own=max(offers,key=lambda o:(own[o.uid],-offers.index(o)))
        first_foe=max(offers,key=lambda o:(foe[o.uid],-offers.index(o)))
        own_if_lose=max(own[o.uid] for o in offers if o.uid!=first_foe.uid)
        foe_if_win=max(foe[o.uid] for o in offers if o.uid!=first_own.uid)
        gain=max(0.,own[first_own.uid]-own_if_lose)
        denial=max(0.,foe[first_foe.uid]-foe_if_win)
        return gain,denial

    def auction_bid_ceiling(self,game):
        """Deterministic maximum REAL spend; never uses hidden opponent cards.

        This is recalculated on every legal turn of the current auction, but
        is independent of rivals' bids and uses no RNG. Bonuses only affect
        the legal effective minimum, not the coin budget. The cap applies
        to a player's *actual* bid/price in coins.
        """
        state=game.auction
        coins=max(0,int(game.players[self.player].coins))
        if state is None or coins==0:
            return 0
        if self.difficulty=='łatwy':
            # Strict user-requested cap: <= 50% of current coins, rounded DOWN.
            # A very simple, timid bidder even at later auctions.
            return min(coins//2,2+state.number)
        if game.auction_catalog!='v22':
            # Preserve older v3/v4 bot behavior for archived rule variants.
            return min(coins,2+state.number*2)

        own_gain,opponent_denial=self.auction_first_pick_advantage(game)
        future=tuple(getattr(game,'auction_bag',()) or ())
        future_auctions=len(future)>=3
        if self.difficulty!='trudny':
            # Normal: reasonable first-choice price plus a modest denial
            # factor; retains a tiny reserve for later auctions.
            value=1.75*own_gain+.35*opponent_denial
            reserve=2 if future_auctions and coins>=9 else 0
            return max(0,min(coins-reserve,int(value+.5)))

        # Hard: use opponent's public position AND the identities of the
        # unpurchased, still-eligible catalog archetypes, whose availability
        # is derivable from previous public awards. No future rarity peek.
        powerful={'A002','A006','A011','A012','A013','A015'}
        premium_left=sum(1 for key in future if key in powerful)
        own=game.players[self.player]
        foe=game.players[1-self.player]
        emergency=own.hp<=30 and (foe.board or foe.hp<=35)
        # A thin purse and strong future catalog make coins more valuable.
        risk_multiplier=(1.0
                         +(.22 if coins<10 else .08)
                         +(.16 if future_auctions else 0.)
                         +min(.24,premium_left*.04))
        if emergency:
            risk_multiplier=max(1.,risk_multiplier-.25)
        strategic_value=(2.0*own_gain+1.1*opponent_denial)
        if emergency:
            strategic_value*=1.2
        # Not every coin should be committed while strong archetypes remain.
        reserve=(min(coins//3,2+premium_left) if future_auctions
                 and not emergency else 0)
        return max(0,min(coins-reserve,int(strategic_value/risk_multiplier+.5)))

    def choose(self,game):
        p=game.pending
        if p is None:return
        choices=p.choices
        def score(opt):
            target=opt.target
            if target is None:
                return 4 if opt.mode in ('ally','Wzmocnij') else 3
            if target.startswith('hero:'):
                hero=game.players[int(target.split(':')[1])]
                return 15 if hero.idx==self.player and hero.hp<80 else 5
            if target in game.units:
                u=game.units[target]
                is_enemy=u.owner!=self.player
                if is_enemy:
                    if opt.mode in ('Wzmocnij','Cel sojuszniczy','Wzmocnij siebie'):return -50
                    return 10 + max(0,7-u.hp)+u.atk*.7
                if opt.mode in ('Osłab','Cel wrogi'):return -50
                return 7+(u.atk*.7)+(2 if u.hp<u.max_hp else 0)
            if target in game.cards:return 7 + game.cards[target].attack
            return 0
        if self.difficulty=='łatwy':
            best=0
        else:
            best=max(range(len(choices)),key=lambda i:(score(choices[i]),-i))
        game.choose(best)

    def step(self,game):
        if game.phase=='finished':return
        if game.phase=='auction':
            state=game.auction
            if state is None or state.turn!=self.player:return
            if state.phase=='bidding':
                # Value priority over the FREE second pick, not the card
                # in isolation. Respect actual-spend ceilings at every level.
                ceiling=self.auction_bid_ceiling(game)
                # V22 vouchers modify effective minimum, never money paid.
                minimum=(max(1,state.highest_effective+1-state.bid_bonus[self.player])
                         if game.auction_catalog=='v22' else state.current_bid+1)
                if minimum<=ceiling:
                    game.auction_bid(self.player,minimum)
                else:
                    game.auction_pass(self.player)
            else:
                remaining=[x for x in state.offers if x.uid not in state.picks.values()]
                if game.auction_catalog=='v22' and self.difficulty!='łatwy':
                    best=max(remaining,key=lambda x:(
                        self.auction_offer_value(game,x),x.atk,x.hp,x.uid))
                else:
                    # Legacy v4 and easy AI retain their established heuristics.
                    best=max(remaining,key=lambda x:(
                        x.hp,{'podstawowa':0,'rzadka':1,'legendarna':2}[x.rarity]))
                game.auction_pick(self.player,best.uid)
            return
        if game.phase=='mulligan':
            if (getattr(game,'starting_compensation','')=='choice_2_5_or_coins'
                    and self.player==1-game.first
                    and game.starting_compensation_choice is None):
                # A modest, deterministic policy based exclusively on the
                # AI's own hand; it never peeks at the human player's cards.
                own=game.players[self.player]
                strong=max((game.cards[uid].attack for uid in own.hand),default=0)
                # Base cards top out at 4 ATK: a threshold of 5 meant
                # the AI always picked the guard, never the coins.
                option='coins' if strong>=4 else 'unit_2_5'
                game.choose_starting_compensation(self.player,option)
                return  # Exactly one audited command per AI.step (replay invariant).
            if self.player not in game.mulligan_done:
                game.finish_mulligan(self.player,[])
            return
        if game.pending:
            if game.pending.owner==self.player:self.choose(game)
            return
        if game.active!=self.player or game.phase!='turn':return
        p=game.players[self.player]
        # Prefer a good unit; basic creature scaling is included in attack and hp.
        candidates=[cid for cid in p.hand if game.can_play(self.player,cid)]
        if candidates:
            def unit_score(cid):
                card=game.cards[cid]
                f=card.definition.faction
                if self.difficulty=='łatwy':
                    return -(card.attack*.65+card.max_hp*.34)
                if self.difficulty=='trudny':
                    enemies=game.players[1-self.player].board
                    allies=p.board
                    family=card.definition.family
                    estimate=card.attack*.65+card.max_hp*.34
                    # Deterministyczna ocena z publicznego stanu planszy.
                    if f=='Elfy' and family=='Obrażenia':
                        estimate+=4.5 if enemies else .5
                    elif f=='Elfy' and family=='Leczenie':
                        wounded=any(game.units[a].hp<game.units[a].max_hp for a in allies)
                        estimate+=4.0 if wounded or p.hp<85 else .5
                    elif f=='Ludzie':
                        estimate+=2.5+min(4,len(allies))*.7
                    elif f=='Krasnoludy':
                        estimate+=4.1
                    elif f=='Dzikie bestie':
                        estimate+=1.2
                    elif f=='Potwory':
                        estimate+=2.4 if enemies else .5
                    if len(p.board)==4:
                        estimate+=.7
                    return estimate
                return card.attack*.65+card.max_hp*.34+(2.5 if f in ('Elfy','Ludzie') else 1.0)
            best=max(candidates,key=unit_score)
            game.play(best)
            return
        # Full board: optional replacement of an own unit that has not attacked.
        if not p.played_this_turn and len(p.board)==5 and p.hand:
            eligible=[uid for uid in p.board if game.units[uid].attacks==0]
            if eligible:
                def quality(cid):
                    c=game.cards[cid]
                    if cid in game.units:
                        u=game.units[cid]
                        return u.atk*.65 + (u.hp+u.armor)*.34
                    return c.attack*.65+c.max_hp*.34 + (1.5 if c.definition.faction=='Elfy' else 0)
                worst=min(eligible,key=quality)
                best=max(p.hand,key=quality)
                if quality(best)>quality(worst)+1.75 and game.can_play(self.player,best,worst):
                    game.play(best,worst)
                    return
        # Attack legal opponents: prioritize kills and otherwise enemy hero if favorable.
        for uid in list(p.board):
            targets=game.legal_attacks(uid)
            if not targets:continue
            attacker=game.units[uid]
            def target_score(t):
                if t.startswith('hero:'):
                    return (12 if not game.players[1-self.player].board else 4)+attacker.atk*.2
                defender=game.units[t]
                kill=15 if attacker.atk>=defender.hp+defender.armor and not defender.shield else 0
                survive=5 if attacker.hp>defender.atk else -1
                return kill+survive+defender.atk*.7-defender.armor*.2
            if self.difficulty=='łatwy':
                tgt=targets[0]
            elif self.difficulty=='trudny':
                def expert_score(t):
                    basic=target_score(t)
                    if t.startswith('hero:'):
                        hero=game.players[1-self.player]
                        return (10000 if hero.hp<=attacker.atk else 0) + basic + (11 if hero.hp<35 else 0)
                    target=game.units[t]
                    effective=max(0,attacker.atk-target.armor)
                    kill=(target.hp<=effective and not target.shield)
                    survive=attacker.hp>target.atk
                    return basic+(13 if kill else 0)+(4 if survive else -4)-(3 if target.shield or target.armor else 0)
                tgt=max(targets,key=expert_score)
            else:
                tgt=max(targets,key=target_score)
            game.attack(uid,tgt)
            return
        game.end_turn()
