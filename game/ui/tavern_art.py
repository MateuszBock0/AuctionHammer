"""Board-mounted candle and overturned ale sprite art, v0.9.98.

The pixel atlas is hand-isolated from the approved 0.9.98 tavern-board image,
indexed to a 48-colour pixel palette, with hard transparent edges. It is stored
as a small compressed ASCII asset so the Python/Windows release bundles it
without image format plugins, external dependencies or a new download.

All flame, pour and spread are decorative pixel-aligned draws using the
existing fixed Pygame board projection and are NEVER gameplay actions.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
import zlib

import pygame

from game.ui.beer_fx import candle_frame

_ATLAS = Path(__file__).resolve().parents[2] / 'assets/ui/tavern_board_props.pxart'
# Source regions of the (86x216) RGBA pixel sheet, in logical pixels.
_CANDLE=pygame.Rect(0,0,70,64)
_FLAME=pygame.Rect(53,71,32,44)
_MUG=pygame.Rect(4,139,76,75)

# White foam, bright beer, and candlelit 16/32-bit tavern palette.
_DARK=(34,20,14)
_WOOD=(89,45,24)
_WOOD_LIGHT=(148,78,35)
_BRASS=(187,116,48)
_GOLD=(250,191,76)
_BEER=(220,128,35)
_BEER_LIGHT=(252,187,64)
_FOAM=(255,232,178)
_EMBER=(248,100,29)


@lru_cache(maxsize=1)
def load_tavern_sprites():
    """Decode the trusted, versioned RGBA pixel atlas once, before draw loops."""
    lines=_ATLAS.read_text(encoding='ascii').splitlines()
    magic,w,h,colors=lines[0].split()
    if magic!='PXART-1' or (int(w),int(h),int(colors))!=(86,216,48):
        raise ValueError('Invalid AuctionHammer pixel tavern atlas header')
    raw=zlib.decompress(base64.b85decode(lines[1]))
    palette_size=int(colors)*3
    palette=raw[:palette_size]
    indices=raw[palette_size:]
    if len(indices)!=int(w)*int(h) or len(palette)!=palette_size:
        raise ValueError('Invalid pixel tavern atlas payload')
    rgba=bytearray(len(indices)*4)
    for i,index in enumerate(indices):
        if index==255:
            continue
        j=i*4
        rgba[j:j+3]=palette[index*3:index*3+3]
        rgba[j+3]=255
    sheet=pygame.image.fromstring(bytes(rgba),(int(w),int(h)),'RGBA')
    return tuple(sheet.subsurface(r).copy() for r in (_CANDLE,_FLAME,_MUG))


def _sq(screen,c,x,y,w,h):
    pygame.draw.rect(screen,c,(int(x),int(y),int(w),int(h)))


def _poly(screen,c,points):
    pygame.draw.polygon(screen,c,[(int(px),int(py)) for px,py in points])


def _mount(screen,x):
    """Wedge/bronze frame is bolted TO the board edge, not a floating torch HUD.

    Side X=57/1020 comes from the existing 1480x980 logical board. A shaded
    bevel bridges the recessed side to the board while cards remain untouched.
    """
    left=x<500
    d=1 if left else -1
    center=x+(11 if left else 0)
    def pt(a,y):
        return (center+d*a,y)
    # Quarter-view wood rim protrudes INWARDS; fine grain & stepped shadows.
    _poly(screen,(29,22,18),[pt(-32,350),pt(28,349),pt(48,357),
                            pt(48,433),pt(31,443),pt(-30,438)])
    _poly(screen,(79,42,23),[pt(-28,353),pt(24,352),pt(41,361),
                            pt(41,431),pt(28,437),pt(-27,434)])
    _poly(screen,(124,67,30),[pt(-24,354),pt(20,353),pt(38,362),
                             pt(38,368),pt(-24,363)])
    _poly(screen,(52,34,23),[pt(35,369),pt(43,361),pt(43,433),
                            pt(33,441)])
    for offset in (-15,0,15):
        _sq(screen,(114,66,33),*pt(offset,384),2,20)
        _sq(screen,(145,88,44),*pt(offset+3,393),2,12)
    # Real board corner: a continuous brass edge reaches towards its field.
    pygame.draw.lines(screen,(245,172,70),False,
                      [pt(-27,352),pt(21,352),pt(41,361)],3)
    pygame.draw.lines(screen,(69,42,27),False,
                      [pt(42,368),pt(42,434),pt(29,442)],4)
    for yy in (359,436):
        cx,cy=pt(30,yy)
        pygame.draw.circle(screen,(59,38,26),(cx,cy),5)
        pygame.draw.circle(screen,(235,161,72),(cx-1,cy-1),3)
        _sq(screen,(255,207,119),cx-2,cy-3,2,2)
    return center,d


def _draw_candle(screen,center,d,now_ms,animate,splash):
    candle,flame,_=load_tavern_sprites()
    # One fairly large wax candle, *on the board's brass corner cup*.
    # 48 colours, crisp RGBA pixels; no flat polygon candle silhouettes.
    cimg=candle if d==-1 else pygame.transform.flip(candle,True,False)
    screen.blit(cimg,(center-34,295))
    fx,fy,fh=candle_frame(now_ms,animate,phase=0 if d==1 else 2)
    boost=round(7*max(0.0,min(1.0,splash))) if animate else 0
    if boost:
        # NEAREST: sprite stays pixel art, even during the flare.
        fire=pygame.transform.scale(flame,(32+boost,44+boost))
    else:
        fire=flame
    screen.blit(fire,(center-fire.get_width()//2+fx,
                      263-fire.get_height()+44+fy-fh))
    if boost:
        for i in range(3):
            px=center+d*(4+i*9)
            _sq(screen,(252,176,62),px,263-i*6,3,3)


def _draw_mug(screen,center,d,tilt):
    _,_,mug=load_tavern_sprites()
    # Sprite was composed facing left. Flip to face INTO the left board.
    original=mug if d==-1 else pygame.transform.flip(mug,True,False)
    # 4 quantised poses, no subpixel interpolation and no continuous wobble.
    pose=min(3,max(0,int(tilt*3.999)))
    deg=(24,16,8,0)[pose]
    image=pygame.transform.rotate(original,deg if d==-1 else -deg)
    pos=image.get_rect(center=(center-3*d,402))
    screen.blit(image,pos)


def draw_tavern_rail(screen,x,fill,pouring,progress,splash,
                     now_ms=0,animate=True,tilt=0.0):
    """Paint paired board-mounted props. Historical callers remain compatible."""
    center,d=_mount(screen,x)
    _draw_candle(screen,center,d,now_ms,animate,
                 splash if animate else 0.0)
    _draw_mug(screen,center,d,tilt if animate else 0.0)
    if pouring and animate:
        # A short foamy filler stream appears above the mug before tipping.
        fx=center+d*6
        top=367+round(5*progress)
        _sq(screen,_BEER_LIGHT,fx-2,top,4,10)
        _sq(screen,_FOAM,fx-2,top+10,6,3)


def _side_points(x):
    """Rim contact and inward flow, mirrored in real board coordinates."""
    # X=57 -> contact 105, flow to 105+150. X=1020 -> contact 992,
    # flow to 992-150. Both lie on the existing TOP edge of own card row.
    if x<500:
        return 105,1
    return 992,-1


def draw_board_spill(screen,x,pour,burn,now_ms=0):
    """Foam falls from the tipped mug and catches alight ON the board surface.

    Confined to 2D board bevel (y=427..441), first-card top art edge and outer
    margins. Never reaches health/status text, UI controls or combat hitboxes.
    Draws even during active burda as low embers. Can be fully disabled with A.
    """
    if pour<=0.0 and burn<=0.0:
        return
    rim,d=_side_points(x)
    phase=(max(0,int(now_ms))//125)%4
    if pour>0.0:
        extent=round(20+125*min(1.0,pour))
        # Animated visible pour FALLS from the mug to the board frame.
        startx=rim-d*19
        starty=391
        endx=rim+d*9
        yy=429
        pygame.draw.lines(screen,(94,49,22),False,
                          [(startx,starty),(rim-d*8,411),(endx,yy)],9)
        pygame.draw.lines(screen,_BEER,False,
                          [(startx,starty),(rim-d*8,411),(endx,yy)],6)
        pygame.draw.lines(screen,_BEER_LIGHT,False,
                          [(startx-d*2,starty),(rim-d*10,411),(endx-d*2,yy)],2)
        for step in range(0,extent,7):
            px=rim+d*step
            y=429+(step//14)%3
            # Flat angular puddle following the real board's horizontal edge.
            _sq(screen,(112,65,27),px,y,6,9)
            _sq(screen,_BEER,px,y+1,6,5)
            _sq(screen,_BEER_LIGHT,px+d*2,y+1,2,2)
            if step%28==0:
                _sq(screen,_FOAM,px,y+5,5,3)
        for i in range(7):
            offset=(i*29+phase*9)%max(20,extent)
            px=rim+d*offset
            py=422+(i*7+phase*3)%15
            _sq(screen,_FOAM if i%2 else _GOLD,px,py,3,3)
    if burn>0.0:
        # Fire is present at the candle's side board mount first, then runs
        # inward along the beer. Embers keep the effect alive for brawl turns.
        count=max(3,round(12*burn))
        for i in range(count):
            step=i*12
            px=rim+d*step
            base=435+(i%2)
            ht=3+round(burn*(5+(i*7+phase*3)%11))
            # Entire flame strip stays above the first card's *title/stat*
            # zones (all y<=438); its luminous tips are visible over board.
            _poly(screen,(105,38,19),[(px-d*6,base),(px-d*2,base-ht),
                                     (px+d*3,base-ht//2),(px+d*7,base)])
            _poly(screen,_EMBER,[(px-d*3,base),(px,base-ht),
                                (px+d*4,base)])
            if burn>0.5 and i%3==0:
                _sq(screen,(255,224,97),px,base-max(3,ht//2),3,4)
        # A few sparks rise ABOVE the board bevel, but never across hero HP.
        for i in range(3):
            sx=rim+d*(12+i*25+phase*3)
            sy=417-((i+phase)%3)*5
            _sq(screen,(242,118,43),sx,sy,2,3)
        # Right and left side trim remain visibly smouldering after the pour.
        _sq(screen,(162,73,32),rim-d*4,427,6,9)
