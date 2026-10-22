"""Minimal Fantasy visual system — decorative only; no gameplay access.

All coordinates are on the 1480 × 980 logical Pygame canvas.
Texture generation is deterministic, cached, offline and never obscures text.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
import sys
import pygame

ASSET_ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[2]))/'assets'/'ui'/'tavern'

# Consistent, restrained candlelit-walnut palette. Gold is an accent
# rather than a background. The original faction palette is unchanged.
TAVERN_PANEL_BG=(58,43,27)
TAVERN_PANEL_INNER=(76,57,37)
TAVERN_TOOLTIP_BG=(68,50,31)
TAVERN_GOLD=(214,176,92)
TAVERN_BRASS=(168,128,67)
TAVERN_HOVER_GOLD=(232,196,111)
TAVERN_TEXT=(241,231,214)
TAVERN_MUTED=(206,189,160)
TAVERN_SHADOW=(28,20,12)
TAVERN_SCRIM=(34,22,12)

INK=(12,19,27)
SLATE=TAVERN_PANEL_BG
BRASS=TAVERN_BRASS
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
        # Warm walnut fallback, not blue-black when the scene is absent.
        for y in range(h):
            t=y/max(1,h-1)
            wave=.5+.5*math.cos(t*math.pi*2.1)
            base=(int(32+13*t+4*wave),int(22+10*t+2*wave),
                  int(14+6*t+wave))
            pygame.draw.line(art,base,(0,y),(w,y))
        # Actual Tavern UI Pack v2 scenery; dark wells below keep units legible.
        scene=ASSET_ROOT/'tavern_scene.jpg'
        if scene.is_file():
            try:
                im=pygame.image.load(str(scene)).convert()
                art.blit(pygame.transform.smoothscale(im,(w,h)),(0,0))
            except (pygame.error,OSError):
                pass
        # Subtle warm tint keeps the original tavern photograph legible.
        candlelight=pygame.Surface(size,pygame.SRCALPHA)
        candlelight.fill((93,54,23,44))
        art.blit(candlelight,(0,0))
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
        # Tavern pack v2: *only* a quiet tabletop crop, never the busy
        # full tavern illustration behind text/units. Optimized ~36 KB.
        wood=ASSET_ROOT/'wood_ambient.png'
        if wood.is_file():
            try:
                texture=pygame.image.load(str(wood)).convert()
                surface=pygame.transform.smoothscale(texture,(w,h))
                surface.set_alpha(38)
                art.blit(surface,(0,0))
            except (OSError,pygame.error):
                pass
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
            (pygame.Rect(82,90,983,315),(58,38,25,206)),
            (pygame.Rect(82,406,983,310),(61,41,27,209)),
            (pygame.Rect(82,713,983,246),(69,45,28,216))):
            pygame.draw.rect(overlays,c,rect,border_radius=21)
            pygame.draw.rect(overlays,(198,151,93,48),rect,1,border_radius=21)
        # Edge vignette using narrow translucent strokes, no expensive blur.
        for n in range(33):
            alpha=int((33-n)*1.35)
            r=pygame.Rect(n*2,n*2,w-n*4,h-n*4)
            if r.width>0 and r.height>0:
                pygame.draw.rect(overlays,(*TAVERN_SHADOW,alpha),r,2,border_radius=15)
        art.blit(overlays,(0,0))
        return art

    def ornament(self,screen,x,y,width=310,height=28):
        """Small genuine tavern gold divider, never used beneath card text."""
        key=('divider',int(width),int(height))
        if key not in self._textures:
            file=ASSET_ROOT/'gold_divider.png'
            if file.is_file():
                try:
                    img=pygame.image.load(str(file)).convert_alpha()
                    self._textures[key]=pygame.transform.smoothscale(
                        img,(int(width),int(height)))
                except (OSError,pygame.error):
                    self._textures[key]=None
            else:
                self._textures[key]=None
        sprite=self._textures[key]
        if sprite is not None:
            screen.blit(sprite,(int(x),int(y)))

    def carved_panel(self,screen,rect,opacity=215):
        """Detailed wood-and-gold carving behind auction/menu text only."""
        path=ASSET_ROOT/'tavern_panel.png'
        key=('carved',rect.size)
        if key not in self._textures:
            try:
                raw=pygame.image.load(str(path)).convert_alpha()
                self._textures[key]=pygame.transform.smoothscale(raw,rect.size)
            except (OSError,pygame.error):
                self._textures[key]=None
        panel=self._textures[key]
        if panel is not None:
            tile=panel.copy()
            tile.set_alpha(max(0,min(255,opacity)))
            screen.blit(tile,rect)

    def tavern_plaque(self,screen,rect):
        path=ASSET_ROOT/'tavern_plaque.png'
        key=('plaque',rect.size)
        if key not in self._textures:
            try:
                raw=pygame.image.load(str(path)).convert_alpha()
                self._textures[key]=pygame.transform.smoothscale(raw,rect.size)
            except (OSError,pygame.error):
                self._textures[key]=None
        if self._textures[key] is not None:
            screen.blit(self._textures[key],rect)

    def panel(self,screen,rect,fill=None,line=None,radius=12):
        base=fill or TAVERN_PANEL_BG
        # Allow chosen browns to show through instead of flattening all
        # overlays into near-black. Keep cool faction borders intact.
        base=tuple(int(channel*.78+wood*.22)
                   for channel,wood in zip(base,TAVERN_PANEL_BG))
        accent=line or BRASS
        shadow=pygame.Surface((rect.width+12,rect.height+12),pygame.SRCALPHA)
        pygame.draw.rect(shadow,(*TAVERN_SHADOW,88),
                         pygame.Rect(6,7,rect.width,rect.height),
                         border_radius=radius+1)
        screen.blit(shadow,(rect.x-6,rect.y-5))
        pygame.draw.rect(screen,TAVERN_SHADOW,rect,border_radius=radius)
        core=rect.inflate(-2,-2)
        pygame.draw.rect(screen,base,core,border_radius=max(2,radius-2))
        # Bevel: bronze highlights at the upper edge; recessed bottom.
        pygame.draw.line(screen,tuple(min(255,c+24) for c in base),
                         (rect.left+radius,rect.top+2),
                         (rect.right-radius,rect.top+2),1)
        pygame.draw.line(screen,(36,25,14),
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
            base=(96,69,43) if not hover else (125,86,52)
            edge=(221,166,88)
        else:
            base=(69,48,33) if not hover else (99,67,40)
            edge=(187,139,73) if hover else (118,91,59)
        if pressed and active:
            base=tuple(max(0,c-12) for c in base)
        self.panel(screen,rect,base,edge,9)
        if active and rect.height>22:
            pygame.draw.line(screen,(129,156,151) if hover else (88,111,111),
                             (rect.x+13,rect.y+5),(rect.right-13,rect.y+5),1)

    def slot(self,screen,rect,owner=0):
        accent=PLAYER if owner==0 else ENEMY
        self.panel(screen,rect,(43,34,27),accent,12)
        inner=rect.inflate(-12,-12)
        pygame.draw.rect(screen,(38,29,22),inner,border_radius=9)
        pygame.draw.rect(screen,(95,68,42),inner,1,border_radius=9)
        # Small corner-line engraving; never under a placed card's labels.
        for sx in (rect.x+11,rect.right-11):
            for sy in (rect.y+11,rect.bottom-11):
                dx=1 if sx<rect.centerx else -1
                dy=1 if sy<rect.centery else -1
                pygame.draw.line(screen,BRASS,(sx,sy),(sx+dx*9,sy),1)
                pygame.draw.line(screen,BRASS,(sx,sy),(sx,sy+dy*9),1)

    def legendary_underlay(self,screen,rect):
        """Dark amethyst velvet below artwork and opaque text/stat panels.

        Only the card gutters remain visible. This never changes cached art,
        labels, faction colors or gameplay state.
        """
        key=('legendary_underlay',rect.size)
        if key not in self._textures:
            w,h=rect.size
            tile=pygame.Surface((w,h),pygame.SRCALPHA)
            pygame.draw.rect(tile,(51,27,48,246),
                             pygame.Rect(2,2,w-4,h-4),border_radius=10)
            # Two fine side rails stay outside the card's content zones.
            for x in (3,w-4):
                pygame.draw.line(tile,(168,100,62,170),
                                 (x,13),(x,h-14),1)
            pygame.draw.rect(tile,(232,172,79,113),
                             pygame.Rect(4,4,w-8,h-8),1,border_radius=9)
            self._textures[key]=tile
        screen.blit(self._textures[key],rect.topleft)

    def legendary_artwork(self,screen,rect,animate=True):
        """A warm amethyst/gold art treatment, limited to the illustration.

        The image itself is not replaced. Family emblems, statuses, card name,
        ability panel, progression and opaque ATK/HP plates are drawn later.
        """
        key=('legendary_art',rect.size)
        if key not in self._textures:
            w,h=rect.size
            overlay=pygame.Surface((w,h),pygame.SRCALPHA)
            for y in range(h):
                depth=y/max(1,h-1)
                color=(78+int(depth*39),34+int(depth*23),
                       73-int(depth*29),15+int(depth*15))
                pygame.draw.line(overlay,color,(0,y),(w-1,y),1)
            # Rays and a restrained brass mandorla mark the art as legendary.
            for x in (int(w*.12),int(w*.88)):
                pygame.draw.line(overlay,(242,191,95,39),
                                 (x,2),(w//2,max(5,h-3)),1)
            if w>=95 and h>=33:
                pygame.draw.arc(overlay,(250,205,110,80),
                                pygame.Rect(8,3,w-16,max(7,h-6)),
                                .22,2.92,1)
            pygame.draw.rect(overlay,(247,199,93,85),
                             pygame.Rect(0,0,w,h),1,border_radius=4)
            self._textures[key]=overlay
        screen.blit(self._textures[key],rect.topleft)
        if animate and rect.width>=80 and rect.height>=35:
            # Barely perceptible light, always within the artwork area.
            strength=.5+.5*math.sin(pygame.time.get_ticks()/1320)
            shine=pygame.Surface((rect.width,rect.height),pygame.SRCALPHA)
            pygame.draw.line(shine,(255,221,138,round(15+strength*24)),
                             (7,2),(rect.width-8,2),2)
            screen.blit(shine,rect.topleft)

    def legendary_offer_ornament(self,screen,rect,animate=True):
        """A recognizable auction-card motif behind, never above, the copy."""
        key=('legendary_offer',rect.size)
        if key not in self._textures:
            w,h=rect.size
            tile=pygame.Surface((w,h),pygame.SRCALPHA)
            corner=min(63,w//4,h//4)
            # Velvet-and-gold corners, with a clear center for all labels.
            for left in (True,False):
                edge=0 if left else w-1
                sign=1 if left else -1
                pygame.draw.polygon(tile,(88,37,63,112),
                                    [(edge,0),(edge+sign*corner,0),
                                     (edge,corner)])
                pygame.draw.lines(tile,(250,201,111,132),False,
                                  [(edge+sign*7,corner//2),
                                   (edge+sign*7,7),
                                   (edge+sign*corner//2,7)],2)
                pygame.draw.circle(tile,(254,220,143,179),
                                   (edge+sign*15,15),3,1)
                pygame.draw.line(tile,(215,143,64,70),
                                 (edge+sign*8,h-42),(edge+sign*8,h-10),1)
            pygame.draw.line(tile,(243,193,99,123),
                             (w//2-29,h-8),(w//2+29,h-8),2)
            self._textures[key]=tile
        screen.blit(self._textures[key],rect.topleft)
        self.rarity_frame(screen,rect,'legendarna',animate=animate)

    def rarity_frame(self,screen,rect,tier,animate=True):
        """Edge-only rarity: subtle bronze, silver-blue, ornate gold.

        The unit's selection/attack/readiness outline is drawn separately,
        after this frame. Never fill over opaque name/ATK/PŻ panels.
        """
        from game.ui.rarity_view import rarity_color
        shade=rarity_color(tier)
        if tier=='podstawowa':
            pygame.draw.rect(screen,shade,rect,2,border_radius=11)
            return
        if tier=='rzadka':
            pygame.draw.rect(screen,(56,77,118),rect.inflate(2,2),
                             3,border_radius=12)
            pygame.draw.rect(screen,shade,rect,2,border_radius=11)
            for corner in ((rect.left+8,rect.top+8),(rect.right-9,rect.top+8),
                           (rect.left+8,rect.bottom-9),(rect.right-9,rect.bottom-9)):
                pygame.draw.circle(screen,(205,223,251),corner,2)
            return
        if tier!='legendarna':return
        pygame.draw.rect(screen,(139,90,26),rect.inflate(6,6),
                         5,border_radius=14)
        pygame.draw.rect(screen,shade,rect.inflate(3,3),
                         3,border_radius=12)
        pygame.draw.rect(screen,(255,226,135),rect.inflate(-3,-3),
                         1,border_radius=10)
        # Four corner engravings + an animated gemstone on the external edge.
        for x,direction in ((rect.left,-1),(rect.right,1)):
            for y,vertical in ((rect.top,-1),(rect.bottom,1)):
                pts=[(x+direction*5,y+vertical*5),
                     (x-direction*8,y+vertical*5),
                     (x+direction*5,y-vertical*8)]
                pygame.draw.lines(screen,(255,225,133),False,pts,2)
        center=(rect.centerx,rect.top-3)
        color=(255,238,161)
        if animate:
            glow=.5+.5*math.sin(pygame.time.get_ticks()/1050)
            color=tuple(min(255,int(a+glow*(255-a))) for a in shade)
        pygame.draw.polygon(screen,(140,93,33),
                            [(center[0],center[1]-6),(center[0]+8,center[1]),
                             (center[0],center[1]+6),(center[0]-8,center[1])])
        pygame.draw.polygon(screen,color,
                            [(center[0],center[1]-4),(center[0]+5,center[1]),
                             (center[0],center[1]+4),(center[0]-5,center[1])])

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
