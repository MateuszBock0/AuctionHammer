"""AuctionHammer UI: v23 game client, card art progression and gameplay clarity."""
from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path
import pygame
from game.ui.combat_visuals import CombatVisuals
from game.ui.ability_feedback import AbilityFeedback
from game.ui.music import FantasyTavernMusic
from game.ui.sfx import QuietSFX,load_levels,save_levels
from game.ui.visual_theme import (
    VisualTheme, TAVERN_PANEL_BG, TAVERN_PANEL_INNER, TAVERN_TOOLTIP_BG,
    TAVERN_GOLD, TAVERN_BRASS, TAVERN_HOVER_GOLD, TAVERN_TEXT,
    TAVERN_MUTED, TAVERN_SCRIM
)
from game.ui.match_history import MatchRecorder
from game.ui.match_summary import build_match_summary
from game.core.persistence import save_match, load_match, save_path
from game.core.audit import (audit_path, archive_path, list_archived_matches,
                             write_last_match, initialize_audit,
                             configure_audit_context, record_ai_difficulty)
from game import config as cfg
from game.core.engine import Match
from game.core.auction_catalog import CATALOG,RARITIES,live_variant,v23_variant,catalog_for
from game.core.ai import ComputerOpponent
from game.core.models import IllegalMove
from game.ui.card_view import (CardView, FACTION_COLORS, ART, PIXEL_ART_IDS,
                               standard_hit_damage,
                               CHORAZY_ART_LEVELS, status_display_priority)
from game.ui.assets import ROOT_DIR
from game.ui.card_infographics import (card_cue, highlighted_numeric_ranges,
                                       AUCTION_MECHANIC_LABELS)
from game.ui.auction_badges import draw_trigger_icon, TRIGGER_NAMES
from game.ui.card_summary import ability_summary
from game.ui.v23_help import v23_base_card_note, v23_base_card_short_note
from game.ui.auction_copy import (preview_auction_copy, full_preview_auction_copy,
                                  identify_auction_variant)
from game.ui.rarity_view import card_rarity
from game.ui.attack_view import attack_display, inactive_card_reason
from game.ui.gameplay_clarity import turn_readout, selected_card_readout, combat_notice
from game.ui.decision_clarity import economy_cue, positional_cues
from game.ui.aura_links import live_aura_links
from game.ui.onboarding import TutorialProgress, HELP_PAGES, attack_reason_help
from game.core.status_view import active_statuses, hand_grants, STATUS_COLORS
from game.ui.layout import fitted_viewport, window_to_canvas, preferred_window_size
from game.ui.text_fit import wrap_pixels
from game.ui.beer_fx import beer_fx_state,beer_overflow_state,board_spill_timeline,slot_flame_strength,tavern_flame_intensity
from game.ui.tavern_help import brawl_help_lines
from game.ui.decision_preview import (preview_standard_attack,preview_replacement,
                                      brawl_at_risk,next_brawl_damage)
from game.ui.tavern_art import draw_tavern_rail,draw_board_spill,draw_slot_flamelets

