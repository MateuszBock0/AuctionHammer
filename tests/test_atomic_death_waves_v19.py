"""Game Master v19 §7: wspólna migawka śmierci, kaskady i priorytet fal."""
import unittest

from test_engine import setup_game,force_unit
from game.core.models import IllegalMove


def choose_target(match, target, mode=None):
    assert match.pending is not None,(target,match.events[-12:])
    assert match.pending.context=='death_wave', match.pending
    idx=next(i for i,c in enumerate(match.pending.choices)
             if c.target==target and (mode is None or c.mode==mode))
    match.choose(idx)


class AtomicDeathWaveTests(unittest.TestCase):
    def test_snapshot_preserved_until_all_death_choices_are_declared(self):
        g=setup_game(701)
        force_unit(g,'S84',0)
        force_unit(g,'S23',0)
        victim=force_unit(g,'S01',1)
        victim.hp=1
        g._kill_batch(['S84','S23'])
        self.assertEqual(g.death_waves[0]['triggers'],('S84','S23'))
        self.assertEqual(set(g.death_waves[0]['options']),{'S84','S23'})
        g._drain()
        self.assertEqual(g.pending.uid,'S84')
        choose_target(g,'S01')
        # S84 does NOT kill the target until the whole cohort has declared.
        self.assertEqual(victim.hp,1)
        self.assertIn('S01',g.units)
        self.assertEqual(g.pending.uid,'S23')
        choose_target(g,'S01','Osłab')
        self.assertNotIn('S01',g.units)
        self.assertEqual(g.cards['S01'].zone,'grave')
        self.assertEqual([x[0] for x in g.death_wave_log[:4]],
                         ['wykryto','rozstrzyganie','wykryto','zamknięto'])
        g.assert_integrity()

    def test_new_lethal_outcome_is_new_group_not_same_death_wave(self):
        g=setup_game(702)
        force_unit(g,'S81',0)
        dying=force_unit(g,'S83',1)
        target=force_unit(g,'S01',0)
        dying.base_max_hp=4
        dying.hp=1
        g._kill_batch(['S81'])
        g._drain()
        choose_target(g,'S83','Osłab')
        self.assertIsNotNone(g.pending,(g.events[-12:],g.death_wave_log,[(x,y.hp) for x,y in g.units.items()]))
        self.assertEqual(g.pending.uid,'S83')
        self.assertEqual(g.pending.context,'death_wave')
        self.assertIn('S01',g.units)
        choose_target(g,'S01')
        self.assertEqual([x[1] for x in g.death_wave_log if x[0]=='wykryto'],[1,2])
        self.assertTrue(any(e.kind=='poison' and e.source=='S83' for e in target.effects))
        g.assert_integrity()

    def test_both_sides_trigger_from_one_batch_and_hero_is_checked_after_wave(self):
        g=setup_game(703)
        force_unit(g,'S21',0)
        force_unit(g,'S17',1)
        g.players[1].hp=3
        g._kill_batch(['S17','S21'])
        self.assertEqual(g.death_waves[0]['triggers'],('S21','S17'))
        g._drain()
        # Damage 4 and healing 6 resolve in one closed wave; no premature defeat.
        self.assertEqual(g.players[1].hp,5)
        self.assertEqual(g.phase,'turn')
        self.assertEqual(len(g.death_waves),0)
        g.assert_integrity()

    def test_stunned_monster_does_not_trigger_on_death(self):
        g=setup_game(704)
        force_unit(g,'S83',0)
        force_unit(g,'S01',1)
        g._add_effect('S83','stun',source='S59',expires=3,positive=False)
        g._kill_batch(['S83'])
        g._drain()
        self.assertEqual(len(g.death_waves),0)
        self.assertFalse(any(e.kind=='poison' for e in g.units['S01'].effects))
        g.assert_integrity()

    def test_hero_death_stops_events_from_a_later_group(self):
        g=setup_game(705)
        force_unit(g,'S21',0)
        force_unit(g,'S90',1)
        g.players[1].hp=3
        g._kill_batch(['S21'])
        g._kill_batch(['S90'])
        g._drain()
        self.assertEqual(g.phase,'finished')
        self.assertEqual(g.winner,0)
        self.assertEqual(len(g.death_waves),0)
        self.assertFalse(any(c.quick_on_first_summon for c in g.cards.values()))

    def test_one_shield_spent_in_stable_order_on_two_simultaneous_deaths(self):
        g=setup_game(706)
        force_unit(g,'S21',0)
        force_unit(g,'S17',1)
        g.players[1].hero_shield=1
        g.players[1].hp=50
        g._kill_batch(['S21','S17'])
        g._drain()
        self.assertEqual(g.players[1].hp,56)
        self.assertEqual(g.players[1].hero_shield,0)

    def test_same_death_group_deterministic_under_reordered_detection(self):
        results=[]
        for fallen in (('S83','S84'),('S84','S83')):
            g=setup_game(707)
            force_unit(g,'S84',0)
            force_unit(g,'S83',0)
            force_unit(g,'S01',1)
            g._kill_batch(fallen)
            self.assertEqual(g.death_waves[0]['triggers'],('S84','S83'))
            g._drain()
            choose_target(g,'S01')
            choose_target(g,'S01')
            results.append((g.units['S01'].hp,
                            [(e.kind,e.value,e.remaining) for e in g.units['S01'].effects],
                            tuple(g.death_wave_log)))
        self.assertEqual(results[0],results[1])

    def test_multiple_death_effects_use_the_same_target_snapshot(self):
        g=setup_game(708)
        force_unit(g,'S84',0)
        force_unit(g,'S83',0)
        target=force_unit(g,'S01',1)
        target.hp=1
        g._kill_batch(['S84','S83'])
        g._drain()
        choose_target(g,'S01')
        self.assertEqual(target.hp,1)
        self.assertEqual(g.pending.uid,'S83')
        choose_target(g,'S01')
        self.assertEqual(g.cards['S01'].zone,'grave')
        self.assertEqual(g.death_wave_log[-1][0],'zamknięto')
        g.assert_integrity()

    def test_hero_armor_and_shield_from_death_at_once(self):
        g=setup_game(709)
        force_unit(g,'S20',0)
        force_unit(g,'S82',0)
        g._kill_batch(['S20','S82'])
        g._drain()
        self.assertEqual(g.players[0].hero_shield,1)
        self.assertEqual(g.players[0].hero_armor,8)
        g.assert_integrity()

    def test_simultaneous_immunity_cannot_retroactively_cancel_stun(self):
        g=setup_game(710)
        g.active=1
        force_unit(g,'S88',1)
        force_unit(g,'S84',0)
        target=force_unit(g,'S01',1)
        g._kill_batch(['S84','S88'])
        self.assertEqual(g.death_waves[0]['triggers'],('S88','S84'))
        g._drain()
        choose_target(g,'S01')  # immune source first
        choose_target(g,'S01')  # stun source, same state at declaration
        kinds=[e.kind for e in target.effects]
        self.assertIn('immune_stun',kinds)
        self.assertIn('stun',kinds)
        g.assert_integrity()

    def test_earlier_cleanse_cannot_remove_debuff_from_same_wave(self):
        g=setup_game(711)
        g.active=1
        force_unit(g,'S87',1)
        force_unit(g,'S84',0)
        target=force_unit(g,'S01',1)
        g._add_effect('S01','stun',expires=3,source='S59',positive=False)
        self.assertTrue(any(e.kind=='stun' for e in target.effects))
        g._kill_batch(['S84','S87'])
        g._drain()
        choose_target(g,'S01')
        choose_target(g,'S01')
        # Pre-existing stun is removed; new stun from this same cohort survives.
        self.assertEqual(sum(e.kind=='stun' for e in target.effects),1)
        g.assert_integrity()

    def test_standard_combat_places_both_dead_units_in_one_group(self):
        g=setup_game(712)
        attacker=force_unit(g,'S66',0)
        defender=force_unit(g,'S21',1)
        attacker.played_turn=0
        attacker.hp=1
        defender.hp=1
        attacker.base_attack=3
        defender.base_attack=3
        g.attack('S66','S21')
        self.assertNotIn('S66',g.units)
        self.assertNotIn('S21',g.units)
        self.assertIn(('wykryto',1,('S66','S21')),g.death_wave_log)
        self.assertEqual(g.players[0].hp,96)
        g.assert_integrity()



if __name__=='__main__':
    unittest.main()
