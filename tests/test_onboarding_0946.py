"""0.9.46: genuine read-only onboarding, input routing and tutorial flow."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.core.audit import state_snapshot, digest
from game.ui.app import SoloApp
from game.ui.onboarding import TutorialProgress, HELP_PAGES, attack_reason_help


def fake_match():
    return SimpleNamespace(
        phase="mulligan",first=0,active=0,
        starting_compensation="choice_2_5_or_coins",
        starting_compensation_choice=None,pending=None,auction=None,
        auction_history=[],audit_actions=[],
        players=[SimpleNamespace(board=[],mulligan_selected=[]),
                 SimpleNamespace(board=[],mulligan_selected=[])],
        legal_attacks=lambda uid: []
    )


class TutorialLogicTests(unittest.TestCase):
    def test_five_stages_are_driven_by_real_successful_commands(self):
        g=fake_match()
        coach=TutorialProgress()
        coach.start(g)
        self.assertEqual(coach.hint(g).stage,1)
        g.phase="turn"
        self.assertEqual(coach.hint(g).stage,2)
        g.audit_actions.append({"result":"illegal","command_owner":0,"operation":"play"})
        coach.observe(g)
        self.assertFalse(coach.play_seen)
        g.audit_actions.append({"result":"ok","command_owner":1,"operation":"play"})
        coach.observe(g)
        self.assertFalse(coach.play_seen)
        g.audit_actions.append({"result":"ok","command_owner":0,"operation":"play"})
        coach.observe(g)
        self.assertEqual(coach.hint(g).stage,3)
        g.audit_actions.append({"result":"ok","command_owner":0,"operation":"attack"})
        coach.observe(g)
        self.assertEqual(coach.hint(g).stage,4)
        g.auction=SimpleNamespace(phase="bidding",turn=0)
        g.phase="auction"
        self.assertIn("LICYTACJA",coach.hint(g).title)
        g.auction.phase="picking"
        self.assertIn("WYBÓR",coach.hint(g).title)
        g.auction.turn=1
        self.assertIn("RUCH KOMPUTERA",coach.hint(g).title)
        g.auction.turn=0
        g.phase="turn"
        g.auction_history=[{"number":1}]
        coach.observe(g)
        self.assertEqual(coach.hint(g).stage,5)

    def test_pending_and_second_player_bonus_override_lessons(self):
        g=fake_match()
        g.first=1
        coach=TutorialProgress()
        coach.start(g)
        self.assertIn("REKOMPENSATA",coach.hint(g).title)
        g.starting_compensation_choice="coins"
        self.assertIn("WYMIANA",coach.hint(g).title)
        g.phase="turn"
        g.pending=SimpleNamespace(owner=0)
        self.assertIn("ZDOLNOŚĆ",coach.hint(g).title)
        g.pending.owner=1
        self.assertIn("RUCH KOMPUTERA",coach.hint(g).title)

    def test_help_content_and_reason_explanations(self):
        self.assertEqual(len(HELP_PAGES),4)
        self.assertIn("Atakować",attack_reason_help("CZEKA NA TURĘ"))
        self.assertIn("Szybki atak",attack_reason_help("NOWA JEDNOSTKA"))
        self.assertIn("Prowokację",attack_reason_help("BRAK LEGALNEGO CELU"))
        self.assertIn("Szybki atak",HELP_PAGES[1].sections[3][1])


class TutorialInterfaceTests(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)

    def tearDown(self):
        pygame.quit()

    @staticmethod
    def key(which):
        return pygame.event.Event(pygame.KEYDOWN,{"key":which})

    @staticmethod
    def click(pos):
        return pygame.event.Event(pygame.MOUSEBUTTONUP,{"pos":pos,"button":1})

    def test_menu_guided_match_is_opt_in_and_non_mutating(self):
        app=self.app
        before=digest(state_snapshot(app.game))
        self.assertFalse(app.tutorial.active)
        app.help_open=True
        with patch.object(app,"_present"):
            app._draw_help_overlay()
        self.assertEqual(before,digest(state_snapshot(app.game)))
        app.help_open=False
        with patch.object(app,"_physical_to_virtual",side_effect=lambda x:x):
            self.assertTrue(app.handle(self.click((500,299))))
        self.assertTrue(app.tutorial.active)
        self.assertFalse(app.menu_open)
        self.assertEqual(app.game.phase,"mulligan")
        self.assertTrue(app.tutorial_welcome_open)
        self.assertIsNotNone(app.tutorial.hint(app.game))

    def test_all_help_pages_are_renderable_and_read_only(self):
        app=self.app
        app.menu_open=False
        before=digest(state_snapshot(app.game))
        app.help_open=True
        with patch.object(app,"_present"):
            for index in range(len(HELP_PAGES)):
                app.help_page=index
                app.draw()
        self.assertEqual(before,digest(state_snapshot(app.game)))

    def test_visible_welcome_is_modal_and_only_start_closes_it(self):
        app=self.app
        app.menu_open=True
        with patch.object(app,"_physical_to_virtual",side_effect=lambda x:x):
            app.handle(self.click((500,299)))
        self.assertTrue(app.tutorial_welcome_open)
        before=digest(state_snapshot(app.game))
        with patch.object(app,"_button",wraps=app._button) as painted:
            with patch.object(app,"_present"):
                app.draw()
        self.assertIn("ROZPOCZNIJ NAUKĘ  [ENTER]",
                      [x.args[1] for x in painted.call_args_list if len(x.args)>1])
        app.handle(self.key(pygame.K_SPACE))
        self.assertFalse(app.tutorial_welcome_open)
        self.assertTrue(app.tutorial.active)
        self.assertEqual(before,digest(state_snapshot(app.game)))

    def test_welcome_skip_disables_coach_without_executing_game_action(self):
        app=self.app
        app._start_guided_match()
        before=digest(state_snapshot(app.game))
        app.handle(self.key(pygame.K_ESCAPE))
        self.assertFalse(app.tutorial_welcome_open)
        self.assertFalse(app.tutorial.active)
        self.assertEqual(before,digest(state_snapshot(app.game)))

    def test_gold_targets_follow_game_state_and_keep_engine_unchanged(self):
        app=self.app
        app._start_guided_match()
        app.handle(self.key(pygame.K_RETURN))
        game=app.game
        before=digest(state_snapshot(game))
        if app._bonus_selection_due():
            self.assertEqual(len(app._tutorial_targets()),2)
        else:
            self.assertTrue(app._tutorial_targets())
        with patch.object(app,"_present"):
            app.draw()
        self.assertEqual(before,digest(state_snapshot(game)))
        app.tutorial.active=False
        self.assertEqual(app._tutorial_targets(),[])

    def test_help_can_still_open_after_welcome(self):
        app=self.app
        app._start_guided_match()
        app.handle(self.key(pygame.K_RETURN))
        app.handle(self.key(pygame.K_F1))
        self.assertTrue(app.help_open)
        self.assertFalse(app.tutorial_welcome_open)

    def test_F1_help_is_modal_even_during_auction(self):
        app=self.app
        app.menu_open=False
        app.game.phase="auction"
        # Help routing is safe even without a running auction overlay.
        before=digest(state_snapshot(app.game))
        self.assertTrue(app.handle(self.key(pygame.K_F1)))
        self.assertTrue(app.help_open)
        self.assertTrue(app.handle(self.key(pygame.K_RIGHT)))
        self.assertEqual(app.help_page,1)
        self.assertTrue(app.handle(self.key(pygame.K_ESCAPE)))
        self.assertFalse(app.help_open)
        self.assertEqual(before,digest(state_snapshot(app.game)))

    def test_switch_guide_without_changing_gameplay(self):
        app=self.app
        app.menu_open=False
        before=digest(state_snapshot(app.game))
        app.handle(self.key(pygame.K_t))
        self.assertTrue(app.tutorial.active)
        app.update()
        with patch.object(app,"_present"):
            app.draw()
        app.handle(self.key(pygame.K_t))
        self.assertFalse(app.tutorial.active)
        self.assertEqual(before,digest(state_snapshot(app.game)))

    def test_help_keyboard_and_mouse_do_not_escape_to_game(self):
        app=self.app
        app.menu_open=False
        app.game.phase="turn"
        before=digest(state_snapshot(app.game))
        app.handle(self.key(pygame.K_F1))
        with patch.object(app,"_physical_to_virtual",side_effect=lambda x:x):
            app.handle(self.click((1025,792)))
        self.assertEqual(app.help_page,1)
        app.handle(self.key(pygame.K_SPACE))
        app.handle(self.key(pygame.K_q))
        self.assertTrue(app.help_open)
        self.assertEqual(before,digest(state_snapshot(app.game)))
        with patch.object(app,"_physical_to_virtual",side_effect=lambda x:x):
            app.handle(self.click((1160,792)))
        self.assertFalse(app.help_open)

    def test_guided_restart_confirmation_can_be_cancelled(self):
        app=self.app
        app.game.phase="turn"
        before=digest(state_snapshot(app.game))
        with patch.object(app,"_physical_to_virtual",side_effect=lambda x:x):
            app.handle(self.click((500,299)))
        self.assertEqual(app.confirm_action,"restart")
        self.assertFalse(app.tutorial.active)
        app.handle(self.key(pygame.K_ESCAPE))
        self.assertFalse(app._start_tutorial_after_restart)
        self.assertEqual(before,digest(state_snapshot(app.game)))
        with patch.object(app,"_physical_to_virtual",side_effect=lambda x:x):
            app.handle(self.click((500,299)))
        self.assertEqual(app.confirm_action,"restart")
        # Discard path starts fresh guided match with the existing confirmation.
        self.assertTrue(app.handle(self.key(pygame.K_d)))
        self.assertTrue(app.tutorial.active)
        self.assertTrue(app.tutorial_welcome_open)
        self.assertEqual(app.game.phase,"mulligan")
        self.assertFalse(app.menu_open)


if __name__=="__main__":
    unittest.main()
