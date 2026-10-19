"""Resolution of the twelve auction archetypes, active v4.

All abilities enter Match's existing public command/trigger/choice pipeline.
Never bypass the game phase, board capacity, death-wave queue or owner checks.
Pending choices are the same dataclasses as the 70 basic cards.
"""
from __future__ import annotations

from dataclasses import replace
from math import ceil
from .models import Card,CardDefinition,Choice,Pending,Unit
from .auction_catalog import CATALOG,RARITIES,catalog_for


def kind(game,uid):
    return game.auction_awards.get(uid,{}).get('archetype','')


def rarity(game,uid):
    data=game.auction_awards.get(uid,{})
    return RARITIES.index(data['rarity']) if data.get('archetype') in catalog_for(game.auction_catalog) else 0


def pick_choices(game,mode,ids,label):
    return [Choice(mode,x,f'{label} — {game.label(x)}') for x in ids]


def foe_has_playable_deck(own,enemy):
    return bool(own.deck or enemy.deck)


def options(game,uid,context,attacked=None):
    aid=kind(game,uid)
    if not aid and uid not in game.auction_death_grants:return []
    own=game.players[game.cards[uid].owner]
    enemy=game.players[1-own.idx]
    myboard=[x for x in own.board if x!=uid]
    opponents=list(enemy.board)
    tier=rarity(game,uid)
    if context=='auction_cart_play':
        if tier==1:
            candidates=list(reversed(own.deck[-3:]))+list(reversed(enemy.deck[-1:]))
        else:
            candidates=list(reversed(own.deck[-3:]))+list(reversed(enemy.deck[-3:]))
        return (pick_choices(game,'cart_play',candidates,'Zagraj z talii')
                if len(own.board)<5 else [])
    if context=='auction_silence_next':
        already=game.auction_pending_targets.get(uid,[])
        return [Choice('stop',None,'Zakończ wyciszanie')]+pick_choices(
            game,'silence', [x for x in opponents if x not in already],'Wycisz')
    if context=='auction_exile_next':
        already=game.auction_pending_targets.get(uid,[])
        return [Choice('stop',None,'Zakończ wygnanie')]+pick_choices(
            game,'exile',[x for x in opponents if x not in already],'Wygnaj')
    if context=='auction_exchange_enemy':
        return pick_choices(game,'exchange_enemy',enemy.hand,'Wymień')
    if context=='auction_discard':
        return pick_choices(game,'discard',enemy.hand,'Odrzuć na cmentarz')
    if context=='auction_return_second':
        already=game.auction_pending_targets.get(uid,[])
        return pick_choices(game,'return_hand',
            [x for x in own.grave if x not in already and x.startswith('S')], 'Na rękę')
    if uid in game.auction_death_grants and aid!='A001' and context=='death':
        return pick_choices(game,'chain_capture',opponents,'Przejmij') if len(own.board)<5 else []
    if aid=='A001' and context=='death':
        result=pick_choices(game,'kill',opponents,'Zabij')
        if tier>=1 and len(own.board)<5:
            result+=pick_choices(game,'capture',opponents,'Przejmij')
            if tier==2:
                result+=pick_choices(game,'capture_chain',opponents,'Przejmij i nadaj łańcuch')
        return result
    if aid=='A002' and (context=='play' or context=='auction_evolve'):
        if tier==1:return pick_choices(game,'general_target',myboard,'Daj dwa ataki i x2 obrażeń')
        return [Choice('auto',None,'Aura')] if tier==0 else []
    if aid=='A003' and context=='death':
        available=[x for x in own.grave if x.startswith('S')]
        result=pick_choices(game,'to_hand',available,'Na rękę')
        if tier>=1:
            result+=pick_choices(game,'revive_one',available,'Wskrześ z 1 PŻ')
        if tier==2:
            result+=pick_choices(game,'revive_pair',available,'Wskrześ + zwróć inną')
        return result
    if aid=='A004' and context=='play':
        if len(own.board)>=5:return []
        ids=myboard + (opponents if tier>=1 else [])
        return pick_choices(game,'copy',[x for x in ids if x in game.units],
                            'Utwórz efemeryczną kopię')
    if aid=='A005' and context=='play':
        return [Choice('auto',None,'Przenieś monety i dodaj nowe')]
    if aid=='A006' and context=='play':
        if tier==2:return [Choice('auto',None,'Wycisz wszystkie jednostki wroga')]
        return pick_choices(game,'silence',opponents,'Wycisz')
    if aid=='A007':return []
    if aid=='A008' and context=='play':
        return pick_choices(game,'mark' if tier==0 else 'exile',opponents,
                            'Naznacz' if tier==0 else 'Wygnaj') or (
                            [Choice('auto',None,'Wygnaj kartę z ręki')]
                            if tier>=1 and enemy.hand else [])
    if aid=='A009' and context=='play':
        if tier==2:return [Choice('swap_all',None,'Wymień obie ręce')]
        return pick_choices(game,'exchange_own',own.hand,'Wymień własną') if enemy.hand else []
    if aid=='A010' and context=='end':
        result=[]
        # v22 Queen summons fixed-strength soldiers; the legacy v4
        # legendary version still needs another unit for copying.
        needs_ally=(game.auction_catalog!='v22' and tier==2)
        if len(own.board)<5 and (not needs_ally or myboard):
            result.append(Choice('summon',None,'Przywołaj jednostki'))
        if not needs_ally or myboard:
            result.append(Choice('grow',None,'Wzmocnij Królową'))
        return result
    if aid=='A011' and context=='death':
        return [Choice('auto',None,'Katastrofa')]
    if aid=='A012' and context=='play':
        if tier==1:
            return [Choice('copy_to_self',None,'Kopiuj PŻ rywala do siebie'),
                    Choice('copy_to_enemy',None,'Kopiuj swoje PŻ do rywala')]
        return [Choice('auto',None,'Manipuluj PŻ bohaterów')]
    if aid=='A013' and context=='play':
        return pick_choices(game,'bastion',opponents,'Przebij MAX PŻ')
    if aid in ('A014','A015'):
        return []
    if aid=='A016' and context=='play':
        if tier<2:
            choices=pick_choices(game,'cart_draw',list(reversed(own.deck[-3:])),
                                 'Dobierz jedną z własnej talii')
            if choices:return choices
            # The rare second effect is independent of the basic draw.
            # Even with no own cards, it may play the opponent's top card.
            if tier==1 and len(own.board)<5 and foe_has_playable_deck(own,enemy):
                return [Choice('auto',None,'Pomiń dobór, zagraj z talii')]
            return []
        return options(game,uid,'auction_cart_play')
    if aid=='A018' and context=='play':
        return [Choice('auto',None,'Nadaj premię na następną aukcję')]
    return []



