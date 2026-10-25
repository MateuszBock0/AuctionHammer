"""Animacje wyłącznie odczytujące autorytatywny stan Game Master v19.

Nie przewidujemy wyników ataku i nie wywołujemy metod mutujących Match:
obrażenia, leczenie, tarcze, zatrucia, bonusy i zgony są wykrywane z różnicy
dwóch ZATWIERDZONYCH stanów. Ruch ataku z zatwierdzonego dziennika zdarzeń.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sin, cos, pi
import copy
import re
import pygame

from game.core.status_view import active_statuses
from game.ui.combat_outcome import committed_attack_outcome

KINDS = {
    'damage':((255,121,125),'-'),
    'heal':((115,238,168),'+'),
    'poison':((194,231,89),'TRUC'),
    'shield':((255,210,64),'TARCZA'),
    'armor':((186,208,242),'PANC'),
    'death':((250,190,117),'ZGON'),
    'attack':((255,202,127),'ATAK'),
    'special':((198,152,245),'EFEKT'),
    'stun':((198,152,245),'OGŁ'),
    'regen':((104,242,189),'REGEN'),
    'quick':((103,225,242),'SZYBKI'),
    'double':((227,69,78),'2×'),
    'summon':((224,186,103),'WEJŚCIE'),
    'turn':((208,171,102),''),
}


@dataclass(frozen=True)
class Pulse:
    kind: str
    at: tuple[int,int]
    born: int
    label: str = ''
    origin: tuple[int,int] | None = None
    lifetime: int = 840
    lane: int = 0  # Separate simultaneous HP / shield / armor callouts.


@dataclass(frozen=True)
class CombatCard:
    """Read-only, short-lived picture of a committed combatant."""
    uid: str
    rect: pygame.Rect
    old_hp: int
    new_hp: int
    born: int
    dead: bool = False
    unit: object = None
    statuses: tuple = ()
    lifetime: int = 440


class CombatVisuals:
    """Ostatnie wizualizacje; FIFO z ograniczoną pamięcią, bez zmian gry."""

    def __init__(self, max_pulses: int = 56):
        self.max_pulses = max_pulses
        self.last_state = None
        self.read_events = 0
        self.last_active = None
        self.pulses: list[Pulse] = []
        self.combat_cards: dict[str,CombatCard] = {}
        self.fallen_cards: list[CombatCard] = []
        self.last_attack_outcome = None
        self.impacts: dict[str,tuple[int,int]] = {}
        self._attack_start_state = None
        self._attack_start_event = 0

    @staticmethod
    def _anchor(rect: pygame.Rect) -> tuple[int,int]:
        # Dolne płytki ATAK / PŻ są nietykalne: środek nad obszarem ilustracji.
        return rect.centerx, rect.y + min(88, max(30,rect.height//3))

    def _snapshot(self, game, unit_rect, hero_rect):
        state = {}
        for owner, player in enumerate(game.players):
            rect = hero_rect(owner)
            state[f'hero:{owner}'] = {
                'hp':player.hp,'shield':player.hero_shield,
                'armor':player.hero_armor,'status':frozenset(),
                'at':(rect.centerx,rect.centery),'attacks':0,
            }
            for uid in player.board:
                slot=game.slot_of(uid)
                if uid not in game.units:
                    continue
                unit=game.units[uid]
                position=self._anchor(unit_rect(owner,slot))
                effects=frozenset(e.kind for e in unit.effects)
                state[uid] = {
                    'hp':unit.hp,'shield':unit.shield,'armor':unit.armor,
                    'status':effects,'at':position,'attacks':unit.attacks,
                    'rect':unit_rect(owner,slot).copy(),
                    'unit':copy.deepcopy(unit),
                    'statuses':tuple(active_statuses(game,uid)),
                }
        return state

    def _push(self,kind,at,now,label='',origin=None,delay_ms=0):
        # Distinguish simultaneously committed HP, shield and armor changes.
        # An impact projectile is not a label and does not consume a lane.
        labelled=('damage','heal','shield','armor','death')
        lane=0
        if kind in labelled:
            lane=sum(
                1 for p in self.pulses
                if p.kind in labelled and p.at==at
                and abs(p.born-(int(now)+delay_ms))<250
            )%3
        self.pulses.append(Pulse(kind,at,int(now)+delay_ms,str(label),
                                 origin,lane=lane))
        if len(self.pulses)>self.max_pulses:
            del self.pulses[:-self.max_pulses]

    def shake_offset(self,uid: str,now: int) -> tuple[int,int]:
        """Brief deterministic UI-only nudge after a real resolved impact."""
        impact=self.impacts.get(uid)
        if impact is None:
            return (0,0)
        born,strength=impact
        age=now-born
        if age<0 or age>=220:
            return (0,0)
        frame=min(4,age//44)
        dx,dy=((4,0),(-3,1),(2,-1),(-1,0),(0,0))[frame]
        return (round(dx*strength/4),round(dy*strength/4))

    def sync(self,game,unit_rect,hero_rect,now: int):
        """Pobierz zatwierdzony stan po wykonaniu komend przez silnik."""
        current=self._snapshot(game,unit_rect,hero_rect)
        prior=self.last_state
        self.last_state=current
        journal=getattr(game,'event_journal',[])
        start_event=self.read_events
        fresh=journal[start_event:]
        self.read_events=len(journal)
        if prior is None:
            self.last_active=game.active
            return
        # The engine may suspend an attack until a mandatory ability/death
        # choice is resolved. An "atakuje" journal line is NOT evidence that
        # its damage or retaliation is final.
        if any(' atakuje: ' in evt['text'] for evt in fresh):
            if self._attack_start_state is None:
                self._attack_start_state=prior
                self._attack_start_event=start_event
        attack_events=[]
        committed_attack_start=None
        unresolved=(getattr(game,'pending',None) is not None
                    or getattr(game,'deferred_attack',None) is not None
                    or bool(getattr(game,'trigger_queue',()))
                    or bool(getattr(game,'death_waves',()))
                    or getattr(game,'active_death_wave',None) is not None)
        self.last_attack_outcome=None
        if self._attack_start_state is not None and not unresolved:
            committed_attack_start=self._attack_start_state
            attack_events=journal[self._attack_start_event:]
            self.last_attack_outcome=committed_attack_outcome(
                game,committed_attack_start,current,attack_events,len(journal))
            self._attack_start_state=None
        attack_confirmed = self.last_attack_outcome is not None
        impact_delay = 165 if attack_confirmed else 0
        # Auras/entrances operate on confirmed board occupancy only.
        for uid,data in current.items():
            if uid not in prior and not uid.startswith('hero:'):
                self._push('summon',data['at'],now,'')
        if game.active != self.last_active:
            self.last_active=game.active
            self._push('turn',current[f'hero:{game.active}']['at'],now,'')
        # Keep a short read-only picture of BOTH combatants, so the player
        # can follow their HP changing and see the fallen card turn grey.
        fighting=set()
        confirmed_deaths=set()
        for uid,old in prior.items():
            if uid.startswith('hero:') or uid in current:
                continue
            if any(evt['text'].startswith(f'Zgon {game.label(uid)}.')
                   for evt in fresh):
                confirmed_deaths.add(uid)
        # Przy walce oba końce są znane nawet wtedy, gdy atakujący już zginął.
        for evt in attack_events:
            message=evt['text']
            if ' atakuje: ' in message:
                actor,target=message.split(' atakuje: ',1)
                target=target.rstrip('.')
                before=committed_attack_start or prior
                src=next((cid for cid in before if cid in game.cards
                          and game.cards[cid].definition.name==actor),None)
                dst=next((cid for cid in current if cid in game.cards
                          and game.cards[cid].definition.name==target),None)
                if dst is None:
                    dst=next((cid for cid in before if cid in game.cards
                              and game.cards[cid].definition.name==target),None)
                if target.startswith('Bohater'):
                    dst=next((f'hero:{i}' for i,p in enumerate(game.players)
                              if p.name in target),None)
                if src and dst:
                    start=(before.get(src) or current.get(src) or {}).get('at')
                    end=(current.get(dst) or before.get(dst) or {}).get('at')
                    if start and end:
                        self._push('attack',end,now,origin=start)
                        fighting.update((src,dst))
        for uid in fighting | confirmed_deaths:
            old=prior.get(uid)
            if not old or uid.startswith('hero:'):
                continue
            latest=current.get(uid)
            dead=uid in confirmed_deaths
            new_hp=max(0,latest['hp']) if latest else 0
            transition=CombatCard(
                uid,old['rect'],max(0,old['hp']),new_hp,int(now),
                dead=dead,unit=old['unit'],statuses=old['statuses'])
            if dead:
                self.fallen_cards.append(transition)
                self.fallen_cards=self.fallen_cards[-12:]
                self.combat_cards.pop(uid,None)
            elif latest is not None:
                self.combat_cards[uid]=transition
        for uid,old in prior.items():
            if uid not in current:
                if uid in confirmed_deaths:
                    self._push('death',old['at'],now,'ZGON',delay_ms=impact_delay)
                continue
            new=current[uid]
            delta=new['hp']-old['hp']
            if delta<0:
                self._push('damage',new['at'],now,f'-{abs(delta)} PŻ',
                           delay_ms=impact_delay)
            if delta>0:
                self._push('heal',new['at'],now,f'+{delta} PŻ',
                           delay_ms=impact_delay)
            if (delta<0 or new['shield']<old['shield']
                    or new['armor']<old['armor']) and not uid.startswith('hero:'):
                strength=4 if delta<0 else 2
                self.impacts[uid]=(int(now)+impact_delay,strength)
            if new['shield']<old['shield']:
                # A blocked hit may deal zero HP damage. Show the actual
                # consumed protection instead of falsely reporting a wound.
                self._push('shield',new['at'],now,
                           f'TARCZA -{old["shield"]-new["shield"]}',
                           delay_ms=impact_delay)
            if new['shield']>old['shield']:
                self._push('shield',new['at'],now,
                           f'TARCZA +{new["shield"]-old["shield"]}')
            if new['armor']<old['armor']:
                self._push('armor',new['at'],now,
                           f'PANC. -{old["armor"]-new["armor"]}',
                           delay_ms=impact_delay)
            if new['armor']>old['armor']:
                self._push('armor',new['at'],now,
                           f'PANC. +{new["armor"]-old["armor"]}')
            for kind in sorted(new['status']-old['status']):
                mapped={'poison':'poison','stun':'stun','regen':'regen',
                        'quick':'quick','double':'double'}.get(kind,'special')
                self._push(mapped,new['at'],now)
        self.pulses=[p for p in self.pulses if now-p.born < p.lifetime]
        self.combat_cards={uid:card for uid,card in self.combat_cards.items()
                           if now-card.born < card.lifetime}
        self.fallen_cards=[card for card in self.fallen_cards
                           if now-card.born < card.lifetime]
        self.impacts={uid:data for uid,data in self.impacts.items()
                      if now-data[0]<220}

    @staticmethod
    def interpolated_hp(card: CombatCard,now: int):
        """HP decreases first; only afterwards does the losing card grey out."""
        age=max(0,now-card.born)
        t=min(1.0,max(0.0,(age-120)/115.0))
        return max(0,round(card.old_hp+(card.new_hp-card.old_hp)*t))

    def hp_display(self,uid,now):
        card=self.combat_cards.get(uid)
        if card is None or not card.old_hp>card.new_hp:
            return None
        if now-card.born >= card.lifetime:
            return None
        return self.interpolated_hp(card,now)

    def _combat_outline(self,screen,rect,age):
        """Short highlight around both participants, without covering stats."""
        if age<0 or age>=430:return
        opacity=max(0,int(210*(1-age/430)))
        # Eight hard-edged 2px strokes, never a rounded glowing halo.
        # Draw only outside the card so ATK/HP plates stay legible.
        halo=pygame.Surface((rect.w+14,rect.h+14),pygame.SRCALPHA)
        color=(255,217,125,opacity)
        left,top=5,5
        right,bottom=rect.w+8,rect.h+8
        for x,dx in ((left,1),(right,-1)):
            for y,dy in ((top,1),(bottom,-1)):
                pygame.draw.line(halo,color,(x,y),(x+dx*14,y),2)
                pygame.draw.line(halo,color,(x,y),(x,y+dy*14),2)
        screen.blit(halo,(rect.x-7,rect.y-7))

    def draw_cards(self,screen,game,card_view,now):
        """Overlay combat feedback only: no changes to Match or board state."""
        for uid,card in self.combat_cards.items():
            if uid in game.units:
                self._combat_outline(screen,card.rect,now-card.born)
        for card in self.fallen_cards:
            age=now-card.born
            if not 0<=age<card.lifetime or card.uid not in game.cards:
                continue
            # Render the actual former unit to a local surface (never an
            # invented new card). Numbers fall to zero before desaturation.
            render=pygame.Surface(card.rect.size,pygame.SRCALPHA)
            local=pygame.Rect(0,0,*card.rect.size)
            card_view.draw(render,game.cards[card.uid],local,card.unit,
                           statuses=card.statuses,
                           hp_override=self.interpolated_hp(card,now))
            self._combat_outline(screen,card.rect,age)
            grey_factor=min(1.0,max(0.0,(age-220)/145))
            if grey_factor>0:
                grey=pygame.transform.grayscale(render)
                grey.set_alpha(int(255*grey_factor))
                render.blit(grey,(0,0))
            if age>355:
                render.set_alpha(max(0,int(255*(card.lifetime-age)/85)))
            screen.blit(render,card.rect.topleft)

    def draw(self,screen: pygame.Surface,now: int,font: pygame.font.Font):
        """Eased projectiles, impact particles, floating text and status rings.

        Effects are cosmetic, short-lived, capped, and avoid card stat plates.
        """
        alive=[]
        for pulse in self.pulses:
            age=now-pulse.born
            if age<0:
                # A delayed impact must survive earlier animation frames.
                alive.append(pulse)
                continue
            if age>=pulse.lifetime:
                continue
            alive.append(pulse)
            t=age/pulse.lifetime
            color,title=KINDS[pulse.kind]
            alpha=max(0,int(230*(1-t)**1.2))
            x,y=pulse.at
            if pulse.kind=='attack' and pulse.origin is not None:
                travel=min(1.,t*4.8)
                eased=1-(1-travel)**3
                x=pulse.origin[0]+(pulse.at[0]-pulse.origin[0])*eased
                y=pulse.origin[1]+(pulse.at[1]-pulse.origin[1])*eased
                radius=4+int(7*(1-travel))
                # Crisp 8-bit projectile: a compact square with a stepped
                # border and four small rectangular trail fragments.
                # No radial gradient, circles, blur or smooth scaling.
                glow=pygame.Surface((60,60),pygame.SRCALPHA)
                pygame.draw.rect(glow,(*color,max(0,int(alpha*.24))),
                                 (30-radius-3,30-radius-3,
                                  2*radius+6,2*radius+6),2)
                pygame.draw.rect(glow,(*color,alpha),
                                 (30-radius//2,30-radius//2,
                                  max(2,radius),max(2,radius)))
                for i in range(4):
                    u=max(0.,eased-(i+1)*.055)
                    tx=pulse.origin[0]+(pulse.at[0]-pulse.origin[0])*u
                    ty=pulse.origin[1]+(pulse.at[1]-pulse.origin[1])*u
                    size=max(2,6-i)
                    pygame.draw.rect(screen,
                                     tuple(int(c*(.53+.11*i)) for c in color),
                                     (int(tx)-size//2,int(ty)-size//2,
                                      size,size))
                screen.blit(glow,(int(x)-30,int(y)-30))
                continue
            if pulse.kind=='turn':
                radius=15+int(25*t)
                fx=pygame.Surface((radius*2+8,radius*2+8),pygame.SRCALPHA)
                pygame.draw.circle(fx,(*color,int(alpha*.48)),
                                   (radius+4,radius+4),radius,2)
                screen.blit(fx,(int(x)-radius-4,int(y)-radius-4))
                continue
            rise=14+int(32*(1-(1-t)**2))
            y-=rise
            # Distinct anchored lanes prevent a simultaneous hit and shield
            # absorption from painting their numbers directly over each other.
            y+=pulse.lane*26
            radius=11+int(24*t)
            fx=pygame.Surface((radius*2+18,radius*2+18),pygame.SRCALPHA)
            center=(radius+9,radius+9)
            if pulse.kind in ('shield','armor','summon'):
                pygame.draw.circle(fx,(*color,int(alpha*.7)),center,radius,2)
                for k in range(6):
                    a=2*pi*k/6 + t
                    pygame.draw.circle(fx,(*color,int(alpha*.83)),
                                       (int(center[0]+cos(a)*radius),
                                        int(center[1]+sin(a)*radius)),2)
            elif pulse.kind=='death':
                for i in range(11):
                    angle=2*pi*i/11
                    length=radius*(.33+.62*t)
                    pygame.draw.circle(fx,(*color,alpha),
                                       (int(center[0]+cos(angle)*length),
                                        int(center[1]+sin(angle)*length)),
                                       2+((i+1)%3))
            elif pulse.kind=='damage':
                pygame.draw.circle(fx,(*color,int(alpha*.25)),center,radius,2)
                for k in range(7):
                    angle=2*pi*k/7
                    distance=radius*(.4+.55*t)
                    px=int(center[0]+cos(angle)*distance)
                    py=int(center[1]+sin(angle)*distance)
                    pygame.draw.circle(fx,(*color,int(alpha*.88)),
                                       (px,py),max(1,int(3*(1-t))))
            elif pulse.kind=='heal':
                pygame.draw.circle(fx,(*color,int(alpha*.15)),center,radius)
                for k in range(5):
                    angle=2*pi*k/5+t*1.6
                    px=int(center[0]+cos(angle)*radius*.65)
                    py=int(center[1]+sin(angle)*radius*.65)
                    pygame.draw.circle(fx,(*color,int(alpha*.78)),
                                       (px,py),max(1,int(3*(1-t))))
            else:
                pygame.draw.circle(fx,(*color,int(alpha*.17)),center,radius)
                pygame.draw.circle(fx,(*color,int(alpha*.38)),center,
                                   max(2,radius-4),2)
            screen.blit(fx,(int(x)-radius-9,int(y)-radius-9))
            label=pulse.label or title
            if not label:
                continue
            message=font.render(label,True,color)
            if message.get_width()>104:
                continue
            # Contrast-protected floating value: transparent framed bubble
            # over busy card pixel art, respecting canvas bounds.
            bubble=pygame.Surface((message.get_width()+14,
                                   message.get_height()+8),pygame.SRCALPHA)
            bg_alpha=min(205,int(alpha*.88))
            pygame.draw.rect(bubble,(12,23,30,bg_alpha),
                             bubble.get_rect(),border_radius=6)
            pygame.draw.rect(bubble,(*color,int(alpha*.8)),
                             bubble.get_rect(),1,border_radius=6)
            message.set_alpha(alpha)
            bubble.blit(message,(7,4))
            bx=max(4,min(screen.get_width()-bubble.get_width()-4,
                         int(x)-bubble.get_width()//2))
            by=max(4,min(screen.get_height()-bubble.get_height()-4,
                         int(y)-bubble.get_height()//2))
            screen.blit(bubble,(bx,by))
        self.pulses=alive
