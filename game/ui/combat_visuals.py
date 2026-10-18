"""Animacje wyłącznie odczytujące autorytatywny stan Game Master v19.

Nie przewidujemy wyników ataku i nie wywołujemy metod mutujących Match:
obrażenia, leczenie, tarcze, zatrucia, bonusy i zgony są wykrywane z różnicy
dwóch ZATWIERDZONYCH stanów. Ruch ataku z zatwierdzonego dziennika zdarzeń.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sin, cos, pi
import re
import pygame

KINDS = {
    'damage':((255,121,125),'-'),
    'heal':((115,238,168),'+'),
    'poison':((194,231,89),'TRUC'),
    'shield':((112,213,255),'TARCZA'),
    'armor':((186,208,242),'PANC'),
    'death':((250,190,117),'ZGON'),
    'attack':((255,202,127),'ATAK'),
    'special':((198,152,245),'EFEKT'),
    'stun':((198,152,245),'OGŁ'),
    'regen':((104,242,189),'REGEN'),
    'quick':((103,225,242),'SZYBKI'),
    'double':((255,166,106),'2×'),
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


class CombatVisuals:
    """Ostatnie wizualizacje; FIFO z ograniczoną pamięcią, bez zmian gry."""

    def __init__(self, max_pulses: int = 56):
        self.max_pulses = max_pulses
        self.last_state = None
        self.read_events = 0
        self.last_active = None
        self.pulses: list[Pulse] = []

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
            for slot,uid in enumerate(player.board):
                if uid not in game.units:
                    continue
                unit=game.units[uid]
                position=self._anchor(unit_rect(owner,slot))
                effects=frozenset(e.kind for e in unit.effects)
                state[uid] = {
                    'hp':unit.hp,'shield':unit.shield,'armor':unit.armor,
                    'status':effects,'at':position,'attacks':unit.attacks,
                }
        return state

    def _push(self,kind,at,now,label='',origin=None):
        self.pulses.append(Pulse(kind,at,int(now),str(label),origin))
        if len(self.pulses)>self.max_pulses:
            del self.pulses[:-self.max_pulses]

    def sync(self,game,unit_rect,hero_rect,now: int):
        """Pobierz zatwierdzony stan po wykonaniu komend przez silnik."""
        current=self._snapshot(game,unit_rect,hero_rect)
        prior=self.last_state
        self.last_state=current
        journal=getattr(game,'event_journal',[])
        fresh=journal[self.read_events:]
        self.read_events=len(journal)
        if prior is None:
            self.last_active=game.active
            return
        # Auras/entrances operate on confirmed board occupancy only.
        for uid,data in current.items():
            if uid not in prior and not uid.startswith('hero:'):
                self._push('summon',data['at'],now,'')
        if game.active != self.last_active:
            self.last_active=game.active
            self._push('turn',current[f'hero:{game.active}']['at'],now,'')
        # Przy walce oba końce są znane nawet wtedy, gdy atakujący już zginął.
        for evt in fresh:
            message=evt['text']
            if ' atakuje: ' in message:
                actor,target=message.split(' atakuje: ',1)
                target=target.rstrip('.')
                src=next((cid for cid in prior if cid in game.cards
                          and game.cards[cid].definition.name==actor),None)
                dst=next((cid for cid in current if cid in game.cards
                          and game.cards[cid].definition.name==target),None)
                if dst is None:
                    dst=next((cid for cid in prior if cid in game.cards
                              and game.cards[cid].definition.name==target),None)
                if target.startswith('Bohater'):
                    dst=next((f'hero:{i}' for i,p in enumerate(game.players)
                              if p.name in target),None)
                if src and dst:
                    start=(prior.get(src) or current.get(src) or {}).get('at')
                    end=(current.get(dst) or prior.get(dst) or {}).get('at')
                    if start and end:self._push('attack',end,now,origin=start)
        for uid,old in prior.items():
            if uid not in current:
                if not uid.startswith('hero:'):
                    self._push('death',old['at'],now,'ZGON')
                continue
            new=current[uid]
            delta=new['hp']-old['hp']
            if delta<0:self._push('damage',new['at'],now,str(delta))
            if delta>0:self._push('heal',new['at'],now,f'+{delta}')
            if new['shield']>old['shield']:
                self._push('shield',new['at'],now,'TARCZA')
            if new['armor']>old['armor']:
                self._push('armor',new['at'],now,f'+{new["armor"]-old["armor"]}')
            for kind in sorted(new['status']-old['status']):
                mapped={'poison':'poison','stun':'stun','regen':'regen',
                        'quick':'quick','double':'double'}.get(kind,'special')
                self._push(mapped,new['at'],now)
        self.pulses=[p for p in self.pulses if now-p.born < p.lifetime]

    def draw(self,screen: pygame.Surface,now: int,font: pygame.font.Font):
        """Eased projectiles, impact particles, floating text and status rings.

        Effects are cosmetic, short-lived, capped, and avoid card stat plates.
        """
        alive=[]
        for pulse in self.pulses:
            age=now-pulse.born
            if age<0 or age>=pulse.lifetime:
                continue
            alive.append(pulse)
            t=age/pulse.lifetime
            color,title=KINDS[pulse.kind]
            alpha=max(0,int(230*(1-t)**1.2))
            x,y=pulse.at
            if pulse.kind=='attack' and pulse.origin is not None:
                travel=min(1.,t*3.05)
                eased=1-(1-travel)**3
                x=pulse.origin[0]+(pulse.at[0]-pulse.origin[0])*eased
                y=pulse.origin[1]+(pulse.at[1]-pulse.origin[1])*eased
                radius=4+int(7*(1-travel))
                glow=pygame.Surface((60,60),pygame.SRCALPHA)
                pygame.draw.circle(glow,(*color,max(0,int(alpha*.25))),
                                   (30,30),radius*3)
                pygame.draw.circle(glow,(*color,alpha),(30,30),radius)
                for i in range(4):
                    u=max(0.,eased-(i+1)*.055)
                    tx=pulse.origin[0]+(pulse.at[0]-pulse.origin[0])*u
                    ty=pulse.origin[1]+(pulse.at[1]-pulse.origin[1])*u
                    pygame.draw.circle(screen,tuple(int(c*(.53+.11*i)) for c in color),
                                       (int(tx),int(ty)),max(1,4-i))
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
            shadow=font.render(label,True,(6,14,21))
            shadow.set_alpha(alpha)
            message.set_alpha(alpha)
            bx=int(x)-message.get_width()//2
            by=int(y)-message.get_height()//2
            screen.blit(shadow,(bx+1,by+2))
            screen.blit(message,(bx,by))
        self.pulses=alive
