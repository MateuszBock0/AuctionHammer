"""End-to-end forensic match companion file and finished UI launcher."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

from game.core.audit import write_last_match, read_report
from game.core.combat_html import FILENAME, render_combat_html
from game.core.engine import Match


class CombatHtmlAcceptance(unittest.TestCase):
    def test_finished_match_exports_companion_html_and_preserves_signed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'LOCALAPPDATA':directory}):
                game=Match(9440,audit_enabled=True)
                game.phase='finished'
                game.winner=0
                written=write_last_match(game)
                html_path=written.with_name(FILENAME)
                self.assertTrue(written.is_file())
                self.assertTrue(html_path.is_file())
                self.assertEqual(read_report(written)['summary']['combat_attacks'],0)
                document=html_path.read_text(encoding='utf8')
                self.assertIn('Księga Starć',document)
                self.assertIn('Widoczne walki:',document)
                self.assertIn('PRZED',document)
                self.assertIn('PO',document)

    def test_explicit_destination_only_writes_requested_json(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'latest.json'
            game=Match(9441,audit_enabled=True)
            game.phase='finished'
            game.winner=0
            write_last_match(game,file)
            self.assertTrue(file.is_file())
            self.assertFalse(file.with_name(FILENAME).exists())

    def test_old_audit_without_combat_analysis_is_renderable(self):
        initial={
            'players':{'0':{'hp':100},'1':{'hp':99}},
            'units':{'S01':{'hp':3,'owner':0,'current_attack':2,
                              'current_max_hp':4,'shield':0,'effects':[],'attacks':0}},
            'cards':{},'pending':None,'deferred_attack':None
        }
        report={'seed':12,'environment':{'build':{'commit':None}},
                'initial_state':initial,
                'actions':[{'seq':1,'operation':'attack','args':['S01','hero:1'],
                            'actor_before':0,'round_before':1,'result':'ok',
                            'changes':{'players':{'1':{'before':{'hp':99},
                                                       'after':{'hp':97}}}}}],
                'internal_events':[],
                'event_journal':[{'action_seq':1,'text':'Przykładowy atak & tarcza'}]}
        document=render_combat_html(report)
        self.assertIn('Przykładowy atak &amp; tarcza',document)
        self.assertIn('S01',document)
        self.assertIn('hero:1',document)
        self.assertNotIn('<script src=',document)
        self.assertNotIn('http://',document)

    def test_finished_screen_book_button_opens_report(self):
        import pygame
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        try:
            app.menu_open=False
            app.game.phase='finished'
            app.game.winner=0
            with patch.object(app,'_open_combat_book') as opener:
                app.click(pygame.Rect(885,637,239,52).center)
                opener.assert_called_once()
                opener.reset_mock()
                app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_w}))
                opener.assert_called_once()
        finally:
            pygame.quit()


if __name__=='__main__':
    unittest.main()
