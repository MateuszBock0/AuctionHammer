"""Animacje wyłącznie odczytujące autorytatywny stan Game Master v19.

Nie przewidujemy wyników ataku i nie wywołujemy metod mutujących Match:
obrażenia, leczenie, tarcze, zatrucia, bonusy i zgony są wykrywane z różnicy
dwóch ZATWIERDZONYCH stanów. Ruch ataku z zatwierdzonego dziennika zdarzeń.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sin, pi
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
            return
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
        """Efekty nad ilustracjami, z przezroczystością i płynną interpolacją."""
        live=[]
        for p in self.pulses:
            age=now-p.born
            if age<0 or age>=p.lifetime:continue
            live.append(p)
            t=age/p.lifetime
            color,title=KINDS[p.kind]
            alpha=max(0,int(240*(1-t)))
            if p.kind=='attack' and p.origin is not None:
                travel=min(1.,t*2.9)
                x=p.origin[0]+(p.at[0]-p.origin[0])*travel
                y=p.origin[1]+(p.at[1]-p.origin[1])*travel
                radius=max(2,int(9*(1-travel*.45)))
                glow=pygame.Surface((radius*8,radius*8),pygame.SRCALPHA)
                pygame.draw.circle(glow,(*color,alpha//3),
                                   (radius*4,radius*4),radius*3)
                pygame.draw.circle(glow,(*color,alpha),
                                   (radius*4,radius*4),radius)
                screen.blit(glow,(int(x)-radius*4,int(y)-radius*4))
                continue
            x,y=p.at
            y-=int(10+29*t)
            radius=14+int(21*t)
            surf=pygame.Surface((radius*2+4,radius*2+4),pygame.SRCALPHA)
            if p.kind in ('shield','armor'):
                pygame.draw.circle(surf,(*color,int(alpha*.85)),
                                   (radius+2,radius+2),radius,3)
            elif p.kind=='death':
                for i in range(8):
                    vx=int((i%4-1.5)*radius*.55)
                    vy=int((i//4*2-1)*radius*.65)
                    pygame.draw.circle(surf,(*color,alpha),
                                       (radius+vx+2,radius+vy+2),3)
            else:
                pygame.draw.circle(surf,(*color,int(alpha*.28)),
                                   (radius+2,radius+2),radius)
            screen.blit(surf,(int(x)-radius-2,int(y)-radius-2))
            label=p.label or title
            rendered=font.render(label,True,color)
            rendered.set_alpha(alpha)
            if rendered.get_width()>106:
                continue
            screen.blit(rendered,(int(x)-rendered.get_width()//2,
                                  int(y)-rendered.get_height()//2))
        self.pulses=live
