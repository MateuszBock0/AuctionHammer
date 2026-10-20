"""0.9.38: globally accessible F11/A, phase guidance, no floating log.

These checks exercise actual Pygame event dispatch and ensure UI toggles do
not modify the deterministic game engine or signed audit state.
"""
import os
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.audit import state_snapshot,digest
from game.core.models import Pending,Choice
from game.ui.app import SoloApp
from test_auction_v22_0931 import award,ready
from test_auction_v4_engine import place_basic


class GuidanceAndGlobalShortcuts(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)

    def tearDown(self):
        pygame.quit()

    def test_f11_initial_menu_and_every_overlay(self):
        app=self.app
        def key():
            return pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_F11})
        with patch.object(app,'_toggle_fullscreen') as switch:
            for setup in (lambda:None,
                          lambda:setattr(app,'menu_open',False),
                          lambda:setattr(app,'history_open',True),
                          lambda:setattr(app,'history_open',False),
                          lambda:setattr(app,'replay_index',0),
                          lambda:setattr(app,'details_card',app.game.players[0].hand[0])):
                setup()
                self.assertTrue(app.handle(key()))
            self.assertEqual(switch.call_count,6)
        self.assertEqual(app.game.phase,'mulligan')

    def test_a_toggles_cosmetic_vfx_from_menu_and_from_game_without_engine_mutation(self):
        app=self.app
        before=digest(state_snapshot(app.game))
        for menu in (True,False,False):
            app.menu_open=menu
            current=app.animations_enabled
            self.assertTrue(app.handle(pygame.event.Event(
                pygame.KEYDOWN,{'key':pygame.K_a})))
            self.assertNotEqual(app.animations_enabled,current)
            self.assertEqual(digest(state_snapshot(app.game)),before)
            self.assertIn('ANIMACJE',app.visual_notice)
        self.assertFalse(app.history_open)

    def test_first_mulligan_guidance_explains_three_and_zero_and_confirmation(self):
        app=self.app
        if app._bonus_selection_due():
            self.assertIn('WYBÓR REKOMPENSATY',app._phase_guidance())
            app._choose_bonus('coins')
        self.assertIn('ZAZNACZ DO 3 KART',app._phase_guidance())
        self.assertIn('ENTER',app._phase_guidance())
        self.assertIn('ZERO',app._phase_guidance())
        app.menu_open=False
        app.click(app.hand_layout()[app.game.players[0].hand[0]].center)
        self.assertIn('1/3',app._phase_guidance())

    def test_pending_and_enemy_turn_explain_current_actor(self):
        app=self.app
        app.menu_open=False
        if app.game.first==1 and app.game.starting_compensation_choice is None:
            app.game.choose_starting_compensation(0,'coins')
        app.game.finish_mulligan(0,[])
        g=app.game
        g.pending=Pending('S01',0,'play',[Choice('test',None,'test')])
        self.assertIn('WYBIERZ CEL',app._phase_guidance())
        g.pending=None
        g.active=1
        self.assertIn('TURA KOMPUTERA',app._phase_guidance())

    def test_player_step_play_attack_end_instructions(self):
        app=self.app
        app.menu_open=False
        if app.game.first==1 and app.game.starting_compensation_choice is None:
            app.game.choose_starting_compensation(0,'coins')
        app.game.finish_mulligan(0,[])
        g=app.game
        g.phase='turn'
        g.active=0
        app.selected=None
        self.assertIn('ZAGRAJ',app._phase_guidance())
        hand=g.players[0].hand[0]
        app.selected=hand
        self.assertIn('WYBIERZ WOLNE POLE',app._phase_guidance())
        app.selected=None
        attacker=place_basic(g,'S27',0)
        g.units[attacker].played_turn=-10
        g.players[0].played_this_turn=True
        app.selected=attacker
        self.assertIn('ZAATAKUJ',app._phase_guidance())
        # With the v0.9.39 starter guard, more than one own unit can be
        # present. The end-turn hint appears only after ALL are exhausted.
        for unit_id in g.players[0].board:
            g.units[unit_id].attacks=2
        app.selected=None
        self.assertIn('ZAKOŃCZ TURĘ',app._phase_guidance())

    def test_no_false_play_prompt_after_all_five_board_units_attacked(self):
        app=self.app
        app.menu_open=False
        if app.game.first==1 and app.game.starting_compensation_choice is None:
            app.game.choose_starting_compensation(0,'coins')
        app.game.finish_mulligan(0,[])
        g=app.game
        g.phase='turn'
        g.active=0
        for uid in list(g.bank)[:max(0,5-len(g.players[0].board))]:
            place_basic(g,uid,0)
        # The second-player starting guard may already occupy one of 5 slots.
        # Every existing unit must have spent both possible attacks.
        for uid in g.players[0].board:
            g.units[uid].attacks=2
        g.players[0].played_this_turn=False
        self.assertEqual(len(g.players[0].board),5)
        app.selected=g.players[0].hand[0]
        self.assertIn('BRAK JEDNOSTKI DO ZASTĄPIENIA',app._phase_guidance())
        app.selected=None
        self.assertIn('ZAKOŃCZ TURĘ',app._phase_guidance())
        g.assert_integrity()

    def test_log_is_confined_to_sidebar_and_history_is_explicit_overlay(self):
        app=self.app
        calls=[]
        original=app._text
        def spy(label,size,x,y,color=None,center=False):
            calls.append((str(label),x,y))
            return original(label,size,x,y,color,center)
        with patch.object(app,'_text',side_effect=spy):
            app._draw_log()
        self.assertTrue(calls)
        self.assertTrue(all(x>=1100 for label,x,y in calls))
        self.assertTrue(any('OSTATNIE ZDARZENIE' in label for label,_,_ in calls))
        self.assertFalse(app.history_open)
        app.menu_open=False
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_h}))
        self.assertTrue(app.history_open)
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_ESCAPE}))
        self.assertFalse(app.history_open)

    def test_render_guidance_is_inside_reserved_between_board_corridor(self):
        app=self.app
        app.menu_open=False
        labels=[]
        original=app._text
        def spy(label,size,x,y,color=None,center=False):
            r=original(label,size,x,y,color,center)
            labels.append((str(label),r))
            return r
        with patch.object(app,'_text',side_effect=spy):
            app._draw_phase_guidance()
        self.assertEqual(len(labels),2)
        self.assertTrue(all(pygame.Rect(96,373,952,54).contains(rect) for _,rect in labels))
        app.draw()


if __name__=='__main__':
    unittest.main()
