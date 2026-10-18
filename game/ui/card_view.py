"""Minimal Fantasy: read-only, resolution-aware cards for Game Master v19.

Draw order is deliberate: artwork, subdued overlay, informational panels,
labels/statuses, and finally opaque ATK/HP plates. The gameplay engine is not
modified by rendering.
"""
from __future__ import annotations

import hashlib
import math
import re
import pygame

from game import config as cfg
from game.ui.assets import ImageAssets
from game.core.status_view import STATUS_COLORS
from game.ui.card_infographics import card_cue, FAMILY_COLORS
from game.ui.card_summary import ability_summary
from game.ui.game_icons import GameIcons,status_icon_key

FACTION_COLORS = {
    'Elfy': (101,194,150), 'Dzikie bestie': (220,164,89),
    'Potwory': (176,125,217), 'Krasnoludy': (222,134,93),
    'Ludzie': (122,178,227),
}
TRIGGER_BADGES = {
    'Przy wystawieniu': ('PRZY ZAGRANIU', (55,114,144)),
    'Przy ataku': ('PRZY ATAKU', (139,99,49)),
    'Przy śmierci': ('PRZY ŚMIERCI', (126,77,141)),
    'Na koniec tury': ('NA KONIEC TURY', (65,118,82)),
    'Pasywna': ('PASYWNA', (65,98,152)),
}
ART = {
    'S01':'mag_zorzy.png','S09':'wilk_szponiasty.png',
    'S21':'widmo.png','S34':'chorazy.png','S105':'straznik.png',
    'S27':'kowal_run.png','S82':'rycerz_kosci.png',
}
PRIORITY = ('stun','taunt','poison','shield','armor','double','quick','regen',
            'immune','atk_down','hp_down','atk_up','hp_up','heal_aura','cleanse','other')
FAMILY_MARK = {
    'Obrażenia':'✦','Leczenie':'+','ATK ±':'±','MAX HP ±':'PŻ',
    'Pancerz':'◆','Tarcza':'◇','Trucizna':'☣','Ogłuszenie':'!',
    'Regeneracja':'↗','Prowokacja':'!','Oczyszczanie':'✧',
    'Odporność':'◈','Szybki atak':'»','Podwójny atak':'2×',
}


def card_zones(rect: pygame.Rect) -> dict[str, pygame.Rect]:
    """Deterministic nonoverlapping zones for the three approved card sizes."""
    x,y,w,h=rect
    if h>=320:
        title_h,trigger_h,art_h,stats_h,pad=(34,24,112,52,11)
    elif h>=210:
        title_h,trigger_h,art_h,stats_h,pad=(23,17,38,41,6)
    else:
        title_h,trigger_h,art_h,stats_h,pad=(22,17,22,37,5)
    inner_x=x+pad;inner_w=w-2*pad
    name=pygame.Rect(inner_x,y+3,inner_w,title_h-3)
    trigger=pygame.Rect(inner_x,name.bottom,inner_w,trigger_h)
    art=pygame.Rect(inner_x,trigger.bottom+3,inner_w,art_h)
    stats=pygame.Rect(inner_x,y+h-pad-stats_h,inner_w,stats_h)
    info=pygame.Rect(inner_x,art.bottom+3,inner_w,stats.top-art.bottom-6)
    return {'name':name,'trigger':trigger,'art':art,'info':info,'stats':stats}


def compact_context(effect: str) -> str:
    """Show a grounded target clue; no guessed recipient when none is explicit."""
    value=effect.lower()
    if 'wybranej wrogiej jednostce' in value or 'wskazanej wrogiej jednostce' in value:
        return 'CEL: WROGA JEDNOSTKA'
    if 'atakowanej wrogiej jednostce' in value:
        return 'CEL: ATAKOWANY WRÓG'
    if 'wybranego wrogiego bohatera' in value or 'wrogiemu bohaterowi' in value:
        return 'CEL: WROGI BOHATER'
    if 'wybranej sojuszniczej jednostce' in value or 'wybranej własnej jednostce' in value:
        return 'CEL: SOJUSZNIK'
    if 'własnego bohatera' in value or 'własnemu bohaterowi' in value:
        return 'CEL: WŁASNY BOHATER'
    if 'tej jednostce' in value or 'ta jednostka' in value:
        return 'CEL: TA JEDNOSTKA'
    if 'wszystkie wrogie' in value or 'wszystkich wrog' in value:
        return 'CEL: WSZYSCY WROGOWIE'
    # A sentence fragment is not presented as if it were a complete rule.
    return 'SZCZEGÓŁY ZDOLNOŚCI: [I]'


