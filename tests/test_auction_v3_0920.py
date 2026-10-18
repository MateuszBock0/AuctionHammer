"""Acceptance tests for the real twelve-card auction catalog (draft v3)."""
import os
import unittest
from dataclasses import asdict
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

from game.core.engine import Match
from game.core.models import Card, CardDefinition
from game.core.auction_catalog import CATALOG,BY_ID,RARITIES,stats
from game.core.ai import ComputerOpponent
from game.core.audit import make_report,verify_replay
from game.core.auction_skills import evolve
from test_engine import force_unit


def game_for(seed=920):
    g=Match(seed,auctions_enabled=True,auction_catalog_mode='v3')
    g.finish_mulligan(0,[]);g.finish_mulligan(1,[])
    g.phase='turn';g.active=0
    g.players[0].turn_count=max(1,g.players[0].turn_count)
    return g


def add(g,archetype,rarity='podstawowa',owner=0,board=False):
    item=BY_ID[archetype]
    uid=f'AUC_TEST_{archetype}_{owner}_{len(g.auction_awards)}'
    faction={'play':'Elfy','death':'Potwory','end':'Krasnoludy','passive':'Ludzie'}[item.trigger]
    trigger={'play':'Przy wystawieniu','death':'Przy śmierci','end':'Na koniec tury','passive':'Pasywna'}[item.trigger]
    atk,hp=stats(item,3)
    d=CardDefinition(uid,item.name,faction,'Prowokacja',trigger,atk,hp,
                     item.basic,'Brak skalowania',0,0)
    c=Card(uid,d,owner=owner,zone='hand')
    g.cards[uid]=c;g.defs[uid]=d;g.players[owner].hand.append(uid)
    g.auction_awards[uid]={'archetype':archetype,'number':1,'completed_round':3,
         'rarity':rarity,'level':1,'atk':atk,'hp':hp,'abilities':(archetype,)}
    if board:
        g.players[owner].hand.remove(uid)
        g.players[owner].board.append(uid)
        c.zone='board'
        from game.core.models import Unit
        g.units[uid]=Unit(uid,owner,atk,hp,hp,0,g.players[owner].turn_count-1)
        g._update_auras()
    return uid


def choose(g,mode=None,target=None):
    if not g.pending:raise AssertionError('No pending choice')
    for i,opt in enumerate(g.pending.choices):
        if (mode is None or opt.mode==mode) and (target is None or opt.target==target):
            g.choose(i);return
    raise AssertionError((mode,target,[asdict(c) for c in g.pending.choices]))


class CatalogTests(unittest.TestCase):
    def test_all_12_and_36_versions(self):
        self.assertEqual(len(CATALOG),12)
        self.assertEqual(len({x.ident for x in CATALOG}),12)
        for n in CATALOG:
            for r in (3,6,9,12):
                a,h=stats(n,r)
                self.assertEqual(a+h,r+8)
                self.assertEqual(a,n.atk_at_round3)
                self.assertGreater(h,0)
            self.assertTrue(n.basic and n.rare and n.legendary)

    def test_three_distinct_draft_offers(self):
        g=game_for(92001)
        for _ in range(6):g.end_turn()
        self.assertEqual(g.phase,'auction')
        self.assertEqual(len(g.auction.offers),3)
        self.assertEqual(len({o.archetype for o in g.auction.offers}),3)
        self.assertTrue(all(o.archetype in BY_ID for o in g.auction.offers))
        self.assertTrue(all(o.atk+o.hp==11 for o in g.auction.offers))
        g.assert_integrity()

    def test_rarity_evolution_exactly_after_three_full_rounds(self):
        g=game_for(92002)
        uid=add(g,'A005','podstawowa')
        evolve(g,5)
        self.assertEqual(g.auction_awards[uid]['rarity'],'podstawowa')
        evolve(g,6)
        self.assertEqual(g.auction_awards[uid]['rarity'],'rzadka')
        evolve(g,9)
        self.assertEqual(g.auction_awards[uid]['rarity'],'legendarna')
        evolve(g,12)
        self.assertEqual(g.auction_awards[uid]['rarity'],'legendarna')
        self.assertEqual(g.cards[uid].max_hp,10)
        g.assert_integrity()


