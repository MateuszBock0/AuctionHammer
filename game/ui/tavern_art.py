"""Small pixel-art candle sconces and beer tankards along the tavern rails.

All drawing uses integer-aligned Pygame primitives at the fixed logical canvas
size. No new textures, alpha surfaces, blocking delays or gameplay changes.
The decoration never moves a card, a button or its clickable hitbox.
"""
from __future__ import annotations

import pygame

from game.ui.beer_fx import candle_frame


def _pixel(screen,color,x,y,w,h):
    """A square pixel-art color block, deliberately not antialiased."""
    pygame.draw.rect(screen,color,(int(x),int(y),int(w),int(h)))


def _wooden_rail(screen,x):
    # A warm, carved oak inset matches the tavern board; squared pixel joints.
    _pixel(screen,(27,22,19),x-33,263,66,203)
    _pixel(screen,(91,57,34),x-30,266,60,197)
    _pixel(screen,(122,77,43),x-26,270,52,189)
    _pixel(screen,(48,33,24),x-22,274,44,181)
    _pixel(screen,(77,49,31),x-19,276,38,176)
    for y in (276,350,367,439,455):
        _pixel(screen,(153,101,55),x-27,y,54,2)
        _pixel(screen,(60,36,25),x-26,y+3,52,2)
    for y,offset in ((291,-2),(327,3),(398,-4),(447,1)):
        _pixel(screen,(109,67,39),x-15+offset,y,22,2)
        _pixel(screen,(133,81,44),x-8+offset,y+5,14,2)
    # Riveted brass edge, corners use distinct staircase-style pixels.
    for sign in (-1,1):
        bx=x+sign*28
        _pixel(screen,(225,170,96),bx-1,279,3,157)
        for y in (273,459):
            _pixel(screen,(226,176,94),bx-4,y-3,7,7)
            _pixel(screen,(91,56,32),bx-1,y,2,2)
    _pixel(screen,(230,184,106),x-26,269,52,3)
    _pixel(screen,(230,184,106),x-26,458,52,3)


def _candle_flame(screen,cx,wick_top,frame,splash):
    """Blocky four-frame flame; brief shared flare after the beer fills."""
    dx,dy,delta=frame
    flare=round(4*max(0.0,min(1.0,splash)))
    tip=cx+dx
    peak=wick_top-19+dy-delta-flare
    # Two thin colored halo steps; not an expensive translucent glow surface.
    _pixel(screen,(96,57,35),tip-7,peak+5,15,13+flare)
    _pixel(screen,(151,76,35),tip-5,peak+3,11,14+flare)
    _pixel(screen,(217,110,37),tip-4,peak+2,9,13+flare)
    _pixel(screen,(251,161,48),tip-2,peak+1,6,11+flare)
    _pixel(screen,(255,219,108),tip-1,peak+5,4,7+flare)
    _pixel(screen,(255,243,169),tip,peak+8,2,4+flare)
    _pixel(screen,(255,199,75),tip,peak,2,3)
    if splash>0.0:
        # Same tick and same magnitude for the candles of BOTH side rails.
        _pixel(screen,(231,143,56),tip-9,peak+6,2,5)
        _pixel(screen,(250,184,72),tip+9,peak+8,2,4)


def _candle(screen,cx,top,height,frame,splash):
    # A visible wick, two shades of beeswax, three chunky wax drips.
    _pixel(screen,(49,38,29),cx-1,top-5,3,7)
    _candle_flame(screen,cx,top-5,frame,splash)
    _pixel(screen,(105,73,45),cx-8,top-1,16,height+2)
    _pixel(screen,(224,192,130),cx-6,top,13,height)
    _pixel(screen,(247,224,167),cx-3,top+2,5,height-5)
    _pixel(screen,(187,143,90),cx+4,top+2,3,height-3)
    # Uneven, blocky dripping wax makes the object a candle not a torch.
    _pixel(screen,(252,228,179),cx-7,top+5,3,10)
    _pixel(screen,(246,218,159),cx+5,top+6,3,13)
    _pixel(screen,(244,218,169),cx-2,top+13,3,9)
    _pixel(screen,(255,238,196),cx-6,top-1,12,3)


