"""0.9.55: immediate, read-only combat feedback and responsive attack targets."""
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
from game.ui.combat_outcome import AttackOutcome, committed_attack_outcome
from game.ui.combat_visuals import CombatVisuals
from game.ui.gameplay_clarity import combat_notice
from test_engine import force_unit, setup_game


class CombatOutcomeTests(unittest.TestCase):
    @staticmethod
    def slot(owner, index):
        return pygame.Rect(110 + 176*index, 431 if owner == 0 else 152, 148, 220)

    @staticmethod
    def hero(owner):
        return pygame.Rect(110, 662 if owner == 0 else 98, 935, 44)

    def test_real_attack_reports_committed_hp_without_modifying_game(self):
        game = setup_game(955101)
        attacker = force_unit(game, "S09", 0)
        defender = force_unit(game, "S01", 1)
        attacker.played_turn = 0
        defender.base_max_hp = 35
        defender.hp = 35
        visuals = CombatVisuals()
        visuals.sync(game, self.slot, self.hero, 0)
        game.attack("S09", "S01")
        after_attack = digest(state_snapshot(game))
        visuals.sync(game, self.slot, self.hero, 100)
        outcome = visuals.last_attack_outcome
        self.assertIsNotNone(outcome)
        self.assertTrue(any("PŻ" in line and "→" in line for line in outcome.lines))
        self.assertEqual(digest(state_snapshot(game)), after_attack)
        visuals.sync(game, self.slot, self.hero, 120)
        self.assertIsNone(visuals.last_attack_outcome)

    def test_attack_waits_for_real_s68_ability_choice_before_reporting(self):
        game = setup_game(955102)
        attacker = force_unit(game, "S68", 0)
        force_unit(game, "S01", 1)
        attacker.played_turn = 0
        visuals = CombatVisuals()
        visuals.sync(game, self.slot, self.hero, 0)
        game.attack("S68", "S01")
        self.assertIsNotNone(game.pending)
        self.assertIsNotNone(game.deferred_attack)
        before = digest(state_snapshot(game))
        visuals.sync(game, self.slot, self.hero, 100)
        self.assertIsNone(visuals.last_attack_outcome)
        self.assertEqual(digest(state_snapshot(game)), before)
        self.assertFalse(any(pulse.kind == "attack" for pulse in visuals.pulses))
        game.choose(0)
        self.assertIsNone(game.pending)
        self.assertIsNone(game.deferred_attack)
        after = digest(state_snapshot(game))
        visuals.sync(game, self.slot, self.hero, 200)
        self.assertIsNotNone(visuals.last_attack_outcome)
        self.assertTrue(any("PŻ" in line for line in visuals.last_attack_outcome.lines))
        self.assertTrue(any(pulse.kind == "attack" for pulse in visuals.pulses))
        self.assertEqual(digest(state_snapshot(game)), after)

    def test_shield_absorbs_attack_without_fake_hp_damage(self):
        game = SimpleNamespace(
            players=[SimpleNamespace(name="Gracz"), SimpleNamespace(name="Komputer")],
            cards={
                "a": SimpleNamespace(definition=SimpleNamespace(name="Rycerz")),
                "b": SimpleNamespace(definition=SimpleNamespace(name="Wilk")),
            },
        )
        prior = {
            "a": {"hp": 8, "shield": 0},
            "b": {"hp": 5, "shield": 1},
        }
        current = {
            "a": {"hp": 8, "shield": 0},
            "b": {"hp": 5, "shield": 0},
        }
        out = committed_attack_outcome(game, prior, current,
                                       [{"text": "Rycerz atakuje: Wilk."}], 1)
        self.assertEqual(out.lines, ("Wilk: tarcza 1→0",))
        self.assertNotIn("PŻ", out.lines[0])

    def test_removal_without_engine_death_does_not_show_zgon(self):
        game = SimpleNamespace(
            players=[SimpleNamespace(name="Gracz"), SimpleNamespace(name="AI")],
            cards={"b": SimpleNamespace(definition=SimpleNamespace(name="Wilk"))},
        )
        old = {"b": {"hp": 3, "shield": 0}}
        outcome = committed_attack_outcome(game, old, {},
                                           [{"text": "Bohater atakuje: Wilk."}], 5)
        self.assertIsNotNone(outcome)
        self.assertNotIn("ZGON", " ".join(outcome.lines))

    def test_future_impact_effect_is_not_dropped_before_it_starts(self):
        pygame.init()
        try:
            visuals = CombatVisuals()
            visuals._push("damage", (80, 80), 100, "-3", delay_ms=165)
            screen = pygame.Surface((300, 300), pygame.SRCALPHA)
            font = pygame.font.Font(None, 18)
            visuals.draw(screen, 100, font)
            self.assertEqual(len(visuals.pulses), 1)
            self.assertEqual(visuals.pulses[0].born, 265)
            visuals.draw(screen, 265, font)
            self.assertEqual(len(visuals.pulses), 1)
        finally:
            pygame.quit()


