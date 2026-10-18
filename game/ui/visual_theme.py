"""Minimal Fantasy visual system — decorative only; no gameplay access.

All coordinates are on the 1480 × 980 logical Pygame canvas.
Texture generation is deterministic, cached, offline and never obscures text.
"""
from __future__ import annotations

import math
import random
import pygame

INK=(12,19,27)
SLATE=(29,44,56)
BRASS=(185,145,79)
SILVER=(100,128,140)
PLAYER=(72,141,120)
ENEMY=(149,87,105)


class VisualTheme:
    def __init__(self):
        self._textures={}

    @staticmethod
    def background(size):
        w,h=size
        art=pygame.Surface(size).convert()
        # Deep teal-to-umber stone, like a candlelit medieval map table.
        for y in range(h):
            t=y/max(1,h-1)
            wave=.5+.5*math.cos(t*math.pi*2.1)
            base=(int(15+8*t+4*wave),int(24+7*t+3*wave),
                  int(32+8*t+2*wave))
            pygame.draw.line(art,base,(0,y),(w,y))
        rng=random.Random(916)
        # Carved slate grain (no dynamically changing noise / flicker).
        grain=pygame.Surface(size,pygame.SRCALPHA)
        for _ in range(6000):
            x=rng.randrange(w);y=rng.randrange(h)
            a=rng.randrange(5,21)
            bright=rng.randrange(2)==0
            pygame.draw.line(grain,(201,172,124,a) if bright
                             else (0,0,0,a),
                             (x,y),(min(w-1,x+rng.randrange(1,20)),y),1)
        art.blit(grain,(0,0))
        # Broad, subdued hand-carved sigils; recessed behind play zones.
        sigils=pygame.Surface(size,pygame.SRCALPHA)
        for cx,cy,r in ((570,390,214),(540,825,278),(552,258,142)):
            for radius,alpha in ((r,36),(int(r*.73),19),(int(r*.44),22)):
                pygame.draw.circle(sigils,(168,132,81,alpha),(cx,cy),radius,2)
            for k in range(12):
                angle=2*math.pi*k/12
                px=cx+math.cos(angle)*r
                py=cy+math.sin(angle)*r
                pygame.draw.circle(sigils,(166,138,92,32),(int(px),int(py)),3,1)
        art.blit(sigils,(0,0))
        # Distinct but calm well surfaces for player/AI/hand.
        overlays=pygame.Surface(size,pygame.SRCALPHA)
        for rect,c in (
            (pygame.Rect(82,90,983,315),(59,36,47,53)),
            (pygame.Rect(82,406,983,310),(28,58,54,51)),
            (pygame.Rect(82,713,983,246),(45,56,45,64))):
            pygame.draw.rect(overlays,c,rect,border_radius=21)
            pygame.draw.rect(overlays,(198,151,93,48),rect,1,border_radius=21)
        # Edge vignette using narrow translucent strokes, no expensive blur.
        for n in range(33):
            alpha=int((33-n)*1.35)
            r=pygame.Rect(n*2,n*2,w-n*4,h-n*4)
            if r.width>0 and r.height>0:
                pygame.draw.rect(overlays,(0,0,0,alpha),r,2,border_radius=15)
        art.blit(overlays,(0,0))
        return art

    def panel(self,screen,rect,fill=None,line=None,radius=12):
        base=fill or SLATE
        accent=line or SILVER
        shadow=pygame.Surface((rect.width+12,rect.height+12),pygame.SRCALPHA)
        pygame.draw.rect(shadow,(0,0,0,79),
                         pygame.Rect(6,7,rect.width,rect.height),
                         border_radius=radius+1)
        screen.blit(shadow,(rect.x-6,rect.y-5))
        pygame.draw.rect(screen,(8,15,23),rect,border_radius=radius)
        core=rect.inflate(-2,-2)
        pygame.draw.rect(screen,base,core,border_radius=max(2,radius-2))
        # Bevel: bronze highlights at the upper edge; recessed bottom.
        pygame.draw.line(screen,tuple(min(255,c+24) for c in base),
                         (rect.left+radius,rect.top+2),
                         (rect.right-radius,rect.top+2),1)
        pygame.draw.line(screen,(12,20,28),
                         (rect.left+radius,rect.bottom-3),
                         (rect.right-radius,rect.bottom-3),1)
        pygame.draw.rect(screen,accent,rect,1,border_radius=radius)
        # Corner studs are tiny and outside text core.
        if rect.width>=165 and rect.height>=48:
            for px in (rect.x+9,rect.right-10):
                pygame.draw.circle(screen,BRASS,(px,rect.y+8),2)

    def button(self,screen,rect,hover=False,active=True,accent=False,pressed=False):
        if not active:
            base=(39,47,52);edge=(67,77,80)
        elif accent:
            base=(72,103,82) if not hover else (87,130,98)
            edge=(206,166,96)
        else:
            base=(43,65,74) if not hover else (58,89,98)
            edge=(111,142,145) if hover else (82,107,117)
        if pressed and active:
            base=tuple(max(0,c-12) for c in base)
        self.panel(screen,rect,base,edge,9)
        if active and rect.height>22:
            pygame.draw.line(screen,(129,156,151) if hover else (88,111,111),
                             (rect.x+13,rect.y+5),(rect.right-13,rect.y+5),1)

    def slot(self,screen,rect,owner=0):
        accent=PLAYER if owner==0 else ENEMY
        self.panel(screen,rect,(27,41,49),accent,12)
        inner=rect.inflate(-12,-12)
        pygame.draw.rect(screen,(17,29,38),inner,border_radius=9)
        pygame.draw.rect(screen,(56,73,80),inner,1,border_radius=9)
        # Small corner-line engraving; never under a placed card's labels.
        for sx in (rect.x+11,rect.right-11):
            for sy in (rect.y+11,rect.bottom-11):
                dx=1 if sx<rect.centerx else -1
                dy=1 if sy<rect.centery else -1
                pygame.draw.line(screen,BRASS,(sx,sy),(sx+dx*9,sy),1)
                pygame.draw.line(screen,BRASS,(sx,sy),(sx,sy+dy*9),1)

    def card_lustre(self,screen,rect,faction):
        """Rim-only accents: rendered behind data fields, no text overlays."""
        pygame.draw.rect(screen,(8,15,22),rect.move(0,3),border_radius=11)
        pygame.draw.rect(screen,(26,36,46),rect,border_radius=11)
        pygame.draw.rect(screen,faction,rect,2,border_radius=11)
        pygame.draw.line(screen,(199,163,106),
                         (rect.left+14,rect.top+4),(rect.right-14,rect.top+4),1)
        pygame.draw.line(screen,(68,75,75),
                         (rect.left+14,rect.bottom-5),(rect.right-14,rect.bottom-5),1)

    @staticmethod
    def content_bounds(text,font,x,y,center=False):
        surface=font.render(str(text),True,(255,255,255))
        return surface.get_rect(center=(x,y)) if center else surface.get_rect(topleft=(x,y))
