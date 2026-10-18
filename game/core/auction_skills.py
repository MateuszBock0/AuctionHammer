"""Authoritative V3 auction abilities. Mutations only via Match engine entry points.

This remains a draft rule set: A002, A004, A010, A012 choices follow the
interpretations recorded in KATALOG_AUKCYJNY_12_v3(2).md.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import replace
from math import ceil
from .models import Card, Choice, Effect, Pending, Unit
from .auction_catalog import RARITIES


def award(game, uid):
    return game.auction_awards.get(uid)


def cid(game, uid):
    a=award(game,uid)
    return a.get('archetype') if a else None


def tier(game, uid):
    return RARITIES.index(award(game,uid)['rarity']) if award(game,uid) else 0


def options(game, uid, context):
    a=award(game,uid)
    owner=game.cards[uid].owner
    ally=[x for x in game.players[owner].board if x!=uid]
    enemy=list(game.players[1-owner].board)
    myhand=list(game.players[owner].hand)
    his_hand=list(game.players[1-owner].hand)
    def choices(mode, targets):
        return [Choice(mode, t, f'{mode}: {game.label(t)}') for t in targets]
    if not a:
        if context=='death' and uid in game.auction_death_links:
            return choices('chain_take',enemy) if len(game.players[owner].board)<5 else []
        return []
    n=a['archetype'];level=tier(game,uid)
    if n=='A001' and context=='death':
        result=choices('kill',enemy)
        if level>=1 and len(game.players[owner].board)<5:result+=choices('take',enemy)
        if level>=2 and len(game.players[owner].board)<5:result+=choices('take_link',enemy)
        return result
    if n=='A002' and context in ('play','evolve'):
        return choices('general_ally',ally) if level==1 else [Choice('auto',None,'Aura')]
    if n=='A003' and context=='death':
        available=[x for x in game.players[owner].grave if x!=uid and x.startswith('S')]
        result=choices('grave_hand',available)
        if level>=1:result+=choices('grave_field',available)
        if level>=2:result+=choices('grave_two',available)
        return result
    if n=='A004' and context=='play':
        if len(game.players[owner].board)>=5:return []
        return choices('copy',[x for x in (ally if level==0 else ally+enemy)
                               if x not in game.ephemerals])
    if n in ('A005','A011'):
        return [Choice('auto',None,'Aktywuj')]
    if n=='A006' and context=='play':
        return [Choice('auto',None,'Wycisz wszystkich')] if level==2 else choices('silence',enemy)
    if n=='A008' and context=='play':
        return choices('mark' if level==0 else 'exile',enemy)
    if n=='A009' and context=='play':
        if level==2:return [Choice('auto',None,'Wymień całe ręce')]
        return choices('swap_own',myhand) if his_hand else []
    if n=='A010' and context=='end':
        return [Choice('soldiers',None,'Przywołaj'), Choice('self_buff',None,'Wzmocnij Królową')]
    if n=='A012' and context=='play':
        if level==1:return [Choice('copy_own_hp',None,'Moje PŻ = PŻ rywala'),
                            Choice('copy_enemy_hp',None,'PŻ rywala = moje PŻ')]
        return [Choice('auto',None,'Zmiana PŻ')]
    return []


def pending_chain(game,uid,owner,choices,chain):
    if choices:
        game.auction_chain=chain
        game.pending=Pending(uid,owner,'auction_chain',choices)
    else:game.auction_chain=None


def return_to_hand(game,uid,owner):
    if uid in game.players[owner].grave:
        game.players[owner].grave.remove(uid)
        game.players[owner].hand.append(uid)
        game.cards[uid].zone='hand';game.cards[uid].owner=owner


def summon_grave(game,uid,owner,hp=None):
    if uid not in game.players[owner].grave or len(game.players[owner].board)>=5:return False
    game.players[owner].grave.remove(uid)
    game.players[owner].board.append(uid)
    c=game.cards[uid];c.zone='board';c.owner=owner
    game.units[uid]=Unit(uid,owner,c.attack,c.max_hp,hp if hp is not None else c.max_hp,
                         c.ability_level,game.players[owner].turn_count)
    game._update_auras()
    return True


def create_copy(game,target,owner,source,legendary=False,quiet=False,stats=None):
    if len(game.players[owner].board)>=5 or target in game.ephemerals:return None
    game.auction_copy_serial+=1
    uid=f'EPH{game.auction_copy_serial:06d}'
    original=game.cards[target]
    definition=original.definition
    if stats is not None:definition=replace(definition,atk=stats[0],hp=stats[1])
    card=Card(uid,definition,owner=owner,zone='board')
    game.cards[uid]=card;game.defs[uid]=definition
    src=game.units[target]
    if legendary:
        unit=deepcopy(src);unit.uid=uid;unit.owner=owner;unit.attacks=0
        unit.played_turn=game.players[owner].turn_count
        unit.shield=1;unit.shield_source=source
        unit.effects=[replace(e,source=uid if e.source==target else e.source) for e in unit.effects]
    else:
        atk,hp=stats if stats else (definition.atk,definition.hp)
        unit=Unit(uid,owner,atk,hp,hp,0,game.players[owner].turn_count)
    game.units[uid]=unit;game.players[owner].board.append(uid)
    game.ephemerals.add(uid)
    if target in game.auction_awards:game.auction_awards[uid]=dict(game.auction_awards[target])
    game._log(f'Przywołano efemeryczną kopię {game.label(target)} jako {uid}.')
    game._update_auras(defer_reactive=True)
    if not quiet and (definition.faction=='Elfy' or definition.id in ('S34','S35')):
        game._queue(uid,'play')
    return uid


def exile(game,uid):
    if uid in game.units:
        game._remove_unit(uid,death=False)
        if uid in game.cards and uid in game.players[game.cards[uid].owner].grave:
            game.players[game.cards[uid].owner].grave.remove(uid)
    elif uid in game.cards and game.cards[uid].zone=='hand':
        game.players[game.cards[uid].owner].hand.remove(uid)
    if uid in game.ephemerals:
        game.ephemerals.remove(uid)
        game.auction_awards.pop(uid,None);game.defs.pop(uid,None);game.cards.pop(uid,None)
    else:
        game.cards[uid].zone='excluded';game.cards[uid].owner=None
        game.excluded.append(uid)
    game._log(f'Wygnano {uid} bez zgonu, nagrody i efektu śmierci.')
    game._update_auras()


def capture(game,uid,newowner):
    if uid not in game.units or len(game.players[newowner].board)>=5:return False
    unit=game.units[uid]
    game.players[unit.owner].board.remove(uid)
    unit.owner=newowner;unit.attacks=0;unit.played_turn=game.players[newowner].turn_count
    game.cards[uid].owner=newowner
    game.players[newowner].board.append(uid)
    game._update_auras()
    game._log(f'Przejęcie jednostki {game.label(uid)}.')
    return True


def hero_set(game,owner,hp):
    pl=game.players[owner];old=pl.hp
    pl.hp=min(100,int(hp))
    for value in (75,50,25):
        if old>value>=pl.hp and value not in pl.thresholds:
            pl.thresholds.add(value);pl.coins+=2
            game._log(f'{pl.name}: +2 monety za przekroczenie {value} PŻ.')


def exile_random_hand(game,owner):
    hand=game.players[owner].hand
    if hand:
        index=game.rng.randrange(len(hand));game.rng_draw_index+=1
        exile(game,hand[index])


def swap(game,owner,left,right):
    a=game.players[owner].hand;b=game.players[1-owner].hand
    if left not in a or right not in b:return
    i=a.index(left);j=b.index(right)
    a[i]=right;b[j]=left
    game.cards[left].owner=1-owner;game.cards[right].owner=owner
    game._log(f'Wymiana kart z ręki: {left} ↔ {right}.')


def chain(game,uid,choice):
    state=game.auction_chain
    if state is None:return
    kind=state['kind'];owner=state['owner'];opp=1-owner
    if kind=='silence':
        if choice.target in game.units and choice.target not in state['chosen']:
            game._add_effect(choice.target,'silence',expires=game._expiry(opp),
                             source=uid,positive=False)
            state['chosen'].append(choice.target)
        game.auction_chain=None
    elif kind=='exile':
        if choice.mode!='stop' and choice.target in game.units:exile(game,choice.target)
        if choice.mode=='stop':exile_random_hand(game,opp);game.auction_chain=None;return
        state['count']+=1
        available=list(game.players[opp].board)
        if state['count']>=3 or not available:
            exile_random_hand(game,opp);game.auction_chain=None
        else:
            pending_chain(game,uid,owner,[Choice('stop',None,'Zakończ wybieranie')]+[
                Choice('exile',x,'Wygnaj '+game.label(x)) for x in available],state)
    elif kind=='swap_own':
        if state['rare']:
            state['kind']='swap_enemy';state['ours']=choice.target
            pending_chain(game,uid,owner,[Choice('swap_enemy',x,'Wybierz '+game.label(x))
                for x in game.players[opp].hand],state)
        else:
            b=game.players[opp].hand
            if b:
                ix=game.rng.randrange(len(b));game.rng_draw_index+=1
                swap(game,owner,choice.target,b[ix])
            game.auction_chain=None
    elif kind=='swap_enemy':
        swap(game,owner,state['ours'],choice.target);game.auction_chain=None
    elif kind=='discard':
        if choice.target in game.players[owner].hand:
            game.players[owner].hand.remove(choice.target)
            game.players[owner].grave.append(choice.target)
            game.cards[choice.target].zone='grave'
        state['remaining']-=1
        if state['remaining']>0 and game.players[owner].hand:
            pending_chain(game,uid,owner,[Choice('discard',x,'Odrzuć '+game.label(x))
                for x in game.players[owner].hand],state)
        else:game.auction_chain=None
    elif kind=='grave_second':
        return_to_hand(game,choice.target,owner);game.auction_chain=None


def execute(game,uid,context,choice):
    if context=='auction_chain':return chain(game,uid,choice)
    owner=game.cards[uid].owner;opp=1-owner
    name=cid(game,uid)
    mode,target=choice.mode,choice.target
    if name is None:
        if mode=='chain_take':capture(game,target,owner)
        return
    level=tier(game,uid)
    if name=='A001' and context=='death':
        if mode=='kill' and target in game.units:
            game.units[target].hp=0;game._kill_batch([target])
        elif mode in ('take','take_link') and capture(game,target,owner):
            if mode=='take_link':game.auction_death_links.add(target)
    elif name=='A002' and context in ('play','evolve'):
        if mode=='general_ally':game.auction_awards[uid]['beneficiary']=target
    elif name=='A003' and context=='death':
        if mode=='grave_hand':return_to_hand(game,target,owner)
        elif mode=='grave_field':
            if not summon_grave(game,target,owner,1):return_to_hand(game,target,owner)
        elif mode=='grave_two':
            available=[x for x in game.players[owner].grave if x!=uid and x.startswith('S')]
            if target not in available:return
            if not summon_grave(game,target,owner):return_to_hand(game,target,owner)
            others=[x for x in available if x!=target and x in game.players[owner].grave]
            pending_chain(game,uid,owner,[Choice('grave_second',x,'Na rękę '+game.label(x))
                  for x in others],{'kind':'grave_second','owner':owner})
    elif name=='A004' and context=='play':
        if target in game.units:create_copy(game,target,owner,uid,legendary=level==2)
    elif name=='A005' and context=='play':
        enemy=game.players[opp];ours=game.players[owner]
        theft=3 if level==0 else max(3,ceil(enemy.coins/2)) if level==1 else enemy.coins
        stolen=min(theft,enemy.coins)
        enemy.coins-=stolen;ours.coins+=stolen
        fresh=(3,4,5)[level];ours.coins+=fresh
        game._log(f'Bankier: przeniósł {stolen} monet, wygenerował {fresh} nowych.')
    elif name=='A006' and context=='play':
        if level==2:
            for x in list(game.players[opp].board):
                game._add_effect(x,'silence',expires=game._expiry(opp),
                                 source=uid,positive=False)
        elif target in game.units:
            game._add_effect(target,'silence',expires=game._expiry(opp),
                             source=uid,positive=False)
            others=[x for x in game.players[opp].board if x!=target]
            if level==1:
                pending_chain(game,uid,owner,[Choice('silence',x,'Wycisz '+game.label(x))
                      for x in others],{'kind':'silence','owner':owner,'chosen':[target]})
    elif name=='A008' and context=='play':
        if level==0 and target in game.units:
            game._add_effect(target,'banish_mark',expires=game._expiry(opp),
                             source=uid,positive=False)
        elif level==1:
            if target in game.units:exile(game,target)
            exile_random_hand(game,opp)
        else:
            if target in game.units:exile(game,target)
            available=list(game.players[opp].board)
            if available:
                pending_chain(game,uid,owner,[Choice('stop',None,'Zakończ')]+[
                    Choice('exile',x,'Wygnaj '+game.label(x)) for x in available],
                    {'kind':'exile','owner':owner,'count':1})
            else:exile_random_hand(game,opp)
    elif name=='A009' and context=='play':
        if level==2:
            a=game.players[owner].hand;b=game.players[opp].hand
            game.players[owner].hand=b;game.players[opp].hand=a
            for x in a:game.cards[x].owner=opp
            for x in b:game.cards[x].owner=owner
            pending_chain(game,uid,opp,[Choice('discard',x,'Odrzuć '+game.label(x)) for x in a],
                          {'kind':'discard','owner':opp,'remaining':min(2,len(a))})
        elif target in game.players[owner].hand:
            state={'kind':'swap_own','owner':owner,'rare':level==1}
            pending_chain(game,uid,owner,[Choice('swap_own',target,'Potwierdź wymianę')],state)
    elif name=='A010' and context=='end' and uid in game.units:
        u=game.units[uid]
        if mode=='self_buff':
            if level==0:atk,hp=1,1
            elif level==1:atk,hp=4,4
            else:
                other=[game.units[x] for x in game.players[owner].board if x!=uid]
                if not other:return
                best=max(other,key=lambda z:(z.atk+z.max_hp,-game.players[owner].board.index(z.uid)))
                atk,hp=best.atk,best.max_hp
            u.base_attack+=atk;u.base_max_hp+=hp;u.hp+=hp
            if level==1:game._add_effect(uid,'taunt',source=uid)
        else:
            if level<2:
                atk=1 if level==0 else 2
                for _ in range(min(1 if level==0 else 2,5-len(game.players[owner].board))):
                    soldier=create_copy(game,uid,owner,uid,quiet=True,stats=(atk,atk))
                    if soldier and level==1:game._add_effect(soldier,'taunt',source=uid)
            else:
                others=[game.units[x] for x in game.players[owner].board
                        if x!=uid and x not in game.ephemerals]
                if not others:return
                best=max(others,key=lambda z:(z.atk+z.max_hp,-game.players[owner].board.index(z.uid)))
                for _ in range(min(2,5-len(game.players[owner].board))):
                    create_copy(game,best.uid,owner,uid,quiet=True,stats=(best.atk,best.max_hp))
    elif name=='A011' and context=='death':
        if level<=1:
            victims=list(game.players[opp].board)
            events=[(x,5,False) for x in victims]
            if level==1:events.append((f'hero:{opp}',5,False))
        else:
            events=[(x,999999,True) for x in list(game.units)]
            events.append((f'hero:{opp}',10,False))
        if game._resolving_death_wave:game._wave_damage.extend(events)
        else:
            for target,damage,ignore in events:game._damage(target,damage,ignore,defer_death=True)
            game._kill_batch([x for x,u in list(game.units.items()) if u.hp<=0])
    elif name=='A012' and context=='play':
        if level==0:
            avg=(game.players[owner].hp+game.players[opp].hp)//2
            hero_set(game,owner,avg);hero_set(game,opp,avg)
            game._heal(f'hero:{owner}',10)
        elif level==1:
            if mode=='copy_own_hp':hero_set(game,owner,game.players[opp].hp)
            else:hero_set(game,opp,game.players[owner].hp)
            game._heal(f'hero:{owner}',10)
        else:
            hero_set(game,opp,game.players[opp].hp-20)
            game._heal(f'hero:{owner}',20)
        game._check_winner()


def evolve(game,completed_round):
    for uid,a in list(game.auction_awards.items()):
        if uid in game.ephemerals:continue
        elapsed=completed_round-a.get('completed_round',completed_round)
        if elapsed<=0 or elapsed%3!=0:continue
        current=RARITIES.index(a['rarity'])
        if current>=2:continue
        a['rarity']=RARITIES[current+1]
        game._log(f'Karta {game.label(uid)} ewoluuje: {a["rarity"]}.')
        if a['archetype']=='A002' and current+1==1 and uid in game.units:
            game._queue(uid,'evolve')


def double_and_damage(game,uid):
    for source in game.players[game.units[uid].owner].board:
        a=award(game,source)
        if not a or a['archetype']!='A002' or source not in game.units:return_if_false=False
        else:return_if_false=True
        if not return_if_false or game._disabled(game.units[source]):continue
        grade=tier(game,source)
        if grade==1 and a.get('beneficiary')==uid:return True
        if grade==2 and uid in a.get('beneficiaries',[]):return True
    return False


def heroic_save(game,owner):
    if game.players[owner].hp>0:return False
    for uid in list(game.players[owner].board):
        a=award(game,uid)
        if a and a['archetype']=='A007' and not a.get('rescue_used') and uid in game.units and not game._disabled(game.units[uid]):
            grade=tier(game,uid)
            a['rescue_used']=True
            game.players[owner].hp=(1,20,25)[grade]
            game._log(f'{game.label(uid)} poświęca się i ratuje bohatera.')
            game._kill_batch([uid])
            if grade==2:
                for x in list(game.players[1-owner].board):
                    game._add_effect(x,'stun',expires=game._expiry(1-owner),
                                     source=uid,positive=False)
            return True
    return False