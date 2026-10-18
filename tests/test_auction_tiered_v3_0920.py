"""High-risk rarities: every multi-step operation retains authoritative queue."""
import unittest
from game.core.models import Choice
from game.core.auction_abilities import execute, options, boosted_attack
from test_engine import setup_game,force_unit
from test_auction_catalog_v3_0920 import add_card


class TieredAuctionRegressions(unittest.TestCase):
    def test_A001_rare_capture_and_legendary_chain_source(self):
        for tier in (1,2):
            g=setup_game(4010+tier)
            u=add_card(g,'A001',tier,board=True)
            target=force_unit(g,'S01',1)
            g._kill_batch([u]);g._drain()
            self.assertTrue(g.pending)
            mode='capture_chain' if tier==2 else 'capture'
            choices=g.pending.choices
            idx=next(i for i,ch in enumerate(choices) if ch.mode==mode and ch.target=='S01')
            g.choose(idx)
            self.assertEqual(g.units['S01'].owner,0)
            self.assertIn('S01',g.players[0].board)
            self.assertNotIn('S01',g.players[1].board)
            self.assertEqual('S01' in g.auction_death_grants,tier==2)
            g.assert_integrity()

    def test_A003_legendary_revive_then_second_to_hand(self):
        g=setup_game(4013)
        for uid in ('S01','S02'):
            force_unit(g,uid,0)
            g._remove_unit(uid,death=False)
        source=add_card(g,'A003',2,board=True)
        g._kill_batch([source]);g._drain()
        index=next(i for i,c in enumerate(g.pending.choices)
                   if c.mode=='revive_pair' and c.target=='S01')
        g.choose(index)
        self.assertIn('S01',g.players[0].board)
        self.assertEqual(g.units['S01'].hp,g.units['S01'].max_hp)
        self.assertTrue(g.pending)
        self.assertEqual(g.pending.context,'auction_return_second')
        g.choose(next(i for i,c in enumerate(g.pending.choices)
                      if c.target=='S02'))
        self.assertIn('S02',g.players[0].hand)
        g.assert_integrity()

    def test_A004_rare_can_copy_enemy_and_legendary_inherits_buffs_and_shield(self):
        for tier in (1,2):
            g=setup_game(4014+tier)
            force_unit(g,'S01',1)
            g._add_effect('S01','atk',3,source='S02',positive=True)
            source=add_card(g,'A004',tier,board=True)
            execute(g,source,'play',Choice('copy','S01','copy'))
            ids=[x for x in g.ephemeral_ids if x in g.units]
            self.assertEqual(len(ids),1)
            new=g.units[ids[0]]
            self.assertEqual(new.owner,0)
            if tier==2:
                self.assertEqual(new.shield,1)
                self.assertEqual(new.atk,g.units['S01'].atk)
            else:
                self.assertEqual(new.shield,0)
                self.assertEqual(new.atk,new.base_attack)
            g.assert_integrity()

    def test_A006_rare_two_distinct_silence_targets(self):
        g=setup_game(4016)
        for uid in ('S01','S02'):force_unit(g,uid,1)
        source=add_card(g,'A006',1,board=True)
        execute(g,source,'play',Choice('silence','S01','first'))
        self.assertTrue(g.pending)
        self.assertEqual(g.pending.context,'auction_silence_next')
        g.choose(next(i for i,c in enumerate(g.pending.choices)
                      if c.target=='S02'))
        self.assertTrue(g._has(g.units['S01'],'silence'))
        self.assertTrue(g._has(g.units['S02'],'silence'))
        self.assertIsNone(g.pending)
        g.assert_integrity()

    def test_A007_legendary_rescue_and_stun(self):
        g=setup_game(4017)
        guard=add_card(g,'A007',2,board=True)
        force_unit(g,'S01',1)
        g.players[0].hp=2
        g._damage('hero:0',7)
        self.assertEqual(g.players[0].hp,25)
        self.assertTrue(g._has(g.units['S01'],'stun'))
        self.assertIn(guard,g.auction_rescue_spent)
        g.assert_integrity()

    def test_A008_legendary_three_exiles_plus_random_hand_card(self):
        g=setup_game(4018)
        for uid in ('S01','S02','S03'):force_unit(g,uid,1)
        hand_before=len(g.players[1].hand)
        source=add_card(g,'A008',2,board=True)
        execute(g,source,'play',Choice('exile','S01','first'))
        self.assertTrue(g.pending)
        for target in ('S02','S03'):
            index=next(i for i,c in enumerate(g.pending.choices) if c.target==target)
            g.choose(index)
        self.assertTrue({'S01','S02','S03'}.issubset(set(g.exiled)))
        self.assertEqual(len(g.players[1].hand),hand_before-1)
        self.assertIsNone(g.pending)
        g.assert_integrity()

    def test_A009_rare_picks_exact_enemy_hand_card(self):
        g=setup_game(4019)
        source=add_card(g,'A009',1,board=True)
        mine=g.players[0].hand[0]
        enemy=g.players[1].hand[0]
        execute(g,source,'play',Choice('exchange_own',mine,'own'))
        self.assertTrue(g.pending)
        ix=next(i for i,c in enumerate(g.pending.choices) if c.target==enemy)
        g.choose(ix)
        self.assertIn(enemy,g.players[0].hand)
        self.assertIn(mine,g.players[1].hand)
        self.assertEqual(g.cards[mine].owner,1)
        self.assertEqual(g.cards[enemy].owner,0)
        g.assert_integrity()

    def test_A002_legendary_grants_to_newly_played_ally(self):
        g=setup_game(4022)
        source=add_card(g,'A002',2,board=True)
        uid=g.players[0].hand[0]
        g.play(uid)
        self.assertIn(uid,g.auction_general_grants[source])
        self.assertTrue(boosted_attack(g,uid))
        self.assertTrue(g._double(g.units[uid]))
        self.assertTrue(g.units[uid].attacks<2)

    def test_A010_legendary_copies_stats_without_abilities(self):
        g=setup_game(4020)
        friend=force_unit(g,'S09',0)
        source=add_card(g,'A010',2,board=True)
        execute(g,source,'end',Choice('summon',None,'summon'))
        soldiers=[x for x in g.ephemeral_ids if x in g.units]
        self.assertEqual(len(soldiers),2)
        self.assertTrue(all(g.units[x].atk==friend.atk for x in soldiers))
        self.assertTrue(all(g.units[x].max_hp==friend.max_hp for x in soldiers))
        self.assertTrue(all(g.units[x].effects==[] for x in soldiers))
        g.assert_integrity()

    def test_A011_legendary_global_atomic_death(self):
        g=setup_game(4021)
        source=add_card(g,'A011',2,board=True)
        force_unit(g,'S01',0)
        force_unit(g,'S02',1)
        hero=g.players[1].hp
        g._kill_batch([source]);g._drain()
        self.assertNotIn('S01',g.units)
        self.assertNotIn('S02',g.units)
        self.assertEqual(g.players[1].hp,hero-10)
        self.assertEqual(len(g.players[0].board),0)
        self.assertEqual(len(g.players[1].board),0)
        g.assert_integrity()


if __name__=='__main__':
    unittest.main()
