"""Static validation for the documented (inactive) v4 auction draft."""
import json
from pathlib import Path
import unittest


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "auction" / "KATALOG_AUKCYJNY_12_v4.json"


class AuctionV4DraftDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.rules = cls.data["auction_rules"]
        cls.cards = cls.data["cards"]

    def test_twelve_distinct_archetypes_and_all_three_variants(self):
        self.assertEqual(len(self.cards), 12)
        self.assertEqual(len({c["id"] for c in self.cards}), 12)
        self.assertEqual({c["id"] for c in self.cards}, {f"A{i:03}" for i in range(1, 13)})
        for card in self.cards:
            self.assertEqual(set(card["variants"]), {"basic", "rare", "legendary"})
            self.assertTrue(all(card["variants"].values()))
        self.assertEqual(self.data["count_effect_variants"], 36)

    def test_auction_awards_two_cards_not_three_plays(self):
        r = self.rules
        self.assertEqual(r["three_offers_per_auction"], 3)
        self.assertTrue(r["two_cards_awarded_per_auction"])
        self.assertTrue(r["each_player_wins_max_one_card_per_auction"])
        self.assertTrue(r["third_offer_returns_to_auction_pool"])
        self.assertTrue(r["offers_are_not_played_or_summoned"])
        self.assertTrue(r["auction_cards_are_added_to_private_hands"])
        self.assertEqual(r["card_play_limit_per_turn"], 1)
        self.assertEqual(r["board_limit"], 5)

    def test_acquisition_scaling_and_stat_freeze(self):
        self.assertEqual(self.rules["independent_rarity_probabilities"],
                         {"basic": 0.6, "rare": 0.3, "legendary": 0.1})
        for card in self.cards:
            atk3 = card["stats_at_round_3_example"]["atk"]
            hp3 = card["stats_at_round_3_example"]["hp"]
            self.assertEqual(atk3 + hp3, 11)
            for rnd in (3, 6, 9, 12, 60, 120):
                atk = atk3 + (rnd - 3) // 3
                hp = rnd + 8 - atk
                self.assertEqual(atk + hp, rnd + 8)
                self.assertEqual(atk - atk3, (rnd - 3) // 3)
                self.assertEqual(hp - hp3, 2 * ((rnd - 3) // 3))
            self.assertTrue(card["stats_at_acquisition"]["no_changes_after_acquisition"])
        self.assertTrue(self.rules["freeze_stats_at_acquisition"])
        self.assertTrue(self.rules["no_hand_scaling"])

    def test_five_specific_stat_adjustments(self):
        expected = {"A002": (3, 8), "A005": (2, 9), "A007": (2, 9),
                    "A010": (4, 7), "A012": (3, 8)}
        current = {c["id"]: (c["stats_at_round_3_example"]["atk"],
                             c["stats_at_round_3_example"]["hp"]) for c in self.cards}
        for cid, values in expected.items():
            self.assertEqual(current[cid], values)
        self.assertEqual({item["id"] for item in self.data["stat_balance_changes"]}, set(expected))

    def test_status_remains_documentation_only(self):
        self.assertEqual(self.rules["status"], "PROPOSED_DRAFT_NOT_APPROVED")
        self.assertEqual(self.rules["auction_ability_activation_costs"], "not_set_in_this_draft")
        self.assertFalse(self.rules["no_auction_engine_implemented_in_repo"])
        self.assertTrue(self.rules["evolution_does_not_retrigger_on_play_effect"])


if __name__ == "__main__":
    unittest.main()
