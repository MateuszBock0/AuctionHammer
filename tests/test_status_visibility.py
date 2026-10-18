"""Abilities bestowed on another card must show on the recipient and disappear with the effect."""
import unittest
from game.core.engine import Match
from game.core.models import Choice
from game.core.status_view import active_statuses, hand_grants
from test_engine import setup_game, force_unit


def matching(g,uid,key):
    return [s for s in active_statuses(g,uid) if s.category==key]


class StatusVisibilityTests(unittest.TestCase):
    def test_elf_grants_taunt_which_also_changes_enemy_attack_targeting(self):
        g=setup_game(12)
        force_unit(g,'S61',0)
        recipient=force_unit(g,'S01',0)
        hostile=force_unit(g,'S09',1)
        before=matching(g,'S01','taunt')
        self.assertEqual(before,[])
        g._execute('S61','play',Choice('Cel sojuszniczy','S01',''))
        effects=matching(g,'S01','taunt')
        self.assertEqual(len(effects),1)
        self.assertIn('Władczyni Leśnych Więzów',effects[0].source)
        g.active=1
        self.assertEqual(g.legal_attacks('S09'),['S01'])
        g._remove_unit('S01',death=False)
        self.assertEqual(matching(g,'S01','taunt'),[])

    def test_dwarf_end_turn_gift_taunt_to_ally(self):
        g=setup_game(22)
        force_unit(g,'S96',0)
        force_unit(g,'S01',0)
        g._execute('S96','end',Choice('Cel sojuszniczy','S01',''))
        effects=matching(g,'S01','taunt')
        self.assertEqual(len(effects),1)
        self.assertIn('Wartownik Szybu',effects[0].source)
        self.assertIn('wygaśnie',effects[0].detail)

    def test_bestowed_double_attack_and_quick_attack(self):
        g=setup_game(52)
        force_unit(g,'S102',0)
        force_unit(g,'S01',0)
        g._execute('S102','end',Choice('Podwójny atak na następną turę','S01',''))
        self.assertTrue(g._double(g.units['S01']))
        self.assertEqual(len(matching(g,'S01','double')),1)
        self.assertIn('Mechanik Dwóch Ostrzy',matching(g,'S01','double')[0].source)
        force_unit(g,'S78',0)
        g._execute('S78','attack',Choice('Nadaj szybki atak','S01',''),'hero:1')
        self.assertEqual(len(matching(g,'S01','quick')),1)
        self.assertTrue(g._fast(g.units['S01']))

    def test_in_hand_grant_visible_and_played(self):
        g=setup_game(71)
        force_unit(g,'S101',0)
        uid=g.players[0].hand[0]
        g._execute('S101','end',Choice('Szybki atak w kolejnej turze',uid,''))
        self.assertEqual(hand_grants(g,uid)[0].category,'quick')
        self.assertIn('Konstruktor Sprężyn',hand_grants(g,uid)[0].source)
        self.assertEqual(matching(g,uid,'quick'),[])
        g.players[0].turn_count+=1
        # Play can't be called if the player already played this turn.
        g.players[0].played_this_turn=False
        g.play(uid)
        self.assertTrue(any(s.category=='quick' for s in active_statuses(g,uid)))
        self.assertEqual(hand_grants(g,uid),[])

    def test_stat_changes_shield_armor_immunity_regen_sources(self):
        g=setup_game(30)
        for s in ('S04','S08','S05','S03','S64','S60'):
            force_unit(g,s,0)
        # Move S01 to player 0 as a test recipient; board cap does not affect core execution here.
        recipient=force_unit(g,'S01',0)
        g._execute('S04','play',Choice('Wzmocnij','S01',''))
        g._execute('S08','play',Choice('Wzmocnij','S01',''))
        g._execute('S05','play',Choice('Cel sojuszniczy','S01',''))
        g._execute('S03','play',Choice('Cel sojuszniczy','S01',''))
        g._execute('S64','play',Choice('Cel sojuszniczy','S01',''))
        g._execute('S60','play',Choice('Cel sojuszniczy','S01',''))
        states=active_statuses(g,'S01')
        keys={s.category for s in states}
        for k in ('atk_up','hp_up','shield','armor','immune','regen'):
            self.assertIn(k,keys)
        expected={'atk_up':'Tkacz Run','hp_up':'Mag Tkanki Życia',
                  'shield':'Strażniczka Księżycowej Pieczęci',
                  'armor':'Zaklinacz Runicznej Zbroi','immune':'Strażnik Zaklęć Ochronnych',
                  'regen':'Druid Odnowy'}
        for key,name in expected.items():
            self.assertTrue(any(name in s.source for s in states if s.category==key),(key,name))
        self.assertEqual(recipient.shield,1)
        g._damage('S01',1)
        self.assertNotIn('shield',{s.category for s in active_statuses(g,'S01')})
        self.assertGreater(recipient.armor,0)

    def test_poison_stun_disappear_and_intrinsic_taunt_disabled(self):
        g=setup_game(99)
        force_unit(g,'S33',1)
        force_unit(g,'S59',0)
        force_unit(g,'S58',0)
        self.assertTrue(matching(g,'S33','taunt'))
        g._execute('S58','play',Choice('Cel wrogi','S33',''))
        g._execute('S59','play',Choice('Cel wrogi','S33',''))
        self.assertEqual(len(matching(g,'S33','stun')),1)
        self.assertEqual(len(matching(g,'S33','poison')),1)
        self.assertFalse(any(s.name.endswith('(wrodzona)') for s in matching(g,'S33','taunt')))
        g._tick_poison(1)
        g._tick_poison(1)
        self.assertEqual(matching(g,'S33','poison'),[])

    def test_aura_modifiers_are_visible_on_recipients_and_removed(self):
        g=setup_game(43)
        force_unit(g,'S35',0)
        force_unit(g,'S01',0)
        force_unit(g,'S104',0)
        g._execute('S35','play',Choice('ally',None,''))
        self.assertTrue(matching(g,'S01','hp_up'))
        self.assertTrue(matching(g,'S01','heal_aura'))
        self.assertIn('Komendant Straży',matching(g,'S01','hp_up')[0].source)
        g._remove_unit('S35',death=False)
        g._update_auras()
        self.assertFalse(matching(g,'S01','hp_up'))
        self.assertTrue(matching(g,'S01','heal_aura'))
        g._remove_unit('S104',death=False)
        g._update_auras()
        self.assertFalse(matching(g,'S01','heal_aura'))

    def test_aura_armor_is_visible_and_disappears_when_source_removed(self):
        g=setup_game(10)
        force_unit(g,'S105',0)
        force_unit(g,'S01',0)
        g._update_auras()
        self.assertTrue(any('Zbrojmistrz Garnizonu' in s.source for s in matching(g,'S01','armor')))
        g._remove_unit('S105',death=False)
        g._update_auras()
        self.assertFalse(matching(g,'S01','armor'))


