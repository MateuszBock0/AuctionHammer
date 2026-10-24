"""0.9.74 visual combat feedback: only committed HP/protection deltas."""
import copy
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from game.core.engine import Match
from game.ui.app import SoloApp
from game.ui.combat_visuals import CombatVisuals


def state(hp, shield=0, armor=0, at=(160,155)):
    return {'hp':hp,'shield':shield,'armor':armor,'at':at,
            'status':frozenset(),'attacks':0}


class CombatImpactEffects0974(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.fx=CombatVisuals()
        self.fake=SimpleNamespace(active=0,event_journal=[])
        self.old={
            'hero:0':state(100,at=(110,60)),
            'hero:1':state(100,at=(110,30)),
            'U1':state(10,shield=5,armor=4,at=(130,170)),
            'U2':state(4,shield=1,armor=1,at=(330,170))
        }

    def tearDown(self):
        pygame.quit()

    def _sync(self,changed):
        original=copy.deepcopy(self.old)
        with patch.object(self.fx,'_snapshot',side_effect=[original,changed]):
            self.fx.sync(self.fake,None,None,1000)
            self.fx.sync(self.fake,None,None,1100)

    def test_real_hp_damage_healing_shield_armor_and_hero(self):
        changed=copy.deepcopy(self.old)
        changed['U1'].update(hp=7,shield=3,armor=2)
        changed['U2'].update(hp=6,shield=4,armor=3)
        changed['hero:1']['hp']=92
        self._sync(changed)
        pulses={(p.kind,p.at,p.label) for p in self.fx.pulses}
        self.assertIn(('damage',(130,170),'-3 PŻ'),pulses)
        self.assertIn(('heal',(330,170),'+2 PŻ'),pulses)
        self.assertIn(('damage',(110,30),'-8 PŻ'),pulses)
        self.assertIn(('shield',(130,170),'TARCZA -2'),pulses)
        self.assertIn(('armor',(130,170),'PANC. -2'),pulses)
        self.assertIn(('shield',(330,170),'TARCZA +3'),pulses)
        self.assertIn(('armor',(330,170),'PANC. +2'),pulses)
        self.assertEqual([p.lane for p in self.fx.pulses
                          if p.at==(130,170)], [0,1,2])
        self.assertEqual(self.fx.shake_offset('U1',1100),(4,0))
        self.assertEqual(self.fx.shake_offset('U1',1320),(0,0))
        self.assertEqual(self.fx.shake_offset('U2',1100),(0,0))

    def test_absorbed_damage_reports_protection_not_false_hp_wound(self):
        changed=copy.deepcopy(self.old)
        changed['U1'].update(shield=2,armor=2)
        self._sync(changed)
        pulses=[p for p in self.fx.pulses if p.at==(130,170)]
        self.assertEqual({p.kind for p in pulses},{'shield','armor'})
        self.assertIn('TARCZA -3',[p.label for p in pulses])
        self.assertIn('PANC. -2',[p.label for p in pulses])
        self.assertEqual(self.fx.shake_offset('U1',1100),(2,0))
        self.assertEqual(self.fx.shake_offset('U1',1100+220),(0,0))

    def test_no_pulse_if_no_committed_change(self):
        self._sync(copy.deepcopy(self.old))
        self.assertEqual(self.fx.pulses,[])
        self.assertEqual(self.fx.impacts,{})

    def test_pulses_are_capped_and_rendered_without_mutating_results(self):
        changed=copy.deepcopy(self.old)
        changed['U1'].update(hp=1,shield=0,armor=0)
        self._sync(changed)
        source=copy.deepcopy(changed)
        output=pygame.Surface((480,380))
        font=pygame.font.Font(None,18)
        self.fx.draw(output,1100,font)
        self.fx.draw(output,1400,font)
        self.assertEqual(changed,source)
        self.assertTrue(output.get_bounding_rect().width>0)
        self.assertEqual(len(self.fx.pulses),3)
        self.fx.draw(output,2400,font)
        self.assertEqual(self.fx.pulses,[])

    def test_delayed_impact_survives_until_projectile_lands(self):
        self.fx._push('damage',(100,100),1000,'-7 PŻ',delay_ms=165)
        output=pygame.Surface((240,240))
        font=pygame.font.Font(None,18)
        self.fx.draw(output,1050,font)
        self.assertEqual(len(self.fx.pulses),1)
        self.fx.draw(output,1165,font)
        self.assertTrue(output.get_bounding_rect().width>0)

    def test_existing_attack_drag_and_hand_card_rendering_still_works(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp(start_in_menu=True)
        app.menu_open=False
        game=None
        for seed in range(300,500):
            candidate=Match(seed,auctions_enabled=True,auction_catalog='v22',
                            starting_compensation='choice_2_5_or_coins')
            if candidate.first==0:
                game=candidate
                break
        self.assertIsNotNone(game)
        app.game=game
        app.ai.step(game)
        if 1 not in game.mulligan_done:app.ai.step(game)
        game.finish_mulligan(0,[])
        uid=game.players[0].hand[0]
        game.play(uid,slot=0)
        origin=app.slot_rect(0,0)
        with patch.object(app.combat_visuals,'shake_offset',return_value=(3,-1)):
            with patch.object(app.cards_view,'draw',wraps=app.cards_view.draw) as drawn:
                app._draw_board()
        matching=[c for c in drawn.call_args_list
                  if len(c.args)>1 and c.args[1] is game.cards[uid]]
        self.assertEqual(len(matching),1)
        self.assertEqual(matching[0].args[2],origin.move(3,-1))
        # Visual offset must NOT move input targets or any engine card.
        self.assertEqual(app.slot_rect(0,0),origin)
        self.assertEqual(game.slot_of(uid),0)
        app.animations_enabled=False
        with patch.object(app.combat_visuals,'shake_offset',return_value=(4,1)):
            with patch.object(app.cards_view,'draw',wraps=app.cards_view.draw) as drawn:
                app._draw_board()
        matching=[c for c in drawn.call_args_list
                  if len(c.args)>1 and c.args[1] is game.cards[uid]]
        self.assertEqual(matching[0].args[2],origin)


if __name__=="__main__":
    unittest.main()
