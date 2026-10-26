"""0.9.95 tavern beer stage 1: strict economy, fair global damage, audit.

Cost is MAX(10 + both players' started turns, CEIL(current coins/10)).
No rounds-based cap, no repeat surcharge, no increasing damage stacks.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from game.core.engine import Match
from game.core.audit import ACTIONS,state_snapshot
from game.core.models import IllegalMove
from game.core.persistence import save_match,load_match
from test_balance_buff_v24_0990 import ready,starter


class TavernBeer0995(unittest.TestCase):
    def test_price_is_exact_max_of_turns_or_ceil_ten_percent(self):
        g=ready(99501)
        p=g.players[0]
        self.assertTrue(g.tavern_beer_enabled)
        self.assertEqual(sum(x.turn_count for x in g.players),2)
        for money,wanted in ((0,12),(19,12),(119,12),(120,12),
                             (121,13),(299,30),(500,50)):
            with self.subTest(money=money):
                p.coins=money
                self.assertEqual(g.beer_price(0),wanted)
        g.players[0].turn_count=4
        g.players[1].turn_count=5
        p.coins=1
        self.assertEqual(g.beer_price(0),19)

    def test_order_pays_price_and_subsequent_orders_extend_three_only(self):
        g=ready(99502)
        g.players[0].coins=100
        price=g.beer_price(0)
        self.assertEqual(price,12)
        self.assertTrue(g.can_order_beer(0))
        g.order_beer(0)
        self.assertEqual(g.players[0].coins,100-price)
        self.assertEqual(g.beer_turns_remaining,3)
        self.assertEqual(g.beer_orders,1)
        self.assertEqual(g.audit_actions[-1]['operation'],'order_beer')
        g.order_beer(0)
        self.assertEqual(g.beer_turns_remaining,6)
        self.assertEqual(g.beer_orders,2)
        self.assertEqual(g.players[0].coins,100-2*price)
        self.assertIn('tavern_beer_enabled',state_snapshot(g)['ruleset_state'])
        self.assertIn('order_beer',ACTIONS)
        g.assert_integrity()

    def test_1_damage_both_sides_each_completed_player_turn(self):
        g=ready(99503)
        g.players[0].coins=100
        ally=starter(g,'S01',0)
        enemy=starter(g,'S12',1)
        original={uid:g.units[uid].hp for uid in (ally,enemy)}
        g.order_beer(0)
        for left in (2,1,0):
            g.end_turn()
            self.assertEqual(g.beer_turns_remaining,left)
            elapsed=3-left
            for uid in (ally,enemy):
                self.assertEqual(g.units[uid].hp,original[uid]-elapsed)
        g.end_turn()
        self.assertEqual(g.beer_turns_remaining,0)
        for uid in (ally,enemy):
            self.assertEqual(g.units[uid].hp,original[uid]-3)
        g.assert_integrity()

    def test_shield_and_armor_still_apply_to_beer_damage(self):
        g=ready(99504)
        x=starter(g,'S01')
        y=starter(g,'S12',1)
        g.units[x].shield=1
        g.units[y].armor_temp=2
        a,b=g.units[x].hp,g.units[y].hp
        g.players[0].coins=100
        g.order_beer(0)
        g.end_turn()
        self.assertEqual(g.units[x].hp,a)
        self.assertEqual(g.units[x].shield,0)
        self.assertEqual(g.units[y].hp,b)
        self.assertEqual(g.units[y].armor_temp,1)
        g.end_turn()
        self.assertEqual(g.units[x].hp,a-1)
        self.assertEqual(g.units[y].hp,b)
        self.assertEqual(g.units[y].armor_temp,0)
        g.end_turn()
        self.assertEqual(g.units[y].hp,b-1)

    def test_two_simultaneous_deaths_batch_and_rewards(self):
        g=ready(99505)
        ally=starter(g,'S01')
        enemy=starter(g,'S12',1)
        g.units[ally].hp=1
        g.units[enemy].hp=1
        g.players[0].coins=100
        g.order_beer(0)
        g.end_turn()
        self.assertNotIn(ally,g.units)
        self.assertNotIn(enemy,g.units)
        self.assertEqual(g.beer_turns_remaining,2)
        self.assertTrue(any('Fala śmierci' in e['text'] or
                            'Zgon ' in e['text'] for e in g.event_journal))
        g.assert_integrity()

    def test_reject_enemy_turn_pending_and_insufficient_funds(self):
        g=ready(99506)
        p=g.players[0]
        p.coins=0
        self.assertFalse(g.can_order_beer(0))
        with self.assertRaises(IllegalMove):
            g.order_beer(0)
        self.assertEqual(g.beer_turns_remaining,0)
        p.coins=100
        with self.assertRaises(IllegalMove):
            g.order_beer(1)
        g.phase='auction'
        with self.assertRaises(IllegalMove):
            g.order_beer(0)
        g.phase='turn'
        self.assertFalse(g.can_order_beer(1))

    def test_signed_replay_with_real_paid_beer_and_three_ticks(self):
        # A genuine seed-driven, public-command-only game. Never fabricate
        # starting coins or reset the audit seed's initial state.
        from game.core.audit import verify_replay
        game=Match(99570,audit_enabled=True,auctions_enabled=True,
                   auction_catalog='v22',starting_compensation='coins')
        game.finish_mulligan(0,[])
        game.finish_mulligan(1,[])
        bought=False
        ticks=0
        for _ in range(90):
            if game.phase=='auction':
                state=game.auction
                if state.phase=='bidding':
                    game.auction_pass(state.turn)
                else:
                    remaining=[x for x in state.offers
                               if x.uid not in state.picks.values()]
                    game.auction_pick(state.turn,remaining[0].uid)
                continue
            if game.phase!='turn':
                break
            if not bought and game.can_order_beer(game.active):
                game.order_beer(game.active)
                bought=True
            before=game.beer_turns_remaining
            game.end_turn()
            if bought and before>game.beer_turns_remaining:
                ticks+=1
            if bought and ticks>=3:
                break
        self.assertTrue(bought,'Fresh audited game never afforded beer')
        self.assertEqual(ticks,3)
        self.assertEqual(game.beer_turns_remaining,0)
        payload={'complete_from_start':True,'seed':game.seed,
                 'version':'0.9.95',
                 'initial_state':game.audit_initial,
                 'actions':game.audit_actions,
                 'internal_events':game.audit_internal,
                 'event_journal':game.event_journal,
                 'final_state':state_snapshot(game),
                 'summary':{'vacant_slot_income_enabled':game.vacant_income_enabled,
                            'ruleset_version':game.ruleset_version}}
        # Restore the same journal/audit mode used by the real GUI:
        # Match(seed) alone defaults to audit_enabled=False and omits
        # action_seq/internal_seq from journal messages.
        self.assertTrue(verify_replay(
            payload,lambda seed,**kwargs: Match(
                seed,audit_enabled=True,**kwargs)))

    def test_old_save_and_old_signed_state_not_changed(self):
        g=ready(99507)
        g.tavern_beer_enabled=False
        self.assertNotIn('tavern_beer_enabled',state_snapshot(g)['ruleset_state'])
        with TemporaryDirectory() as d:
            path=Path(d)/'archive.json'
            save_match(g,path)
            restored=load_match(path)
            self.assertFalse(restored.tavern_beer_enabled)
            self.assertEqual(state_snapshot(g),state_snapshot(restored))
            with self.assertRaises(IllegalMove):
                restored.order_beer(0)

    def test_live_save_persists_running_hazard(self):
        g=ready(99508)
        g.players[0].coins=100
        g.order_beer(0)
        g.end_turn()
        with TemporaryDirectory() as d:
            path=Path(d)/'game.json'
            save_match(g,path)
            restored=load_match(path)
        self.assertTrue(restored.tavern_beer_enabled)
        self.assertEqual(restored.beer_turns_remaining,2)
        self.assertEqual(restored.beer_orders,1)
        self.assertEqual(state_snapshot(restored),state_snapshot(g))


if __name__=='__main__':
    unittest.main()