def _active_passives(game,aid):
    for uid,u in list(game.units.items()):
        if (game.cards[uid].definition.id==aid and
                kind(game,uid)==aid and not game._disabled(u)):
            yield uid,u,rarity(game,uid)


def convert_healing(game,target,target_owner,amount):
    """A014: highest enemy tier wins, not additive; damage uses normal guards."""
    amount=max(0,int(amount))
    tiers=[tier for _uid,u,tier in _active_passives(game,'A014')
           if u.owner!=target_owner]
    if not tiers or amount<=0:return amount
    tier=max(tiers)
    if tier==0:
        game._log(f'Kapłan Odwróconej Łaski: {game.label(target)} '
                  f'nie może odzyskać {amount} PŻ.')
        return 0
    damage=(amount+1)//2 if tier==1 else amount
    heal=amount-damage
    game._log(f'Kapłan Odwróconej Łaski: z leczenia {amount} PŻ '
              f'{damage} zmieniono w obrażenia, pozostaje leczenie {heal} PŻ.')
    game._damage(target,damage,defer_death=game._suspend_hero_thresholds)
    return heal


def global_trigger_block(game,context):
    """A015 rare blocks death for both players; legendary play/death/end."""
    for _uid,_unit,tier in _active_passives(game,'A015'):
        if tier==2 and context in ('play','death','end'):return True
        if tier==1 and context=='death':return True
    return False


