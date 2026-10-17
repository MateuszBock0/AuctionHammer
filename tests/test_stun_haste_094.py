"""Focused Game Master v17 regressions: stun timing, S95 and all haste sources."""
import unittest
from game.core.models import Choice
from test_engine import setup_game,force_unit

def add_hand(g,uid):
    for p in g.players:
        for z in ('hand','deck','grave','board'):
            arr=getattr(p,z)
            if uid in arr:arr.remove(uid)
    if uid in g.bank:g.bank.remove(uid)
    g.cards[uid].owner=0
    g.cards[uid].zone='hand'
    g.players[0].hand.append(uid)

class StunRegressions(unittest.TestCase):
    def test_hammer_stuns_lowest_atk_for_one_turn(self):
        g=setup_game(200)
        force_unit(g,'S95',0)
        low=force_unit(g,'S66',1)
        target=force_unit(g,'S114',1)
        g.end_turn()
        self.assertFalse(any(e.kind=='stun' for e in low.effects))
        self.assertTrue(any(e.kind=='stun' for e in target.effects))
        self.assertEqual(g.legal_attacks('S114'),[])
        g.end_turn()
        self.assertFalse(any(e.kind=='stun' for e in target.effects))
        g.end_turn()
        self.assertIn('hero:0',g.legal_attacks('S114'))

    def test_hammer_does_not_stun_same_unit_in_consecutive_turns(self):
        g=setup_game(202)
        hammer=force_unit(g,'S95',0)
        force_unit(g,'S114',1)
        g.end_turn()
        self.assertEqual((hammer.last_stun_target,hammer.last_stun_turn),('S114',1))
        g.end_turn();g.end_turn()
        self.assertEqual((hammer.last_stun_target,hammer.last_stun_turn),('S114',1))
        g.end_turn();g.end_turn()
        self.assertEqual((hammer.last_stun_target,hammer.last_stun_turn),('S114',3))

    def test_hammer_switches_target_next_turn(self):
        g=setup_game(203)
        hammer=force_unit(g,'S95',0)
        force_unit(g,'S114',1)
        force_unit(g,'S66',1)
        g.end_turn()
        self.assertEqual(hammer.last_stun_target,'S114')
        g.end_turn();g.end_turn()
        self.assertEqual(hammer.last_stun_target,'S66')

    def test_hammer_does_not_damage_when_stun_is_immune(self):
        g=setup_game(204)
        g.cards['S95'].hand_turns=3
        force_unit(g,'S95',0)
        target=force_unit(g,'S114',1)
        g._add_effect('S114','immune_stun',source='S76')
        initial=target.hp
        g.end_turn()
        self.assertEqual(target.hp,initial)
        self.assertFalse(any(e.kind=='stun' for e in target.effects))

    def test_bear_stun_upgrade_requires_success(self):
        g=setup_game(205)
        g.cards['S15'].hand_turns=3
        force_unit(g,'S15',0)
        target=force_unit(g,'S114',1)
        g._add_effect('S114','immune_stun',source='S76')
        initial=target.hp
        g._execute('S15','attack',Choice('auto','S114',''),attacked='S114')
        self.assertEqual(target.hp,initial)

    def test_stun_prevents_immediate_attack_and_end_ability(self):
        g=setup_game(206)
        force_unit(g,'S95',0)
        quick=force_unit(g,'S66',0)
        quick.played_turn=g.players[0].turn_count
        g._add_effect('S66','quick',source='S66')
        self.assertTrue(g.legal_attacks('S66'))
        g._add_effect('S66','stun',expires=g._expiry(0),source='S59',positive=False)
        g._add_effect('S95','stun',expires=g._expiry(0),source='S59',positive=False)
        force_unit(g,'S114',1)
        self.assertEqual(g.legal_attacks('S66'),[])
        g.end_turn()
        self.assertFalse(any(e.kind=='stun' for e in g.units['S114'].effects))

    def test_independent_stuns_extend_duration(self):
        g=setup_game(207)
        force_unit(g,'S95',0)
        target=force_unit(g,'S114',1)
        g._add_effect('S114','stun',expires=g._expiry(1),source='S59',positive=False)
        g.end_turn()
        self.assertEqual(sorted(e.expires for e in target.effects if e.kind=='stun'),[2,3])
        g._remove_unit('S95',death=False)
        g.end_turn();g.end_turn()
        self.assertEqual(g.legal_attacks('S114'),[])
        g.end_turn();g.end_turn()
        self.assertTrue(g.legal_attacks('S114'))

class HasteRegressions(unittest.TestCase):
    def test_innate_quick_attack_on_play(self):
        for uid in ('S114',):
            with self.subTest(uid=uid):
                g=setup_game(310)
                add_hand(g,uid)
                g.play(uid)
                self.assertIn('hero:1',g.legal_attacks(uid))
                g.attack(uid,'hero:1')
                self.assertEqual(g.units[uid].attacks,1)
                self.assertEqual(g.legal_attacks(uid),[])

    def test_gepard_cannot_itself_attack_on_play(self):
        g=setup_game(311)
        add_hand(g,'S78')
        g.play('S78')
        self.assertEqual(g.legal_attacks('S78'),[])

    def test_gepard_grants_quick_to_other_newly_played_unit(self):
        g=setup_game(312)
        force_unit(g,'S78',0)
        add_hand(g,'S01')
        g.play('S01')
        self.assertEqual(g.legal_attacks('S01'),[])
        g.attack('S78','hero:1')
        idx=next(i for i,c in enumerate(g.pending.choices) if c.target=='S01')
        g.choose(idx)
        self.assertIn('hero:1',g.legal_attacks('S01'))

    def test_constructor_grants_quick_only_next_turn(self):
        g=setup_game(313)
        force_unit(g,'S101',0)
        add_hand(g,'S01')
        g.end_turn()
        idx=next(i for i,c in enumerate(g.pending.choices) if c.target=='S01')
        g.choose(idx)
        self.assertEqual(g.cards['S01'].quick_next_turn,2)
        g.end_turn()
        g.play('S01')
        self.assertIn('hero:1',g.legal_attacks('S01'))

    def test_nightmare_grants_quick_to_next_play(self):
        g=setup_game(314)
        force_unit(g,'S90',0)
        add_hand(g,'S01')
        g._kill_batch(['S90']);g._drain()
        recipients=[x for x in g.players[0].hand if g.cards[x].quick_on_first_summon]
        self.assertEqual(len(recipients),min(2,len(g.players[0].hand)))
        selected=recipients[0]
        g.play(selected)
        self.assertIn('hero:1',g.legal_attacks(selected))

if __name__=='__main__': unittest.main()
