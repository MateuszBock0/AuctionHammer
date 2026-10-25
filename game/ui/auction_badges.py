"""Tiny fixed-grid icons for auction triggers — pixel art, no font glyphs."""
from __future__ import annotations

import pygame

# 5x5 silhouettes. The source's actual trigger, not a guessed card class,
# selects the glyph. Unknown/archived archetypes use the neutral square.
PIXELS = {
    "death": (
        "01110", "10101", "11111", "11011", "10101",
    ),
    "play": (
        "00100", "01110", "11111", "00100", "01110",
    ),
    "end": (
        "11111", "10001", "01110", "00100", "11111",
    ),
    "passive": (
        "00100", "01110", "11111", "01110", "00100",
    ),
}
TRIGGER_NAMES = {
    "death": "PRZY ŚMIERCI",
    "play": "PRZY ZAGRANIU",
    "end": "KONIEC TURY",
    "passive": "PASYWNA",
}


def draw_trigger_icon(screen: pygame.Surface, rect: pygame.Rect,
                      trigger: str) -> None:
    """Render five-pixel 8-bit glyph centered in a bordered dark tile."""
    pattern=PIXELS.get(trigger,("11111", "10001", "10001", "10001", "11111"))
    pygame.draw.rect(screen,(29,38,43),rect)
    pygame.draw.rect(screen,(145,128,94),rect,1)
    scale=max(1,min((rect.width-4)//5,(rect.height-4)//5))
    left=rect.centerx-(5*scale)//2
    top=rect.centery-(5*scale)//2
    for y,line in enumerate(pattern):
        for x,pixel in enumerate(line):
            if pixel=="1":
                pygame.draw.rect(screen,(239,204,144),
                                 (left+x*scale,top+y*scale,scale,scale))
