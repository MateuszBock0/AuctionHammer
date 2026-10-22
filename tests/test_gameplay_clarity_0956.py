"""0.9.56 Gameplay Clarity: tested source-of-truth presentation only."""
from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from game.core.audit import digest, state_snapshot
from game.ui.app import SoloApp
from game.ui.combat_outcome import committed_attack_outcome
from game.ui.decision_clarity import economy_cue, positional_cues
from test_engine import setup_game, force_unit


class DecisionClarityTests(unittest.TestCase):
    def test_income_is_only_a_current_estimate_and_does_not_touch_match(self):
        game = setup_game(956100)
        game.vacant_income_enabled = True
        initial = digest(state_snapshot(game))
        self.assertEqual(economy_cue(game).vacant_income, 5)
        force_unit(game, "S34", 0, slot=2)
        self.assertEqual(economy_cue(game).vacant_income, 4)
        game.active = 1
        self.assertIsNone(economy_cue(game).vacant_income)
        self.assertNotEqual(digest(state_snapshot(game)), initial)

    def test_rounds_until_next_eligible_auction_or_no_bag(self):
        game = setup_game(956101)
        game.auctions_enabled = True
        game.auction_catalog = "v22"
        game.auction_bag = ["one", "two", "three"]
        for round_number, expected in ((1, 3), (2, 2), (3, 1), (4, 3)):
            game.round = round_number
            self.assertEqual(economy_cue(game).rounds_to_auction, expected)
        game.auction_bag = ["one", "two"]
        self.assertIsNone(economy_cue(game).rounds_to_auction)
        game.auctions_enabled = False
        self.assertIsNone(economy_cue(game).rounds_to_auction)

    def test_s34_real_neighbour_priority_and_enemy_mode(self):
        game = setup_game(956102)
        source = force_unit(game, "S34", 0, slot=2)
        left = force_unit(game, "S01", 0, slot=1)
        right = force_unit(game, "S02", 0, slot=3)
        enemy = force_unit(game, "S09", 1, slot=2)
        source.aura_mode = "ally"
        game._update_auras()
        before = digest(state_snapshot(game))
        cue = positional_cues(game, "S34")
        self.assertEqual(len(cue), 1)
        self.assertEqual((cue[0].uid, cue[0].owner, cue[0].slot),
                         ("S02", 0, 3))
        self.assertEqual(cue[0].label, "AURA +ATK")
        source.aura_mode = "enemy"
        game._update_auras()
        self.assertEqual(positional_cues(game, "S34")[0].uid, "S09")
        self.assertEqual(positional_cues(game, "S34")[0].label, "AURA -ATK")
        self.assertFalse(positional_cues(game, "S01"))
        self.assertNotEqual(digest(state_snapshot(game)), before)

    def test_s108_marks_opposing_lane_even_when_empty_not_guaranteed_stun(self):
        game = setup_game(956103)
        force_unit(game, "S108", 0, slot=4)
        before = digest(state_snapshot(game))
        cue = positional_cues(game, "S108")
        self.assertEqual(len(cue), 1)
        self.assertEqual((cue[0].owner, cue[0].slot, cue[0].uid),
                         (1, 4, None))
        self.assertIn("REAKCJA", cue[0].label)
        self.assertEqual(digest(state_snapshot(game)), before)
        game.fixed_board_slots = False
        self.assertFalse(positional_cues(game, "S108"))

    def test_attack_summary_includes_actual_armor_and_status_delta(self):
        game = SimpleNamespace(players=[], cards={
            "a": SimpleNamespace(definition=SimpleNamespace(name="Rycerz")),
            "b": SimpleNamespace(definition=SimpleNamespace(name="Strażnik")),
        })
        prior = {
            "a": {"hp": 9, "shield": 0, "armor": 0, "status": ()},
            "b": {"hp": 8, "shield": 1, "armor": 3, "status": ()},
        }
        current = {
            "a": {"hp": 9, "shield": 0, "armor": 0, "status": ()},
            "b": {"hp": 5, "shield": 0, "armor": 1,
                  "status": ("poison",)},
        }
        result = committed_attack_outcome(
            game, prior, current, [{"text": "Rycerz atakuje: Strażnik."}], 1)
        self.assertEqual(result.attacker, "Rycerz")
        self.assertEqual(result.target, "Strażnik")
        detail = result.details[0]
        for fragment in ("PŻ 8→5", "tarcza 1→0", "pancerz 3→1",
                         "nowe efekty: poison"):
            self.assertIn(fragment, detail)
        self.assertNotIn("ZGON", detail)


class DrawReadOnlyTests(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp, "_desktop_resolution",
                          return_value=(1536, 864)):
            self.app = SoloApp(start_in_menu=True)
        self.app.menu_open = False
        if self.app._bonus_selection_due():
            self.app._choose_bonus("coins")

    def tearDown(self):
        pygame.quit()

    def test_hover_over_ticker_exposes_large_complete_report_without_action(self):
        app = self.app
        game = app.game
        app.attack_outcome_latest = SimpleNamespace(
            attacker="Rycerz", target="Strażnik",
            lines=("Strażnik: PŻ 8→5",),
            details=("Strażnik: PŻ 8→5, tarcza 1→0, pancerz 3→1",))
        before = digest(state_snapshot(game))
        captured = []
        original = app._text
        def observe(*args, **kwargs):
            captured.append(str(args[0]))
            return original(*args, **kwargs)
        with patch.object(app, "mouse_pos", return_value=(1200, 925)):
            with patch.object(app, "_text", side_effect=observe):
                app._draw_hover_guidance()
        self.assertTrue(any("PEŁNE SKUTKI" in s for s in captured))
        self.assertTrue(any("pancerz" in s for s in captured))
        self.assertEqual(digest(state_snapshot(game)), before)

    def test_positional_highlight_uses_real_selected_source_and_preserves_match(self):
        app = self.app
        app.game.phase = "turn"
        app.game.active = 0
        force_unit(app.game, "S108", 0, slot=0)
        app.selected = "S108"
        before = digest(state_snapshot(app.game))
        with patch("game.ui.app.pygame.draw.rect",
                   wraps=pygame.draw.rect) as rectangles:
            app._draw_positional_cues()
        self.assertTrue(any(len(call.args)>=4 and call.args[3]==3
                            for call in rectangles.call_args_list))
        self.assertEqual(digest(state_snapshot(app.game)), before)


if __name__ == "__main__":
    unittest.main()