def block_trigger(game,uid,context,attacked=None):
    if context not in ('play','death','end'):return False
    if global_trigger_block(game,context):return True
    if context!='play':return False
    source=game.cards[uid].owner
    wardens=[(w,w_owner,t) for w,w_unit,t in _active_passives(game,'A015')
             for w_owner in [w_unit.owner]
             if w_owner!=source and t<2 and w not in game.auction_blocked_play]
    if not wardens:return False
    aid=kind(game,uid)
    if aid in ('A005','A012','A018'):
        aimed=(aid in ('A005','A012'))
    else:
        from .effects import options as basic_options
        choices=(options(game,uid,'play',attacked) if aid else
                 basic_options(game,uid,'play',attacked))
        aimed=any((c.target and
                    (c.target==f'hero:{1-source}' or
                     (c.target in game.units and
                      game.units[c.target].owner!=source)))
                  for c in choices)
        if not aimed:
            words=game.cards[uid].definition.effect.lower()
            aimed=(any(x in words for x in ('wrog','przeciwnik','rywala')) and
                   not any(x in words for x in ('własnego bohatera','własne jednostki')))
    if not aimed:return False
    chosen=min(wardens,key=lambda a:(a[1],game.players[a[1]].board.index(a[0])))[0]
    game.auction_blocked_play.add(chosen)
    game._log(f'Wieszczka {game.label(chosen)}: anulowano pierwszą '
              f'wrogą zdolność przy wystawieniu {game.label(uid)}.')
    return True

def _prepare_pending(game,uid,context,choices,owner=None):
    if choices:
        game.pending=Pending(uid,game.cards[uid].owner if owner is None else owner,
                             context,list(choices))


def _return_to_hand(game,owner,uid):
    p=game.players[owner]
    if uid not in p.grave:return False
    p.grave.remove(uid);p.hand.append(uid)
    game.cards[uid].zone='hand'
    game._log(f'{game.label(uid)} wraca z cmentarza na rękę.')
    return True


def _revive(game,owner,uid,full=False):
    p=game.players[owner]
    if len(p.board)>=5:return _return_to_hand(game,owner,uid)
    if uid not in p.grave:return False
    p.grave.remove(uid)
    card=game.cards[uid]
    card.zone='board'
    unit=Unit(uid,owner,card.attack,card.max_hp,
              card.max_hp if full else 1,card.ability_level,p.turn_count)
    p.board.append(uid);game.units[uid]=unit
    game._log(f'{game.label(uid)} powraca na planszę '
              f'({unit.hp} PŻ; bez Przy wystawieniu).')
    return True


def _capture(game,uid,target,chain=False):
    owner=game.cards[uid].owner
    if target not in game.units or len(game.players[owner].board)>=5:
        return False
    unit=game.units[target]
    old=unit.owner
    if old==owner:return False
    game.players[old].board.remove(target)
    # A captured ally must not continue benefiting from their old general.
    forget_general_links(game,target)
    unit.owner=owner
    unit.played_turn=game.players[owner].turn_count
    unit.attacks=0
    game.players[owner].board.append(target)
    game.cards[target].owner=owner
    if chain:game.auction_death_grants.add(target)
    game._log(f'{game.label(uid)} przejmuje {game.label(target)}.')
    game._update_auras()
    return True


def _kill(game,uid,target):
    if target in game.units:
        u=game.units[target]
        # Kill ignores shields / armor but still uses death waves and rewards.
        game._damage(target,max(1,u.hp),ignore_defense=True)
        game._log(f'{game.label(uid)} zabija {game.label(target)}.')


