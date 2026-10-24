"""0.9.75 — audited endgame stats, legacy fallback, and existing menu actions."""
import copy
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.core.audit import state_snapshot, digest
from game.ui.match_summary import build_match_summary
from game.ui.app import SoloApp


def fake_game(complete=True):
    names={"u1":"Rycerz","u2":"Alchemik","a1":"Karta aukcyjna"}
    cards={uid:SimpleNamespace(definition=SimpleNamespace(name=name),
                               owner=0,ability_level=2)
           for uid,name in names.items()}
    cards["u2"].ability_level=1
    cards["a1"].ability_level=3
    units={"u1":SimpleNamespace(atk=8,max_hp=13)}
    players=[SimpleNamespace(name="GRACZ",hp=57,coins=7),
             SimpleNamespace(name="KOMPUTER",hp=-1,coins=11)]
    actions=[
        {"operation":"play","result":"ok","command_owner":0,
         "changes":{"units":{"u1":{"before":None,
                                    "after":{"current_attack":11,
                                             "current_max_hp":12}}},
                    "cards":{"u1":{"before":{"owner":0,"ability_level":0},
                                   "after":{"owner":0,"ability_level":2}}}}},
        {"operation":"attack","result":"ok","command_owner":0,"changes":{}},
        {"operation":"attack","result":"error","command_owner":0,"changes":{}},
        {"operation":"play","result":"ok","command_owner":1,"changes":{}},
        {"operation":"attack","result":"ok","command_owner":1,"changes":{}},
        {"operation":"end_turn","result":"ok","command_owner":0,
         "changes":{"cards":{"u2":{"before":{"owner":0,"ability_level":0},
                                   "after":{"owner":0,"ability_level":1}},
                             "a1":{"before":{"owner":0,"ability_level":0},
                                   "after":{"owner":0,"ability_level":3}}}}},
    ]
    internal=[
        {"operation":"_damage","args":["hero:1",10],
         "before":{"hero:1":{"hp":18}},
         "after":{"hero:1":{"hp":10}}},
        {"operation":"_damage","args":["u1",5],
         "before":{"u1":{"hp":8}},"after":{"u1":{"hp":6}}},
        {"operation":"_heal","args":["u1",8],
         "before":{"u1":{"hp":6}},"after":{"u1":{"hp":9}}},
        {"operation":"_damage","args":["u1",30],
         "before":{"u1":{"hp":6}},"after":{"u1":None}},
    ]
    return SimpleNamespace(
        phase="finished",round=11,winner=0,
        players=players,death_counts=[4,6],death_counts_complete=True,
        audit_complete=complete,audit_initial={
            "units":{"u2":{"current_attack":9,"current_max_hp":5}},
            "cards":{"u1":{"owner":0,"ability_level":0},
                     "u2":{"owner":0,"ability_level":0}}},
        audit_actions=actions,audit_internal=internal,
        auction_awards={"a1":{"rarity":"podstawowa"}},
        cards=cards,units=units,event_journal=[],
    )


class MatchSummaryPure0975(unittest.TestCase):
    def test_real_signed_stats_exclude_errors_and_opponent_actions(self):
        game=fake_game()
        snapshot=copy.deepcopy(game)
        stats=build_match_summary(game)
        self.assertTrue(stats.complete)
        self.assertEqual((stats.rounds,stats.hero_hp,stats.coins),
                         (11,(57,0),(7,11)))
        self.assertEqual(stats.deaths,(4,6))
        self.assertEqual((stats.plays,stats.attacks,stats.levelled_cards),(1,1,2))
        self.assertEqual(stats.strongest.name,"Rycerz")
        self.assertEqual((stats.strongest.attack,stats.strongest.max_hp,
                          stats.strongest.power),(11,12,23))
        self.assertEqual((stats.largest_damage.hp_lost,
                          stats.largest_damage.target_name),(8,"KOMPUTER"))
        self.assertEqual((stats.leader.name,stats.leader.level),("Rycerz",2))
        self.assertEqual(game,snapshot)

    def test_incomplete_legacy_audit_never_fabricates_achievements(self):
        game=fake_game(complete=False)
        game.death_counts_complete=False
        stats=build_match_summary(game)
        self.assertFalse(stats.complete)
        self.assertIsNone(stats.plays)
        self.assertIsNone(stats.attacks)
        self.assertIsNone(stats.levelled_cards)
        self.assertIsNone(stats.strongest)
        self.assertIsNone(stats.largest_damage)
        self.assertIsNone(stats.leader)
        self.assertIsNone(stats.deaths)
        self.assertEqual(stats.rounds,11)

    def test_missing_signed_log_is_not_mistaken_for_zero(self):
        game=fake_game()
        del game.audit_internal
        stats=build_match_summary(game)
        self.assertFalse(stats.complete)
        self.assertIsNone(stats.plays)

    def test_largest_damage_requires_observed_hp_difference(self):
        game=fake_game()
        game.audit_internal=[
            {"operation":"_damage","args":["hero:1",999],
             "before":{"hero:1":{"hp":44}},
             "after":{"hero:1":{"hp":41}}},
            {"operation":"_damage","args":["u1",777],
             "before":{"u1":{"hp":7}},
             "after":{"u1":None}}
        ]
        stats=build_match_summary(game)
        self.assertEqual(stats.largest_damage.hp_lost,3)
        self.assertEqual(stats.largest_damage.target,"hero:1")

    def test_not_finished_raises(self):
        game=fake_game()
        game.phase="turn"
        with self.assertRaises(ValueError):
            build_match_summary(game)


class MatchSummaryUI0975(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self.app.tutorial_welcome_open=False

    def tearDown(self):
        pygame.quit()

    def test_end_screen_renders_cached_stats_and_preserves_buttons(self):
        app=self.app
        app.game.phase="finished"
        app.game.winner=0
        game=app.game
        before=digest(state_snapshot(game))
        with patch.object(app,"_button",wraps=app._button) as button:
            app._draw_gameover()
        self.assertEqual(digest(state_snapshot(game)),before)
        self.assertIs(app._match_summary_game,game)
        first=app._finished_summary()
        self.assertIs(app._finished_summary(),first)
        rects=[call.args[0] for call in button.call_args_list]
        self.assertIn(pygame.Rect(608,637,260,52),rects)
        self.assertIn(pygame.Rect(885,637,239,52),rects)
        self.assertIn(pygame.Rect(392,702,325,46),rects)
        self.assertIn(pygame.Rect(738,702,325,46),rects)

    def test_replay_or_new_game_does_not_inherit_previous_summary(self):
        app=self.app
        app.game.phase="finished"
        app.game.winner=1
        old=app._finished_summary()
        app.restart()
        self.assertIsNone(app._finished_summary())
        app.game.phase="finished"
        app.game.winner=0
        self.assertIsNot(app._finished_summary(),old)

    def test_incomplete_match_displays_no_fake_achievements(self):
        app=self.app
        app.game.phase="finished"
        app.game.winner=1
        app.game.audit_complete=False
        with patch.object(app,"_text",wraps=app._text) as txt:
            app._draw_gameover()
        displayed=[c.args[0] for c in txt.call_args_list]
        self.assertTrue(any("NIEPEŁNY AUDYT" in x for x in displayed))
        self.assertTrue(any("Brak danych" in x for x in displayed))


if __name__=="__main__":
    unittest.main()
