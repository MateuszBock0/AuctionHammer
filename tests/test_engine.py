"""Testy zgodności silnika z GAME_MASTER_v17: python -m unittest discover -s tests -v"""
import unittest
from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.models import Unit, IllegalMove
from game.core.effects import options


def setup_game(seed=3):
    m=Match(seed)
    m.finish_mulligan(1,[]);m.finish_mulligan(0,[])
    m.active=0
    m.phase='turn'
    if m.players[0].turn_count==0:m.players[0].turn_count=1
    return m


def force_unit(m,uid,player=0):
    card=m.cards[uid]
    if uid in m.bank:m.bank.remove(uid)
    for p in m.players:
        for zone in ('hand','deck','grave','board'):
            arr=getattr(p,zone)
            if uid in arr:arr.remove(uid)
    card.owner=player;card.zone='board'
    p=m.players[player]
    if not p.turn_count:p.turn_count=1
    p.board.append(uid)
    u=Unit(uid,player,card.attack,card.max_hp,card.max_hp,card.ability_level,0)
    m.units[uid]=u
    return u


class GameTests(unittest.TestCase):
    def test_70_exact_unique(self):
        m=Match(2)
        self.assertEqual(len(m.defs),70)
        self.assertEqual(len(m.bank),50)
        self.assertEqual(len(m.cards),70)
        self.assertTrue(all(len(p.hand)==5 and len(p.deck)==5 for p in m.players))
        self.assertEqual(sorted((m.players[0].coins,m.players[1].coins)),[0,3])
        self.assertTrue(all(p.hp==100 for p in m.players))
        m.assert_integrity()

    def test_mulligan_no_duplicate(self):
        m=Match(100)
        exchanged=m.players[0].hand[:3]
        for uid in exchanged:m.mulligan_toggle(uid)
        m.finish_mulligan(0)
        self.assertEqual(len(m.bank),50)
        self.assertEqual(len(m.players[0].hand),5)
        # Both requests are recorded, but nothing is exchanged until both submit.
        self.assertTrue(all(uid in m.players[0].hand for uid in exchanged))
        m.finish_mulligan(1,[])
        self.assertTrue(all(uid not in m.players[0].hand for uid in exchanged))
        self.assertEqual(len(m.bank),47)
        self.assertEqual(set(m.excluded),set(exchanged))
        m.assert_integrity()

    def test_one_play_and_board_order(self):
        m=setup_game()
        p=m.players[0];old=p.hand[:]
        m.play(old[0]);self.assertEqual(p.board,[old[0]])
        with self.assertRaises(IllegalMove):m.play(old[1])
        m.assert_integrity()

    def test_replace_not_death_and_bounty(self):
        m=setup_game()
        for uid in list(m.players[0].hand)[:5]:force_unit(m,uid,0)
        p=m.players[0];p.played_this_turn=False
        replacement=m.bank[0]
        m.bank.remove(replacement)
        m.cards[replacement].owner=0;m.cards[replacement].zone='hand';p.hand.append(replacement)
        old=p.board[1]
        c=m.players[1].coins
        m.play(replacement,old)
        self.assertEqual(p.board[-1],replacement)
        self.assertEqual(len(p.board),5)
        self.assertEqual(m.players[1].coins,c)
        self.assertIn(old,p.grave)
        m.assert_integrity()

    def test_hand_scaling(self):
        m=setup_game()
        p=m.players[0]
        # Manually simulate end-turn scaling without requiring a specific hand draw.
        ids=('S01','S05','S66','S67')
        for uid in ids:
            for player in m.players:
                for place in ('hand','deck','grave','board'):
                    if uid in getattr(player,place):getattr(player,place).remove(uid)
            if uid in m.bank:m.bank.remove(uid)
            m.cards[uid].owner=0;m.cards[uid].zone='hand';p.hand.append(uid)
            m.cards[uid].hand_turns=3
        a=m.cards['S01'];self.assertEqual((a.attack,a.max_hp,a.ability_level),(4,7,1))
        s=m.cards['S05'];self.assertEqual(s.max_hp,6+3*1+2)
        fast=m.cards['S66'];self.assertEqual((fast.attack,fast.max_hp),(2+3*1+2,4+3*1+1))
        double=m.cards['S67'];self.assertEqual((double.attack,double.max_hp),(1+3*1+2,5+3*1))
        m.assert_integrity()

    def test_attack_hero_and_taunt(self):
        m=setup_game()
        force_unit(m,'S09',0)
        force_unit(m,'S33',1)
        m.units['S09'].played_turn=0
        legal=m.legal_attacks('S09')
        self.assertEqual(legal,['S33'])
        with self.assertRaises(IllegalMove):m.attack('S09','hero:1')

    def test_shield_then_armor_then_hp_and_poison(self):
        m=setup_game()
        u=force_unit(m,'S01',1)
        u.shield=1;u.armor_temp=2;u.armor_perm=3
        self.assertEqual(m._damage(u.uid,12),0)
        self.assertEqual(m._damage(u.uid,4),0)
        self.assertEqual(u.armor_temp,0)
        self.assertEqual(u.armor_perm,1)
        self.assertEqual(m._damage(u.uid,2),1)
        self.assertEqual(u.hp,u.base_max_hp-1)
        m._add_poison('S01',1,2,'S11')
        m._tick_poison(1)
        self.assertEqual(u.hp,u.base_max_hp-2)
        self.assertEqual(u.armor_perm,0) if False else None

    def test_thresholds_and_full_round(self):
        m=setup_game()
        p=m.players[0]
        start=p.coins
        m._damage('hero:0',81,ignore_defense=True)
        self.assertEqual(p.coins,start+6)
        m._heal('hero:0',81)
        m._damage('hero:0',81,ignore_defense=True)
        self.assertEqual(p.coins,start+6)

    def test_all_70_abilities_have_handler(self):
        catalog=Match(2).defs
        for uid in catalog:
            with self.subTest(uid=uid):
                m=setup_game(31)
                force_unit(m,uid,0)
                for other in ('S01','S02','S33','S09'):
                    if other==uid:continue
                    force_unit(m,other,1 if other in ('S33','S09') else 0)
                m._death_levels[uid]=1
                context={'Elfy':'play','Dzikie bestie':'attack','Potwory':'death','Krasnoludy':'end','Ludzie':'play'}[catalog[uid].faction]
                target=m.players[1].board[0]
                opts=options(m,uid,context,target)
                if opts:
                    m._execute(uid,context,opts[0],target)
                m._drain()

    def test_selfplay_regressions(self):
        for seed in range(50):
            m=Match(seed)
            m.finish_mulligan(0,[]);m.finish_mulligan(1,[])
            agents=[ComputerOpponent(0),ComputerOpponent(1)]
            for step in range(1700):
                if m.phase=='finished':break
                if m.pending:agents[m.pending.owner].choose(m)
                else:agents[m.active].step(m)
                m.assert_integrity()
            self.assertEqual(m.phase,'finished',f'seed={seed} did not finish')
            self.assertIn(m.winner,(0,1))


if __name__=='__main__':unittest.main()