def _exile(game,uid,target):
    if target in game.units:
        forget_general_links(game,target,include_source=True)
        unit=game.units.pop(target)
        game.players[unit.owner].board.remove(target)
    elif target in game.cards and game.cards[target].zone=='hand':
        owner=game.cards[target].owner
        if target not in game.players[owner].hand:return False
        game.players[owner].hand.remove(target)
    else:return False
    card=game.cards[target]
    card.zone='exiled'
    game.exiled.append(target)
    game._log(f'{game.label(uid)} wygania {game.label(target)} bez zgonu.')
    game._update_auras()
    return True


def _exile_random_hand(game,uid):
    owner=game.cards[uid].owner
    hand=sorted(game.players[1-owner].hand)
    if not hand:return
    target=game.rng.choice(hand)
    game.rng_draw_index+=1
    game._log(f'Losowanie wygnania #{game.rng_draw_index}: {hand} -> {target}.')
    _exile(game,uid,target)


def _swap_hands(game):
    own,enemy=game.players
    own.hand,enemy.hand=enemy.hand,own.hand
    for p in game.players:
        for cid in p.hand:game.cards[cid].owner=p.idx


def _copy(game,uid,target,legendary=False,ephemeral_silent=False):
    owner=game.cards[uid].owner
    p=game.players[owner]
    if target not in game.units or len(p.board)>=5:
        return None
    original=game.units[target]
    original_card=game.cards[target]
    game.serial+=1
    new_uid=f'COPY{game.serial:07d}'
    d=original_card.definition
    card=Card(new_uid,replace(d),owner=owner,zone='board')
    game.cards[new_uid]=card
    game.defs[new_uid]=card.definition
    game.ephemeral_ids.add(new_uid)
    if target in game.auction_awards and kind(game,target):
        game.auction_awards[new_uid]=dict(game.auction_awards[target],ephemeral=True)
    # Preserve wounds in every tier; only legendary retains current bonuses.
    wounds=max(0,original.max_hp-original.hp)
    base_atk=original.atk if legendary else original_card.attack
    base_hp=original.max_hp if legendary else original_card.max_hp
    clone=Unit(new_uid,owner,base_atk,base_hp,max(0,base_hp-wounds),
               original.ability_level,p.turn_count)
    if legendary:
        from copy import deepcopy
        clone.effects=deepcopy([e for e in original.effects if e.kind not in ('atk','max_hp')])
        clone.shield=1
        clone.shield_source=uid
        clone.armor_perm=original.armor_perm
        clone.armor_temp=original.armor_temp
        clone.temporary_armor=deepcopy(original.temporary_armor)
        clone.armor_perm_grants=deepcopy(original.armor_perm_grants)
        clone.aura_hp=0;clone.aura_atk=0
    p.board.append(new_uid);game.units[new_uid]=clone
    game._log(f'{game.label(uid)} tworzy efemeryczną kopię {game.label(target)}.')
    game._update_auras(defer_reactive=True)
    # A004 copies count as extra PLAY with source's on-play triggers; A010
    # produces silent soldiers/copies and never fires an ON_PLAY effect.
    if not ephemeral_silent and d.trigger=='Przy wystawieniu' and kind(game,new_uid)!='A004':
        game._queue(new_uid,'play')
    mark_general_new_ally(game,new_uid)
    return new_uid


def _spawn(game,uid,atk,hp,taunt=False):
    owner=game.cards[uid].owner;p=game.players[owner]
    if len(p.board)>=5:return None
    game.serial+=1
    cid=f'SUM{game.serial:07d}'
    d=CardDefinition(cid,'Żołnierz Królowej','Ludzie',
                     'Prowokacja' if taunt else 'Bez zdolności','Pasywna',
                     atk,hp,'Prowokacja' if taunt else 'Bez zdolności',
                     'Jednostka efemeryczna',0,0)
    game.cards[cid]=Card(cid,d,owner=owner,zone='board')
    game.defs[cid]=d
    unit=Unit(cid,owner,atk,hp,hp,0,p.turn_count)
    game.units[cid]=unit;game.ephemeral_ids.add(cid);p.board.append(cid)
    if taunt:
        game._add_effect(cid,'taunt',source=uid,positive=True)
    game._log(f'{game.label(uid)} przywołuje Żołnierza {atk}/{hp}.')
    mark_general_new_ally(game,cid)
    return cid


