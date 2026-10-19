"""Independent second-pass QA for v23 audit signatures and edge semantics.

Tests a real v23 match under both the original 0.9.36 audit layout and
the additive schema-2 layout. Existing history hashes MUST remain valid.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from game.core.audit import (
    state_snapshot,digest,initialize_audit,make_report,verify_replay)
from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.persistence import save_match,load_match
from tools.simulate_v22 import choose_actor
from test_auction_v22_0931 import ready,award,choose
from test_auction_v4_engine import place_basic


def complete_report(seed,schema,mode='v23'):
    game=Match(seed,audit_enabled=True,auctions_enabled=True,
               auction_catalog='v22')
    game.ruleset_version=mode
    game.audit_state_schema=schema
    initialize_audit(game)
    agents=ComputerOpponent(0),ComputerOpponent(1)
    for _ in range(3000):
        if game.phase=='finished':break
        player=choose_actor(game)
        agents[player].step(game)
        game.assert_integrity()
    if game.phase!='finished':
        raise AssertionError(f'Seed {seed} failed to finish')
    return make_report(game)['payload']


def replay(payload):
    return verify_replay(payload,
        lambda seed,auctions_enabled=False,auction_catalog='v3':
        Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
              auction_catalog=auction_catalog))


class V23AuditRulesetIntegrity(unittest.TestCase):
    def test_new_v23_snapshots_sign_rules_and_deferred_income(self):
        g=ready(237100)
        self.assertEqual(g.audit_state_schema,2)
        before=state_snapshot(g)
        self.assertEqual(before['ruleset_state']['version'],'v23')
        self.assertIsNone(before['ruleset_state']['pending_vacant_income'])
        g._finalize_end_turn()
        after=state_snapshot(g)
        self.assertEqual(after['ruleset_state']['pending_vacant_income'],0)
        self.assertNotEqual(digest(after),digest(before))
        after['ruleset_state']['pending_vacant_income']=None
        self.assertNotEqual(digest(after),digest(state_snapshot(g)),
                            'Tampering with an owed payout must change audit SHA')

    def test_resume_pending_choice_keeps_signed_income_schema_2(self):
        g=ready(237101)
        monster=award(g,'A003',1,zone='board')
        revived=place_basic(g,'S01',0,'grave')
        g.units[monster].hp=0
        g._finalize_end_turn()
        g._drain()
        self.assertIsNotNone(g.pending)
        snapshot=state_snapshot(g)
        self.assertEqual(snapshot['ruleset_state']['pending_vacant_income'],0)
        with TemporaryDirectory() as folder:
            path=Path(folder)/'pending.json'
            save_match(g,path)
            loaded=load_match(path)
        self.assertEqual(digest(snapshot),digest(state_snapshot(loaded)))
        self.assertEqual(loaded.audit_state_schema,2)
        choose(loaded,'revive_one',revived)
        self.assertEqual(loaded.slot_income[0],4)
        self.assertIsNone(loaded.pending_vacant_income)
        loaded.assert_integrity()

    def test_completed_v23_new_schema_replays_every_command(self):
        report=complete_report(237102,2)
        self.assertIn('ruleset_state',report['initial_state'])
        self.assertTrue(replay(report))

    def test_completed_0936_v23_old_schema_replays_without_hash_migration(self):
        report=complete_report(237103,1)
        report['version']='0.9.36'  # old signed archive's public version tag
        self.assertEqual(report['summary']['ruleset_version'],'v23')
        self.assertNotIn('ruleset_state',report['initial_state'])
        self.assertNotIn('ruleset_state',report['final_state'])
        self.assertTrue(replay(report))

    def test_original_v22_rule_mode_replays_without_schema2(self):
        report=complete_report(237104,1,mode='v22')
        self.assertNotIn('ruleset_state',report['initial_state'])
        self.assertTrue(replay(report))


if __name__ == '__main__':
    unittest.main()
