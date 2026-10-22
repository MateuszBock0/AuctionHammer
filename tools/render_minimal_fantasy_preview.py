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
# Zdjęcie regresyjne odpowiadające zgłoszeniu: S64 i S09, trzy formaty.
# Oryginalny renderer, prawdziwe karty i bieżąca specyfikacja v19.
comparison=pygame.Surface((1280,510))
comparison.fill((13,21,31))
comparison.blit(title.render('POPRAWKA CZYTELNOŚCI — ODPORNOŚĆ I OBRAŻENIA',True,
                             (243,237,217)),(20,12))
for x,tag,w,h in ((16,'REKA',125,195),(325,'PLANSZA',148,220),
                  (691,'SZCZEGOLY',255,380)):
    comparison.blit(caption.render(f'{tag}: {w}×{h}',True,(203,224,232)),
                    (x+8,56))
    for ix,uid in enumerate(('S64','S09')):
        xx=x+ix*(w+16)
        comparison.blit(caption.render(uid,True,(203,224,232)),(xx+7,82))
        view.draw(comparison,game.cards[uid],pygame.Rect(xx,106,w,h))
pygame.image.save(comparison,DEST/'S64_S09_CZYTELNOSC_0913.png')

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

# Zrzuty rzeczywistej aplikacji: menu, historia, powtórka i VFX.
from game.ui.app import SoloApp
from game.core.models import Unit
app=SoloApp(start_in_menu=True)
app.draw()
pygame.image.save(app.screen,DEST/'GAME_EXPERIENCE_MENU_0914.png')
app.menu_open=False
app.game._log('Mag Zorzy atakuje: Dwugłowa Hiena.')
app.game._log('Bohater traci 3 PŻ; trucizna zostaje nałożona.')
app.history_open=True
app.draw()
pygame.image.save(app.screen,DEST/'GAME_EXPERIENCE_HISTORIA_0914.png')
app.history_open=False
# Use the same engine placement method as real gameplay; test fixtures must
# not bypass the physical slot registry introduced in 0.9.51.
app.game.units['S115']=Unit('S115',0,3,8,8,1,0,attacks=1,shield=1)
app.game.cards['S115'].owner=0
app.game.cards['S115'].zone='board'
for player in app.game.players:
    for container in (player.hand,player.deck,player.grave,player.board):
        if 'S115' in container:
            container.remove('S115')
if 'S115' in app.game.bank:
    app.game.bank.remove('S115')
app.game._place_on_board('S115',0,slot=3)
app.combat_visuals.sync(app.game,app.slot_rect,app.hero_rect,1000)
app.game.units['S115'].hp=5
app.game.units['S115'].shield=0
app.game._log('Mistrz Dwóch Ostrzy otrzymuje 3 obrażenia.')
app.combat_visuals.sync(app.game,app.slot_rect,app.hero_rect,1010)
app.recorder.capture(app.game)
app.animations_enabled=True
app.screen.blit(app.bg,(0,0))
app._draw_header()
app._draw_board()
app._draw_sidebar()
app.combat_visuals.draw(app.screen,1250,app.fonts_bold[16])
pygame.image.save(app.screen,DEST/'GAME_EXPERIENCE_EFEKTY_0914.png')
app.replay_index=app.recorder.last_index
app.draw()
pygame.image.save(app.screen,DEST/'GAME_EXPERIENCE_POWTORKA_0914.png')

# Audyt wszystkich 35 ikon w rzeczywistych rozmiarach interfejsu.
from game.ui.game_icons import GameIcons, ATLAS_FILES, FAMILY, FACTION
icons=GameIcons()
atlas_sheet=pygame.Surface((1000,815))
atlas_sheet.fill((13,21,31))
atlas_sheet.blit(title.render('35 IKON MINIMAL FANTASY — 40 PX ATLAS',True,
                              (243,237,217)),(18,12))
atlas_sheet.blit(caption.render('Po lewej rozmiar karty 13 px, dalej 20 px i podgląd 40 px',True,
                                (180,202,214)),(18,48))
