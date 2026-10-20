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
        self.assertEqual(len(targets),1)
        self.assertEqual(targets[0],app.slot_rect(0,len(game.players[0].board)))
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

    def test_ordered_combat_notices_survive_one_engine_command(self):
        app=self.app
        app.animations_enabled=False
        messages=('Tarcza blokuje 5 obrażeń.',
                  'Wilk otrzymuje 3 obrażenia.',
                  'Zgon Wilka.')
        for i,line in enumerate(messages):
            app.game.event_journal.append(
                {'text':line,'seq':700+i,'round':1,'active':0})
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            app._capture_visual_feedback()
        self.assertEqual(app.combat_notice_active[1].label,'OBRONA / BLOKADA')
        self.assertEqual(len(app.combat_notice_queue),2)
        with patch('game.ui.app.pygame.time.get_ticks',return_value=3600):
            app._capture_visual_feedback()
        self.assertEqual(app.combat_notice_active[1].label,'OBRAŻENIA')
        self.assertEqual(len(app.combat_notice_queue),1)
        with patch('game.ui.app.pygame.time.get_ticks',return_value=6200):
            app._capture_visual_feedback()
        self.assertEqual(app.combat_notice_active[1].label,'JEDNOSTKA POLEGŁA')
        self.assertEqual(len(app.combat_notice_queue),0)

    def test_tutorial_and_hud_are_both_visible(self):
        app=self.app
        game=self._turn_fixture()
        app.tutorial.start(game)
        app.tutorial_welcome_open=False
        with patch.object(app,'_text',wraps=app._text) as spy:
            app._draw_phase_guidance()
        labels=[str(x.args[0]) for x in spy.call_args_list if x.args]
        self.assertIn('KARTA 0/1',labels)
        self.assertTrue(any('SAMOUCZEK' in x for x in labels))

    def test_auction_inspect_button_never_bids_or_picks(self):
        from types import SimpleNamespace
        app=self.app
        a=SimpleNamespace(turn=0,phase='picking',offers=[
            SimpleNamespace(uid='offer-1',archetype='A014',
                            rarity='rzadka',atk=7,hp=8)])
        app.game.phase='auction'
        app.game.auction=a
        with patch.object(app,'_auction_do') as command:
            app._auction_click(app.auction_inspection_rect(0).center)
        self.assertEqual(app.auction_inspect_index,0)
        command.assert_not_called()
        with patch.object(app,'_text',wraps=app._text) as spy:
            app._draw_auction_inspection()
        shown=[str(c.args[0]) for c in spy.call_args_list if c.args]
        self.assertTrue(any('Kapłan' in txt for txt in shown))
        self.assertTrue(any('PEŁNY OPIS' in txt for txt in shown))
        # A paused inspection cannot be treated as an engine turn.
        with patch.object(app.ai,'step') as ai_move:
            app.update()
        ai_move.assert_not_called()
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_ESCAPE}))
        self.assertIsNone(app.auction_inspect_index)

    def test_combat_ticker_fits_entirely_inside_sidebar(self):
        app=self.app
        from game.ui.gameplay_clarity import combat_notice
        app.combat_notice_active=(1000,combat_notice(
            'Niedźwiedź Grzmotu zadaje wyjątkowo długi ciąg obrażeń '
            'dochodzący jednocześnie do kilku wrogich jednostek na planszy.'))
        app.combat_notice_queue=[]
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1100):
            with patch('game.ui.app.pygame.draw.rect',
                       wraps=pygame.draw.rect) as rectangles:
                with patch.object(app,'_text',wraps=app._text) as writing:
                    app._draw_log()
        sidebar=pygame.Rect(app.SIDEBAR_X,78,364,872)
        ticker=[c.args[2] for c in rectangles.call_args_list
                if len(c.args)>2 and isinstance(c.args[2],pygame.Rect)
                and c.args[2].x==1099]
        self.assertTrue(ticker)
        self.assertTrue(all(sidebar.contains(rect) for rect in ticker))
        message_labels=[c for c in writing.call_args_list
                        if len(c.args)>3 and 899<=c.args[3]<=950]
        self.assertTrue(message_labels)
        for call in message_labels:
            font=app.fonts[call.args[1]]
            self.assertLessEqual(call.args[3]+font.get_height(),sidebar.bottom)

    def test_tutorial_highlights_never_cover_auction_inspection(self):
        app=self.app
        app.tutorial.active=True
        app.tutorial_welcome_open=False
        app.auction_inspect_index=0
        with patch.object(app,'_tutorial_targets') as targeted:
            with patch('game.ui.app.pygame.draw.rect',
                       wraps=pygame.draw.rect) as border:
                app._draw_tutorial_spotlights()
        targeted.assert_not_called()
        border.assert_not_called()
        app.auction_inspect_index=None
        with patch.object(app,'_tutorial_targets',return_value=[
            pygame.Rect(70,70,90,110)]) as targeted:
            app._draw_tutorial_spotlights()
        targeted.assert_called_once()

    def test_combat_notice_expires_without_engine_changes(self):
        app=self.app
        game=app.game
        app.combat_notice_active=(1000,combat_notice('Wilk zadaje 5 obrażeń.'))
        before=digest(state_snapshot(game))
        with patch('game.ui.app.pygame.time.get_ticks',return_value=3599):
            app._capture_visual_feedback()
            self.assertIsNotNone(app.combat_notice_active)
        with patch('game.ui.app.pygame.time.get_ticks',return_value=3600):
            app._capture_visual_feedback()
            self.assertIsNone(app.combat_notice_active)
        self.assertEqual(before,digest(state_snapshot(game)))


if __name__=='__main__':
    unittest.main()