class ResponsiveCanvasTests(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp, "_desktop_resolution", return_value=(1536, 864)):
            self.app = SoloApp(start_in_menu=True)
        self.app.menu_open = False
        if self.app._bonus_selection_due():
            self.app._choose_bonus("coins")

    def tearDown(self):
        pygame.quit()

    def test_new_attack_supersedes_stale_ticker_and_keeps_history(self):
        app = self.app
        app.combat_notice_active = (0, combat_notice("Wilk zadaje 5 obrażeń."))
        app.combat_notice_queue = [combat_notice("Zgon Wilka.")]
        original_count = len(app.game.event_journal)
        app.game.event_journal.append(
            {"text": "Strażnik atakuje: Wilk.",
             "seq": 999, "round": 1, "active": 0})
        outcome = AttackOutcome(original_count + 1, ("Wilk: PŻ 5→2",))
        app.combat_visuals.last_attack_outcome = outcome
        with patch("game.ui.app.pygame.time.get_ticks", return_value=1000):
            app._capture_visual_feedback()
            with patch.object(app, "_text", wraps=app._text) as spy:
                app._draw_log()
        self.assertIsNotNone(app.attack_outcome_active)
        self.assertIsNone(app.combat_notice_active)
        self.assertEqual(app.combat_notice_queue, [])
        self.assertEqual(len(app.game.event_journal), original_count + 1)
        labels = [str(call.args[0]) for call in spy.call_args_list]
        self.assertTrue(any("SKUTKI ATAKU" in label for label in labels))
        self.assertTrue(any("Wilk: PŻ 5→2" in label for label in labels))
        with patch("game.ui.app.pygame.time.get_ticks", return_value=3400):
            app._capture_visual_feedback()
        self.assertIsNone(app.attack_outcome_active)

    def test_attack_finishes_without_new_journal_line_and_still_reports(self):
        app = self.app
        original_count = len(app.game.event_journal)
        app._last_logged_event = original_count
        outcome = AttackOutcome(original_count, ("Wilk: PŻ 4→1",))
        app.combat_visuals.last_attack_outcome = outcome
        with patch("game.ui.app.pygame.time.get_ticks", return_value=1500):
            app._capture_visual_feedback()
        self.assertIsNotNone(app.attack_outcome_active)
        self.assertIs(app.attack_outcome_active[1], outcome)
        self.assertEqual(len(app.game.event_journal), original_count)
        # Re-reading the same outcome may not restart the duration.
        with patch("game.ui.app.pygame.time.get_ticks", return_value=1600):
            app._capture_visual_feedback()
        self.assertEqual(app.attack_outcome_active[0], 1500)

    def test_hovered_legal_attack_target_is_more_distinct(self):
        app = self.app
        target = pygame.Rect(300, 152, 148, 220)
        old = digest(state_snapshot(app.game))
        with patch.object(app, "_attack_target_rects", return_value=[target]):
            with patch.object(app, "mouse_pos", return_value=target.center):
                with patch("game.ui.app.pygame.draw.rect",
                           wraps=pygame.draw.rect) as draws:
                    app._draw_attack_targets()
        self.assertTrue(any(len(call.args) >= 4 and call.args[3] == 4
                            for call in draws.call_args_list))
        self.assertEqual(digest(state_snapshot(app.game)), old)

    def test_ai_action_interval_is_shorter_but_still_readable(self):
        self.assertGreaterEqual(SoloApp.AI_ACTION_DELAY_MS, 350)
        self.assertLessEqual(SoloApp.AI_ACTION_DELAY_MS, 500)


if __name__ == "__main__":
    unittest.main()
