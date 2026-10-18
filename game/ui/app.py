"""AuctionHammer MVP 0.9.18: Minimal Fantasy cards and responsive v19 interface."""
from __future__ import annotations
import os
import re
import subprocess
import pygame
from game.ui.combat_visuals import CombatVisuals
from game.ui.visual_theme import VisualTheme
from game.ui.match_history import MatchRecorder
from game.core.persistence import save_match, load_match, save_path
from game.core.audit import (audit_path, write_last_match, initialize_audit,
                             configure_audit_context, record_ai_difficulty)
from game import config as cfg
from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.models import IllegalMove
from game.ui.card_view import CardView, FACTION_COLORS
from game.ui.card_infographics import card_cue, highlighted_numeric_ranges
from game.ui.card_summary import ability_summary
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
        self.fonts={n:pygame.font.SysFont('segoeui',n,bold=(n>=22)) for n in (12,13,14,15,16,18,20,22,28,34,46)}
        self.theme=VisualTheme()
        self.cards_view=CardView()
        self.fonts_bold={n:pygame.font.SysFont('segoeui',n,bold=True) for n in (13,14,16,18,20,22)}
        self.ai=ComputerOpponent()
        self.bg=self._create_background()
        self.restart()
        self.menu_open=bool(start_in_menu)
        self.menu_page='main'
        self.menu_message=''
        self.history_open=False
        self.history_scroll=0
        self.replay_index=None

    def restart(self):
        if hasattr(self,'game') and self.game.phase=='finished':
            self._export_finished_audit_once()
        self.game=Match(audit_enabled=True)
        configure_audit_context(self.game,self.ai.difficulty,fresh=True)
        self._audit_saved_match=None
        self._audit_notice=''
        self.ai.step(self.game)  # AI mulligan is committed, player's hand still hidden from it.
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
        self.sidebar_card=None
        self._old_pending=None
        self.animations_enabled=True
        self._recent_feedback=[]
        self._last_logged_event=len(self.game.event_journal)
        self.combat_visuals=CombatVisuals()
        self.combat_visuals.sync(self.game,self.slot_rect,self.hero_rect,pygame.time.get_ticks())
        self.recorder=MatchRecorder()
        self.recorder.capture(self.game)
        self.replay_index=None
        self.history_open=False
        self.history_scroll=0

    def _export_finished_audit_once(self,force=False):
        """The most recently FINISHED match is the only exported report."""
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

    def _open_audit_folder(self):
        """Show the persistent folder so the player can upload its one JSON."""
        directory=audit_path().parent
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
        if g.phase=='finished':
            if pygame.Rect(608,637,260,52).collidepoint(pos):
                self.restart()
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
            self.restart();return
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
                try:g.attack(self.selected,target);self.last_error=''
                except IllegalMove as e:self.last_error=str(e)
                if self.selected not in g.units:self.selected=None
                return
            if target in g.players[0].board:
                self.selected=target if self.selected!=target else None
                self.tooltip_open=True;return
        if target in g.units:self.selected=target;self.tooltip_open=True

    def _try_play(self,uid,replace=None):
        try:
            self.game.play(uid,replace)
            self.selected=uid if self.game.legal_attacks(uid) else None
            self.last_error=''
        except IllegalMove as e:self.last_error=str(e)

    def handle(self,event):
        if event.type==pygame.QUIT:return False
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
        if event.type==pygame.VIDEORESIZE:
            if not self.window.get_flags() & pygame.FULLSCREEN:
                dw,dh=self._desktop_resolution()
                max_width,max_height=max(1,dw-24),max(1,dh-64)
                width=max(min(560,max_width),min(int(event.w),max_width))
                height=max(min(360,max_height),min(int(event.h),max_height))
                self.windowed_size=(width,height)
                self.window=pygame.display.set_mode(self.windowed_size,pygame.RESIZABLE)
            return True
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F11:
            self._toggle_fullscreen()
            return True
        if self.details_card is not None:
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_ESCAPE,pygame.K_i):
                self.details_card=None
            elif event.type==pygame.MOUSEWHEEL:
                self.details_scroll=max(0,min(getattr(self,'details_maxscroll',0),self.details_scroll-event.y*35))
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                self.details_card=None
            return True
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                self.selected=None;self.tooltip_open=False
                if self.game.phase=='finished':self.restart()
            elif event.key==pygame.K_r and not self.game.pending:self.restart()
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
            elif event.key==pygame.K_a:
                self.animations_enabled=not self.animations_enabled
                self._recent_feedback=[]
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
            elif event.key==pygame.K_q:return False
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
        if any(w in text for w in ('obrażen','zadaje','rani','traci pż')):
            return (224,116,120)
        if any(w in text for w in ('leczy','ulecz','regeneracj')):
            return (115,222,166)
        if any(w in text for w in ('tarcz','pancerz')):
            return (123,183,236)
        if any(w in text for w in ('trucizn','ogłusz','status')):
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
        if self.menu_open or self.history_open or self.replay_index is not None:
            return
        if g.phase!='finished' and self.details_card is None:
            if self._old_pending is not g.pending:
                self.choice_page=0
                self._old_pending=g.pending
            t=pygame.time.get_ticks()
            if t-self.last_ai_ms>self.AI_ACTION_DELAY_MS:
                if (g.phase=='turn' and
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
                      attacks_remaining=attack_info.remaining,attacks_total=attack_info.limit)
        self._text('WYSTAWIANIE OD PRAWEJ  ·  ATAKI W DOWOLNEJ KOLEJNOŚCI',12,620,413,cfg.GOLD,center=True)
        self._text('TWOJA RĘKA  ·  wybierz kartę i pole lub przeciągnij',14,100,721,cfg.MUTED)
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
            lines=['Kliknij kartę, aby zobaczyć jej opis.','Najpierw zagrywasz JEDNĄ jednostkę','na turę, potem możesz atakować','dowolną liczbą gotowych jednostek.','','FRAKCJE:',
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
            self._text(f'WYBRANO DO WYMIANY: {n}/3',16,1104,743,cfg.GOLD)
            self._button(pygame.Rect(1182,808,243,59),'ZATWIERDŹ WYMIANĘ',accent=True)
        elif self.game.phase=='finished':
            self._button(pygame.Rect(1192,823,236,55),'NOWY MECZ',accent=True)
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

    def _draw_header(self):
        logo,mode,help_area=self.header_regions()
        pygame.draw.rect(self.screen,(21,34,43),pygame.Rect(83,8,1364,67),
                         border_radius=12)
        pygame.draw.line(self.screen,cfg.GOLD,(104,73),(1426,73),1)
        self._text('AUCTION',34,106,22,(232,189,107))
        self._text('HAMMER',34,300,22,cfg.TEXT)
        self._text('SOLO  ·  70 KART  ·  GAME MASTER v19',14,
                   mode.x+8,33,cfg.MUTED)
        help_text='[A] EFEKTY  [H] HISTORIA  [P] POWTÓRKA  [M] MENU'
        font=self.fonts[13]
        # Rendered width is checked at runtime; never overflow the canvas.
        help_text=self.cards_view.clip(help_text,font,help_area.width-12)
        self._text(help_text,13,help_area.x+8,34,cfg.GOLD)

    def _draw_log(self):
        # Delikatny, możliwy do wyłączenia [A] błysk pod ostatnimi
        # zatwierdzonymi zdarzeniami. Żadna animacja nie wpływa na silnik.
        if self.animations_enabled and self._recent_feedback:
            latest,color=self._recent_feedback[-1]
            elapsed=pygame.time.get_ticks()-latest
            alpha=max(0,int(92*(1-elapsed/620)))
            shade=pygame.Surface((940,34),pygame.SRCALPHA)
            shade.fill((*color,alpha))
            self.screen.blit(shade,(109,375))
        entries=self.game.events[-2:]
        y=378
        for s in entries:
            trimmed=self.cards_view.clip(s,self.fonts[12],920)
            self._text(trimmed,12,118,y,cfg.MUTED)
            y+=16
        if self.last_error:
            self._text(self.cards_view.clip(self.last_error,self.fonts[13],750),13,280,954,cfg.RED)

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
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((1,5,10,226));self.screen.blit(shade,(0,0))
        box=pygame.Rect(146,75,1190,831)
        self._panel(box,(24,38,52),FACTION_COLORS[d.faction],18)
        pygame.draw.line(self.screen,(66,91,106),(489,160),(489,843),2)
        self._text('PODGLĄD KARTY',16,186,105,cfg.GOLD)
        details_attack=attack_display(self.game,uid) if u else None
        self.cards_view.draw(self.screen,card,pygame.Rect(194,164,255,380),
                             unit=u,selected=True,
                             statuses=active_statuses(self.game,uid) if u else hand_grants(self.game,uid),
                             ready=details_attack.ready if u else None,
                             attacks_total=details_attack.limit if u else None,
                             attacks_remaining=details_attack.remaining if u else None)
        self._text(f'{d.id} • {d.faction}',18,194,570,FACTION_COLORS[d.faction])
        self._text(f'Aktywacja: {d.trigger}',16,194,600)
        self._text(f'Rodzina: {d.family}',16,194,629)
        self._text(f'Poziom zdolności: {cue.ability_level}',18,194,660,cfg.GOLD)
        self._text(cue.next_threshold if not u else f'Pancerz {u.armor}  •  Tarcza {u.shield}',
                   14,194,689,cfg.MUTED)

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
        for line in self._wrap(summary.full,16,750):
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
        buttons=[pygame.Rect(535,322+i*81,420,61) for i in range(5)]
        for i,rect in enumerate(buttons):
            if not rect.collidepoint(pos):continue
            self.menu_message=''
            if self.menu_page=='main':
                if i==0:
                    self.restart()
                    self.menu_open=False
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
                    self.animations_enabled=not self.animations_enabled
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
        self._panel(pygame.Rect(420,170,650,660),(23,40,53),cfg.GOLD,19)
        self._text('AUCTIONHAMMER',46,746,223,cfg.GOLD,center=True)
        self._text('MINIMAL FANTASY · GAME MASTER v19',16,746,269,cfg.MUTED,center=True)
        if self.menu_page=='main':
            items=('NOWY MECZ','KONTYNUUJ','WCZYTAJ ZAPIS',
                   'USTAWIENIA','WRÓĆ DO GRY')
        else:
            items=(f'ANIMACJE: {"WŁ." if self.animations_enabled else "WYŁ."}',
                   'PEŁNY EKRAN [F11]',f'AI: {self.ai.difficulty.upper()}',
                   'ZAPISZ MECZ','POWRÓT DO MENU')
        for i,label in enumerate(items):
            self._button(pygame.Rect(535,322+i*81,420,61),label,accent=i==0)
        if self.menu_message:
            status=self.cards_view.clip(self.menu_message,self.fonts[14],620)
            self._text(status,14,746,753,cfg.GOLD,center=True)
        self._text('70 kart · bez aukcji · [O] FOLDER OSTATNIEGO AUDYTU',13,
                   746,790,cfg.MUTED,center=True)

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
            turn=f'R{item["round"]:02} · {"GRACZ" if item["active"]==0 else "AI"}'
            self._text(f'{item["seq"]:04}',13,179,yy,cfg.GOLD)
            self._text(turn,13,232,yy,cfg.MUTED)
            line=self.cards_view.clip(item['text'],self.fonts[14],873)
            self._text(line,14,390,yy,cfg.TEXT)
        self._text('Pełny dziennik pozostaje dostępny przez cały mecz.',13,174,866,cfg.MUTED)

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
            label=f'{p.name}: {max(0,min(100,p.hp))} PŻ  ·  {len(p.grave)} utraconych jednostek  ·  {p.coins} monet'
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
            self._draw_attack_targets()
            self._draw_sidebar()
            self._draw_log()
            self._draw_choices()
            self._draw_gameover()
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