class AbilityTests(unittest.TestCase):
    def test_a005_steals_and_mints_separately(self):
        g=game_for(92005);uid=add(g,'A005','rzadka')
        g.players[1].coins=7;g.players[0].coins=2
        g.play(uid)
        self.assertEqual(g.players[1].coins,3)
        self.assertEqual(g.players[0].coins,10)  # 4 stolen + 4 new

    def test_a006_rare_two_silences_and_no_third(self):
        g=game_for(92006)
        force_unit(g,'S09',1);force_unit(g,'S10',1);force_unit(g,'S11',1)
        uid=add(g,'A006','rzadka')
        g.play(uid)
        choose(g,'silence','S09')
        choose(g,'silence','S10')
        self.assertFalse(g.pending)
        self.assertTrue(any(e.kind=='silence' for e in g.units['S09'].effects))
        self.assertTrue(any(e.kind=='silence' for e in g.units['S10'].effects))
        self.assertFalse(any(e.kind=='silence' for e in g.units['S11'].effects))

    def test_a008_rare_exile_no_death_reward(self):
        g=game_for(92008)
        force_unit(g,'S01',1)
        target=add(g,'A008','rzadka')
        old=g.players[0].coins
        g.play(target);choose(g,'exile','S01')
        self.assertNotIn('S01',g.units)
        self.assertIn('S01',g.excluded)
        self.assertEqual(g.players[0].coins,old)
        g.assert_integrity()

    def test_a009_basic_hand_exchange(self):
        g=game_for(92009)
        uid=add(g,'A009')
        g.play(uid)
        self.assertTrue(g.pending)
        selected=g.players[0].hand[0]
        other=g.players[1].hand[0]
        choose(g,'swap_own',selected)
        choose(g,'swap_own',selected)
        self.assertEqual(g.cards[selected].owner,1)
        self.assertEqual(g.cards[other].owner,0) if len(g.players[1].hand)==1 else None
        g.assert_integrity()

    def test_a012_base_average_then_healing(self):
        g=game_for(92012)
        g.players[0].hp=30;g.players[1].hp=80
        uid=add(g,'A012')
        g.play(uid)
        self.assertEqual(g.players[0].hp,65)
        self.assertEqual(g.players[1].hp,55)

    def test_a012_rare_direction_is_not_a_swap(self):
        g=game_for(92013)
        g.players[0].hp=30;g.players[1].hp=80
        uid=add(g,'A012','rzadka')
        g.play(uid);choose(g,'copy_own_hp')
        self.assertEqual(g.players[0].hp,90)
        self.assertEqual(g.players[1].hp,80)

    def test_a002_basic_aura_both_sides(self):
        g=game_for(92014)
        ally=force_unit(g,'S09',0);enemy=force_unit(g,'S10',1)
        a,b=ally.atk,enemy.atk
        uid=add(g,'A002',board=True)
        g._update_auras()
        self.assertEqual(ally.atk,a+1)
        self.assertEqual(enemy.atk,b+1)
        self.assertGreater(g.units[uid].atk,2)
        g._remove_unit(uid,death=False)
        g._update_auras()
        self.assertEqual(ally.atk,a)
        self.assertEqual(enemy.atk,b)

    def test_a002_rare_double_attack_only_selected_ally(self):
        g=game_for(92015)
        ally=force_unit(g,'S09',0);other=force_unit(g,'S10',0)
        uid=add(g,'A002','rzadka',board=True)
        g.auction_awards[uid]['beneficiary']='S09'
        self.assertTrue(g._double(ally))
        self.assertFalse(g._double(other))

    def test_a003_base_returns_starter_from_grave(self):
        g=game_for(92016)
        force_unit(g,'S09',0)
        g._kill_batch(['S09'])
        uid=add(g,'A003',board=True)
        g._kill_batch([uid]);choose(g,'grave_hand','S09')
        self.assertIn('S09',g.players[0].hand)
        self.assertNotIn('S09',g.players[0].grave)
        g.assert_integrity()

    def test_a004_creates_unique_ephemeral_playable_copy(self):
        g=game_for(92017)
        force_unit(g,'S09',0)
        uid=add(g,'A004')
        g.play(uid);choose(g,'copy','S09')
        clones=list(g.ephemerals)
        self.assertEqual(len(clones),1)
        clone=clones[0]
        self.assertIn(clone,g.units)
        self.assertEqual(g.units[clone].atk,g.cards['S09'].definition.atk)
        g.assert_integrity()
        g._kill_batch([clone]);g._drain()
        self.assertNotIn(clone,g.cards)
        g.assert_integrity()

    def test_a007_saves_hero_once_and_sacrifices(self):
        g=game_for(92018)
        uid=add(g,'A007','rzadka',board=True)
        g.players[0].hp=5
        g._damage('hero:0',8)
        self.assertEqual(g.players[0].hp,20)
        self.assertNotIn(uid,g.units)
        self.assertTrue(g.auction_awards[uid]['rescue_used'])

    def test_a010_queen_stacking_is_on_board_not_hand(self):
        g=game_for(92019)
        uid=add(g,'A010','rzadka',board=True)
        unit=g.units[uid]
        old=(unit.atk,unit.max_hp)
        g._execute(uid,'end',__import__('game.core.models',fromlist=['Choice']).Choice('self_buff',None,'BUFF'))
        self.assertEqual(unit.atk,old[0]+4)
        self.assertEqual(unit.max_hp,old[1]+4)
        g._execute(uid,'end',__import__('game.core.models',fromlist=['Choice']).Choice('self_buff',None,'BUFF'))
        self.assertEqual(unit.atk,old[0]+8)
        self.assertEqual(unit.max_hp,old[1]+8)

    def test_a011_base_damage_enemy_board_on_death(self):
        g=game_for(92020)
        target=force_unit(g,'S09',1)
        uid=add(g,'A011',board=True)
        old=g.units['S09'].hp
        g._kill_batch([uid]);g._drain()
        self.assertTrue('S09' not in g.units or g.units['S09'].hp<=old-5)

    def test_a001_base_kill_enemy_on_death(self):
        g=game_for(92021)
        force_unit(g,'S09',1)
        uid=add(g,'A001',board=True)
        g._kill_batch([uid]);choose(g,'kill','S09')
        self.assertNotIn('S09',g.units)


if __name__=='__main__':unittest.main()