def _set_hero_hp(game,owner,value):
    p=game.players[owner]
    old=p.hp;p.hp=min(100,value)
    for threshold in (75,50,25):
        if old>threshold>=p.hp and threshold not in p.thresholds:
            p.thresholds.add(threshold);p.coins+=2
            game._log(f'{p.name}: +2 monety za przekroczenie {threshold} PŻ.')


def _save_hero(game,owner):
    p=game.players[owner]
    if p.hp>0:return False
    guard=next((x for x in p.board if kind(game,x)=='A007'
                and x not in game.auction_rescue_spent
                and x in game.units and not game._disabled(game.units[x])),None)
    if guard is None:return False
    tier=rarity(game,guard)
    game.auction_rescue_spent.add(guard)
    game._remove_unit(guard,death=False) # sacrifice is NOT a kill reward
    p.hp=(1,20,25)[tier]
    game._log(f'{game.label(guard)} poświęca się, ratując bohatera z {p.hp} PŻ.')
    if tier==2:
        for x in list(game.players[1-owner].board):
            if x in game.units:
                game._add_effect(x,'stun',expires=game._expiry(1-owner),
                                 source=guard,positive=False)
    return True


def rescue_heroes(game):
    for owner in (0,1):
        _save_hero(game,owner)


def forget_general_links(game,uid,include_source=False):
    """Buff targets are physical battlefield incarnations, not card UIDs forever."""
    for src,target in list(game.auction_general_targets.items()):
        if target==uid or (include_source and src==uid):
            game.auction_general_targets.pop(src,None)
    for src,recipients in list(game.auction_general_grants.items()):
        recipients.discard(uid)
        if include_source and src==uid:
            game.auction_general_grants.pop(src,None)


def mark_general_new_ally(game,uid):
    """Only units entering after an active legendary general receive its flag."""
    if uid not in game.units:return
    owner=game.units[uid].owner
    for src,leader in list(game.units.items()):
        if (src!=uid and leader.owner==owner and kind(game,src)=='A002'
            and rarity(game,src)==2 and not game._disabled(leader)):
            game.auction_general_grants.setdefault(src,set()).add(uid)


def boosted_attack(game,uid):
    unit=game.units.get(uid)
    if not unit:return False
    for src,target in game.auction_general_targets.items():
        if (target==uid and src in game.units and rarity(game,src)==1
            and game.units[src].owner==unit.owner
            and not game._disabled(game.units[src])):
            return True
    for src,recipients in game.auction_general_grants.items():
        if (uid in recipients and src in game.units and rarity(game,src)==2
            and game.units[src].owner==unit.owner
            and not game._disabled(game.units[src])):
            return True
    return False


