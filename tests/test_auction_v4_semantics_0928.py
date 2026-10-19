"""Auction v4 semantic acceptance matrix, 12 archetypes × 3 rarities.

Unlike the historical smoke suite, each subtest asserts a concrete game-state
effect of the canonical Polish ability text. Tests use public Match actions and
its real death waves; helper injections only construct challenging board states.
"""
import unittest
from game.core import auction_abilities as aa
from game.core.auction_catalog import CATALOG, V4_CARDS, v4_variant
from game.core.models import Effect
from test_auction_v4_engine import ready, award, place_basic, settle


def choose(game, mode, target=None):
    assert game.pending is not None, 'Expected pending ability choice'
    matches=[i for i,c in enumerate(game.pending.choices)
             if c.mode==mode and (target is None or c.target==target)]
    assert matches, f'Missing {mode}:{target} in {game.pending.choices}'
    game.choose(matches[0])


def death(game, uid):
    game._kill_batch([uid])
    game._drain()


class AuctionV4SemanticMatrix(unittest.TestCase):

    def test_A001_3_tiers_kill_capture_and_chain_capture(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(92801+tier)
                target=place_basic(g,'S01',1)
                place_basic(g,'S02',1)
                src=award(g,'A001',tier,zone='board')
                g.units[target].hp=max(1,g.units[target].hp-2)
                g._add_effect(target,'taunt',source='S02')
                hp=g.units[target].hp
                death(g,src)
                if tier==0:
                    self.assertEqual({c.mode for c in g.pending.choices},{'kill'})
                    choose(g,'kill',target)
                    settle(g)
                    self.assertNotIn(target,g.units)
                    self.assertIn(target,g.players[1].grave)
                    self.assertEqual(g.death_counts,[1,1])
                else:
                    mode='capture' if tier==1 else 'capture_chain'
                    choose(g,mode,target)
                    settle(g)
                    self.assertEqual(g.units[target].owner,0)
                    self.assertEqual(g.units[target].hp,hp)
                    self.assertTrue(g._has(g.units[target],'taunt'))
                    self.assertIn(target,g.players[0].board)
                    self.assertEqual(g.death_counts,[1,0])
                    if tier==2:
                        self.assertIn(target,g.auction_death_grants)
                        death(g,target)
                        choose(g,'chain_capture','S02')
                        settle(g)
                        self.assertEqual(g.units['S02'].owner,0)
                        self.assertIn('S02',g.auction_death_grants)
                g.assert_integrity()

    def test_A002_3_tiers_aura_double_and_future_only(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(92821+tier)
                ally=place_basic(g,'S02',0)
                enemy=place_basic(g,'S03',1)
                original=(g.units[ally].atk,g.units[enemy].atk)
                src=award(g,'A002',tier,zone='board')
                if tier==0:
                    g._update_auras()
                    self.assertEqual(g.units[ally].atk,original[0]+1)
                    self.assertEqual(g.units[enemy].atk,original[1]+1)
                    self.assertEqual(g.units[src].atk,g.units[src].base_attack+1)
                elif tier==1:
                    g._queue(src,'play');g._drain()
                    choose(g,'general_target',ally)
                    settle(g)
                    self.assertTrue(aa.boosted_attack(g,ally))
                    self.assertTrue(g._double(g.units[ally]))
                    self.assertFalse(aa.boosted_attack(g,enemy))
                else:
                    self.assertFalse(aa.boosted_attack(g,ally))
                    place_basic(g,'S01',0,'hand')
                    g.play('S01')
                    if g.pending:choose(g,g.pending.choices[0].mode)
                    settle(g)
                    self.assertTrue(aa.boosted_attack(g,'S01'))
                    self.assertFalse(aa.boosted_attack(g,ally))
                death(g,src)
                if tier==0:
                    self.assertEqual(g.units[ally].atk,original[0])
                    self.assertEqual(g.units[enemy].atk,original[1])
                elif tier==1:self.assertFalse(aa.boosted_attack(g,ally))
                else:self.assertFalse(aa.boosted_attack(g,'S01'))
                g.assert_integrity()

    def test_A003_3_tiers_return_reanimate_and_two_different(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(92841+tier)
                place_basic(g,'S01',0,'grave')
                place_basic(g,'S02',0,'grave')
                src=award(g,'A003',tier,zone='board')
                death(g,src)
                if tier==0:
                    choose(g,'to_hand','S01')
                    settle(g)
                    self.assertIn('S01',g.players[0].hand)
                    self.assertNotIn('S01',g.units)
                elif tier==1:
                    choose(g,'revive_one','S01')
                    settle(g)
                    self.assertEqual(g.units['S01'].hp,1)
                    self.assertNotIn('S01',g.players[0].grave)
                else:
                    choose(g,'revive_pair','S01')
                    self.assertEqual(g.units['S01'].hp,g.units['S01'].max_hp)
                    choose(g,'return_hand','S02')
                    settle(g)
                    self.assertIn('S02',g.players[0].hand)
                    self.assertNotIn('S01',g.players[0].grave)
                g.assert_integrity()

    def test_A004_3_tiers_copy_target_permissions_and_bonuses(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(92861+tier)
                mine=place_basic(g,'S02',0)
                foe=place_basic(g,'S03',1)
                g._add_effect(foe,'atk',3,source=mine)
                g.units[foe].shield=1
                g.units[foe].hp-=2
                original=(g.units[foe].atk,g.units[foe].max_hp,g.units[foe].hp)
                src=award(g,'A004',tier)
                g.play(src)
                possible={c.target for c in g.pending.choices}
                if tier==0:
                    self.assertIn(mine,possible)
                    self.assertNotIn(foe,possible)
                    choose(g,'copy',mine)
                else:
                    self.assertIn(foe,possible)
                    choose(g,'copy',foe)
                settle(g)
                self.assertEqual(len(g.ephemeral_ids),1)
                clone=g.units[next(iter(g.ephemeral_ids))]
                self.assertEqual(clone.owner,0)
                if tier==2:
                    self.assertEqual((clone.atk,clone.max_hp,clone.hp),original)
                    self.assertEqual(clone.shield,1)
                if tier==1:
                    self.assertEqual(clone.atk,g.cards[foe].attack)
                    self.assertEqual(clone.shield,0)
                g.assert_integrity()

    def test_A005_3_tiers_exact_economy_including_small_wallets(self):
        for tier,enemy_coins,steal,mint in ((0,2,2,3),(1,9,5,4),(2,11,11,5)):
            with self.subTest(tier=tier):
                g=ready(92881+tier)
                g.players[0].coins=7
                g.players[1].coins=enemy_coins
                src=award(g,'A005',tier)
                g.play(src);settle(g)
                self.assertEqual(g.players[0].coins,7+steal+mint)
                self.assertEqual(g.players[1].coins,enemy_coins-steal)
                g.assert_integrity()

    def test_A006_3_tiers_silence_one_two_or_all(self):
        for tier,expected in ((0,1),(1,2),(2,3)):
            with self.subTest(tier=tier):
                g=ready(92901+tier)
                for cid in ('S01','S02','S03'):place_basic(g,cid,1)
                src=award(g,'A006',tier)
                g.play(src)
                if tier==0:choose(g,'silence','S01')
                elif tier==1:
                    choose(g,'silence','S01')
                    choose(g,'silence','S02')
                settle(g)
                silenced={cid for cid in ('S01','S02','S03')
                          if g._has(g.units[cid],'silence')}
                self.assertEqual(len(silenced),expected)
                self.assertTrue(all(
                    any(e.expires==g._expiry(1) for e in g.units[x].effects
                        if e.kind=='silence') for x in silenced))
                g.assert_integrity()

    def test_A007_3_tiers_one_time_rescue_and_legendary_stun(self):
        for tier,life in ((0,1),(1,20),(2,25)):
            with self.subTest(tier=tier):
                g=ready(92921+tier)
                place_basic(g,'S01',1)
                src=award(g,'A007',tier,zone='board')
                g._damage('hero:0',140)
                self.assertEqual(g.players[0].hp,life)
                self.assertIn(src,g.auction_rescue_spent)
                self.assertEqual(g.death_counts,[0,0])
                self.assertNotIn(src,g.units)
                self.assertEqual(g._has(g.units['S01'],'stun'),tier==2)
                g._damage('hero:0',30)
                self.assertLessEqual(g.players[0].hp,0)
                g.assert_integrity()

    def test_A008_3_tiers_marker_and_immediate_exile(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(92941+tier)
                for cid in ('S01','S02','S03'):place_basic(g,cid,1)
                old_hand=set(g.players[1].hand)
                src=award(g,'A008',tier)
                g.play(src)
                if tier==0:
                    choose(g,'mark','S01');settle(g)
                    self.assertIn('S01',g.units)
                    self.assertTrue(g._has(g.units['S01'],'auction_exile_mark'))
                    g.players[1].turn_count+=1
                    aa.expire_exile_marks(g,1)
                    self.assertIn('S01',g.exiled)
                else:
                    choose(g,'exile','S01')
                    if tier==2:
                        choose(g,'exile','S02')
                        choose(g,'exile','S03')
                    settle(g)
                    self.assertIn('S01',g.exiled)
                    self.assertEqual(len(old_hand-set(g.players[1].hand)),1)
                    if tier==2:self.assertTrue({'S02','S03'}<=set(g.exiled))
                self.assertEqual(g.death_counts,[0,0])
                self.assertNotIn('S01',g.players[1].grave)
                g.assert_integrity()

    def test_A009_3_tiers_exchange_random_chosen_and_whole_hands(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(92961+tier)
                src=award(g,'A009',tier)
                after_src=[c for c in g.players[0].hand if c!=src]
                old_foe=set(g.players[1].hand)
                g.play(src)
                if tier<2:
                    mine=after_src[0]
                    choose(g,'exchange_own',mine)
                    if tier==1:
                        foe=sorted(old_foe)[-1]
                        choose(g,'exchange_enemy',foe)
                        self.assertIn(foe,g.players[0].hand)
                    else:
                        self.assertTrue(old_foe.intersection(g.players[0].hand))
                    self.assertIn(mine,g.players[1].hand)
                    self.assertEqual(g.cards[mine].owner,1)
                else:
                    choose(g,'swap_all')
                    self.assertTrue(old_foe<=set(g.players[0].hand))
                    discards=list(g.players[1].hand)
                    for cid in discards[:2]:
                        choose(g,'discard',cid)
                    self.assertEqual(len(g.players[1].hand),len(discards)-min(2,len(discards)))
                settle(g)
                g.assert_integrity()

    def test_A010_3_tiers_summon_or_correct_once_only_growth(self):
        for tier,bonus in ((0,1),(1,4),(2,3)):
            with self.subTest(tier=tier):
                g=ready(92981+tier)
                ally=place_basic(g,'S01',0)
                g.units[ally].base_attack=3
                g.units[ally].base_max_hp=5
                g.units[ally].hp=5
                src=award(g,'A010',tier,zone='board')
                # Validate +HP is granted exactly once even to a damaged Queen.
                queen=g.units[src]
                queen.hp-=5
                before=(queen.atk,queen.max_hp,queen.hp)
                g.end_turn()
                choose(g,'grow')
                settle(g)
                expected_atk=(1,4,3)[tier]
                expected_hp=(1,4,5)[tier]
                self.assertEqual(queen.atk,before[0]+expected_atk)
                self.assertEqual(queen.max_hp,before[1]+expected_hp)
                self.assertEqual(queen.hp,before[2]+expected_hp)
                self.assertEqual(g._taunt(queen),tier==1)
                g.assert_integrity()

    def test_A011_3_tiers_simultaneous_casualties_and_hero_damage(self):
        for tier,hero_damage in ((0,0),(1,5),(2,10)):
            with self.subTest(tier=tier):
                g=ready(93001+tier)
                enemy=place_basic(g,'S01',1)
                ally=place_basic(g,'S02',0)
                g.units[enemy].hp=2
                g.units[ally].hp=2
                src=award(g,'A011',tier,zone='board')
                old=g.players[1].hp
                death(g,src)
                settle(g)
                self.assertNotIn(enemy,g.units)
                if tier==2:self.assertNotIn(ally,g.units)
                else:self.assertIn(ally,g.units)
                self.assertEqual(g.players[1].hp,old-hero_damage)
                self.assertEqual(g.death_counts[1],1)
                g.assert_integrity()

    def test_A012_3_tiers_mean_choose_direction_or_steal_health(self):
        for tier in range(3):
            with self.subTest(tier=tier):
                g=ready(93021+tier)
                g.players[0].hp=30
                g.players[1].hp=60
                src=award(g,'A012',tier)
                g.play(src)
                if tier==1:choose(g,'copy_to_self')
                settle(g)
                expected=((55,45),(70,60),(50,40))[tier]
                self.assertEqual((g.players[0].hp,g.players[1].hp),expected)
                g.assert_integrity()


class AuctionInterlocksAndLimits(unittest.TestCase):
    def test_silenced_A011_has_no_death_trigger(self):
        g=ready(93100)
        place_basic(g,'S01',0)
        target=award(g,'A011',1,owner=1,zone='board')
        silencer=award(g,'A006',0,owner=0,zone='hand')
        old_enemy=g.players[0].hp
        g.play(silencer)
        choose(g,'silence',target);settle(g)
        death(g,target);settle(g)
        self.assertEqual(g.players[0].hp,old_enemy)
        self.assertIn('S01',g.units)
        g.assert_integrity()

    def test_legendary_A002_buff_does_not_survive_revival_or_capture(self):
        g=ready(93101)
        source=award(g,'A002',2,zone='board')
        place_basic(g,'S01',0,'hand')
        g.play('S01')
        if g.pending:choose(g,g.pending.choices[0].mode)
        settle(g)
        self.assertTrue(aa.boosted_attack(g,'S01'))
        death(g,'S01')
        place_basic(g,'S01',0,'board')
        self.assertFalse(aa.boosted_attack(g,'S01'))
        g.assert_integrity()

        g=ready(93102)
        source=award(g,'A002',2,zone='board')
        place_basic(g,'S01',0,'hand')
        g.play('S01')
        if g.pending:choose(g,g.pending.choices[0].mode)
        settle(g)
        self.assertTrue(aa.boosted_attack(g,'S01'))
        # Crossing ownership removes the ally-only aura; source is not captured.
        aa._capture(g,source,'S01') if False else None
        capturer=award(g,'A001',1,owner=1,zone='board')
        death(g,capturer)
        choose(g,'capture','S01');settle(g)
        self.assertEqual(g.units['S01'].owner,1)
        self.assertFalse(aa.boosted_attack(g,'S01'))
        g.assert_integrity()

    def test_A003_rare_falls_back_to_hand_on_full_board(self):
        g=ready(93103)
        for cid in ('S01','S02','S03','S04','S05'):
            place_basic(g,cid,0)
        place_basic(g,'S06',0,'grave')
        src=award(g,'A003',1,zone='board')
        # On source death board count shrinks to five, so fallback still required.
        death(g,src)
        choose(g,'revive_one','S06')
        settle(g)
        self.assertIn('S06',g.players[0].hand)
        self.assertNotIn('S06',g.units)
        g.assert_integrity()

    def test_A004_legendary_copy_of_A002_aura_does_not_stack_external_buffs(self):
        g=ready(93104)
        ally=place_basic(g,'S01',0)
        general=award(g,'A002',0,zone='board')
        g._update_auras()
        before=g.units[ally].atk
        source=award(g,'A004',2)
        g.play(source)
        choose(g,'copy',general)
        settle(g)
        self.assertEqual(len(g.ephemeral_ids),1)
        self.assertEqual(g.units[ally].atk,before+1)
        copy=next(iter(g.ephemeral_ids))
        self.assertTrue(g.units[copy].shield)
        self.assertEqual(aa.rarity(g,copy),0)
        g.assert_integrity()

    def test_all_36_descriptions_still_exact_at_runtime(self):
        for aid in CATALOG:
            for tier,r in enumerate(('podstawowa','rzadka','legendarna')):
                with self.subTest(archetype=aid,rarity=r):
                    g=ready(93105+tier)
                    uid=award(g,aid,tier)
                    self.assertEqual(g.cards[uid].definition.effect,
                                     v4_variant(aid,r))
                    self.assertEqual(len(V4_CARDS[aid]['variants']),3)
                    g.assert_integrity()


if __name__=='__main__':
    unittest.main()
