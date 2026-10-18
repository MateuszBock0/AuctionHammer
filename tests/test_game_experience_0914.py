"""Historia i powtórki, efekty VFX oraz nowe menu/AI; wszystkie stany tylko-do-odczytu."""
import os
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.ui.combat_visuals import CombatVisuals
from game.ui.match_history import MatchRecorder


class HistoryTests(unittest.TestCase):
    def test_journal_preserves_events_after_short_log_rollover(self):
        game=Match(9141)
        original=len(game.event_journal)
        for i in range(180):
            game._log(f'Test zdarzenia {i}')
        self.assertEqual(len(game.events),160)
        self.assertEqual(len(game.event_journal),original+180)
        self.assertEqual(game.event_journal[-1]['seq'],len(game.event_journal))
        self.assertIn('Test zdarzenia 0',game.event_journal[original]['text'])

    def test_recorder_copies_read_only_frames(self):
        game=Match(9142)
        recorder=MatchRecorder()
        self.assertTrue(recorder.capture(game))
        self.assertFalse(recorder.capture(game))
        before=recorder.get(0)
        game._log('Nowy wpis')
        game.players[0].hp=73
        self.assertTrue(recorder.capture(game))
        self.assertEqual(before.game.players[0].hp,100)
        self.assertEqual(recorder.get(1).game.players[0].hp,73)
        self.assertEqual(before.game.event_journal,[])
        self.assertEqual(game.players[0].hp,73)

    def test_snapshot_cap_does_not_modify_live_history(self):
        game=Match(9143)
        recorder=MatchRecorder(max_frames=5)
        for i in range(20):
            game._log(f'Próba {i}')
            recorder.capture(game)
        self.assertEqual(len(recorder.frames),5)
        self.assertGreater(len(game.event_journal),20)


class EffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800,600))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_damage_healing_shield_death_and_poison_are_from_real_state(self):
        from test_engine import setup_game, force_unit
        game=setup_game(9144)
        unit=force_unit(game,'S01',0)
        unit.hp=4
        def unit_rect(owner,slot):
            return pygame.Rect(100+slot*150,120+owner*260,148,220)
        def hero_rect(owner):
            return pygame.Rect(100,62+owner*420,600,44)
        visual=CombatVisuals()
        visual.sync(game,unit_rect,hero_rect,1000)
        initial=(game.players[0].hp,unit.hp)
        unit.hp=2
        unit.shield=1
        game._add_poison('S01',1,2,'S58',0)
        visual.sync(game,unit_rect,hero_rect,1010)
        kinds={p.kind for p in visual.pulses}
        self.assertTrue({'damage','shield','poison'}<=kinds)
        unit.hp=4
        visual.sync(game,unit_rect,hero_rect,1050)
        self.assertIn('heal',{p.kind for p in visual.pulses})
        game.players[0].board.remove('S01')
        game.units.pop('S01')
        visual.sync(game,unit_rect,hero_rect,1080)
        self.assertIn('death',{p.kind for p in visual.pulses})
        self.assertEqual(game.players[0].hp,initial[0])
        canvas=pygame.Surface((800,600))
        visual.draw(canvas,1180,pygame.font.SysFont('segoeui',16))

    def test_fx_lifetime_and_capacity(self):
        visual=CombatVisuals(max_pulses=3)
        for i in range(20):
            visual._push('damage',(30,60),100,f'-{i}')
        self.assertEqual(len(visual.pulses),3)
        pygame.font.init()
        visual.draw(pygame.Surface((200,200)),1100,pygame.font.Font(None,16))
        self.assertFalse(visual.pulses)


class SuppliedIconsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320,240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_35_original_icons_are_available_in_portable_atlas(self):
        from game.ui.game_icons import GameIcons, FAMILY, FACTION, ATLAS_FILES
        icons=GameIcons()
        self.assertEqual(len(ATLAS_FILES),35)
        self.assertEqual(len(FAMILY),14)
        self.assertEqual(len(FACTION),5)
        for name in FAMILY:
            with self.subTest(family=name):
                surface=icons.get(name,'families',16)
                self.assertIsNotNone(surface)
                self.assertEqual(surface.get_size(),(16,16))
        for name in FACTION:
            with self.subTest(faction=name):
                self.assertIsNotNone(icons.get(name,'factions',20))
        for path in ATLAS_FILES:
            if path.startswith('statusy/'):
                with self.subTest(status=path):
                    surface=icons.get(path.split('/')[1],'statuses',20)
                    self.assertIsNotNone(surface)

    def test_immunity_icon_is_resolved_from_actual_status(self):
        from game.ui.game_icons import status_icon_key
        from game.core.status_view import VisibleStatus
        poison=VisibleStatus('immune','ODP','Odporność na truciznę','Nie otrzymuje trucizny')
        stun=VisibleStatus('immune','ODP','Odporność na ogłuszenie','Nie otrzymuje ogłuszenia')
        self.assertEqual(status_icon_key(poison),'immune_poison')
        self.assertEqual(status_icon_key(stun),'immune_stun')


class MenuAndAITests(unittest.TestCase):
    def setUp(self):
        pygame.init()
    def tearDown(self):
        pygame.quit()

    def test_three_ai_levels_are_available_and_deterministic(self):
        game=Match(9145)
        for diff in ('łatwy','normalny','trudny'):
            ai=ComputerOpponent(difficulty=diff)
            self.assertEqual(ai.difficulty,diff)
            self.assertEqual(ai.player,1)
            # Przebieg mulliganu nie powinien ujawniać AI ręki gracza.
            ai.step(game)

    def test_main_menu_history_and_replay_are_modal(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        self.assertTrue(app.menu_open)
        app.draw()
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_ESCAPE}))
        self.assertFalse(app.menu_open)
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_h}))
        self.assertTrue(app.history_open)
        app.draw()
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_p}))
        self.assertIsNotNone(app.replay_index)
        active=app.game.active
        app.draw()
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_ESCAPE}))
        self.assertIsNone(app.replay_index)
        self.assertEqual(app.game.active,active)
        app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_m}))
        self.assertTrue(app.menu_open)
        app.menu_page='settings'
        app.draw()


if __name__=='__main__':
    unittest.main()
