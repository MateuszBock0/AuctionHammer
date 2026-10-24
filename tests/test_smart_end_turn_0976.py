"""0.9.76: end-turn CTA is accurate, non-blocking and uses both input paths."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.audit import digest, state_snapshot
from game.ui.app import SoloApp
from game.ui.gameplay_clarity import turn_readout
from test_engine import setup_game, force_unit


class SmartEndTurn0976(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',
                          return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self.app.tutorial_welcome_open=False
        self.app.game=setup_game(76001)
        self.app._end_turn_warning=None
        self.app.selected=None

    def tearDown(self):
        pygame.quit()

    def click_button(self):
        self.app.click(pygame.Rect(1201,816,221,52).center)

    def press_space(self):
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,
                                           {'key':pygame.K_SPACE}))

    def test_first_click_warns_without_mutating_match(self):
        app=self.app
        self.assertTrue(turn_readout(app.game).can_play)
        before=digest(state_snapshot(app.game))
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            self.click_button()
            self.assertTrue(app._end_turn_warning_active())
            self.assertIn('KARTA',app._end_turn_warning_text(turn_readout(app.game)))
            self.assertEqual(digest(state_snapshot(app.game)),before)
            self.assertEqual(app.game.active,0)

    def test_second_click_confirms_and_clears_selection(self):
        app=self.app
        app.selected=app.game.players[0].hand[0]
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            self.click_button()
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1400):
            self.click_button()
        self.assertEqual(app.game.active,1)
        self.assertIsNone(app.selected)
        self.assertIsNone(app._end_turn_warning)

    def test_space_then_click_and_click_then_space_equivalent(self):
        for first in ('space','click'):
            with self.subTest(first=first):
                app=self.app
                app.game=setup_game(76002)
                app._end_turn_warning=None
                before=digest(state_snapshot(app.game))
                with patch('game.ui.app.pygame.time.get_ticks',return_value=1100):
                    self.press_space() if first=='space' else self.click_button()
                    self.assertEqual(digest(state_snapshot(app.game)),before)
                    self.assertTrue(app._end_turn_warning_active())
                with patch('game.ui.app.pygame.time.get_ticks',return_value=1200):
                    self.click_button() if first=='space' else self.press_space()
                    self.assertEqual(app.game.active,1)

    def test_no_legal_actions_finish_immediately_without_warning(self):
        app=self.app
        app.game.players[0].played_this_turn=True
        self.assertFalse(turn_readout(app.game).can_act)
        self.click_button()
        self.assertEqual(app.game.active,1)
        self.assertIsNone(app._end_turn_warning)

    def test_ready_ally_is_reported_even_after_card_play(self):
        app=self.app
        app.game.players[0].played_this_turn=True
        force_unit(app.game,'S09',0)
        cue=turn_readout(app.game)
        self.assertFalse(cue.can_play)
        self.assertGreater(cue.ready_units,0)
        with patch('game.ui.app.pygame.time.get_ticks',return_value=950):
            self.press_space()
            self.assertIn('GOTOWA JEDNOSTKA',
                          app._end_turn_warning_text(turn_readout(app.game)))
            self.assertEqual(app.game.active,0)

    def test_warning_expires_and_requires_fresh_first_attempt(self):
        app=self.app
        before=digest(state_snapshot(app.game))
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            self.press_space()
        expired=1000+app.END_TURN_WARNING_MS
        with patch('game.ui.app.pygame.time.get_ticks',return_value=expired):
            self.assertFalse(app._end_turn_warning_active())
            self.press_space()
            self.assertEqual(digest(state_snapshot(app.game)),before)
            self.assertTrue(app._end_turn_warning_active())
        with patch('game.ui.app.pygame.time.get_ticks',return_value=expired+300):
            self.press_space()
            self.assertEqual(app.game.active,1)

    def test_game_action_invalidates_old_confirmation(self):
        app=self.app
        uid=app.game.players[0].hand[0]
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            self.press_space()
            self.assertTrue(app._end_turn_warning_active())
            app.game.play(uid)
            self.assertFalse(app._end_turn_warning_active())
            # Existing warning cannot skip new choices after playing.
            self.press_space()
            self.assertEqual(app.game.active,0)

    def test_new_game_and_save_load_cannot_reuse_confirmation(self):
        app=self.app
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            self.press_space()
            self.assertTrue(app._end_turn_warning_active())
        app.restart()
        self.assertIsNone(app._end_turn_warning)
        self.assertFalse(app._end_turn_warning_active())
        app.game=setup_game(76003)
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1600):
            self.press_space()
            self.assertEqual(app.game.active,0)

    def test_draw_button_states_are_derived_from_real_legal_actions(self):
        app=self.app
        # Call the underlying side panel so labels reflect normal gameplay.
        lines=[]
        button=app._button
        text=app._text
        with patch.object(app,'_button',side_effect=lambda *a,**k:
                          (lines.append((a[1],k)),button(*a,**k))[1]):
            app._draw_sidebar()
        states=[(label,opts) for label,opts in lines if 'TURĘ' in label]
        self.assertEqual(len(states),1)
        self.assertFalse(states[0][1].get('accent',False))
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            self.press_space()
            lines.clear()
            with patch.object(app,'_button',side_effect=lambda *a,**k:
                              (lines.append((a[1],k)),button(*a,**k))[1]):
                app._draw_sidebar()
            self.assertTrue(any('POTWIERDŹ' in label for label,_ in lines))
        app._end_turn_warning=None
        app.game.players[0].played_this_turn=True
        lines.clear()
        with patch.object(app,'_button',side_effect=lambda *a,**k:
                          (lines.append((a[1],k)),button(*a,**k))[1]):
            app._draw_sidebar()
        self.assertTrue(any('ZAKOŃCZ TURĘ' in label and opt.get('accent')
                            for label,opt in lines))

    def test_nonhuman_turn_never_accepts_endturn_request(self):
        app=self.app
        app.game.active=1
        self.assertFalse(app._end_turn_available())
        before=digest(state_snapshot(app.game))
        self.click_button()
        self.press_space()
        self.assertEqual(digest(state_snapshot(app.game)),before)
        self.assertFalse(app._end_turn_warning_active())


if __name__=='__main__':
    unittest.main()
