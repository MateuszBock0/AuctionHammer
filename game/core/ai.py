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
        # New games with approved v24 buff patch; old saves retain the
        # exact historical ability valuation.
        if (getattr(game,'balance_patch_v24',False)
                and game.auction_catalog=='v22'):
            if offer.archetype=='A014' and tier>=1:
                ability+=(3.5 if tier==1 else
                          min(5,len(own.board)+1)*3.2)
            elif offer.archetype=='A002':
                ability+=(2.0,4.0,6.5)[tier]
            elif offer.archetype=='A003' and not own.grave:
                if len(own.board)<5:
                    ability+=(4.5,5.5,7.0)[tier]
            elif offer.archetype in ('A004','A016') and len(own.board)>=4:
                ability+=(2.0,4.0,7.0)[tier]
            elif offer.archetype=='A009':
                ability+=min(7,len(own.hand))*(tier+1)*.8
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
            # 0.9.97: the normal AI competes for first pick even when two
            # cards have similar value. Still protects a future-auction reserve.
            value=2.6*own_gain+.85*opponent_denial
            baseline=3+min(6,state.number)
            reserve=2 if future_auctions and coins>=9 else 0
            return max(0,min(coins-reserve,max(baseline,int(value+2.5))))

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

    def hard_combo_finish(self,game):
        """Cheap, read-only bounded finish check; overridable for A/B tests."""
        if self.difficulty!='trudny' or game.phase!='turn':
            return None
        from .hard_tactics import forced_hero_finish
        return forced_hero_finish(game,self.player)

    def hard_attack_choice(self,game):
        """Use a bounded 3-step micro-plan, otherwise original 0.9.93 AI.

        Fast constant-work path: at most five ready sources, five targets,
        beam width five, three plies; never mutates the live Match.
        """
        if self.difficulty!='trudny' or game.phase!='turn':
            return None
        from .hard_tactics import shield_break_setup
        win=self.hard_combo_finish(game)
        if win is not None:
            return win
        # Keep the established 0.9.93 general-purpose valuation. The new
        # setup is used only if there is no immediate valuable takedown or
        # an already-unblocked lethal hero action.
        baseline=self._hard_attack_choice_093(game)
        if baseline is not None:
            uid,target=baseline
            if target.startswith('hero:'):
                foe=game.players[1-self.player]
                attacker=game.units[uid]
                if not foe.hero_shield and attacker.atk>=foe.hp+foe.hero_armor:
                    return baseline
            elif target in game.units:
                unit=game.units[target]
                if not unit.shield:
                    return baseline
        return shield_break_setup(game,self.player) or baseline

    def _hard_attack_choice_093(self,game):
        """Pick an attack across ALL ready allies using public board state.

        No speculative Match commands, RNG, hidden hands or search on live
        state. Shield/armor and General's actual double-hit bonus are taken
        from resolved units. Multi-hit lethal is prioritized across allies.
        Returns (source, target) or None if every attack is a bad trade.
        """
        if self.difficulty!='trudny' or game.phase!='turn':
            return None
        from . import auction_abilities
        own=game.players[self.player]
        foe=game.players[1-self.player]
        options=[]
        face=[]
        for uid in own.board:
            if uid not in game.units:
                continue
            attacker=game.units[uid]
            targets=game.legal_attacks(uid)
            if not targets:
                continue
            raw=attacker.atk*(2 if game.auction_catalog in ('v4','v22')
                                  and auction_abilities.boosted_attack(game,uid) else 1)
            for target_id in targets:
                if target_id==f'hero:{1-self.player}':
                    damage=(0 if foe.hero_shield else
                            max(0,raw-foe.hero_armor))
                    face.append((uid,target_id,raw,damage))
                    continue
                defender=game.units[target_id]
                defender_raw=defender.atk*(2 if game.auction_catalog in ('v4','v22')
                        and auction_abilities.boosted_attack(game,target_id) else 1)
                harm=(0 if defender.shield else max(0,raw-defender.armor))
                retaliation=(0 if attacker.shield else max(0,defender_raw-attacker.armor))
                kill=harm>=defender.hp
                lost=retaliation>=attacker.hp
                definition=game.cards[target_id].definition
                own_def=game.cards[uid].definition
                enemy_aura=definition.id in ('A002','S34','S35','S105')
                ally_aura=own_def.id in ('A002','S34','S35','S105')
                # Killing a death-trigger creature can be costly; don't
                # overvalue the removal without seeing its ability choices.
                death_risk=(7.0 if kill and definition.faction=='Potwory'
                            else 6.0 if kill and definition.id in ('A001','A003')
                            else 0.0)
                if definition.id=='S103':
                    # S103 damages the attacker BEFORE normal combat.
                    retaliation+=2+defender.ability_level
                    lost=retaliation>=attacker.hp
                enemy_threat=(defender.atk*.65+defender.hp*.12
                              + (8.0 if enemy_aura else 0.0))
                attacker_value=(attacker.atk*.65+attacker.hp*.15
                                + (10.0 if ally_aura else 0.0))
                score=(harm*.53+ (15+enemy_threat if kill else 0.0)
                       + (5 if harm and not lost else 0.0)
                       - (attacker_value*.77+6 if lost else retaliation*.49)
                       - death_risk)
                if defender.shield:
                    score-=2.2  # a shield-clearing attack isn't a kill
                # Only compare legal actions; earliest source breaks ties.
                options.append((score,uid,target_id))
        if face:
            # The hero can be finished with multiple ready attacks. With a
            # shield, sacrifice the smallest hit first to absorb it, then
            # measure remaining real damage vs public armor and HP.
            raw_hits=sorted(x[2] for x in face)
            remaining=raw_hits[1:] if foe.hero_shield else raw_hits
            potential=max(0,sum(remaining)-foe.hero_armor)
            if potential>=foe.hp and foe.hp>0:
                if foe.hero_shield:
                    sacrificial=min(face,key=lambda v:(v[2],own.board.index(v[0])))
                    return sacrificial[0],sacrificial[1]
                # Lowest adequate hit first: preserve stronger moves if the
                # hero survives from a scripted rescue.
                viable=sorted(face,key=lambda v:(v[2],own.board.index(v[0])))
                hit=next((x for x in viable if x[3]>=foe.hp),viable[0])
                return hit[0],hit[1]
            for uid,target_id,raw,damage in face:
                unit=game.units[uid]
                # Hero hits do not provoke a standard counterattack.
                value=(damage*.9 + (5 if not foe.board else 2.5)
                       + (8 if foe.hp<=35 else 0)
                       + (2 if unit.hp<=3 else 0))
                if foe.hero_shield:
                    value=1.5 - raw*.06
                options.append((value,uid,target_id))
        if not options:
            return None
        # Stable board order: no RNG use and no dependence on dictionary hash.
        score,uid,tgt=max(options,key=lambda x:(x[0],-own.board.index(x[1])))
        return (uid,tgt) if score>=0 else None

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
        # Paid tavern brawl is optional for HARD only in this first pass.
        # Easy and normal preserve their proven historical decision policies.
        # A visible finishing attack always outranks wasting coins.
        if getattr(game,'tavern_beer_enabled',False) and self.difficulty=='trudny':
            from .beer_strategy import should_ai_order_beer
            if (self.hard_combo_finish(game) is None
                    and should_ai_order_beer(game,self.player,self.difficulty)):
                game.order_beer(self.player)
                return  # Exactly one recorded action, just like other AI steps.
        # A guaranteed lethal sequence outranks playing another card;
        # this also avoids accidentally triggering a rescue/death effect
        # before landing the decisive attack.
        if self.difficulty=='trudny':
            # A bounded plan can set up a genuine 2–3 hit finish
            # (e.g. use a weak hit to remove hero shield first).
            combo=self.hard_combo_finish(game)
            if combo is not None:
                game.attack(*combo)
                return
            plan=self.hard_attack_choice(game)
            if plan is not None and plan[1]==f'hero:{1-self.player}':
                enemy=game.players[1-self.player]
                current=game.units[plan[0]]
                raw=current.atk
                from . import auction_abilities
                if game.auction_catalog in ('v4','v22') and auction_abilities.boosted_attack(game,plan[0]):
                    raw*=2
                if (raw>=enemy.hp+enemy.hero_armor and not enemy.hero_shield):
                    game.attack(*plan)
                    return
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
        # Expert considers *every* source/target pair before choosing.
        # Normal and easy retain their previously tested behavior.
        if self.difficulty=='trudny':
            plan=self.hard_attack_choice(game)
            if plan is not None:
                game.attack(*plan)
            else:
                game.end_turn()
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
            else:
                tgt=max(targets,key=target_score)
            game.attack(uid,tgt)
            return
        game.end_turn()
