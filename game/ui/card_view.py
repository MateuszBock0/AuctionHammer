"""Wizualizacja kart — wyłącznie Pygame, bez zmian stanu gry."""
import hashlib
import pygame
from game import config as cfg
from game.ui.assets import ImageAssets
from game.core.status_view import STATUS_COLORS

FACTION_COLORS={
    'Elfy':(101,194,150),'Dzikie bestie':(220,164,89),'Potwory':(176,125,217),
    'Krasnoludy':(222,134,93),'Ludzie':(122,178,227),
}
ART={'S01':'mag_zorzy.png','S09':'wilk_szponiasty.png','S21':'widmo.png','S34':'chorazy.png',
     'S105':'straznik.png','S27':'kowal_run.png','S82':'rycerz_kosci.png'}

class CardView:
    def __init__(self):
        self.images=ImageAssets()
        self.font_title=pygame.font.SysFont('segoeui',14,bold=True)
        self.font_small=pygame.font.SysFont('segoeui',12)
        self.font_stats=pygame.font.SysFont('segoeui',19,bold=True)
        self.font_badge=pygame.font.SysFont('segoeui',10,bold=True)
        self.artcache={}

    @staticmethod
    def clip(s,font,width):
        if font.size(s)[0]<=width:return s
        while s and font.size(s+'…')[0]>width:s=s[:-1]
        return s+'…' 

    def art(self,cid,faction,size):
        if cid in ART:return self.images.get_card_image(ART[cid],size)
        key=(cid,size)
        if key in self.artcache:return self.artcache[key]
        w,h=size;color=FACTION_COLORS[faction]
        im=pygame.Surface(size)
        im.fill(tuple(max(0,int(x*.28)) for x in color))
        pygame.draw.circle(im,tuple(min(255,int(x*.57+35)) for x in color),(w//2,h//2),min(w,h)//3,4)
        pygame.draw.line(im,color,(w//2,12),(w//2,h-12),3)
        pygame.draw.line(im,color,(12,h//2),(w-12,h//2),3)
        seed=int(hashlib.sha1(cid.encode()).hexdigest()[:4],16)
        n=5+seed%5
        for k in range(n):
            angle=6.283*k/n
            import math
            pt=(int(w//2+math.cos(angle)*w*.3),int(h//2+math.sin(angle)*h*.3))
            pygame.draw.circle(im,color,pt,3)
        self.artcache[key]=im
        return im

    def draw(self,screen,card,rect,unit=None,selected=False,dim=False,hover=False,statuses=()):
        d=card.definition;color=FACTION_COLORS[d.faction]
        # Preserve the faction accent while making the active effect(s) obvious.
        # Selected cards keep a separate gold outline; effects are never hidden.
        border=statuses[0].color if statuses else (cfg.HOVER if hover else color)
        pygame.draw.rect(screen,(5,9,16),rect.move(0,4),border_radius=10)
        pygame.draw.rect(screen,(28,42,54),rect,border_radius=10)
        if selected:
            pygame.draw.rect(screen,cfg.GOLD,rect.inflate(7,7),2,border_radius=12)
        pygame.draw.rect(screen,border,rect,3 if statuses else 2,border_radius=10)
        # Multiple simultaneous effects: segmented multicolour rim at the top.
        distinct=list(dict.fromkeys(st.category for st in statuses))[:7]
        if distinct:
            inner_width=rect.width-12
            for j,key in enumerate(distinct):
                xx=rect.x+6+round(inner_width*j/len(distinct))
                ww=max(1,round(inner_width*(j+1)/len(distinct))-round(inner_width*j/len(distinct)))
                pygame.draw.rect(screen,STATUS_COLORS[key],pygame.Rect(xx,rect.y+2,ww,5))
        name=self.clip(d.name,self.font_title,rect.width-16)
        name_s=self.font_title.render(name,True,cfg.TEXT)
        screen.blit(name_s,(rect.x+7,rect.y+8))
        art_rect=pygame.Rect(rect.x+7,rect.y+34,rect.width-14,max(22,rect.height-86))
        if art_rect.height>0 and art_rect.width>0:
            screen.blit(self.art(d.id,d.faction,art_rect.size),art_rect)
        subtitle=self.clip(d.family.upper(),self.font_small,rect.width-16)
        screen.blit(self.font_small.render(subtitle,True,color),(rect.x+8,rect.bottom-47))
        atk=unit.atk if unit else card.attack
        hp=unit.hp if unit else card.max_hp
        hptotal=unit.max_hp if unit else card.max_hp
        a=self.font_stats.render(str(atk),True,(245,206,130))
        h=self.font_stats.render(f'{hp}/{hptotal}',True,(249,126,127))
        screen.blit(a,(rect.x+10,rect.bottom-29));screen.blit(h,(rect.right-10-h.get_width(),rect.bottom-29))
        # Status pills stay inside the artwork area, away from the card family
        # and ATK/HP. The detailed modal lists *all* active effects and sources.
        if statuses:
            labels=[]
            seen=set()
            for status in statuses:
                identity=(status.category,status.short)
                if identity not in seen:
                    labels.append(status);seen.add(identity)
            limit=6 if rect.width<200 else 9
            hidden=max(0,len(labels)-limit)
            shown=labels[:limit-(1 if hidden else 0)]
            if hidden:
                from game.core.status_view import VisibleStatus
                shown.append(VisibleStatus('other',f'+{hidden+1}', 'Więcej efektów', 'Pełne szczegóły w panelu [I]'))
            # Up to three compact rows inside the illustration, anchored below.
            rows=[shown[i:i+3] for i in range(0,len(shown),3)]
            for row_i,row in enumerate(rows):
                yy=art_rect.bottom-3-(len(rows)-row_i)*19
                x=art_rect.x+2
                for st in row:
                    badge=self.font_badge.render(st.short,True,(13,24,35))
                    bw=min(art_rect.right-x-2,badge.get_width()+9)
                    if bw<22:break
                    br=pygame.Rect(x,yy,bw,16)
                    pygame.draw.rect(screen,st.color,br,border_radius=4)
                    screen.blit(badge,(x+4,yy+2))
                    x+=bw+3
        elif card.hand_turns>0:
            caption=self.font_badge.render(f'W ręku: {card.hand_turns}t | Zdolność +{card.ability_level}',True,cfg.TEXT)
            r=pygame.Rect(rect.x+4,art_rect.bottom-19,rect.width-8,16)
            pygame.draw.rect(screen,(67,105,96),r,border_radius=3)
            screen.blit(caption,(r.x+4,r.y+1))
        if dim:
            shade=pygame.Surface(rect.size,pygame.SRCALPHA);shade.fill((2,8,12,130));screen.blit(shade,rect.topleft)
