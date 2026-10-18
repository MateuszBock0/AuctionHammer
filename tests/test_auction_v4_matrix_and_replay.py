"""End-to-end smoke of every live auction v4 rarity and ordinary solo play.

Uses unchanged ComputerOpponent at both seats as a deterministic stress driver.
"""
import unittest
from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.audit import state_snapshot,verify_replay
from game.core.auction_catalog import CATALOG
from test_auction_v4_engine import ready,award,place_basic


class AllAuctionAbilityVariants(unittest.TestCase):
    def test_each_of_36_variants_resolves_in_real_match_pipeline(self):
        count=0
        for number,(aid,definition) in enumerate(CATALOG.items()):
            for tier in range(3):
                with self.subTest(archetype=aid,rarity=tier):
                    g=ready(2700+number*3+tier)
                    place_basic(g,'S01',0)
                    place_basic(g,'S02',1)
                    place_basic(g,'S03',0,'grave')
                    g.players[0].hp=62
                    g.players[1].hp=47
                    trigger=definition.trigger
                    if trigger=='play':
                        uid=award(g,aid,tier,owner=0,zone='hand')
                        g.play(uid)
                    else:
                        uid=award(g,aid,tier,owner=0,zone='board')
                        if trigger=='death':
                            g._kill_batch([uid])
                            g._drain()
                        elif trigger=='end':
                            g.end_turn()
                        else:
                            g._update_auras()
                            if aid=='A007':
                                g._damage('hero:0',150)
                    for _ in range(22):
                        if not g.pending:
                            break
                        g.choose(0)
                    self.assertIsNone(g.pending,'Unresolved auction choice')
                    self.assertIn(uid,g.cards)
                    g.assert_integrity()
                    count+=1
        self.assertEqual(count,36)


class FullSoloAndAuditRegression(unittest.TestCase):
    def test_v4_unchanged_ai_can_play_and_audit_replay(self):
        m=Match(2151,auctions_enabled=True,auction_catalog='v4',
                audit_enabled=True)
        ai=[ComputerOpponent(0),ComputerOpponent(1)]
        for step in range(220):
            if m.phase=='finished':
                break
            if m.phase=='mulligan':
                for bot in ai:bot.step(m)
            elif m.phase=='auction':
                ai[m.auction.turn].step(m)
            elif m.pending:
                ai[m.pending.owner].step(m)
            else:
                ai[m.active].step(m)
            m.assert_integrity()
        self.assertTrue(m.audit_complete)
        self.assertGreaterEqual(len(m.auction_history),1)
        report={
            'seed':m.seed,
            'complete_from_start':m.audit_complete,
            'initial_state':m.audit_initial,
            'actions':m.audit_actions,
            'event_journal':list(m.event_journal),
            'internal_events':m.audit_internal,
            'final_state':state_snapshot(m)
        }
        self.assertEqual(report['initial_state']['auction_catalog'],'v4')
        self.assertTrue(verify_replay(report,
            lambda seed,auctions_enabled=False,auction_catalog='v4':
                Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
                      auction_catalog=auction_catalog)))


if __name__=='__main__':
    unittest.main()
