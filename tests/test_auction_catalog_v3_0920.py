"""Targeted 12×3 auction catalog v3 acceptance and integrity regressions."""
import unittest
from dataclasses import replace
from game.core.engine import Match
from game.core.models import Card,CardDefinition,Unit,Choice
from game.core.auction_catalog import CATALOG,RARITIES,stats,evolve
from game.core.auction import advance_rarity
from game.core.auction_abilities import options,execute,kind
from test_engine import setup_game,force_unit


def add_card(g,aid,tier=0,owner=0,board=False):
    name=CATALOG[aid].name
    uid=f'AUCTEST{len(g.auction_awards):03d}{aid}'
    d=CardDefinition(aid,name,'Ludzie',CATALOG[aid].family,
                     {'play':'Przy wystawieniu','end':'Na koniec tury',
                      'death':'Przy śmierci','passive':'Pasywna'}[CATALOG[aid].trigger],
                     CATALOG[aid].atk,11-CATALOG[aid].atk,
                     CATALOG[aid].abilities[tier],
                     'Karta aukcyjna bez skalowania w ręce',0,0)
    g.cards[uid]=Card(uid,d,owner=owner,zone='board' if board else 'hand')
    g.defs[uid]=d
    g.auction_awards[uid]={
        'number':1,'level':1,'rarity':RARITIES[tier],
        'initial_rarity':RARITIES[tier],'atk':d.atk,'hp':d.hp,
        'archetype':aid,'purchase_round':3,'last_evolve_round':3}
    g.players[owner].board.append(uid) if board else g.players[owner].hand.append(uid)
    if board:
        p=g.players[owner]
        g.units[uid]=Unit(uid,owner,d.atk,d.hp,d.hp,0,0)
    return uid


