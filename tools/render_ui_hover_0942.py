"""Offscreen review screenshots for the unmodified tavern art and UI 0.9.42.

This renders actual Pygame screens; it neither simulates user approvals nor
changes the canonical 70-card catalog, seven PNGs or gameplay engine.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import pygame
from game.core.engine import Match
from game.ui.app import SoloApp
from game.ui.card_view import card_zones

DEST=Path(__file__).resolve().parents[1]/'preview'/'ui_0942'
DEST.mkdir(parents=True,exist_ok=True)

def new_match(first=0):
    for seed in range(42000,42200):
        g=Match(seed,audit_enabled=True,auctions_enabled=True,
                auction_catalog='v22',
                starting_compensation='choice_2_5_or_coins')
        if g.first==first:
            return g
    raise RuntimeError('Could not find matching starting seat')

def capture(app,name,point=(-10000,-10000),time_ms=10000):
    with patch.object(app,'mouse_pos',return_value=point):
        with patch('game.ui.app.pygame.time.get_ticks',return_value=time_ms):
            app.draw()
    dest=DEST/name
    pygame.image.save(app.screen,dest)
    print(dest,flush=True)

pygame.init()
with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
    app=SoloApp(start_in_menu=True)
app.menu_open=False

app.game=new_match(first=1)
app.selected=None
capture(app,'01_wybor_rekompensaty_tawerna.png')

app.game=new_match(first=0)
app._hover_uid=None
app._hover_start_ms=0
uid,area=next(iter(app.hand_layout().items()))
app._update_hover_target(area.center,now=1000)
capture(app,'02_duzy_podglad_karty_po_najechaniu.png',point=area.center,time_ms=1500)

app.game.cards[uid].quick_on_first_summon=True
app._hover_uid=None
pos=(area.x+1,card_zones(area)['art'].y)
capture(app,'03_wyjasnienie_statusu_i_zrodla.png',point=pos,time_ms=1500)

app.game.finish_mulligan(0,[])
app.game.finish_mulligan(1,[])
capture(app,'04_legalne_akcje_karty_i_tura.png')
pygame.quit()
