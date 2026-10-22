"""Regression: hand exchange must not make ready attackers appear locked."""
from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.core.auction_abilities import _swap_hands
from game.ui.app import SoloApp
from test_engine import setup_game, force_unit


def minimal_app(game, selected):
    """Exercise actual click handling without opening a Pygame window."""
    app = SoloApp.__new__(SoloApp)
    app.game = game
    app.selected = selected
    app.details_card = None
    app.sidebar_card = None
    app.last_error = ""
    app.scroll = 0
    app.tooltip_open = False
    app.choice_page = 0
    return app


class AttackSelectionAfterSwapTests(unittest.TestCase):
    def test_swapped_hands_do_not_block_other_ready_attackers(self):
        game = setup_game(95701)
        first = force_unit(game, "S31", 0, slot=0)
        second = force_unit(game, "S32", 0, slot=1)
        previous_hands = tuple(tuple(p.hand) for p in game.players)
        _swap_hands(game)  # A009 legendary swap_all implementation
        self.assertEqual(tuple(game.players[0].hand), previous_hands[1])
        self.assertEqual(tuple(game.players[1].hand), previous_hands[0])
        self.assertIn("hero:1", game.legal_attacks("S31"))
        self.assertIn("hero:1", game.legal_attacks("S32"))

        app = minimal_app(game, "S31")
        enemy_hero = app.hero_rect(1).center
        app.click(enemy_hero)
        self.assertEqual(first.attacks, 1)
        self.assertIsNone(app.selected, "An exhausted attacker must not stay selected.")
        self.assertIn("hero:1", game.legal_attacks("S32"))

        app.click(app.slot_rect(0, 1).center)
        self.assertEqual(app.selected, "S32")
        app.click(enemy_hero)
        self.assertEqual(second.attacks, 1)
        self.assertIsNone(app.selected)
        self.assertEqual(app.last_error, "")

    def test_double_attacker_stays_selected_until_second_attack(self):
        game = setup_game(95702)
        unit = force_unit(game, "S115", 0, slot=0)
        app = minimal_app(game, "S115")
        enemy_hero = app.hero_rect(1).center
        self.assertIn("hero:1", game.legal_attacks("S115"))

        app.click(enemy_hero)
        self.assertEqual(unit.attacks, 1)
        self.assertEqual(app.selected, "S115")
        self.assertIn("hero:1", game.legal_attacks("S115"))

        app.click(enemy_hero)
        self.assertEqual(unit.attacks, 2)
        self.assertIsNone(app.selected)

    def test_selection_clears_after_pending_attack_choice_resolves(self):
        game = setup_game(95703)
        unit = force_unit(game, "S68", 0, slot=0)
        app = minimal_app(game, "S68")
        app.click(app.hero_rect(1).center)
        self.assertEqual(unit.attacks, 1)
        self.assertIsNotNone(game.pending)
        self.assertEqual(app.selected, "S68",
                         "Selection must persist while the ability is pending.")
        app._choose(0)
        self.assertIsNone(game.pending)
        self.assertIsNone(app.selected)
        self.assertEqual(app.last_error, "")


if __name__ == "__main__":
    unittest.main()