for index,entry in enumerate(ATLAS_FILES):
    cat,key=entry.split('/')
    if cat=='zdolnosci':
        group='families'
        lookup=next(k for k,v in FAMILY.items() if v==key)
    elif cat=='frakcje':
        group='factions'
        lookup=next(k for k,v in FACTION.items() if v==key)
    else:
        group='statuses'
        lookup=key
    column,row=index%5,index//5
    x,y=14+column*197,80+row*104
    pygame.draw.rect(atlas_sheet,(39,56,67),pygame.Rect(x,y,189,98),border_radius=8)
    atlas_sheet.blit(caption.render(view.clip(key,caption,166),True,
                                   (228,234,235)),(x+11,y+8))
    for delta,icon_size in ((14,13),(70,20),(130,40)):
        glyph=icons.get(lookup,group,icon_size)
        if glyph is not None:
            atlas_sheet.blit(glyph,(x+delta,y+39+(40-icon_size)//2))
pygame.image.save(atlas_sheet,DEST/'IKONY_35_WYSOKA_JAKOSC_0915.png')

# 0.9.16 — rzeczywiste zrzuty wszystkich kluczowych ekranów.
from game.ui.layout import preferred_window_size, fitted_viewport
app=SoloApp()
app.menu_open=False
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_PLANSZA.png')
for factor,label in ((1.,'100'),(1.25,'125'),(1.5,'150')):
    physical=(round(1920/factor),round(1080/factor))
    target=pygame.Surface(physical)
    target.fill((5,9,14))
    vp=pygame.Rect(*fitted_viewport(physical,(1480,980)))
    target.blit(pygame.transform.smoothscale(app.screen,vp.size),vp.topleft)
    pygame.image.save(target,DEST/f'VISUAL_0916_DPI_{label}.png')
app.menu_open=True
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_MENU.png')
app.menu_open=False
app.menu_page='settings'
app.menu_open=True
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_USTAWIENIA.png')
app.menu_open=False
app.details_card=app.game.players[0].hand[0]
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_KARTA_DETALE.png')
app.details_card=None
for i in range(27):
    app.game._log(f'Zdarzenie testowe {i}: efekt obrażeń, leczenia, pancerza i statusu.')
app.history_open=True
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_HISTORIA.png')
app.history_open=False
t=pygame.time.get_ticks()
app.combat_visuals._push('attack',(575,225),t,origin=(575,539))
app.combat_visuals._push('damage',(515,205),t,'-5')
app.combat_visuals._push('heal',(638,526),t,'+3')
app.combat_visuals._push('shield',(716,535),t,'TARCZA')
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_ANIMACJE.png')
app.combat_visuals.pulses.clear()
app.replay_index=app.recorder.last_index
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_POWTORKA.png')
app.replay_index=None
app.game.phase='finished'
app.game.winner=0
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0916_KONIEC.png')
# One separate UI regression screenshot: real engine HP remains -5 while
# the player's visible HP counter and end-screen summary show 0.
app.game.winner=1
app.game.players[0].hp=-5
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0918_KONIEC_0_PZ.png')
if app.game.players[0].hp!=-5:
    raise AssertionError('Render must not change the authoritative hero HP')

# 0.9.19 — real pygame snapshots for both auction stages, plus wood texture.
from game.core.engine import Match
auction_match=Match(191919,auctions_enabled=True,auction_catalog='placeholders')
auction_match.finish_mulligan(0,[])
auction_match.finish_mulligan(1,[])
for _ in range(6):
    if auction_match.phase=='auction':
        break
    auction_match.end_turn()
assert auction_match.phase=='auction'
app.game=auction_match
app.menu_open=False
app.replay_index=None
app.history_open=False
app.details_card=None
app._audit_notice=''
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0919_AUKCJA_LICYTACJA.png')
auction_match.auction_pass(auction_match.auction.turn)
auction_match.auction_pass(auction_match.auction.turn)
assert auction_match.auction.phase=='picking'
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0919_AUKCJA_WYBOR_KART.png')
first=auction_match.auction.turn
auction_match.auction_pick(first,auction_match.auction.offers[2].uid)
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0919_AUKCJA_WYBOR_PO_1.png')
auction_match.auction_pick(auction_match.auction.turn,
                           auction_match.auction.offers[0].uid)
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0919_TAWERNA_PLANSZA.png')
# Real purchased placeholder card (including non-scaling cue) in all sizes.
from game.ui.card_view import CardView
sheet=pygame.Surface((680,465))
sheet.fill((22,30,34))
cv=CardView()
uid=auction_match.auction_history[0]['picks'][first]
card=auction_match.cards[uid]
for rect in (pygame.Rect(22,34,125,195),
             pygame.Rect(170,34,148,220),
             pygame.Rect(355,34,255,380)):
    cv.draw(sheet,card,rect)
pygame.image.save(sheet,DEST/'VISUAL_0919_STRAZNIK_3_ROZMIARY.png')

# 0.9.20 — exact Tavern scene/menu with the real source textures.
app=SoloApp()
app.menu_open=False
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0920_TAWERNA_PELNA_PLANSZA.png')
app.menu_open=True
app.menu_page='main'
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0920_DREWNIANE_MENU.png')
app.menu_open=False
app.game=auction_match
app.game.phase='auction' if app.game.auction else app.game.phase
# Use a fresh match to keep real auction state after previous preview choices.
app.game=Match(202020,auctions_enabled=True,auction_catalog='placeholders')
app.game.finish_mulligan(0,[])
app.game.finish_mulligan(1,[])
for _ in range(6):
    if app.game.phase=='auction':break
    app.game.end_turn()
assert app.game.phase=='auction'
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0920_DREWNIANA_AUKCJA.png')

# 0.9.21 — show three distinct v3 archetypes and evolving rarity,
# explicitly marking all complex abilities as planned/inactive.
from game.core.auction_catalog import CATALOG
stage=Match(212121,auctions_enabled=True)
for player in (0,1):
    if stage.phase=='mulligan':stage.finish_mulligan(player,[])
for _ in range(6):
    if stage.phase=='auction':break
    stage.end_turn()
assert stage.phase=='auction'
assert len({x.archetype for x in stage.auction.offers})==3
app.game=stage
app.menu_open=False
app.draw()
pygame.image.save(app.screen,DEST/'VISUAL_0921_KATALOG_12_OFERTY.png')
stage.auction_pass(stage.auction.turn)
stage.auction_pass(stage.auction.turn)
stage.auction_pick(stage.auction.turn,stage.auction.offers[0].uid)
stage.auction_pick(stage.auction.turn,stage.auction.offers[1].uid)
uid=stage.auction_history[-1]['picks'][stage.auction_history[-1]['winner']]
sheet=pygame.Surface((680,465))
sheet.fill((25,20,16))
cv=CardView()
for rect in (pygame.Rect(22,34,125,195),
             pygame.Rect(170,34,148,220),
             pygame.Rect(355,34,255,380)):
    cv.draw(sheet,stage.cards[uid],rect)
pygame.image.save(sheet,DEST/'VISUAL_0921_NIEAKTYWNE_ZDOLNOSCI_KART.png')

pygame.quit()
print('Utworzono 37 obrazów podglądu Pygame w folderze preview.')
