"""v0.9.97 pixel candles: deterministic loops and fixed rendering geometry."""
from __future__ import annotations

import unittest

import pygame

from game.ui.beer_fx import candle_frame
from game.ui.tavern_art import draw_tavern_rail


class CandlePixelArt0997(unittest.TestCase):
    def test_four_frames_loop_130ms_one_pixel_sway(self):
        frames=[candle_frame(ms) for ms in (0,130,260,390)]
        self.assertEqual(len(set(frames)),4)
        self.assertEqual(candle_frame(520),frames[0])
        self.assertEqual(candle_frame(259),frames[1])
        for x,y,h in frames:
            self.assertLessEqual(abs(x),1)
            self.assertLessEqual(abs(y),1)
            self.assertLessEqual(abs(h),1)
        self.assertNotEqual(candle_frame(0,phase=2),frames[0])
        self.assertTrue(all(candle_frame(ms,False)==(0,0,0)
                            for ms in range(0,2100,133)))

    def _render(self,ms=0,animate=True,splash=0.0):
        canvas=pygame.Surface((1080,480))
        canvas.fill((9,11,13))
        for x in (57,1020):
            draw_tavern_rail(canvas,x,28,False,1.0,splash,
                             now_ms=ms,animate=animate)
        return canvas

    def test_animated_flames_are_visible_and_toggle_a_freezes_them(self):
        first=self._render(ms=0)
        next_frame=self._render(ms=130)
        left=pygame.Rect(24,273,66,91)
        self.assertNotEqual(
            pygame.image.tobytes(first.subsurface(left),"RGB"),
            pygame.image.tobytes(next_frame.subsurface(left),"RGB"))
        static_a=self._render(ms=0,animate=False)
        static_b=self._render(ms=390,animate=False)
        self.assertEqual(
            pygame.image.tobytes(static_a,"RGB"),
            pygame.image.tobytes(static_b,"RGB"))

    def test_synchronized_flare_only_in_decoration_not_on_cards(self):
        regular=self._render(ms=0,splash=0.0)
        burst=self._render(ms=0,splash=1.0)
        for cx in (57,1020):
            section=pygame.Rect(cx-31,275,62,82)
            self.assertNotEqual(
                pygame.image.tobytes(regular.subsurface(section),"RGB"),
                pygame.image.tobytes(burst.subsurface(section),"RGB"))
        # Neither fixture nor splash may paint into the central five-card rows.
        back=(9,11,13,255)
        for image in (regular,burst):
            for x in (107,120,950,972,980,1080-1):
                if x==107 or x==120 or x==950 or x==972 or x==980:
                    self.assertEqual(image.get_at((x,310)),back)
            self.assertEqual(image.get_at((107,407)),back)
            self.assertEqual(image.get_at((980,407)),back)


if __name__=='__main__':
    unittest.main()
