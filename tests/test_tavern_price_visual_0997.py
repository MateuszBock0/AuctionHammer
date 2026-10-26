"""v0.9.97: independent beer price, stronger normal AI and shared flame FX."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.audit import state_snapshot,verify_replay
from game.core.persistence import save_match,load_match
from game.ui.beer_fx import beer_fx_state,beer_overflow_state
from test_balance_buff_v24_0990 import ready


class BeerPrice0997(unittest.TestCase):
    def test_personal_mugs_and_turns_not_wealth(self):
        g=ready(99701)
        g.tavern_price_v2_enabled=True
        g.players[0].coins=150
        g.players[1].coins=150
        turns=sum(p.turn_count for p in g.players)
        self.assertEqual(g.beer_price(0),10+turns//2)
        self.assertEqual(g.beer_price(1),10+turns//2)
        g.order_beer(0)
        self.assertEqual(g.beer_price(0),20+turns//2)
        self.assertEqual(g.beer_price(1),10+turns//2)
        g.players[0].turn_count+=2
        self.assertEqual(g.beer_price(0),21+turns//2)
        self.assertEqual(g.beer_price(1),11+turns//2)
        self.assertEqual(g.beer_turns_remaining,3)
        g.assert_integrity()

    def test_old_formula_survives_and_new_save_roundtrips(self):
        g=ready(99702)
        g.players[0].coins=300
        self.assertFalse(g.tavern_price_v2_enabled)
        self.assertEqual(g.beer_price(0),30)
        g.tavern_price_v2_enabled=True
        g.order_beer(0)
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'match.json'
            save_match(g,path)
            restored=load_match(path)
            self.assertTrue(restored.tavern_price_v2_enabled)
            self.assertEqual(restored.beer_orders_by_player,[1,0])
            self.assertEqual(restored.beer_price(0),g.beer_price(0))
            old=ready(99703)
            del old.tavern_price_v2_enabled
            del old.beer_orders_by_player
            save_match(old,path)
            legacy=load_match(path)
            self.assertFalse(legacy.tavern_price_v2_enabled)
            self.assertEqual(legacy.beer_orders_by_player,[0,0])

    def test_new_price_signed_audit_replays(self):
        g=Match(99704,audit_enabled=True,auctions_enabled=True,
                auction_catalog='v22',tavern_price_v2_enabled=True)
        g.finish_mulligan(0,[])
        g.finish_mulligan(1,[])
        purchased=False
        for _ in range(100):
            if g.phase=='auction':
                a=g.auction
                if a.phase=='bidding':g.auction_pass(a.turn)
                else:
                    opts=[o for o in a.offers if o.uid not in a.picks.values()]
                    g.auction_pick(a.turn,opts[0].uid)
                continue
            if g.phase!='turn':break
            if not purchased and g.can_order_beer(g.active):
                g.order_beer(g.active)
                purchased=True
            g.end_turn()
            if purchased:break
        self.assertTrue(purchased)
        payload={'complete_from_start':True,'seed':g.seed,
                 'version':'0.9.97','initial_state':g.audit_initial,
                 'actions':g.audit_actions,'internal_events':g.audit_internal,
                 'event_journal':g.event_journal,
                 'final_state':state_snapshot(g),
                 'summary':{'ruleset_version':g.ruleset_version,
                            'vacant_slot_income_enabled':g.vacant_income_enabled}}
        self.assertTrue(verify_replay(
            payload,lambda seed,**kwargs: Match(seed,audit_enabled=True,**kwargs)))


class NormalBid0997(unittest.TestCase):
    def test_contests_near_equal_offers_and_saves_some_coins(self):
        game=SimpleNamespace(auction=SimpleNamespace(number=1),
          players=[SimpleNamespace(coins=20),SimpleNamespace(coins=20)],
          auction_catalog='v22',auction_bag=['A001','A002','A003'])
        ai=ComputerOpponent(0,'normalny')
        ai.auction_first_pick_advantage=lambda _: (0.,0.)
        self.assertGreaterEqual(ai.auction_bid_ceiling(game),4)
        self.assertLess(ai.auction_bid_ceiling(game),20)
        game.players[0].coins=3
        self.assertLessEqual(ai.auction_bid_ceiling(game),3)
        self.assertEqual(ComputerOpponent(0,'łatwy').auction_bid_ceiling(game),1)


class MugOverflow0997(unittest.TestCase):
    def test_full_mug_shared_fx_turn_off_and_expiry(self):
        self.assertEqual(beer_overflow_state(1600,None),0.0)
        self.assertEqual(beer_overflow_state(1599,1000),0.0)
        self.assertEqual(beer_overflow_state(1600,1000),1.0)
        self.assertGreater(beer_overflow_state(1800,1000),0.0)
        self.assertEqual(beer_overflow_state(2050,1000),0.0)
        self.assertEqual(beer_overflow_state(1600,1000,False),0.0)
        self.assertEqual(beer_fx_state(1600,1000)[0],1.0)


if __name__=='__main__':
    unittest.main()
