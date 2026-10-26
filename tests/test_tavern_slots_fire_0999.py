"""0.9.99: beer mug exits and all ten slot rims burn for active brawl turns."""
from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import pygame

from game.ui.app import SoloApp
from game.ui.beer_fx import slot_flame_strength
from game.ui.tavern_art import draw_slot_flamelets, draw_board_spill


class FireBrawl0999(TestCase):
    def test_spreads_right_to_left_to_all_ten_slots(self):
        stamp=10000
        self.assertEqual(slot_flame_strength(3,stamp+800,stamp,True,0,4),0)
        self.assertGreater(slot_flame_strength(3,stamp+1100,stamp,True,0,4),0)
        self.assertEqual(slot_flame_strength(3,stamp+1100,stamp,True,0,0),0)
        for owner in (0,1):
            for slot in range(5):
                self.assertEqual(slot_flame_strength(
                    3,stamp+2500,stamp,True,owner,slot),1.0)

    def test_brawl_turns_are_the_only_persistent_flame_authority(self):
        stamp=10000
        for remain in (3,2,1):
            for owner in (0,1):
                for slot in range(5):
                    self.assertGreater(slot_flame_strength(
                        remain,stamp+4000,stamp,True,owner,slot),0)
        for owner in (0,1):
            for slot in range(5):
                self.assertEqual(slot_flame_strength(0,stamp+4000,stamp,
                                                      True,owner,slot),0.0)
                self.assertEqual(slot_flame_strength(6,stamp+4000,stamp,
                                                      False,owner,slot),0.0)
                self.assertEqual(slot_flame_strength(1,stamp,None,True,
                                                      owner,slot),1.0)

    def test_small_flames_only_touch_outer_card_slot_frame(self):
        surface=pygame.Surface((1080,730))
        bg=(14,15,16,255)
        surface.fill(bg[:3])
        original=surface.copy()
        for owner,y in ((1,152),(0,431)):
            for index in range(5):
                rect=pygame.Rect(107+174*index,y,148,220)
                draw_slot_flamelets(surface,rect,now_ms=2500,
                                    owner=owner,index=index,strength=1.0)
                self.assertEqual(surface.get_at(rect.center),bg)
                self.assertEqual(surface.get_at((rect.centerx,rect.y+27)),bg)
                self.assertEqual(surface.get_at((rect.centerx,rect.bottom-27)),bg)
                self.assertNotEqual(
                    pygame.image.tobytes(surface.subsurface(
                        pygame.Rect(rect.left-5,rect.top,9,20)),"RGB"),
                    pygame.image.tobytes(original.subsurface(
                        pygame.Rect(rect.left-5,rect.top,9,20)),"RGB"))
        for pt in ((400,126),(550,400),(400,678),(1075,550)):
            self.assertEqual(surface.get_at(pt),bg)

    def test_right_only_mug_and_spill_during_paid_animation(self):
        class FakeApp:
            FIRST_X,SLOT_W,SLOT_GAP,OWN_Y,OPP_Y=107,148,26,431,152
            animations_enabled=True
            replay_index=None
            menu_open=False
            history_open=False
            help_open=False
            details_card=None
            _beer_fx_started_ms=5000
            def __init__(self,ticks):
                self.screen=pygame.Surface((1480,980))
                self.game=SimpleNamespace(
                    tavern_beer_enabled=True,beer_turns_remaining=ticks,
                    beer_price=lambda _:10,can_order_beer=lambda _:True)
            def _text(self,*a,**k):
                pass
            def _button(self,*a,**k):
                pass
            def slot_rect(self,owner,index):
                return SoloApp.slot_rect(self,owner,index)
            def beer_buy_rect(self):
                return pygame.Rect(10,544,94,38)

        def draw(now,ticks,animate=True):
            fake=FakeApp(ticks)
            fake.animations_enabled=animate
            with patch('pygame.time.get_ticks',return_value=now), \
                 patch('game.ui.app.draw_tavern_rail') as rail, \
                 patch('game.ui.app.draw_board_spill') as spill, \
                 patch('game.ui.app.draw_slot_flamelets') as outlines:
                SoloApp._draw_tavern_beer(fake)
                props={c.args[1]:c.kwargs for c in rail.call_args_list}
                return props,spill.call_args_list,outlines.call_args_list
        props,spills,flames=draw(5100,3)
        self.assertFalse(props[57]['show_mug'])
        self.assertTrue(props[1020]['show_mug'])
        self.assertEqual(props[1020]['mug_anchor'],(1021,565))
        self.assertEqual(len(flames),0)
        props,spills,flames=draw(6350,3)  # roll off right during exit
        self.assertTrue(props[1020]['show_mug'])
        self.assertGreater(props[1020]['mug_anchor'][0],1021)
        self.assertGreater(props[1020]['mug_anchor'][1],565)
        props,spills,flames=draw(7600,3)
        self.assertFalse(props[57]['show_mug'])
        self.assertFalse(props[1020]['show_mug'])
        self.assertEqual(len(flames),10)
        self.assertEqual(len(spills),1)
        self.assertEqual(spills[0].args[1],1020)
        self.assertTrue(spills[0].kwargs['lower_right'])
        props,spills,flames=draw(7600,0)
        self.assertFalse(props[1020]['show_mug'])
        self.assertEqual(len(flames),0)
        self.assertEqual(len(spills),0)
        props,spills,flames=draw(6000,3,animate=False)
        self.assertFalse(props[1020]['show_mug'])
        self.assertEqual(len(flames),0)
        self.assertEqual(len(spills),0)

    def test_one_spill_on_right_lower_board_frame(self):
        screen=pygame.Surface((1100,800))
        screen.fill((13,14,15))
        draw_board_spill(screen,1020,1.0,1.0,now_ms=1000,
                         lower_right=True)
        self.assertNotEqual(screen.get_at((955,652)),(13,14,15,255))
        self.assertEqual(screen.get_at((50,470)),(13,14,15,255))
        self.assertEqual(screen.get_at((400,650)),(13,14,15,255))


if __name__=='__main__':
    import unittest
    unittest.main()
