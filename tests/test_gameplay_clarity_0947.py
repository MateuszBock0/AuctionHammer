"""0.9.47 Gameplay Clarity: read-only indicators and actual pygame render."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.audit import state_snapshot,digest
from game.ui.app import SoloApp
from game.ui.gameplay_clarity import turn_readout,selected_card_readout,combat_notice


def simple_game():
    return SimpleNamespace(
        phase='turn',active=0,pending=None,
        players=[SimpleNamespace(hand=['s1'],board=['u1'],played_this_turn=False),
                 SimpleNamespace(board=['enemy'])],
        units={'u1':object()},
        can_play=lambda owner,uid,replaced=None: owner==0 and uid=='s1' and replaced is None,
        legal_attacks=lambda uid: ['enemy'] if uid=='u1' else [],
    )


class GameplayReadoutTests(unittest.TestCase):
    def test_turn_counts_only_genuinely_available_actions(self):
        game=simple_game()
        hud=turn_readout(game)
        self.assertEqual((hud.played_cards,hud.ready_units,hud.can_play),(0,1,True))
        game.players[0].played_this_turn=True
        self.assertEqual((turn_readout(game).played_cards,turn_readout(game).can_play),(1,False))
        game.active=1
        self.assertEqual(turn_readout(game).ready_units,0)
        self.assertFalse(turn_readout(game).can_act)

    def test_pending_choice_and_full_board_replacement(self):
        game=simple_game()
        game.pending=SimpleNamespace(owner=0)
        self.assertFalse(turn_readout(game).can_act)
        game.pending=None
        game.players[0].board=['x1','x2','x3','x4','x5']
        game.units={uid:object() for uid in game.players[0].board}
        game.legal_attacks=lambda uid: []
        game.can_play=lambda owner,uid,replaced=None: replaced=='x2'
        self.assertTrue(turn_readout(game).can_play)
        game.can_play=lambda owner,uid,replaced=None: False
        self.assertFalse(turn_readout(game).can_play)

    def test_notice_keeps_exact_journal_words_and_defense_priority(self):
        for message,label in (
            ('Tarcza blokuje 4 obrażenia.','OBRONA / BLOKADA'),
            ('Pancerz pochłania 3 obrażenia.','OBRONA / BLOKADA'),
            ('Wilk zadaje 7 obrażeń.','OBRAŻENIA'),
            ('Zgon Wilka.','JEDNOSTKA POLEGŁA'),
            ('Strażnik leczy 2 PŻ.','LECZENIE'),
            ('Nadaje truciznę.','EFEKT / STATUS'),
        ):
            with self.subTest(message=message):
                cue=combat_notice(message)
                self.assertIsNotNone(cue)
                self.assertEqual(cue.label,label)
                self.assertEqual(cue.message,message)
        self.assertIsNone(combat_notice('Runda 1.'))


class GameplayCanvasTests(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        if self.app._bonus_selection_due():
            self.app._choose_bonus('coins')

    def tearDown(self):
        pygame.quit()

    def _turn_fixture(self):
        game=self.app.game
        game.phase='turn'
        game.active=0
        game.pending=None
        game.players[0].played_this_turn=False
        return game

    def test_gold_targets_only_for_selected_legal_hand_card(self):
        app=self.app
        game=self._turn_fixture()
        uid=game.players[0].hand[0]
        app.selected=uid
        before=digest(state_snapshot(game))
        targets=app._play_target_rects()
        self.assertEqual(len(targets),5-len(game.players[0].board))
        app._draw_play_targets()
        self.assertEqual(before,digest(state_snapshot(game)))
        app.selected=None
        self.assertFalse(app._play_target_rects())
        app.selected=uid
        game.active=1
        self.assertFalse(app._play_target_rects())

    def test_hud_and_sidebar_render_without_mutating_game(self):
        app=self.app
        game=self._turn_fixture()
        uid=game.players[0].hand[0]
        app.selected=uid
        before=digest(state_snapshot(game))
        hud=turn_readout(game)
        self.assertTrue(hud.can_play)
        self.assertEqual(selected_card_readout(game,uid).label,'ZAGRAJ KARTĘ')
        with patch.object(app,'_text',wraps=app._text) as spy:
            app._draw_phase_guidance()
            app._draw_sidebar()
        labels=[str(x.args[0]) for x in spy.call_args_list if x.args]
        self.assertIn('TWOJA TURA',labels)
        self.assertIn('KARTA 0/1',labels)
        self.assertIn('ZAGRAJ KARTĘ',labels)
        self.assertEqual(before,digest(state_snapshot(game)))

    def test_complete_turn_screen_renders_without_state_changes(self):
        app=self.app
        game=self._turn_fixture()
        uid=game.players[0].hand[0]
        app.selected=uid
        before=digest(state_snapshot(game))
        with patch.object(app,'_present'):
            app.draw()
        self.assertEqual(before,digest(state_snapshot(game)))

    def test_ticker_reads_events_even_with_vfx_off(self):
        app=self.app
        app.animations_enabled=False
        game=app.game
        game.event_journal.append({'text':'Tarcza blokuje 2 obrażenia.',
                                   'seq':999,'round':1,'active':0})
        before=digest(state_snapshot(game))
        app._capture_visual_feedback()
        self.assertIsNotNone(app.combat_notice_active)
        self.assertEqual(app.combat_notice_active[1].label,'OBRONA / BLOKADA')
        with patch.object(app,'_text',wraps=app._text) as spy:
            app._draw_log()
        self.assertTrue(any('OBRONA / BLOKADA' in str(x.args[0])
                            for x in spy.call_args_list if x.args))
        self.assertEqual(before,digest(state_snapshot(game)))

    def test_combat_notice_expires_without_engine_changes(self):
        app=self.app
        game=app.game
        app.combat_notice_active=(1000,combat_notice('Wilk zadaje 5 obrażeń.'))
        before=digest(state_snapshot(game))
        with patch('game.ui.app.pygame.time.get_ticks',return_value=4399):
            app._capture_visual_feedback()
            self.assertIsNotNone(app.combat_notice_active)
        with patch('game.ui.app.pygame.time.get_ticks',return_value=4400):
            app._capture_visual_feedback()
            self.assertIsNone(app.combat_notice_active)
        self.assertEqual(before,digest(state_snapshot(game)))


if __name__=='__main__':
    unittest.main()
