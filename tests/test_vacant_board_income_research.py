"""Non-production slot-income rule acceptance checks."""
import unittest
import tempfile
from pathlib import Path
from game.core.engine import Match
from tools.research_vacant_board_income import (VacantBoardIncomeMatch,
                                                 vacant_slot_bonus,duel,study)


class SlotIncomeResearch(unittest.TestCase):
    def test_exact_table_for_0_to_5_units(self):
        self.assertEqual([vacant_slot_bonus(i) for i in range(6)],
                         [5,4,3,2,1,0])
        with self.assertRaises(ValueError):
            vacant_slot_bonus(6)

    def test_standard_match_is_unchanged(self):
        ref=Match(220000,auctions_enabled=True,auction_catalog="v22")
        modified=VacantBoardIncomeMatch(220000,auctions_enabled=True,
                                        auction_catalog="v22")
        self.assertEqual(ref.first,modified.first)
        self.assertEqual(ref.players[1-ref.first].coins,3)
        self.assertEqual(modified.players[1-modified.first].coins,3)
        self.assertEqual(ref.players[ref.first].coins,0)

    def test_on_turn_end_without_units_grants_five(self):
        g=VacantBoardIncomeMatch(220001,auctions_enabled=True,auction_catalog="v22")
        g.finish_mulligan(0,[]);g.finish_mulligan(1,[])
        actor=g.active
        self.assertEqual(len(g.players[actor].board),0)
        previous=g.players[actor].coins
        g.end_turn()
        self.assertEqual(g.players[actor].coins,previous+5)
        self.assertEqual(g.slot_income[actor],5)
        g.assert_integrity()

    def test_match_completes_on_same_seed(self):
        a=duel(220002,extra_income=False)
        b=duel(220002,extra_income=True)
        self.assertEqual(a["first"],b["first"])
        self.assertEqual(a["slot_income_first"],0)
        self.assertEqual(a["slot_income_second"],0)
        self.assertGreater(b["slot_income_first"]+b["slot_income_second"],0)

    def test_reports_paired_seeds_and_returns_results(self):
        with tempfile.TemporaryDirectory() as temp:
            report=study(seeds=2,start_seed=220005,levels=("normalny",),
                         output_dir=temp)
            self.assertEqual(report["finished"],4)
            self.assertEqual(report["failed"],0)
            self.assertEqual(len(report["comparisons"]),2)
            self.assertTrue(all(x["matched_seeds"]==2 for x in report["comparisons"]))
            self.assertTrue((Path(temp)/"summary.json").is_file())
            self.assertTrue((Path(temp)/"scenarios.csv").is_file())
            self.assertTrue((Path(temp)/"matches.csv").is_file())


if __name__=="__main__":
    unittest.main()
