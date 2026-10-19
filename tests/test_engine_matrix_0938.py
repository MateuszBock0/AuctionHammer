"""0.9.38: end-to-end smoke matrix for every 70 base and 51 auction variants.

Uses real Match game paths and standard pending resolution, rather than
calling card handlers directly. This is branch coverage / invariant smoke,
NOT a claim to exhaust every possible combination of card interactions.
"""
from __future__ import annotations

import unittest
import csv
from pathlib import Path
from game.core.engine import Match
from game.core.models import FACTIONS, FAMILIES
from game.core.auction_catalog import CATALOG_V22, RARITIES, V22_CARDS
from game.core import auction_abilities
from test_auction_v22_0931 import ready, award
from test_auction_v4_engine import place_basic


def resolve_all(game,limit=32):
    for i in range(limit):
        if game.pending is None:
            break
        game.choose(0)
    assert game.pending is None, (
        'An ability left Pending unresolved after '+str(limit)+' selections')
    game.assert_integrity()


def stage(game,card_id):
    """Four physically distinct cards: source, an ally, an enemy and a grave."""
    occupied={card_id}
    def next_one(candidates):
        result=next(cid for cid in candidates if cid not in occupied)
        occupied.add(result)
        return result
    ally=next_one(('S03','S05','S02','S07','S33'))
    enemy=next_one(('S01','S09','S15','S35','S58'))
    grave=next_one(('S17','S82','S02','S60','S21'))
    place_basic(game,ally,0,'board')
    place_basic(game,enemy,1,'board')
    place_basic(game,grave,0,'grave')
    game.players[0].hp=70
    game.players[1].hp=65
    return ally,enemy,grave


class BaseCardV23FullCatalog(unittest.TestCase):
    def test_70_of_70_in_actual_activation_pipeline(self):
        names=Match(38000).defs
        self.assertEqual(len(names),70)
        activated=set()
        for index,(cid,definition) in enumerate(names.items()):
            with self.subTest(card=cid,trigger=definition.trigger):
                game=ready(38001+index)
                ally,enemy,grave=stage(game,cid)
                if definition.faction in ('Elfy','Ludzie'):
                    place_basic(game,cid,0,'hand')
                    game.play(cid)
                elif definition.faction=='Dzikie bestie':
                    place_basic(game,cid,0,'board')
                    self.assertIn(enemy,game.legal_attacks(cid))
                    game.attack(cid,enemy)
                elif definition.faction=='Potwory':
                    place_basic(game,cid,0,'board')
                    game.units[cid].hp=0
                    game._kill_batch([cid])
                    game._drain()
                    self.assertIn(cid,game.players[0].grave)
                elif definition.faction=='Krasnoludy':
                    place_basic(game,cid,0,'board')
                    game.end_turn()
                else:
                    self.fail('Unknown activation family: '+definition.faction)
                resolve_all(game)
                game.assert_integrity()
                activated.add(cid)
        self.assertEqual(activated,set(names))

    def test_14_families_each_have_five_distinct_faction_representatives(self):
        definitions=Match(38100).defs
        self.assertEqual(set(d.faction for d in definitions.values()),set(FACTIONS))
        for family in FAMILIES:
            with self.subTest(family=family):
                self.assertEqual({d.faction for d in definitions.values()
                                  if d.family==family},set(FACTIONS))


class AuctionV23FullMatrix(unittest.TestCase):
    def test_51_of_51_in_live_v23_execution_pipeline(self):
        self.assertEqual(len(CATALOG_V22),17)
        self.assertEqual(len(V22_CARDS),17)
        completed=set()
        for index,(aid,archetype) in enumerate(CATALOG_V22.items()):
            for tier,rarity in enumerate(RARITIES):
                with self.subTest(archetype=aid,rarity=rarity):
                    game=ready(38200+index*3+tier)
                    ally,enemy,grave=stage(game,aid)
                    uid=award(game,aid,tier,owner=0,
                              zone='hand' if archetype.trigger=='play' else 'board')
                    self.assertEqual(auction_abilities.kind(game,uid),aid)
                    self.assertEqual(auction_abilities.rarity(game,uid),tier)
                    if archetype.trigger=='play':
                        game.play(uid)
                    elif archetype.trigger=='death':
                        game.units[uid].hp=0
                        game._kill_batch([uid])
                        game._drain()
                    elif archetype.trigger=='end':
                        game.end_turn()
                    elif archetype.trigger=='passive':
                        game._update_auras()
                        if aid=='A002' and tier==1:
                            game._queue(uid,'play')
                            game._drain()
                        elif aid=='A007':
                            game._damage('hero:0',1000)
                        elif aid=='A014':
                            game._heal('hero:1',5)
                        elif aid=='A015':
                            game._queue(enemy,'play')
                            game._drain()
                    else:
                        self.fail('Unknown auction trigger: '+archetype.trigger)
                    resolve_all(game)
                    game.assert_integrity()
                    completed.add((aid,tier))
        self.assertEqual(completed,
                         {(a,t) for a in CATALOG_V22 for t in range(3)})

    def test_published_121_row_matrix_matches_live_catalogues(self):
        path=Path(__file__).resolve().parents[1]/'docs'/'ENGINE_COVERAGE_MATRIX_0938.csv'
        with path.open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        definitions=Match(38310).defs
        expected={('podstawowa',cid,'—') for cid in definitions}
        expected.update({('aukcyjna',aid,rarity)
                         for aid in CATALOG_V22
                         for rarity in RARITIES})
        actual={(row['pool'],row['card_id'],row['rarity']) for row in rows}
        self.assertEqual(len(rows),121)
        self.assertEqual(len(actual),121)
        self.assertEqual(actual,expected)
        for row in rows:
            reference=(definitions if row['pool']=='podstawowa' else CATALOG_V22)
            self.assertEqual(row['name'],reference[row['card_id']].name)
            self.assertTrue(row['engine_path'] and row['test_scope'])

    def test_all_51_variant_texts_nonempty_and_separate_from_base_pool(self):
        game=ready(38300)
        base_ids=set(game.defs)
        self.assertEqual(len(base_ids),70)
        self.assertEqual(len(game.auction_bag),17)
        self.assertTrue(base_ids.isdisjoint(CATALOG_V22))
        for aid in CATALOG_V22:
            with self.subTest(auction_card=aid):
                self.assertNotIn(aid,game.bank)
                for rarity in ('basic','rare','legendary'):
                    self.assertTrue(V22_CARDS[aid]['variants'][rarity].strip())


if __name__=='__main__':
    unittest.main()
