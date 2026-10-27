"""Presentation-only readability regression for shortened current card descriptions.

Historical rulesets and canonical gameplay definitions must stay unchanged.
"""
from __future__ import annotations

import unittest

from game.core.auction_catalog import live_variant
from game.ui.auction_copy import full_preview_auction_copy, preview_auction_copy
from game.ui.v23_help import v23_base_card_note

ORIGINAL_BASE_LENGTHS = {
    "S95": 402, "S32": 309, "S87": 252, "S108": 270, "S99": 244,
}
ORIGINAL_AUCTION_LENGTHS = {
    ("A003", "rzadka"): 356, ("A003", "legendarna"): 386,
    ("A014", "rzadka"): 318, ("A014", "legendarna"): 231,
    ("A016", "rzadka"): 297, ("A016", "legendarna"): 285,
    ("A018", "legendarna"): 293,
    ("A009", "legendarna"): 292, ("A009", "rzadka"): 235,
    ("A012", "rzadka"): 276, ("A004", "legendarna"): 268,
    ("A002", "rzadka"): 245, ("A002", "legendarna"): 256,
    ("A015", "podstawowa"): 236, ("A015", "rzadka"): 237,
    ("A015", "legendarna"): 254,
}
TIERS = {"podstawowa": "basic", "rzadka": "rare", "legendarna": "legendary"}


class ShortenedCardCopy(unittest.TestCase):
    def test_conditional_base_explanations_are_shorter_and_v23_only(self):
        mandatory = {
            "S95": ("1 + poziom", "2 zwykłe obrażenia", "zapamiętanego celu"),
            "S32": ("1 obrażenie przez 2", "2 zwykłe obrażenia", "po lewej"),
            "S87": ("2 trwałego pancerza", "za poziom", "4 PŻ"),
            "S108": ("po raz pierwszy", "1 bazowe + poziom", "ponownie"),
            "S99": ("1 tymczasowego pancerza", "+poziom trwałego", "truciznę"),
        }
        for card_id, old_length in ORIGINAL_BASE_LENGTHS.items():
            with self.subTest(card=card_id):
                new = v23_base_card_note(card_id, "v23")
                self.assertGreater(len(new), 100)
                self.assertLess(len(new), old_length)
                self.assertEqual(v23_base_card_note(card_id, "v22"), "")
                for fragment in mandatory[card_id]:
                    self.assertIn(fragment, new)

    def test_auction_full_and_quick_previews_preserve_ruleset(self):
        for (card_id, tier), old_length in ORIGINAL_AUCTION_LENGTHS.items():
            with self.subTest(card=card_id, tier=tier):
                original = live_variant("v22", card_id, tier)
                displayed = full_preview_auction_copy(card_id, tier, "v23", original)
                self.assertTrue(displayed)
                self.assertLess(len(displayed), old_length)
                self.assertNotIn("[v23:", displayed)
                self.assertEqual(full_preview_auction_copy(
                    card_id, tier, "v22", original), original)
                short = preview_auction_copy(card_id, tier, "v23", original)
                self.assertLess(len(short), len(displayed))
                self.assertEqual(preview_auction_copy(
                    card_id, tier, "v22", original), original)
                self.assertEqual(live_variant("v22", card_id, tier), original)

    def test_important_auction_conditions_survive(self):
        requirements = {
            ("A003", "rzadka"): ("1 PŻ", "brak pola", "Szkieleta", "7/7"),
            ("A003", "legendarna"): ("2 różnych", "pełnym PŻ", "obie", "8/8"),
            ("A014", "rzadka"): ("nominalnego", "zaokrąglona w górę",
                                 "Tarcza i pancerz", "regenerację 2 PŻ"),
            ("A014", "legendarna"): ("nominalne", "pełnym PŻ", "2 PŻ",
                                      "Porcje się kumulują"),
            ("A016", "rzadka"): ("Najpierw dobierz", "Potem zagraj",
                                 "pełnej planszy", "połowę"),
            ("A016", "legendarna"): ("przejmij", "pełnej planszy", "pełne"),
            ("A018", "legendarna"): ("0 monet", "+5 ATK", "+5 MAX PŻ",
                                      "+5 bieżących PŻ"),
            ("A009", "legendarna"): ("własnością kart", "2 karty", "+3 ATK"),
            ("A012", "rzadka"): ("ALBO", "drugi bohater bez zmian", "10 PŻ"),
            ("A015", "legendarna"): ("tylko wrogie", "Przy śmierci",
                                      "własnych zdolności"),
        }
        for (card_id, tier), fragments in requirements.items():
            raw = live_variant("v22", card_id, tier)
            text = full_preview_auction_copy(card_id, tier, "v23", raw)
            for fragment in fragments:
                with self.subTest(card=card_id, tier=tier, phrase=fragment):
                    self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
