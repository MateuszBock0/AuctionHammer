"""0.9.31 v22 acceptance: 15 executable variants and separate physical auction bag."""
import unittest
from game.core.engine import Match
from game.core.models import Card,CardDefinition,Unit
from game.core import auction
from game.core.auction_catalog import (CATALOG_V22,V22_CARDS,RARITIES,TRIGGER,
                                      live_variant,stats_v22)
from game.core.persistence import save_match,load_match
from test_auction_v4_engine import place_basic
from pathlib import Path
import tempfile

def ready(seed=93100):
    g=Match(seed,auctions_enabled=True,auction_catalog='v22')
    g.finish_mulligan(0,[])
    g.finish_mulligan(1,[])
    g.active=0;g.phase='turn'
    for p in g.players:p.turn_count=max(1,p.turn_count)
    return g

def award(g,aid,tier=0,owner=0,zone='hand',n=1):
    uid=f'AUC{n:03d}{aid}'
    a=CATALOG_V22[aid]
    atk,hp=stats_v22(aid,3)
    d=CardDefinition(aid,a.name,'Ludzie',a.family,TRIGGER[a.trigger],
                     atk,hp,live_variant('v22',aid,RARITIES[tier]),'v22',0,0)
    card=Card(uid,d,owner=owner,zone=zone)
    g.cards[uid]=card;g.defs[uid]=d
    g.auction_bag.remove(aid)
    g.auction_awards[uid]={'number':n,'level':1,'rarity':RARITIES[tier],
        'initial_rarity':RARITIES[tier],'atk':atk,'hp':hp,'archetype':aid,
        'purchase_round':3,'last_evolve_round':3,'ability_implemented':True}
    getattr(g.players[owner],zone).append(uid)
    if zone=='board':g.units[uid]=Unit(uid,owner,atk,hp,hp,0,0)
    return uid

def choose(g,mode,target=None):
    assert g.pending is not None,(mode,target)
    matches=[i for i,c in enumerate(g.pending.choices)
             if c.mode==mode and (target is None or c.target==target)]
    assert matches,(mode,target,g.pending.choices)
    g.choose(matches[0])

class AuctionV22DataAndSupply(unittest.TestCase):
    def test_all_17_archetypes_exact_51_texts_and_8_auctions(self):
        g=ready(93101)
        self.assertEqual(len(V22_CARDS),17)
        self.assertNotIn('A017',V22_CARDS)
        self.assertEqual(len(set(g.auction_bag)),17)
        for aid in CATALOG_V22:
            for rarity in RARITIES:
                self.assertTrue(live_variant('v22',aid,rarity))
            for r in (3,6,9,12,15,18,21,24):
                self.assertEqual(sum(stats_v22(aid,r)),r+8)
        g.round=4
        for idx in range(8):
            g.round=4+idx*3
            state=auction.begin(g)
            self.assertIsNotNone(state)
            self.assertEqual(len({x.archetype for x in state.offers}),3)
            if state.phase=='bidding':
                g.auction_pass(state.turn);g.auction_pass(state.turn)
            g.auction_pick(state.turn,state.offers[0].uid)
            g.auction_pick(g.auction.turn,state.offers[1].uid)
            self.assertEqual(len(g.auction_bag),17-(idx+1)*2)
            self.assertFalse(any(x.startswith('AUC') for x in g.bank))
            g.assert_integrity()
        self.assertEqual(len(g.auction_bag),1)
        self.assertIsNone(auction.begin(g))

    def test_legacy_v4_save_stays_twelve_archetypes(self):
        g=Match(93102,auction_catalog='v4',auctions_enabled=True)
        self.assertEqual(len(g.auction_bag),12)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'old.json';save_match(g,path)
            loaded=load_match(path)
        self.assertEqual(loaded.auction_catalog,'v4')
        self.assertEqual(len(loaded.auction_bag),12)
        loaded.assert_integrity()

