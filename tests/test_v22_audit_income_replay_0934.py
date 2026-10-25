"""Regression: v22 audits must replay with the original saved economy.

New v22 games gain vacant-slot income. An archived old or explicit legacy-mode
match must NOT be replayed under the newer bonus rule.
"""
from __future__ import annotations
import copy
import unittest

from game.core.ai import ComputerOpponent
from game.core.audit import make_report,verify_replay
from game.core.engine import Match
from tools.simulate_v22 import choose_actor


def audited_game(seed,bonus):
    g=Match(seed,audit_enabled=True,auctions_enabled=True,
            auction_catalog='v22',vacant_income_enabled=bonus,
            balance_patch_v24=bonus)
    bot=(ComputerOpponent(0,'normalny'),ComputerOpponent(1,'normalny'))
    for _ in range(3000):
        if g.phase=='finished':break
        actor=choose_actor(g)
        if actor not in (0,1):raise AssertionError('No actor')
        bot[actor].step(g)
        g.assert_integrity()
    if g.phase!='finished':raise AssertionError('Game did not finish')
    return make_report(g)['payload']


def replay(payload):
    return verify_replay(payload,
        lambda seed,auctions_enabled=False,auction_catalog='v3':
        Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
              auction_catalog=auction_catalog))


class SignedIncomeReplayTests(unittest.TestCase):
    def test_v22_new_economy_replays_with_ledger(self):
        payload=audited_game(934600,True)
        self.assertTrue(payload['summary']['vacant_slot_income_enabled'])
        self.assertGreater(sum(payload['summary']['vacant_slot_income_total']),0)
        self.assertTrue(replay(payload))

    def test_v22_legacy_disabled_income_replays_with_original_rules(self):
        payload=audited_game(934601,False)
        self.assertFalse(payload['summary']['vacant_slot_income_enabled'])
        self.assertEqual(payload['summary']['vacant_slot_income_total'],[0,0])
        self.assertTrue(replay(payload))

    def test_old_v22_audit_without_income_metadata_assumes_old_rules(self):
        payload=audited_game(934602,False)
        # Format of pre-0.9.34 archives did not contain either of these keys.
        payload['version']='0.9.33'
        payload['summary'].pop('vacant_slot_income_enabled')
        payload['summary'].pop('vacant_slot_income_total')
        self.assertTrue(replay(payload))

    def test_income_ledger_mismatch_is_detected_not_silently_accepted(self):
        payload=audited_game(934603,True)
        altered=copy.deepcopy(payload)
        altered['summary']['vacant_slot_income_total'][0]+=1
        with self.assertRaisesRegex(ValueError,'dochodu za wolne pola'):
            replay(altered)

    def test_bad_income_mode_metadata_rejected(self):
        payload=audited_game(934604,False)
        payload['summary']['vacant_slot_income_enabled']='nie'
        with self.assertRaisesRegex(ValueError,'flaga dochodu'):
            replay(payload)


if __name__=='__main__':
    unittest.main()
