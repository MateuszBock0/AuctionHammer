"""Integration acceptance tests for AuctionHammer auction cards v4.

The established v3 rules remain available for old saves and audits.
These tests exercise Match commands and its real trigger/death-wave pipeline.
"""
import tempfile
import unittest
from pathlib import Path
from game.core.engine import Match
from game.core.models import Card,CardDefinition,Unit
from game.core.auction_catalog import CATALOG,V4_CARDS,v4_variant,stats_v4
from game.core.auction_abilities import rarity
from game.core.persistence import save_match,load_match
from game.core.audit import state_snapshot,make_report,verify_replay


RARITIES=('podstawowa','rzadka','legendarna')


def ready(seed=2401):
    game=Match(seed,auctions_enabled=True,auction_catalog='v4')
    game.finish_mulligan(0,[])
    game.finish_mulligan(1,[])
    game.active=0
    game.phase='turn'
    game.players[0].turn_count=max(1,game.players[0].turn_count)
    game.players[1].turn_count=max(1,game.players[1].turn_count)
    return game


def place_basic(game,cid,owner=0,zone='board'):
    card=game.cards[cid]
    for p in game.players:
        for attr in ('hand','deck','grave','board'):
            entries=getattr(p,attr)
            if cid in entries:entries.remove(cid)
    if cid in game.bank:game.bank.remove(cid)
    card.owner=owner;card.zone=zone
    getattr(game.players[owner],zone if zone!='board' else 'board').append(cid)
    if zone=='board':
        game.units[cid]=Unit(cid,owner,card.attack,card.max_hp,card.max_hp,
                             card.ability_level,0)
    return cid


def award(game,aid,tier=0,owner=0,zone='hand',number=1):
    uid=f'AUC{number:03d}{aid}'
    atk,hp=stats_v4(aid,3)
    original=CATALOG[aid]
    definition=CardDefinition(aid,original.name,'Ludzie',original.family,
                   {'play':'Przy wystawieniu','death':'Przy śmierci',
                    'end':'Na koniec tury','passive':'Pasywna'}[original.trigger],
                   atk,hp,v4_variant(aid,RARITIES[tier]),'v4',0,0)
    card=Card(uid,definition,owner=owner,zone=zone)
    game.cards[uid]=card;game.defs[uid]=definition
    # This synthetic purchase consumes its archetype just like real auction.pick.
    if game.auction_catalog=='v4' and aid in game.auction_bag:
        game.auction_bag.remove(aid)
    game.auction_awards[uid]={'number':number,'level':1,
        'rarity':RARITIES[tier],'initial_rarity':RARITIES[tier],
        'atk':atk,'hp':hp,'archetype':aid,'purchase_round':3,
        'last_evolve_round':3,'ability_implemented':True}
    game.players[owner].__getattribute__(zone).append(uid)
    if zone=='board':
        game.units[uid]=Unit(uid,owner,atk,hp,hp,0,0)
    return uid


def settle(game):
    while game.pending is not None:
        game.choose(0)
    game.assert_integrity()