def _candle_sconce(screen,x,now_ms,animate,splash):
    # Brass fixture below two different-height candles; no moving mount.
    _pixel(screen,(35,36,33),x-23,334,46,19)
    _pixel(screen,(168,111,60),x-22,335,44,4)
    _pixel(screen,(239,182,102),x-22,339,44,3)
    _pixel(screen,(89,65,43),x-17,342,34,7)
    _pixel(screen,(206,150,80),x-19,350,38,4)
    _pixel(screen,(65,53,39),x-4,353,8,10)
    _pixel(screen,(184,125,63),x-7,358,14,4)
    # Separate phases make a gentle "living tavern" rather than a flashing icon.
    left=candle_frame(now_ms,animate,phase=0)
    right=candle_frame(now_ms,animate,phase=2)
    _candle(screen,x-12,310,27,left,splash)
    _candle(screen,x+11,317,20,right,splash)


def _beer_mug(screen,x,fill,pouring,progress,splash):
    # A simple wall shelf connects the tankard physically to the wooden rail.
    _pixel(screen,(41,32,25),x-29,425,58,11)
    _pixel(screen,(209,148,81),x-30,423,60,4)
    _pixel(screen,(122,78,44),x-27,429,54,3)
    top=416-max(1,min(37,int(fill)))
    # Black-square silhouette with a distinct stepped handle.
    _pixel(screen,(30,31,30),x-19,373,40,50)
    _pixel(screen,(70,57,41),x-16,377,34,43)
    _pixel(screen,(161,111,62),x-13,378,29,40)
    _pixel(screen,(66,52,37),x+19,386,11,4)
    _pixel(screen,(198,142,81),x+27,387,4,27)
    _pixel(screen,(204,150,86),x+20,412,11,4)
    _pixel(screen,(52,44,34),x+20,391,7,20)
    # Amber beer rises with the exact paid fill animation.
    _pixel(screen,(171,105,35),x-13,top,28,416-top)
    _pixel(screen,(232,160,48),x-10,top+1,24,max(1,415-top))
    _pixel(screen,(255,199,69),x-9,top+1,4,max(1,413-top))
    _pixel(screen,(245,225,168),x-15,top-2,31,4)
    for px,dy in ((-12,0),(-6,-3),(2,1),(9,-2)):
        _pixel(screen,(255,242,209),x+px,top-3+dy,7,5)
    # Brass rim and hammer marks: deliberately square and chunky.
    _pixel(screen,(233,179,107),x-19,375,38,3)
    _pixel(screen,(216,166,105),x-19,374,3,47)
    _pixel(screen,(221,170,105),x+16,377,3,43)
    _pixel(screen,(229,176,105),x-18,418,37,4)
    _pixel(screen,(85,57,38),x-14,402,31,7)
    _pixel(screen,(245,186,106),x-10,404,22,3)
    _pixel(screen,(110,73,42),x-2,406,6,2)
    if pouring:
        stream_y=352+round(5*progress)
        _pixel(screen,(255,188,68),x-2,stream_y,5,17)
        _pixel(screen,(255,231,156),x-4,stream_y+11,9,3)
    if splash>0.0:
        # Small 8-bit drops after the mug fills; confined to the empty gutter.
        travel=round((1-splash)*13)
        rise=round(6*splash)
        for sign in (-1,1):
            dx=sign*(23+travel)
            _pixel(screen,(247,178,60),x+dx-2,top-8-rise,5,5)
            _pixel(screen,(255,223,119),x+dx+sign*5,top-12,3,3)
        _pixel(screen,(255,210,105),x-21,top-5,42,3)


def draw_tavern_rail(screen,x,fill,pouring,progress,splash,
                     now_ms=0,animate=True):
    """Paint a pixel-art rail; both sides react to one confirmed paid mug.

    x is one of the preexisting decorative gutter centers (57 or 1020).
    All effects are visual. They cannot add damage, alter Match or move cards.
    """
    _wooden_rail(screen,x)
    _candle_sconce(screen,x,now_ms,animate,splash if animate else 0.0)
    _beer_mug(screen,x,fill,pouring and animate,progress,
              splash if animate else 0.0)