if __name__=='__main__':unittest.main()

class IntegrationStatusTests(unittest.TestCase):
    def test_real_play_and_choice_grant_taunt_to_other_unit(self):
        g=setup_game(45)
        force_unit(g,'S01',0)
        uid='S61'
        for p in g.players:
            for zone in ('hand','deck','grave','board'):
                if uid in getattr(p,zone):getattr(p,zone).remove(uid)
        if uid in g.bank:g.bank.remove(uid)
        g.cards[uid].owner=0;g.cards[uid].zone='hand';g.players[0].hand.append(uid)
        g.players[0].played_this_turn=False
        g.play(uid)
        self.assertIsNotNone(g.pending)
        index=next(i for i,opt in enumerate(g.pending.choices) if opt.target=='S01')
        g.choose(index)
        self.assertIsNone(g.pending)
        self.assertEqual(len(matching(g,'S01','taunt')),1)
        self.assertIn('Władczyni Leśnych Więzów',matching(g,'S01','taunt')[0].source)
        g.assert_integrity()

    def test_two_armor_donors_and_absorption_provenance(self):
        g=setup_game(71)
        for src in ('S03','S82'):force_unit(g,src,0)
        friend=force_unit(g,'S01',0)
        g._execute('S03','play',Choice('Cel sojuszniczy','S01',''))
        g._execute('S82','death',Choice('Pozostała jednostka','S01',''))
        armor=matching(g,'S01','armor')
        self.assertEqual(sum(friend.armor_perm_grants.values()),friend.armor_perm)
        self.assertEqual({st.source for st in armor},{'Zaklinacz Runicznej Zbroi','Golem Grobowy'})
        # Direct attack removes armor from the oldest grant first.
        g._damage('S01',3)
        remaining=matching(g,'S01','armor')
        self.assertEqual(sum(friend.armor_perm_grants.values()),friend.armor_perm)
        self.assertEqual(len(remaining),2)
        g._damage('S01',2)
        self.assertEqual(len(matching(g,'S01','armor')),1)
        self.assertIn('Golem Grobowy',matching(g,'S01','armor')[0].source)

    def test_expiry_removes_issued_buff_from_render_state(self):
        g=setup_game(28)
        force_unit(g,'S96',0)
        force_unit(g,'S01',0)
        # Simulate a buff scheduled to expire at this own turn's end.
        g._add_effect('S01','taunt',expires=g.players[0].turn_count,source='S96')
        self.assertEqual(len(matching(g,'S01','taunt')),1)
        g._finalize_end_turn()
        self.assertEqual(matching(g,'S01','taunt'),[])

    def test_monster_death_gives_next_played_unit_quick(self):
        g=setup_game(39)
        force_unit(g,'S90',0)
        g._execute('S90','death',Choice('auto',None,''))
        recipients=[x for x in g.players[0].hand if g.cards[x].quick_on_first_summon]
        self.assertEqual(len(recipients),min(2,len(g.players[0].hand)))
        next_uid=recipients[0]
        g.players[0].played_this_turn=False
        g.play(next_uid)
        self.assertFalse(g.cards[next_uid].quick_on_first_summon)
        self.assertTrue(matching(g,next_uid,'quick'))

class ArmorSynchronizationTests(unittest.TestCase):
    def test_armor_stripping_hits_temporary_before_permanent(self):
        g=setup_game(81)
        force_unit(g,'S26',1)
        recipient=force_unit(g,'S01',1)
        force_unit(g,'S12',0)
        g._execute('S26','end',Choice('Cel sojuszniczy','S01',''))
        recipient.armor_perm=4
        self.assertEqual(sum(recipient.temporary_armor.values()),2)
        g._execute('S12','attack',Choice('auto','S01',''),'S01')
        self.assertEqual(sum(recipient.temporary_armor.values()),0)
        self.assertEqual(recipient.armor_perm,4)
        self.assertFalse(any(s.name=='Pancerz tymczasowy' for s in active_statuses(g,'S01')))

    def test_cleansing_temporary_positive_removes_backing_armor(self):
        g=setup_game(82)
        force_unit(g,'S26',1)
        force_unit(g,'S01',1)
        g._execute('S26','end',Choice('Cel sojuszniczy','S01',''))
        recipient=g.units['S01']
        self.assertEqual(sum(recipient.temporary_armor.values()),2)
        self.assertTrue(g._clean('S01',negative=False))
        self.assertEqual(sum(recipient.temporary_armor.values()),0)
        self.assertFalse(matching(g,'S01','armor'))