def execute(game,uid,context,choice,attacked=None):
    aid=kind(game,uid)
    tier=rarity(game,uid)
    owner=game.cards[uid].owner
    own=game.players[owner]
    foe=game.players[1-owner]
    mode=choice.mode;target=choice.target

    if context=='auction_cart_play':
        if mode=='cart_play' and target in own.deck+foe.deck and len(own.board)<5:
            if target in foe.deck:
                foe.deck.remove(target)
                own.deck.append(target)
                game.cards[target].owner=owner
                game._log('Kartograf przejmuje kartę z talii przeciwnika.')
            game._play_deck_effect(owner,target)
        return
    if context=='auction_silence_next':
        if mode=='silence' and target in game.units:
            game._add_effect(target,'silence',expires=game._expiry(1-owner),
                             source=uid,positive=False)
        game.auction_pending_targets.pop(uid,None)
        return
    if context=='auction_exile_next':
        saved=game.auction_pending_targets.setdefault(uid,[])
        if mode=='exile' and target not in saved:
            _exile(game,uid,target);saved.append(target)
        if mode=='stop' or len(saved)>=3 or not foe.board:
            game.auction_pending_targets.pop(uid,None)
            _exile_random_hand(game,uid)
        else:_prepare_pending(game,uid,'auction_exile_next',options(game,uid,'auction_exile_next'))
        return
    if context=='auction_exchange_enemy':
        mine=game.auction_pending_targets.pop(uid,[])
        if mine and mine[0] in own.hand and target in foe.hand:
            first=mine[0]
            own.hand[own.hand.index(first)]=target
            foe.hand[foe.hand.index(target)]=first
            game.cards[first].owner=1-owner;game.cards[target].owner=owner
            game._log(f'{game.label(uid)} wymienia karty: {first} ⇄ {target}.')
        return
    if context=='auction_discard':
        if target in foe.hand:
            foe.hand.remove(target)
            if game.auction_catalog in ('v4','v22') and target in game.auction_awards:
                # Legendary A009 must never recycle an auction card into a
                # basic graveyard, even after stealing/swapping hands.
                game.auction_used.append(target)
                game.cards[target].zone='auction_used'
                game._log(f'{game.label(uid)}: {game.label(target)} '
                          'trafia do osobnego woreczka zużytych kart aukcyjnych.')
            else:
                foe.grave.append(target)
                game.cards[target].zone='grave'
                game._log(f'{game.label(uid)}: {game.label(target)} trafia na cmentarz.')
        remaining=game.auction_pending_targets.get(uid,[])
        # This is a *count* of up to two discards, not a list of card IDs.
        # Previously comparison with the chosen card never consumed it and
        # could incorrectly discard the whole hand.
        if remaining:remaining.pop(0)
        if remaining and foe.hand:
            _prepare_pending(game,uid,'auction_discard',options(game,uid,'auction_discard'),owner=foe.idx)
        else:game.auction_pending_targets.pop(uid,None)
        return
    if context=='auction_return_second':
        saved=game.auction_pending_targets.pop(uid,[])
        if target!=uid and target not in saved:_return_to_hand(game,owner,target)
        return
    if context=='death' and uid in game.auction_death_grants and aid!='A001':
        if mode=='chain_capture':
            game.auction_wave_ops.append(('capture',uid,target,True))
        return

    if aid=='A001' and context=='death':
        if mode=='kill':
            _kill(game,uid,target)
        elif mode in ('capture','capture_chain'):
            game.auction_wave_ops.append(('capture',uid,target,mode=='capture_chain'))
    elif aid=='A002':
        if mode=='general_target' and target in own.board:
            game.auction_general_targets[uid]=target
            game._log(f'Generał wybiera {game.label(target)} do podwójnych ataków.')
    elif aid=='A003' and context=='death':
        if mode=='to_hand':
            game.auction_wave_ops.append(('to_hand',owner,target,False))
        elif mode=='revive_one':
            game.auction_wave_ops.append(('revive',owner,target,False))
        elif mode=='revive_pair':
            game.auction_wave_ops.append(('revive_pair',uid,owner,target))
    elif aid=='A004' and context=='play':
        _copy(game,uid,target,legendary=tier==2)
    elif aid=='A005' and context=='play':
        money=foe.coins
        stolen=(min(3,money) if tier==0 else
                min(money,max(3,ceil(money/2))) if tier==1 else money)
        foe.coins-=stolen;own.coins+=stolen
        extra=(3,4,5)[tier]
        own.coins+=extra
        game._log(f'{game.label(uid)} kradnie {stolen} i tworzy {extra} monet.')
    elif aid=='A006' and context=='play':
        if tier==2:
            for enemy in list(foe.board):
                if enemy in game.units:
                    game._add_effect(enemy,'silence',expires=game._expiry(1-owner),
                                     source=uid,positive=False)
        elif target in game.units:
            game._add_effect(target,'silence',expires=game._expiry(1-owner),
                             source=uid,positive=False)
            if tier==1:
                rest=[x for x in foe.board if x!=target]
                if rest:
                    game.auction_pending_targets[uid]=[target]
                    _prepare_pending(game,uid,'auction_silence_next',
                                     options(game,uid,'auction_silence_next'))
    elif aid=='A008' and context=='play':
        if tier==0:
            if target in game.units:
                game._add_effect(target,'auction_exile_mark',
                                 expires=game.players[1-owner].turn_count+1,
                                 source=uid,positive=False)
        else:
            if target in game.units:_exile(game,uid,target)
            if tier==1:
                _exile_random_hand(game,uid)
            else:
                game.auction_pending_targets[uid]=[target] if target else []
                rest=[x for x in foe.board if x!=target]
                if rest:
                    _prepare_pending(game,uid,'auction_exile_next',
                                     options(game,uid,'auction_exile_next'))
                else:
                    game.auction_pending_targets.pop(uid,None)
                    _exile_random_hand(game,uid)
    elif aid=='A009' and context=='play':
        if mode=='swap_all':
            _swap_hands(game)
            # Opponent discards up to two from their NEW hand.
            game.auction_pending_targets[uid]=['discard']*min(2,len(foe.hand))
            if foe.hand:
                _prepare_pending(game,uid,'auction_discard',
                                 options(game,uid,'auction_discard'),owner=foe.idx)
        elif mode=='exchange_own' and target in own.hand and foe.hand:
            game.auction_pending_targets[uid]=[target]
            if tier==0:
                pool=sorted(foe.hand)
                selected=game.rng.choice(pool);game.rng_draw_index+=1
                execute(game,uid,'auction_exchange_enemy',Choice('exchange_enemy',selected,'auto'))
            else:
                _prepare_pending(game,uid,'auction_exchange_enemy',
                                 options(game,uid,'auction_exchange_enemy'))
    elif aid=='A010' and context=='end':
        if mode=='summon':
            if tier==0:
                _spawn(game,uid,1,1)
            elif tier==1:
                for _ in range(2):
                    _spawn(game,uid,2,2,taunt=True)
            elif game.auction_catalog=='v22':
                for _ in range(2):
                    _spawn(game,uid,3,3)
            else:
                # Archived v4 battles retain their original copy rule.
                allies=[x for x in own.board if x!=uid and x in game.units]
                if allies:
                    strongest=max(allies,key=lambda x:(game.units[x].atk+
                                    game.units[x].max_hp,-own.board.index(x)))
                    source=game.units[strongest]
                    for _ in range(2):
                        _spawn(game,uid,source.atk,source.max_hp)
        elif mode=='grow' and uid in game.units:
            if game.auction_catalog=='v22':
                bonus_atk=bonus_hp=(1,2,3)[tier]
            elif tier==2:
                allies=[x for x in own.board if x!=uid and x in game.units]
                if not allies:return
                strongest=max(allies,key=lambda x:(game.units[x].atk+
                                game.units[x].max_hp,-own.board.index(x)))
                bonus_atk=game.units[strongest].atk
                bonus_hp=game.units[strongest].max_hp
            else:
                bonus_atk=bonus_hp=(1,4)[tier]
            game._add_effect(uid,'atk',bonus_atk,source=uid,positive=True)
            # Match._add_effect('max_hp') already adds the same bonus to
            # current HP. Applying it twice over-healed a wounded Queen.
            game._add_effect(uid,'max_hp',bonus_hp,source=uid,positive=True)
            if tier==1:game._add_effect(uid,'taunt',source=uid)
    elif aid=='A011' and context=='death':
        if tier<2:
            for e in list(foe.board):
                if e in game.units:game._damage(e,5,defer_death=True)
            if tier>=1:game._damage(f'hero:{1-owner}',5)
        else:
            for pid in (owner,1-owner):
                for card in list(game.players[pid].board):
                    if card in game.units:
                        game._damage(card,max(1,game.units[card].hp),
                                     ignore_defense=True,defer_death=True)
            game._damage(f'hero:{1-owner}',10)
    elif aid=='A013' and context=='play':
        if target in game.units and game.units[target].owner==1-owner:
            victim=game.units[target]
            pct=(25,40,60)[tier]
            value=(victim.max_hp*pct+99)//100
            if tier==2 and victim.shield:
                victim.shield=0
                victim.shield_source=''
                game._log('Łamacz Bastionów: legendarna zdolność zdejmuje Tarczę.')
            elif victim.shield:
                victim.shield=0
                victim.shield_source=''
                game._log(f'Łamacz Bastionów: Tarcza pochłania {value} obrażeń.')
                return
            game._damage(target,value,ignore_defense=True)
    elif aid=='A016' and context=='play':
        if mode=='cart_draw' and target in own.deck:
            own.deck.remove(target)
            own.hand.append(target)
            game.cards[target].zone='hand'
            game._log(f'Kartograf: {game.label(target)} dobrano do ręki.')
        if tier==1:
            # First choice can empty the deck; recycle again for the
            # optional second selection only when a board slot remains.
            if len(own.board)<5:
                game._refill_deck_from_grave(owner)
            choices=options(game,uid,'auction_cart_play')
            if choices:_prepare_pending(game,uid,'auction_cart_play',choices)
        elif tier==2 and mode=='cart_play':
            execute(game,uid,'auction_cart_play',choice)
    elif aid=='A018' and context=='play':
        if tier<2:
            own.coins+=2
            bonus=(2,5)[tier]
            game.auction_vouchers[owner].append({'bonus':bonus})
            game._log(f'Licytator: +2 monety i +{bonus} skutecznej oferty '
                      'na następną aukcję.')
        else:
            game.auction_vouchers[owner].append({'guaranteed':True})
            game._log('Licytator: gwarancja pierwszego wyboru na następną aukcję.')
    elif aid=='A012' and context=='play':
        if tier==0:
            mean=(own.hp+foe.hp)//2
            _set_hero_hp(game,owner,mean)
            _set_hero_hp(game,1-owner,mean)
            game._heal(f'hero:{owner}',10)
        elif tier==1:
            if mode=='copy_to_self':_set_hero_hp(game,owner,foe.hp)
            else:_set_hero_hp(game,1-owner,own.hp)
            game._heal(f'hero:{owner}',10)
        else:
            _set_hero_hp(game,1-owner,foe.hp-20)
            game._heal(f'hero:{owner}',20)
    game._update_auras()