class AuctionCatalogV3(unittest.TestCase):
    def test_12_unique_definitions_and_stat_formula_all_rounds(self):
        self.assertEqual(len(CATALOG),12)
        for r in (3,6,9,12,30):
            for aid,d in CATALOG.items():
                atk,hp=stats(aid,r)
                self.assertEqual(atk+hp,r+8)
                self.assertEqual(atk,d.atk)
                self.assertGreater(hp,0)
                self.assertEqual(len(d.abilities),3)

    def test_rarity_only_changes_effect_not_atk_hp(self):
        g=setup_game(3201)
        x=add_card(g,'A005',0)
        orig=(g.cards[x].attack,g.cards[x].max_hp)
        advance_rarity(g,6)
        self.assertEqual(g.auction_awards[x]['rarity'],'rzadka')
        self.assertEqual((g.cards[x].attack,g.cards[x].max_hp),orig)
        advance_rarity(g,6)
        self.assertEqual(g.auction_awards[x]['rarity'],'rzadka')
        advance_rarity(g,9)
        self.assertEqual(g.auction_awards[x]['rarity'],'legendarna')
        self.assertEqual((g.cards[x].attack,g.cards[x].max_hp),orig)
        advance_rarity(g,12)
        self.assertEqual(g.auction_awards[x]['rarity'],'legendarna')

    def test_A005_coin_transfer_and_new_coins_every_tier(self):
        for tier,expected in [(0,(3,3)),(1,(5,4)),(2,(9,5))]:
            g=setup_game(3202+tier)
            uid=add_card(g,'A005',tier)
            g.players[1].coins=9
            before=g.players[0].coins
            g.players[0].played_this_turn=False
            g.play(uid)
            stolen,created=expected
            self.assertEqual(g.players[1].coins,9-stolen)
            self.assertEqual(g.players[0].coins,before+stolen+created)
            g.assert_integrity()

    def test_A006_silence_blocks_abilities_but_not_normal_attack(self):
        g=setup_game(3206)
        target=force_unit(g,'S115',1)
        uid=add_card(g,'A006',2,board=True)
        execute(g,uid,'play',Choice('auto',None,'auto'))
        self.assertTrue(g._disabled(target))
        self.assertEqual(g._double(target),False)
        self.assertTrue(g._has(target,'silence'))
        self.assertFalse(g._has(target,'stun'))

    def test_A008_exile_no_death_reward_and_preserves_70_base(self):
        g=setup_game(3208)
        target=force_unit(g,'S01',1)
        uid=add_card(g,'A008',1,board=True)
        before=g.players[0].coins
        execute(g,uid,'play',Choice('exile','S01','wygnaj'))
        self.assertNotIn('S01',g.units)
        self.assertNotIn('S01',g.players[1].grave)
        self.assertIn('S01',g.exiled)
        self.assertEqual(g.players[0].coins,before)
        g.assert_integrity()

    def test_A009_legendary_hand_swap_discards_to_grave(self):
        g=setup_game(3209)
        uid=add_card(g,'A009',2,board=True)
        hand0=list(g.players[0].hand)
        hand1=list(g.players[1].hand)
        execute(g,uid,'play',Choice('swap_all',None,'swap'))
        self.assertEqual(g.players[0].hand,hand1)
        self.assertEqual(g.players[1].hand,hand0)
        self.assertIsNotNone(g.pending)
        self.assertEqual(g.pending.owner,1)
        first=g.pending.choices[0].target
        g.choose(0)
        self.assertIn(first,g.players[1].grave)
        self.assertIn(first,g.cards)
        self.assertEqual(g.cards[first].owner,1)
        g.assert_integrity()

    def test_A010_rare_spawns_two_taunting_ephemeral_soldiers(self):
        g=setup_game(3210)
        uid=add_card(g,'A010',1,board=True)
        execute(g,uid,'end',Choice('summon',None,'summon'))
        soldiers=[x for x in g.players[0].board if x in g.ephemeral_ids]
        self.assertEqual(len(soldiers),2)
        for x in soldiers:
            self.assertEqual((g.units[x].atk,g.units[x].hp),(2,2))
            self.assertTrue(g._taunt(g.units[x]))
        g._remove_unit(soldiers[0],death=True)
        self.assertNotIn(soldiers[0],g.players[0].grave)
        self.assertIn(soldiers[0],g.vanished)
        g.assert_integrity()

    def test_A010_base_buff_permanent_and_cumulative(self):
        g=setup_game(3211)
        uid=add_card(g,'A010',0,board=True)
        before=(g.units[uid].atk,g.units[uid].max_hp,g.units[uid].hp)
        for _ in range(2):
            execute(g,uid,'end',Choice('grow',None,'grow'))
        after=(g.units[uid].atk,g.units[uid].max_hp,g.units[uid].hp)
        self.assertEqual(after,tuple(x+2 for x in before))

    def test_A012_hp_base_rare_legendary_ignores_defensive_armor(self):
        for tier in range(3):
            g=setup_game(3212+tier)
            uid=add_card(g,'A012',tier,board=True)
            g.players[0].hp=30
            g.players[1].hp=70
            g.players[1].hero_armor=100
            if tier==0:
                execute(g,uid,'play',Choice('auto',None,'auto'))
                self.assertEqual((g.players[0].hp,g.players[1].hp),(60,50))
            elif tier==1:
                execute(g,uid,'play',Choice('copy_to_self',None,'self'))
                self.assertEqual((g.players[0].hp,g.players[1].hp),(80,70))
            else:
                execute(g,uid,'play',Choice('auto',None,'drain'))
                self.assertEqual((g.players[0].hp,g.players[1].hp),(50,50))
            self.assertEqual(g.players[1].hero_armor,100)

    def test_A002_base_aura_affects_both_sides(self):
        g=setup_game(32022)
        ally=force_unit(g,'S01',0)
        foe=force_unit(g,'S02',1)
        uid=add_card(g,'A002',0,board=True)
        g._update_auras()
        self.assertEqual(ally.atk,g.cards['S01'].attack+1)
        self.assertEqual(foe.atk,g.cards['S02'].attack+1)
        g._remove_unit(uid,death=False)
        g._update_auras()
        self.assertEqual(ally.atk,g.cards['S01'].attack)
        self.assertEqual(foe.atk,g.cards['S02'].attack)

    def test_A002_rare_double_attack_and_damage_applies_only_to_chosen(self):
        g=setup_game(3220)
        ally=force_unit(g,'S09',0)
        other=force_unit(g,'S10',0)
        uid=add_card(g,'A002',1,board=True)
        execute(g,uid,'play',Choice('general_target','S09','select'))
        self.assertTrue(g._double(ally))
        self.assertFalse(g._double(other))
        self.assertEqual(ally.atk*2,2*ally.atk)

    def test_A004_base_copy_is_ephemeral_and_does_not_take_extra_normal_play(self):
        g=setup_game(3204)
        original=force_unit(g,'S09',0)
        uid=add_card(g,'A004',0,board=True)
        g.players[0].played_this_turn=True
        execute(g,uid,'play',Choice('copy','S09','copy'))
        copies=[x for x in g.ephemeral_ids if x in g.units]
        self.assertEqual(len(copies),1)
        self.assertEqual(g.units[copies[0]].base_attack,original.base_attack)
        self.assertTrue(g.players[0].played_this_turn)
        g.assert_integrity()

    def test_A007_rare_sacrifices_without_kill_reward(self):
        g=setup_game(3207)
        uid=add_card(g,'A007',1,board=True)
        g.players[0].hp=3
        coins=g.players[1].coins
        g._damage('hero:0',8)
        self.assertEqual(g.players[0].hp,20)
        self.assertNotIn(uid,g.units)
        self.assertIn(uid,g.auction_rescue_spent)
        self.assertEqual(g.players[1].coins,coins)
        g.assert_integrity()

    def test_A011_basic_death_damage_wave(self):
        g=setup_game(32111)
        uid=add_card(g,'A011',0,board=True)
        target=force_unit(g,'S01',1)
        old=target.hp
        g._kill_batch([uid])
        g._drain()
        self.assertLess(target.hp if 'S01' in g.units else 0,old)
        self.assertIn(uid,g.players[0].grave)
        g.assert_integrity()

    def test_A001_basic_death_kills_selected_enemy(self):
        g=setup_game(32101)
        uid=add_card(g,'A001',0,board=True)
        force_unit(g,'S01',1)
        g._kill_batch([uid])
        g._drain()
        self.assertTrue(g.pending is not None)
        choices=g.pending.choices
        ix=next(i for i,x in enumerate(choices) if x.target=='S01')
        g.choose(ix)
        self.assertIn('S01',g.players[1].grave)
        g.assert_integrity()

    def test_A003_basic_returns_card_from_grave(self):
        g=setup_game(3203)
        other=force_unit(g,'S01',0)
        g._remove_unit('S01',death=False)
        uid=add_card(g,'A003',0,board=True)
        g._kill_batch([uid])
        g._drain()
        self.assertTrue(g.pending is not None)
        i=next(i for i,x in enumerate(g.pending.choices) if x.target=='S01')
        g.choose(i)
        self.assertIn('S01',g.players[0].hand)
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
