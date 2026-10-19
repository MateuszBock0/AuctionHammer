"""Smoke tests for reproducible v22 AI tournament and archived audit evidence."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from game.core.audit import archive_path,list_archived_matches,read_report
from tools.simulate_v22 import (choose_actor,simulate_one,tournament)
from game.core.engine import Match


class V22TournamentAcceptance(unittest.TestCase):
    def test_actor_selection_is_defined_for_mulligan_and_real_game(self):
        game=Match(230100,audit_enabled=True,
                   auctions_enabled=True,auction_catalog="v22")
        self.assertEqual(choose_actor(game),0)
        game.finish_mulligan(0,[])
        self.assertEqual(choose_actor(game),1)
        game.finish_mulligan(1,[])
        self.assertEqual(choose_actor(game),game.active)

    def test_audited_v22_complete_game_includes_every_command(self):
        game,steps=simulate_one(230101,max_steps=3000)
        self.assertEqual(game.phase,"finished")
        self.assertGreater(steps,10)
        self.assertTrue(game.auctions_enabled)
        self.assertEqual(game.auction_catalog,"v22")
        self.assertTrue(game.audit_complete)
        self.assertTrue(game.audit_actions)
        self.assertTrue(all(item["error"] is None for item in game.audit_actions))
        game.assert_integrity()

    def test_tournament_archives_two_real_games_and_verifies_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            result=tournament(games=2,start_seed=230102,
                              output_dir=path,verify_every=1)
            summary=result["summary"]
            self.assertEqual((summary["finished"],summary["failed"]),(2,0))
            self.assertEqual(summary["audit_replays_verified"],2)
            self.assertEqual(len(result["matches"]),2)
            entries=list_archived_matches(archive_path(path/"AuctionHammer-OSTATNI-MECZ.json"))
            self.assertEqual(len(entries),2)
            self.assertTrue(all(read_report(
                archive_path(path/"AuctionHammer-OSTATNI-MECZ.json")/entry["file"]
            )["complete_from_start"] for entry in entries))
            self.assertTrue((path/"raport_100_meczow.json").exists())
            self.assertTrue((path/"wyniki_meczow.csv").exists())

    def test_unfinished_match_stores_diagnostics_and_returns_nonzero_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            report=tournament(games=1,start_seed=230111,max_steps=10,
                              output_dir=folder,verify_every=0)
            self.assertEqual(report["summary"]["finished"],0)
            self.assertEqual(report["summary"]["failed"],1)
            self.assertEqual(report["failed_seeds"],[230111])
            self.assertTrue((Path(folder)/"failures"/"seed_230111.json").is_file())
            self.assertFalse((Path(folder)/"AuctionHammer-OSTATNI-MECZ.json").exists())


if __name__=="__main__":
    unittest.main()
