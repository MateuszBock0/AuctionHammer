"""Production v22 vacant-slot coins after the ending player's own turn."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from game.core.engine import Match
from game.core.persistence import save_match,load_match
from game.core.audit import make_report,verify_replay
from test_auction_v4_engine import place_basic
from test_auction_v22_0931 import award,ready,choose


def new_match(seed=934300):
    game=Match(seed,audit_enabled=True,auctions_enabled=True,auction_catalog="v22")
    game.finish_mulligan(0,[]);game.finish_mulligan(1,[])
    return game


class VacantSlotsProduction(unittest.TestCase):
    def test_new_v22_live_both_players_get_empty_slot_income_each_own_turn(self):
        game=new_match()
        self.assertTrue(game.vacant_income_enabled)
        first=game.first
        second=1-first
        original=[p.coins for p in game.players]
        game.end_turn()
        self.assertEqual(game.players[first].coins,original[first]+5)
        self.assertEqual(game.players[second].coins,original[second])
        game.end_turn()
        self.assertEqual(game.slot_income,[5,5])
        self.assertEqual(game.slot_income_turns,[1,1])
        # The ordinary +1 to both on a completed round is untouched.
        self.assertEqual(game.players[first].coins,original[first]+5+1)
        self.assertEqual(game.players[second].coins,original[second]+5+1)
        game.assert_integrity()

    def test_exact_board_occupancy_zero_through_five(self):
        for units in range(6):
            with self.subTest(occupied=units):
                g=new_match(934301+units)
                first=g.active
                for cid in ('S01','S02','S03','S04','S05')[:units]:
                    place_basic(g,cid,first)
                old=g.players[first].coins
                g.end_turn()
                self.assertEqual(g.slot_income[first],5-units)
                self.assertEqual(g.players[first].coins,old+5-units)
                g.assert_integrity()

    def test_economy_applies_after_queued_queen_summon_not_before(self):
        g=ready(934310)
        self.assertTrue(g.vacant_income_enabled)
        g.active=0
        queen=award(g,'A010',0,zone='board')
        old=g.players[0].coins
        g.end_turn()
        self.assertIsNotNone(g.pending)
        self.assertEqual(g.slot_income[0],0)
        choose(g,'summon')
        self.assertEqual(len(g.players[0].board),2)
        self.assertEqual(g.slot_income[0],3)
        self.assertEqual(g.players[0].coins,old+3+(1 if 0!=g.first else 0))
        g.assert_integrity()

    def test_v4_and_explicit_old_v22_games_stay_on_old_economy(self):
        for mode in ('v4','v22'):
            with self.subTest(mode=mode):
                g=Match(934320,auctions_enabled=True,auction_catalog=mode,
                        vacant_income_enabled=False)
                g.finish_mulligan(0,[]);g.finish_mulligan(1,[])
                first=g.active;old=g.players[first].coins
                g.end_turn()
                self.assertEqual(g.players[first].coins,old)
                self.assertEqual(g.slot_income,[0,0])
                with tempfile.TemporaryDirectory() as folder:
                    file=Path(folder)/'legacy.json'
                    save_match(g,file)
                    loaded=load_match(file)
                self.assertFalse(loaded.vacant_income_enabled)
                loaded.assert_integrity()
        g=Match(934321,auctions_enabled=True,auction_catalog='v4')
        self.assertFalse(g.vacant_income_enabled)

    def test_enabled_economy_survives_saved_match_resume(self):
        g=new_match(934330)
        first=g.active
        g.end_turn()
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'saved.json'
            save_match(g,file)
            g=load_match(file)
        self.assertTrue(g.vacant_income_enabled)
        self.assertEqual(g.slot_income[first],5)
        second=g.active
        g.end_turn()
        self.assertEqual(g.slot_income[second],5)
        g.assert_integrity()

    def test_completed_match_audit_counts_slot_income_and_replays(self):
        from tools.simulate_v22 import simulate_one
        g,steps=simulate_one(934340)
        self.assertGreater(steps,10)
        self.assertTrue(g.vacant_income_enabled)
        self.assertGreater(sum(g.slot_income),0)
        payload=make_report(g)['payload']
        self.assertTrue(payload['summary']['vacant_slot_income_enabled'])
        self.assertEqual(payload['summary']['vacant_slot_income_total'],g.slot_income)
        self.assertTrue(verify_replay(
            payload,lambda seed,auctions_enabled=False,auction_catalog='v3':
            Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
                  auction_catalog=auction_catalog)))


if __name__=="__main__":
    unittest.main()
