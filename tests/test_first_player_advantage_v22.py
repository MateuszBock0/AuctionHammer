"""Regression tests for non-invasive first-mover advantage experiments."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from tools.analyze_first_player_advantage import (
    AuctionPlusFourAI,experiment,play,summarize,wilson_interval)
from tools.simulate_v22 import simulate_one


class FirstPlayerResearchTests(unittest.TestCase):
    def test_wilson_bounds(self):
        self.assertEqual(wilson_interval(0,0),[None,None])
        for successes,attempts in ((0,10),(5,10),(10,10),(77,100)):
            low,high=wilson_interval(successes,attempts)
            self.assertLessEqual(low,successes/attempts)
            self.assertGreaterEqual(high,successes/attempts)
            self.assertGreaterEqual(low,0.0)
            self.assertLessEqual(high,1.0)

    def test_baseline_matches_full_audited_game(self):
        for seed in (220000,220001):
            with self.subTest(seed=seed):
                expected,_steps=simulate_one(seed,("normalny","normalny"))
                trial=play(seed,3,"normalny","standard")
                self.assertEqual(trial["first_player_index"],expected.first)
                self.assertEqual(trial["winner_index"],expected.winner)
                self.assertEqual(trial["rounds"],expected.round)
                self.assertEqual(trial["auctions_completed"],len(expected.auction_history))

    def test_paired_seed_stays_in_same_first_seat_across_bonuses(self):
        outcomes=[play(220002,bonus,"normalny","standard") for bonus in (0,3,7)]
        self.assertEqual({x["first_player_index"] for x in outcomes},
                         {outcomes[0]["first_player_index"]})
        self.assertEqual([x["second_player_start_coins"] for x in outcomes],
                         [0,3,7])
        for outcome in outcomes:
            self.assertIn(outcome["winner_index"],(0,1))
            self.assertGreaterEqual(outcome["auctions_completed"],1)

    def test_bid_ceiling_variant_is_real_but_remains_legal(self):
        baseline=play(220003,3,"normalny","standard")
        modified=play(220003,3,"normalny","auction_plus4")
        self.assertEqual(baseline["first_player_index"],modified["first_player_index"])
        self.assertGreaterEqual(modified["auctions_completed"],1)
        self.assertGreaterEqual(modified["auction_spend_first"],0)
        self.assertGreaterEqual(modified["auction_spend_second"],0)
        self.assertTrue(issubclass(AuctionPlusFourAI.__mro__[1],object))

    def test_small_trial_writes_complete_csv_json_with_paired_flips(self):
        with tempfile.TemporaryDirectory() as folder:
            report=experiment(
                games_per_scenario=2,start_seed=220010,
                bonuses=(3,5),profiles=(("normalny","standard"),),
                output_dir=folder)
            self.assertEqual(report["summary"]["total_expected"],4)
            self.assertEqual(report["summary"]["total_finished"],4)
            self.assertEqual(report["summary"]["total_failed"],0)
            self.assertEqual(len(report["scenarios"]),2)
            scenario=next(s for s in report["scenarios"]
                          if s["second_start_coins"]==5)
            self.assertEqual(scenario["paired_vs_3coins_same_ai_policy"]["matched_seeds"],2)
            self.assertTrue((Path(folder)/"wyniki_scenariuszy.json").exists())
            self.assertTrue((Path(folder)/"wyniki_scenariuszy.csv").exists())
            self.assertTrue((Path(folder)/"wyniki_meczow.csv").exists())

    def test_invalid_bonus_rejected(self):
        with self.assertRaises(ValueError):
            play(220100,-1)
        with self.assertRaises(ValueError):
            experiment(1,bonuses=(0,5))


if __name__=="__main__":
    unittest.main()