class AuctionV22FiveVariants(unittest.TestCase):
    def test_A013_three_tiers_ignore_armor_but_shield_works(self):
        for tier,pct in enumerate((25,40,60)):
            with self.subTest(tier=tier):
                g=ready(93113+tier)
                t=place_basic(g,'S01',1)
                g.units[t].base_max_hp=20;g.units[t].hp=20
                g.units[t].armor_perm=30;g.units[t].shield=1
                s=award(g,'A013',tier)
                g.play(s);choose(g,'bastion',t)
                self.assertEqual(g.units[t].shield,0)
                self.assertEqual(g.units[t].hp,20-(12 if tier==2 else 0))
                if tier!=2:
                    g._remove_unit(s,death=False)
                    # Recast the target effect without shield.
                    from game.core.auction_abilities import execute
                    from game.core.models import Choice
                    execute(g,s,'play',Choice('bastion',t,''))
                    self.assertEqual(g.units[t].hp,20-(5 if tier==0 else 8))
                self.assertEqual(g.units[t].armor_perm,30)
                g.assert_integrity()

    def test_A014_three_tiers_healing_conversion(self):
        for tier,expected in enumerate((60,59,55)):
            with self.subTest(tier=tier):
                g=ready(93123+tier)
                s=award(g,'A014',tier,zone='board')
                g.players[1].hp=60
                g._heal('hero:1',5)
                self.assertEqual(g.players[1].hp,expected)
                g._heal('hero:0',5)
                g.assert_integrity()

    def test_A015_three_tiers_cancel_triggers(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(93133+tier)
                w=award(g,'A015',tier,zone='board')
                victim=place_basic(g,'S33',0)
                place_basic(g,'S01',1,'hand')
                g.active=1
                old=g.units[victim].hp
                g.play('S01')
                self.assertEqual(g.units[victim].hp,old)
                self.assertIsNone(g.pending)
                self.assertEqual(g.players[1].played_this_turn,True)
                g.assert_integrity()

    def test_A016_three_tiers_deck_draw_and_free_play(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(93143+tier)
                src=award(g,'A016',tier)
                old=g.players[0].played_this_turn
                g.play(src)
                self.assertTrue(g.players[0].played_this_turn)
                if tier<2:
                    candidate=g.pending.choices[0].target
                    choose(g,'cart_draw',candidate)
                    self.assertIn(candidate,g.players[0].hand)
                if tier>=1 and g.pending:
                    candidate=g.pending.choices[0].target
                    choose(g,'cart_play',candidate)
                    self.assertIn(candidate,g.units)
                    self.assertNotIn(candidate,g.players[g.units[candidate].owner].deck)
                g.assert_integrity()

    def test_A018_three_tiers_vouchers_and_automatic_auction(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(93153+tier)
                src=award(g,'A018',tier)
                old=g.players[0].coins
                g.play(src)
                self.assertEqual(g.players[0].coins,old+(2 if tier<2 else 0))
                self.assertEqual(len(g.auction_vouchers[0]),1)
                g.round=4
                state=auction.begin(g)
                if tier==2:
                    self.assertEqual((state.phase,state.winner,state.price),('picking',0,0))
                else:
                    self.assertEqual(state.bid_bonus[0],(2,5)[tier])
                    minimum=max(1,state.highest_effective+1-state.bid_bonus[0])
                    # Give bidder enough money regardless of start bonus.
                    g.players[0].coins=10
                    g.auction_bid(state.turn,minimum)
                    self.assertEqual(state.highest_effective,minimum+(2,5)[tier])
                self.assertEqual(g.auction_vouchers[0],[])
                g.assert_integrity()

    def test_two_legendary_guarantees_cancel_each_other(self):
        g=ready(93190)
        g.auction_vouchers=[[{'guaranteed':True}],[{'guaranteed':True}]]
        g.round=4
        state=auction.begin(g)
        self.assertEqual(state.phase,'bidding')
        g.auction_pass(state.turn);g.auction_pass(state.turn)
        self.assertEqual(state.phase,'picking')
        self.assertEqual(state.price,0)
        g.assert_integrity()

if __name__=='__main__':
    unittest.main()