# Auction-only accent colors: brown, silver, gold.
# Keep rarity colors on hand cards and the battlefield unchanged.
AUCTION_RARITY_COLORS = {
    'podstawowa': (196, 148, 99),
    'rzadka': (215, 222, 230),
    'legendarna': (255, 213, 111),
}

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
    DRAG_THRESHOLD_SQ=100  # 10 px: distinguish drags from clicks.
    DRAG_RETURN_MS=180     # Cosmetic only; no Match state mutation.
    HAND_LEVEL_FX_MS=1050  # Read-only celebration after each 3 turns in hand.

    def __init__(self,start_in_menu=False):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        self.audio_levels=load_levels()
        self.music = FantasyTavernMusic(volume=self.audio_levels['music'])
        self.sfx = QuietSFX(volume=self.audio_levels['sfx'])
        # Fit the opening window to the current display, respecting Windows DPI
        # scaling and keeping room for the title bar and taskbar.
        # The internal canvas and all clickable hitboxes retain their v17 size.
        logical_size=(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT)
        desktop_size=self._desktop_resolution()
        self.windowed_size=preferred_window_size(desktop_size,logical_size)
        self.window=pygame.display.set_mode(self.windowed_size,pygame.RESIZABLE)
        self.screen=pygame.Surface(logical_size).convert()
        # The exact same heraldic icon is embedded in the Windows executable.
        # Non-Windows/development startup stays safe if the optional art is absent.
        icon_path=ROOT_DIR/'assets'/'branding'/'chorazy_zawsze_zdazy_icon.png'
        if icon_path.is_file():
            try:
                pygame.display.set_icon(pygame.image.load(str(icon_path)).convert_alpha())
            except (pygame.error,OSError):
                pass
        pygame.display.set_caption(cfg.WINDOW_TITLE)
        self.clock=pygame.time.Clock()
        self.fonts={n:pygame.font.SysFont('segoeui',n,bold=(n>=22)) for n in (11,12,13,14,15,16,18,20,22,28,34,46)}
        self.theme=VisualTheme()
        self.cards_view=CardView()
        self._sidebar_desc_uid=None
        self._sidebar_desc_scroll=0
        self._sidebar_desc_maxscroll=0
        self.auction_art_regions=[]
        self.detail_art_regions=[]
        self.fonts_bold={n:pygame.font.SysFont('segoeui',n,bold=True) for n in (13,14,16,18,20,22)}
        self.ai=ComputerOpponent()
        self.bg=self._create_background()
        self.animations_enabled=True
        self.ai_speed_index=1  # 0: calm, 1: normal, 2: fast; cosmetic pacing only
        self.tutorial=TutorialProgress()
        self.help_open=False
        self.help_page=0
        self._start_tutorial_after_restart=False
        # Local UI session only: computer opens game 1, human opens game 2,
        # then alternate. The engine's seeded/random first-player rule stays
        # unchanged for archives, replay tools and headless simulations.
        self._next_first_player=1
        self._first_menu_game_unused=False
        self.restart()
        # The opening menu has a pre-created game behind it. Starting from
        # that menu should use it rather than silently skip game number one.
        self._first_menu_game_unused=bool(start_in_menu)
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

    @staticmethod
    def _match_with_first_player(first):
        """Select a fresh random seed with the requested opening seat.

        Match remains the sole authority on first-player selection, including
        its original RNG draw order. This preserves signed replay verification:
        replaying the chosen seed without any UI reproduces the same start.
        Rejected candidates are never shown, recorded, or saved.
        """
        if first not in (0,1):
            raise ValueError('Nieprawidłowy gracz rozpoczynający')
        for _ in range(128):
            candidate=Match(audit_enabled=True,auctions_enabled=True,
                            auction_catalog='v22',
                            starting_compensation='choice_2_5_or_coins',
                            fixed_board_slots=True,
                            tavern_price_v2_enabled=True,
                            tavern_scaled_damage_enabled=True,
                            tavern_min_hp_damage_enabled=True)
            if candidate.first==first:
                return candidate
        raise RuntimeError('Nie znaleziono losowania właściwej kolejności')

    def restart(self):
        if hasattr(self,'game') and self.game.phase=='finished':
            self._export_finished_audit_once()
        self.tutorial.active=False
        self.tutorial_welcome_open=False
        self.help_open=False
        self._first_menu_game_unused=False
        # UI creates game #1 with human second (first=1), game #2 with
        # computer second (first=0), and alternates from there.
        first=self._next_first_player
        self.game=self._match_with_first_player(first)
        self._next_first_player=1-first
        configure_audit_context(self.game,self.ai.difficulty,fresh=True)
        self._audit_saved_match=None
        self._audit_notice=''
        self.auction_bid_text=''  # legacy UI compatibility only
        self.auction_slider_value=None
        self.auction_slider_key=None
        self.auction_slider_dragging=False
        self.auction_status=''
        self.auction_inspect_index=None
        self.auction_inspect_scroll=0
        self.ai.step(self.game)  # One audited command per step, even during mulligan.
        if self.game.phase=='mulligan' and 1 not in self.game.mulligan_done:
            # AI was second and chose its compensation; now finish its own
            # hidden mulligan without exposing or evaluating the human hand.
            self.ai.step(self.game)
        self.selected=None
        self.hover=None
        self._hover_uid=None
        self._hover_start_ms=0
        self.scroll=0
        self.choice_page=0
        self.last_error=''
        self.last_ai_ms=0
        self.drag_start=None
        self.drag_pointer=None
        self.drag_return=None
        self._end_turn_warning=None
        self._reset_hand_growth_tracking()
        self.tooltip_open=False
        self.details_card=None
        self.details_scroll=0
        self.details_image_zoom=False
        self.sidebar_card=None
        self._old_pending=None
        self._recent_feedback=[]
        self.combat_notice_active=None
        self.combat_notice_queue=[]
        self.attack_outcome_active=None
        self.attack_outcome_latest=None
        self._last_handled_attack_outcome=None
        self.visual_notice=''
        self.visual_notice_tick=-10000
        self._last_logged_event=len(self.game.event_journal)
        self.combat_visuals=CombatVisuals()
        self.combat_visuals.sync(self.game,self.slot_rect,self.hero_rect,pygame.time.get_ticks())
        self.ability_feedback=AbilityFeedback()
        self.ability_feedback.reset(self.game)
        self.sfx.reset(self.game)
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

    def _open_combat_book(self):
        """Open the offline Księga Starć only AFTER a finished match."""
        from game.core.combat_html import FILENAME as COMBAT_HTML_FILENAME
        report=audit_path().with_name(COMBAT_HTML_FILENAME)
        if not report.is_file() and self.game.phase=='finished':
            self._export_finished_audit_once(force=True)
        if not report.is_file():
            self._audit_notice='BRAK KSIĘGI STARC — najpierw zakończ mecz.'
            return False
        try:
            if os.name=='nt':
                os.startfile(str(report))
            else:
                subprocess.Popen(['xdg-open',str(report)],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            return True
        except (OSError,AttributeError) as exc:
            self._audit_notice='Nie można otworzyć Księgi Starć: '+str(exc)
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
        self.drag_pointer=None
        self.drag_return=None

    def _viewport(self):
        return pygame.Rect(*fitted_viewport(self.window.get_size(),(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT)))

    def _physical_to_virtual(self,pos):
        result=window_to_canvas(pos,tuple(self._viewport()),(cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT))
        return result if result is not None else (-10000,-10000)

    def mouse_pos(self):
        return self._physical_to_virtual(pygame.mouse.get_pos())

    def _floating_hand_card(self):
        """Read-only dragged/returning hand card and its canvas rectangle.

        Preserve the original cursor-to-card offset so grabbing a corner
        does not snap the card center to the mouse. All positions are in
        logical canvas coordinates, including on scaled Windows displays.
        """
        player=self.game.players[0]
        if (self.drag_start is not None and self.game.phase=='turn'
                and self.game.active==0 and self.game.pending is None
                and not (self.menu_open or self.history_open
                         or self.replay_index is not None or self.details_card
                         or self.confirm_action or self.help_open)):
            start,uid=self.drag_start
            pointer=self.drag_pointer if self.drag_pointer is not None else start
            distance=(pointer[0]-start[0])**2+(pointer[1]-start[1])**2
            if uid in player.hand and distance>self.DRAG_THRESHOLD_SQ:
                origin=self.hand_layout().get(uid)
                if origin is not None:
                    return (uid,origin.move(pointer[0]-start[0],
                                            pointer[1]-start[1]),False)
        if self.drag_return is not None:
            uid,start,started=self.drag_return
            if uid not in player.hand:
                self.drag_return=None
                return None
            target=self.hand_layout().get(uid)
            if target is None:
                self.drag_return=None
                return None
            elapsed=max(0,pygame.time.get_ticks()-started)
            if elapsed>=self.DRAG_RETURN_MS:
                self.drag_return=None
                return None
            progress=elapsed/self.DRAG_RETURN_MS
            ease=1-(1-progress)**3
            left=round(start[0]+(target.x-start[0])*ease)
            top=round(start[1]+(target.y-start[1])*ease)
            return (uid,pygame.Rect(left,top,target.width,target.height),True)
        return None

    def _queue_drag_return(self,uid,rect):
        """Animate an invalid drop back to hand, without playing a card."""
        if not self.animations_enabled or rect is None:
            return
        destination=self.hand_layout().get(uid)
        if destination is not None and rect.topleft!=destination.topleft:
            self.drag_return=(uid,rect.topleft,pygame.time.get_ticks())

    def _draw_drag_overlay(self):
        """Draw the floating card above the board, without intercepting input."""
        floating=self._floating_hand_card()
        if floating is None:
            return
        uid,rect,returning=floating
        shadow=rect.move(6,8)
        pygame.draw.rect(self.screen,(9,17,24),shadow,border_radius=12)
        pointer=self.drag_pointer
        valid=(not returning and pointer is not None
               and any(target.collidepoint(pointer)
                       for target in self._play_target_rects()))
        outline=(238,187,83) if valid else (113,214,223)
        self.cards_view.draw(
            self.screen,self.game.cards[uid],rect,hover=True,
            rarity=self.game.auction_awards.get(uid,{}).get('rarity'),
            animate_rarity=self.animations_enabled,
            statuses=hand_grants(self.game,uid))
        pygame.draw.rect(self.screen,outline,rect.inflate(4,4),
                         3 if valid else 2,border_radius=12)

    def _attack_drag_state(self):
        """Read-only in-flight attack selection from an allied board unit."""
        # Historical read-only tests construct SoloApp without __init__.
        if (getattr(self,'drag_start',None) is None
                or getattr(self,'drag_pointer',None) is None):
            return None
        if (self.menu_open or self.history_open or self.help_open
                or self.replay_index is not None or self.details_card is not None
                or self.confirm_action or self.tutorial_welcome_open
                or self.game.phase!='turn' or self.game.active!=0
                or self.game.pending is not None):
            return None
        start,uid=self.drag_start
        point=self.drag_pointer
        if uid not in self.game.players[0].board or uid not in self.game.units:
            return None
        if (point[0]-start[0])**2+(point[1]-start[1])**2<=self.DRAG_THRESHOLD_SQ:
            return None
        targets=self.game.legal_attacks(uid)
        if not targets:
            return None
        hovered=self.target_under(point)
        return (uid,point,hovered if hovered in targets else None)

    def _draw_attack_drag(self):
        """A faint red aiming cue only while actually dragging an attacker.

        Uses a small temporary RGBA canvas so opacity is genuine, not a
        simulated opaque pink stroke. Never changes game state or hitboxes.
        The cursor stays unobstructed and valid targets retain their outlines.
        """
        state=self._attack_drag_state()
        if state is None:
            return
        uid,pointer,valid=state
        if not pygame.Rect(0,0,cfg.WINDOW_WIDTH,cfg.WINDOW_HEIGHT).collidepoint(pointer):
            return
        src=self.slot_rect(0,self.game.slot_of(uid))
        if src.inflate(10,10).collidepoint(pointer):
            return  # No backwards arrow when the mouse is still over source.
        direction=pygame.Vector2(pointer)-pygame.Vector2(src.center)
        if direction.length_squared()<1:
            return
        scale=max(abs(direction.x)/(src.width/2),
                  abs(direction.y)/(src.height/2))
        if scale<=0:
            return
        unit=direction.normalize()
        start=pygame.Vector2(src.center)+direction/scale+unit*3
        tip=pygame.Vector2(pointer)-unit*11
        if (tip-start).length_squared()<100:
            return
        tail=tip-unit*8
        side=pygame.Vector2(-unit.y,unit.x)*3.5
        vertices=(tip,tail+side,tail-side)
        xs=[start.x,tip.x]+[v.x for v in vertices]
        ys=[start.y,tip.y]+[v.y for v in vertices]
        bounds=pygame.Rect(int(min(xs))-4,int(min(ys))-4,
                           int(max(xs)-min(xs))+9,int(max(ys)-min(ys))+9)
        layer=pygame.Surface(bounds.size,pygame.SRCALPHA)
        color=(207,84,96,77 if valid is not None else 49)
        local=lambda p:(round(p.x-bounds.x),round(p.y-bounds.y))
        pygame.draw.line(layer,color,local(start),local(tip),2)
        pygame.draw.polygon(layer,color,[local(v) for v in vertices])
        self.screen.blit(layer,bounds.topleft)

    def _reset_hand_growth_tracking(self):
        """Loading/new games establish baseline; no artificial level-up."""
        game=self.game
        self._hand_growth_game=game
        self._hand_growth_seen={
            uid:(game.cards[uid].hand_turns,
                 game.cards[uid].attack,game.cards[uid].max_hp)
            for uid in game.players[0].hand
        }
        self._hand_level_fx={}

    def _sync_hand_growth(self,now=None):
        """Detect actual committed level changes without altering Match."""
        if getattr(self,'_hand_growth_game',None) is not self.game:
            self._reset_hand_growth_tracking()
            return
        if now is None:
            now=pygame.time.get_ticks()
        previous=self._hand_growth_seen
        updated={}
        for uid in self.game.players[0].hand:
            card=self.game.cards[uid]
            latest=(card.hand_turns,card.attack,card.max_hp)
            before=previous.get(uid)
            if (before is not None and latest[0]//3>before[0]//3
                    and uid not in self.game.auction_awards
                    and self.animations_enabled):
                self._hand_level_fx[uid]=(
                    now,latest[0]//3,latest[1]-before[1],
                    latest[2]-before[2])
            updated[uid]=latest
        self._hand_growth_seen=updated
        self._hand_level_fx={
            uid:fx for uid,fx in self._hand_level_fx.items()
            if uid in updated and 0<=now-fx[0]<self.HAND_LEVEL_FX_MS
        }

    def _draw_hand_level_fx(self,uid,rect):
        """Brief gold glow and grounded ATK/HP changes on the hand card."""
        if not self.animations_enabled or self.replay_index is not None:
            return
        fx=self._hand_level_fx.get(uid)
        if fx is None:
            return
        started,level,atk,hp=fx
        age=pygame.time.get_ticks()-started
        if not 0<=age<self.HAND_LEVEL_FX_MS:
            return
        fade=1-age/self.HAND_LEVEL_FX_MS
        halo=pygame.Surface((rect.width+18,rect.height+18),pygame.SRCALPHA)
        pygame.draw.rect(halo,(255,206,92,round(165*fade)),
                         halo.get_rect().inflate(-8,-8),width=5,
                         border_radius=13)
        self.screen.blit(halo,(rect.x-9,rect.y-9))
        banner=pygame.Rect(rect.x+4,rect.y+76,rect.width-8,42)
        panel=pygame.Surface(banner.size,pygame.SRCALPHA)
        panel.fill((34,35,30,round(237*fade)))
        self.screen.blit(panel,banner.topleft)
        pygame.draw.rect(self.screen,(239,196,102),banner,2,
                         border_radius=5)
        heading=self.fonts_bold[13].render(
            f'AWANS! POZ. {level}',True,(255,223,137))
        changes=self.fonts[11].render(
            f'ATK {atk:+d}  PŻ {hp:+d}',True,(215,253,219))
        self.screen.blit(heading,(banner.centerx-heading.get_width()//2,
                                  banner.y+4))
        self.screen.blit(changes,(banner.centerx-changes.get_width()//2,
                                  banner.y+23))

    HOVER_PREVIEW_DELAY_MS=420

    def _update_hover_target(self,pos,now=None):
        """Track pointer dwell on hand and deployed cards; no Match action/RNG."""
        if now is None:
            now=pygame.time.get_ticks()
        if (self.menu_open or self.history_open or self.replay_index is not None
                or self.details_card is not None or self.confirm_action or self.help_open
                or self.game.phase in ('finished','auction')
                or self._bonus_selection_due() or self.drag_start is not None
                or self.game.pending is not None):
            uid=None
        else:
            uid=self.card_under(pos)
        if uid!=self._hover_uid:
            self._hover_uid=uid
            self._hover_start_ms=now

    def _hover_preview_ready(self,now=None):
        if now is None:
            now=pygame.time.get_ticks()
        uid=self._hover_uid
        if uid in self.game.players[0].hand:
            visible=uid in self.hand_layout()
        elif uid in self.game.units:
            unit=self.game.units[uid]
            visible=uid in self.game.players[unit.owner].board
        else:
            visible=False
        # Don't let a 286x439 preview obscure the opponent while the
        # player is choosing a legal target for a selected attacker.
        if (visible and uid!=self.selected
                and self.selected in self.game.players[0].board
                and self.game.phase=='turn' and self.game.active==0
                and self.game.legal_attacks(self.selected)):
            return False
        return (visible and uid in self.game.cards
                and now-self._hover_start_ms>=self.HOVER_PREVIEW_DELAY_MS
                and not (self.menu_open or self.history_open or self.confirm_action
                         or self.help_open or self.replay_index is not None
                         or self.details_card is not None or self.drag_start is not None
                         or self._bonus_selection_due() or self.game.pending is not None
                         or self.game.phase in ('auction','finished')))

    def _hover_preview_rect(self,uid):
        """Read-only hover panel outside its source unit's board rectangle."""
        if uid in self.game.players[0].hand:
            source=self.hand_layout()[uid]
            left=max(82,min(772,source.centerx-143))
            return pygame.Rect(left,289,286,439)
        unit=self.game.units[uid]
        source=self.slot_rect(unit.owner,self.game.slot_of(uid))
        left=source.right+18 if source.centerx<500 else source.left-304
        left=max(82,min(772,left))
        return pygame.Rect(left,398 if unit.owner==1 else 87,286,439)

    def _hovered_status(self,pos):
        """Find a drawn status badge, never infer undisplayed effects."""
        uid=self.card_under(pos)
        if uid not in self.game.cards:
            return None
        if uid in self.game.units:
            unit=self.game.units[uid]
            rect=self.slot_rect(unit.owner,self.game.slot_of(uid))
            statuses=active_statuses(self.game,uid)
            board=True
        else:
            rect=self.hand_layout().get(uid)
            if rect is None:
                return None
            statuses=hand_grants(self.game,uid)
            board=False
        for status,area,remaining in self.cards_view.visible_status_hitboxes(
                rect,statuses,board=board):
            if area.collidepoint(pos):
                return status,remaining
        return None

    def _draw_hover_guidance(self):
        """Context-only tooltips over the finished board, not inside modals."""
        if (self.menu_open or self.history_open or self.replay_index is not None
                or self.details_card is not None or self.confirm_action
                or self.help_open or self.game.phase in ('auction','finished')
                or self._bonus_selection_due() or self.drag_start is not None
                or self.game.pending is not None):
            return
        pos=self.mouse_pos()
        if self._draw_brawl_hover_help(pos):
            return
        # Optional larger combat reading area, accessible even after the
        # transient two-line ticker expires. Entirely read-only.
        last=getattr(self,'attack_outcome_latest',None)
        if (last is not None and
                pygame.Rect(1099,899,330,49).collidepoint(pos)):
            lines=[f'{last.attacker} → {last.target}' if last.attacker
                   else 'OSTATNIO ROZSTRZYGNIĘTY ATAK']
            for item in (last.details or last.lines):
                lines.extend(self._wrap(item,15,389))
            lines=lines[:9]
            panel=pygame.Rect(668,590,416,56+len(lines)*23)
            panel.bottom=min(panel.bottom,942)
            self._panel(panel,TAVERN_TOOLTIP_BG,(115,223,238),10)
            self._text('PEŁNE SKUTKI OSTATNIEGO ATAKU',15,
                       panel.x+12,panel.y+10,(115,223,238))
            for i,line in enumerate(lines):
                self._text(self.cards_view.clip(line,self.fonts[15],392),
                           15,panel.x+12,panel.y+39+i*23,cfg.TEXT)
            return
        hit=self._hovered_status(pos)
        if hit is not None:
            status,remaining=hit
            title=status.name if status is not None else f'POZOSTAŁE EFEKTY: {len(remaining)}'
            color=status.color if status is not None else cfg.GOLD
            if status is not None:
                items=[status.detail]
                if status.source:
                    items.append('Źródło: '+status.source)
            else:
                items=[f'{st.name}: {st.detail}' for st in remaining[:4]]
                if len(remaining)>4:
                    items.append(f'Jeszcze {len(remaining)-4} efektów — pełny wykaz [I]')
            rows=[]
            for item in items:
                rows.extend(self._wrap(item,13,369))
            rows=rows[:6]
            height=62+23*len(rows)
            rect=pygame.Rect(min(pos[0]+19,cfg.WINDOW_WIDTH-421),
                             min(pos[1]+18,cfg.WINDOW_HEIGHT-height-14),
                             408,height)
            rect.x=max(8,rect.x);rect.y=max(8,rect.y)
            self._panel(rect,TAVERN_TOOLTIP_BG,color,9)
            self._text(self.cards_view.clip(title,self.fonts[16],382),
                       16,rect.x+12,rect.y+9,color)
            for index,row in enumerate(rows):
                self._text(self.cards_view.clip(row,self.fonts[13],380),
                           13,rect.x+12,rect.y+40+index*23,TAVERN_TEXT)
            return
        if not self._hover_preview_ready():
            return
        uid=self._hover_uid
        # Same full-size preview as the hand, but deployed cards use live
        # unit stats, statuses, readiness and exact auction rarity.
        box=self._hover_preview_rect(uid)
        self._panel(box,TAVERN_PANEL_BG,TAVERN_GOLD,11)
        pygame.draw.rect(self.screen,TAVERN_BRASS,box.inflate(-9,-9),
                         1,border_radius=8)
        unit=self.game.units.get(uid)
        if unit is None:
            title='KARTA NA RĘCE · PODGLĄD'
            statuses=hand_grants(self.game,uid)
        else:
            title=('TWOJA JEDNOSTKA · PODGLĄD' if unit.owner==0
                   else 'JEDNOSTKA RYWALA · PODGLĄD')
            statuses=active_statuses(self.game,uid)
        self._text(self.cards_view.clip(title,self.fonts[13],260),
                   13,box.x+13,box.y+11,TAVERN_GOLD)
        card=self.game.cards[uid]
        params={}
        if unit is not None:
            attack=attack_display(self.game,uid)
            params=dict(attacks_remaining=attack.remaining,
                        attacks_total=attack.limit,ready=attack.ready,
                        guard_kills=self._guard_progress(uid))
        self.cards_view.draw(
            self.screen,card,pygame.Rect(box.x+15,box.y+34,255,380),
            unit=unit,statuses=statuses,
            rarity=self.game.auction_awards.get(uid,{}).get('rarity'),
            animate_rarity=self.animations_enabled,**params)
        self._text('PRAWY KLIK — PEŁNY OPIS' if unit is not None
                   else 'PRAWY KLIK / [I] — PEŁNY OPIS',12,
                   box.x+13,box.bottom-20,TAVERN_MUTED)

    def _visible_pixel_art_regions(self):
        """Restore only images belonging to the visible layer, not hidden UI."""
        if (self.menu_open or self.help_open or self.history_open
                or self.confirm_action or self.tutorial_welcome_open
                or self.replay_index is not None or self._bonus_selection_due()
                or self.game.phase=='finished'):
            return ()
        if self.details_card is not None:
            return tuple(self.detail_art_regions)
        if self.game.phase=='auction':
            return tuple(self.auction_art_regions[-1:]
                         if self.auction_inspect_index is not None
                         else self.auction_art_regions)
        return tuple(self.cards_view.pixel_art_regions)

    def _present(self):
        viewport=self._viewport()
        self.window.fill((5,9,14))
        if viewport.size==self.screen.get_size():
            self.window.blit(self.screen,viewport.topleft)
        else:
            # Fractional nearest-neighbour resizing deletes thin Segoe UI
            # strokes. Smooth the finished text/UI but preserve original
            # portraits with an exact nearest-neighbour image-only composite.
            # All logical hitboxes remain unchanged.
            ui=pygame.transform.smoothscale(self.screen,viewport.size)
            self.window.blit(ui,viewport.topleft)
            regions=self._visible_pixel_art_regions()
            if regions:
                pixel=pygame.transform.scale(self.screen,viewport.size)
                logical=self.screen.get_rect()
                for rect in regions:
                    src=pygame.Rect(rect).clip(logical)
                    if not src:
                        continue
                    left=round(src.left*viewport.width/logical.width)
                    top=round(src.top*viewport.height/logical.height)
                    right=round(src.right*viewport.width/logical.width)
                    bottom=round(src.bottom*viewport.height/logical.height)
                    if right<=left or bottom<=top:
                        continue
                    area=pygame.Rect(left,top,right-left,bottom-top)
                    self.window.blit(pixel,(viewport.x+left,viewport.y+top),area)
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
        """Measured wrapping: long unbroken terms never leave their panel."""
        return list(wrap_pixels(text,self.fonts[size],maxwidth))

    def _infographic_box(self,rect,title,value,color,subtitle=''):
        self._panel(rect,TAVERN_PANEL_INNER,color,9)
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
        self.theme.panel(self.screen,rect,fill or TAVERN_PANEL_BG,
                         line or TAVERN_BRASS,radius)

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

    def slot_under(self,owner,pos):
        for index in range(5):
            if self.slot_rect(owner,index).collidepoint(pos):
                return index
        return None

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
            for uid in p.board:
                if self.slot_rect(idx,self.game.slot_of(uid)).collidepoint(pos):return uid
        return None

    def target_under(self,pos):
        for idx in (0,1):
            if self.hero_rect(idx).collidepoint(pos):return f'hero:{idx}'
            for uid in self.game.players[idx].board:
                if self.slot_rect(idx,self.game.slot_of(uid)).collidepoint(pos):return uid
        return None

    # Choice controls are confined to their own panel below the skill description.
    CHOICES_PER_PAGE = 6
    CHOICE_FIRST_Y = 467
    CHOICE_ROW_HEIGHT = 54
    AI_ACTION_DELAY_MS = 480
    AI_SPEED_LEVELS = (('SPOKOJNE',750), ('STANDARD',480), ('SZYBKIE',280))

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
        else:
            if pending and pending.context == 'attack':
                self._release_exhausted_attacker()
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

    def _queen_board_choice(self,pos):
        """Map an A010 end-turn decision to the intuitive live-board click.

        Clicking the Queen means growth; clicking an empty friendly slot
        means summoning. These select existing engine choices only: the
        simulation remains responsible for legal choices and spawn slots.
        """
        pending=self.game.pending
        if (pending is None or pending.owner!=0 or pending.context!='end'
                or pending.uid not in self.game.players[0].board
                or self.game.auction_awards.get(pending.uid,{}).get('archetype')!='A010'):
            return None
        if self.target_under(pos)==pending.uid:
            mode='grow'
        else:
            slot=self.slot_under(0,pos)
            if (slot is None or self.game.unit_at(0,slot) is not None
                    or len(self.game.players[0].board)>=5):
                return None
            mode='summon'
        matches=[i for i,ch in enumerate(pending.choices) if ch.mode==mode]
        return matches[0] if len(matches)==1 else None

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
            elif pygame.Rect(885,637,239,52).collidepoint(pos):
                self._open_combat_book()
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
            queen_choice=self._queen_board_choice(pos)
            if queen_choice is not None:
                self._choose(queen_choice)
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
                        self.selected=uid if uid in g.players[0].mulligan_selected else None
                        self.last_error=''
                    except IllegalMove as e:self.last_error=str(e)
                    return
            if pygame.Rect(1182,808,243,59).collidepoint(pos):
                try:g.finish_mulligan(0)
                except IllegalMove as e:self.last_error=str(e)
                self.selected=None
            return
        if self.beer_buy_rect().collidepoint(pos) and g.phase=='turn':
            self._order_tavern_beer()
            return
        if pygame.Rect(1201,816,221,52).collidepoint(pos):
            self._request_end_turn()
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
            self.tooltip_open=self.selected is not None;return
        target=self.target_under(pos)
        if g.active==0:
            if self.selected in g.players[0].hand:
                target_slot=self.slot_under(0,pos)
                if target_slot is not None:
                    replace=target if target in g.players[0].board and len(g.players[0].board)==5 else None
                    chosen_slot=target_slot if g.fixed_board_slots else None
                    if (target in g.players[0].board and
                            (len(g.players[0].board)<5 or
                             not g.can_play(0,self.selected,replace,chosen_slot))):
                        # A hand-card preview must not prevent selecting an ally
                        # when placing/replacing it here is not a legal move.
                        self.selected=target
                        self.tooltip_open=True
                        self.last_error=''
                        return
                    self._try_play(self.selected,replace,target_slot)
                    return
                if target is None:
                    self.selected=None
                    self.tooltip_open=False
                    return
            if self.selected in g.players[0].board and target is not None and (target in g.players[1].board or target=='hero:1'):
                self._try_attack(self.selected,target)
                return
            if target in g.players[0].board:
                self.selected=target if self.selected!=target else None
                self.tooltip_open=True;return
        if target in g.units:self.selected=target;self.tooltip_open=True

    @staticmethod
    def auction_offer_rect(index):
        # Card bottom remains clear of the bidding HUD; grow vertically UP.
        return pygame.Rect(271+index*318,159,278,461)

    @staticmethod
    def auction_offer_zones(index):
        """Measured, mutually exclusive text/art/interaction slots."""
        r=SoloApp.auction_offer_rect(index)
        return {
            'name':pygame.Rect(r.x+12,r.y+34,r.width-24,36),
            'art':pygame.Rect(r.x+14,r.y+84,116,116),
            'atk':pygame.Rect(r.x+142,r.y+96,r.width-153,28),
            'hp':pygame.Rect(r.x+142,r.y+141,r.width-153,28),
            'rarity':pygame.Rect(r.x+13,r.y+215,r.width-26,22),
            'trigger':pygame.Rect(r.x+13,r.y+244,r.width-26,25),
            'description':pygame.Rect(r.x+18,r.y+282,r.width-36,103),
            'inspect':pygame.Rect(r.x+26,r.y+395,r.width-52,35),
            'hint':pygame.Rect(r.x+18,r.y+437,r.width-36,18),
        }

    @staticmethod
    def auction_bid_tiles():
        """Leading offer, own bid and secondary totals; no text collisions."""
        return {
            'leader':pygame.Rect(271,633,452,74),
            'own':pygame.Rect(736,633,452,74),
            'summary':pygame.Rect(271,713,917,21),
        }

    @staticmethod
    def auction_badge_rects(index):
        """Two small, fixed pixel-art tiles outside each offer title."""
        rect=SoloApp.auction_offer_rect(index)
        return (pygame.Rect(rect.x+9,rect.y+5,23,23),
                pygame.Rect(rect.right-32,rect.y+5,23,23))

    @staticmethod
    def auction_control_rect(action):
        return {
            'pass':pygame.Rect(528,773,210,45),
            'bid':pygame.Rect(759,773,210,45),
        }[action]

    @staticmethod
    def auction_slider_rect():
        return pygame.Rect(483,746,516,14)

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

    @staticmethod
    def auction_inspection_rect(index):
        rect=SoloApp.auction_offer_rect(index)
        return SoloApp.auction_offer_zones(index)['inspect']

    def _auction_click(self,pos):
        a=self.game.auction
        if a is None:return
        # Inspecting an offer never submits a bid or purchases the card.
        for i in range(len(a.offers)):
            if self.auction_inspection_rect(i).collidepoint(pos):
                self.auction_inspect_index=i
                self.auction_inspect_scroll=0
                return
        if a.turn!=0:return
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

    def _draw_auction_inspection(self):
        a=self.game.auction
        index=self.auction_inspect_index
        if (self.game.phase!='auction' or a is None or index is None
                or index>=len(a.offers)):
            return
        offer=a.offers[index]
        definition=catalog_for(self.game.auction_catalog).get(offer.archetype)
        raw=(v23_variant(self.game.auction_catalog,offer.archetype,
                         offer.rarity,getattr(self.game,'ruleset_version','v22'),
                         getattr(self.game,'general_friendly_only',False))
             if definition is not None and self.game.auction_catalog in ('v4','v22')
             else definition.abilities[RARITIES.index(offer.rarity)]
             if definition is not None else 'Nie znaleziono definicji.')
        description=full_preview_auction_copy(
            offer.archetype,offer.rarity,
            getattr(self.game,'ruleset_version','v22'),raw)
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((*TAVERN_SCRIM,240));self.screen.blit(shade,(0,0))
        rect=pygame.Rect(255,190,972,593)
        rarity_accent=AUCTION_RARITY_COLORS[offer.rarity]
        self._panel(rect,TAVERN_PANEL_INNER,rarity_accent,18)
        if offer.rarity=='legendarna':
            self.theme.legendary_offer_ornament(
                self.screen,rect,animate=self.animations_enabled)
        name=definition.name if definition is not None else offer.archetype
        sprite=self.cards_view.images.get_auction_image(
            offer.archetype,offer.rarity,(106,106),mode='contain')
        name_width=742 if sprite is not None else 890
        self._text(self.cards_view.clip(name,self.fonts[28],name_width),
                   28,294,226,cfg.GOLD)
        self._text(self.cards_view.clip(
                   f'OFERTA {index+1}  ·  {offer.rarity.upper()}  ·  '
                   f'{offer.atk} ATK / {offer.hp} PŻ',self.fonts[16],name_width),
                   16,296,282,rarity_accent)
        if sprite is not None:
            portrait=pygame.Rect(1075,216,106,106)
            dominant=self.cards_view.images.get_auction_color(
                offer.archetype,offer.rarity)
            if dominant is not None:
                pygame.draw.rect(self.screen,dominant,
                                 portrait.inflate(12,12),border_radius=10)
            self.screen.blit(sprite,portrait)
            self.auction_art_regions.append(portrait.copy())
            pygame.draw.rect(self.screen,rarity_accent,portrait,2,border_radius=7)
        self._text('PEŁNY OPIS ZDOLNOŚCI',18,296,335,cfg.GOLD)
        lines=self._wrap(description,18,853)
        visible=12
        maximum=max(0,len(lines)-visible)
        self.auction_inspect_scroll=max(0,min(
            getattr(self,'auction_inspect_scroll',0),maximum))
        start=self.auction_inspect_scroll
        for i,line in enumerate(lines[start:start+visible]):
            self._text(line,18,296,378+i*25,cfg.TEXT)
        if maximum:
            self._text(f'OPIS: LINIE {start+1}–{min(len(lines),start+visible)}'
                       f'/{len(lines)}  ·  PRZEWIJAJ KÓŁKIEM MYSZY',
                       13,296,688,cfg.MUTED)
        self._button(pygame.Rect(934,710,239,49),'ZAMKNIJ  [ESC]',small=True)

    def _draw_auction(self):
        a=self.game.auction
        if self.game.phase!='auction' or a is None:return
        overlay=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        overlay.fill((*TAVERN_SCRIM,225))
        self.screen.blit(overlay,(0,0))
        # Reclaim the unused top gutter for vertically taller offers.
        self._panel(pygame.Rect(203,25,1076,819),TAVERN_PANEL_BG,TAVERN_GOLD,12)
        self.theme.carved_panel(self.screen,pygame.Rect(219,36,1044,786),opacity=82)
        self._text(f'AUKCJA {a.number} · PO RUNDZIE {a.completed_round}',28,
                   741,67,cfg.GOLD,center=True)
        self._text('17 ARCHETYPÓW · 51 AKTYWNYCH WARIANTÓW ZDOLNOŚCI',16,
                   741,108,cfg.TEXT,center=True)
        self.theme.ornament(self.screen,565,132,350,18)
        for i,off in enumerate(a.offers):
            rect=self.auction_offer_rect(i)
            claimed=off.uid in a.picks.values()
            selectable=a.phase=='picking' and a.turn==0 and not claimed
            tier_accent=AUCTION_RARITY_COLORS[off.rarity]
            self._panel(rect,(52,37,26) if not claimed else (38,34,29),
                        tier_accent if not claimed else cfg.PANEL_BORDER,14)
            # Rarity framing belongs to auction offers only.
            pygame.draw.rect(self.screen,tier_accent,rect.inflate(-3,-3),
                             4 if off.rarity=='legendarna' else
                             3 if off.rarity=='rzadka' else 2,border_radius=13)
            self.theme.carved_panel(self.screen,rect.inflate(-8,-8),opacity=72)
            if off.rarity=='rzadka':
                pygame.draw.rect(self.screen,(112,124,139),
                                 rect.inflate(-9,-9),1,border_radius=11)
            elif off.rarity=='legendarna':
                pygame.draw.rect(self.screen,(251,223,145),
                                 rect.inflate(-10,-10),1,border_radius=11)
                self.theme.legendary_offer_ornament(
                    self.screen,rect,animate=self.animations_enabled)
            adef=catalog_for(self.game.auction_catalog).get(off.archetype)
            self._text(f'OFERTA {i+1} · {off.archetype or "ARCHIWALNA"}',14,
                       rect.centerx,rect.y+17,cfg.GOLD,center=True)
            hint=None
            if adef is not None:
                trigger_icon,family_icon=self.auction_badge_rects(i)
                draw_trigger_icon(self.screen,trigger_icon,adef.trigger)
                pygame.draw.rect(self.screen,(29,38,43),family_icon)
                pygame.draw.rect(self.screen,tier_accent,family_icon,1)
                icon=self.cards_view.icons.get(adef.family,'families',19)
                if icon is not None:
                    self.screen.blit(icon,icon.get_rect(center=family_icon.center))
                pointer=self.mouse_pos()
                if trigger_icon.collidepoint(pointer):
                    hint='AKTYWACJA: '+TRIGGER_NAMES.get(adef.trigger,'INNA')
                elif family_icon.collidepoint(pointer):
                    hint=('MECHANIKA: '+
                          AUCTION_MECHANIC_LABELS.get(off.archetype,adef.family.upper()))

            zones=self.auction_offer_zones(i)
            name=adef.name if adef else f'Strażnik aukcji {off.hp} PŻ'
            self._text(self.cards_view.clip(name,self.fonts[16],zones['name'].width),
                       16,zones['name'].centerx,zones['name'].centery,
                       cfg.TEXT,center=True)

            # Keep the portrait intact: every label now has a separate
            # opaque pixel-art strip BELOW the image, never across faces.
            artbox=zones['art']
            # Square offers ONLY: 295x209 -> 116x116 with ordinary cover
            # has ZERO vertical overflow, so focus_y alone is a no-op.
            # Small 8% zoom creates room to crop lower scenery; top anchor
            # preserves the first source row, faces and upper-body detail.
            # Full-sized previews, banners and all gameplay UI stay intact.
            portrait=self.cards_view.images.get_auction_image(
                off.archetype,off.rarity,artbox.size,mode='cover',
                focus=(0.5,0.0),zoom=1.08)
            if portrait is not None:
                self.auction_art_regions.append(artbox.copy())
                dominant=self.cards_view.images.get_auction_color(
                    off.archetype,off.rarity)
                if dominant is not None:
                    pygame.draw.rect(self.screen,dominant,artbox.inflate(6,6))
                self.screen.blit(portrait,artbox)
                pygame.draw.rect(self.screen,tier_accent,artbox,2)
            else:
                pygame.draw.rect(self.screen,(42,33,29),artbox)
                pygame.draw.rect(self.screen,tier_accent,artbox,1)
            for key,value in (('atk',f'ATAK {off.atk}'),
                              ('hp',f'PŻ {off.hp}')):
                slot=zones[key]
                self._text(self.cards_view.clip(value,self.fonts[18],slot.width),
                           18,slot.left,slot.top+2,
                           cfg.GREEN if not claimed else cfg.MUTED)

            rarity=zones['rarity']
            pygame.draw.rect(self.screen,(42,32,26),rarity)
            pygame.draw.rect(self.screen,tier_accent,rarity,1)
            tier_text=off.rarity.upper()
            level_text=f'POZIOM {off.level}'
            tier_width=self.fonts[16].size(tier_text)[0]
            level_width=self.fonts[12].size(level_text)[0]
            left=rarity.centerx-(tier_width+12+level_width)//2
            self._text(tier_text,16,left,
                       rarity.centery-self.fonts[16].get_height()//2,tier_accent)
            self._text(level_text,12,left+tier_width+12,
                       rarity.centery-self.fonts[12].get_height()//2,cfg.MUTED)

            trigger=zones['trigger']
            pygame.draw.rect(self.screen,(36,31,27),trigger)
            pygame.draw.rect(self.screen,(111,87,59),trigger,1)
            if adef is not None:
                family_name=AUCTION_MECHANIC_LABELS.get(
                    off.archetype,adef.family.upper())
                label=TRIGGER_NAMES.get(adef.trigger,'ZDOLNOŚĆ')+' · '+family_name
            else:
                label='ZDOLNOŚĆ'
            self._text(self.cards_view.clip(label,self.fonts[12],trigger.width-10),
                       12,trigger.centerx,trigger.centery,cfg.GOLD,center=True)

            description=(v23_variant(self.game.auction_catalog,off.archetype,
                                       off.rarity,getattr(self.game,'ruleset_version','v22'),
                                       getattr(self.game,'general_friendly_only',False))
                         if adef and self.game.auction_catalog in ('v4','v22') else
                         'PLANOWANA: '+adef.abilities[RARITIES.index(off.rarity)]
                         if adef else 'Prowokacja i 1 Tarcza po wystawieniu')
            rules=getattr(self.game,'ruleset_version','v22')
            if adef is not None and self.game.auction_catalog=='v22':
                description=preview_auction_copy(off.archetype,off.rarity,rules,
                                                 description)
            desc=zones['description']
            pygame.draw.rect(self.screen,(41,31,26),desc)
            pygame.draw.rect(self.screen,(91,72,50),desc,1)
            lines=wrap_pixels(description,self.fonts[13],desc.width-13,
                              max_lines=5)
            for j,line in enumerate(lines):
                self._text(line,13,desc.centerx,desc.y+13+19*j,
                           cfg.TEXT,center=True)

            self._button(zones['inspect'],'PEŁNA ZDOLNOŚĆ',small=True)
            status=zones['hint']
            if hint is not None:
                notice=self.cards_view.clip(hint,self.fonts[12],status.width)
                self._text(notice,12,status.centerx,status.centery,
                           cfg.GOLD,center=True)
            elif claimed:
                selected_by=next(p for p,card in a.picks.items() if card==off.uid)
                notice=f'WYBRANO: {self.game.players[selected_by].name}'
                self._text(self.cards_view.clip(notice,self.fonts[12],status.width),
                           12,status.centerx,status.centery,cfg.MUTED,center=True)
            elif selectable:
                self._text('KLIKNIJ, ABY WYBRAĆ',12,status.centerx,
                           status.centery,cfg.GOLD,center=True)
            # Only truly purchasable offers respond to hover. Corner-only
            # pixel brackets leave art, rarity and the ability text clear.
            if selectable and rect.collidepoint(self.mouse_pos()):
                self._pixel_attack_corners(self.screen,
                                           rect.inflate(-8,-8),
                                           (249,209,125),length=14)
        if self.tutorial.active:
            hint=self.tutorial.hint(self.game)
            if hint is not None:
                self._text(self.cards_view.clip(hint.detail,self.fonts[13],934),
                           13,741,832,cfg.GOLD,center=True)
        who=self.game.players[a.turn].name
        if a.phase=='bidding':
            minimum,coins=self.auction_slider_bounds()
            leader=('BRAK' if a.highest_bidder is None
                    else self.game.players[a.highest_bidder].name)
            bonus=a.bid_bonus[0] if self.game.auction_catalog=='v22' else 0
            self._sync_auction_slider()
            chosen=self.auction_slider_value
            # Fixed, wood-tone pixel panels with top padding. The actual
            # coin cost and effective bid remain separate authoritative data.
            tiles=self.auction_bid_tiles()
            leader_box=tiles['leader']
            own_box=tiles['own']
            for tile in (leader_box,own_box):
                pygame.draw.rect(self.screen,(43,34,29),tile)
                pygame.draw.rect(self.screen,TAVERN_BRASS,tile,2)
                pygame.draw.rect(self.screen,(95,74,49),tile.inflate(-8,-8),1)
            leader_label='PROWADZI: '+leader
            self._text(self.cards_view.clip(leader_label,self.fonts[14],
                                            leader_box.width-30),14,
                       leader_box.x+16,leader_box.y+12,cfg.TEXT)
            self._text('SKUTECZNA OFERTA',12,leader_box.x+16,
                       leader_box.y+46,cfg.MUTED)
            self._text(str(a.highest_effective),22,leader_box.right-40,
                       leader_box.y+48,cfg.GOLD,center=True)

            self._text('TWOJA OFERTA',14,own_box.x+16,
                       own_box.y+12,cfg.TEXT)
            self._text(str(chosen) if chosen is not None else 'BRAK MONET',
                       22,own_box.x+16,own_box.y+40,
                       cfg.GREEN if chosen is not None else cfg.RED)
            divider=own_box.right-135
            pygame.draw.line(self.screen,(119,92,56),
                             (divider,own_box.y+11),(divider,own_box.bottom-11),2)
            self._text('MINIMUM',12,divider+16,own_box.y+11,cfg.MUTED)
            self._text(str(minimum),18,divider+16,own_box.y+37,cfg.GOLD)
            after_bid=(str(coins-chosen) if chosen is not None else '—')
            effective=(str(chosen+bonus) if chosen is not None else '—')
            summary=tiles['summary']
            caption=(f'BONUS A018 +{bonus}  ·  SKUTECZNA {effective}  ·  '
                     f'MONETY PO WYGRANEJ {after_bid}')
            if minimum>coins:
                caption='BRAK MONET NA PRZEBICIE — PASUJ'
            self._text(self.cards_view.clip(caption,self.fonts[12],summary.width-20),
                       12,summary.centerx,summary.centery,
                       cfg.RED if minimum>coins else cfg.MUTED,center=True)
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
                for action,label in (('pass','PASUJ'),('bid','LICYTUJ [ENTER]')):
                    enabled=action=='pass' or affordable
                    self._button(self.auction_control_rect(action),label,
                                 active=enabled,accent=action=='bid' and enabled,
                                 small=True)
            else:
                self._text('RUCH KOMPUTERA...',16,741,786,cfg.GOLD,center=True)
        else:
            self._text(f'WYBIERA: {who}  ·  ZWYCIĘZCA LICYTACJI: '
                       f'{self.game.players[a.winner].name}  ·  CENA: {a.price}',16,
                       741,671,cfg.TEXT,center=True)
            self._text('Kliknij jedną z dostępnych ofert' if a.turn==0
                       else 'Komputer wybiera kartę...',16,741,786,
                       cfg.GOLD,center=True)
        if self.auction_status:
            self._text(self.cards_view.clip(self.auction_status,self.fonts[13],920),
                       13,741,832,cfg.RED,center=True)

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

    def _release_exhausted_attacker(self):
        """Avoid leaving an attacker selected once its final attack is spent.

        Keep the selection while an attack ability is unresolved, and keep it
        when the unit genuinely has another legal attack (e.g. double attack).
        """
        uid=self.selected
        if (uid in self.game.players[0].board and self.game.pending is None
                and not self.game.legal_attacks(uid)):
            self.selected=None

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

    def _try_attack(self,uid,target):
        """One authoritative attack route for mouse clicks and drag releases."""
        issue=self._attack_issue(uid,target)
        if issue:
            self.last_error=issue
            return False
        try:
            self.game.attack(uid,target)
            self.last_error=''
        except IllegalMove as exc:
            self.last_error=str(exc)
            return False
        self.selected=uid
        self._release_exhausted_attacker()
        if self.selected not in self.game.units:
            self.selected=None
        return True

    def _try_play(self,uid,replace=None,slot=None):
        g=self.game
        chosen_slot=slot if g.fixed_board_slots else None
        if not g.can_play(0,uid,replace,chosen_slot):
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
            if chosen_slot is None:
                g.play(uid,replace)
            else:
                g.play(uid,replace,slot=chosen_slot)
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

    END_TURN_WARNING_MS=4200

    def _end_turn_available(self):
        """Only expose a turn-finish command when the engine allows it."""
        g=self.game
        return (g.phase=='turn' and g.active==0 and g.pending is None
                and g.end_queue is None and g.deferred_attack is None)

    def _end_turn_warning_key(self):
        """Invalidate confirmation after any authoritative action or turn swap."""
        g=self.game
        return (g, g.action_turn,
                len(getattr(g,'audit_actions',())),
                len(g.event_journal))

    def _end_turn_warning_active(self,now=None):
        warning=getattr(self,'_end_turn_warning',None)
        if warning is None or not self._end_turn_available():
            return False
        if now is None:
            now=pygame.time.get_ticks()
        key,born=warning
        return (key==self._end_turn_warning_key()
                and 0<=now-born<self.END_TURN_WARNING_MS)

    def _end_turn_warning_text(self,readout):
        """Show potential actions only; never imply a guaranteed card effect."""
        cues=[]
        if readout.can_play:
            cues.append('KARTA DO ZAGRANIA')
        if readout.ready_units:
            label=('1 GOTOWA JEDNOSTKA' if readout.ready_units==1
                   else f'{readout.ready_units} GOTOWE JEDNOSTKI')
            cues.append(label)
        return 'POMIJASZ: '+' + '.join(cues)

    def _request_end_turn(self):
        """Single UI entry for mouse and Space, without touching Match on warn."""
        if not self._end_turn_available():
            return False
        hud=turn_readout(self.game)
        if hud.can_act and not self._end_turn_warning_active():
            self._end_turn_warning=(self._end_turn_warning_key(),
                                    pygame.time.get_ticks())
            return False
        self._end_turn_warning=None
        try:
            self.game.end_turn()
        except IllegalMove as exc:
            self.last_error=str(exc)
            return False
        self.selected=None
        self.last_error=''
        return True

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
            self.visual_notice=(('WYBRANO CHORĄŻEGO 2/1 + 4 PANC.'
                                 if getattr(self.game,'starter_guard_armor_rule',False)
                                 else 'WYBRANO CHORĄŻEGO 2/5') if choice=='unit_2_5'
                                else 'WYBRANO +3 MONETY')
            self.visual_notice_tick=pygame.time.get_ticks()
        except IllegalMove as exc:
            self.last_error=str(exc)

    def _draw_bonus_selection(self):
        if not self._bonus_selection_due():return
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((*TAVERN_SCRIM,212))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(340,262,800,421)
        self._panel(panel,TAVERN_PANEL_BG,TAVERN_GOLD,15)
        self.theme.carved_panel(self.screen,panel.inflate(-21,-18),opacity=47)
        self._text('DAR DLA DRUGIEGO GRACZA',28,740,302,cfg.GOLD,center=True)
        self._text('Jedna decyzja przed wymianą kart. Wybierz swoją rekompensatę.',
                   16,740,369,TAVERN_TEXT,center=True)
        pygame.draw.line(self.screen,TAVERN_BRASS,(442,412),(1038,412),1)
        # Starter Chorazy portrait and existing button hitboxes.
        guard_area=pygame.Rect(438,443,604,67)
        self.theme.button(self.screen,guard_area,guard_area.collidepoint(self.mouse_pos()),
                          True,True,False)
        portrait=self.cards_view.images.get_card_image(
            CHORAZY_ART_LEVELS[0],(80,55),mode='contain')
        self.screen.blit(portrait,(guard_area.x+13,guard_area.y+6))
        armored=getattr(self.game,'starter_guard_armor_rule',False)
        self._text('[1] CHORĄŻY  2 ATK / 1 PŻ / 4 PANC.' if armored
                   else '[1] CHORĄŻY  2 ATK / 5 PŻ',
                   18,guard_area.x+111,guard_area.y+9,cfg.TEXT)
        self._text('„Chorąży zawsze zdąży.” · +1 ATK / +2 PŻ za zabójstwo'
                   if armored else '„Chorąży zawsze zdąży.” · Jednostka bez zdolności',
                   12,guard_area.x+111,guard_area.y+41,TAVERN_MUTED)
        coin_area=pygame.Rect(438,537,604,67)
        self.theme.button(self.screen,coin_area,coin_area.collidepoint(self.mouse_pos()),
                          True,False,False)
        for dx in (0,12,24):
            center=(coin_area.x+34+dx,coin_area.y+32)
            pygame.draw.circle(self.screen,(159,112,46),center,19)
            pygame.draw.circle(self.screen,cfg.GOLD,center,15,2)
        self._text('[2] +3 MONETY',18,coin_area.x+112,coin_area.y+9,cfg.TEXT)
        self._text('Więcej środków na rozgrywkę · bez dodatkowej jednostki',
                   12,coin_area.x+112,coin_area.y+41,TAVERN_MUTED)
        self._text('Chorąży nie atakuje w swojej pierwszej turze i zajmuje pole.',
                   13,740,638,TAVERN_MUTED,center=True)
        if self.last_error:
            self._text(self.cards_view.clip(self.last_error,self.fonts[13],690),
                       13,740,654,cfg.RED,center=True)

    def _request_restart(self):
        if self._first_menu_game_unused and not self._needs_confirmation():
            # Start button on the opening menu is NOT a second match.
            self._first_menu_game_unused=False
            self.menu_open=False
            return True
        if self._needs_confirmation():
            self.confirm_action='restart'
            self.confirm_error=''
        else:
            self.restart()
            self.menu_open=False
        return True

    def _start_guided_match(self):
        """Launch a fresh, opt-in tutorial; never discard a live match silently."""
        if self._first_menu_game_unused and not self._needs_confirmation():
            self._first_menu_game_unused=False
            self.tutorial.start(self.game)
            self.tutorial_welcome_open=True
            self.menu_open=False
            return True
        if self._needs_confirmation():
            self._start_tutorial_after_restart=True
            return self._request_restart()
        self.restart()
        self.tutorial.start(self.game)
        self.tutorial_welcome_open=True
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
            guided=self._start_tutorial_after_restart
            self._start_tutorial_after_restart=False
            self.restart()
            if guided:
                self.tutorial.start(self.game)
                self.tutorial_welcome_open=True
            self.menu_open=False
            return True
        return False  # confirmed application quit

    def _draw_confirmation(self):
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((*TAVERN_SCRIM,225))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(379,292,724,390)
        self._panel(panel,TAVERN_PANEL_INNER,TAVERN_GOLD,16)
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
        if event.type==pygame.MOUSEMOTION:
            pointer=self._physical_to_virtual(event.pos)
            if self.drag_start is not None:
                self.drag_pointer=pointer
            self._update_hover_target(pointer)
        # Global shortcuts must work from the *first menu screen*,
        # during mulligan, history/replay and any open modal.
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F11:
            self._toggle_fullscreen()
            return True
        if event.type==pygame.KEYDOWN and event.key==pygame.K_a:
            self._toggle_animations()
            return True
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F8:
            self.ai_speed_index=(self.ai_speed_index+1)%len(self.AI_SPEED_LEVELS)
            self.visual_notice='TEMPO AI: '+self.AI_SPEED_LEVELS[self.ai_speed_index][0]
            self.visual_notice_tick=pygame.time.get_ticks()
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
        # The first tutorial screen must be unmissable and must absorb mouse /
        # keyboard input instead of silently starting the ordinary mulligan.
        if self.tutorial_welcome_open:
            if event.type==pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                    self.tutorial_welcome_open=False
                elif event.key==pygame.K_ESCAPE:
                    self.tutorial_welcome_open=False
                    self.tutorial.active=False
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                pos=self._physical_to_virtual(event.pos)
                if pygame.Rect(421,764,377,55).collidepoint(pos):
                    self.tutorial_welcome_open=False
                elif pygame.Rect(829,764,218,55).collidepoint(pos):
                    self.tutorial_welcome_open=False
                    self.tutorial.active=False
            return True
        # The handbook is a modal even over auctions and the main menu.
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F1 and self.confirm_action is None:
            self.help_open=not self.help_open
            return True
        if self.help_open:
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    self.help_open=False
                elif event.key==pygame.K_RIGHT:
                    self.help_page=min(len(HELP_PAGES)-1,self.help_page+1)
                elif event.key==pygame.K_LEFT:
                    self.help_page=max(0,self.help_page-1)
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                pos=self._physical_to_virtual(event.pos)
                if pygame.Rect(1101,772,123,45).collidepoint(pos):
                    self.help_open=False
                elif pygame.Rect(840,772,120,45).collidepoint(pos):
                    self.help_page=max(0,self.help_page-1)
                elif pygame.Rect(969,772,120,45).collidepoint(pos):
                    self.help_page=min(len(HELP_PAGES)-1,self.help_page+1)
            return True
        if (event.type==pygame.KEYDOWN and event.key==pygame.K_t
                and not (self.menu_open or self.history_open or self.replay_index is not None
                         or self.details_card is not None or self.confirm_action)):
            if self.tutorial.active:
                self.tutorial.active=False
            else:
                self.tutorial.start(self.game)
            return True
        # Always-visible exit control during gameplay (the menu gets its own).
        # Modal overlays retain priority; auction and game-over exit stays active.
        if (event.type==pygame.MOUSEBUTTONUP and event.button==1
                and not (self.confirm_action or self.menu_open or self.history_open
                         or self.replay_index is not None or self.details_card
                         or self._bonus_selection_due())
                and self.exit_button_rect().collidepoint(
                    self._physical_to_virtual(event.pos))):
            return self._request_exit()
        if self.confirm_action is not None:
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    self.confirm_action=None
                    self.confirm_error=''
                    self._start_tutorial_after_restart=False
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
                    self._start_tutorial_after_restart=False
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
                if self._menu_click(self._physical_to_virtual(event.pos)) is False:
                    return False
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
            if self.auction_inspect_index is not None:
                if event.type==pygame.KEYDOWN and event.key in (
                        pygame.K_ESCAPE,pygame.K_i,pygame.K_RETURN):
                    self.auction_inspect_index=None
                    self.auction_inspect_scroll=0
                elif event.type==pygame.KEYDOWN and event.key in (
                        pygame.K_DOWN,pygame.K_PAGEDOWN):
                    self.auction_inspect_scroll+=3 if event.key==pygame.K_PAGEDOWN else 1
                elif event.type==pygame.KEYDOWN and event.key in (
                        pygame.K_UP,pygame.K_PAGEUP):
                    self.auction_inspect_scroll=max(
                        0,self.auction_inspect_scroll-
                        (3 if event.key==pygame.K_PAGEUP else 1))
                elif event.type==pygame.MOUSEWHEEL:
                    self.auction_inspect_scroll=max(
                        0,self.auction_inspect_scroll-event.y*3)
                elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                    self.auction_inspect_index=None
                    self.auction_inspect_scroll=0
                return True
            if event.type==pygame.KEYDOWN and event.key in (
                    pygame.K_1,pygame.K_2,pygame.K_3):
                if self.game.auction.phase=='bidding':
                    self.auction_inspect_index=event.key-pygame.K_1
                    self.auction_inspect_scroll=0
                    return True
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
            elif event.key==pygame.K_w and self.game.phase=='finished':
                self._open_combat_book()
            elif (self.game.pending and self.game.pending.owner == 0
                  and pygame.K_1 <= event.key <= pygame.K_6):
                index = self.choice_page * self.CHOICES_PER_PAGE + event.key - pygame.K_1
                if index < len(self.game.pending.choices):
                    self._choose(index)
            elif event.key==pygame.K_RETURN and self.game.phase=='mulligan':
                try:self.game.finish_mulligan(0)
                except IllegalMove as e:self.last_error=str(e)
            elif event.key==pygame.K_b and self.game.phase=='turn' and self.game.active==0 and not self.game.pending:
                self._order_tavern_beer()
            elif event.key==pygame.K_SPACE and self.game.phase=='turn' and self.game.active==0 and not self.game.pending:
                self._request_end_turn()
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
            elif (self.card_description_rect().collidepoint(self.mouse_pos())
                  and getattr(self,'_sidebar_desc_maxscroll',0)>0):
                self._scroll_sidebar_description(event.y)
            else:self.scroll=max(0,self.scroll-event.y)
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            pos=self._physical_to_virtual(event.pos)
            card=self.card_under(pos)
            self.drag_start=(pos,card)
            if (card in self.game.players[0].hand and self.game.phase=='turn'
                    and self.game.active==0 and not self.game.pending):
                now=pygame.time.get_ticks()
                self.sfx.enqueue('card_pick',now)
                self.sfx.tick(now)
            self.drag_pointer=pos
            self.drag_return=None
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            pos=self._physical_to_virtual(event.pos)
            if self.drag_start:
                down,card=self.drag_start
                # Capture both drag previews before clearing the pointer.
                self.drag_pointer=pos
                attack_drag=self._attack_drag_state()
                floating=self._floating_hand_card()
                self.drag_start=None
                self.drag_pointer=None
                distance=(pos[0]-down[0])**2+(pos[1]-down[1])**2
                if attack_drag is not None:
                    uid,point,legal_target=attack_drag
                    if legal_target is not None:
                        self._try_attack(uid,legal_target)
                    else:
                        target=self.target_under(point)
                        if target in self.game.players[1].board or target=='hero:1':
                            self.last_error=self._attack_issue(uid,target)
                    return True
                if (card in self.game.players[0].board
                        and self.game.phase=='turn' and self.game.active==0
                        and distance>self.DRAG_THRESHOLD_SQ):
                    # Exhausted/stunned allies cannot start drag attacks.
                    return True
                if (not self.game.pending and card in self.game.players[0].hand
                        and distance>self.DRAG_THRESHOLD_SQ):
                    played=False
                    if (self.OWN_Y-12<=pos[1]<=self.OWN_Y+self.SLOT_H+12
                            and self.game.phase=='turn' and self.game.active==0):
                        # Only one of the five real slots is legal.
                        target_slot=self.slot_under(0,pos)
                        if target_slot is None:
                            self.last_error='Upuść kartę na jednym z pięciu pól własnej planszy.'
                        else:
                            target=self.target_under(pos)
                            replace=(target if target in self.game.players[0].board
                                     and len(self.game.players[0].board)==5 else None)
                            played=self._try_play(card,replace,target_slot)
                    if not played and floating is not None:
                        self._queue_drag_return(card,floating[1])
                    # False would shut down the main application loop.
                    return True
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
        """FIFO of committed combat events, including when VFX is disabled."""
        events=[event['text'] for event in self.game.event_journal]
        if len(events)<self._last_logged_event:
            self._last_logged_event=0
            self.combat_notice_active=None
            self.combat_notice_queue=[]
        now=pygame.time.get_ticks()
        outcome=self.combat_visuals.last_attack_outcome
        attack_batch=(outcome is not None
                      and outcome is not self._last_handled_attack_outcome)
        if attack_batch:
            # Choices can finish an attack without adding journal lines.
            # Track the resolved outcome itself, not event count alone.
            self._last_handled_attack_outcome=outcome
            # A new committed attack supersedes an obsolete event backlog.
            # The full authoritative chronology remains available under H.
            self.attack_outcome_active=(now,outcome)
            self.attack_outcome_latest=outcome
            self.combat_notice_active=None
            self.combat_notice_queue.clear()
        for event in events[self._last_logged_event:]:
            notice=None if attack_batch else combat_notice(event)
            if notice is not None:
                if self.combat_notice_active is None:
                    self.combat_notice_active=(now,notice)
                else:
                    self.combat_notice_queue.append(notice)
                    self.combat_notice_queue=self.combat_notice_queue[-24:]
            if self.animations_enabled:
                color=self._feedback_color(event)
                if color:
                    self._recent_feedback.append((now,color))
        self._last_logged_event=len(events)
        self._recent_feedback=self._recent_feedback[-2:]
        self._recent_feedback=[e for e in self._recent_feedback if now-e[0]<620]
        if self.attack_outcome_active and now-self.attack_outcome_active[0]>=2400:
            self.attack_outcome_active=None
        if self.combat_notice_active and now-self.combat_notice_active[0]>=2600:
            self.combat_notice_active=(
                (now,self.combat_notice_queue.pop(0))
                if self.combat_notice_queue else None)

    def update(self):
        g=self.game
        self._sync_tavern_fx()
        if g.phase!='auction':
            self.auction_inspect_index=None
        self._export_finished_audit_once()
        # Synchronize committed snapshots BEFORE classifying their journal.
        # The newest attack recap must appear on the very next rendered frame.
        self.combat_visuals.sync(g,self.slot_rect,self.hero_rect,pygame.time.get_ticks())
        # Some archived UI tests instantiate SoloApp without __init__.
        # Real sessions always have an observer; sparse tests remain valid.
        if hasattr(self,'ability_feedback'):
            self.ability_feedback.observe(
                g,self.slot_rect,self.hero_rect,pygame.time.get_ticks(),
                allowed=(self.animations_enabled and g.phase=='turn' and
                         not (self.menu_open or self.help_open or self.history_open
                              or self.replay_index is not None
                              or self.confirm_action is not None
                              or self.details_card is not None
                              or self.tutorial_welcome_open)))
        self.sfx.observe(g,self.combat_visuals,pygame.time.get_ticks(),
                         allowed=not (self.menu_open or self.help_open
                                     or self.history_open or self.replay_index is not None
                                     or self.confirm_action is not None
                                     or self.details_card is not None))
        self._capture_visual_feedback()
        self._sync_hand_growth()
        self.tutorial.observe(g)
        if (self.menu_open or self.history_open or self.help_open
                or self.tutorial_welcome_open or self.auction_inspect_index is not None
                or self.replay_index is not None or self.confirm_action is not None):
            return
        if g.phase!='finished' and self.details_card is None:
            if self._old_pending is not g.pending:
                self.choice_page=0
                self._old_pending=g.pending
            t=pygame.time.get_ticks()
            if t-self.last_ai_ms>self.AI_SPEED_LEVELS[self.ai_speed_index][1]:
                if (g.phase=='auction' and g.auction and g.auction.turn==1) or (g.phase=='turn' and
                    (g.active==1 or (g.pending and g.pending.owner==1))):
                    try:self.ai.step(g)
                    except IllegalMove as e:self.last_error=str(e)
                    self.last_ai_ms=t
                    self._sync_hand_growth(t)
            if self.selected in g.cards and self.selected not in g.players[0].hand and self.selected not in g.units:
                self.selected=None
        now=pygame.time.get_ticks()
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

    def _aura_focus(self):
        """Selected or hovered living unit, suppressed in blocking overlays."""
        if (self.game.phase!='turn' or self.game.pending is not None
                or self.replay_index is not None or self.menu_open
                or self.history_open or self.help_open or self.confirm_action
                or self.details_card is not None or self.tutorial_welcome_open
                or self.drag_start is not None):
            return None
        hovered=self.card_under(self.mouse_pos())
        if hovered in self.game.units and live_aura_links(self.game,hovered):
            return hovered
        if self.selected in self.game.units:
            return self.selected
        return hovered if hovered in self.game.units else None

    @staticmethod
    def _aura_connector_path(source_rect,target_rect,source_owner,target_owner):
        """Orthogonal route in the empty corridor, never through a card.

        Same-side paths run only in the free gap between cards and their
        owner's hero bar, avoiding the central phase HUD. Cross-row geometry
        is retained, but long cross-row lines are no longer painted over the
        turn information: endpoint outlines and exact bonus tags remain.
        """
        if source_owner==target_owner:
            if source_owner==0:
                # Friendly card bottom y=651, own hero begins y=662.
                y=max(source_rect.bottom,target_rect.bottom)+5
                start=source_rect.midbottom
                end=target_rect.midbottom
            else:
                # Opponent hero bottom y=142, enemy card top y=152.
                y=min(source_rect.top,target_rect.top)-5
                start=source_rect.midtop
                end=target_rect.midtop
        else:
            upper=source_rect if source_owner==1 else target_rect
            lower=source_rect if source_owner==0 else target_rect
            y=(upper.bottom+lower.top)//2
            start=(source_rect.midtop if source_owner==0
                   else source_rect.midbottom)
            end=(target_rect.midtop if target_owner==0
                 else target_rect.midbottom)
        return (start,(start[0],y),(end[0],y),end)

    def _draw_aura_links(self):
        """Visualize only current resolved aura links, never imagined effects."""
        focus=self._aura_focus()
        links=live_aura_links(self.game,focus)
        if not links:
            return
        # Link color is tied to the individual source's modifier direction.
        color_for=lambda link: (
            (120,208,150) if link.kind=='atk' and link.amount>0 else
            (245,163,109) if link.kind=='atk' else
            (126,193,238) if link.kind=='max_hp' and link.amount>0 else
            (226,155,129) if link.kind=='max_hp' else
            (150,189,246))
        stamp_counts={}
        for link in links:
            src=self.game.units.get(link.source)
            dst=self.game.units.get(link.target)
            if src is None or dst is None:
                continue
            source_rect=self.slot_rect(src.owner,self.game.slot_of(link.source))
            target_rect=self.slot_rect(dst.owner,self.game.slot_of(link.target))
            tint=color_for(link)
            pygame.draw.rect(self.screen,tint,
                             source_rect.inflate(5,5),2,border_radius=12)
            pygame.draw.rect(self.screen,tint,
                             target_rect.inflate(7,7),2,border_radius=12)
            # Cross-row aura effects retain colored endpoints and an
            # authoritative label. Skip lines crossing the 56px turn HUD.
            if link.source!=link.target and src.owner==dst.owner:
                path=self._aura_connector_path(
                    source_rect,target_rect,src.owner,dst.owner)
                for start,end in zip(path,path[1:]):
                    if start==end:
                        continue
                    pygame.draw.line(self.screen,(35,47,49),start,end,5)
                    pygame.draw.line(self.screen,tint,start,end,2)
                # Arrow tip points from the empty corridor to the beneficiary.
                start,end=path[-2:]
                direction=pygame.Vector2(end)-pygame.Vector2(start)
                if direction.length_squared()>1:
                    direction=direction.normalize()
                    side=pygame.Vector2(-direction.y,direction.x)
                    tip=pygame.Vector2(end)
                    back=tip-direction*9
                    pygame.draw.polygon(self.screen,tint,[
                        (int(tip.x),int(tip.y)),
                        (int((back+side*4).x),int((back+side*4).y)),
                        (int((back-side*4).x),int((back-side*4).y))])
            # The tag identifies the exact applied *source contribution*.
            # Use image area, not the name/stats plate, and stack when two
            # different sources point to the same recipient.
            rank=stamp_counts.get(link.target,0)
            stamp_counts[link.target]=rank+1
            label=self.cards_view.clip(link.label,self.fonts_bold[13],125)
            font=self.fonts_bold[13]
            text=font.render(label,True,tint)
            tag=pygame.Rect(target_rect.centerx-text.get_width()//2-8,
                            target_rect.y+51+rank*24,
                            text.get_width()+16,21)
            pygame.draw.rect(self.screen,(22,33,42),tag,border_radius=5)
            pygame.draw.rect(self.screen,tint,tag,1,border_radius=5)
            self.screen.blit(text,(tag.centerx-text.get_width()//2,
                                   tag.centery-text.get_height()//2))

    def _draw_positional_cues(self):
        """Highlight actual S34 aura recipient / S108 reaction lane."""
        if (self.game.phase!='turn' or self.selected not in self.game.units
                or self.game.pending or self.replay_index is not None):
            return
        for cue in positional_cues(self.game,self.selected):
            # Detailed active S34 labels are now drawn by the aura-link
            # renderer; retain S108's hypothetical reaction-area cue.
            if cue.label.startswith('AURA ') and live_aura_links(
                    self.game,self.selected):
                continue
            rect=self.slot_rect(cue.owner,cue.slot)
            color=((112,214,156) if cue.label=='AURA +ATK'
                   else (243,176,105) if cue.label=='AURA -ATK'
                   else (189,143,240))
            pygame.draw.rect(self.screen,color,rect.inflate(8,8),
                             3,border_radius=14)
            label=self.cards_view.clip(cue.label,self.fonts_bold[13],
                                       rect.width-12)
            stamp=self.fonts_bold[13].render(label,True,color)
            marker=pygame.Rect(rect.x+4,rect.y+51,rect.w-8,24)
            pygame.draw.rect(self.screen,(22,35,46),marker,border_radius=5)
            self.screen.blit(stamp,(marker.centerx-stamp.get_width()//2,
                                    marker.centery-stamp.get_height()//2))

    def _guard_progress(self,uid):
        """Show the new opt-in starter's kill stage; not S34 or old saves."""
        if (uid=='SUM_START_GUARD'
                and getattr(self.game,'starter_guard_kill_rule',False)
                and uid in self.game.units
                and self.game.cards[uid].definition.name=='Chorąży'):
            return min(3,getattr(self.game,'starter_guard_kills',0))
        return None

    @staticmethod
    def beer_buy_rect():
        # Decorative left gutter; never overlaps cards or the hero HUD.
        return pygame.Rect(10,544,94,38)

    @staticmethod
    def brawl_status_rect():
        """The existing BURDA label only, NOT the KUP [B] button."""
        return pygame.Rect(11,498,91,27)

    def _draw_brawl_hover_help(self,pos):
        """Highlight BURDA and draw help in the SIDE panel, not over cards.

        Called by the standard hover guidance after modal/replay checks.
        No click handling or gameplay data is modified by this read-only UI.
        """
        if not getattr(self.game,'tavern_beer_enabled',False):
            return False
        label=self.brawl_status_rect()
        if not label.collidepoint(pos):
            return False
        pygame.draw.rect(self.screen,(64,47,27),label,border_radius=5)
        pygame.draw.rect(self.screen,cfg.GOLD,label,2,border_radius=5)
        ticks=max(0,getattr(self.game,'beer_turns_remaining',0))
        self._text(f'BURDA: {ticks} TUR',11,56,507,cfg.GOLD,center=True)
        # The centre board holds 10 active card slots. Never obscure them
        # with a 350px-wide help popup; temporarily use the card sidebar.
        rows=[]
        for sentence in brawl_help_lines(self.game):
            rows.extend(self._wrap(sentence,13,310))
        rows=rows[:12]
        area=pygame.Rect(1099,300,338,61+22*len(rows))
        self._panel(area,TAVERN_TOOLTIP_BG,TAVERN_GOLD,10)
        self._text('KARCZEMNA BURDA  [?]',16,area.x+12,area.y+10,cfg.GOLD)
        pygame.draw.line(self.screen,TAVERN_BRASS,
                         (area.x+12,area.y+38),
                         (area.right-12,area.y+38),1)
        for index,line in enumerate(rows):
            self._text(self.cards_view.clip(line,self.fonts[13],314),
                       13,area.x+12,area.y+47+22*index,TAVERN_TEXT)
        return True

    def _order_tavern_beer(self):
        try:
            self.game.order_beer(0)
            self.last_error=''
        except IllegalMove as exc:
            self.last_error=str(exc)

    def _sync_tavern_fx(self):
        """React only to AUTHORITATIVE paid orders, not to mouse clicks."""
        game=self.game
        identity=id(game)
        count=getattr(game,'beer_orders',0)
        if getattr(self,'_beer_fx_match_identity',None)!=identity:
            self._beer_fx_match_identity=identity
            self._beer_fx_last_orders=count
            self._beer_fx_started_ms=None
            self._beer_fx_owner=None
            return
        if count<=getattr(self,'_beer_fx_last_orders',0):
            return
        self._beer_fx_last_orders=count
        entries=(e for e in reversed(game.event_journal[-20:])
                 if 'zamawia kufel za' in e.get('text',''))
        event=next(entries,None)
        self._beer_fx_owner=event['active'] if event is not None else None
        self._beer_fx_started_ms=pygame.time.get_ticks()

    def _draw_tavern_beer(self):
        """Board-mounted candles, one right-side mug during a paid pour, and fire.

        There is no permanent left-side mug: it blocked the little tavern HUD.
        After the mug spills it leaves the board. The 10 card-position flames
        follow Match.beer_turns_remaining, NOT wall-clock time or saved UI state.
        """
        active=bool(getattr(self.game,'tavern_beer_enabled',False))
        ticks=max(0,getattr(self.game,'beer_turns_remaining',0)) if active else 0
        now=pygame.time.get_ticks()
        animate=(getattr(self,'animations_enabled',False)
                 and getattr(self,'replay_index',None) is None
                 and not getattr(self,'menu_open',False)
                 and not getattr(self,'history_open',False)
                 and not getattr(self,'help_open',False)
                 and getattr(self,'details_card',None) is None)
        started=getattr(self,'_beer_fx_started_ms',None)
        progress,_sway,pouring=beer_fx_state(now,started,animate)
        splash=beer_overflow_state(now,started,animate)
        tilt,stream,burn=board_spill_timeline(now,started,animate)
        age=(now-started if started is not None else None)
        # A new, actually paid mug exists only while its pour is in progress.
        # On resumed games there is no transient mug, just the real turn state.
        show_mug=(bool(ticks) and animate and age is not None
                  and 0<=age<1450)
        # The spent mug rolls off the right-hand timber, rather than abruptly
        # blinking away: four pixel-snapped exit poses over the last 250 ms.
        exit_step=(min(4,max(0,(age-1200)//62))
                   if show_mug else 0)
        mug_anchor=(1021+5*exit_step,565+4*exit_step)
        # Keep the original wax candle art on BOTH sides of the board frame.
        for x in (57,1020):
            draw_tavern_rail(self.screen,x,0,
                             pouring and show_mug and x==1020,
                             progress,splash if ticks else 0.0,
                             now_ms=now,animate=animate,tilt=tilt,
                             show_mug=show_mug and x==1020,
                             mug_anchor=mug_anchor)
        if ticks and animate:
            # Only the mug at the RIGHT spills. No mysterious left-side ale.
            draw_board_spill(self.screen,1020,stream,burn,now_ms=now,
                             lower_right=True)
            # Delicate 8-bit flamelets rim each of the 10 board positions.
            # The paid fire visibly travels right-to-left, then remains lit
            # until the authoritative brawl counter reaches zero.
            for owner in (0,1):
                for slot in range(5):
                    power=(slot_flame_strength(ticks,now,started,animate,
                                               owner,slot)
                           * tavern_flame_intensity(ticks))
                    if power>0.0:
                        draw_slot_flamelets(self.screen,
                                           self.slot_rect(owner,slot),
                                           now_ms=now,owner=owner,
                                           index=slot,strength=power)
        # The purchase HUD stays accessible and unmoved in the left gutter.
        if not active:
            return
        panel=pygame.Rect(8,475,97,115)
        pygame.draw.rect(self.screen,(35,29,23),panel,border_radius=7)
        pygame.draw.rect(self.screen,(143,100,47),panel,1,border_radius=7)
        price=self.game.beer_price(0)
        self._text(f'PIWO {price} M',12,56,485,cfg.GOLD,center=True)
        self._text(f'BURDA: {ticks} TUR',11,56,507,cfg.TEXT,center=True)
        enabled=self.game.can_order_beer(0)
        self._button(self.beer_buy_rect(),'KUP [B]',active=enabled,small=True)
        if ticks:
            if getattr(self.game,'tavern_min_hp_damage_enabled',False):
                # Per-target minimum cannot be represented by one DMG count.
                self._text('MIN. 10% MAX PŻ',11,1018,486,cfg.GOLD,center=True)
                self._text(f'BAZA {ticks} DMG',11,1018,509,cfg.TEXT,center=True)
            else:
                next_damage=(ticks if getattr(self.game,'tavern_scaled_damage_enabled',False)
                             else 1)
                self._text(f'{next_damage} DMG / TURA',11,1018,486,cfg.GOLD,center=True)
                self._text('+3 ZA KUFEL',11,1018,509,cfg.TEXT,center=True)

    def _draw_board(self):
        self._text('STREFA KOMPUTERA',15,107,78,cfg.MUTED)
        self._text('TWOJA STREFA',15,107,412,cfg.MUTED)
        self._draw_hero(1)
        self._draw_hero(0)
        for owner,p in enumerate(self.game.players):
            for i in range(5):
                rect=self.slot_rect(owner,i)
                self.theme.slot(self.screen,rect,owner)
                uid=self.game.unit_at(owner,i)
                if uid is None:
                    self._text('+',34,rect.centerx,rect.centery-8,(64,85,100),center=True)
                    self._text(f'POLE {i+1}',12,rect.centerx,rect.bottom-21,cfg.MUTED,center=True)
                    continue
                if uid not in self.game.units:continue
                selected=self.selected==uid
                u=self.game.units[uid]
                attack_info=attack_display(self.game,uid)
                # Cosmetic impact shake: draw the live card a few pixels away
                # from its fixed slot, never move gameplay hitboxes or state.
                render_rect=rect
                if self.animations_enabled and self.replay_index is None:
                    offset=self.combat_visuals.shake_offset(
                        uid,pygame.time.get_ticks())
                    render_rect=rect.move(*offset)
                self.cards_view.draw(self.screen,self.game.cards[uid],render_rect,u,
                     selected=selected,hover=rect.collidepoint(self.mouse_pos()),
                     dim=bool(inactive_card_reason(self.game,uid)),
                     rarity=self.game.auction_awards.get(uid,{}).get('rarity'),
                     animate_rarity=self.animations_enabled,
                     statuses=active_statuses(self.game,uid),ready=attack_info.ready,
                     attacks_remaining=attack_info.remaining,attacks_total=attack_info.limit,
                     guard_kills=self._guard_progress(uid),
                     hp_override=(self.combat_visuals.hp_display(uid,pygame.time.get_ticks())
                                  if self.animations_enabled and self.replay_index is None
                                  else None))
                # Outline only truly legal attacks, not perceived attack
                # strength or status guesses. Selected target remains dominant.
                if owner==0 and attack_info.ready and not selected:
                    pygame.draw.rect(self.screen,(121,196,160),rect.inflate(6,6),
                                     2,border_radius=13)
        self._draw_positional_cues()
        self._draw_aura_links()
        self._draw_brawl_risk_badges()
        note=('STAŁE POZYCJE  ·  WYBIERZ WOLNE POLE  ·  ATAKI W DOWOLNEJ KOLEJNOŚCI'
              if self.game.fixed_board_slots else
              'WYSTAWIANIE OD PRAWEJ  ·  ATAKI W DOWOLNEJ KOLEJNOŚCI')
        self._text(note,12,620,413,cfg.GOLD,center=True)
        for uid in self._play_replacement_targets():
            rect=self.slot_rect(0,self.game.slot_of(uid))
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
        floating=self._floating_hand_card()
        for uid,rect in hand.items():
            pygame.draw.rect(self.screen,(18,32,41),rect.inflate(11,10),border_radius=13)
            if floating is not None and floating[0]==uid:
                # Empty recess rather than drawing the same card twice.
                pygame.draw.rect(self.screen,(113,214,223),rect,2,border_radius=11)
                continue
            marked=(self.game.phase=='mulligan'
                    and uid in self.game.players[0].mulligan_selected)
            self.cards_view.draw(self.screen,self.game.cards[uid],rect,
                                 selected=(uid==self.selected or marked),
                                 dim=(self.game.phase=='turn' and self.game.active!=0),
                                 hover=rect.collidepoint(self.mouse_pos()),
                                 rarity=self.game.auction_awards.get(uid,{}).get('rarity'),
                                 animate_rarity=self.animations_enabled,
                                 statuses=hand_grants(self.game,uid))
            if (self.game.phase=='turn' and self.game.active==0
                    and not self.game.pending and not p0.played_this_turn):
                # Respect exact game.can_play including five-slot replacement.
                can_place=(self.game.can_play(0,uid,None) if len(p0.board)<5
                           else any(self.game.can_play(0,uid,replaced)
                                    for replaced in p0.board))
                if can_place and uid!=self.selected:
                    pygame.draw.rect(self.screen,(207,164,90),rect.inflate(6,6),
                                     2,border_radius=12)
            self._draw_hand_level_fx(uid,rect)
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

    def _draw_brawl_risk_badges(self):
        """Small warning outside the card edge; does not move/select any unit."""
        if next_brawl_damage(self.game)<=0 or self.game.phase!='turn':
            return
        for owner in (0,1):
            for index in range(5):
                uid=self.game.unit_at(owner,index)
                if uid is None or not brawl_at_risk(self.game,uid):
                    continue
                rect=self.slot_rect(owner,index)
                center=(rect.right+10,rect.y+15)
                pygame.draw.circle(self.screen,(64,22,19),center,12)
                pygame.draw.circle(self.screen,(248,113,94),center,10,2)
                self._text('!',15,center[0],center[1]-1,
                           (255,230,174),center=True)

    def _draw_decision_preview(self):
        """Hover-driven combat/replacement estimations, sidebar-only and safe.

        Draw after ordinary hover hints so current legal decision has priority.
        In a game phase modal, replay or pending ability, display nothing.
        """
        game=self.game
        if (game.phase!='turn' or game.active!=0 or game.pending is not None
                or self.menu_open or self.history_open or self.help_open
                or self.replay_index is not None or self.details_card is not None
                or self.confirm_action or self.tutorial_welcome_open
                or self._bonus_selection_due()):
            return
        pointer=self.mouse_pos()
        dragged=getattr(self,'drag_start',None)
        if dragged is not None and getattr(self,'drag_pointer',None) is not None:
            start,drag_uid=dragged
            pointer=self.drag_pointer
            if ((pointer[0]-start[0])**2+(pointer[1]-start[1])**2
                    <=self.DRAG_THRESHOLD_SQ):
                return
            candidate=drag_uid
        else:
            candidate=self.selected
        player=game.players[0]
        title=None
        rows=[]
        if candidate in player.board and candidate in game.units:
            target=self.target_under(pointer)
            view=preview_standard_attack(game,candidate,target) if target else None
            if view is not None:
                title='PODGLĄD ZWYKŁEGO ATAKU'
                strike=view.strike
                rows.append(f'CEL: {game.label(target)}')
                rows.append(f'ATAK: {strike.raw}  ·  PŻ −{strike.hp_loss}')
                if strike.blocked_by_shield:
                    rows.append('TARCZA CELU: BLOKUJE CAŁY CIOS')
                elif strike.absorbed:
                    rows.append(f'PANCERZ CELU: POCHŁONIE {strike.absorbed}')
                rows.append(f'PŻ CELU: {max(0,strike.after_hp)} PO TRAFIENIU')
                if view.counter is not None:
                    counter=view.counter
                    rows.append(f'ODWET: {counter.raw}  ·  PŻ −{counter.hp_loss}')
                    if counter.blocked_by_shield:
                        rows.append('TWOJA TARCZA: BLOKUJE ODWET')
                    elif counter.absorbed:
                        rows.append(f'TWÓJ PANCERZ: POCHŁONIE {counter.absorbed}')
                    rows.append(f'TWOJE PŻ: {max(0,counter.after_hp)}')
                if view.extra_effects_possible:
                    rows.append('UWAGA: DODATKOWE ZDOLNOŚCI PRZED CIOSEM')
                rows.append('Szacunek bez zdolności i efektów po śmierci.')
        elif candidate in player.hand and len(player.board)==5:
            target=self.target_under(pointer)
            if target in player.board:
                view=preview_replacement(game,candidate,target)
                if view is not None:
                    title='PORÓWNANIE PRZY WYMIANIE'
                    old=game.cards[target].definition.name
                    new=game.cards[candidate].definition.name
                    rows.extend((f'OBECNA: {old}',f'NOWA: {new}',
                                 f'ATK: {view.old_atk} → {view.new_atk}  '
                                 f'({view.new_atk-view.old_atk:+d})',
                                 f'PŻ: {view.old_hp} → {view.new_hp}  '
                                 f'({view.new_hp-view.old_hp:+d})'))
                    if view.loses_outgoing_aura:
                        rows.append('UWAGA: ZNIKNIE OBECNA AURA')
                    rows.append('Stara karta znika BEZ efektu śmierci.')
                    rows.append('Zdolności i aury mogą zmienić statystyki.')
        if title is None:
            return
        area=pygame.Rect(1099,285,338,55+len(rows)*26)
        self._panel(area,TAVERN_TOOLTIP_BG,TAVERN_GOLD,10)
        self._text(title,15,area.x+12,area.y+11,cfg.GOLD)
        pygame.draw.line(self.screen,TAVERN_BRASS,
                         (area.x+12,area.y+38),(area.right-12,area.y+38))
        for i,row in enumerate(rows):
            font=13
            self._text(self.cards_view.clip(row,self.fonts[font],314),
                       font,area.x+12,area.y+46+i*26,
                       cfg.RED if row.startswith('UWAGA') else cfg.TEXT)

    @staticmethod
    def card_description_rect():
        return pygame.Rect(1101,370,329,111)

    def _scroll_sidebar_description(self,steps):
        self._sidebar_desc_scroll=max(0,min(
            getattr(self,'_sidebar_desc_maxscroll',0),
            getattr(self,'_sidebar_desc_scroll',0)-steps*2))

    def _draw_sidebar_description(self,uid,description):
        """Complete measured sidebar copy, wheel-scrollable without ellipses."""
        if getattr(self,'_sidebar_desc_uid',None)!=uid:
            self._sidebar_desc_uid=uid
            self._sidebar_desc_scroll=0
        lines=self._wrap(description,13,308)
        visible=3  # Windows Segoe 13 renders at 18 px; preserve row separation.
        self._sidebar_desc_maxscroll=max(0,len(lines)-visible)
        offset=min(getattr(self,'_sidebar_desc_scroll',0),
                   self._sidebar_desc_maxscroll)
        self._sidebar_desc_scroll=offset
        area=self.card_description_rect()
        pygame.draw.rect(self.screen,(38,35,31),area,border_radius=6)
        pygame.draw.rect(self.screen,TAVERN_BRASS,area,1,border_radius=6)
        self._text('DZIAŁANIE ZDOLNOŚCI',14,area.x+7,area.y+4,cfg.GOLD)
        for i,line in enumerate(lines[offset:offset+visible]):
            self._text(line,13,area.x+7,area.y+28+i*20,cfg.TEXT)
        if len(lines)>visible:
            self._text(f'KÓŁKO: {offset+1}–{min(len(lines),offset+visible)}/{len(lines)} '
                       '· [I] PEŁNY OPIS',11,area.x+7,area.bottom-14,cfg.GOLD)
        else:
            self._text('[I] PEŁNY OPIS I WARUNKI',11,
                       area.x+7,area.bottom-14,cfg.MUTED)

    def _draw_sidebar(self):
        rect=pygame.Rect(self.SIDEBAR_X,78,364,872)
        self._panel(rect,TAVERN_PANEL_INNER,TAVERN_BRASS,16)
        if self.game.pending and self.game.pending.owner == 0:
            self._draw_choice_sidebar()
            return
        self._text('KARTA / AKCJE',22,1103,106,cfg.GOLD)
        card_id=self.selected or self.card_under(self.mouse_pos())
        self.sidebar_card=card_id if card_id in self.game.cards else None
        if self.sidebar_card:
            context=selected_card_readout(self.game,self.sidebar_card)
            chip=pygame.Rect(1291,97,139,35)
            pygame.draw.rect(self.screen,(44,40,33),chip,border_radius=8)
            pygame.draw.rect(self.screen,context.color,chip,2,border_radius=8)
            self._text(self.cards_view.clip(context.label,self.fonts[12],chip.width-16),
                       12,chip.centerx,chip.centery,context.color,center=True)
        if card_id and card_id in self.game.cards:
            c=self.game.cards[card_id];d=c.definition;u=self.game.units.get(card_id)
            cue=card_cue(c,u)
            summary=ability_summary(c,u)
            self._text(self.cards_view.clip(d.name,self.fonts[18],310),18,1105,150,FACTION_COLORS[d.faction])
            self._text(f'{d.id} • {d.faction} • POZ. {cue.ability_level}',13,1105,181,cfg.MUTED)
            guard_kills=self._guard_progress(card_id)
            self._infographic_box(pygame.Rect(1104,210,153,70),'AKTYWACJA',cue.trigger,(142,215,238),cue.family)
            self._infographic_box(
                pygame.Rect(1267,210,157,70),
                'ZA ZABÓJSTWA' if guard_kills is not None else 'ROZWÓJ CO 3 TURY',
                f'{guard_kills}/3 ZABÓJSTW' if guard_kills is not None else cue.upgrade,
                cfg.GREEN, 'LIMIT 3' if guard_kills is not None else cue.next_threshold)
            base_atk=u.atk if u else c.attack
            normal_damage, boosted=standard_hit_damage(
                base_atk, active_statuses(self.game,card_id) if u else ())
            combat_line=(f'ATAK {normal_damage} (GEN. ×2) / PŻ {u.hp}'
                         if boosted else
                         f'ATAK {base_atk} / PŻ {u.hp if u else c.max_hp}')
            self._infographic_box(pygame.Rect(1104,290,320,69),
                                  'AKTUALNY EFEKT',cue.base,cue.color,combat_line)
            rules=getattr(self.game,'ruleset_version','v22')
            complete=(full_preview_auction_copy(d.id,card_rarity(c),rules,summary.full)
                      if d.id.startswith('A0') and self.game.auction_catalog=='v22' and card_rarity(c) and identify_auction_variant(d) else
                      (v23_base_card_note(d.id,rules) or summary.full))
            self._draw_sidebar_description(card_id,complete)
            self._text('POSTĘP / WZROST',15,1105,491,cfg.GOLD)
            self._text(self.cards_view.clip(cue.growth,self.fonts[13],309),13,1105,517,cfg.MUTED)
            if u:
                statuses=sorted(active_statuses(self.game,card_id),
                                key=status_display_priority)
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
                if u.owner==0:
                    reason=inactive_card_reason(self.game,card_id) or attack_display(self.game,card_id).reason
                    target=self.target_under(self.mouse_pos())
                    legal=self.game.legal_attacks(card_id)
                    blocked=(target=='hero:1' or target in self.game.players[1].board) and target not in legal
                    if blocked:
                        issue=self._attack_issue(card_id,target)
                        reason=('CEL: PROWOKACJA — ATAKUJ OBROŃCĘ'
                                if issue.startswith('PROWOKACJA') else
                                'CEL NIEDOSTĘPNY — '+reason)
                    self._text(self.cards_view.clip('ATAK: '+reason,
                                                   self.fonts[13],316),
                               13,1105,667,
                               cfg.RED if blocked else cfg.GREEN if reason=='GOTOWA' else cfg.MUTED)
                else:
                    self._text('JEDNOSTKA RYWALA — MOŻLIWY CEL ATAKU',
                               12,1105,667,cfg.RED)
            else:
                grants=hand_grants(self.game,card_id)
                if grants:
                    self._text('PRZYZNANE CECHY W RĘCE',14,1105,553,cfg.GOLD)
                    for j,st in enumerate(grants[:3]):
                        self._text(self.cards_view.clip(st.name,self.fonts[13],310),13,1105,577+j*25,st.color)
                context=selected_card_readout(self.game,card_id)
                self._text(self.cards_view.clip(context.action or d.scaling,
                                                self.fonts[12],313),
                           12,1105,658,context.color)
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
            economy=economy_cue(self.game)
            auction=(f'  ·  AUKCJA ZA {economy.rounds_to_auction} R.'
                     if economy.rounds_to_auction is not None
                     else '')
            title=f'RUNDA {self.game.round}'+auction
            self._text(self.cards_view.clip(title,self.fonts[15],315),
                       15,1104,743,cfg.GOLD)
            if self.game.active==0:
                income=(f'  ·  TERAZ +{economy.vacant_income} MONET ZA POLA'
                        if economy.vacant_income is not None else '')
                status='TWOJA TURA'+income
                self._text(self.cards_view.clip(status,self.fonts[12],319),
                           12,1104,773,cfg.GREEN)
            else:self._text('RUCH KOMPUTERA',15,1104,773,cfg.RED)
            status=turn_readout(self.game)
            warned=self._end_turn_warning_active()
            if warned:
                # No modal: 4.2 s to confirm, with a real engine readout.
                notice=self._end_turn_warning_text(status)
                self._text(self.cards_view.clip(notice,self.fonts[12],319),
                           12,1104,797,cfg.GOLD)
            elif self.game.players[0].next_fast:
                self._text('NASTĘPNA KARTA: SZYBKI ATAK',13,1104,796,STATUS_COLORS['quick'])
            elif status.is_human_turn:
                action_msg=('DOSTĘPNE AKCJE: ZAGRAJ / ATAKUJ' if status.can_act
                            else 'BRAK DALSZYCH AKCJI — ZAKOŃCZ TURĘ')
                self._text(self.cards_view.clip(action_msg,self.fonts[12],319),
                           12,1104,797,
                           cfg.GOLD if status.can_act else cfg.GREEN)
            can=self._end_turn_available()
            label=('POTWIERDŹ  [SPACJA]' if warned else
                   'ZAKOŃCZ TURĘ  [SPACJA]')
            rect=pygame.Rect(1201,816,221,52)
            self._button(rect,label,active=can,
                         accent=can and not status.can_act,small=True)
            if warned:
                # Important but restrained warning frame around existing CTA.
                pygame.draw.rect(self.screen,cfg.GOLD,rect.inflate(4,4),
                                 3,border_radius=12)
        if self.game.phase!='finished':
            self._button(pygame.Rect(1093,869,145,33),'NOWY MECZ  [R]',small=True)

    @staticmethod
    def exit_button_rect():
        """Fixed hit target on the internal canvas; scales with the viewport."""
        return pygame.Rect(1349,27,86,34)

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
            if self._bonus_selection_due():
                guard=('2/1 +4 PANC.' if getattr(g,'starter_guard_armor_rule',False)
                       else '2/5')
                return f'WYBÓR REKOMPENSATY  ·  [1] CHORĄŻY {guard} LUB [2] +3 MONETY'
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
        if self.selected in player.board:
            info=attack_display(g,self.selected)
            if info.ready:
                return 'TWOJA TURA  ·  ZAATAKUJ PODŚWIETLONY CEL (MOŻLIWY ATAK)'
            return 'ATAK NIEDOSTĘPNY: '+info.reason+'  ·  '+attack_reason_help(info.reason)
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
        rect=pygame.Rect(96,372,952,56)
        hint=self.tutorial.hint(self.game)
        if hint is not None:
            # Keep the five-step coach visible alongside the real turn HUD.
            # Readable gold framed lesson, not an ordinary journal message.
            pygame.draw.rect(self.screen,(47,38,25),rect,border_radius=9)
            pygame.draw.rect(self.screen,(249,201,100),rect,3,border_radius=9)
            pygame.draw.rect(self.screen,(249,201,100),
                             pygame.Rect(rect.x+3,rect.y+4,6,rect.height-8),
                             border_radius=3)
            title,detail=hint.title,hint.detail
            self._text(self.cards_view.clip(title,self.fonts[16],524),
                       16,rect.x+18,rect.y+3,cfg.GOLD)
            self._text(self.cards_view.clip(detail,self.fonts[13],528),
                       13,rect.x+18,rect.y+31,cfg.TEXT)
            for index in range(5):
                dot=pygame.Rect(rect.right-155+index*23,rect.y+5,14,8)
                pygame.draw.rect(self.screen,cfg.GOLD if index<hint.stage else (89,78,64),
                                 dot,border_radius=3)
            if self.game.phase=='turn':
                self._draw_turn_counters(rect,compact=True)
            else:
                self._text('POMOC [F1]   WYŁĄCZ [T]',12,rect.right-220,
                           rect.y+32,cfg.GOLD)
            return
        pygame.draw.rect(self.screen,TAVERN_PANEL_INNER,rect,border_radius=7)
        pygame.draw.rect(self.screen,TAVERN_BRASS,rect,1,border_radius=7)
        parts=self._phase_guidance().split('  ·  ')
        title=parts[0]
        detail='  ·  '.join(parts[1:]) if len(parts)>1 else 'Wykonaj legalną akcję wskazaną na planszy.'
        if self.game.phase=='turn':
            hud=turn_readout(self.game)
            heading=('TWOJA TURA' if hud.is_human_turn else
                     'WYBÓR ZDOLNOŚCI' if self.game.pending and self.game.pending.owner==0
                     else 'RUCH KOMPUTERA')
            self._text(heading,18,rect.x+12,rect.y+3,
                       cfg.GREEN if hud.is_human_turn else cfg.GOLD)
            self._text(self.cards_view.clip(detail if len(parts)>1 else title,
                                            self.fonts[13],525),
                       13,rect.x+12,rect.y+31,cfg.TEXT)
            self._draw_turn_counters(rect)
            return
        self._text(self.cards_view.clip(title,self.fonts[14],rect.width-28),
                   14,rect.x+12,rect.y+4,cfg.GOLD)
        self._text(self.cards_view.clip(detail,self.fonts[13],rect.width-28),
                   13,rect.x+12,rect.y+29,cfg.TEXT)

    def _draw_turn_counters(self,rect,compact=False):
        """One shared read-only HUD for normal play AND opt-in tutorials."""
        hud=turn_readout(self.game)
        for x,w,label,enabled in (
                (650,169,f'KARTA {hud.played_cards}/1',
                 hud.is_human_turn and hud.can_play),
                (831,205,f'GOTOWE DO ATAKU: {hud.ready_units}',
                 hud.is_human_turn and hud.ready_units>0)):
            pill=pygame.Rect(x,rect.y+(24 if compact else 9),
                             w,27 if compact else 38)
            color=cfg.GREEN if enabled else TAVERN_MUTED
            pygame.draw.rect(self.screen,(49,43,32),pill,border_radius=7)
            pygame.draw.rect(self.screen,color,pill,2 if enabled else 1,
                             border_radius=7)
            self._text(self.cards_view.clip(label,self.fonts[13],w-16),
                       13,pill.centerx,pill.centery,color,center=True)

    def _draw_header(self):
        logo,mode,help_area=self.header_regions()
        pygame.draw.rect(self.screen,TAVERN_PANEL_BG,pygame.Rect(83,8,1364,67),
                         border_radius=12)
        pygame.draw.line(self.screen,cfg.GOLD,(104,73),(1426,73),1)
        self._text('AUCTION',34,106,22,(232,189,107))
        self._text('HAMMER',34,300,22,cfg.TEXT)
        self._text(f'SOLO  ·  70 KART + AUKCJE {self.game.auction_catalog.upper()}  ·  BALANS v21',14,
                   mode.x+8,33,cfg.MUTED)
        speed=self.AI_SPEED_LEVELS[self.ai_speed_index][0]
        help_text=(f'AI {speed} [F8]  ·  ANIM [A]  ·  EKRAN [F11]')
        font=self.fonts[13]
        # Reserve a dedicated, clearly clickable exit button on the right.
        help_text=self.cards_view.clip(help_text,font,
                                      self.exit_button_rect().x-help_area.x-18)
        self._text(help_text,13,help_area.x+8,34,cfg.GOLD)
        self._button(self.exit_button_rect(),'WYJDŹ',small=True)

    def _draw_log(self):
        """Latest attack outcome takes priority over the older event ticker."""
        now=pygame.time.get_ticks()
        notice=(getattr(self,'visual_notice','')
                if now-getattr(self,'visual_notice_tick',-10000)<2400
                else '')
        recap=self.attack_outcome_active
        if recap is not None and 0<=now-recap[0]<2400:
            outcome=recap[1]
            rect=pygame.Rect(1099,899,330,49)
            pygame.draw.rect(self.screen,(34,53,59),rect,border_radius=8)
            pygame.draw.rect(self.screen,(115,223,238),rect,2,border_radius=8)
            heading='SKUTKI ATAKU  ·  [H] HISTORIA'
            self._text(self.cards_view.clip(heading,self.fonts[12],304),
                       12,1108,900,(115,223,238))
            for index,line in enumerate(outcome.lines[:2]):
                self._text(self.cards_view.clip(line,self.fonts[13],306),
                           13,1108,917+index*16,cfg.TEXT)
            # A new invalid input must still surface its error immediately;
            # combat feedback may not hide interaction feedback for 2.4 s.
            if self.last_error:
                self._text(self.cards_view.clip(self.last_error,self.fonts[13],750),
                           13,280,954,cfg.RED)
            return
        active=self.combat_notice_active
        if active is not None and 0<=now-active[0]<2600:
            cue=active[1]
            # The sidebar ends at y=950: keep the entire ticker and both
            # lines of text inside it, including the latest truncated line.
            rect=pygame.Rect(1099,899,330,49)
            pygame.draw.rect(self.screen,(43,35,29),rect,border_radius=8)
            pygame.draw.rect(self.screen,cue.color,rect,2,border_radius=8)
            count=len(self.combat_notice_queue)
            heading=cue.label+(f'  ·  DALEJ {count}  [H]' if count else '  ·  [H]')
            self._text(self.cards_view.clip(heading,self.fonts[12],304),
                       12,1108,900,cue.color)
            lines=self._wrap(notice or cue.message,11,306)
            if lines:
                self._text(self.cards_view.clip(lines[0],self.fonts[11],306),
                           11,1108,918,cfg.TEXT)
                if len(lines)>1:
                    last=lines[1]+('…' if len(lines)>2 else '')
                    self._text(self.cards_view.clip(last,self.fonts[11],306),
                               11,1108,934,cfg.TEXT)
        else:
            recent=getattr(self,'attack_outcome_latest',None)
            last=(recent.lines[0] if recent is not None else
                  self.game.events[-1] if self.game.events else 'Nie ma jeszcze zdarzeń.')
            heading=('OSTATNI ATAK · NAJEDŹ, ABY ROZWINĄĆ'
                     if recent is not None else
                     'OSTATNIE ZDARZENIE  ·  [H] PEŁNA HISTORIA')
            self._text(self.cards_view.clip(heading,self.fonts[12],319),
                       12,1104,909,cfg.GOLD)
            self._text(self.cards_view.clip(notice or last,self.fonts[13],319),
                       13,1104,928,cfg.TEXT if notice or recent else cfg.MUTED)
        if self.last_error:
            self._text(self.cards_view.clip(self.last_error,self.fonts[13],750),
                       13,280,954,cfg.RED)

    def _attack_target_rects(self):
        """Ask the engine for *currently legal* attack targets only."""
        g=self.game
        if g.pending or g.phase!='turn' or g.active!=0:
            return []
        drag=self._attack_drag_state()
        candidate=drag[0] if drag is not None else self.selected
        if candidate not in g.players[0].board:
            return []
        result=[]
        for target in g.legal_attacks(candidate):
            if target.startswith('hero:'):
                result.append(self.hero_rect(int(target.split(':')[1])))
            elif target in g.players[1].board:
                result.append(self.slot_rect(1,g.slot_of(target)))
        return result

    def _play_target_rects(self):
        """Golden areas for real legal placements and replacements."""
        g=self.game
        if g.phase!='turn' or g.active!=0 or g.pending is not None:
            return []
        player=g.players[0]
        # Show actual legal destinations while dragging a card, even if the
        # card was not previously selected by clicking it.
        dragged=self.drag_start[1] if self.drag_start is not None else None
        candidate=dragged if dragged in player.hand else self.selected
        if candidate not in player.hand:
            return []
        if len(player.board)<5 and g.can_play(0,candidate,None):
            return [self.slot_rect(0,i) for i in g.available_slots(0)]
        if len(player.board)==5:
            return [self.slot_rect(0,g.slot_of(uid)) for uid in player.board
                    if g.can_play(0,candidate,uid)]
        return []

    def _draw_play_targets(self):
        # Gold = play/replace, cyan = attack, violet = ability target.
        for rect in self._play_target_rects():
            pygame.draw.rect(self.screen,(238,187,83),rect.inflate(8,8),
                             3,border_radius=13)

    @staticmethod
    def _pixel_attack_corners(screen,rect,color,length=11):
        """Four short 8-bit corner brackets; leave art/stat labels unobscured."""
        x1,y1,x2,y2=rect.left,rect.top,rect.right-1,rect.bottom-1
        for x,dx in ((x1,1),(x2,-1)):
            for y,dy in ((y1,1),(y2,-1)):
                pygame.draw.line(screen,color,(x,y),(x+dx*length,y),2)
                pygame.draw.line(screen,color,(x,y),(x,y+dy*length),2)

    def _draw_attack_targets(self):
        pointer=self.mouse_pos()
        for rect in self._attack_target_rects():
            # Only Match.legal_attacks makes a unit/hero target actionable.
            hovered=rect.collidepoint(pointer)
            area=rect.inflate(9 if hovered else 7,9 if hovered else 7)
            pygame.draw.rect(self.screen,
                             (170,250,255) if hovered else (115,223,238),
                             area,4 if hovered else 2)
            if hovered:
                # The 4px outline and hard pixel corners already signal
                # a legal target; avoid stamping ATAKUJ over art/faces.
                self._pixel_attack_corners(self.screen,area,
                                           (226,245,224),length=13)

    def _draw_attack_source_feedback(self):
        """Highlight the selected attacker without predicting combat results."""
        if (self.game.phase!='turn' or self.game.active!=0
                or self.game.pending is not None):
            return
        drag=self._attack_drag_state()
        uid=drag[0] if drag is not None else self.selected
        if uid not in self.game.players[0].board:
            return
        if not self.game.legal_attacks(uid):
            return
        source=self.slot_rect(0,self.game.slot_of(uid)).inflate(8,8)
        # Pixel-art gold brackets distinguish 'the one that will attack'
        # from cyan engine-confirmed legal targets.
        self._pixel_attack_corners(self.screen,source,(245,192,116),length=13)


    def _draw_choices(self):
        """Highlight legal ability targets without covering information."""
        pending = self.game.pending
        if pending is None or pending.owner != 0:
            return
        # A010's grow/summon modes have target=None, so regular choice
        # highlights do not show them. Give each legal mode its board target.
        if (pending.context=='end' and pending.uid in self.game.players[0].board
                and self.game.auction_awards.get(pending.uid,{}).get('archetype')=='A010'):
            modes={ch.mode for ch in pending.choices}
            if 'grow' in modes:
                rect=self.slot_rect(0,self.game.slot_of(pending.uid))
                pygame.draw.rect(self.screen,(194,150,246),rect.inflate(8,8),
                                 4,border_radius=13)
            if 'summon' in modes:
                for slot in range(5):
                    if self.game.unit_at(0,slot) is not None:
                        continue
                    rect=self.slot_rect(0,slot)
                    pygame.draw.rect(self.screen,(194,150,246),
                                     rect.inflate(8,8),3,border_radius=13)
                    self._text('PRZYWOŁAJ',13,rect.centerx,rect.centery+25,
                               (225,196,253),center=True)
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
                        rect = self.slot_rect(player.idx, self.game.slot_of(target))
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
        self._panel(info,TAVERN_PANEL_INNER,TAVERN_BRASS,12)
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
        self._panel(pane,TAVERN_PANEL_BG,TAVERN_GOLD,12)
        self._text(f'WYBIERZ CEL / WARIANT ({len(pending.choices)})',
                   14,1107,410,cfg.GOLD)
        queen_modes=(pending.context=='end'
                     and self.game.auction_awards.get(pending.uid,{}).get('archetype')=='A010'
                     and pending.uid in self.game.players[0].board)
        if queen_modes:
            self._text('Królowa = WZMOCNIJ · wolne pole = PRZYWOŁAJ',
                       12,1107,437,cfg.TEXT)
        else:
            self._text('Wybierz cel lub sposób działania.',13,1107,437,cfg.TEXT)
        pygame.draw.line(self.screen,TAVERN_BRASS,(1107,458),(1421,458),1)
        for index,rect in self.choice_bounds():
            choice=pending.choices[index]
            hovered=rect.collidepoint(self.mouse_pos())
            pygame.draw.rect(self.screen,(98,72,42) if hovered else TAVERN_PANEL_INNER,
                             rect,border_radius=8)
            pygame.draw.rect(self.screen,TAVERN_HOVER_GOLD if hovered else TAVERN_BRASS,
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
        # Show one coherent full text, not a duplicated baseline plus a
        # truncated v23 appendix. Historical ruleset descriptions are untouched.
        detail_summary=(full_preview_auction_copy(d.id,card_rarity(card),
                           getattr(self.game,'ruleset_version','v22'),summary.full)
                        if d.id.startswith('A0') and self.game.auction_catalog=='v22' and card_rarity(card) and identify_auction_variant(d) else
                        (v23_note or summary.full))
        guard_kills=self._guard_progress(uid)
        if guard_kills is not None:
            detail_summary=(
                f'EASTER EGG — CHORĄŻY ZAWSZE ZDĄŻY: {guard_kills}/3 zabójstw. '
                'Za zabicie wrogiej jednostki własnym zwykłym atakiem '
                'otrzymuje +1 ATK i +2 MAX PŻ oraz +2 bieżące PŻ, '
                'najwyżej trzykrotnie. Kontratak i efekty innych kart '
                'nie naliczają zabójstw.')
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((*TAVERN_SCRIM,225));self.screen.blit(shade,(0,0))
        box=pygame.Rect(146,75,1190,831)
        self._panel(box,TAVERN_PANEL_INNER,FACTION_COLORS[d.faction],18)
        pygame.draw.line(self.screen,TAVERN_BRASS,(489,160),(489,843),2)
        self._text('PODGLĄD KARTY',16,186,105,cfg.GOLD)
        details_attack=attack_display(self.game,uid) if u else None
        if self.details_image_zoom:
            # "Contain" is important here: see the ENTIRE existing image.
            # AUCTIONHAMMER_PIXEL_ART_70_v1
            if d.id in PIXEL_ART_IDS:
                artwork=self.cards_view.images.get_card_image(
                    f'pixel_art/{d.id}_portrait.png',(276,520),
                    mode='contain',pixelated=True)
            elif d.id in ART or (d.id=='SUM_START_GUARD' and d.name=='Chorąży'):
                file=(CHORAZY_ART_LEVELS[min(2,guard_kills)]
                      if guard_kills is not None else ART.get(d.id,ART['S34']))
                artwork=self.cards_view.images.get_card_image(
                    file,(276,520),mode='contain')
            else:
                current_rarity=card_rarity(
                    card,self.game.auction_awards.get(uid,{}).get('rarity'))
                artwork=(self.cards_view.images.get_auction_image(
                    d.id,current_rarity,(276,520),mode='contain')
                    if current_rarity is not None else None)
                if artwork is None:
                    artwork=self.cards_view.art(
                        d.id,d.faction,(276,520),d.family,d.name,
                        rarity=current_rarity)
            self.screen.blit(artwork,(184,164))
            self.detail_art_regions.append(pygame.Rect(184,164,276,520))
            self._text('POWIĘKSZONA ORYGINALNA ILUSTRACJA',13,186,697,cfg.MUTED)
        else:
            detail_start=len(self.cards_view.pixel_art_regions)
            self.cards_view.draw(self.screen,card,pygame.Rect(194,164,255,380),
                                 unit=u,selected=True,
                                 rarity=self.game.auction_awards.get(uid,{}).get('rarity'),
                                 animate_rarity=self.animations_enabled,
                                 guard_kills=guard_kills,
                                 statuses=active_statuses(self.game,uid) if u else hand_grants(self.game,uid),
                                 ready=details_attack.ready if u else None,
                                 attacks_total=details_attack.limit if u else None,
                                 attacks_remaining=details_attack.remaining if u else None)
            # CardView excludes the status/readiness plaques from the sharp
            # portrait segments; keep precisely those segments in this modal.
            self.detail_art_regions.extend(
                self.cards_view.pixel_art_regions[detail_start:])
            self._text(f'{d.id} • {d.faction}',18,194,570,FACTION_COLORS[d.faction])
            self._text(f'Aktywacja: {d.trigger}',16,194,600)
            self._text(f'Rodzina: {d.family}',16,194,629)
            label=(f'ZABÓJSTWA: {guard_kills}/3' if guard_kills is not None
                   else f'Poziom zdolności: {cue.ability_level}' if not d.id.startswith('SUM')
                   else 'JEDNOSTKA BEZ ROZWOJU NA RĘCE')
            self._text(self.cards_view.clip(label,self.fonts[16],276),16,194,659,cfg.GOLD)
            self._text(cue.next_threshold if not u else f'Pancerz {u.armor}  •  Tarcza {u.shield}',
                       14,194,685,cfg.MUTED)
            # Archetype baseline and actual MAX HP are distinct from wounds.
            raw_atk=u.atk if u else card.attack
            current_atk,_general=standard_hit_damage(
                raw_atk,active_statuses(self.game,uid) if u else ())
            current_max=u.max_hp if u else card.max_hp
            # Real deltas only; wounds stay separate from maximum HP.
            atk_label=(f'ATK  BAZA {d.atk} → TERAZ {current_atk}'
                       if current_atk!=d.atk else f'ATK  {current_atk} (bez zmian)')
            hp_label=(f'MAX PŻ  BAZA {d.hp} → TERAZ {current_max}'
                      if current_max!=d.hp else f'MAX PŻ  {current_max} (bez zmian)')
            self._text(atk_label,14,194,717,cfg.TEXT)
            self._text(hp_label,14,194,741,cfg.TEXT)
            if u:
                self._text(f'BIEŻĄCE PŻ: {max(0,u.hp)}/{current_max}',
                           14,194,765,cfg.MUTED)
        self._button(pygame.Rect(194,806,255,40),
                     '[G] KARTA' if self.details_image_zoom else '[G] ILUSTRACJA',
                     small=True,accent=self.details_image_zoom)

        self._text(self.cards_view.clip(d.name,self.fonts[28],760),28,520,115,FACTION_COLORS[d.faction])
        self._infographic_box(
            pygame.Rect(520,159,228,70),'AKTUALNY EFEKT',
            f'+{guard_kills} ATK / +{guard_kills*2} MAX PŻ'
            if guard_kills is not None else cue.base,cue.color,
            'Premia za zabójstwa' if guard_kills is not None else
            'Liczba zmienna oznaczona pogrubieniem')
        self._infographic_box(
            pygame.Rect(763,159,227,70),
            'AWANS ZA ZABÓJSTWA' if guard_kills is not None else 'CO 3 WŁASNE TURY NA RĘCE',
            f'{guard_kills}/3 ZABÓJSTW' if guard_kills is not None else cue.upgrade,
            cfg.GREEN,'MAX 3' if guard_kills is not None else 'Próg: 3 / 6 / 9 / 12…')
        self._infographic_box(pygame.Rect(1005,159,227,70),'MOMENT AKTYWACJI',cue.trigger,cfg.HOVER,
                              cue.family)
        pygame.draw.line(self.screen,cfg.PANEL_BORDER,(518,243),(1297,243),1)

        content_top=264;content_bottom=817
        y=content_top-self.details_scroll
        if u:
            damage, doubled=standard_hit_damage(
                u.atk, active_statuses(self.game,uid))
            if doubled:
                if content_top<=y<content_bottom-24:
                    self._text(f'GENERAŁ: ATK W WALCE {u.atk} × 2 = {damage} (PRZED OBRONĄ)',
                               16,520,y,cfg.GREEN)
                y+=35
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
        if content_top<=y<content_bottom-25:
            self._text('PREMIA ZA ZABÓJSTWA' if guard_kills is not None
                       else 'PRZYROST STATYSTYK NA RĘCE',18,520,y,cfg.GOLD)
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

    @staticmethod
    def menu_exit_rect():
        return pygame.Rect(535,722,420,52)

    def _change_audio_level(self,channel):
        if channel not in ('music','sfx'):
            return
        steps=round(self.audio_levels[channel]*10)
        self.audio_levels[channel]=((steps+1)%11)/10
        if channel=='music':
            self.music.set_volume(self.audio_levels[channel])
        else:
            self.sfx.set_volume(self.audio_levels[channel])
        save_levels(self.audio_levels)

    def _menu_click(self,pos):
        if self.menu_page=='settings':
            if pygame.Rect(430,282,300,34).collidepoint(pos):
                self._change_audio_level('music')
                return
            if pygame.Rect(745,282,300,34).collidepoint(pos):
                self._change_audio_level('sfx')
                return
        if self.menu_page=='main' and self.menu_exit_rect().collidepoint(pos):
            return self._request_exit()
        if (self.menu_page=='main'
                and pygame.Rect(430,282,180,34).collidepoint(pos)):
            return self._start_guided_match()
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
                    self._first_menu_game_unused=False
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
                        self._end_turn_warning=None
                        self._reset_hand_growth_tracking()
                        self.drag_start=None
                        self.drag_pointer=None
                        self.drag_return=None
                        # A loaded match is the last displayed seat; the next
                        # NEW MATCH opens from its opposite seat. Loading is
                        # not itself counted as starting a new game.
                        self._next_first_player=1-game.first
                        self._first_menu_game_unused=False
                        self.tutorial.active=False
                        self._audit_saved_match=None
                        self._audit_notice=''
                        self.selected=None
                        self.sidebar_card=None
                        self.details_card=None
                        self._old_pending=None
                        self.last_error=''
                        self._last_logged_event=len(game.event_journal)
                        self._recent_feedback=[]
                        self.combat_notice_active=None
                        self.combat_notice_queue=[]
                        self.attack_outcome_active=None
                        self._last_handled_attack_outcome=None
                        self.auction_inspect_index=None
                        self.combat_visuals=CombatVisuals()
                        self.combat_visuals.sync(game,self.slot_rect,self.hero_rect,pygame.time.get_ticks())
                        self.ability_feedback=AbilityFeedback()
                        self.ability_feedback.reset(game)
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
        shade.fill((*TAVERN_SCRIM,230))
        self.screen.blit(shade,(0,0))
        self._panel(pygame.Rect(420,170,650,660),TAVERN_PANEL_BG,TAVERN_GOLD,19)
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
            self._button(pygame.Rect(430,282,180,34),'SAMOUCZEK',small=True)
            self._button(pygame.Rect(625,282,240,34),'HISTORIA MECZÓW',small=True)
            self._button(pygame.Rect(875,282,160,34),'CREDITS',small=True)
            self._button(self.menu_exit_rect(),'WYJDŹ Z GRY  [Q]',small=True)
        else:
            # Independent levels: clicking steps by 10%, zero is mute.
            self._button(pygame.Rect(430,282,300,34),
                         f'MUZYKA: {round(100*self.audio_levels["music"])}%',small=True)
            self._button(pygame.Rect(745,282,300,34),
                         f'EFEKTY: {round(100*self.audio_levels["sfx"])}%',small=True)
            items=(f'ANIMACJE [A]: {"WŁ." if self.animations_enabled else "WYŁ."}',
                   'PEŁNY EKRAN [F11]',f'AI: {self.ai.difficulty.upper()}',
                   'ZAPISZ MECZ','POWRÓT DO MENU')
        for i,label in enumerate(items):
            self._button(pygame.Rect(535,322+i*81,420,61),label,accent=i==0)
        if self.menu_message:
            status=self.cards_view.clip(self.menu_message,self.fonts[14],620)
            self._text(status,14,746,784 if self.menu_page=='main' else 753,
                       cfg.GOLD,center=True)
        footer=(
            'Archiwum zachowuje wersje i dawne zasady'
            if self.menu_page=='archive' else
            'Kliknij MUZYKA / EFEKTY: +10% · 0% = wyciszone'
            if self.menu_page=='settings' else
            'F11 — pełny ekran · A — animacje · H — historia · M — menu'
        )
        self._text(footer,13,746,810 if self.menu_page=='main' else 790,
                   cfg.MUTED,center=True)

    def _draw_history_overlay(self):
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((*TAVERN_SCRIM,210))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(135,86,1205,818)
        self._panel(panel,TAVERN_PANEL_INNER,TAVERN_GOLD,13)
        journal=self.game.event_journal
        self._text(f'HISTORIA MECZU ({len(journal)} ZDARZEŃ)',28,173,126,cfg.GOLD)
        self._text('H / ESC — zamknij     P — zobacz zapisane stany planszy',15,174,168,cfg.MUTED)
        self._text('KÓŁKO MYSZY / STRZAŁKI — przewijaj',13,174,197,cfg.MUTED)
        end=max(0,len(journal)-self.history_scroll)
        page=journal[max(0,end-24):end]
        for i,item in enumerate(page):
            yy=226+i*26
            if i%2==0:
                pygame.draw.rect(self.screen,(90,65,42),
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
        shade.fill((*TAVERN_SCRIM,232))
        self.screen.blit(shade,(0,cfg.WINDOW_HEIGHT-87))
        frame=self.recorder.get(self.replay_index)
        self._text(f'POWTÓRKA · STAN {self.replay_index+1}/{len(self.recorder.frames)}'
                   f' · RUNDA {frame.round}',20,120,902,cfg.GOLD)
        self._text('← / →  POPRZEDNI / NASTĘPNY STAN      P / ESC  POWRÓT DO GRY',14,120,941,cfg.TEXT)

    def _finished_summary(self):
        """Calculate signed statistics once per finished game, not per frame."""
        if self.game.phase!='finished':
            return None
        if getattr(self,'_match_summary_game',None) is not self.game:
            self._match_summary_game=self.game
            self._match_summary_cache=build_match_summary(self.game)
        return self._match_summary_cache

    def _draw_gameover(self):
        if self.game.phase!='finished':return
        summary=self._finished_summary()
        overlay=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        overlay.fill((*TAVERN_SCRIM,205))
        self.screen.blit(overlay,(0,0))
        self._panel(pygame.Rect(164,117,1152,738),
                    TAVERN_PANEL_INNER,TAVERN_GOLD,16)
        won=self.game.winner==0
        color=cfg.GREEN if won else cfg.RED
        self._text('ZWYCIĘSTWO!' if won else 'PORAŻKA',46,740,142,
                   color,center=True)
        self._text('Wygrywa: '+self.game.players[self.game.winner].name,
                   20,740,209,cfg.TEXT,center=True)
        pygame.draw.line(self.screen,TAVERN_BRASS,(206,258),(1274,258),2)

        for owner in (0,1):
            p=self.game.players[owner]
            rect=pygame.Rect(205+owner*544,270,524,65)
            self._panel(rect,(28,43,52),cfg.GREEN if owner==0 else cfg.RED,8)
            # Preserve the historical, regression-tested "GRACZ: 0 PŻ"
            # presentation for clamped negative health.
            self._text(f'{p.name}: {summary.hero_hp[owner]} PŻ',18,
                       rect.x+15,rect.y+7,cfg.GOLD)
            self._text(f'MONETY: {summary.coins[owner]}',16,
                       rect.right-180,rect.y+9,cfg.TEXT)
            deaths=(str(summary.deaths[owner]) if summary.deaths else '—')
            self._text('ZGONY JEDNOSTEK: '+deaths,12,
                       rect.x+15,rect.y+37,cfg.MUTED)

        tiles=(
            ('RUNDA KOŃCOWA',str(summary.rounds)),
            ('WYSTAWIONE KARTY',str(summary.plays) if summary.plays is not None else '—'),
            ('WYKONANE ATAKI',str(summary.attacks) if summary.attacks is not None else '—'),
            ('KARTY ROZWINIĘTE',str(summary.levelled_cards)
             if summary.levelled_cards is not None else '—'),
        )
        for index,(label,value) in enumerate(tiles):
            rect=pygame.Rect(205+index*274,351,249,83)
            self._panel(rect,(35,51,60),TAVERN_BRASS,8)
            self._text(label,13,rect.centerx,rect.y+8,cfg.MUTED,center=True)
            self._text(value,28,rect.centerx,rect.y+54,cfg.GOLD,center=True)

        highlights=(
            ('NAJSILNIEJSZA JEDNOSTKA',
             summary.strongest.name if summary.strongest else 'Brak danych',
             (f'ATK {summary.strongest.attack} + MAX PŻ {summary.strongest.max_hp}'
              if summary.strongest else 'Wymagany pełny audyt'),
             (f'ŁĄCZNIE: {summary.strongest.power}' if summary.strongest else '')),
            ('NAJWIĘKSZY UBYTEK PŻ',
             f'{summary.largest_damage.hp_lost} PŻ' if summary.largest_damage else 'Brak danych',
             (summary.largest_damage.target_name if summary.largest_damage
              else 'Wymagany pełny audyt'),
             'Pojedynczy zarejestrowany efekt'),
            ('LIDER ROZWOJU',
             summary.leader.name if summary.leader else 'Brak awansów',
             (f'POZIOM ZDOLNOŚCI {summary.leader.level}'
              if summary.leader else 'Brak osiągniętego poziomu'),
             'Podstawowe karty gracza'),
        )
        for index,(title,name,detail,caption) in enumerate(highlights):
            rect=pygame.Rect(205+index*366,451,348,147)
            self._panel(rect,(33,48,58),TAVERN_BRASS,9)
            self._text(title,14,rect.centerx,rect.y+12,cfg.GOLD,center=True)
            f=self.fonts_bold[16]
            clipped=self.cards_view.clip(name,f,rect.width-24)
            self._text(clipped,16,rect.centerx,rect.y+50,cfg.TEXT,center=True)
            clipped=self.cards_view.clip(detail,self.fonts[14],rect.width-24)
            self._text(clipped,14,rect.centerx,rect.y+83,cfg.GREEN,center=True)
            self._text(caption,12,rect.centerx,rect.y+112,cfg.MUTED,center=True)

        if not summary.complete:
            footer='NIEPEŁNY AUDYT: szczegółowe osiągnięcia pominięto (starszy zapis)'
        else:
            footer=('Osiągnięcia na podstawie zapisu akcji i rzeczywistych '
                    'zmian statystyk')
        self._text(footer,13,740,609,cfg.MUTED,center=True)
        self._button(pygame.Rect(608,637,260,52),'NOWY MECZ',accent=True)
        self._button(pygame.Rect(885,637,239,52),'KSIĘGA STARC  [W]',small=True)
        self._button(pygame.Rect(392,702,325,46),'EKSPORT AUDYTU  [E]',small=True,accent=True)
        self._button(pygame.Rect(738,702,325,46),'OTWÓRZ FOLDER  [O]',small=True)
        self._text(f'Historia: {len(self.game.event_journal)} zdarzeń'
                   f'  ·  P — powtórka  ·  H — historia  ·  R — nowy mecz',
                   13,740,757,cfg.MUTED,center=True)
        notice=getattr(self,'_audit_notice','')
        if notice:
            font=self.fonts[13]
            self._text(self.cards_view.clip(notice,font,1025),
                       13,740,788,cfg.GOLD,center=True)

    def _draw_help_overlay(self):
        """Four-page, opt-in local reference; no new UI engine state."""
        if not self.help_open:
            return
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((*TAVERN_SCRIM,235))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(202,121,1080,739)
        self._panel(panel,TAVERN_PANEL_INNER,TAVERN_GOLD,17)
        page=HELP_PAGES[self.help_page]
        self._text('PODRĘCZNA POMOC · AUCTIONHAMMER',15,240,155,cfg.MUTED)
        self._text(page.title,28,240,195,cfg.GOLD)
        self._text(f'{self.help_page+1} / {len(HELP_PAGES)}',16,1160,191,cfg.GOLD)
        y=250
        for line in self._wrap(page.intro,16,984):
            self._text(line,16,246,y,cfg.TEXT)
            y+=24
        y+=20
        for heading,description in page.sections:
            self._text(heading,16,246,y,cfg.GOLD)
            y+=27
            for line in self._wrap(description,15,977):
                if y>744:
                    break
                self._text(line,15,258,y,cfg.TEXT)
                y+=21
            y+=16
            if y>744:
                break
        self._button(pygame.Rect(840,772,120,45),'← WSTECZ',
                     active=self.help_page>0,small=True)
        self._button(pygame.Rect(969,772,120,45),'DALEJ →',
                     active=self.help_page<len(HELP_PAGES)-1,small=True)
        self._button(pygame.Rect(1101,772,123,45),'ZAMKNIJ',small=True)
        self._text('F1 / ESC — zamknij · ← / → — zmień stronę',13,243,799,cfg.MUTED)

    def _tutorial_targets(self):
        """Canvas areas the player should try next; entirely read-only."""
        if not self.tutorial.active or self.tutorial_welcome_open:
            return []
        g=self.game
        if g.phase=='mulligan':
            if self._bonus_selection_due():
                return [pygame.Rect(438,443,604,67),pygame.Rect(438,537,604,67)]
            if 0 in g.mulligan_done:
                return []
            return list(self.hand_layout().values())+[pygame.Rect(1182,808,243,59)]
        if g.phase=='auction' and g.auction is not None:
            a=g.auction
            if a.turn!=0:
                return []
            if a.phase=='bidding':
                minimum,coins=self.auction_slider_bounds()
                if minimum>coins:
                    return [self.auction_control_rect('pass')]
                return [self.auction_slider_rect(),
                        self.auction_control_rect('bid'),
                        self.auction_control_rect('pass')]
            return [self.auction_offer_rect(i) for i,off in enumerate(a.offers)
                    if off.uid not in a.picks.values()]
        if g.phase!='turn':
            return []
        if g.pending is not None:
            return ([pygame.Rect(1099,160,326,650)] if g.pending.owner==0
                    else [])
        if g.active!=0:
            return []
        player=g.players[0]
        if not self.tutorial.play_seen:
            if player.played_this_turn:
                return [pygame.Rect(1201,816,221,52)]
            if self.selected in player.hand:
                if len(player.board)<5:
                    return [self.slot_rect(0,i) for i in g.available_slots(0)]
                return [self.slot_rect(0,g.slot_of(uid)) for uid in player.board
                        if g.can_play(0,self.selected,uid)]
            return list(self.hand_layout().values())
        if not self.tutorial.attack_seen:
            if self.selected in player.board:
                targets=g.legal_attacks(self.selected)
                if targets:
                    areas=[]
                    for target in targets:
                        if target=='hero:1':
                            areas.append(self.hero_rect(1))
                        elif target in g.players[1].board:
                            areas.append(self.slot_rect(1,g.slot_of(target)))
                    return areas
            ready=[uid for uid in player.board if g.legal_attacks(uid)]
            if ready:
                return [self.slot_rect(0,g.slot_of(uid)) for uid in ready]
            return [pygame.Rect(1201,816,221,52)]
        return []

    def _draw_tutorial_spotlights(self):
        if (not self.tutorial.active or self.tutorial_welcome_open
                or self.menu_open or self.history_open or self.help_open
                or self.confirm_action is not None or self.details_card is not None
                or self.replay_index is not None
                or self.auction_inspect_index is not None):
            return
        accent=(255,219,125) if pygame.time.get_ticks()//420%2==0 else (219,158,70)
        for rect in self._tutorial_targets()[:8]:
            outline=rect.inflate(9,9)
            pygame.draw.rect(self.screen,accent,outline,4,border_radius=12)
            pygame.draw.circle(self.screen,accent,
                               (outline.right-9,outline.top+9),7)

    def _draw_tutorial_welcome(self):
        if not self.tutorial_welcome_open:
            return
        shade=pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        shade.fill((*TAVERN_SCRIM,235))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(269,137,941,721)
        self._panel(panel,TAVERN_PANEL_INNER,cfg.GOLD,18)
        self.theme.carved_panel(self.screen,panel.inflate(-24,-22),opacity=64)
        self._text('PIERWSZY MECZ · TRYB NAUKI',16,740,177,cfg.MUTED,center=True)
        self._text('WITAJ W SAMOUCZKU',34,740,218,cfg.GOLD,center=True)
        self._text('Zagraj normalną partię, a gra pokaże Ci kolejne kroki.',
                   18,740,278,cfg.TEXT,center=True)
        self._text('Podświetlone na złoto karty i pola to sugerowane akcje.',
                   15,740,313,cfg.MUTED,center=True)
        steps=(
            ('01','PRZYGOTOWANIE','Wymień do 3 kart i wybierz rekompensatę.'),
            ('02','WYSTAWIANIE','Wybierz kartę z ręki i wolne pole planszy.'),
            ('03','ATAK','Wybierz jednostkę i podświetlony cel.'),
            ('04','AUKCJA','Licytuj pierwszeństwo wyboru i zdobądź kartę.'),
            ('05','GOTOWE','Samouczek podpowie, gdzie sprawdzić resztę zasad.'),
        )
        for i,(number,title,description) in enumerate(steps):
            y=355+i*70
            pygame.draw.rect(self.screen,(52,43,34),
                             pygame.Rect(354,y-6,780,61),border_radius=10)
            pygame.draw.rect(self.screen,TAVERN_BRASS,
                             pygame.Rect(354,y-6,780,61),1,border_radius=10)
            pygame.draw.circle(self.screen,(190,140,64),(396,y+24),19)
            self._text(number,15,396,y+24,(29,27,25),center=True)
            self._text(title,18,432,y,cfg.GOLD)
            self._text(description,14,432,y+27,cfg.TEXT)
        self._button(pygame.Rect(421,764,377,55),'ROZPOCZNIJ NAUKĘ  [ENTER]',accent=True)
        self._button(pygame.Rect(829,764,218,55),'POMIŃ  [ESC]')

    def draw(self):
        self.cards_view.pixel_art_regions.clear()
        self.auction_art_regions.clear()
        self.detail_art_regions.clear()
        # W powtórce renderujemy kopię, bez kierowania do niej jakichkolwiek
        # komend. Po każdej klatce przywracamy żywy Match.
        live=self.game
        if self.replay_index is not None:
            self.game=self.recorder.get(self.replay_index).game
        try:
            self.screen.blit(self.bg,(0,0))
            self._draw_header()
            self._draw_board()
            self._draw_tavern_beer()
            self._draw_phase_guidance()
            if self.replay_index is None and self.animations_enabled:
                self.combat_visuals.draw_cards(
                    self.screen,self.game,self.cards_view,pygame.time.get_ticks())
            self._draw_play_targets()
            self._draw_attack_targets()
            self._draw_attack_source_feedback()
            self._draw_sidebar()
            self._draw_log()
            self._draw_choices()
            self._draw_hover_guidance()
            self._draw_decision_preview()
            self._draw_drag_overlay()
            self._draw_attack_drag()
            self._draw_gameover()
            self._draw_auction()
            if self.replay_index is None and self.animations_enabled:
                self.combat_visuals.draw(self.screen,pygame.time.get_ticks(),
                                         self.fonts_bold[16])
                if self.game.phase=='turn' and hasattr(self,'ability_feedback'):
                    self.ability_feedback.draw(
                        self.screen,pygame.time.get_ticks(),self.fonts_bold[14])
            if self.replay_index is None:
                self._draw_details()
        finally:
            self.game=live
        # The auction / game-over scrims dim the header. Redraw its real,
        # clickable exit button ABOVE those overlays, but BELOW any modal.
        if (self.game.phase in ('auction', 'finished')
                and self.replay_index is None
                and not (self.menu_open or self.history_open or self.details_card
                         or self.confirm_action or self._bonus_selection_due())):
            self._button(self.exit_button_rect(), 'WYJDŹ', small=True)
        if self.replay_index is None:self._draw_auction_inspection()
        if self.replay_index is not None:self._draw_replay_controls()
        if self.history_open:self._draw_history_overlay()
        if self.menu_open:self._draw_menu()
        if self.confirm_action:self._draw_confirmation()
        if self.help_open:self._draw_help_overlay()
        if (self._bonus_selection_due() and not self.menu_open and not self.help_open
                and not self.history_open and self.replay_index is None
                and self.details_card is None):
            self._draw_bonus_selection()
        self._draw_tutorial_spotlights()
        if self.tutorial_welcome_open:self._draw_tutorial_welcome()
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
