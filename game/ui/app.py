"""AuctionHammer MVP 0.9.40: Chorazy 3/5 with versioned starter modes."""
from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path
import pygame
from game.ui.combat_visuals import CombatVisuals
from game.ui.music import FantasyTavernMusic
from game.ui.visual_theme import VisualTheme
from game.ui.match_history import MatchRecorder
from game.core.persistence import save_match, load_match, save_path
from game.core.audit import (audit_path, archive_path, list_archived_matches,
                             write_last_match, initialize_audit,
                             configure_audit_context, record_ai_difficulty)
from game import config as cfg
from game.core.engine import Match
from game.core.auction_catalog import CATALOG,RARITIES,live_variant,v23_variant,catalog_for
from game.core.ai import ComputerOpponent
from game.core.models import IllegalMove
from game.ui.card_view import CardView, FACTION_COLORS, ART
from game.ui.card_infographics import card_cue, highlighted_numeric_ranges
from game.ui.card_summary import ability_summary
from game.ui.v23_help import v23_base_card_note
from game.ui.attack_view import attack_display
from game.core.status_view import active_statuses, hand_grants, STATUS_COLORS
from game.ui.layout import fitted_viewport, window_to_canvas, preferred_window_size

class SoloApp:
    SIDEBAR_X=1082
    SLOT_W=148
    SLOT_H=220
    SLOT_GAP=26
    FIRST_X=107
    OPP_Y=152
    OWN_Y=431
    HAND_Y=746
    HAND_W=125
    HAND_H=195

    def __init__(self,start_in_menu=False):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        self.music = FantasyTavernMusic()
        # Fit the opening window to the current display, respecting Windows DPI
        # scaling and keeping room for the title bar and taskbar.
        # The internal canvas and all clickable hitboxes retain their v17 size.
        logical_size=(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT)
        desktop_size=self._desktop_resolution()
        self.windowed_size=preferred_window_size(desktop_size,logical_size)
        self.window=pygame.display.set_mode(self.windowed_size,pygame.RESIZABLE)
        self.screen=pygame.Surface(logical_size).convert()
        pygame.display.set_caption(cfg.WINDOW_TITLE)
        self.clock=pygame.time.Clock()
        self.fonts={n:pygame.font.SysFont('segoeui',n,bold=(n>=22)) for n in (11,12,13,14,15,16,18,20,22,28,34,46)}
        self.theme=VisualTheme()
        self.cards_view=CardView()
        self.fonts_bold={n:pygame.font.SysFont('segoeui',n,bold=True) for n in (13,14,16,18,20,22)}
        self.ai=ComputerOpponent()
        self.bg=self._create_background()
        self.animations_enabled=True
        self.restart()
        self.confirm_action=None
        self.confirm_error=''
        self.menu_open=bool(start_in_menu)
        self.menu_page='main'
        self.menu_message=''
        self._archive_records=[]
        self.archive_page=0
        self._archive_selected_record=None
        self.history_open=False
        self.history_scroll=0
        self.replay_index=None

    def restart(self):
        if hasattr(self,'game') and self.game.phase=='finished':
            self._export_finished_audit_once()
        self.game=Match(audit_enabled=True,auctions_enabled=True,
                        auction_catalog='v22',starting_compensation='choice_2_5_or_coins')
        configure_audit_context(self.game,self.ai.difficulty,fresh=True)
        self._audit_saved_match=None
        self._audit_notice=''
        self.auction_bid_text=''  # legacy UI compatibility only
        self.auction_slider_value=None
        self.auction_slider_key=None
        self.auction_slider_dragging=False
        self.auction_status=''
        self.ai.step(self.game)  # One audited command per step, even during mulligan.
        if self.game.phase=='mulligan' and 1 not in self.game.mulligan_done:
            # AI was second and chose its compensation; now finish its own
            # hidden mulligan without exposing or evaluating the human hand.
            self.ai.step(self.game)
        self.selected=None
        self.hover=None
        self.scroll=0
        self.choice_page=0
        self.last_error=''
        self.last_ai_ms=0
        self.drag_start=None
        self.tooltip_open=False
        self.details_card=None
        self.details_scroll=0
        self.details_image_zoom=False
        self.sidebar_card=None
        self._old_pending=None
        self._recent_feedback=[]
        self.visual_notice=''
        self.visual_notice_tick=-10000
        self._last_logged_event=len(self.game.event_journal)
        self.combat_visuals=CombatVisuals()
        self.combat_visuals.sync(self.game,self.slot_rect,self.hero_rect,pygame.time.get_ticks())
        self.recorder=MatchRecorder()
        self.recorder.capture(self.game)
        self.replay_index=None
        self.history_open=False
        self.history_scroll=0

    def _export_finished_audit_once(self,force=False):
        """Persist latest audit plus the deduplicated history of every finished match."""
        game=getattr(self,'game',None)
        if game is None or game.phase!='finished':
            return None
        if not force and getattr(self,'_audit_saved_match',None) is game:
            return audit_path()
        try:
            path=write_last_match(game)
            self._audit_saved_match=game
            self._audit_notice='AUDYT ZAPISANY: '+path.name
            return path
        except (OSError,ValueError,TypeError) as exc:
            self._audit_notice='BŁĄD ZAPISU AUDYTU: '+str(exc)
            return None

    def _open_audit_folder(self,archive=False):
        """Open the persistent folder containing audits (or its full archive)."""
        directory=archive_path() if archive else audit_path().parent
        try:
            directory.mkdir(parents=True,exist_ok=True)
            if os.name=='nt':
                os.startfile(str(directory))
            else:
                subprocess.Popen(['xdg-open',str(directory)],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            return True
        except (OSError,AttributeError) as exc:
            self._audit_notice='Nie można otworzyć folderu: '+str(exc)
            return False

    def _open_archived_record(self,record):
        """Open the exact selected match in Explorer, not just its first page."""
        filename=str(record.get('file',''))
        if not filename or Path(filename).name!=filename or not filename.endswith('.json.gz'):
            self.menu_message='Nieprawidłowa nazwa pliku historii.'
            return False
        target=archive_path()/filename
        if not target.is_file():
            self.menu_message='Plik historii nie istnieje: '+filename
            return False
        try:
            if os.name=='nt':
                subprocess.Popen(['explorer.exe','/select,',str(target)],
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(['xdg-open',str(target.parent)],
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.menu_message='WYBRANY MECZ: '+filename
            return True
        except (OSError,AttributeError) as exc:
            self.menu_message='Nie można otworzyć meczu: '+str(exc)
            return False

    @staticmethod
    def _desktop_resolution():
        """Get SDL's display dimensions in its own DPI-aware window coordinates."""
        try:
            sizes=pygame.display.get_desktop_sizes()
            if sizes:
                try:
                    index=pygame.display.get_window_display_index()
                except (AttributeError, pygame.error):
                    index=0
                if not (0<=index<len(sizes)):
                    index=0
                width,height=sizes[index]
                if width>0 and height>0:
                    return int(width),int(height)
        except (AttributeError, pygame.error):
            pass
        info=pygame.display.Info()
        return max(640,int(info.current_w)),max(480,int(info.current_h))

    def _toggle_fullscreen(self):
        """Fullscreen uses the actual desktop mode; restore windowed size on exit."""
        if self.window.get_flags() & pygame.FULLSCREEN:
            self.window=pygame.display.set_mode(self.windowed_size,pygame.RESIZABLE)
        else:
            self.windowed_size=tuple(self.window.get_size())
            self.window=pygame.display.set_mode(self._desktop_resolution(),pygame.FULLSCREEN)
        self.drag_start=None

    def _viewport(self):
        return pygame.Rect(*fitted_viewport(self.window.get_size(),(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT)))

    def _physical_to_virtual(self,pos):
        result=window_to_canvas(pos,tuple(self._viewport()),(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))
        return result if result is not None else (-10000,-10000)

    def mouse_pos(self):
        return self._physical_to_virtual(pygame.mouse.get_pos())

    def _present(self):
        viewport=self._viewport()
        self.window.fill((5,9,14))
        if viewport.size==self.screen.get_size():
            self.window.blit(self.screen,viewport.topleft)
        else:
            scaled=pygame.transform.smoothscale(self.screen,viewport.size)
            self.window.blit(scaled,viewport.topleft)
        pygame.display.flip()

    def _open_details(self,uid=None):
        uid=uid or self.selected or self.card_under(self.mouse_pos())
        if uid not in self.game.cards:return
        self.details_card=uid
        self.details_scroll=0
        self.details_image_zoom=False

    def _create_background(self):
        return self.theme.background((cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))

    def _text(self,s,size,x,y,color=None,center=False):
        font=self.fonts[size]
        sf=font.render(str(s),True,color or cfg.TEXT)
        pos=sf.get_rect(center=(x,y)) if center else (x,y)
        self.screen.blit(sf,pos)
        return sf.get_rect(topleft=pos) if not center else sf.get_rect(center=(x,y))

    def _wrap(self,text,size,maxwidth):
        font=self.fonts[size]
        result=[]
        for para in text.split('\n'):
            line=''
            for word in para.split():
                candidate=(line+' '+word).strip()
                if font.size(candidate)[0]>maxwidth and line:
                    result.append(line);line=word
                else:line=candidate
            result.append(line)
        return result

    def _infographic_box(self,rect,title,value,color,subtitle=''):
        self._panel(rect,(31,50,58),color,9)
        self._text(title,12,rect.x+9,rect.y+5,cfg.MUTED)
        # Long upgrade formulas should remain completely visible, not ellipsized
        # in the narrow laptop sidebar.
        font=next((self.fonts_bold[n] for n in (18,16,14,13)
                   if self.fonts_bold[n].size(value)[0]<=rect.width-14),
                  self.fonts_bold[13])
        text=self.cards_view.clip(value,font,rect.width-14)
        self.screen.blit(font.render(text,True,color),(rect.x+9,rect.y+23))
        if subtitle:
            cap=self.cards_view.clip(subtitle,self.fonts[12],rect.width-14)
            self._text(cap,12,rect.x+9,rect.y+45,cfg.TEXT)

    def _rich_effect_text(self,definition,x,y,width,size=18,top=0,bottom=920):
        """Render effect prose with the precise scaling number in bold.
        Durations and unrelated counts stay regular, per Game Master v19.
        """
        regular=self.fonts[size]
        bold=self.fonts_bold[size]
        marks=set(highlighted_numeric_ranges(definition))
        cx=x;cy=y
        for token in re.finditer(r'\s+|\d+|[^\s\d]+',definition.effect):
            piece=token.group()
            if '\n' in piece:
                cy+=size+8;cx=x
                continue
            if piece.isspace():
                if cx>x:
                    cx+=regular.size(piece)[0]
                continue
            emphasis=token.span() in marks
            font=bold if emphasis else regular
            w=font.size(piece)[0]
            if cx+w>x+width and cx>x:
                cy+=size+9
                cx=x
            if top<=cy<bottom-size-3:
                self.screen.blit(font.render(piece,True,(173,255,189) if emphasis else cfg.TEXT),(cx,cy))
            cx+=w
        return cy+size+7

    def _panel(self,rect,fill=None,line=None,radius=14):
        self.theme.panel(self.screen,rect,fill or cfg.PANEL,
                         line or cfg.PANEL_BORDER,radius)

    def _button(self,rect,label,active=True,accent=False,small=False):
        mp=self.mouse_pos()
        hover=rect.collidepoint(mp)
        pressed=bool(pygame.mouse.get_pressed()[0]) and hover
        self.theme.button(self.screen,rect,hover,active,accent,pressed)
        size=14 if small else 16
        clipped=self.cards_view.clip(label,self.fonts[size],rect.width-20)
        self._text(clipped,size,rect.centerx,rect.centery,
                   cfg.TEXT if active else cfg.MUTED,center=True)

    def slot_rect(self,owner,index):
        return pygame.Rect(self.FIRST_X+index*(self.SLOT_W+self.SLOT_GAP),self.OWN_Y if owner==0 else self.OPP_Y,self.SLOT_W,self.SLOT_H)

    def hand_layout(self):
        hand=self.game.players[0].hand
        visible=6
        self.scroll=max(0,min(self.scroll,max(0,len(hand)-visible)))
        result={}
        for i,uid in enumerate(hand[self.scroll:self.scroll+visible]):
            result[uid]=pygame.Rect(90+i*156,self.HAND_Y,self.HAND_W,self.HAND_H)
        return result

    def hero_rect(self,idx):
        return pygame.Rect(110,98,935,44) if idx==1 else pygame.Rect(110,662,935,44)

    def card_under(self,pos):
        for uid,rect in self.hand_layout().items():
            if rect.collidepoint(pos):return uid
        for idx,p in enumerate(self.game.players):
            for j,uid in enumerate(p.board):
                if self.slot_rect(idx,j).collidepoint(pos):return uid
        return None

    def target_under(self,pos):
        for idx in (0,1):
            if self.hero_rect(idx).collidepoint(pos):return f'hero:{idx}'
            for j,uid in enumerate(self.game.players[idx].board):
                if self.slot_rect(idx,j).collidepoint(pos):return uid
        return None

    # Choice controls are confined to their own panel below the skill description.
    CHOICES_PER_PAGE = 6
    CHOICE_FIRST_Y = 467
    CHOICE_ROW_HEIGHT = 54
    AI_ACTION_DELAY_MS = 850

    def choice_bounds(self):
        """Choice buttons belong to the sidebar, never above the game board."""
        pending = self.game.pending
        if pending is None:
            return []
        start = self.choice_page * self.CHOICES_PER_PAGE
        count = min(len(pending.choices), start + self.CHOICES_PER_PAGE)
        return [(i, pygame.Rect(1104, self.CHOICE_FIRST_Y +
                                (i - start) * self.CHOICE_ROW_HEIGHT, 320, 47))
                for i in range(start, count)]

    def _choice_last_page(self):
        pending = self.game.pending
        return (len(pending.choices) - 1) // self.CHOICES_PER_PAGE if pending else 0

    def _choose(self, index):
        pending=self.game.pending
        try:
            self.game.choose(index)
            self.last_error = ''
            # After choosing S66's self-haste, let the player click an attack target
            # immediately, without having to reselect the freshly played elf.
            if pending and pending.context=='play' and pending.uid in self.game.units:
                if self.game.legal_attacks(pending.uid):
                    self.selected=pending.uid
        except IllegalMove as exc:
            self.last_error = str(exc)
        self.choice_page = 0

    def _choose_target(self, target):
        """Clicking a highlighted board target picks an unambiguous option."""
        pending = self.game.pending
        if pending is None or target is None:
            return
        matches = [i for i, item in enumerate(pending.choices)
                   if item.target == target]
        if len(matches) == 1:
            self._choose(matches[0])
        elif len(matches) > 1:
            self.choice_page = matches[0] // self.CHOICES_PER_PAGE
            self.last_error = 'Wybierz wariant zdolności w panelu po prawej.'

    def click(self,pos,button=1):
        g=self.game
        if self.details_card is not None:
            self.details_card=None;return
        if g.phase=='auction':
            self._auction_click(pos)
            return
        if g.phase=='finished':
            if pygame.Rect(608,637,260,52).collidepoint(pos):
                self._request_restart()
            elif pygame.Rect(392,702,325,46).collidepoint(pos):
                self._export_finished_audit_once(force=True)
            elif pygame.Rect(738,702,325,46).collidepoint(pos):
                self._open_audit_folder()
            return
        if g.pending:
            if g.pending.owner != 0:
                return
            for index, rect in self.choice_bounds():
                if rect.collidepoint(pos):
                    self._choose(index)
                    return
            if pygame.Rect(1103,814,150,38).collidepoint(pos):
                self.choice_page = max(0, self.choice_page - 1)
                return
            if pygame.Rect(1274,814,150,38).collidepoint(pos):
                self.choice_page = min(self._choice_last_page(), self.choice_page + 1)
                return
            self._choose_target(self.target_under(pos) or self.card_under(pos))
            return
        if pygame.Rect(1103,686,316,40).collidepoint(pos):
            uid=self.sidebar_card
            if uid in g.cards:self._open_details(uid)
            return
        if g.phase=='mulligan':
            for uid,rect in self.hand_layout().items():
                if rect.collidepoint(pos):
                    try:
                        g.mulligan_toggle(uid)
                        self.selected=uid
                        self.last_error=''
                    except IllegalMove as e:self.last_error=str(e)
                    return
            if pygame.Rect(1182,808,243,59).collidepoint(pos):
                try:g.finish_mulligan(0)
                except IllegalMove as e:self.last_error=str(e)
                self.selected=None
            return
        if pygame.Rect(1201,816,221,52).collidepoint(pos):
            if g.active==0:
                try:g.end_turn()
                except IllegalMove as e:self.last_error=str(e)
                self.selected=None
            return
        if pygame.Rect(1093,869,145,33).collidepoint(pos):
            self._request_restart();return
        if pygame.Rect(1016,861,40,37).collidepoint(pos):
            self.scroll=min(self.scroll+1,max(0,len(g.players[0].hand)-6));return
        if pygame.Rect(42,861,40,37).collidepoint(pos):
            self.scroll=max(0,self.scroll-1);return
        hand_card=next((uid for uid,r in self.hand_layout().items() if r.collidepoint(pos)),None)
        if hand_card and g.active==0:
            self.selected=hand_card if self.selected!=hand_card else None
            self.tooltip_open=True;return
        target=self.target_under(pos)
        if g.active==0:
            if self.selected in g.players[0].hand:
                if (target in g.players[0].board) or (self.OWN_Y-12<=pos[1]<=self.OWN_Y+self.SLOT_H+12):
                    replace=target if target in g.players[0].board and len(g.players[0].board)==5 else None
                    self._try_play(self.selected,replace)
                    return
                if target is None:return
            if self.selected in g.players[0].board and target is not None and (target in g.players[1].board or target=='hero:1'):
                issue=self._attack_issue(self.selected,target)
                if issue:
                    self.last_error=issue
                else:
                    try:g.attack(self.selected,target);self.last_error=''
                    except IllegalMove as e:self.last_error=str(e)
                if self.selected not in g.units:self.selected=None
                return
            if target in g.players[0].board:
                self.selected=target if self.selected!=target else None
                self.tooltip_open=True;return
        if target in g.units:self.selected=target;self.tooltip_open=True

    @staticmethod
    def auction_offer_rect(index):
        return pygame.Rect(271+index*318,254,278,364)

    @staticmethod
    def auction_control_rect(action):
        return {
            'pass':pygame.Rect(528,753,210,49),
            'bid':pygame.Rect(759,753,210,49),
        }[action]

    @staticmethod
    def auction_slider_rect():
        return pygame.Rect(483,715,516,16)

    def auction_slider_bounds(self):
        a=self.game.auction
        minimum=(max(1,a.highest_effective+1-a.bid_bonus[0])
                 if self.game.auction_catalog=='v22'
                 else max(1,a.current_bid+1))
        return minimum,self.game.players[0].coins

    def _sync_auction_slider(self):
        a=self.game.auction
        if a is None or a.phase!='bidding' or a.turn!=0:
            self.auction_slider_key=None
            return
        minimum,coins=self.auction_slider_bounds()
        # A new bid by either side must invalidate the old selection.
        key=(id(a),a.turn,a.phase,a.highest_effective,a.current_bid,
             a.bid_bonus[0])
        if key!=self.auction_slider_key:
            self.auction_slider_key=key
            self.auction_slider_value=minimum
            self.auction_slider_dragging=False
        if minimum<=coins:
            if self.auction_slider_value is None:
                self.auction_slider_value=minimum
            self.auction_slider_value=max(minimum,min(
                coins,int(self.auction_slider_value)))
        else:
            self.auction_slider_value=None

    def _set_auction_slider_from_pointer(self,pos):
        self._sync_auction_slider()
        minimum,coins=self.auction_slider_bounds()
        if self.game.auction.turn!=0 or minimum>coins:return
        rect=self.auction_slider_rect()
        ratio=max(0.0,min(1.0,(pos[0]-rect.left)/max(1,rect.width)))
        self.auction_slider_value=minimum+round((coins-minimum)*ratio)

    def _shift_auction_slider(self,delta=0,edge=None):
        self._sync_auction_slider()
        minimum,coins=self.auction_slider_bounds()
        if minimum>coins:return
        if edge=='minimum':self.auction_slider_value=minimum
        elif edge=='balance':self.auction_slider_value=coins
        else:self.auction_slider_value=max(minimum,min(
            coins,self.auction_slider_value+delta))

    def _auction_bid_issue(self,amount):
        """Check affordability in UI; Match remains authoritative."""
        a=self.game.auction
        if a is None or a.phase!='bidding' or a.turn!=0:
            return 'Teraz nie możesz licytować.'
        minimum=(max(1,a.highest_effective+1-a.bid_bonus[0])
                 if self.game.auction_catalog=='v22' else max(1,a.current_bid+1))
        coins=self.game.players[0].coins
        if amount<minimum:
            return f'Minimalna oferta to {minimum} monet.'
        if amount>coins:
            return f'Masz {coins} monet, potrzeba {amount}. Wybierz PASUJ.'
        return ''

    def _auction_do(self,operation,uid=None):
        game=self.game
        if game.phase!='auction' or game.auction is None or game.auction.turn!=0:
            return
        try:
            if operation=='pass':
                game.auction_pass(0)
            elif operation=='bid':
                self._sync_auction_slider()
                amount=self.auction_slider_value
                if amount is None:
                    self.auction_status='Brak monet na wymaganą ofertę. Wybierz PASUJ.'
                    return
                issue=self._auction_bid_issue(amount)
                if issue:
                    self.auction_status=issue
                    return
                game.auction_bid(0,amount)
            elif operation=='pick':
                game.auction_pick(0,uid)
            self.auction_status=''
            self.auction_bid_text=''
            self.auction_slider_key=None
        except (IllegalMove,ValueError) as exc:
            self.auction_status=str(exc)

    def _auction_click(self,pos):
        a=self.game.auction
        if a is None or a.turn!=0:return
        if a.phase=='picking':
            for i,offer in enumerate(a.offers):
                if self.auction_offer_rect(i).collidepoint(pos):
                    self._auction_do('pick',offer.uid)
                    return
        elif a.phase=='bidding':
            if self.auction_slider_rect().inflate(0,20).collidepoint(pos):
                self._set_auction_slider_from_pointer(pos)
                return
            for action in ('pass','bid'):
                if self.auction_control_rect(action).collidepoint(pos):
                    self._auction_do(action)
                    return

    def _draw_auction(self):
        a=self.game.auction
        if self.game.phase!='auction' or a is None:return
        overlay=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        overlay.fill((4,8,13,229))
        self.screen.blit(overlay,(0,0))
        self._panel(pygame.Rect(203,112,1076,732),(58,39,28),cfg.GOLD,16)
        self.theme.carved_panel(self.screen,pygame.Rect(219,125,1044,694),opacity=82)
        self._text(f'AUKCJA {a.number} · PO RUNDZIE {a.completed_round}',28,
                   741,152,cfg.GOLD,center=True)
        self._text('17 ARCHETYPÓW · 51 AKTYWNYCH WARIANTÓW ZDOLNOŚCI',16,
                   741,205,cfg.TEXT,center=True)
        self.theme.ornament(self.screen,565,228,350,22)
        for i,off in enumerate(a.offers):
            rect=self.auction_offer_rect(i)
            claimed=off.uid in a.picks.values()
            selectable=a.phase=='picking' and a.turn==0 and not claimed
            self._panel(rect,(52,37,26) if not claimed else (38,34,29),
                        cfg.GOLD if selectable else cfg.PANEL_BORDER,14)
            self.theme.carved_panel(self.screen,rect.inflate(-8,-8),opacity=72)
            adef=catalog_for(self.game.auction_catalog).get(off.archetype)
            self._text(f'OFERTA {i+1} · {off.archetype or "ARCHIWALNA"}',14,
                       rect.centerx,rect.y+17,cfg.GOLD,center=True)
            name=adef.name if adef else f'Strażnik aukcji {off.hp} PŻ'
            self._text(self.cards_view.clip(name,self.fonts[16],rect.width-20),16,
                       rect.centerx,rect.y+53,cfg.TEXT,center=True)
            self._text(f'{off.atk} ATAK     {off.hp} PŻ',22,rect.centerx,
                       rect.y+102,cfg.GREEN if not claimed else cfg.MUTED,center=True)
            self._text(f'{off.rarity.upper()} · POZIOM {off.level}',13,
                       rect.centerx,rect.y+155,cfg.GOLD,center=True)
            description=(v23_variant(self.game.auction_catalog,off.archetype,
                                      off.rarity,getattr(self.game,'ruleset_version','v22'))
                         if adef and self.game.auction_catalog in ('v4','v22') else
                         'PLANOWANA: '+adef.abilities[RARITIES.index(off.rarity)]
                         if adef else 'Prowokacja i 1 Tarcza po wystawieniu')
            lines=self._wrap(description,13,rect.width-36)
            for j,line in enumerate(lines[:4]):
                self._text(line,13,rect.centerx,rect.y+190+24*j,
                           cfg.TEXT,center=True)
            if claimed:
                selected_by=next(p for p,card in a.picks.items() if card==off.uid)
                self._text(f'WYBRANO: {self.game.players[selected_by].name}',13,
                           rect.centerx,rect.y+322,cfg.MUTED,center=True)
            elif selectable:
                self._text('KLIKNIJ, ABY WYBRAĆ',14,rect.centerx,
                           rect.y+322,cfg.GOLD,center=True)
        who=self.game.players[a.turn].name
        if a.phase=='bidding':
            minimum,coins=self.auction_slider_bounds()
            leader=('BRAK' if a.highest_bidder is None
                    else self.game.players[a.highest_bidder].name)
            bonus=a.bid_bonus[0] if self.game.auction_catalog=='v22' else 0
            self._text(f'OFERUJE PRZECIWNIK: {leader}  ·  '
                       f'NAJWYŻSZA OFERTA SKUTECZNA: {a.highest_effective}  ·  '
                       f'NASZ BONUS A018: +{bonus}',14,741,644,cfg.TEXT,center=True)
            self._sync_auction_slider()
            chosen=self.auction_slider_value
            self._text(
                f'MINIMUM DO ZAPŁATY: {minimum}  ·  '
                f'WYBRANA OFERTA: {chosen if chosen is not None else "BRAK"}  ·  '
                f'SKUTECZNA WARTOŚĆ: {(chosen+bonus) if chosen is not None else "—"}  ·  '
                f'MONETY PO WYGRANEJ: {(coins-chosen) if chosen is not None else "—"}',
                13,741,678,cfg.MUTED,center=True)
            if a.turn==0:
                affordable=minimum<=coins
                track=self.auction_slider_rect()
                pygame.draw.rect(self.screen,(60,69,79),track,border_radius=7)
                if affordable:
                    ratio=0 if coins==minimum else (chosen-minimum)/(coins-minimum)
                    handle_x=track.left+round(track.width*ratio)
                    pygame.draw.rect(self.screen,cfg.GOLD,
                                     pygame.Rect(track.left,track.y,handle_x-track.left+1,track.height),
                                     border_radius=7)
                    pygame.draw.circle(self.screen,(249,218,134),
                                       (handle_x,track.centery),12)
                self._text(f'{minimum}',13,track.left-37,track.y-4,cfg.TEXT)
                self._text(f'{coins}',13,track.right+14,track.y-4,cfg.TEXT)
                if not affordable:
                    self._text('BRAK MONET NA PRZEBICIE — PASUJ',13,
                               741,746,cfg.RED,center=True)
                for action,label in (('pass','PASUJ'),('bid','LICYTUJ [ENTER]')):
                    enabled=action=='pass' or affordable
                    self._button(self.auction_control_rect(action),label,
                                 active=enabled,accent=action=='bid' and enabled,
                                 small=True)
            else:
                self._text('RUCH KOMPUTERA...',16,741,753,cfg.GOLD,center=True)
        else:
            self._text(f'WYBIERA: {who}  ·  ZWYCIĘZCA LICYTACJI: '
                       f'{self.game.players[a.winner].name}  ·  CENA: {a.price}',16,
                       741,656,cfg.TEXT,center=True)
            self._text('Kliknij jedną z dostępnych ofert' if a.turn==0
                       else 'Komputer wybiera kartę...',16,741,757,
                       cfg.GOLD,center=True)
        if self.auction_status:
            self._text(self.cards_view.clip(self.auction_status,self.fonts[13],920),
                       13,741,810,cfg.RED,center=True)

    def _play_replacement_targets(self):
        """Only highlight friendly units eligible for replacement."""
        g=self.game
        if (g.phase!='turn' or g.pending or g.active!=0 or
                self.selected not in g.players[0].hand):
            return []
        p=g.players[0]
        if p.played_this_turn or len(p.board)!=5:
            return []
        return [uid for uid in p.board if g.can_play(0,self.selected,uid)]

    def _attack_issue(self,uid,target):
        """Explain illegal targets before they become failed audit commands."""
        legal=self.game.legal_attacks(uid)
        if target in legal:
            return ''
        if not legal:
            return 'Ta jednostka nie może teraz atakować (gotowość, ogłuszenie lub limit ataków).'
        if ('hero:1' not in legal and
                all(t in self.game.players[1].board for t in legal)):
            return 'PROWOKACJA: najpierw zaatakuj turkusowo podświetlonego obrońcę.'
        return 'Nielegalny cel. Dozwolone cele są podświetlone turkusową ramką.'

    def _try_play(self,uid,replace=None):
        g=self.game
        if not g.can_play(0,uid,replace):
            p=g.players[0]
            if g.phase!='turn' or g.active!=0 or g.pending:
                self.last_error='Wystawianie jest teraz niedostępne.'
            elif p.played_this_turn:
                self.last_error='Możesz wystawić tylko jedną kartę w turze.'
            elif len(p.board)==5 and replace is None:
                self.last_error='Plansza 5/5: kliknij podświetloną własną jednostkę do zastąpienia.'
            elif len(p.board)==5 and replace in p.board:
                self.last_error='Tej jednostki nie można zastąpić po wykorzystaniu ataku.'
            else:
                self.last_error='Wskaż wolne pole własnej planszy.'
            return False
        try:
            g.play(uid,replace)
            self.selected=uid if g.legal_attacks(uid) else None
            self.last_error=''
            return True
        except IllegalMove as exc:
            self.last_error=str(exc)
            return False

    def _toggle_animations(self):
        """A switches cosmetic animation only, never combat mechanics."""
        self.animations_enabled=not self.animations_enabled
        self._recent_feedback=[]
        self.visual_notice=('ANIMACJE WŁĄCZONE' if self.animations_enabled
                            else 'ANIMACJE WYŁĄCZONE')
        self.visual_notice_tick=pygame.time.get_ticks()

    def _needs_confirmation(self):
        return self.game.phase not in ('mulligan','finished')

    def _bonus_selection_due(self):
        g=self.game
        return (g.phase=='mulligan' and g.first==1
                and getattr(g,'starting_compensation',None)=='choice_2_5_or_coins'
                and getattr(g,'starting_compensation_choice',None) is None)

    def _choose_bonus(self,choice):
        try:
            self.game.choose_starting_compensation(0,choice)
            self.last_error=''
            self.visual_notice=('WYBRANO CHORĄŻEGO 2/5' if choice=='unit_2_5'
                                else 'WYBRANO +3 MONETY')
            self.visual_notice_tick=pygame.time.get_ticks()
        except IllegalMove as exc:
            self.last_error=str(exc)

    def _draw_bonus_selection(self):
        if not self._bonus_selection_due():return
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((5,8,12,225))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(340,282,800,390)
        self._panel(panel,(32,46,53),cfg.GOLD,15)
        self._text('TWÓJ WYBÓR NA START',28,740,322,cfg.GOLD,center=True)
        self._text('Zaczynasz jako drugi. Wybierz dokładnie jedną rekompensatę.',
                   16,740,381,cfg.TEXT,center=True)
        self._button(pygame.Rect(438,443,604,67),'[1] CHORĄŻY 2 ATAK / 5 PŻ',
                     accent=True)
        self._button(pygame.Rect(438,537,604,67),'[2] +3 MONETY')
        self._text('Chorąży: bez zdolności, nie atakuje w pierwszej własnej turze.',
                   14,740,626,cfg.MUTED,center=True)
        if self.last_error:
            self._text(self.cards_view.clip(self.last_error,self.fonts[13],690),
                       13,740,654,cfg.RED,center=True)

    def _request_restart(self):
        if self._needs_confirmation():
            self.confirm_action='restart'
            self.confirm_error=''
        else:
            self.restart()
            self.menu_open=False
        return True

    def _request_exit(self):
        if self._needs_confirmation():
            self.confirm_action='quit'
            self.confirm_error=''
            return True
        return False

    def _resolve_confirmation(self,save=False):
        action=self.confirm_action
        if not action:return True
        if save:
            try:
                save_match(self.game)
            except (OSError,ValueError,TypeError) as exc:
                self.confirm_error='Nie zapisano meczu: '+str(exc)
                return True
        self.confirm_action=None
        self.confirm_error=''
        if action=='restart':
            self.restart()
            self.menu_open=False
            return True
        return False  # confirmed application quit

    def _draw_confirmation(self):
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((4,8,14,229))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(379,292,724,390)
        self._panel(panel,(33,45,55),cfg.GOLD,16)
        action='nowej gry' if self.confirm_action=='restart' else 'wyjścia'
        self._text('NIEZAPISANA ROZGRYWKA',28,742,333,cfg.GOLD,center=True)
        self._text('Przed rozpoczęciem '+action+' zdecyduj, co zrobić z obecną partią.',
                   15,742,386,cfg.TEXT,center=True)
        self._button(pygame.Rect(470,462,540,52),'[S] ZAPISZ I KONTYNUUJ',accent=True)
        self._button(pygame.Rect(470,530,540,52),'[D] BEZ ZAPISU')
        self._button(pygame.Rect(470,598,540,52),'[ESC] ANULUJ')
        if self.confirm_error:
            self._text(self.cards_view.clip(self.confirm_error,self.fonts[13],640),
                       13,420,661,cfg.RED)

    def handle(self,event):
        if self.music.handle_event(event):return True
        if event.type==pygame.QUIT:return self._request_exit()
        # Global shortcuts must work from the *first menu screen*,
        # during mulligan, history/replay and any open modal.
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F11:
            self._toggle_fullscreen()
            return True
        if event.type==pygame.KEYDOWN and event.key==pygame.K_a:
            self._toggle_animations()
            return True
        # Window-system events must precede modal overlays (including menu).
        if event.type==pygame.VIDEORESIZE:
            if not self.window.get_flags() & pygame.FULLSCREEN:
                dw,dh=self._desktop_resolution()
                max_width,max_height=max(1,dw-24),max(1,dh-64)
                width=max(min(560,max_width),min(int(event.w),max_width))
                height=max(min(360,max_height),min(int(event.h),max_height))
                self.windowed_size=(width,height)
                self.window=pygame.display.set_mode(self.windowed_size,pygame.RESIZABLE)
            return True
        if self.confirm_action is not None:
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    self.confirm_action=None
                    self.confirm_error=''
                elif event.key==pygame.K_s:
                    return self._resolve_confirmation(save=True)
                elif event.key==pygame.K_d:
                    return self._resolve_confirmation(save=False)
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                pos=self._physical_to_virtual(event.pos)
                if pygame.Rect(470,462,540,52).collidepoint(pos):
                    return self._resolve_confirmation(save=True)
                if pygame.Rect(470,530,540,52).collidepoint(pos):
                    return self._resolve_confirmation(save=False)
                if pygame.Rect(470,598,540,52).collidepoint(pos):
                    self.confirm_action=None
                    self.confirm_error=''
            return True
        if event.type==pygame.KEYDOWN and event.key==pygame.K_q:
            return self._request_exit()
        # Panele modalne odcinają interakcje od żywego silnika.
        if self.menu_open:
            if event.type==pygame.KEYDOWN and event.key==pygame.K_o:
                self._open_audit_folder()
                return True
            if event.type==pygame.KEYDOWN:
                if event.key in (pygame.K_m,pygame.K_ESCAPE):
                    self.menu_open=False
                elif event.key==pygame.K_RETURN and self.menu_page=='main':
                    self.menu_open=False
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                self._menu_click(self._physical_to_virtual(event.pos))
            return True
        if self.replay_index is not None:
            if event.type==pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,pygame.K_p,pygame.K_h):
                    self.replay_index=None
                elif event.key in (pygame.K_RIGHT,pygame.K_PERIOD):
                    self.replay_index=min(self.recorder.last_index,self.replay_index+1)
                elif event.key in (pygame.K_LEFT,pygame.K_COMMA):
                    self.replay_index=max(0,self.replay_index-1)
            elif event.type==pygame.MOUSEWHEEL:
                self.replay_index=max(0,min(self.recorder.last_index,self.replay_index+event.y))
            return True
        if self.history_open:
            if event.type==pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,pygame.K_h):
                    self.history_open=False
                elif event.key==pygame.K_p and self.recorder.frames:
                    self.history_open=False
                    self.replay_index=self.recorder.last_index
                elif event.key in (pygame.K_UP,pygame.K_PAGEUP):
                    self.history_scroll=min(max(0,len(self.game.event_journal)-24),self.history_scroll+5)
                elif event.key in (pygame.K_DOWN,pygame.K_PAGEDOWN):
                    self.history_scroll=max(0,self.history_scroll-5)
            elif event.type==pygame.MOUSEWHEEL:
                self.history_scroll=max(0,min(max(0,len(self.game.event_journal)-24),
                                              self.history_scroll+event.y*3))
            return True
        if self.details_card is not None:
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_ESCAPE,pygame.K_i):
                self.details_card=None
            elif event.type==pygame.KEYDOWN and event.key==pygame.K_g:
                self.details_image_zoom=not self.details_image_zoom
            elif event.type==pygame.MOUSEWHEEL:
                self.details_scroll=max(0,min(getattr(self,'details_maxscroll',0),self.details_scroll-event.y*35))
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                pos=self._physical_to_virtual(event.pos)
                if pygame.Rect(194,806,255,40).collidepoint(pos):
                    self.details_image_zoom=not self.details_image_zoom
                else:
                    self.details_card=None
            return True
        if self._bonus_selection_due():
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_1:self._choose_bonus('unit_2_5')
                elif event.key==pygame.K_2:self._choose_bonus('coins')
                elif event.key==pygame.K_h:
                    self.history_open=True
                    self.history_scroll=0
                elif event.key==pygame.K_m:
                    self.menu_open=True
                    self.menu_page='main'
                elif event.key==pygame.K_p and self.recorder.frames:
                    self.replay_index=self.recorder.last_index
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                pos=self._physical_to_virtual(event.pos)
                if pygame.Rect(438,443,604,67).collidepoint(pos):
                    self._choose_bonus('unit_2_5')
                elif pygame.Rect(438,537,604,67).collidepoint(pos):
                    self._choose_bonus('coins')
            return True
        if self.game.phase=='auction':
            if event.type==pygame.KEYDOWN and event.key==pygame.K_m:
                self.menu_page='main'
                self.menu_open=True
                return True
            if event.type==pygame.KEYDOWN and self.game.auction.turn==0:
                state=self.game.auction
                if state.phase=='bidding':
                    if event.key in (pygame.K_LEFT,pygame.K_DOWN):
                        self._shift_auction_slider(-1)
                    elif event.key in (pygame.K_RIGHT,pygame.K_UP):
                        self._shift_auction_slider(+1)
                    elif event.key==pygame.K_HOME:
                        self._shift_auction_slider(edge='minimum')
                    elif event.key==pygame.K_END:
                        self._shift_auction_slider(edge='balance')
                    elif event.key==pygame.K_RETURN:
                        self._auction_do('bid')
                    elif event.key==pygame.K_ESCAPE:
                        self._auction_do('pass')
                elif state.phase=='picking' and pygame.K_1<=event.key<=pygame.K_3:
                    self._auction_do('pick',state.offers[event.key-pygame.K_1].uid)
            elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                pos=self._physical_to_virtual(event.pos)
                if (self.game.auction.turn==0
                        and self.game.auction.phase=='bidding'
                        and self.auction_slider_rect().inflate(0,20).collidepoint(pos)):
                    self.auction_slider_dragging=True
                    self._set_auction_slider_from_pointer(pos)
            elif event.type==pygame.MOUSEMOTION and self.auction_slider_dragging:
                self._set_auction_slider_from_pointer(
                    self._physical_to_virtual(event.pos))
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                self.auction_slider_dragging=False
                self._auction_click(self._physical_to_virtual(event.pos))
            return True
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                self.selected=None;self.tooltip_open=False
                if self.game.phase=='finished':self.restart()
            elif event.key==pygame.K_r and not self.game.pending:
                self._request_restart()
            elif event.key==pygame.K_m:
                self.menu_page='main'
                self.menu_open=True
            elif event.key==pygame.K_h:
                self.history_open=True
                self.history_scroll=0
            elif event.key==pygame.K_p and self.recorder.frames:
                self.replay_index=self.recorder.last_index
            elif event.key==pygame.K_o:
                self._open_audit_folder()
            elif event.key==pygame.K_e and self.game.phase=='finished':
                self._export_finished_audit_once(force=True)
            elif (self.game.pending and self.game.pending.owner == 0
                  and pygame.K_1 <= event.key <= pygame.K_6):
                index = self.choice_page * self.CHOICES_PER_PAGE + event.key - pygame.K_1
                if index < len(self.game.pending.choices):
                    self._choose(index)
            elif event.key==pygame.K_RETURN and self.game.phase=='mulligan':
                try:self.game.finish_mulligan(0)
                except IllegalMove as e:self.last_error=str(e)
            elif event.key==pygame.K_SPACE and self.game.phase=='turn' and self.game.active==0 and not self.game.pending:
                try:self.game.end_turn();self.selected=None
                except IllegalMove as e:self.last_error=str(e)
            elif event.key==pygame.K_LEFT:
                if self.game.pending and self.game.pending.owner==0:self.choice_page=max(0,self.choice_page-1)
                else:self.scroll=max(0,self.scroll-1)
            elif event.key==pygame.K_RIGHT:
                if self.game.pending and self.game.pending.owner==0:self.choice_page=min(self._choice_last_page(),self.choice_page+1)
                else:self.scroll+=1
            elif event.key==pygame.K_i:
                self._open_details(self.game.pending.uid if self.game.pending
                                   else self.selected or self.sidebar_card)

        elif event.type==pygame.MOUSEWHEEL:
            if self.game.pending and self.game.pending.owner==0:
                self.choice_page=max(0,min(self._choice_last_page(),self.choice_page-event.y))
            else:self.scroll=max(0,self.scroll-event.y)
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            pos=self._physical_to_virtual(event.pos)
            self.drag_start=(pos,self.card_under(pos))
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            pos=self._physical_to_virtual(event.pos)
            if self.drag_start:
                down,card=self.drag_start;self.drag_start=None
                if not self.game.pending and card in self.game.players[0].hand and (pos[0]-down[0])**2+(pos[1]-down[1])**2>100:
                    if self.OWN_Y-12<=pos[1]<=self.OWN_Y+self.SLOT_H+12 and self.game.phase=='turn' and self.game.active==0:
                        target=self.target_under(pos)
                        replace=target if target in self.game.players[0].board and len(self.game.players[0].board)==5 else None
                        self._try_play(card,replace)
                    return
            self.click(pos)
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==3:
            point=self._physical_to_virtual(event.pos)
            uid=self.card_under(point)
            if uid in self.game.cards:self._open_details(uid)
            else:self.selected=None;self.tooltip_open=False
        return True

    @staticmethod
    def _feedback_color(message):
        """Only colour recorded engine messages; do not predict their results."""
        text=message.lower()
        # Armor/shield reports also mention "obrażeń": classify defense
        # BEFORE damage so a blocked hit does not flash red like a wound.
        if any(w in text for w in ('tarcza blokuje','tarcza bohatera blokuje',
                                    'pancerz pochłania','pancerz bohatera pochłania')):
            return (123,183,236)
        if any(w in text for w in ('obrażen','zadaje','rani','traci pż')):
            return (224,116,120)
        if any(w in text for w in ('leczy','ulecz','regeneracj','odzyskuje')):
            return (115,222,166)
        if any(w in text for w in ('tarcz','pancerz','zmiana aury')):
            return (123,183,236)
        if any(w in text for w in ('trucizn','ogłusz','status','wyciszenie')):
            return (190,145,242)
        if any(w in text for w in ('zgon','umiera','ginie')):
            return (236,188,132)
        return None

    def _capture_visual_feedback(self):
        events=[event['text'] for event in self.game.event_journal]
        if len(events)<self._last_logged_event:
            self._last_logged_event=0
        if len(events)>self._last_logged_event:
            if self.animations_enabled:
                timestamp=pygame.time.get_ticks()
                for event in events[self._last_logged_event:]:
                    color=self._feedback_color(event)
                    if color:
                        self._recent_feedback.append((timestamp,color))
                self._recent_feedback=self._recent_feedback[-2:]
            self._last_logged_event=len(events)
        now=pygame.time.get_ticks()
        self._recent_feedback=[e for e in self._recent_feedback if now-e[0]<620]

    def update(self):
        g=self.game
        self._export_finished_audit_once()
        self._capture_visual_feedback()
        if (self.menu_open or self.history_open
                or self.replay_index is not None or self.confirm_action is not None):
            return
        if g.phase!='finished' and self.details_card is None:
            if self._old_pending is not g.pending:
                self.choice_page=0
                self._old_pending=g.pending
            t=pygame.time.get_ticks()
            if t-self.last_ai_ms>self.AI_ACTION_DELAY_MS:
                if (g.phase=='auction' and g.auction and g.auction.turn==1) or (g.phase=='turn' and
                    (g.active==1 or (g.pending and g.pending.owner==1))):
                    try:self.ai.step(g)
                    except IllegalMove as e:self.last_error=str(e)
                    self.last_ai_ms=t
            if self.selected in g.cards and self.selected not in g.players[0].hand and self.selected not in g.units:
                self.selected=None
        now=pygame.time.get_ticks()
        self.combat_visuals.sync(g,self.slot_rect,self.hero_rect,now)
        self.recorder.capture(g)

    def _draw_hero(self,idx):
        p=self.game.players[idx]
        rect=self.hero_rect(idx)
        border=cfg.GREEN if idx==0 else cfg.RED
        self._panel(rect,(29,45,59),border,9)
        pygame.draw.line(self.screen,(187,147,83),(rect.x+12,rect.y+5),
                         (rect.x+154,rect.y+5),1)
        x=rect.x+176
        hp=max(0,min(100,p.hp))
        pygame.draw.rect(self.screen,(64,71,79),(x,rect.y+14,425,17),border_radius=6)
        pygame.draw.rect(self.screen,(66,171,125) if idx==0 else (181,78,87),(x,rect.y+14,int(hp/100*425),17),border_radius=6)
        self._text(p.name,18,rect.x+15,rect.y+9)
        self._text(f'{hp}/100',14,x+173,rect.y+14,(255,255,255))
        self._text(f'MONETY  {p.coins}',16,rect.right-172,rect.y+11,cfg.GOLD)

    def _draw_board(self):
        self._text('STREFA KOMPUTERA',15,107,78,cfg.MUTED)
        self._text('TWOJA STREFA',15,107,412,cfg.MUTED)
        self._draw_hero(1)
        self._draw_hero(0)
        for owner,p in enumerate(self.game.players):
            for i in range(5):
                rect=self.slot_rect(owner,i)
                self.theme.slot(self.screen,rect,owner)
                if i>=len(p.board):
                    self._text('+',34,rect.centerx,rect.centery-8,(64,85,100),center=True)
                    self._text(f'POLE {i+1}',12,rect.centerx,rect.bottom-21,cfg.MUTED,center=True)
                    continue
                uid=p.board[i]
                if uid not in self.game.units:continue
                selected=self.selected==uid
                u=self.game.units[uid]
                attack_info=attack_display(self.game,uid)
                self.cards_view.draw(self.screen,self.game.cards[uid],rect,u,
                     selected=selected,hover=rect.collidepoint(self.mouse_pos()),
                     statuses=active_statuses(self.game,uid),ready=attack_info.ready,
                     attacks_remaining=attack_info.remaining,attacks_total=attack_info.limit,
                     hp_override=(self.combat_visuals.hp_display(uid,pygame.time.get_ticks())
                                  if self.animations_enabled and self.replay_index is None
                                  else None))
        self._text('WYSTAWIANIE OD PRAWEJ  ·  ATAKI W DOWOLNEJ KOLEJNOŚCI',12,620,413,cfg.GOLD,center=True)
        for uid in self._play_replacement_targets():
            rect=self.slot_rect(0,self.game.players[0].board.index(uid))
            pygame.draw.rect(self.screen,cfg.GREEN,rect.inflate(8,8),
                             4,border_radius=13)
        p0=self.game.players[0]
        if (self.game.phase=='turn' and self.game.active==0 and
                self.selected in p0.hand and len(p0.board)==5):
            hint=('PLANSZA 5/5: WYBIERZ PODŚWIETLONĄ JEDNOSTKĘ DO WYMIANY'
                  if not p0.played_this_turn else
                  'WYSTAWIONO JUŻ KARTĘ W TEJ TURZE')
            self._text(hint,13,100,721,cfg.GREEN if not p0.played_this_turn else cfg.MUTED)
        elif self.game.phase=='mulligan':
            self._text('WYMIANA STARTOWA  ·  wybierz maks. 3 karty na ręce, ENTER zatwierdza',
                       14,100,721,cfg.GOLD)
        else:
            self._text('TWOJA RĘKA  ·  wybierz kartę i pole lub przeciągnij',
                       14,100,721,cfg.MUTED)
        hand=self.hand_layout()
        for uid,rect in hand.items():
            pygame.draw.rect(self.screen,(18,32,41),rect.inflate(11,10),border_radius=13)
            marked=(self.game.phase=='mulligan'
                    and uid in self.game.players[0].mulligan_selected)
            self.cards_view.draw(self.screen,self.game.cards[uid],rect,
                                 selected=(uid==self.selected or marked),
                                 dim=(self.game.phase=='turn' and self.game.active!=0),
                                 statuses=hand_grants(self.game,uid))
            if marked:
                pygame.draw.rect(self.screen,cfg.GOLD,rect.inflate(9,9),4,border_radius=12)
                badge=pygame.Rect(rect.x+6,rect.y+72,rect.width-12,29)
                pygame.draw.rect(self.screen,(130,56,54),badge,border_radius=6)
                pygame.draw.rect(self.screen,cfg.GOLD,badge,2,border_radius=6)
                rank=self.game.players[0].mulligan_selected.index(uid)+1
                self._text(f'✓  WYMIANA {rank}/3',13,badge.centerx,badge.centery,
                           (255,250,238),center=True)
        if len(self.game.players[0].hand)>6:
            self._button(pygame.Rect(42,861,40,37),'‹',active=self.scroll>0,small=True)
            self._button(pygame.Rect(1016,861,40,37),'›',active=self.scroll+6<len(self.game.players[0].hand),small=True)
            self._text(f'{self.scroll+1}–{min(self.scroll+6,len(self.game.players[0].hand))} / {len(self.game.players[0].hand)}',13,866,721,cfg.MUTED)

    def _draw_sidebar(self):
        rect=pygame.Rect(self.SIDEBAR_X,78,364,872)
        self._panel(rect,(23,35,47),cfg.PANEL_BORDER,16)
        if self.game.pending and self.game.pending.owner == 0:
            self._draw_choice_sidebar()
            return
        self._text('KARTA / AKCJE',22,1103,106,cfg.GOLD)
        card_id=self.selected or self.card_under(self.mouse_pos())
        self.sidebar_card=card_id if card_id in self.game.cards else None
        if card_id and card_id in self.game.cards:
            c=self.game.cards[card_id];d=c.definition;u=self.game.units.get(card_id)
            cue=card_cue(c,u)
            summary=ability_summary(c,u)
            self._text(self.cards_view.clip(d.name,self.fonts[18],310),18,1105,150,FACTION_COLORS[d.faction])
            self._text(f'{d.id} • {d.faction} • POZ. {cue.ability_level}',13,1105,181,cfg.MUTED)
            self._infographic_box(pygame.Rect(1104,210,153,70),'AKTYWACJA',cue.trigger,(142,215,238),cue.family)
            self._infographic_box(pygame.Rect(1267,210,157,70),'ROZWÓJ CO 3 TURY',cue.upgrade,cfg.GREEN,cue.next_threshold)
            self._infographic_box(pygame.Rect(1104,290,320,69),'AKTUALNY EFEKT',cue.base,cue.color,
                                  f'ATAK {u.atk if u else c.attack} / PŻ {u.hp if u else c.max_hp}')
            self._text('DZIAŁANIE ZDOLNOŚCI',15,1105,380,cfg.GOLD)
            yy=405
            for line in self._wrap(summary.full,13,312)[:3]:
                self._text(line,13,1105,yy,cfg.TEXT);yy+=18
            if len(self._wrap(summary.full,13,312))>3:
                self._text('Pełny opis i wartości: [I]',12,1105,464,cfg.MUTED)
            self._text('POSTĘP / WZROST',15,1105,491,cfg.GOLD)
            self._text(self.cards_view.clip(cue.growth,self.fonts[13],309),13,1105,517,cfg.MUTED)
            if u:
                statuses=active_statuses(self.game,card_id)
                self._text(f'AKTYWNE EFEKTY ({len(statuses)})',15,1105,548,cfg.GOLD)
                # Important quantities are available immediately from the
                # sidebar, not hidden behind the full documentation window.
                for j,st in enumerate(statuses[:2]):
                    yy=571+j*37
                    pygame.draw.circle(self.screen,st.color,(1113,yy+7),5)
                    self._text(self.cards_view.clip(st.name,self.fonts[13],296),13,1126,yy,st.color)
                    detail=self.cards_view.clip(st.detail,self.fonts[12],302)
                    self._text(detail,12,1126,yy+21,cfg.MUTED)
                if len(statuses)>2:
                    self._text(f'+{len(statuses)-2} pozostałych efektów — [I]',12,1105,648,cfg.MUTED)
            else:
                grants=hand_grants(self.game,card_id)
                if grants:
                    self._text('PRZYZNANE CECHY W RĘCE',14,1105,553,cfg.GOLD)
                    for j,st in enumerate(grants[:3]):
                        self._text(self.cards_view.clip(st.name,self.fonts[13],310),13,1105,577+j*25,st.color)
                self._text(self.cards_view.clip(d.scaling,self.fonts[12],313),12,1105,658,cfg.MUTED)
        else:
            lines=['Kliknij kartę, aby zobaczyć jej opis.','Możesz zagrać JEDNĄ kartę na turę','i atakować gotowymi jednostkami','w dowolnej kolejności.','','FRAKCJE:',
                   'ELFY: efekt przy wystawieniu','BESTIE: efekt przy ataku','POTWORY: efekt przy śmierci',
                   'KRASNOLUDY: efekt na koniec tury','LUDZIE: efekty pasywne']
            y=171
            for line in lines:
                self._text(line,14,1105,y,cfg.MUTED);y+=29
            self._text('KOLORY AKTYWNYCH EFEKTÓW',14,1105,531,cfg.GOLD)
            samples=[('PROW','taunt'),('TRUC','poison'),('OGŁ','stun'),
                     ('TARCZ','shield'),('REGEN','regen'),('ODP','immune'),
                     ('SZYB','quick'),('2×','double')]
            for i,(label,key) in enumerate(samples):
                x=1105+(i%2)*153;y=559+(i//2)*28
                pygame.draw.circle(self.screen,STATUS_COLORS[key],(x+6,y+6),5)
                self._text(label,14,x+18,y,STATUS_COLORS[key])
        if card_id and card_id in self.game.cards:
            self._button(pygame.Rect(1103,686,316,40),'PEŁNY OPIS KARTY  [I]',accent=True,small=True)
        if self.game.phase=='mulligan':
            n=len(self.game.players[0].mulligan_selected)
            first='TY' if self.game.first==0 else 'KOMPUTER'
            # Read the actual loaded match, not the default for newly created
            # games; older saves and archives keep their historical rules.
            mode=getattr(self.game,'starting_compensation','coins')
            if mode=='coins':
                bonus='+3 MONETY'
            elif mode=='choice_2_5_or_coins':
                selected=getattr(self.game,'starting_compensation_choice',None)
                guard=self.game.units.get('SUM_START_GUARD')
                bonus=('+3 MONETY' if selected=='coins' else
                       f'CHORĄŻY {guard.atk}/{guard.max_hp}' if guard else
                       'WYBIERZ REKOMPENSATĘ' if self.game.first==1 else
                       'WYBIERA KOMPUTER')
            else:
                guard=self.game.units.get('SUM_START_GUARD')
                if guard and mode=='unit_3_5':
                    bonus=f'CHORĄŻY {guard.atk}/{guard.max_hp}'
                elif guard:
                    bonus=f'STRAŻNIK {guard.atk}/{guard.max_hp}'
                else:
                    bonus='BRAK JEDNOSTKI STARTOWEJ'
            self._text(f'ZACZYNA: {first}  ·  DRUGI: {bonus}',
                       11,1104,728,cfg.MUTED)
            self._text(f'WYBRANO DO WYMIANY: {n}/3',16,1104,743,cfg.GOLD)
            self._text('Kliknij do 3 kart z ręki albo pomiń [ENTER]',12,
                       1104,773,cfg.TEXT)
            self._button(pygame.Rect(1182,808,243,59),'ZATWIERDŹ WYMIANĘ',accent=True)
        elif self.game.phase=='finished':
            # The winning/losing overlay owns the only actionable new-game CTA.
            pass
        else:
            self._text(f'RUNDA {self.game.round}',18,1104,743,cfg.GOLD)
            if self.game.active==0:
                self._text('TWOJA TURA',15,1104,773,cfg.GREEN)
            else:self._text('RUCH KOMPUTERA',15,1104,773,cfg.RED)
            if self.game.players[0].next_fast:
                self._text('NASTĘPNA KARTA: SZYBKI ATAK',13,1104,796,STATUS_COLORS['quick'])
            can=self.game.active==0 and not self.game.pending
            self._button(pygame.Rect(1201,816,221,52),'ZAKOŃCZ TURĘ',active=can,accent=can)
        self._button(pygame.Rect(1093,869,145,33),'NOWY MECZ  [R]',small=True)

    @staticmethod
    def header_regions():
        """Separate logo, mode and shortcuts. No text may cross its cell."""
        return (pygame.Rect(100,9,430,66),
                pygame.Rect(548,9,430,66),
                pygame.Rect(998,9,441,66))

    def _phase_guidance(self):
        """Player-facing next-action advice derived ONLY from committed state."""
        g=self.game
        if g.phase=='finished':
            return 'KONIEC MECZU  ·  [R] NOWA PARTIA   [H] HISTORIA   [P] POWTÓRKA'
        if g.phase=='mulligan':
            count=len(g.players[0].mulligan_selected)
            if 0 not in g.mulligan_done:
                return (f'WYMIANA STARTOWA {count}/3  ·  ZAZNACZ DO 3 KART Z RĘKI  ·  '
                        '[ENTER] ZATWIERDŹ (MOŻESZ WYMIENIĆ ZERO)')
            return 'WYMIANA STARTOWA  ·  KOMPUTER KOŃCZY PRZYGOTOWANIE'
        if g.phase=='auction':
            auction=g.auction
            if auction is None:return 'AUKCJA  ·  PRZYGOTOWANIE OFERT'
            if auction.phase=='bidding':
                if auction.turn==0:
                    return 'AUKCJA  ·  WYBIERZ OFERTĘ SUWAKIEM  ·  [ENTER] LICYTUJ  ·  [ESC] PASUJ'
                return 'AUKCJA  ·  KOMPUTER LICYTUJE'
            if auction.turn==0:
                return 'AUKCJA  ·  WYBIERZ JEDNĄ KARTĘ Z OFERT (PIERWSZY / DRUGI WYBÓR)'
            return 'AUKCJA  ·  KOMPUTER WYBIERA KARTĘ'
        if g.pending:
            if g.pending.owner==0:
                return 'TWOJA TURA  ·  WYBIERZ CEL LUB WARIANT ZDOLNOŚCI PO PRAWEJ'
            return 'TURA KOMPUTERA  ·  ROZSTRZYGANIE ZDOLNOŚCI'
        if g.active!=0:
            return 'TURA KOMPUTERA  ·  ZACZEKAJ NA ZAGRANIA I ATAKI RYWALA'
        player=g.players[0]
        if self.selected in player.hand:
            if player.played_this_turn:
                return 'TWOJA TURA  ·  KARTA JUŻ ZAGRANA  ·  ZAATAKUJ LUB ZAKOŃCZ [SPACJA]'
            if len(player.board)==5:
                if not any(g.can_play(0,self.selected,x) for x in player.board):
                    return 'TWOJA TURA  ·  PEŁNA PLANSZA: BRAK JEDNOSTKI DO ZASTĄPIENIA  ·  [SPACJA]'
                return 'TWOJA TURA  ·  PEŁNA PLANSZA: WSKAŻ JEDNOSTKĘ DO ZASTĄPIENIA'
            return 'TWOJA TURA  ·  WYBIERZ WOLNE POLE, ABY ZAGRAĆ KARTĘ'
        if self.selected in player.board and g.legal_attacks(self.selected):
            return 'TWOJA TURA  ·  ZAATAKUJ PODŚWIETLONY CEL (MOŻLIWY ATAK)'
        can_attack=any(g.legal_attacks(uid) for uid in player.board)
        can_play=(bool(player.hand) and not player.played_this_turn
                  and (len(player.board)<5 or
                       any(g.units[uid].attacks==0 for uid in player.board)))
        if can_play and can_attack:
            return 'TWOJA TURA  ·  ZAGRAJ KARTĘ LUB WYBIERZ JEDNOSTKĘ DO ATAKU'
        if can_play:
            return 'TWOJA TURA  ·  ZAGRAJ JEDNĄ KARTĘ Z RĘKI NA PLANSZĘ'
        if can_attack:
            return 'TWOJA TURA  ·  WYBIERZ GOTOWĄ JEDNOSTKĘ I ZAATAKUJ'
        return 'TWOJA TURA  ·  ZAKOŃCZ TURĘ [SPACJA]  ·  BRAK INNYCH AKCJI'

    def _draw_phase_guidance(self):
        # 54 px of dedicated space, strictly between the two board rows.
        # Two typographic levels are easier to scan than a single truncated log.
        rect=pygame.Rect(96,373,952,54)
        pygame.draw.rect(self.screen,(25,42,53),rect,border_radius=7)
        pygame.draw.rect(self.screen,(111,157,172),rect,1,border_radius=7)
        parts=self._phase_guidance().split('  ·  ')
        title=parts[0]
        detail='  ·  '.join(parts[1:]) if len(parts)>1 else 'Wykonaj legalną akcję wskazaną na planszy.'
        self._text(self.cards_view.clip(title,self.fonts[14],rect.width-28),
                   14,rect.x+12,rect.y+4,cfg.GOLD)
        self._text(self.cards_view.clip(detail,self.fonts[13],rect.width-28),
                   13,rect.x+12,rect.y+29,cfg.TEXT)

    def _draw_header(self):
        logo,mode,help_area=self.header_regions()
        pygame.draw.rect(self.screen,(21,34,43),pygame.Rect(83,8,1364,67),
                         border_radius=12)
        pygame.draw.line(self.screen,cfg.GOLD,(104,73),(1426,73),1)
        self._text('AUCTION',34,106,22,(232,189,107))
        self._text('HAMMER',34,300,22,cfg.TEXT)
        self._text(f'SOLO  ·  70 KART + AUKCJE {self.game.auction_catalog.upper()}  ·  BALANS v21',14,
                   mode.x+8,33,cfg.MUTED)
        help_text=(f'[A] ANIM {"WŁ." if self.animations_enabled else "WYŁ."}  '
                   '[F11] EKRAN  [H] HISTORIA  [M] MENU')
        font=self.fonts[13]
        # Rendered width is checked at runtime; never overflow the canvas.
        help_text=self.cards_view.clip(help_text,font,help_area.width-12)
        self._text(help_text,13,help_area.x+8,34,cfg.GOLD)

    def _draw_log(self):
        """Last journal entry stays INSIDE the sidebar. H opens the full log."""
        if self.animations_enabled and self._recent_feedback:
            latest,color=self._recent_feedback[-1]
            elapsed=pygame.time.get_ticks()-latest
            alpha=max(0,int(72*(1-elapsed/620)))
            shade=pygame.Surface((321,35),pygame.SRCALPHA)
            shade.fill((*color,alpha))
            self.screen.blit(shade,(1100,906))
        notice=(getattr(self,'visual_notice','')
                if pygame.time.get_ticks()-getattr(self,'visual_notice_tick',-10000)<2400
                else '')
        last=self.game.events[-1] if self.game.events else 'Nie ma jeszcze zdarzeń.'
        self._text('OSTATNIE ZDARZENIE  ·  [H] PEŁNA HISTORIA',12,
                   1104,909,cfg.GOLD)
        self._text(self.cards_view.clip(notice or last,self.fonts[12],319),
                   12,1104,929,cfg.TEXT if notice else cfg.MUTED)
        if self.last_error:
            self._text(self.cards_view.clip(self.last_error,self.fonts[13],750),
                       13,280,954,cfg.RED)

    def _attack_target_rects(self):
        """Ask the engine for *currently legal* attack targets only."""
        g=self.game
        if g.pending or g.phase!='turn' or g.active!=0:
            return []
        if self.selected not in g.players[0].board:
            return []
        result=[]
        for target in g.legal_attacks(self.selected):
            if target.startswith('hero:'):
                result.append(self.hero_rect(int(target.split(':')[1])))
            elif target in g.players[1].board:
                result.append(self.slot_rect(1,g.players[1].board.index(target)))
        return result

    def _draw_attack_targets(self):
        for rect in self._attack_target_rects():
            # Cyan means legal ATTACK, distinct from the gold selected card,
            # purple ability target and red numbered mulligan badge.
            pygame.draw.rect(self.screen,(115,223,238),rect.inflate(7,7),
                             3,border_radius=14)

    def _draw_choices(self):
        """Highlight legal ability targets without covering information."""
        pending = self.game.pending
        if pending is None or pending.owner != 0:
            return
        counts = {}
        for ch in pending.choices:
            if ch.target is not None:
                counts[ch.target] = counts.get(ch.target, 0) + 1
        for target, count in counts.items():
            rect = None
            if target.startswith('hero:'):
                rect = self.hero_rect(int(target.split(':')[1]))
            else:
                for player in self.game.players:
                    if target in player.board:
                        rect = self.slot_rect(player.idx, player.board.index(target))
                        break
                if target in self.game.players[0].hand:
                    rect = self.hand_layout().get(target)
            if rect is not None:
                pygame.draw.rect(self.screen,(189,143,240),rect.inflate(8,8),3,border_radius=13)
                pygame.draw.circle(self.screen,(189,143,240),(rect.right-3,rect.y+3),6)

    def _draw_choice_sidebar(self):
        """Dedicated selection panel below the skill description."""
        pending=self.game.pending
        card=self.game.cards[pending.uid].definition
        self._text('WYBÓR ZDOLNOŚCI',22,1104,108,cfg.GOLD)

        # Skill description is fully separated from interactive controls.
        info=pygame.Rect(1094,145,342,239)
        self._panel(info,(31,47,59),cfg.PANEL_BORDER,12)
        self._text(self.cards_view.clip(card.name,self.fonts[18],312),
                   18,1107,162,FACTION_COLORS[card.faction])
        self._text(f'Aktywacja: {card.trigger}',14,1107,191,cfg.TEXT)
        self._text('DZIAŁANIE ZDOLNOŚCI',14,1107,223,cfg.GOLD)
        lines=self._wrap(card.effect,14,314)
        for i,line in enumerate(lines[:4]):
            self._text(self.cards_view.clip(line,self.fonts[14],314),
                       14,1107,252+i*22,cfg.TEXT)
        if len(lines)>4:
            self._text('Pełny opis: naciśnij [I]',12,1107,354,cfg.MUTED)

        pane=pygame.Rect(1094,394,342,500)
        self._panel(pane,(22,37,49),cfg.GOLD,12)
        self._text(f'WYBIERZ CEL / WARIANT ({len(pending.choices)})',
                   14,1107,410,cfg.GOLD)
        self._text('Wybierz cel lub sposób działania.',13,1107,437,cfg.TEXT)
        pygame.draw.line(self.screen,cfg.PANEL_BORDER,(1107,458),(1421,458),1)
        for index,rect in self.choice_bounds():
            choice=pending.choices[index]
            hovered=rect.collidepoint(self.mouse_pos())
            pygame.draw.rect(self.screen,(50,76,85) if hovered else (39,59,72),
                             rect,border_radius=8)
            pygame.draw.rect(self.screen,cfg.HOVER if hovered else cfg.PANEL_BORDER,
                             rect,2,border_radius=8)
            label=self._wrap(choice.label.replace('  →  ',' → '),13,288)
            number=index-self.choice_page*self.CHOICES_PER_PAGE+1
            self._text(f'{number}. {self.cards_view.clip(label[0],self.fonts[13],270)}',
                       13,rect.x+10,rect.y+(8 if len(label)>1 else 16),cfg.TEXT)
            if len(label)>1:
                rest=self.cards_view.clip(' '.join(label[1:]),self.fonts[13],285)
                self._text(rest,13,rect.x+25,rect.y+28,cfg.MUTED)
        if self._choice_last_page():
            self._button(pygame.Rect(1103,814,150,38),'← WSTECZ',
                         active=self.choice_page>0,small=True)
            self._button(pygame.Rect(1274,814,150,38),'DALEJ →',
                         active=self.choice_page<self._choice_last_page(),small=True)
            self._text(f'Strona {self.choice_page+1}/{self._choice_last_page()+1}',
                       13,1263,866,cfg.MUTED,center=True)
        else:
            self._text('Kliknij opcję albo podświetlony cel na planszy.',
                       12,1107,852,cfg.MUTED)
        self._text('Pełny opis zdolności: [I]',12,1107,876,cfg.MUTED)

    def _draw_details(self):
        uid=self.details_card
        if uid not in self.game.cards:return
        card=self.game.cards[uid];d=card.definition;u=self.game.units.get(uid)
        cue=card_cue(card,u)
        summary=ability_summary(card,u)
        v23_note=v23_base_card_note(d.id,getattr(self.game,'ruleset_version','v22'))
        detail_summary=(f'{summary.full}  [DODATKOWA ZASADA v23] {v23_note}'
                        if v23_note else summary.full)
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((1,5,10,226));self.screen.blit(shade,(0,0))
        box=pygame.Rect(146,75,1190,831)
        self._panel(box,(24,38,52),FACTION_COLORS[d.faction],18)
        pygame.draw.line(self.screen,(66,91,106),(489,160),(489,843),2)
        self._text('PODGLĄD KARTY',16,186,105,cfg.GOLD)
        details_attack=attack_display(self.game,uid) if u else None
        if self.details_image_zoom:
            # "Contain" is important here: see the ENTIRE existing image.
            if d.id in ART or (d.id=='SUM_START_GUARD' and d.name=='Chorąży'):
                file=ART.get(d.id,ART['S34'])
                artwork=self.cards_view.images.get_card_image(
                    file,(276,520),mode='contain')
            else:
                artwork=self.cards_view.art(d.id,d.faction,(276,520),d.family,d.name)
            self.screen.blit(artwork,(184,164))
            self._text('POWIĘKSZONA ORYGINALNA ILUSTRACJA',13,186,697,cfg.MUTED)
        else:
            self.cards_view.draw(self.screen,card,pygame.Rect(194,164,255,380),
                                 unit=u,selected=True,
                                 statuses=active_statuses(self.game,uid) if u else hand_grants(self.game,uid),
                                 ready=details_attack.ready if u else None,
                                 attacks_total=details_attack.limit if u else None,
                                 attacks_remaining=details_attack.remaining if u else None)
            self._text(f'{d.id} • {d.faction}',18,194,570,FACTION_COLORS[d.faction])
            self._text(f'Aktywacja: {d.trigger}',16,194,600)
            self._text(f'Rodzina: {d.family}',16,194,629)
            label=(f'Poziom zdolności: {cue.ability_level}' if not d.id.startswith('SUM')
                   else 'JEDNOSTKA BEZ ROZWOJU NA RĘCE')
            self._text(self.cards_view.clip(label,self.fonts[16],276),16,194,659,cfg.GOLD)
            self._text(cue.next_threshold if not u else f'Pancerz {u.armor}  •  Tarcza {u.shield}',
                       14,194,685,cfg.MUTED)
            # Archetype baseline and actual MAX HP are distinct from wounds.
            current_atk=u.atk if u else card.attack
            current_max=u.max_hp if u else card.max_hp
            self._text(f'ATK  BAZA {d.atk} → TERAZ {current_atk}',14,194,717,cfg.TEXT)
            self._text(f'MAX PŻ  BAZA {d.hp} → TERAZ {current_max}',14,194,741,cfg.TEXT)
            if u:
                self._text(f'BIEŻĄCE PŻ: {max(0,u.hp)}/{current_max}',
                           14,194,765,cfg.MUTED)
        self._button(pygame.Rect(194,806,255,40),
                     '[G] KARTA' if self.details_image_zoom else '[G] ILUSTRACJA',
                     small=True,accent=self.details_image_zoom)

        self._text(self.cards_view.clip(d.name,self.fonts[28],760),28,520,115,FACTION_COLORS[d.faction])
        self._infographic_box(pygame.Rect(520,159,228,70),'AKTUALNY EFEKT',cue.base,cue.color,
                              'Liczba zmienna oznaczona pogrubieniem')
        self._infographic_box(pygame.Rect(763,159,227,70),'CO 3 WŁASNE TURY NA RĘCE',cue.upgrade,cfg.GREEN,
                              'Próg: 3 / 6 / 9 / 12…')
        self._infographic_box(pygame.Rect(1005,159,227,70),'MOMENT AKTYWACJI',cue.trigger,cfg.HOVER,
                              cue.family)
        pygame.draw.line(self.screen,cfg.PANEL_BORDER,(518,243),(1297,243),1)

        content_top=264;content_bottom=817
        y=content_top-self.details_scroll
        if content_top<=y<content_bottom-27:self._text('ZDOLNOŚĆ — WARTOŚĆ SKALUJĄCA POGRUBIONA',18,520,y,cfg.GOLD)
        y+=37
        for line in self._wrap(detail_summary,16,750):
            if content_top<=y<content_bottom-24:self._text(line,16,520,y,cfg.GREEN)
            y+=24
        y+=12
        if content_top<=y<content_bottom-24:self._text('ORYGINALNY OPIS (WARTOŚCI BAZOWE)',16,520,y,cfg.GOLD)
        y+=31
        for line in self._wrap(d.effect,16,750):
            if content_top<=y<content_bottom-24:self._text(line,16,520,y,cfg.TEXT)
            y+=24
        y+=24
        if content_top<=y<content_bottom-25:self._text('ULEPSZENIE ZDOLNOŚCI',20,520,y,cfg.GOLD)
        y+=36
        for line in self._wrap(d.scaling,18,750):
            if content_top<=y<content_bottom-25:self._text(line,18,520,y,cfg.TEXT)
            y+=27
        y+=23
        if content_top<=y<content_bottom-25:self._text('PRZYROST STATYSTYK NA RĘCE',18,520,y,cfg.GOLD)
        y+=32
        if content_top<=y<content_bottom-25:self._text(cue.growth,18,520,y,cfg.TEXT)
        y+=48
        statuses=active_statuses(self.game,uid) if u else hand_grants(self.game,uid)
        if content_top<=y<content_bottom-26:
            self._text(f'AKTYWNE / NADANE EFEKTY ({len(statuses)})',18,520,y,cfg.GOLD)
        y+=35
        for st in statuses:
            if content_top<=y<content_bottom-23:
                self._text('●',18,523,y,st.color)
                self._text(st.name,18,549,y,st.color)
            y+=27
            provenance=f'Źródło: {st.source}' if st.source else 'Źródło: własna zdolność'
            for line in self._wrap(st.detail+'  |  '+provenance,15,740):
                if content_top<=y<content_bottom-23:self._text(line,15,550,y,cfg.TEXT)
                y+=22
            y+=10
        if not statuses and content_top<=y<content_bottom-23:
            self._text('Brak dodatkowych statusów',15,549,y,cfg.MUTED)
        y+=26
        self.details_maxscroll=max(0,y-780)
        self._text('Kółko myszy: przewiń opis • Zielone pogrubienie: wartość rosnąca',13,524,857,cfg.MUTED)
        self._button(pygame.Rect(1095,853,201,39),'ZAMKNIJ [I / ESC]',small=True)

    def _menu_click(self,pos):
        credits_button=pygame.Rect(875,282,160,34)
        if self.menu_page=='main' and credits_button.collidepoint(pos):
            self.menu_page='credits'
            self.menu_message=''
            return
        if self.menu_page=='credits':
            if pygame.Rect(535,690,420,61).collidepoint(pos):
                self.menu_page='main'
            return
        history_button=pygame.Rect(625,282,240,34)
        if self.menu_page=='main' and history_button.collidepoint(pos):
            try:
                self._archive_records=list_archived_matches()
                self.archive_page=0
                self._archive_selected_record=None
                self.menu_message=''
                self.menu_page='archive'
            except (OSError,ValueError,TypeError) as exc:
                self.menu_message='Nie można odczytać historii: '+str(exc)
            return
        if self.menu_page=='archive':
            total=max(1,(len(self._archive_records)+3)//4)
            self.archive_page=max(0,min(getattr(self,'archive_page',0),total-1))
            if pygame.Rect(535,715,170,36).collidepoint(pos):
                self.archive_page=max(0,self.archive_page-1)
                return
            if pygame.Rect(785,715,170,36).collidepoint(pos):
                self.archive_page=min(total-1,self.archive_page+1)
                return
        buttons=[pygame.Rect(535,322+i*81,420,61) for i in range(5)]
        for i,rect in enumerate(buttons):
            if not rect.collidepoint(pos):continue
            self.menu_message=''
            if self.menu_page=='archive':
                if i==4:
                    self.menu_page='main'
                else:
                    index=self.archive_page*4+i
                    if index<len(self._archive_records):
                        self._archive_selected_record=self._archive_records[index]
                        self._open_archived_record(self._archive_selected_record)
                return
            if self.menu_page=='main':
                if i==0:
                    self._request_restart()
                elif i==1:
                    self.menu_open=False
                elif i==2:
                    try:
                        game=load_match()
                        if not hasattr(game,'audit_actions'):
                            # Old saved game has no historic trace: mark partial.
                            initialize_audit(game,complete=False)
                        game.audit_enabled=True
                        context=configure_audit_context(game,self.ai.difficulty,fresh=False)
                        recorded_difficulty=context.get('ai_difficulty_current')
                        if recorded_difficulty in ('łatwy','normalny','trudny'):
                            self.ai.difficulty=recorded_difficulty
                        self.game=game
                        self._audit_saved_match=None
                        self._audit_notice=''
                        self.selected=None
                        self.sidebar_card=None
                        self.details_card=None
                        self._old_pending=None
                        self.last_error=''
                        self._last_logged_event=len(game.event_journal)
                        self._recent_feedback=[]
                        self.combat_visuals=CombatVisuals()
                        self.combat_visuals.sync(game,self.slot_rect,self.hero_rect,pygame.time.get_ticks())
                        self.recorder=MatchRecorder()
                        self.recorder.capture(game)
                        self.replay_index=None
                        self.history_open=False
                        self.menu_open=False
                    except (OSError,ValueError,TypeError,KeyError) as exc:
                        self.menu_message=f'Nie można wczytać meczu: {exc}'
                elif i==3:
                    self.menu_page='settings'
                else:
                    self.menu_open=False
            else:
                if i==0:
                    self._toggle_animations()
                elif i==1:
                    self._toggle_fullscreen()
                elif i==2:
                    choices=('łatwy','normalny','trudny')
                    index=choices.index(self.ai.difficulty)
                    self.ai.difficulty=choices[(index+1)%len(choices)]
                    record_ai_difficulty(self.game,self.ai.difficulty)
                elif i==3:
                    try:
                        save_match(self.game)
                        self.menu_message='ZAPISANO MECZ — można kontynuować po restarcie'
                    except (OSError,ValueError,TypeError) as exc:
                        self.menu_message=f'Nie można zapisać meczu: {exc}'
                else:
                    self.menu_page='main'
            return

    def _draw_menu(self):
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((4,9,16,234))
        self.screen.blit(shade,(0,0))
        self._panel(pygame.Rect(420,170,650,660),(56,35,23),cfg.GOLD,19)
        self.theme.carved_panel(self.screen,pygame.Rect(432,186,625,632),opacity=98)
        self._text('AUCTIONHAMMER',46,746,223,cfg.GOLD,center=True)
        self._text('TAWERNA · GAME MASTER v23',16,746,269,cfg.MUTED,center=True)
        if self.menu_page=='credits':
            self._text('TWÓRCY I MUZYKA',28,746,329,cfg.GOLD,center=True)
            self._text('AuctionHammer — projekt i kod: Mateusz Boćko',16,746,389,cfg.TEXT,center=True)
            self._text('ŚCIEŻKA DŹWIĘKOWA',20,746,452,cfg.GOLD,center=True)
            self._text('Fantasy Tavern Music — 13 utworów',18,746,491,cfg.TEXT,center=True)
            self._text('Kompozytor: Alek Kaczan',16,746,533,cfg.TEXT,center=True)
            self._text('Wydawca: PGN Music',16,746,568,cfg.TEXT,center=True)
            self._text('Album 2021 · 13 utworów · odrębne prawa do muzyki',14,746,609,cfg.MUTED,center=True)
            self._text('pgnmusic.com',16,746,648,cfg.GOLD,center=True)
            self._button(pygame.Rect(535,690,420,61),'POWRÓT DO MENU')
            self._text('Kod: MIT  ·  Muzyka: odrębna licencja PGN Music',13,746,790,cfg.MUTED,center=True)
            return
        if self.menu_page=='archive':
            total=max(1,(len(self._archive_records)+3)//4)
            self.archive_page=max(0,min(getattr(self,'archive_page',0),total-1))
            records=self._archive_records[self.archive_page*4:(self.archive_page+1)*4]
            items=tuple(
                self.cards_view.clip(
                    f'{item.get("exported_at_utc","")[:16].replace("T"," ")}  ·  '
                    f'v{item.get("version","?")}  ·  '
                    f'{"WYGRANA" if item.get("winner")==0 else "PORAŻKA"}  ·  '
                    f'{item.get("rounds","?")} rund  [FOLDER]',
                    self.fonts[16],390)
                for item in records)
            items=items+tuple('—' for _ in range(4-len(items)))+('WRÓĆ DO MENU',)
            self._text(f'ZAPISANE MECZE: {len(self._archive_records)}',16,746,287,cfg.GOLD,center=True)
            self._button(pygame.Rect(535,715,170,36),'POPRZEDNIA',
                         active=self.archive_page>0,small=True)
            self._text(f'STRONA {self.archive_page+1}/{total}',13,746,733,
                       cfg.GOLD,center=True)
            self._button(pygame.Rect(785,715,170,36),'NASTĘPNA',
                         active=self.archive_page+1<total,small=True)
            if not self._archive_records:
                self._text('BRAK ZAPISANYCH MECZÓW',15,746,699,
                           cfg.MUTED,center=True)
        elif self.menu_page=='main':
            items=('NOWY MECZ','KONTYNUUJ','WCZYTAJ ZAPIS',
                   'USTAWIENIA','WRÓĆ DO GRY')
            self._button(pygame.Rect(625,282,240,34),'HISTORIA MECZÓW',small=True)
            self._button(pygame.Rect(875,282,160,34),'CREDITS',small=True)
        else:
            items=(f'ANIMACJE [A]: {"WŁ." if self.animations_enabled else "WYŁ."}',
                   'PEŁNY EKRAN [F11]',f'AI: {self.ai.difficulty.upper()}',
                   'ZAPISZ MECZ','POWRÓT DO MENU')
        for i,label in enumerate(items):
            self._button(pygame.Rect(535,322+i*81,420,61),label,accent=i==0)
        if self.menu_message:
            status=self.cards_view.clip(self.menu_message,self.fonts[14],620)
            self._text(status,14,746,753,cfg.GOLD,center=True)
        footer=(
            'Archiwum zachowuje wersje i dawne zasady'
            if self.menu_page=='archive' else
            '[A] animacje walki (nie muzyka) · [F11] pełny ekran'
            if self.menu_page=='settings' else
            'F11 — pełny ekran · A — animacje · H — historia · M — menu'
        )
        self._text(footer,13,746,790,cfg.MUTED,center=True)

    def _draw_history_overlay(self):
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((3,7,12,218))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(135,86,1205,818)
        self._panel(panel,(25,40,52),cfg.GOLD,13)
        journal=self.game.event_journal
        self._text(f'HISTORIA MECZU ({len(journal)} ZDARZEŃ)',28,173,126,cfg.GOLD)
        self._text('H / ESC — zamknij     P — zobacz zapisane stany planszy',15,174,168,cfg.MUTED)
        self._text('KÓŁKO MYSZY / STRZAŁKI — przewijaj',13,174,197,cfg.MUTED)
        end=max(0,len(journal)-self.history_scroll)
        page=journal[max(0,end-24):end]
        for i,item in enumerate(page):
            yy=226+i*26
            if i%2==0:
                pygame.draw.rect(self.screen,(35,53,64),
                                 pygame.Rect(167,yy-2,1141,25),border_radius=3)
            turn=f'R{item["round"]:02} · {"TY" if item["active"]==0 else "AI"}'
            message=item['text']
            color=(self._feedback_color(message) or cfg.TEXT)
            self._text(f'{item["seq"]:04}',13,179,yy,cfg.GOLD)
            self._text(turn,13,232,yy,cfg.MUTED)
            self._text(self.cards_view.clip(message,self.fonts[14],873),
                       14,390,yy,color)
        self._text(f'Wyświetlono {len(page)} z {len(journal)} zdarzeń.  '
                   'H/ESC — powrót na planszę.',13,174,866,cfg.MUTED)

    def _draw_replay_controls(self):
        shade=pygame.Surface((cfg.WINDOW_WIDTH,87),pygame.SRCALPHA)
        shade.fill((13,22,35,232))
        self.screen.blit(shade,(0,cfg.WINDOW_HEIGHT-87))
        frame=self.recorder.get(self.replay_index)
        self._text(f'POWTÓRKA · STAN {self.replay_index+1}/{len(self.recorder.frames)}'
                   f' · RUNDA {frame.round}',20,120,902,cfg.GOLD)
        self._text('← / →  POPRZEDNI / NASTĘPNY STAN      P / ESC  POWRÓT DO GRY',14,120,941,cfg.TEXT)

    def _draw_gameover(self):
        if self.game.phase!='finished':return
        overlay=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        overlay.fill((0,0,0,170))
        self.screen.blit(overlay,(0,0))
        self._panel(pygame.Rect(332,226,810,586),(28,44,58),cfg.GOLD,16)
        won=self.game.winner==0
        self._text('ZWYCIĘSTWO!' if won else 'PORAŻKA',46,738,300,
                   cfg.GREEN if won else cfg.RED,center=True)
        self._text(f'Wygrywa: {self.game.players[self.game.winner].name}',
                   22,738,370,center=True)
        self._text(f'ROZEGRANE RUNDY: {self.game.round}',18,738,419,cfg.GOLD,center=True)
        for owner,p in enumerate(self.game.players):
            y=470+owner*47
            deaths=getattr(self.game,'death_counts',[0,0])[owner]
            complete=getattr(self.game,'death_counts_complete',False)
            deaths_label=(f'{deaths} zgonów jednostek' if complete
                          else f'{deaths} zgonów od wczytania')
            label=(f'{p.name}: {max(0,min(100,p.hp))} PŻ  ·  '
                   f'{deaths_label}  ·  {p.coins} monet')
            self._text(label,16,738,y,cfg.TEXT,center=True)
        self._text(f'Historia: {len(self.game.event_journal)} zdarzeń  ·  '
                   f'powtórka: {len(self.recorder.frames)} stanów',15,738,575,cfg.MUTED,center=True)
        self._text('H — historia  ·  P — powtórka  ·  R — nowy mecz',
                   15,738,608,cfg.MUTED,center=True)
        self._button(pygame.Rect(608,637,260,52),'NOWY MECZ',accent=True)
        self._button(pygame.Rect(392,702,325,46),'EKSPORT AUDYTU  [E]',small=True,accent=True)
        self._button(pygame.Rect(738,702,325,46),'OTWÓRZ FOLDER  [O]',small=True)
        notice=getattr(self,'_audit_notice','')
        if notice:
            font=self.fonts[13]
            self._text(self.cards_view.clip(notice,font,745),
                       13,738,770,cfg.GOLD,center=True)

    def draw(self):
        # W powtórce renderujemy kopię, bez kierowania do niej jakichkolwiek
        # komend. Po każdej klatce przywracamy żywy Match.
        live=self.game
        if self.replay_index is not None:
            self.game=self.recorder.get(self.replay_index).game
        try:
            self.screen.blit(self.bg,(0,0))
            self._draw_header()
            self._draw_board()
            self._draw_phase_guidance()
            if self.replay_index is None and self.animations_enabled:
                self.combat_visuals.draw_cards(
                    self.screen,self.game,self.cards_view,pygame.time.get_ticks())
            self._draw_attack_targets()
            self._draw_sidebar()
            self._draw_log()
            self._draw_choices()
            self._draw_gameover()
            self._draw_auction()
            if self.replay_index is None and self.animations_enabled:
                self.combat_visuals.draw(self.screen,pygame.time.get_ticks(),
                                         self.fonts_bold[16])
            if self.replay_index is None:
                self._draw_details()
        finally:
            self.game=live
        if self.replay_index is not None:self._draw_replay_controls()
        if self.history_open:self._draw_history_overlay()
        if self.menu_open:self._draw_menu()
        if self.confirm_action:self._draw_confirmation()
        if (self._bonus_selection_due() and not self.menu_open
                and not self.history_open and self.replay_index is None
                and self.details_card is None):
            self._draw_bonus_selection()
        self._present()

    def run(self):
        running=True
        while running:
            for event in pygame.event.get():
                if not self.handle(event):running=False
            self.update()
            self.draw()
            self.clock.tick(cfg.FPS)
        pygame.quit()


def run():
    SoloApp(start_in_menu=True).run()