class CardView:
    def __init__(self):
        self.images=ImageAssets()
        self.icons=GameIcons()
        self.fonts={}
        for size in (9,10,11,12,13,14,15,17,18,20,22,25):
            self.fonts[(size,False)]=pygame.font.SysFont('segoeui',size)
            self.fonts[(size,True)]=pygame.font.SysFont('segoeui',size,bold=True)
        self.font_title=self.fonts[(14,True)]
        self.artcache={}

    def font(self,size,bold=False):
        return self.fonts[(size,bold)]

    @staticmethod
    def clip(text,font,width):
        text=str(text)
        if font.size(text)[0]<=width:return text
        while text and font.size(text+'…')[0]>width:
            text=text[:-1]
        return text+'…' if text else ''

    def _fit_font(self,text,width,sizes=(14,13,12,11,10,9),bold=True):
        for size in sizes:
            ft=self.font(size,bold)
            if ft.size(str(text))[0]<=width:return ft
        return self.font(9,bold)

    @staticmethod
    def wrap_ability(text,font,width,max_lines):
        """Zawijaj na granicach słów; jeśli trzeba skracać, ZAWSZE zaznacz ….

        Nigdy nie ukrywaj ostatniej linii po cichu. Pełny tekst dostępny
        pozostaje w panelu i widoku [I].
        """
        if max_lines<=0:return ()
        lines=[]
        current=''
        for word in text.split():
            candidate=(current+' '+word).strip()
            if current and font.size(candidate)[0]>width:
                lines.append(current)
                current=word
            else:
                current=candidate
        if current:lines.append(current)
        if not lines:return ()
        if len(lines)>max_lines:
            lines=lines[:max_lines]
            lines[-1]=CardView.clip(lines[-1]+'…',font,width)
        return tuple(CardView.clip(line,font,width) for line in lines)

    def summary_layout(self,card,rect,unit=None):
        """Wyznacza faktyczne strefy tekstu, także do testowania kolizji."""
        d=card.definition
        cue=card_cue(card,unit)
        short=ability_summary(card,unit)
        zone=card_zones(rect)
        info=zone['info']
        large=rect.height>=320
        label_h=18 if large else 14
        family=pygame.Rect(info.x+3,info.y+3,info.width-6,label_h)
        # Puste skróty ODP, SZYBKI, TARCZA, 2 ATAKI itd. dublowały
        # nagłówek kategorii, zabierając miejsce opisowi celu i warunku.
        show_value=cue.effect_value is not None
        if d.family=='Ogłuszenie' and cue.effect_value==0:
            show_value=False
        main=None
        if show_value:
            main=pygame.Rect(info.x+4,family.bottom+2,info.width-8,
                             23 if large else 16)
        footer=pygame.Rect(info.x+3,info.bottom-(31 if large else 15),
                           info.width-6,27 if large else 12)
        desc_y=(main.bottom+1) if main else (family.bottom+3)
        font=self.font(14 if large else (12 if show_value else 13))
        step=max(font.get_height()+1,17 if large else 14)
        free=max(0,footer.top-desc_y)
        max_lines=min(5 if large else (2 if show_value else 3),free//step)
        text=short.full if large else short.short
        lines=self.wrap_ability(text,font,info.width-8,max_lines)
        boxes=tuple(pygame.Rect(info.x+4,desc_y+i*step,info.width-8,
                                font.get_height()) for i in range(len(lines)))
        return {
            'family':family,'main':main,'footer':footer,'font':font,
            'lines':lines,'boxes':boxes,'show_value':show_value,
        }

    def art(self,cid,faction,size,family=''):
        if cid in ART:
            return self.images.get_card_image(ART[cid],size)
        key=(cid,size,family)
        if key in self.artcache:return self.artcache[key]
        w,h=size;color=FACTION_COLORS[faction];accent=FAMILY_COLORS.get(family,color)
        im=pygame.Surface(size)
        for yy in range(h):
            k=yy/max(1,h)
            pygame.draw.line(im,tuple(int(c*(.25+.14*k)) for c in color),(0,yy),(w,yy))
        cx,cy=w//2,h//2
        radius=max(8,min(w,h)*.32)
        pygame.draw.circle(im,accent,(cx,cy),int(radius),2)
        count=5+int(hashlib.sha1(cid.encode()).hexdigest()[:4],16)%5
        for j in range(count):
            t=2*math.pi*j/count
            pygame.draw.circle(im,accent,(int(cx+math.cos(t)*radius*.7),
                                          int(cy+math.sin(t)*radius*.7)),2)
        symbol=FAMILY_MARK.get(family,'✦')
        label=self.font(25,True).render(symbol,True,(245,243,233))
        im.blit(label,label.get_rect(center=(cx,cy)))
        self.artcache[key]=im
        return im

    def _center(self,screen,text,rect,font,color):
        surf=font.render(text,True,color)
        screen.blit(surf,surf.get_rect(center=rect.center))

    def _pill(self,screen,rect,text,color,font=None,foreground=(249,249,243)):
        pygame.draw.rect(screen,color,rect,border_radius=4)
        f=font or self.font(10,True)
        self._center(screen,self.clip(text,f,rect.width-6),rect,f,foreground)

    def draw(self,screen,card,rect,unit=None,selected=False,dim=False,
             hover=False,statuses=(),ready=None,attacks_remaining=None,
             attacks_total=None):
        d=card.definition
        cue=card_cue(card,unit)
        summary=ability_summary(card,unit)
        color=FACTION_COLORS[d.faction]
        zone=card_zones(rect)
        large=rect.height>=320
        board=unit is not None
        pad=11 if large else 6
        # BACKGROUND + FRAME
        pygame.draw.rect(screen,(6,10,16),rect.move(0,3),border_radius=11)
        pygame.draw.rect(screen,(25,37,49),rect,border_radius=11)
        pygame.draw.rect(screen,color,rect,2,border_radius=11)
        # IMAGE: never contains stats or descriptive text.
        art=zone['art']
        screen.blit(self.art(d.id,d.faction,art.size,d.family),art)
        if dim:
            shade=pygame.Surface(art.size,pygame.SRCALPHA)
            shade.fill((6,10,17,130))
            screen.blit(shade,art.topleft)
        pygame.draw.rect(screen,(88,107,114),art,1,border_radius=5)
        emblem=self.icons.get(d.faction,'factions',min(19,art.height-4))
        if emblem is not None:
            screen.blit(emblem,(art.x+2,art.y+2))
        # ALL INFORMATION PANELS are opaque and above artwork/dimming.
        name_rect=zone['name']
        pygame.draw.rect(screen,(20,31,43),name_rect,border_radius=4)
        pygame.draw.rect(screen,(19,31,41),zone['info'],border_radius=5)
        trigger_text,trigger_color=TRIGGER_BADGES[d.trigger]
        pygame.draw.rect(screen,trigger_color,zone['trigger'],border_radius=4)
        stats_rect=zone['stats']
        half=(stats_rect.width-5)//2
        attack_box=pygame.Rect(stats_rect.x,stats_rect.y,half,stats_rect.height)
        health_box=pygame.Rect(attack_box.right+5,stats_rect.y,stats_rect.width-half-5,stats_rect.height)
        pygame.draw.rect(screen,(51,38,27),attack_box,border_radius=5)
        pygame.draw.rect(screen,(61,34,42),health_box,border_radius=5)
        pygame.draw.rect(screen,(147,108,54),attack_box,1,border_radius=5)
        pygame.draw.rect(screen,(153,84,91),health_box,1,border_radius=5)
        # MAIN TEXT
        title_size=17 if large else (13 if rect.height>=210 else 12)
        title=self._fit_font(d.name,name_rect.width-8,(title_size,14,13,12,11,10,9))
        self._center(screen,self.clip(d.name,title,name_rect.width-8),name_rect,title,cfg.TEXT)
        trigger_font=self._fit_font(trigger_text,zone['trigger'].width-7,
                                   (13,12,11,10,9))
        self._center(screen,trigger_text,zone['trigger'],trigger_font,(250,253,249))
        info=zone['info']
        text_plan=self.summary_layout(card,rect,unit)
        family=text_plan['family']
        family_name=d.family.upper().replace("MAX HP","MAX PŻ").replace("ATK","ATAK")
        # Bez ozdobnych znaków, które mogą być wyświetlane jako puste kwadraty
        # w niektórych czcionkach Windows.
        family_icon=self.icons.get(d.family,'families',15 if large else 13)
        if family_icon is None:
            self._pill(screen,family,family_name,cue.color,
                       self._fit_font(family_name,family.width-7,
                                      (13,12,11,10) if large else (12,11,10)),
                       (15,23,28))
        else:
            pygame.draw.rect(screen,cue.color,family,border_radius=4)
            glyph_rect=pygame.Rect(family.x+2,
                                   family.centery-family_icon.get_height()//2,
                                   *family_icon.get_size())
            screen.blit(family_icon,glyph_rect)
            text_rect=pygame.Rect(family.x+family_icon.get_width()+4,
                                  family.y,family.width-family_icon.get_width()-5,
                                  family.height)
            ft=self._fit_font(family_name,text_rect.width-4,
                              (12,11,10) if large else (11,10))
            self._center(screen,self.clip(family_name,ft,text_rect.width-4),
                         text_rect,ft,(15,23,28))
        main=text_plan['main']
        if main is not None:
            bfont=self._fit_font(cue.base,main.width,
                                 (20,18,17,15,13,11) if large else (15,14,13,12,11))
            self._center(screen,self.clip(cue.base,bfont,main.width),main,
                         bfont,(245,245,230))
        for line,region in zip(text_plan['lines'],text_plan['boxes']):
            screen.blit(text_plan['font'].render(line,True,(235,240,239)),
                        region.topleft)
        # Pasek rozwoju jest oddzielony od opisów. Nie rysujemy nad nim
        # dodatkowego tekstu, który w 0.9.12 kolidował z podglądem 255×380.
        footer=text_plan['footer']
        pygame.draw.rect(screen,(39,75,65),footer,border_radius=3)
        ft=self._fit_font(cue.upgrade,footer.width-8,
                          (13,12,11,10) if large else (10,9))
        self._center(screen,self.clip(cue.upgrade,ft,footer.width-8),
                     footer,ft,(183,255,196))
        # Statuses cover artwork only, never stats or ability panel.
        if statuses:
            prio=lambda st:PRIORITY.index(st.category) if st.category in PRIORITY else 99
            ordered=sorted(statuses,key=prio)
            compact=ordered[:2]
            x=art.x+3;y=art.bottom-17
            for status in compact:
                sf=self.font(9,True)
                icon=self.icons.get(status_icon_key(status),'statuses',13)
                if icon is not None:
                    width=37
                    pill=pygame.Rect(x,y,width,14)
                    pygame.draw.rect(screen,status.color,pill,border_radius=4)
                    screen.blit(icon,(x,y))
                    label=self.clip(status.short,sf,width-16)
                    text=sf.render(label,True,(14,23,29))
                    screen.blit(text,(x+14,y+(14-text.get_height())//2))
                else:
                    label=self.clip(status.short,sf,34)
                    width=max(23,min(39,sf.size(label)[0]+8))
                    self._pill(screen,pygame.Rect(x,y,width,14),label,status.color,sf,(14,23,29))
                x+=width+3
            rest=len(ordered)-len(compact)
            if rest:
                self._pill(screen,pygame.Rect(art.right-29,y,26,14),f'+{rest}',
                           (61,78,92),self.font(9,True))
        # Progress on hand; never shown on deployed units.
        if not board:
            label=f'{card.hand_turns%3}/3 · POZ. {card.ability_level}'
            sf=self.font(10,True)
            pw=min(art.width-6,sf.size(label)[0]+9)
            self._pill(screen,pygame.Rect(art.right-pw-3,art.y+4,pw,16),
                       label,(34,79,65),sf)
        elif attacks_total is not None:
            rem=max(0,int(attacks_remaining or 0))
            count=f'ATAKI {rem}/{max(1,int(attacks_total))}'
            sf=self.font(9,True)
            w=min(art.width-6,sf.size(count)[0]+10)
            tag=pygame.Rect(art.right-w-3,art.y+3,w,17)
            self._pill(screen,tag,count,(43,105,72) if ready else (74,78,89),sf)
        # ATK + PŻ last: large, opaque, never dimmed or overlapped.
        attack=unit.atk if board else card.attack
        hp=unit.hp if board else card.max_hp
        max_hp=unit.max_hp if board else card.max_hp
        label_font=self.font(10 if large else 9,True)
        value_font=self.font(25 if large else (22 if rect.height>=210 else 20),True)
        max_font=self.font(13 if large else 10)
        for r,t in ((attack_box,'ATAK'),(health_box,'PŻ')):
            label=label_font.render(t,True,(213,210,201))
            screen.blit(label,(r.x+4,r.y+2))
        aa=value_font.render(str(attack),True,(255,215,132))
        screen.blit(aa,aa.get_rect(centerx=attack_box.centerx,bottom=attack_box.bottom-2))
        hh=value_font.render(str(hp),True,(255,153,157))
        mm=max_font.render('/'+str(max_hp),True,(223,196,198))
        total=hh.get_width()+mm.get_width()
        if total>health_box.width-4:
            small=self.font(17,True)
            hh=small.render(str(hp),True,(255,153,157))
            mm=self.font(9).render('/'+str(max_hp),True,(223,196,198))
            total=hh.get_width()+mm.get_width()
        xx=health_box.centerx-total//2
        screen.blit(hh,(xx,health_box.bottom-hh.get_height()-2))
        screen.blit(mm,(xx+hh.get_width(),health_box.bottom-mm.get_height()-4))
        # Selection overlays stay on the edge and are visually distinct.
        if selected:
            pygame.draw.rect(screen,cfg.GOLD,rect.inflate(5,5),3,border_radius=12)
        elif hover:
            pygame.draw.rect(screen,cfg.HOVER,rect.inflate(3,3),1,border_radius=12)
