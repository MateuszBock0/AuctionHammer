"""0.9.98: approved pixel-art props, real board-edge spill and flame timing."""
from __future__ import annotations

import unittest
from pathlib import Path

import pygame

from game.ui.beer_fx import board_spill_timeline
from game.ui.tavern_art import (
    load_tavern_sprites, draw_board_spill, draw_tavern_rail, _side_points,
)


class BoardMountedBeer0998(unittest.TestCase):
    def test_png_independent_pixel_atlas_is_loaded_once(self):
        items=load_tavern_sprites()
        self.assertEqual(tuple(s.get_size() for s in items),
                         ((70,64),(32,44),(76,75)))
        self.assertIs(load_tavern_sprites(),items)
        for sprite in items:
            # Pixel art must have crisp hard transparency, no blurry outline.
            opaque=sum(sprite.get_at((x,y)).a==255 for y in range(sprite.get_height())
                       for x in range(sprite.get_width()))
            self.assertGreater(opaque,300)
            self.assertTrue(all(sprite.get_at((x,y)).a in (0,255)
                                for y in range(sprite.get_height())
                                for x in range(sprite.get_width())))

    def test_exact_purchase_timeline_and_disable(self):
        stamp=123000
        self.assertEqual(board_spill_timeline(stamp,None),(0.0,0.0,0.0))
        self.assertEqual(board_spill_timeline(stamp-1,stamp),(0.0,0.0,0.0))
        self.assertEqual(board_spill_timeline(stamp+600,stamp)[0],0.0)
        self.assertGreater(board_spill_timeline(stamp+840,stamp)[0],0.8)
        self.assertGreater(board_spill_timeline(stamp+1000,stamp)[1],0.8)
        self.assertGreater(board_spill_timeline(stamp+1190,stamp)[2],0.8)
        self.assertEqual(board_spill_timeline(stamp+2150,stamp),(0.0,0.0,0.0))
        self.assertEqual(board_spill_timeline(stamp+1100,stamp,False),
                         (0.0,0.0,0.0))
        for tick in range(stamp,stamp+2300,47):
            for v in board_spill_timeline(tick,stamp):
                self.assertGreaterEqual(v,0.0)
                self.assertLessEqual(v,1.0)

    def test_tilt_splashes_are_mirrored_onto_both_board_edges(self):
        self.assertEqual(_side_points(57),(105,1))
        self.assertEqual(_side_points(1020),(992,-1))
        a=pygame.Surface((1080,480));a.fill((9,11,13))
        b=a.copy()
        for x in (57,1020):
            draw_tavern_rail(a,x,25,False,1.0,0.0,now_ms=0,
                             animate=True,tilt=0.0)
            draw_tavern_rail(b,x,25,False,1.0,0.0,now_ms=0,
                             animate=True,tilt=1.0)
            draw_board_spill(b,x,pour=1.0,burn=1.0,now_ms=1175)
        self.assertNotEqual(pygame.image.tobytes(a,'RGB'),
                            pygame.image.tobytes(b,'RGB'))
        # The *board* is visibly wet and burning, not merely the side HUD.
        for xx in (150,940):
            self.assertNotEqual(b.get_at((xx,430)),(9,11,13,255))
        # Both hero/status areas and central card hitboxes remain untouched.
        for px,py in ((300,310),(600,430),(400,465),(600,440),
                      (140,465),(900,465),(1079,460)):
            self.assertEqual(b.get_at((px,py)),(9,11,13,255))

    def test_idle_props_static_with_animations_disabled(self):
        a=pygame.Surface((1080,480));a.fill((9,11,13))
        b=a.copy()
        draw_tavern_rail(a,57,9,False,1.0,1.0,now_ms=0,animate=False,tilt=1)
        draw_tavern_rail(b,57,9,False,1.0,1.0,now_ms=10000,animate=False,tilt=0)
        self.assertEqual(pygame.image.tobytes(a,'RGB'),
                         pygame.image.tobytes(b,'RGB'))


if __name__=='__main__':
    unittest.main()
