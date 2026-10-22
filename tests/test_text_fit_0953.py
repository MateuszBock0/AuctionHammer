"""0.9.53: pixel-based description containment for all 70+51 cards."""
import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from game.core.engine import Match
from game.core.models import Card,CardDefinition
from game.core.auction_catalog import CATALOG_V22,RARITIES,TRIGGER,live_variant,stats_v22
from game.ui.card_view import CardView,card_zones
from game.ui.text_fit import clip_pixels,wrap_pixels


class DescriptionBounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.view=CardView()
        cls.base=list(Match(95300).cards.values())
        cls.auction=[]
        for ident,a in CATALOG_V22.items():
            for rarity in RARITIES:
                atk,hp=stats_v22(ident,3)
                definition=CardDefinition(
                    ident,a.name,'Ludzie',a.family,TRIGGER[a.trigger],
                    atk,hp,live_variant('v22',ident,rarity),'v22',0,0)
                cls.auction.append(Card(
                    f'{ident}-{rarity}',definition,owner=0,zone='hand'))
        assert len(cls.base)==70 and len(cls.auction)==51

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_121_descriptions_stay_within_card_info_zones(self):
        for width,height in ((125,195),(148,220),(255,380)):
            rect=pygame.Rect(12,13,width,height)
            info=card_zones(rect)['info']
            self.assertGreater(info.height,0)
            for c in self.base+self.auction:
                with self.subTest(card=c.uid,size=rect.size):
                    plan=self.view.summary_layout(c,rect)
                    regions=[plan['family'],plan['footer'],*plan['boxes']]
                    if plan['main'] is not None:
                        regions.append(plan['main'])
                    for block in regions:
                        self.assertTrue(info.contains(block),(c.uid,rect.size,block,info))
                    for line,box in zip(plan['lines'],plan['boxes']):
                        self.assertLessEqual(plan['font'].size(line)[0],box.width,
                                             (c.uid,rect.size,line))
                        self.assertLessEqual(plan['font'].get_height(),box.height)
                        self.assertLessEqual(box.bottom,plan['footer'].top)
                    self.assertLessEqual(plan['family'].bottom,
                                         (plan['main'] or plan['footer']).top)

    def test_unbroken_polish_and_symbols_never_overflow(self):
        f=self.view.font(13)
        sample='ŻółwĘóśĆćŁŁ' * 40
        for width in (37,71,113,185,322,853):
            with self.subTest(width=width):
                clipped=clip_pixels(sample,f,width)
                self.assertLessEqual(f.size(clipped)[0],width)
                all_lines=wrap_pixels('Użyj '+sample+' teraz',f,width)
                self.assertTrue(all_lines)
                self.assertTrue(all(f.size(line)[0]<=width for line in all_lines))
                abbreviated=wrap_pixels('Użyj '+sample+' teraz',f,width,max_lines=3)
                self.assertLessEqual(len(abbreviated),3)
                self.assertTrue(all(f.size(line)[0]<=width for line in abbreviated))
                self.assertTrue(abbreviated[-1].endswith('…'))

    def test_all_51_auction_snippets_fit_four_line_offer_panels(self):
        f=self.view.font(13)
        for ident,a in CATALOG_V22.items():
            for rarity in RARITIES:
                lines=wrap_pixels(live_variant('v22',ident,rarity),f,
                                  278-36,max_lines=4)
                self.assertLessEqual(len(lines),4)
                self.assertTrue(all(f.size(line)[0]<=242 for line in lines),
                                (ident,rarity,lines))

    def test_auction_inspection_can_show_full_unbroken_text_without_loss(self):
        f=self.view.font(18)
        sample=('BardzoDługaZdolnośćBezSpacji'*38)+' końcowa reguła.'
        lines=wrap_pixels(sample,f,853)
        self.assertGreater(len(lines),12)
        self.assertTrue(all(f.size(line)[0]<=853 for line in lines))
        # The modal scrolls through the complete wrapped list, it never
        # discards lines as the short four-line offer preview must do.
        self.assertIn('końcowa',lines[-1])


if __name__=='__main__':
    unittest.main()
