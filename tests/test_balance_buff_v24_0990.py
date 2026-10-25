"""Deterministic acceptance for the six user-approved auction buffs (v24/0.9.90)."""
import unittest

from game.core.engine import Match
from game.core.models import Card, CardDefinition, Unit, Choice
from game.core import auction_abilities as aa
from game.core.auction_catalog import CATALOG_V22, RARITIES, TRIGGER, live_variant, stats_v22


def ready(seed=2490):
    g=Match(seed,auctions_enabled=True,auction_catalog='v22',
            starting_compensation='coins')
    g.finish_mulligan(0,[])
    g.finish_mulligan(1,[])
    g.active=0;g.phase='turn'
    for p in g.players:p.turn_count=max(1,p.turn_count)
    return g


def award(g,aid,tier=0,owner=0,zone='hand',n=1):
    uid=f'AUCV24{n:03d}{aid}'
    archetype=CATALOG_V22[aid]
    atk,hp=stats_v22(aid,3)
    definition=CardDefinition(aid,archetype.name,'Ludzie',archetype.family,
        TRIGGER[archetype.trigger],atk,hp,
        live_variant('v22',aid,RARITIES[tier]),'v24',0,0)
    g.cards[uid]=Card(uid,definition,owner=owner,zone=zone)
    g.defs[uid]=definition
    g.auction_awards[uid]={'number':n,'level':1,'rarity':RARITIES[tier],
        'initial_rarity':RARITIES[tier],'atk':atk,'hp':hp,'archetype':aid,
        'purchase_round':3,'last_evolve_round':3,'ability_implemented':True}
    if aid in g.auction_bag:g.auction_bag.remove(aid)
    if zone=='board':
        g.units[uid]=Unit(uid,owner,atk,hp,hp,0,0)
        g._place_on_board(uid,owner)
    else:
        getattr(g.players[owner],zone).append(uid)
    return uid


def starter(g,cid,owner=0,zone='board'):
    for p in g.players:
        for z in ('board','hand','deck','grave'):
            if cid in getattr(p,z):getattr(p,z).remove(cid)
    if cid in g.bank:g.bank.remove(cid)
    c=g.cards[cid];c.owner=owner;c.zone=zone
    if zone=='board':
        g.units[cid]=Unit(cid,owner,c.attack,c.max_hp,c.max_hp,c.ability_level,0)
        g._place_on_board(cid,owner)
    else:
        getattr(g.players[owner],zone).append(cid)
    return cid


class ApprovedBuffs(unittest.TestCase):
    def test_a014_regen_one_random_or_all_and_stack(self):
        for tier,expected in [(1,1),(2,3)]:
            g=ready(2490+tier)
            src=award(g,'A014',tier,zone='board')
            starter(g,'S01');starter(g,'S02')
            aa.execute(g,src,'end',Choice('auto',None,''))
            affected=[uid for uid in g.players[0].board
                      if any(e.kind=='regen' and e.value==2 and e.remaining==2
                             for e in g.units[uid].effects)]
            self.assertEqual(len(affected),expected)
            if tier==2:
                aa.execute(g,src,'end',Choice('auto',None,''))
                self.assertEqual(sum(e.kind=='regen' for e in g.units[src].effects),2)

    def test_a003_skeleton_6_7_8_and_higher_hand_stats(self):
        for tier in range(3):
            g=ready(2500+tier)
            src=award(g,'A003',tier,zone='board')
            hand=starter(g,'S01',zone='hand')
            g.cards[hand].hand_turns=10
            options=aa.options(g,src,'death')
            self.assertEqual(options[0].mode,'v24_skeleton')
            aa.execute(g,src,'death',options[0])
            g._remove_unit(src,death=True)
            aa.resolve_wave_ops(g)
            sk=[uid for uid in g.players[0].board
                if g.cards[uid].definition.name=='Szkielet Matki Kości']
            self.assertEqual(len(sk),1)
            self.assertEqual(g.units[sk[0]].atk,max(6+tier,g.cards[hand].attack))
            self.assertEqual(g.units[sk[0]].max_hp,max(6+tier,g.cards[hand].max_hp))
            self.assertEqual(g.cards[sk[0]].definition.effect,'Bez zdolności')

    def test_a004_full_board_shield_and_stat_bonus(self):
        for tier in range(3):
            g=ready(2510+tier)
            src=award(g,'A004',tier,zone='board')
            for cid in ['S01','S02','S03','S04']:starter(g,cid)
            target=starter(g,'S12',1)
            choices=aa.options(g,src,'play')
            self.assertTrue(choices)
            choice=next((c for c in choices if c.target==target),choices[0])
            atk=g.units[src].atk
            aa.execute(g,src,'play',choice)
            self.assertEqual(g.units[src].shield,1)
            bonus=(0 if tier==0 else
                   (g.units[target].atk+1)//2 if tier==1 else g.units[target].atk)
            self.assertEqual(g.units[src].atk,atk+bonus)
            self.assertEqual(len(g.players[0].board),5)

    def test_a009_new_hand_receives_bonus_not_old_hand(self):
        g=ready(2520)
        src=award(g,'A009',1,zone='board')
        old=starter(g,'S01',zone='hand')
        acquired=starter(g,'S12',1,'hand')
        before=g.cards[acquired].attack
        g.auction_pending_targets[src]=[old]
        aa.execute(g,src,'auction_exchange_enemy',Choice('exchange_enemy',acquired,''))
        self.assertEqual(g.cards[acquired].owner,0)
        self.assertEqual(g.cards[acquired].attack,before+2)
        self.assertEqual(g.cards[old].owner,1)
        self.assertEqual(g.cards[old].attack,g.cards[old].definition.atk)

    def test_a016_full_board_legendary_fallback(self):
        g=ready(2530)
        src=award(g,'A016',2,zone='board')
        for cid in ['S01','S02','S03','S04']:starter(g,cid)
        target=starter(g,'S12',1)
        choice=next(c for c in aa.options(g,src,'play') if c.target==target)
        aa.execute(g,src,'play',choice)
        self.assertEqual(g.units[src].shield,1)
        self.assertEqual(g.units[src].atk,g.units[src].base_attack+g.units[target].atk)

    def test_a002_armor_only_once_and_evolution_delta(self):
        g=ready(2540);src=award(g,'A002',1,zone='board')
        aa.grant_general_defense(g,src)
        self.assertEqual(g.units[src].armor_perm,2)
        aa.grant_general_defense(g,src)
        self.assertEqual(g.units[src].armor_perm,2)
        g.auction_awards[src]['rarity']=RARITIES[2]
        aa.grant_general_defense(g,src)
        self.assertEqual(g.units[src].armor_perm,4)
        self.assertEqual(g.units[src].shield,1)

    def test_legacy_match_without_v24_flag_keeps_old_rules(self):
        g=ready(2550);del g.balance_patch_v24
        src=award(g,'A014',2,zone='board')
        self.assertEqual(aa.options(g,src,'end'),[])
        src2=award(g,'A002',1,zone='board',n=2)
        aa.grant_general_defense(g,src2)
        self.assertEqual(g.units[src2].armor_perm,0)


if __name__=='__main__':
    unittest.main()
