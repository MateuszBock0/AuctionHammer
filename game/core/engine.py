"""AuctionHammer: deterministyczny silnik meczu solo oparty na Game Master v19.
Wszystkie mutacje stanu gry odbywają się tutaj — UI i AI wysyłają komendy.
"""
from __future__ import annotations
from collections import deque
from pathlib import Path
import sys
import random
from .models import Card, Unit, Player, Effect, Pending, Choice, IllegalMove, load_catalog
from .effects import options
from .audit import initialize_audit, audit_action, trace_effect
from . import auction as auction_rules
from . import auction_skills

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))

class Match:
    def __init__(self, seed: int | None = None, audit_enabled: bool = False,
                 auctions_enabled: bool = False,
                 auction_catalog_mode: str = 'placeholders'):
        # Opt in from the real game client; bulk simulations remain lightweight.
        self.audit_enabled=bool(audit_enabled)
        self.auctions_enabled=bool(auctions_enabled)
        self.auction_catalog_mode=auction_catalog_mode
        self.ephemerals=set()
        self.auction_copy_serial=0
        self.auction_death_links=set()
        self.auction_chain=None
        self.auction=None
        self.auction_history=[]
        self.auction_awards={}
        self.seed = seed if seed is not None else random.SystemRandom().randrange(2**31)
        self.rng = random.Random(self.seed)
        self.defs = load_catalog(ROOT / 'data' / 'cards_base_70.json')
        self.cards = {id:Card(id,d) for id,d in self.defs.items()}
        self.units: dict[str,Unit] = {}
        self.bank = list(self.cards)
        self.rng.shuffle(self.bank)
        self.players = [Player(0,'GRACZ'),Player(1,'KOMPUTER')]
        self.first = self.rng.randrange(2)
        self.active = self.first
        self.players[1-self.first].coins = 3
        self.round = 1
        self.phase = 'mulligan'
        self.pending: Pending | None = None
        self.trigger_queue = deque()  # zwykłe wyzwalacze: (uid, context, target)
        # Każda fala przechowuje *zamrożone* wybory wszystkich źródeł zgonu.
        # Efekty śmierci z jednej fali wykonują się dopiero po zebraniu
        # wszystkich decyzji, bez usuwania nowych ofiar w jej środku.
        self.death_waves = deque()
        self.active_death_wave = None
        self._resolving_death_wave = False
        self._next_death_wave_id = 1
        self._wave_damage = []
        self._wave_healing = []
        self._wave_status_ops = []
        self._wave_defense_ops = []
        self._suspend_hero_thresholds = False
        self.deferred_attack: tuple[str,str] | None = None
        self.end_queue: deque[str] | None = None
        self._next_turn_due = False
        self.position_reactions_due = False
        self._draining = False
        self.winner: int | None = None
        self.events: list[str] = []
        # Dziennik obserwacyjny dla historii i powtórek; bez wpływu na silnik.
        self.event_journal: list[dict] = []
        self.serial = 0
        self._death_disabled = {}
        self._death_levels = {}
        self.action_turn = 0
        self.rng_draw_index = 0  # v19: licznik rzeczywistych losowań efektów
        self.mulligan_done = set()
        self.mulligan_requests: dict[int,list[str]] = {}
        self.excluded: list[str] = []
        for p in self.players:
            for i in range(10):
                uid = self.bank.pop()
                self.cards[uid].owner=p.idx
                if i<5:
                    p.hand.append(uid); self.cards[uid].zone='hand'
                else:
                    p.deck.append(uid); self.cards[uid].zone='deck'
            self.rng.shuffle(p.deck)
        self._log('Rozdano po 5 kart na rękę i do talii. Po jednym egzemplarzu na typ.')
        self._log(f'Pierwszy ruch: {self.players[self.first].name}. Drugi gracz ma 3 monety.')
        if self.auctions_enabled:
            self._log("Wariant aukcyjny testowy: aukcje po rundach 3, 6, 9...")
        if self.audit_enabled:
            initialize_audit(self)

    def _log(self, line):
        event={'seq':len(self.event_journal)+1,
               'round':self.round,'active':self.active,
               'phase':self.phase,'text':line}
        if getattr(self,'audit_enabled',False) and hasattr(self,'audit_actions'):
            event['action_seq']=getattr(self,'_audit_open_action',None)
            event['internal_seq']=getattr(self,'_audit_open_internal',None)
        self.event_journal.append(event)
        self.events.append(line)
        self.events=self.events[-160:]

    def label(self, target):
        if target is None: return 'brak'
        if isinstance(target,str) and target.startswith('hero:'):
            return 'Bohater — '+self.players[int(target.split(':')[1])].name
        return self.cards[target].definition.name

    def _check(self, condition, message):
        if not condition: raise IllegalMove(message)

    def _player(self): return self.players[self.active]

    @audit_action('mulligan_toggle')
    def mulligan_toggle(self, uid):
        self._check(self.phase=='mulligan','Mulligan zakończony')
        p=self.players[0]
        self._check(uid in p.hand,'Nie ma karty na ręce')
        if uid in p.mulligan_selected:
            p.mulligan_selected.remove(uid)
        else:
            self._check(len(p.mulligan_selected)<3,'Maksymalnie 3 karty')
            p.mulligan_selected.append(uid)

    @audit_action('finish_mulligan')
    def finish_mulligan(self, player_idx=0, selected=None):
        self._check(self.phase=='mulligan','Nie ten etap')
        self._check(player_idx not in self.mulligan_done,'Mulligan już zakończony')
        p=self.players[player_idx]
        selected=list(p.mulligan_selected if selected is None else selected)
        self._check(len(selected)<=3 and len(selected)==len(set(selected)) and all(x in p.hand for x in selected),'Niedozwolony mulligan')
        # v17: both players submit hidden choices. A single authoritative draw
        # resolves the two submissions together, without returning discards.
        self.mulligan_requests[player_idx] = selected
        self.mulligan_done.add(player_idx)
        self._log(f'{p.name}: zatwierdzono wybór mulliganu.')
        if len(self.mulligan_done)==2:
            # Selection order must not influence access to returned cards.
            for pid in (0,1):
                player=self.players[pid]
                for old in self.mulligan_requests[pid]:
                    self._check(bool(self.bank),'Brak zamienników w banku')
                    new=self.bank.pop(self.rng.randrange(len(self.bank)))
                    player.hand[player.hand.index(old)]=new
                    self.cards[new].owner=pid
                    self.cards[new].zone='hand'
                    self.cards[old].zone='excluded'
                    self.cards[old].owner=None
                    self.excluded.append(old)
                player.mulligan_selected.clear()
                self._log(f'{player.name}: wymieniono {len(self.mulligan_requests[pid])} kart.')
            self.phase='turn'
            self._start_turn()
            self.assert_integrity()

    @trace_effect('_start_turn')
    def _start_turn(self):
        if self.phase=='finished':return
        p=self._player()
        p.turn_count += 1
        self.action_turn += 1
        p.played_this_turn=False
        for uid in p.board:self.units[uid].attacks=0
        # All own-turn START draw before poison as specified.
        while len(p.hand)<5:
            if not p.deck:
                if not p.grave:break
                p.deck=p.grave[:];p.grave.clear();self.rng.shuffle(p.deck)
                for uid in p.deck:self.cards[uid].zone='deck'
                self._log(f'{p.name}: przetasowano cmentarz do talii.')
            uid=p.deck.pop()
            p.hand.append(uid);self.cards[uid].zone='hand'
        self._log(f'RUNDA {self.round} | Tura {p.name} (ręka {len(p.hand)}).')
        self._tick_poison(p.idx)
        self._drain()

    @trace_effect('_tick_poison')
    def _tick_poison(self,owner):
        # One atomic poison wave for all units of this player (v17).
        fallen=[]
        for uid in list(self.players[owner].board):
            if uid not in self.units:continue
            u=self.units[uid]
            poison=[e for e in u.effects if e.kind=='poison' and e.remaining>0]
            if not poison:continue
            dmg=sum(e.value+(e.bonus_once if e.remaining==e.initial_ticks else 0) for e in poison)
            self._damage(uid,dmg,ignore_defense=True,defer_death=True)
            for e in poison:e.remaining-=1
            u.effects=[e for e in u.effects if e.kind!='poison' or e.remaining>0]
            if u.hp<=0:fallen.append(uid)
        p=self.players[owner]
        poison=[e for e in p.hero_effects if e.kind=='poison' and e.remaining>0]
        if poison:
            self._damage('hero:'+str(owner),sum(e.value+(e.bonus_once if e.remaining==e.initial_ticks else 0) for e in poison),ignore_defense=True)
            for e in poison:e.remaining-=1
            p.hero_effects=[e for e in p.hero_effects if e.kind!='poison' or e.remaining>0]
        if fallen:self._kill_batch(fallen)

    def can_play(self,player,uid,replace=None):
        p=self.players[player]
        if self.phase!='turn' or self.pending or self.active!=player or p.played_this_turn or uid not in p.hand:return False
        if len(p.board)<5:return replace is None
        return replace in p.board and self.units[replace].attacks==0

    @audit_action('play')
    def play(self,uid,replace=None):
        p=self._player()
        self._check(self.can_play(self.active,uid,replace),'Nie można zagrać tej karty (1 na turę; pełna plansza wymaga zastąpienia niewykorzystanej jednostki)')
        if replace is not None:
            self._remove_unit(replace,death=False)
            self._log(f'{p.name}: zastąpiono {self.label(replace)} (bez śmierci).')
        card=self.cards[uid]
        p.hand.remove(uid)
        card.zone='board'
        u=Unit(uid,p.idx,card.attack,card.max_hp,card.max_hp,card.ability_level,p.turn_count)
        self.units[uid]=u;p.board.append(uid)
        p.played_this_turn=True
        if p.next_fast or card.quick_next_turn==p.turn_count or card.quick_on_first_summon:
            self._add_effect(uid,'quick',source='S66' if card.quick_on_first_summon else 'temporary',expires=p.turn_count)
            p.next_fast=False
        u.fallback_double_pending=card.double_on_first_eligible
        card.quick_on_first_summon=False
        card.double_on_first_eligible=False
        card.quick_next_turn=None
        self._log(f'{p.name} wystawia {self.label(uid)} {u.atk}/{u.hp}.')
        if self._fast(u):
            self._log(f'{self.label(uid)}: Szybki atak — może atakować od razu.')
        # Apply continuous auras immediately, but resolve first-sighting
        # reactive triggers only after the played card's primary ON_PLAY effect.
        self._update_auras(defer_reactive=True)
        self.position_reactions_due=True
        if card.definition.faction=='Elfy':self._queue(uid,'play')
        if uid in self.auction_awards and self.auction_awards[uid].get('archetype')=='A002':
            self._queue(uid,'play')
        # Legendary Generals empower only subsequently played allies.
        if uid not in self.ephemerals:
            for src in list(p.board):
                if src==uid:continue
                meta=self.auction_awards.get(src)
                if (meta and meta.get('archetype')=='A002'
                        and meta.get('rarity')=='legendarna'
                        and not self._disabled(self.units[src])):
                    meta.setdefault('beneficiaries',[]).append(uid)
        if card.definition.id in ('S34','S35'):
            self._queue(uid,'play')
        if card.definition.id == 'S106':u.shield=1;u.shield_source=uid;u.used_shield_aura=False
        if uid in self.auction_awards and self.auction_awards[uid].get('archetype','PLACEHOLDER')=='PLACEHOLDER':
            u.shield=1
            u.shield_source=uid
            self._log(f'{self.label(uid)}: wrodzona Prowokacja i 1 Tarcza (karta aukcyjna).')
        if card.definition.id == 'S39' and u.ability_level:
            u.armor_perm+=u.ability_level
            u.armor_perm_source=uid
            u.armor_perm_grants[uid]=u.armor_perm_grants.get(uid,0)+u.ability_level
            u.passives_triggered.add('immune_bonus')
        self._drain()

    def legal_attacks(self,uid):
        if uid not in self.units or self.phase!='turn' or self.pending or self.active!=self.units[uid].owner:return []
        u=self.units[uid];p=self.players[u.owner]; d=self.cards[uid].definition
        if self._has(u,'stun'):return []
        if u.played_turn==p.turn_count and not self._fast(u):return []
        if u.attacks >= (2 if self._double(u) else 1):return []
        target_units=self.players[1-u.owner].board
        taunts=[x for x in target_units if self._taunt(self.units[x])]
        return taunts if taunts else target_units+['hero:'+str(1-u.owner)]

    @audit_action('attack')
    def attack(self,uid,target):
        self._check(target in self.legal_attacks(uid),'Nielegalny cel ataku')
        a=self.units[uid];a.attacks+=1
        self._log(f'{self.label(uid)} atakuje: {self.label(target)}.')
        self.deferred_attack=(uid,target)
        if uid in self.units and self.cards[uid].definition.faction=='Dzikie bestie' and not self._disabled(a):
            self._queue(uid,'attack',target)
        self._drain()

    def _finish_attack(self,uid,target):
        if uid not in self.units or target not in self.units and not target.startswith('hero:'):
            return
        # v17 priority stage 4: passive defender response AFTER ON_ATTACK,
        # before simultaneous standard combat. Attack has already been spent.
        if target in self.units and self.cards[target].definition.id=='S103' and not self._disabled(self.units[target]):
            self._damage(uid,1+self.units[target].ability_level)
        if uid not in self.units or (target not in self.units and not target.startswith('hero:')):
            return
        a=self.units[uid]
        amplifier=2 if auction_skills.double_and_damage(self,uid) else 1
        if target.startswith('hero:'):
            self._damage(target,a.atk*amplifier)
        else:
            b=self.units[target]
            da,db=a.atk*amplifier,b.atk*(2 if auction_skills.double_and_damage(self,target) else 1)
            # simultaneous damage; store victims until both are applied
            to_attacker=self._damage(uid,db,defer_death=True)
            to_defender=self._damage(target,da,defer_death=True)
            # Passive S107 triggers when standard damage actually wounded it.
            if uid in self.units and target in self.units:
                for defender,attacker in ((uid,target),(target,uid)):
                    d=self.cards[defender].definition
                    received=to_attacker if defender==uid else to_defender
                    if d.id=='S107' and received>0 and not self._disabled(self.units[defender]):
                        self._add_poison(attacker,1,2,defender,self.units[defender].ability_level)
            fallen=[c for c in (uid,target) if c in self.units and self.units[c].hp<=0]
            self._kill_batch(fallen)
        self._update_auras()

    @audit_action('end_turn')
    def end_turn(self):
        self._check(self.phase=='turn' and self.pending is None and self.end_queue is None and self.deferred_attack is None,'Nie można zakończyć tury')
        self.end_queue=deque(self._player().board)
        self._log(f'{self._player().name} kończy turę.')
        self._drain()

    @audit_action('choose')
    def choose(self,index):
        self._check(self.pending is not None,'Brak wyboru')
        pending=self.pending
        self._check(0<=index<len(pending.choices),'Nieprawidłowy wybór')
        choice=pending.choices[index]
        self.pending=None
        if pending.context=='death' and self.active_death_wave is not None:
            wave=self.active_death_wave
            self._check(wave['cursor'] < len(wave['sources'])
                        and wave['sources'][wave['cursor']][0]==pending.uid,
                        'Niezgodność kolejki wspólnej fali śmierci')
            wave['decisions'].append((pending.uid,choice))
            wave['cursor']+=1
        else:
            self._execute(pending.uid,pending.context,choice,pending.attack_target)
        self._drain()

    def _queue(self,uid,context,target=None):
        self.trigger_queue.append((uid,context,target))

    def _drain(self):
        if self._draining:return
        self._draining=True
        try:
            limit=0
            while self.phase=='turn' and self.pending is None and limit<300:
                limit+=1
                # Otwarta fala ma pierwszeństwo nad nowymi efektami. Najpierw
                # zbieramy wszystkie wybory, potem rozpatrujemy wspólny wynik.
                if self.active_death_wave is not None:
                    wave=self.active_death_wave
                    if wave['cursor']<len(wave['sources']):
                        uid,choices=wave['sources'][wave['cursor']]
                        if not choices:
                            wave['cursor']+=1
                        elif len(choices)==1 and choices[0].mode=='auto':
                            wave['decisions'].append((uid,choices[0]))
                            wave['cursor']+=1
                        else:
                            self.pending=Pending(uid,self.cards[uid].owner,
                                                 'death',list(choices))
                        continue
                    self.active_death_wave=None
                    self._resolve_death_wave(wave)
                    continue
                if self.trigger_queue:
                    uid,ctx,tgt=self.trigger_queue.popleft()
                    if ctx not in ('death',) and uid not in self.units:continue
                    if ctx in ('death',) and self._death_disabled.get(uid,False):continue
                    choices=(auction_skills.options(self,uid,ctx) if (uid in self.auction_awards or uid in self.auction_death_links) else options(self,uid,ctx,tgt))
                    if not choices:continue
                    if len(choices)==1 and choices[0].mode=='auto':
                        self._execute(uid,ctx,choices[0],tgt)
                    else:
                        self.pending=Pending(uid,self.cards[uid].owner,ctx,choices,tgt)
                    continue
                if self.death_waves:
                    wave=self.death_waves.popleft()
                    if wave['sources'] is None:
                        # A subsequent cohort can already have been detected
                        # due to aura collapse. It receives its OWN choice
                        # snapshot only after the preceding group has closed.
                        wave['sources']=tuple(
                            (uid,tuple(auction_skills.options(self,uid,'death') if (uid in self.auction_awards or uid in self.auction_death_links) else options(self,uid,'death')))
                            for uid in wave['source_ids'])
                    self.active_death_wave=wave
                    continue
                if self.position_reactions_due:
                    self.position_reactions_due=False
                    self._update_auras()
                    continue
                if self.deferred_attack:
                    uid,target=self.deferred_attack
                    self.deferred_attack=None
                    self._finish_attack(uid,target)
                    continue
                if self.end_queue is not None:
                    if self.end_queue:
                        uid=self.end_queue.popleft()
                        if uid in self.units and self.cards[uid].definition.faction=='Krasnoludy' and not self._disabled(self.units[uid]):
                            self._queue(uid,'end')
                        continue
                    self.end_queue=None
                    self._finalize_end_turn()
                    continue
                if self._next_turn_due:
                    # Resolve queued death triggers and hero lethal BEFORE starting a new turn.
                    self._next_turn_due=False
                    self._check_winner()
                    if self.phase=='finished':break
                    if (self.auctions_enabled and (self.round-1)%3==0
                            and self.round>1 and not any(
                                item["completed_round"]==self.round-1
                                for item in self.auction_history)):
                        self._next_turn_due=True  # resume exactly this boundary after the auction
                        auction_rules.begin(self)
                        break
                    self.active=1-self.active
                    self._update_auras()
                    self._start_turn()
                    continue
                break
            self._check(limit<300,'Zbyt długa kolejka efektów')
            if (not self.trigger_queue and not self.deferred_attack and self.pending is None
                    and not self.death_waves and self.active_death_wave is None):
                self._check_winner()
        finally:
            self._draining=False


    @trace_effect('_finalize_end_turn')
    def _finalize_end_turn(self):
        p=self._player()
        for uid in list(p.board):
            if uid not in self.units:continue
            u=self.units[uid]
            if not self._disabled(u) and self.cards[uid].definition.id=='S109':
                self._heal(uid,2+u.ability_level)
            portions=[e for e in u.effects if e.kind=='regen' and e.remaining>0]
            if portions:
                self._heal(uid,sum(e.value+(e.bonus_once if e.remaining==e.initial_ticks else 0) for e in portions))
                for e in portions:e.remaining-=1
                u.effects=[e for e in u.effects if e.kind!='regen' or e.remaining>0]
        # End of the controller's turn is the boundary for pending exile marks.
        for marked in list(p.board):
            if marked in self.units and any(e.kind=='banish_mark' and e.expires is not None
                                             and e.expires<=p.turn_count for e in self.units[marked].effects):
                auction_skills.exile(self,marked)
        for uid in p.hand:
            card=self.cards[uid]
            if uid not in self.auction_awards and uid not in self.ephemerals:
                card.hand_turns+=1
        # v19 S91: the deferred grant expires after the first own turn when
        # the unit was legally able to attack; stun delays that first turn.
        for uid in list(p.board):
            if uid not in self.units:continue
            unit=self.units[uid]
            if unit.fallback_double_pending and not self._has(unit,'stun') and (unit.played_turn!=p.turn_count or self._fast(unit)):
                unit.fallback_double_pending=False
        for uid in list(p.board):
            if uid not in self.units:continue
            u=self.units[uid]
            oldmax=u.max_hp
            old_effects=u.effects
            u.effects=[e for e in u.effects if (e.expires is None or e.expires>p.turn_count or u.owner!=p.idx) and (e.expire_action is None or e.expire_action>self.action_turn)]
            for effect in old_effects:
                if effect not in u.effects and effect.kind=='temp_armor_marker':u.temporary_armor.pop(effect.source,None)
            if u.max_hp<oldmax: u.hp-=oldmax-u.max_hp
            elif u.hp>u.max_hp:u.hp=u.max_hp
        for pl in self.players:
            if pl.idx!=p.idx:
                for uid in list(pl.board):
                    if uid not in self.units: continue
                    enemy=self.units[uid];oldmax=enemy.max_hp
                    old_effects=enemy.effects
                    enemy.effects=[e for e in enemy.effects if e.expire_action is None or e.expire_action>self.action_turn]
                    for effect in old_effects:
                        if effect not in enemy.effects and effect.kind=='temp_armor_marker':enemy.temporary_armor.pop(effect.source,None)
                    if enemy.max_hp<oldmax:enemy.hp-=oldmax-enemy.max_hp
                    enemy.hp=min(enemy.hp,enemy.max_hp)
        p.hero_effects=[e for e in p.hero_effects if e.expires is None or e.expires>p.turn_count]
        for uid in p.hand:
            c=self.cards[uid]
            if c.quick_next_turn is not None and c.quick_next_turn<=p.turn_count:c.quick_next_turn=None
        fallen=[uid for uid in p.board if self.units[uid].hp<=0]
        self._kill_batch(fallen)
        if p.idx!=self.first:
            self.round+=1
            for pl in self.players:pl.coins+=1
            self._log('Pełna runda: +1 moneta dla obu graczy.')
            if self.auction_catalog_mode=='v3':
                auction_skills.evolve(self,self.round-1)
        self._next_turn_due=True
        self._update_auras()

    def _has(self,u,kind):return any(e.kind==kind for e in u.effects)
    def _disabled(self,u):return self._has(u,'stun') or self._has(u,'silence')
    def _fast(self,u):return self._has(u,'quick') or (self.cards[u.uid].definition.id=='S114' and not self._disabled(u))
    def _double(self,u):
        if self.auction_catalog_mode=='v3' and auction_skills.double_and_damage(self,u.uid):return True
        # S67 grants a status on play; it no longer has innate double attack.
        # S91's hand fallback grants double for the first *eligible* own turn.
        p=self.players[u.owner]
        eligible=(u.played_turn!=p.turn_count or self._fast(u)) and not self._has(u,'stun')
        fallback=u.fallback_double_pending and eligible
        intrinsic=(self.cards[u.uid].definition.id in ('S115','S79') and not self._disabled(u)
                   and (self.cards[u.uid].definition.id!='S79' or u.attacks>0))
        return self._has(u,'double') or fallback or intrinsic
    def _taunt(self,u):
        return (self._has(u,'taunt') or
                ((self.cards[u.uid].definition.id=='S33' or u.uid in self.auction_awards)
                 and not self._disabled(u)))

    def _expiry(self,owner,kind='next'):
        p=self.players[owner]
        return p.turn_count+(0 if self.active==owner and self.end_queue is None and self.phase=='turn' else 1)

    @trace_effect('_add_effect')
    def _add_effect(self,uid,kind,value=0,remaining=0,expires=None,source='',positive=True,bonus_once=0,expire_action=None):
        u=self.units.get(uid)
        if u is None:return False
        if kind in ('poison','stun') and self._is_immune(uid,kind):return False
        if not positive and self.cards[uid].definition.id=='S111' and not self._disabled(u):
            # S111 immediately removes *temporary* negative effects. Permanent
            # penalties are outside the card's cleansing scope (GM v17).
            temporary = expires is not None or expire_action is not None or remaining>0
            if temporary:
                self._log(f'{self.label(uid)} usuwa nałożony efekt {kind} (S111).')
                # Quality upgrade: +1 HP per stored level, only when an
                # eligible negative status was actually intercepted/removed.
                if u.ability_level:
                    self._heal(uid,u.ability_level)
                return False
        if self._resolving_death_wave:
            # Dopóki nie poznamy wszystkich wyników, nowe statusy nie mogą
            # wpływać na ocenę kolejnej zdolności z TEJ SAMEJ migawki.
            self._wave_status_ops.append(('add',uid,kind,value,remaining,expires,
                                          source,positive,bonus_once,expire_action))
            return True
        if kind=='stun':
            existing=[e.expires or 0 for e in u.effects if e.kind=='stun']
            if existing:expires=max(expires or 0,max(existing)+1)
        u.effects.append(Effect(kind,value,remaining,expires,source,positive,bonus_once,expire_action,remaining))
        if kind=='max_hp':
            if value>0:u.hp+=value
            else:u.hp=min(u.hp,u.max_hp)
        suffix=f' od {self.label(source)}' if source in self.cards and source!=uid else ''
        self._log(f'{self.label(uid)} otrzymuje {kind} {value if value else ""}{suffix}'.strip())
        return True

    def _is_immune(self,uid,kind):
        if uid not in self.units:return False
        return any(e.kind=='immune_'+kind for e in self.units[uid].effects) or (kind=='poison' and self.cards[uid].definition.id=='S39' and not self._disabled(self.units[uid]))

    @trace_effect('_add_poison')
    def _add_poison(self,target,total,turns,source,bonus=0):
        if target in self.units:
            if self._is_immune(target,'poison'):return
            if self.cards[source].definition.id=='S32' and any(e.kind=='poison' and e.source==source for e in self.units[target].effects):return
            self._add_effect(target,'poison',total,turns,source=source,positive=False,bonus_once=bonus)
        elif target and target.startswith('hero:'):
            self.players[int(target.split(':')[1])].hero_effects.append(Effect('poison',total,turns,source=source,positive=False))

    @trace_effect('_grant_immunity')
    def _grant_immunity(self,target,types,expires=None,source=''):
        if target not in self.units:return
        if self._resolving_death_wave:
            self._wave_status_ops.append(('immune',target,tuple(types),expires,source))
            return
        u=self.units[target]
        for kind in types:
            u.effects=[e for e in u.effects if e.kind!=kind]
            self._add_effect(target,'immune_'+kind,expires=expires,source=source)

    @trace_effect('_clean')
    def _clean(self,target,negative=True):
        if target not in self.units:return False
        u=self.units[target]
        if self._resolving_death_wave:
            useful=any(e.positive!=negative and
                       (e.expires is not None or e.expire_action is not None
                        or e.kind in ('poison','regen')) for e in u.effects)
            self._wave_status_ops.append(('clean',target,negative))
            return useful
        oldmax=u.max_hp
        old_effects=list(u.effects)
        before=len(u.effects)
        u.effects=[e for e in u.effects if not (e.positive!=negative and (e.expires is not None or e.expire_action is not None or e.kind in ('poison','regen')))]
        # Cleansing a temporary armor marker must also remove its actual armor.
        removed=[e for e in old_effects if e not in u.effects and e.kind=='temp_armor_marker']
        for e in removed:u.temporary_armor.pop(e.source,None)
        if u.max_hp<oldmax:u.hp-=oldmax-u.max_hp
        if u.hp>u.max_hp:u.hp=u.max_hp
        return len(u.effects)!=before

    @trace_effect('_heal')
    def _heal(self,target,amount,ability=True):
        if self._resolving_death_wave:
            self._wave_healing.append((target,amount,ability))
            return
        if target in self.units:
            u=self.units[target]
            if ability:
                for ally in self.players[u.owner].board:
                    if ally in self.units and self.cards[ally].definition.id=='S104' and not self._disabled(self.units[ally]):
                        amount += 2+self.units[ally].ability_level
            u.hp=min(u.max_hp,u.hp+max(0,amount))
        elif target and target.startswith('hero:'):
            p=self.players[int(target.split(':')[1])];p.hp=min(100,p.hp+max(0,amount))

    @staticmethod
    def _spend_permanent_armor(u, amount):
        """Consume armor and its source ledger in FIFO order.

        Historical/debug states without ledger entries are permitted; only the
        numeric armor value is authoritative for combat.
        """
        taken=min(max(0,amount),u.armor_perm)
        u.armor_perm-=taken
        remaining=taken
        for src in list(u.armor_perm_grants):
            if remaining<=0:break
            spent=min(remaining,u.armor_perm_grants[src])
            u.armor_perm_grants[src]-=spent
            remaining-=spent
            if u.armor_perm_grants[src]<=0:del u.armor_perm_grants[src]
        if not u.armor_perm:u.armor_perm_source=''
        return taken

    @trace_effect('_damage')
    def _damage(self,target,amount,ignore_defense=False,defer_death=False):
        amount=max(0,amount)
        if amount<=0:return 0
        if self._resolving_death_wave:
            # Obrażenia zdolności śmierci nakładamy razem, po przygotowaniu
            # konsekwencji WSZYSTKICH źródeł z tej samej fali.
            self._wave_damage.append((target,amount,ignore_defense))
            return 0
        if target in self.units:
            u=self.units[target]
            if not ignore_defense:
                if u.shield:
                    u.shield=0;u.shield_source="";return 0
                absorb=min(amount,u.armor_temp);u.armor_temp-=absorb;amount-=absorb
                if not u.armor_temp:u.armor_temp_source=""
                for key in list(u.temporary_armor):
                    absorb=min(amount,u.temporary_armor[key]);u.temporary_armor[key]-=absorb;amount-=absorb
                for key in list(u.aura_armor):
                    absorb=min(amount,u.aura_armor[key]);u.aura_armor[key]-=absorb;amount-=absorb
                absorb=self._spend_permanent_armor(u,amount);amount-=absorb
            dealt=max(0,amount);u.hp-=dealt
            if u.hp<=0 and not defer_death:self._kill_batch([target])
            return dealt
        if target and target.startswith('hero:'):
            p=self.players[int(target.split(':')[1])]
            if not ignore_defense:
                if p.hero_shield:p.hero_shield=0;return 0
                a=min(amount,p.hero_armor);p.hero_armor-=a;amount-=a
            old=p.hp;p.hp-=amount
            if not self._suspend_hero_thresholds:
                for threshold in (75,50,25):
                    if old>threshold>=p.hp and threshold not in p.thresholds:
                        p.thresholds.add(threshold);p.coins+=2
                        self._log(f'{p.name}: +2 monety za przekroczenie {threshold} PŻ.')
            return amount
        return 0

    def _ordered_deaths(self,fallen):
        """Porządek v19: najpierw aktywny gracz od lewej, potem drugi."""
        positions={}
        for pid in (self.active,1-self.active):
            for pos,uid in enumerate(self.players[pid].board):
                positions[uid]=(0 if pid==self.active else 1,pos,uid)
        return sorted({uid for uid in fallen if uid in self.units},
                      key=lambda uid:positions.get(uid,(2,999,uid)))

    @trace_effect('_kill_batch')
    def _kill_batch(self,fallen):
        ordered=self._ordered_deaths(fallen)
        if not ordered:return
        # Zbieramy stan wszystkich umierających PRZED usunięciem pierwszej
        # jednostki. Nagrody naliczamy dokładnie raz za fizyczną instancję.
        snapshot=[]
        for uid in ordered:
            unit=self.units[uid]
            blocked=self._disabled(unit)
            self._death_disabled[uid]=blocked
            self._death_levels[uid]=unit.ability_level
            snapshot.append((uid,unit.owner,blocked,
                             self.cards[uid].definition.faction=='Potwory'))
        for uid,owner,_,_ in snapshot:
            self._remove_unit(uid,death=True)
            self.players[1-owner].coins+=1
            self._log(f'Zgon {self.label(uid)}. Przeciwnik właściciela otrzymuje 1 monetę.')
        # Rejestrujemy źródła, ale ich legalne cele zamrażamy dopiero gdy
        # grupa dochodzi na początek kolejki. Wcześniejsza grupa może jeszcze
        # zmienić stan planszy, zwłaszcza po utracie dodatniej aury.
        source_ids=tuple(uid for uid,_,blocked,monster in snapshot
                         if monster and not blocked)
        if source_ids:
            wave={'id':self._next_death_wave_id,'fallen':tuple(ordered),
                  'source_ids':source_ids,'sources':None,
                  'cursor':0,'decisions':[]}
            self._next_death_wave_id+=1
            self.death_waves.append(wave)
            self._log(f'Fala śmierci {wave["id"]}: {len(ordered)} zgonów, '
                      f'{len(source_ids)} zdolności z jednej migawki.')
        # Śmierć od zaniku aury jest następną falą; bieżąca została już
        # zarejestrowana przed przeliczeniem aury.
        self._update_auras()

    @trace_effect('_resolve_death_wave')
    def _resolve_death_wave(self,wave):
        """Jedna faza konsekwencji, po wszystkich wyborach z migawki."""
        self._resolving_death_wave=True
        self._wave_damage=[]
        self._wave_healing=[]
        self._wave_status_ops=[]
        self._wave_defense_ops=[]
        try:
            for uid,choice in wave['decisions']:
                self._execute(uid,'death',choice)
        finally:
            self._resolving_death_wave=False
        # Stosujemy sumę obrażeń i leczenia tej samej fali; pośredni zgon
        # nie blokuje dalszych zdolności. Zużywalne tarcze/pancerz
        # rozdzielane są deterministycznie według kolejności źródeł.
        damage=self._wave_damage
        healing=self._wave_healing
        statuses=self._wave_status_ops
        defenses=self._wave_defense_ops
        self._wave_damage=[]
        self._wave_healing=[]
        self._wave_status_ops=[]
        self._wave_defense_ops=[]
        # Rozstrzygamy operacje oparte na ORYGINALNYCH statusach, a nowe
        # statusy nakładamy dopiero potem. Dwie zdolności oczyszczania
        # korzystają z tej samej migawki, lecz nie usuwają nawzajem
        # efektów przyznanych w tej samej fali.
        for operation in statuses:
            if operation[0]=='clean':
                _,target,negative=operation
                self._clean(target,negative)
        for operation in statuses:
            if operation[0]=='immune':
                _,target,kinds,expires,source=operation
                self._grant_immunity(target,kinds,expires,source)
        for operation in statuses:
            if operation[0]!='add':continue
            (_,target,kind,value,remaining,expires,
             source,positive,bonus_once,expire_action)=operation
            if target not in self.units:continue
            # For poison/stun, legality against prior immunities and
            # self-cleansing was checked while ALL declarations shared the
            # same initial snapshot. A newly granted immunity in this group
            # must not retroactively cancel a simultaneous legal status.
            if kind in ('poison','stun'):
                unit=self.units[target]
                if kind=='stun':
                    stacked=[e.expires or 0 for e in unit.effects if e.kind=='stun']
                    if stacked:expires=max(expires or 0,max(stacked)+1)
                unit.effects.append(Effect(kind,value,remaining,expires,
                                           source,positive,bonus_once,
                                           expire_action,remaining))
                self._log(f'{self.label(target)} otrzymuje {kind} (wspólna fala śmierci).')
            else:
                self._add_effect(target,kind,value,remaining,expires,
                                 source,positive,bonus_once,expire_action)
        # Cała osłona i pancerz fali są przyznane, zanim jakiekolwiek
        # źródło tej fali zada obrażenia.
        for operation in defenses:
            kind,target,amount,source=operation
            if kind=='hero_armor':
                self.players[int(target.split(':')[1])].hero_armor+=amount
            elif kind=='hero_shield':
                self.players[int(target.split(':')[1])].hero_shield=1
            elif target in self.units:
                unit=self.units[target]
                if kind=='shield':
                    unit.shield=1
                    unit.shield_source=source
                elif kind=='armor':
                    unit.armor_perm+=amount
                    unit.armor_perm_source=source
                    unit.armor_perm_grants[source]=unit.armor_perm_grants.get(source,0)+amount
        # Bohaterowie i jednostki dostają zbiorcze konsekwencje przed
        # usunięciem ofiar i weryfikacją wyniku meczu.
        original_hero_hp=[p.hp for p in self.players]
        self._suspend_hero_thresholds=True
        try:
            for target,amount,ignore_defense in damage:
                self._damage(target,amount,ignore_defense=ignore_defense,defer_death=True)
            for target,amount,ability in healing:
                self._heal(target,amount,ability=ability)
        finally:
            self._suspend_hero_thresholds=False
        # Progi bohatera sprawdzamy dla KOŃCOWEGO wyniku wspólnej fali,
        # nie dla przejściowej wartości pomiędzy jednoczesnymi efektami.
        for player,old in zip(self.players,original_hero_hp):
            for threshold in (75,50,25):
                if old>threshold>=player.hp and threshold not in player.thresholds:
                    player.thresholds.add(threshold)
                    player.coins+=2
                    self._log(f'{player.name}: +2 monety za przekroczenie {threshold} PŻ.')
        self._update_auras()
        self._kill_batch([uid for uid,u in list(self.units.items()) if u.hp<=0])
        self._log(f'Zamknięto falę śmierci {wave["id"]}.')
        self._check_winner()

    @trace_effect('_remove_unit')
    def _remove_unit(self,uid,death):
        u=self.units.pop(uid)
        self.players[u.owner].board.remove(uid)
        card=self.cards[uid];card.zone='grave';card.hand_turns=0;card.quick_next_turn=None
        card.quick_on_first_summon=False;card.double_on_first_eligible=False
        self.players[u.owner].grave.append(uid)

    def _update_auras(self,defer_reactive=False):
        # Dynamic auras S34 / S35 / S105. Unit order is always compacted left.
        if not self.units:return
        desired_atk={x:0 for x in self.units};desired_hp={x:0 for x in self.units};armor_sources={x:set() for x in self.units}
        for uid,u in list(self.units.items()):
            if self._disabled(u):continue
            cid=self.cards[uid].definition.id
            friend=self.players[u.owner].board;enemy=self.players[1-u.owner].board
            if cid=='S34':
                position=friend.index(uid)
                value=1+u.ability_level
                if u.aura_mode=='ally':
                    if len(friend)>1:
                        t=friend[position+1] if position+1<len(friend) else friend[position-1]
                        desired_atk[t]+=value
                elif position<len(enemy):desired_atk[enemy[position]]-=value
            elif cid=='S35':
                value=1+u.ability_level
                for x in (friend if u.aura_mode=='ally' else enemy):
                    if x!=uid:desired_hp[x]+=value if u.aura_mode=='ally' else -value
            elif cid=='S105':
                for x in friend:
                    if x!=uid:armor_sources[x].add(uid)
        for uid,u in list(self.units.items()):
            old=u.max_hp
            previous_aura_hp=u.aura_hp
            u.aura_atk=desired_atk[uid];u.aura_hp=desired_hp[uid]
            delta=u.max_hp-old
            if delta>0 and desired_hp[uid]>0:
                # Strengthening a positive aura grants the same amount of current HP.
                u.hp+=delta
            elif delta<0 and previous_aura_hp>0:
                # Losing a positive MAX HP aura removes the corresponding current HP.
                u.hp+=delta
            u.hp=min(u.hp,u.max_hp)
            for src in list(u.aura_armor):
                if src not in armor_sources[uid]:del u.aura_armor[src]
            for src in armor_sources[uid]:
                if src not in u.aura_armor:u.aura_armor[src]=2+self.units[src].ability_level
        # S108: on first facing a new opponent. Deferred during PLAY_CARD
        # so ON_PLAY resolves before newly generated reactive passives.
        if not defer_reactive and not self._resolving_death_wave:
            self._apply_position_reactions()
        if not self._resolving_death_wave:
            dead=[uid for uid,u in list(self.units.items()) if u.hp<=0]
            if dead:self._kill_batch(dead)

    def _apply_position_reactions(self):
        for uid,u in list(self.units.items()):
            if self.cards[uid].definition.id!='S108' or self._disabled(u):continue
            own=self.players[u.owner].board;enemy=self.players[1-u.owner].board
            i=own.index(uid)
            if i<len(enemy) and enemy[i] not in u.seen_opponents:
                opp=enemy[i];u.seen_opponents.add(opp)
                applied=self._add_effect(opp,'stun',expires=self._expiry(self.units[opp].owner),source=uid,positive=False)
                if applied and u.ability_level and opp in self.units:
                    self._damage(opp,u.ability_level)
        # Lethal outcomes of these reactions are resolved in the caller.


    def _check_winner(self):
        if self.phase!='turn':return
        a,b=self.players
        if a.hp>0 and b.hp>0:return
        if a.hp<=0 and b.hp>0:self.winner=1
        elif b.hp<=0 and a.hp>0:self.winner=0
        else:
            # Tie breaker: hero HP; hand+deck; strongest board ATK+HP; second player.
            for metric in (lambda p:p.hp,lambda p:len(p.hand)+len(p.deck),
                           lambda p:max([self.units[x].atk+self.units[x].hp for x in p.board] or [0])):
                va,vb=metric(a),metric(b)
                if va!=vb:
                    self.winner=0 if va>vb else 1;break
            else:self.winner=1-self.first
        self.phase='finished';self.pending=None
        self._log(f'KONIEC MECZU! Zwycięzca: {self.players[self.winner].name}.')

    @audit_action('auction_bid')
    def auction_bid(self,player,amount):
        auction_rules.bid(self,player,amount)

    @audit_action('auction_pass')
    def auction_pass(self,player):
        auction_rules.pass_bid(self,player)

    @audit_action('auction_pick')
    def auction_pick(self,player,uid):
        auction_rules.pick(self,player,uid)

    def assert_integrity(self):
        all_ids=list(self.bank)
        for p in self.players:all_ids+=p.hand+p.deck+p.grave+p.board
        all_ids+=self.excluded
        basic=[uid for uid in all_ids if uid not in self.auction_awards]
        assert len(basic)==70 and len(set(basic))==70,('Bank 70x1 violated',len(basic),len(set(basic)))
        assert len(all_ids)==len(set(all_ids)), 'Auction card duplicated'
        assert set(all_ids)==set(self.cards),('Physical cards mismatch',len(all_ids),len(self.cards))
        assert all(uid not in self.bank and uid not in self.excluded for uid in self.auction_awards)
        for p in self.players:
            assert len(p.board)<=5 and all(self.cards[x].owner==p.idx for x in p.hand+p.deck+p.grave+p.board)
        assert set(self.units)==set(self.players[0].board+self.players[1].board)
        assert all(self.cards[x].zone=='excluded' and self.cards[x].owner is None for x in self.excluded)

    @trace_effect('_execute')
    def _execute(self,uid,context,choice,attacked=None):
        """Katalog 70 kart: parametry, warianty, cele i wszystkie wyjątki aktualnego katalogu v19.

        Dla efektów wymagających wyboru pending zatrzymuje kolejkę, co pozwala
        obsłużyć zarówno gracza jak i agenta tym samym kodem.
        """
        card=self.cards[uid]
        cid=card.definition.id
        owner=card.owner
        level=(self.units[uid].ability_level if uid in self.units else self._death_levels.get(uid,0))
        target=choice.target
        mode=choice.mode
        here=self.units.get(uid)
        def mod(t,kind,val,positive=None,expires=None,action=False):
            if t not in self.units:return
            self._add_effect(t,kind,val,expires=expires,source=uid,
                             positive=(val>0 if positive is None else positive),
                             expire_action=(self.action_turn if action else None))
        def arm(t,val,temporary=False,expires=None):
            if self._resolving_death_wave:
                if t in self.units:
                    self._wave_defense_ops.append(('armor',t,val,uid))
                return
            if t in self.units:
                if temporary:
                    self.units[t].armor_temp+=val
                    self.units[t].armor_temp_source=uid
                    if expires is not None:
                        # Source-tagged temp armor expires independently, via aura_armor.
                        self.units[t].armor_temp-=val
                        self.units[t].temporary_armor[f'{uid}@{self.serial}']=val
                        self.serial+=1
                        # A timed armor source is represented by a zero-value effect.
                        self._add_effect(t,'temp_armor_marker',expires=expires,source=f'{uid}@{self.serial-1}')
                else:
                    self.units[t].armor_perm+=val
                    self.units[t].armor_perm_source=uid
                    ledger=self.units[t].armor_perm_grants
                    ledger[uid]=ledger.get(uid,0)+val
        def regen(t,val,ticks,bonus=0):
            self._add_effect(t,'regen',val,ticks,source=uid,bonus_once=bonus)
        def immune(t,kinds,expires=None):
            self._grant_immunity(t,kinds,expires=expires,source=uid)
            if level and here and 'immune_bonus' not in here.passives_triggered:
                arm(t,level);here.passives_triggered.add('immune_bonus')
            elif level and context=='death':
                # The dead source has no Unit instance, but its first (and only)
                # successful immunity activation still awards the quality bonus.
                arm(t,level)
        next_end=lambda t:self._expiry(self.units[t].owner) if t in self.units else None
        # Elfy
        if cid=='S01':self._damage(target,3+level)
        elif cid=='S02':self._heal(target,4+level)
        elif cid=='S04':mod(target,'atk',(1+level) if mode=='Wzmocnij' else -(1+level))
        elif cid=='S08':mod(target,'max_hp',(4+level) if mode=='Wzmocnij' else -(4+level))
        elif cid=='S03':arm(target,4+level)
        elif cid=='S05':
            if target in self.units:
                self.units[target].shield=1
                self.units[target].shield_source=uid
            arm(target,1)
        elif cid=='S58':self._add_poison(target,2,2,uid,level)
        elif cid=='S59':
            applied = (self._add_effect(target,'stun',expires=next_end(target),source=uid,positive=False)
                       if target in self.units else False)
            self._damage(target,1+(level if applied else 0))
        elif cid=='S60':regen(target,3,2,level)
        elif cid=='S61':mod(target,'taunt',0,True)
        elif cid=='S07':
            useful=self._clean(target,negative=(mode=='Oczyść własną'))
            if mode=='Oczyść własną':self._heal(target,1+(level if useful else 0))
            elif useful:self._damage(target,level)
        elif cid=='S64':immune(target,('poison',))
        elif cid=='S66':
            if mode=='self_quick' and target==uid and uid in self.units:
                self._add_effect(uid,'quick',source=uid)
            elif mode=='hand_quick' and target in self.players[owner].hand and target!=uid:
                self.cards[target].quick_on_first_summon=True
        elif cid=='S67':
            if target in self.players[owner].board and target in self.units:
                self._add_effect(target,'double',source=uid)
        # Dzikie bestie
        elif cid=='S09':self._damage(attacked,1+level)
        elif cid=='S10':self._heal(uid,2+level)
        elif cid=='S68':mod(uid if mode=='Wzmocnij siebie' else attacked,'atk',(1+level) if mode=='Wzmocnij siebie' else -(1+level),action=True)
        elif cid=='S69':
            if mode=='Wzmocnij siebie':mod(uid,'max_hp',1+level)
            else:mod(attacked,'max_hp',-(1+level),expires=next_end(attacked))
        elif cid=='S12':
            if attacked in self.units:
                t=self.units[attacked];remove=2+level
                # The armor stripping ability follows the same layer order as
                # ordinary damage: temporary (including source-tagged parts),
                # then passive aura armor, then permanent armor.
                n=min(t.armor_temp,remove);t.armor_temp-=n;remove-=n
                if not t.armor_temp:t.armor_temp_source=''
                for k in list(t.temporary_armor):
                    n=min(t.temporary_armor[k],remove)
                    t.temporary_armor[k]-=n;remove-=n
                for k in list(t.aura_armor):
                    n=min(t.aura_armor[k],remove)
                    t.aura_armor[k]-=n;remove-=n
                self._spend_permanent_armor(t,remove)
        elif cid=='S70':
            if here:here.shield=1;here.shield_source=uid
        elif cid=='S11':self._add_poison(attacked,1,2,uid,level)
        elif cid=='S15':
            if attacked in self.units:
                applied=self._add_effect(attacked,'stun',expires=next_end(attacked),source=uid,positive=False)
                if applied and level:self._damage(attacked,level)
        elif cid=='S71':regen(uid,1,2,level)
        elif cid=='S72':mod(uid,'taunt',0,True,expires=self.players[owner].turn_count+1)
        elif cid=='S74':
            if self._clean(attacked,negative=False) and level:self._damage(attacked,level)
        elif cid=='S76':immune(uid,('stun',),expires=self.players[owner].turn_count+1)
        elif cid=='S78':
            if target in self.units:mod(target,'quick',0,True,expires=self.players[owner].turn_count)
        elif cid=='S79':pass  # two attacks, checked in _double
        # Potwory
        elif cid=='S21':self._damage(f'hero:{1-owner}',4+level)
        elif cid=='S17':self._heal(f'hero:{owner}',6+level)
        elif cid=='S23':mod(target,'atk',(2+level) if mode=='Wzmocnij' else -(2+level))
        elif cid=='S81':mod(target,'max_hp',(5+level) if mode=='Wzmocnij' else -(5+level))
        elif cid=='S82':
            if target==f'hero:{owner}':
                if self._resolving_death_wave:
                    self._wave_defense_ops.append(('hero_armor',target,6+level,uid))
                else:self.players[owner].hero_armor+=6+level
            else:arm(target,6+level)
        elif cid=='S20':
            if target==f'hero:{owner}':
                if self._resolving_death_wave:
                    self._wave_defense_ops.append(('hero_shield',target,1,uid))
                    self._wave_defense_ops.append(('hero_armor',target,2,uid))
                else:
                    self.players[owner].hero_shield=1
                    self.players[owner].hero_armor+=2
            elif target in self.units:
                if self._resolving_death_wave:
                    self._wave_defense_ops.append(('shield',target,1,uid))
                else:
                    self.units[target].shield=1
                    self.units[target].shield_source=uid
                arm(target,2)
        elif cid=='S83':self._add_poison(target,2,3,uid,level)
        elif cid=='S84':
            applied = (self._add_effect(target,'stun',expires=next_end(target),source=uid,positive=False)
                       if target in self.units else False)
            self._damage(target,2+(level if applied else 0))
        elif cid=='S85':regen(target,3,3,level)
        elif cid=='S86':mod(target,'taunt',0,True)
        elif cid=='S87':
            useful=self._clean(target,True);arm(target,2)
            if useful and level:self._heal(target,level)
        elif cid=='S88':immune(target,('poison','stun'))
        elif cid=='S90':
            available=sorted(self.players[owner].hand)  # migawka fizycznych identyfikatorów
            chosen=self.rng.sample(available,min(2,len(available)))
            if chosen:
                self.rng_draw_index+=1
                self._log(f'Losowanie S90 #{self.rng_draw_index}: źródło {uid}, '
                          f'kandydaci {available}, wybrano {chosen}.')
            for hand_uid in chosen:
                self.cards[hand_uid].quick_on_first_summon=True
                self._log(f'{self.label(hand_uid)} otrzymuje Szybki atak na najbliższe wystawienie (S90).')
        elif cid=='S91':
            if target in self.units:
                mod(target,'double',0,True)
            elif self.players[owner].hand:
                available=sorted(self.players[owner].hand)
                hand_uid=self.rng.choice(available)
                self.rng_draw_index+=1
                self._log(f'Losowanie S91 #{self.rng_draw_index}: źródło {uid}, '
                          f'kandydaci {available}, wybrano {[hand_uid]}.')
                self.cards[hand_uid].double_on_first_eligible=True
                self._log(f'{self.label(hand_uid)} otrzymuje Podwójny atak na pierwszą legalną turę (S91).')
        # Krasnoludy
        elif cid=='S27':
            enemy=self.players[1-owner].board
            if enemy:
                t=min(enemy,key=lambda x:(self.units[x].hp,enemy.index(x)))
                self._damage(t,1+level)
        elif cid=='S25':self._heal(target,2+level)
        elif cid=='S28':mod(target,'atk',(1+level) if mode=='Wzmocnij' else -(1+level),expires=next_end(target))
        elif cid=='S93':mod(target,'max_hp',(1+level) if mode=='Wzmocnij' else -(1+level),expires=next_end(target))
        elif cid=='S26':arm(target,2+level,True,expires=next_end(target))
        elif cid=='S94':
            if target in self.units:
                self.units[target].shield=1
                self.units[target].shield_source=uid
        elif cid=='S32':self._add_poison(target,1,2,uid,level)
        elif cid=='S95':
            enemy=self.players[1-owner].board
            pool=[x for x in enemy if not(here and here.last_stun_target==x and here.last_stun_turn==self.players[owner].turn_count-1)]
            if pool:
                t=min(pool,key=lambda x:(self.units[x].atk,enemy.index(x)))
                applied=self._add_effect(t,'stun',expires=next_end(t),source=uid,positive=False)
                if applied:
                    if level:self._damage(t,level)
                    if here:here.last_stun_target=t;here.last_stun_turn=self.players[owner].turn_count
        elif cid=='S31':regen(target,1,2,level)
        elif cid=='S96':mod(target,'taunt',0,True,expires=next_end(target))
        elif cid=='S97':
            if self._clean(target,True) and level:self._heal(target,level)
        elif cid=='S99':immune(target,('poison',),expires=next_end(target))
        elif cid=='S101':
            if target in self.players[owner].hand:
                self.cards[target].quick_next_turn=self.players[owner].turn_count+1
        elif cid=='S102':mod(target,'double',0,True,expires=self.players[owner].turn_count+1)
        # Ludzie
        elif cid in ('S34','S35'):
            if here:
                here.aura_mode=mode
                self._update_auras()
        elif cid in ('S103','S104','S105','S106','S107','S108','S109','S33','S111','S39','S114','S115'):
            pass  # ongoing triggers handled by combat/turn/aura/status layers
        else:
            raise AssertionError('Missing ability handler for: '+cid)
        self.position_reactions_due=False
        if not self._resolving_death_wave:
            self._update_auras()