def resolve_wave_ops(game):
    """Deferred capture and resurrection after one atomic death wave closes."""
    ops=game.auction_wave_ops
    game.auction_wave_ops=[]
    for item in ops:
        op=item[0]
        if op=='capture':
            _,uid,target,chain=item
            _capture(game,uid,target,chain)
        elif op=='to_hand':
            _,owner,target,_=item
            _return_to_hand(game,owner,target)
        elif op=='revive':
            _,owner,target,full=item
            _revive(game,owner,target,full)
        elif op=='revive_pair':
            _,source,owner,target=item
            if _revive(game,owner,target,True):
                others=[x for x in game.players[owner].grave
                        if x.startswith('S') and x!=target]
                if others:
                    # Second choice happens AFTER the current atomic wave.
                    game.auction_pending_targets[source]=[target]
                    _prepare_pending(game,source,'auction_return_second',
                                     options(game,source,'auction_return_second'))


def expire_exile_marks(game,owner):
    """At the boundary of the marked unit's next own turn."""
    for uid in list(game.players[owner].board):
        if uid not in game.units:continue
        u=game.units[uid]
        markers=[e for e in u.effects if e.kind=='auction_exile_mark'
                 and e.expires is not None
                 and e.expires<=game.players[owner].turn_count]
        if markers:
            _exile(game,markers[0].source,uid)