class AuctionV4DataTests(unittest.TestCase):
    def test_all_36_canonical_variants_and_purchase_scaling(self):
        self.assertEqual(len(V4_CARDS),12)
        for aid in V4_CARDS:
            for tier in RARITIES:
                self.assertTrue(v4_variant(aid,tier))
            for round_number in (3,6,9,12,120):
                atk,hp=stats_v4(aid,round_number)
                self.assertEqual(atk+hp,round_number+8)
                self.assertEqual(atk,V4_CARDS[aid]['stats_at_round_3_example']['atk']+
                                 (round_number-3)//3)

    def test_legacy_v3_is_not_activated(self):
        m=Match(2402,auctions_enabled=True,auction_catalog='v3')
        self.assertEqual(m.auction_catalog,'v3')
        self.assertEqual(m.cards['S01'].definition.id,'S01')

    def test_full_auction_and_ability_metadata(self):
        m=ready(2403)
        m.round=4
        from game.core import auction
        state=auction.begin(m)
        self.assertEqual(len({x.archetype for x in state.offers}),3)
        self.assertTrue(all(x.atk+x.hp==11 for x in state.offers))
        m.auction_pass(m.auction.turn)
        m.auction_pass(m.auction.turn)
        picked=state.offers[0].uid
        m.auction_pick(m.auction.turn,picked)
        self.assertEqual(m.cards[picked].definition.effect,
                         v4_variant(state.offers[0].archetype,state.offers[0].rarity))
        self.assertTrue(m.auction_awards[picked]['ability_implemented'])
        m.auction_pick(m.auction.turn,state.offers[1].uid)
        m.assert_integrity()


class AuctionV4PlayAbilities(unittest.TestCase):
    def test_a005_all_three_tiers_generate_and_steal_money(self):
        for tier,stolen,new in ((0,3,3),(1,5,4),(2,9,5)):
            with self.subTest(tier=tier):
                g=ready(2410+tier)
                uid=award(g,'A005',tier)
                g.players[1].coins=9
                initial=g.players[0].coins
                g.play(uid)
                settle(g)
                self.assertEqual(g.players[1].coins,9-stolen)
                self.assertEqual(g.players[0].coins,initial+stolen+new)

    def test_a012_base_and_two_rare_directions_and_legendary(self):
        for tier,choice_index,expected in ((0,None,(60,50)),
                                             (1,0,(80,80)),
                                             (1,1,(60,40)),
                                             (2,None,(60,20))):
            with self.subTest(tier=tier,mode=choice_index):
                g=ready(2420+tier)
                uid=award(g,'A012',tier)
                g.players[0].hp=50;g.players[1].hp=40
                g.play(uid)
                if tier==1:
                    self.assertIsNotNone(g.pending)
                    g.choose(choice_index)
                settle(g)
                observed=(g.players[0].hp,g.players[1].hp)
                if tier==0:self.assertEqual(observed,(55,45))
                elif tier==1 and choice_index==0:self.assertEqual(observed,(50,40))
                elif tier==1:self.assertEqual(observed,(60,50))
                else:self.assertEqual(observed,(70,20))

    def test_a006_silences_enemies(self):
        for tier,count in ((0,1),(1,2),(2,3)):
            with self.subTest(tier=tier):
                g=ready(2430+tier)
                targets=['S01','S02','S03']
                for uid in targets:place_basic(g,uid,1)
                source=award(g,'A006',tier)
                g.play(source)
                # The rare card offers a legitimate STOP choice or a second
                # enemy: select the second enemy for this two-target regression.
                if tier==1:
                    self.assertIsNotNone(g.pending)
                    g.choose(0)
                    self.assertIsNotNone(g.pending)
                    second=next(i for i,c in enumerate(g.pending.choices)
                                if c.mode=='silence')
                    g.choose(second)
                settle(g)
                self.assertEqual(sum(g._has(g.units[uid],'silence') for uid in targets),count)

    def test_a004_copy_is_ephemeral_and_not_reentrant(self):
        g=ready(2440)
        place_basic(g,'S01',0)
        src=award(g,'A004',1)
        g.play(src)
        self.assertIsNotNone(g.pending)
        g.choose(0)
        settle(g)
        copies=list(g.ephemeral_ids)
        self.assertEqual(len(copies),1)
        copy=copies[0]
        self.assertIn(copy,g.units)
        g._kill_batch([copy])
        g._drain()
        self.assertIn(copy,g.vanished)
        self.assertNotIn(copy,g.players[0].grave)
        g.assert_integrity()

    def test_a009_legendary_swaps_hands_and_enemy_discards(self):
        g=ready(2450)
        src=award(g,'A009',2)
        old0=set(g.players[0].hand)
        old1=set(g.players[1].hand)
        g.play(src)
        self.assertIsNotNone(g.pending)
        g.choose(0)  # Explicitly resolve legendary swap mode
        self.assertTrue(old1.issubset(set(g.players[0].hand)))
        self.assertEqual(g.pending.owner,1)
        settle(g)
        self.assertEqual(len(g.players[1].hand),max(0,len(old0)-1-2))
        g.assert_integrity()

    def test_a008_rare_exiles_without_death(self):
        g=ready(2460)
        place_basic(g,'S01',1)
        source=award(g,'A008',1)
        g.play(source)
        settle(g)
        self.assertIn('S01',g.exiled)
        self.assertNotIn('S01',g.players[1].grave)
        g.assert_integrity()


class AuctionV4DeathAndPassive(unittest.TestCase):
    def test_a001_death_capture_preserves_unit_owner(self):
        g=ready(2470)
        enemy=place_basic(g,'S01',1)
        src=award(g,'A001',1,zone='board')
        g._kill_batch([src])
        g._drain()
        self.assertIsNotNone(g.pending)
        capture=next(i for i,x in enumerate(g.pending.choices)
                     if x.mode=='capture' and x.target==enemy)
        g.choose(capture)
        settle(g)
        self.assertEqual(g.units[enemy].owner,0)
        self.assertIn(enemy,g.players[0].board)

    def test_a003_returns_a_card_from_grave(self):
        g=ready(2480)
        place_basic(g,'S01',0,'grave')
        src=award(g,'A003',0,zone='board')
        g._kill_batch([src]);g._drain()
        settle(g)
        self.assertIn('S01',g.players[0].hand)

    def test_a007_saves_hero_once_at_each_rarity(self):
        for tier,life in ((0,1),(1,20),(2,25)):
            with self.subTest(tier=tier):
                g=ready(2490+tier)
                src=award(g,'A007',tier,zone='board')
                g._damage('hero:0',180)
                self.assertEqual(g.players[0].hp,life)
                self.assertNotIn(src,g.units)
                self.assertIn(src,g.auction_rescue_spent)

    def test_a010_queen_summons_or_accumulates(self):
        g=ready(2500)
        src=award(g,'A010',0,zone='board')
        g.end_turn()
        settle(g)
        self.assertEqual(g.units[src].atk,4)
        self.assertEqual(sum(uid.startswith('SUM') for uid in g.players[0].board),1)

    def test_a011_legendary_kills_all_others_in_atomic_wave(self):
        g=ready(2510)
        place_basic(g,'S01',1)
        place_basic(g,'S02',0)
        src=award(g,'A011',2,zone='board')
        g._kill_batch([src]);g._drain()
        settle(g)
        self.assertNotIn('S01',g.units)
        self.assertNotIn('S02',g.units)
        self.assertEqual(g.players[1].hp,90)

    def test_a002_basic_aura_applies_to_both_players(self):
        g=ready(2520)
        place_basic(g,'S01',0);place_basic(g,'S02',1)
        src=award(g,'A002',0,zone='board')
        g._update_auras()
        self.assertEqual(g.units['S01'].aura_atk,1)
        self.assertEqual(g.units['S02'].aura_atk,1)
        self.assertEqual(g.units[src].aura_atk,1)
        g._kill_batch([src])
        self.assertEqual(g.units['S01'].aura_atk,0)


class AuctionV4Persistence(unittest.TestCase):
    def test_save_reload_with_v4_token(self):
        g=ready(2530)
        place_basic(g,'S01',0)
        src=award(g,'A004',0)
        g.play(src);g.choose(0)
        settle(g)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'v4.json'
            save_match(g,path)
            loaded=load_match(path)
        self.assertEqual(state_snapshot(g),state_snapshot(loaded))
        loaded.assert_integrity()


if __name__=='__main__':
    unittest.main()
