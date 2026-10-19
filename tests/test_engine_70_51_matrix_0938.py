"""0.9.38 stabilization: real engine routing of all 70+51 legal card variants.

This is a complete trigger/pipeline smoke, NOT a proof of every strategic
combination. Target-specific and cross-trigger semantics have separate tests.
"""
import unittest

from game.core.engine import Match
from game.core.auction_catalog import CATALOG_V22,RARITIES
from game.core.auction_abilities import any_future_auction
from game.core.effects import options as base_options
from game.core.models import IllegalMove
from test_auction_v22_0931 import ready,award
from test_auction_v4_engine import place_basic


def prepare(g,source):
    """Two legal basic enemy targets, one ally and one grave target."""
    owner_ally=next(x for x in ('S02','S03','S04','S05') if x!=source)
    enemy_a=next(x for x in ('S09','S01','S15') if x not in (source,owner_ally))
    enemy_b=next(x for x in ('S33','S11','S10') if x not in (source,owner_ally,enemy_a))
    grave=next(x for x in ('S17','S20','S85') if x not in (source,owner_ally,enemy_a,enemy_b))
    place_basic(g,owner_ally,0,'board')
    place_basic(g,enemy_a,1,'board')
    place_basic(g,enemy_b,1,'board')
    place_basic(g,grave,0,'grave')
    g.players[0].hp=79
    g.players[1].hp=79
    return enemy_a


def drain_choices(g,cap=45):
    for _ in range(cap):
        g._drain()
        if g.pending is None:return
        g.choose(0)
    raise AssertionError('Unbounded or stale pending chain')


class EveryBaseCardTriggeredThroughTheMatch(unittest.TestCase):
    def test_all_70_real_trigger_paths_preserve_every_physical_card(self):
        definitions=Match(938001).defs
        self.assertEqual(len(definitions),70)
        count=0
        for cid,d in definitions.items():
            with self.subTest(cid=cid,trigger=d.trigger):
                g=ready(938100+count)
                victim=prepare(g,cid)
                if d.faction in ('Elfy','Ludzie'):
                    place_basic(g,cid,0,'hand')
                    g.active=0
                    g.players[0].played_this_turn=False
                    g.play(cid)
                elif d.faction=='Dzikie bestie':
                    place_basic(g,cid,0,'board')
                    g.units[cid].played_turn=-10
                    g.active=0
                    # The prepared second enemy can have Prowokacja: the
                    # actual legal target must come from the engine, not a
                    # hard-coded first enemy slot.
                    targets=g.legal_attacks(cid)
                    self.assertTrue(targets)
                    g.attack(cid,targets[0])
                elif d.faction=='Potwory':
                    place_basic(g,cid,0,'board')
                    g.units[cid].hp=0
                    g._kill_batch([cid])
                    g._drain()
                elif d.faction=='Krasnoludy':
                    place_basic(g,cid,0,'board')
                    g.active=0
                    g.end_turn()
                else:
                    raise AssertionError('Unknown faction')
                drain_choices(g)
                g.assert_integrity()
                self.assertIn(cid,g.cards)
                self.assertEqual(g.ruleset_version,'v23')
                count+=1
        self.assertEqual(count,70)


class EveryAuctionRarityTriggeredThroughTheMatch(unittest.TestCase):
    def test_all_51_live_rarities_activate_without_breaking_supply(self):
        self.assertEqual(len(CATALOG_V22),17)
        count=0
        for aid,definition in CATALOG_V22.items():
            for tier,name in enumerate(RARITIES):
                with self.subTest(archetype=aid,rarity=name):
                    g=ready(939000+count)
                    prepare(g,'')
                    if definition.trigger in ('play','end','death'):
                        zone='hand' if definition.trigger=='play' else 'board'
                    else:
                        zone='hand' if aid=='A002' else 'board'
                    uid=award(g,aid,tier,zone=zone)
                    if zone=='hand':
                        g.active=0
                        g.players[0].played_this_turn=False
                        g.play(uid)
                    elif definition.trigger=='end':
                        g.active=0
                        g.end_turn()
                    elif definition.trigger=='death':
                        g.units[uid].hp=0
                        g._kill_batch([uid])
                        g._drain()
                    elif aid=='A007':
                        g._damage('hero:0',200)
                    elif aid=='A014':
                        g._heal('hero:1',4)
                    elif aid=='A015':
                        g._update_auras()
                    else:
                        raise AssertionError('Unsupported passive: '+aid)
                    drain_choices(g)
                    g.assert_integrity()
                    self.assertIn(uid,g.cards)
                    self.assertTrue(g.auction_awards[uid]['ability_implemented'])
                    self.assertFalse(any(u.startswith('AUC') for u in g.bank))
                    count+=1
        self.assertEqual(count,51)


if __name__=='__main__':
    unittest.main()
