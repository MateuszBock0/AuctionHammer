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
                    state.turn=0
                    g.auction_bid(0,minimum)
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


class AuctionV22EdgeCollisions(unittest.TestCase):
    def test_A014_partial_heal_shield_armor_and_silencing(self):
        from game.core.auction_abilities import convert_healing
        g=ready(93200)
        priest=award(g,'A014',1,zone='board')
        target=place_basic(g,'S01',1)
        u=g.units[target]
        u.base_max_hp=20;u.hp=12;u.shield=1;u.armor_perm=10
        g._heal(target,5)
        self.assertEqual((u.hp,u.shield,u.armor_perm),(14,0,10))
        g._add_effect(priest,'silence',source='S59',positive=False,expires=5)
        g._heal(target,5)
        self.assertEqual(u.hp,19)
        g.assert_integrity()

    def test_A014_full_hp_is_nominal_and_priests_do_not_stack(self):
        g=ready(93201)
        source=award(g,'A014',1,zone='board')
        target=place_basic(g,'S01',1)
        before=g.units[target].hp
        g._heal(target,5)
        self.assertEqual(g.units[target].hp,before-1)
        # Once a legendary priest is obtained, highest rarity controls
        # conversion, never two independent damage portions.
        g.auction_awards[source]['rarity']='legendarna'
        old=g.units[target].hp
        g._heal(target,5)
        self.assertEqual(g.units[target].hp,old-5)
        g.assert_integrity()

    def test_A015_rare_globally_prevents_death_trigger(self):
        g=ready(93202)
        ward=award(g,'A015',1,zone='board')
        bomber=award(g,'A011',1,owner=1,zone='board',n=2)
        victim=place_basic(g,'S01',0)
        old=g.players[0].hp
        g._kill_batch([bomber])
        g._drain()
        self.assertEqual(g.players[0].hp,old)
        self.assertIn(victim,g.units)
        g.assert_integrity()

    def test_A015_legendary_globally_prevents_end_trigger(self):
        g=ready(93203)
        ward=award(g,'A015',2,zone='board')
        bow=place_basic(g,'S27',0)
        before=g.players[1].hp
        g.end_turn()
        self.assertEqual(g.players[1].hp,before)
        g.assert_integrity()

    def test_A016_rare_can_take_exact_enemy_top_deck_card_once(self):
        g=ready(93204)
        chosen=place_basic(g,'S01',1,'deck')
        # Make the enemy top card deterministic.
        deck=g.players[1].deck
        deck.remove(chosen);deck.append(chosen)
        src=award(g,'A016',1)
        g.play(src)
        own_target=g.pending.choices[0].target
        choose(g,'cart_draw',own_target)
        self.assertTrue(g.pending)
        choose(g,'cart_play',chosen)
        self.assertEqual(g.cards[chosen].owner,0)
        self.assertEqual(g.cards[chosen].zone,'board')
        self.assertIn(chosen,g.players[0].board)
        self.assertNotIn(chosen,g.players[1].deck)
        self.assertEqual(g.players[0].played_this_turn,True)
        g.assert_integrity()

    def test_A016_legendary_at_full_board_never_creates_sixth_unit(self):
        g=ready(93205)
        for cid in ('S01','S02','S03','S04'):
            place_basic(g,cid,0)
        src=award(g,'A016',2)
        original=list(g.players[0].deck)
        g.play(src)
        self.assertIsNone(g.pending)
        self.assertEqual(len(g.players[0].board),5)
        self.assertEqual(g.players[0].deck,original)
        g.assert_integrity()

    def test_A016_pending_selection_save_reload_does_not_duplicate(self):
        g=ready(93206)
        src=award(g,'A016',1)
        g.play(src)
        self.assertIsNotNone(g.pending)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cart_pending.json'
            save_match(g,path)
            loaded=load_match(path)
        self.assertEqual(loaded.pending.uid,src)
        target=loaded.pending.choices[0].target
        loaded.choose(0)
        self.assertIn(target,loaded.players[0].hand)
        if loaded.pending:
            loaded.choose(0)
        loaded.assert_integrity()

    def test_A018_vouchers_survive_save_and_advance_only_once(self):
        g=ready(93207)
        src=award(g,'A018',2)
        g.play(src)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'voucher.json'
            save_match(g,path)
            loaded=load_match(path)
        loaded.round=4
        state=auction.begin(loaded)
        self.assertEqual(state.phase,'picking')
        self.assertEqual(state.price,0)
        self.assertEqual(loaded.auction_vouchers[0],[])
        loaded.assert_integrity()


if __name__=='__main__':
    unittest.main()
