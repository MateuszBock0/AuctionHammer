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


class SafeSaveTests(unittest.TestCase):
    def test_save_roundtrip_preserves_rng_statuses_and_journal(self):
        import tempfile
        from pathlib import Path
        from game.core.persistence import save_match,load_match
        game=Match(91014)
        game._log('Kontrola powtórki po wczytaniu')
        game.players[0].hp=68
        game.players[0].coins=15
        game.players[1].hero_shield=1
        expected_rng=game.rng.getstate()
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'save.json'
            save_match(game,path)
            loaded=load_match(path)
        self.assertEqual(loaded.players[0].hp,68)
        self.assertEqual(loaded.players[0].coins,15)
        self.assertEqual(loaded.players[1].hero_shield,1)
        self.assertEqual(loaded.rng.getstate(),expected_rng)
        self.assertEqual(loaded.event_journal,game.event_journal)
        self.assertEqual(set(loaded.cards),set(game.cards))
        loaded.players[0].hp=1
        self.assertEqual(game.players[0].hp,68)

    def test_pending_choices_and_death_wave_queue_roundtrip(self):
        import tempfile
        from pathlib import Path
        from game.core.persistence import save_match,load_match
        from game.core.models import Pending,Choice
        game=Match(9150)
        choice=Choice('ally','hero:0','Lecz bohatera')
        game.pending=Pending('S02',0,'play',[choice],None)
        game.death_waves.append({
            'id':5,'fallen':('S21',),
            'source_ids':('S21',),'sources':None,
            'cursor':0,'decisions':[('S21',choice)]
        })
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'save.json'
            save_match(game,path)
            restored=load_match(path)
        self.assertEqual(restored.pending.choices[0],choice)
        self.assertEqual(restored.death_waves[0]['fallen'],('S21',))
        self.assertEqual(restored.death_waves[0]['decisions'][0][1],choice)

    def test_corrupted_and_incompatible_save_is_rejected(self):
        import tempfile
        import json
        from pathlib import Path
        from game.core.persistence import save_match,load_match
        game=Match(91015)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'save.json'
            save_match(game,path)
            document=json.loads(path.read_text(encoding='utf-8'))
            document['state']['items'][0][1]='naruszenie'
            path.write_text(json.dumps(document),encoding='utf-8')
            with self.assertRaises(ValueError):load_match(path)

    def test_save_does_not_execute_arbitrary_classes(self):
        from game.core.persistence import _decode
        with self.assertRaises(ValueError):
            _decode({'_type':'dataclass','name':'os.system','fields':{}})


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

    def test_upgraded_atlas_preserves_all_35_icons_at_real_ui_sizes(self):
        """Sprawdź rzeczywistą bitmapę Pygame: 35 ikon, 13 i 20 px."""
        from game.ui.game_icons import GameIcons, ATLAS_FILES, ATLAS_SIZE
        icons=GameIcons()
        source=icons._atlas_image()
        self.assertIsNotNone(source)
        self.assertEqual(ATLAS_SIZE,40)
        self.assertEqual(source.get_size(),(280,200))
        self.assertEqual(len(ATLAS_FILES),35)
        seen=set()
        for group in ('families','statuses','factions'):
            from game.ui.game_icons import FAMILY,FACTION
            if group=='families':
                keys=list(FAMILY)
            elif group=='factions':
                keys=list(FACTION)
            else:
                keys=[key.split('/')[1] for key in ATLAS_FILES
                      if key.startswith('statusy/')]
            for key in keys:
                for size in (13,20):
                    with self.subTest(group=group,key=key,size=size):
                        icon=icons.get(key,group,size)
                        self.assertIsNotNone(icon)
                        self.assertEqual(icon.get_size(),(size,size))
                        alpha=pygame.surfarray.array_alpha(icon)
                        self.assertGreater(int(alpha.max()),100)
                        self.assertTrue(int((alpha==0).sum())>0)
                        seen.add((group,key))
        self.assertEqual(len(seen),35)

    def test_atlas_has_more_detail_than_previous_24_color_version(self):
        """Test regresji jakości: nie wracaj do palety z 24 kolorami."""
        from pathlib import Path
        from game.ui.game_icons import BASE
        path=BASE/'icon_atlas_35.png'
        self.assertTrue(path.is_file())
        image=pygame.image.load(str(path))
        self.assertEqual(image.get_size(),(280,200))
        # 256-kolorowy atlas zachowuje detale i kanał alfa.
        pixels=pygame.surfarray.array3d(image)
        colors=len(set(zip(pixels[::3,::3,0].ravel().tolist(),
                           pixels[::3,::3,1].ravel().tolist(),
                           pixels[::3,::3,2].ravel().tolist())))
        self.assertGreater(colors,80)

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

    def test_ai_tournament_smoke_never_uses_auction_or_cost(self):
        from tools.simulate_ai_levels import tournament
        result=tournament(games=2,max_steps=70)
        self.assertEqual(result['games'],2)
        self.assertEqual(sum(result['scores'].values()),2)
        self.assertFalse(result['auctions'])
        self.assertEqual(result['specification'],'GAME_MASTER_v19')

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
