"""0.9.39: new 5/5 compensation, versioned replay, and UI safety acceptance."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from game.core.engine import Match
from game.core.audit import digest, state_snapshot, make_report, verify_replay
from game.core.persistence import save_match, load_match
from game.ui.app import SoloApp

TOKEN="SUM_START_GUARD"

def new_match(seed=390001):
    return Match(seed,audit_enabled=True,auctions_enabled=True,
                 auction_catalog="v22",starting_compensation="unit_5_5")

def finish_mulligan(game):
    for owner in (0,1):
        game.finish_mulligan(owner,[])

def replay_factory(seed,auctions_enabled=False,auction_catalog="v3",
                   starting_compensation="coins"):
    return Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
                 auction_catalog=auction_catalog,
                 starting_compensation=starting_compensation)

class StartingGuard(unittest.TestCase):
    def test_guard_belongs_to_second_player_without_coins_or_bank_pollution(self):
        for seed in range(390010,390030):
            with self.subTest(seed=seed):
                game=new_match(seed)
                second=1-game.first
                self.assertEqual(len(game.defs),70)
                self.assertEqual(len(game.cards),71)
                self.assertEqual((game.players[0].coins,game.players[1].coins),(0,0))
                self.assertEqual(game.players[second].board,[TOKEN])
                self.assertEqual((game.units[TOKEN].atk,game.units[TOKEN].hp),(5,5))
                self.assertEqual(game.cards[TOKEN].owner,second)
                self.assertEqual(game.cards[TOKEN].zone,"board")
                self.assertIn(TOKEN,game.ephemeral_ids)
                self.assertNotIn(TOKEN,game.bank)
                self.assertNotIn(TOKEN,game.players[second].hand+game.players[second].deck)
                game.assert_integrity()

    def test_guard_cannot_attack_on_first_own_turn_but_can_on_second(self):
        game=new_match()
        finish_mulligan(game)
        second=1-game.first
        self.assertEqual(game.active,game.first)
        game.end_turn()
        self.assertEqual(game.active,second)
        self.assertEqual(game.players[second].turn_count,1)
        self.assertEqual(game.legal_attacks(TOKEN),[])
        game.end_turn()
        game.end_turn()
        self.assertEqual(game.active,second)
        self.assertIn("hero:"+str(game.first),game.legal_attacks(TOKEN))
        game.assert_integrity()

    def test_guard_permanently_vanishes_when_removed(self):
        game=new_match()
        game._remove_unit(TOKEN,death=True)
        self.assertIn(TOKEN,game.vanished)
        self.assertEqual(game.cards[TOKEN].zone,"vanished")
        self.assertTrue(all(TOKEN not in p.grave+p.deck+p.hand for p in game.players))
        game.assert_integrity()

    def test_guard_saves_and_reloads_during_mulligan_and_after_it(self):
        game=new_match()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"guard.json"
            for finished in (False,True):
                if finished:finish_mulligan(game)
                save_match(game,path)
                loaded=load_match(path)
                self.assertEqual(digest(state_snapshot(loaded)),digest(state_snapshot(game)))
                self.assertEqual(loaded.starting_compensation,"unit_5_5")
                loaded.assert_integrity()

    def test_legacy_plus_three_and_exact_archive_replays(self):
        for comp in ("coins","unit_5_5"):
            with self.subTest(mode=comp):
                game=Match(390079,audit_enabled=True,auctions_enabled=True,
                           auction_catalog="v22",starting_compensation=comp)
                if comp=="coins":
                    self.assertNotIn(TOKEN,game.cards)
                    self.assertEqual(game.players[1-game.first].coins,3)
                    self.assertEqual(game.audit_state_schema,2)
                else:
                    self.assertEqual(game.audit_state_schema,3)
                from tools.simulate_v22 import simulate_one
                completed,_=simulate_one(390079,max_steps=3000,
                                         starting_compensation=comp)
                record=make_report(completed)["payload"]
                self.assertTrue(verify_replay(record,replay_factory))
                self.assertEqual(record["summary"]["ruleset_version"],"v23")

class UserInterfaceAcceptance(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False

    def tearDown(self):
        pygame.quit()

    @staticmethod
    def key(code):
        return pygame.event.Event(pygame.KEYDOWN,{"key":code})

    def start_turn(self):
        # SoloApp.restart has already submitted the AI's hidden mulligan.
        self.app.game.finish_mulligan(0,[])

    def test_new_game_is_guard_mode_and_a_persists_through_restart(self):
        self.assertEqual(self.app.game.starting_compensation,"unit_5_5")
        self.app.handle(self.key(pygame.K_a))
        self.assertFalse(self.app.animations_enabled)
        self.app.restart()
        self.assertFalse(self.app.animations_enabled)
        self.assertEqual(self.app.game.starting_compensation,"unit_5_5")

    def test_restart_cannot_discard_active_match_without_confirmation(self):
        self.start_turn()
        before=digest(state_snapshot(self.app.game))
        self.assertTrue(self.app.handle(self.key(pygame.K_r)))
        self.assertEqual(self.app.confirm_action,"restart")
        self.assertTrue(self.app.handle(self.key(pygame.K_ESCAPE)))
        self.assertIsNone(self.app.confirm_action)
        self.assertEqual(digest(state_snapshot(self.app.game)),before)
        self.app.handle(self.key(pygame.K_r))
        self.app.handle(self.key(pygame.K_d))
        self.assertIsNone(self.app.confirm_action)
        self.assertEqual(self.app.game.phase,"mulligan")

    def test_save_then_exit_and_cancel_instead_of_implicit_quit(self):
        self.start_turn()
        self.assertTrue(self.app.handle(self.key(pygame.K_q)))
        self.assertEqual(self.app.confirm_action,"quit")
        with patch("game.ui.app.save_match") as save:
            self.assertFalse(self.app.handle(self.key(pygame.K_s)))
            save.assert_called_once_with(self.app.game)

    def test_save_error_does_not_close_application(self):
        self.start_turn()
        self.app.handle(self.key(pygame.K_q))
        with patch("game.ui.app.save_match",side_effect=OSError("disk full")):
            self.assertTrue(self.app.handle(self.key(pygame.K_s)))
        self.assertEqual(self.app.confirm_action,"quit")
        self.assertIn("disk full",self.app.confirm_error)

    def test_resize_handled_while_menu_or_history_is_open(self):
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            for screen in ("menu","history"):
                self.app.menu_open=screen=="menu"
                self.app.history_open=screen=="history"
                event=pygame.event.Event(pygame.VIDEORESIZE,{"w":990,"h":700})
                self.assertTrue(self.app.handle(event))
                self.assertEqual(self.app.windowed_size,(990,700))

if __name__=="__main__":
    unittest.main()
