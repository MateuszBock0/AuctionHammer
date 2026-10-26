"""Decorative, nonblocking tavern rails; no card/hitbox geometry or assets."""
import pygame


def draw_tavern_rail(screen,x,fill,sway,flicker,pouring,progress,splash):
    """Decorate one of two existing 65px gutters in the 1080px canvas.

    When a paid mug finishes filling, BOTH calls receive the same splash
    strength. The effect cannot apply combat damage; Match owns the rules.
    """
    base=pygame.Rect(x-32,264,65,201)
    pygame.draw.rect(screen,(32,24,20),base,border_radius=7)
    pygame.draw.rect(screen,(101,64,35),base.inflate(-5,-5),border_radius=5)
    pygame.draw.rect(screen,(196,140,72),base,2,border_radius=7)
    for y in (283,326,362,440,452):
        pygame.draw.line(screen,(142,91,47),(x-24,y),(x+24,y),2)
    for vx in (-24,24):
        for vy in (274,455):
            pygame.draw.circle(screen,(228,182,97),(x+vx,vy),3)
            pygame.draw.circle(screen,(68,43,25),(x+vx+1,vy+1),1)

    # A wall-mounted brass and iron candle/torch integrated with the rail.
    pygame.draw.rect(screen,(42,43,43),(x-19,310,38,48))
    pygame.draw.rect(screen,(190,127,62),(x-16,314,32,40),3)
    pygame.draw.polygon(screen,(91,72,48),
                        [(x-7,317),(x-3,286),(x+3,286),(x+7,317)])
    pygame.draw.rect(screen,(241,187,101),(x-13,309,26,5))
    fx=x+sway
    raised=round(9*splash)
    pygame.draw.polygon(screen,(174,64,35),
        [(fx-18,310),(fx-12,289-flicker),(fx-5,296),
         (fx,277-raised),(fx+7,294),(fx+14,285-raised//2),
         (fx+18,308),(fx+6,319),(fx-10,317)])
    pygame.draw.polygon(screen,(249,136,45),
        [(fx-12,308),(fx-6,293),(fx+1,287-raised//2),
         (fx+9,307),(fx+7,315),(fx-8,314)])
    pygame.draw.polygon(screen,(255,217,110),
        [(fx-6,309),(fx-1,299-raised//3),
         (fx+5,309),(fx+1,315),(fx-4,314)])

    # Shelf and tankard share the same woodwork, with an ornate metal handle.
    pygame.draw.rect(screen,(53,35,25),(x-29,425,58,9))
    pygame.draw.rect(screen,(215,149,69),(x-30,423,60,5))
    mug=pygame.Rect(x-20,373,40,51)
    pygame.draw.rect(screen,(49,55,52),mug,border_radius=4)
    pygame.draw.rect(screen,(155,106,48),mug.inflate(-4,-3),border_radius=3)
    fill=max(1,min(38,int(fill)))
    top=mug.bottom-5-fill
    pygame.draw.rect(screen,(225,162,52),(mug.x+5,top,30,fill))
    pygame.draw.rect(screen,(254,206,85),(mug.x+8,top,5,fill))
    pygame.draw.rect(screen,(245,230,185),(mug.x+3,top-1,34,5))
    for px in (x-13,x-3,x+9):
        pygame.draw.circle(screen,(255,242,210),(px,top),4)
    pygame.draw.rect(screen,(214,171,101),mug,3,border_radius=4)
    pygame.draw.rect(screen,(233,190,120),
                     (mug.right-1,mug.y+10,12,28),4,border_radius=5)
    pygame.draw.rect(screen,(90,61,36),(mug.x+2,mug.y+31,36,6))
    pygame.draw.line(screen,(230,172,89),
                     (mug.x+5,mug.y+34),(mug.right-5,mug.y+34),2)
    if pouring:
        pygame.draw.rect(screen,(255,188,71),
                         (x-2,357+round(5*progress),5,15))
        pygame.draw.rect(screen,(250,230,174),(x-5,367,10,3))

    if splash>0.0:
        # Overflow and a simultaneous burst at both torch locations.
        # Remains within the decorative rail; never obscures board cards.
        travel=round((1-splash)*18)
        for direction in (-1,1):
            dx=direction*(23+travel)
            pygame.draw.circle(screen,(250,178,65),
                               (x+dx,top-6-round(7*splash)),3)
            pygame.draw.circle(screen,(255,222,116),
                               (x+dx+direction*4,top-11),2)
        pygame.draw.line(screen,(255,204,86),
                         (x-23,top-2),(x+24,top-2),2)
