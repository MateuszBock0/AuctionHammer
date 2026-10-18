"""Zrzuty nowego interfejsu do weryfikacji w Windows CI.

Wszystkie statystyki i opisy kart są renderowane przez Pygame. Nie ma
napisów ani wartości w ilustracjach PNG.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.models import Unit
from game.core.status_view import VisibleStatus
from game.ui.card_view import CardView

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'preview'
DEST.mkdir(exist_ok=True)

pygame.init()
pygame.display.set_mode((700,640))
view=CardView()
game=Match(911)
elven=game.cards['S01']
elven.hand_turns=2
elven.owner=0
human=game.cards['S115']
unit=Unit('S115',0,8,6,4,0,0,attacks=1,armor_perm=3,shield=1)
statuses=[
    VisibleStatus('poison','TRUC','Trucizna','2 obrażenia przez 3 aktywacje','S83'),
    VisibleStatus('shield','TARCZ','Tarcza','1 ładunek','S20'),
    VisibleStatus('armor','P3','Pancerz trwały','3 punkty','S82'),
    VisibleStatus('double','2×','Podwójny atak','Maksymalnie dwa ataki w turze','S115'),
]

sizes=(('REKA_125x195',125,195),('PLANSZA_148x220',148,220),
       ('SZCZEGOLY_255x380',255,380))
for uid,card in (('S01',elven),('S115',human)):
    for label,width,height in sizes:
        image=pygame.Surface((width+20,height+20))
        image.fill((12,19,29))
        view.draw(image,card,pygame.Rect(10,10,width,height),
                  unit=unit if uid=='S115' and label!='REKA_125x195' else None,
                  statuses=statuses if uid=='S115' and label!='REKA_125x195' else (),
                  ready=uid=='S115' and label!='REKA_125x195',
                  attacks_remaining=1,attacks_total=2)
        pygame.image.save(image,DEST/f'{uid}_{label}.png')

# Porównanie całej rodziny: 3 rzeczywiste wymiary, bez powiększania.
canvas=pygame.Surface((790,485))
canvas.fill((13,21,31))
title=pygame.font.SysFont('segoeui',23,bold=True)
caption=pygame.font.SysFont('segoeui',13)
canvas.blit(title.render('AUCTIONHAMMER — MINIMAL FANTASY',True,(243,237,217)),(22,10))
for i,(label,w,h) in enumerate(sizes):
    x=(15,180,395)[i]
    pygame.draw.rect(canvas,(28,44,57),pygame.Rect(x,48,w+18,h+19),border_radius=10)
    view.draw(canvas,elven,pygame.Rect(x+9,57,w,h))
    text=caption.render(f'{w} × {h} px',True,(180,198,211))
    canvas.blit(text,(x+8,58+h+3))
pygame.image.save(canvas,DEST/'MINIMAL_FANTASY_POROWNANIE.png')
# Komplet 70 kart: rzeczywisty renderer i wszystkie trzy wymiary.
# Pojedyncze arkusze służą porównaniu hierarchii tekstów, celów i statystyk.
for label,width,height in sizes:
    cols=7
    rows=10
    pitch_x=width+14
    pitch_y=height+29
    sheet=pygame.Surface((cols*pitch_x+14,rows*pitch_y+45))
    sheet.fill((13,21,31))
    top=pygame.font.SysFont('segoeui',20,bold=True)
    sheet.blit(top.render(f'70 KART V19 — {width} × {height}',True,(243,237,217)),(14,8))
    tiny=pygame.font.SysFont('segoeui',12)
    for index,card in enumerate(game.cards.values()):
        row,col=divmod(index,cols)
        x,y=8+col*pitch_x,43+row*pitch_y
        sheet.blit(tiny.render(card.definition.id,True,(225,225,221)),(x+6,y-14))
        view.draw(sheet,card,pygame.Rect(x,y,width,height))
    pygame.image.save(sheet,DEST/f'KATALOG_70_{label}.png')

pygame.quit()
print('Utworzono 10 obrazów podglądu Pygame w folderze preview.')
