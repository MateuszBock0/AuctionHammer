"""Targeted regression tests for v17 additions and corrected card effects."""
import unittest
from game.core.engine import Match
from game.ui.layout import fitted_viewport,window_to_canvas
from test_engine import force_unit,setup_game


class V17Regressions(unittest.TestCase):
    def test_all_six_mulligan_cards_excluded_forever(self):
        for seed in range(35):
            m=Match(seed)
            a=m.players[0].hand[:3]
            b=m.players[1].hand[:3]
            m.finish_mulligan(0,a)
            self.assertEqual(len(m.bank),50)
            self.assertEqual(len(m.excluded),0)
            self.assertEqual(m.phase,'mulligan')
            m.finish_mulligan(1,b)
            self.assertEqual(len(m.excluded),6)
            self.assertEqual(len(m.bank),44)
            self.assertEqual(set(m.excluded),set(a+b))
            m.assert_integrity()
            for uid in a+b:
                self.assertNotIn(uid,m.bank)
                for p in m.players:
                    self.assertNotIn(uid,p.hand+p.deck+p.board+p.grave)

    def test_source_on_attack_before_defender_reaction(self):
        m=setup_game(93)
        attacker=force_unit(m,'S09',0)
        defender=force_unit(m,'S103',1)
        attacker.hp=1
        defender.hp=1
        attacker.played_turn=0
        m.attack(attacker.uid,defender.uid)
        self.assertIn(attacker.uid,m.units)
        self.assertEqual(attacker.hp,1)
        self.assertNotIn(defender.uid,m.units)
        self.assertEqual(attacker.attacks,1)

    def test_on_play_before_newly_triggered_position_reaction(self):
        m=setup_game(29)
        trumpeter=force_unit(m,'S108',1)
        trumpeter.hp=3
        uid='S01'
        # Ensure S01 can be played legitimately, irrespective of its dealt zone.
        for p in m.players:
            for zone in ('hand','deck','grave','board'):
                if uid in getattr(p,zone):getattr(p,zone).remove(uid)
        if uid in m.bank:m.bank.remove(uid)
        m.cards[uid].owner=0;m.cards[uid].zone='hand'
        m.players[0].hand.append(uid)
        m.play(uid)
        self.assertIsNotNone(m.pending)
        ix=next(i for i,ch in enumerate(m.pending.choices) if ch.target=='S108')
        m.choose(ix)
        self.assertNotIn('S108',m.units)
        self.assertIn('S01',m.units)
        self.assertFalse(any(e.kind=='stun' for e in m.units['S01'].effects))
        m.assert_integrity()

    def test_s107_poison_upgrade_is_total_not_per_tick(self):
        m=setup_game(77)
        a=force_unit(m,'S09',0)
        m.cards['S107'].hand_turns=3
        d=force_unit(m,'S107',1)
        a.hp=30;a.base_max_hp=30;a.played_turn=0
        m.attack('S09','S107')
        poison=[e for e in a.effects if e.kind=='poison' and e.source=='S107']
        self.assertEqual(len(poison),1)
        self.assertEqual((poison[0].value,poison[0].bonus_once,poison[0].remaining),(1,1,2))

    def test_aura_maxhp_ends_with_hp_adjustment(self):
        m=setup_game(15)
        force_unit(m,'S35',0)
        u=force_unit(m,'S01',0)
        m._update_auras()
        self.assertEqual((u.max_hp,u.hp),(5,5))
        m._remove_unit('S35',death=False)
        m._update_auras()
        self.assertEqual((u.max_hp,u.hp),(4,4))

    def test_s108_first_sight_upgraded_stun_is_once(self):
        m=setup_game(17)
        m.cards['S108'].hand_turns=3
        force_unit(m,'S108',0)
        opponent=force_unit(m,'S01',1)
        initial=opponent.hp
        m._update_auras()
        self.assertEqual(opponent.hp,initial-1)
        self.assertTrue(any(e.kind=='stun' for e in opponent.effects))
        m._update_auras()
        self.assertEqual(opponent.hp,initial-1)

    def test_resizable_viewports_and_hitboxes(self):
        logical=(1480,920)
        for screen in ((1480,920),(1366,768),(1920,1080),(1024,768),(900,600)):
            rect=fitted_viewport(screen,logical)
            x,y,w,h=rect
            self.assertGreater(w,0);self.assertGreater(h,0)
            self.assertLessEqual(x+w,screen[0]);self.assertLessEqual(y+h,screen[1])
            cx,cy=x+w//2,y+h//2
            lx,ly=window_to_canvas((cx,cy),rect,logical)
            self.assertAlmostEqual(lx,logical[0]//2,delta=2)
            self.assertAlmostEqual(ly,logical[1]//2,delta=2)
            self.assertIsNone(window_to_canvas((x-1,cy),rect,logical))
            self.assertIsNone(window_to_canvas((x+w,cy),rect,logical))
