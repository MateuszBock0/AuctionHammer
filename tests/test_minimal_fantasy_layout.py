"""Kontrola Minimal Fantasy: rozmiary, bezkolizyjne strefy i dane silnika v19."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
try:
    import pygame
except ImportError:
    pygame=None

from game import config
from game.ui.card_infographics import card_cue
from test_engine import setup_game,force_unit


@unittest.skipIf(pygame is None,'Brak pygame-ce')
class MinimalFantasyLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1480,980))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_approved_sizes_and_nonoverlapping_zones(self):
        from game.ui.card_view import card_zones
        for width,height in ((125,195),(148,220),(255,380)):
            with self.subTest(size=(width,height)):
                rect=pygame.Rect(12,18,width,height)
                z=card_zones(rect)
                for name,r in z.items():
                    self.assertGreater(r.width,0,(name,r))
                    self.assertGreater(r.height,0,(name,r))
                    self.assertTrue(rect.contains(r),(name,r))
                sequence=('name','trigger','art','info','stats')
                for name1,name2 in zip(sequence,sequence[1:]):
                    self.assertLessEqual(z[name1].bottom,z[name2].top)
                    self.assertFalse(z[name1].colliderect(z[name2]))

    def test_render_all_70_cards_at_each_real_size(self):
        from game.ui.card_view import CardView
        game=setup_game(1005)
        view=CardView()
        screen=pygame.Surface((650,640))
        self.assertEqual(len(game.cards),70)
        for card in game.cards.values():
            for size in ((125,195),(148,220),(255,380)):
                with self.subTest(uid=card.uid,size=size):
                    view.draw(screen,card,pygame.Rect(20,25,*size))
        self.assertEqual(len(view.artcache),63*3)

    def test_deployed_statuses_and_high_stats_do_not_break_draw(self):
        from game.ui.card_view import CardView
        from game.core.status_view import active_statuses
        game=setup_game(1006)
        unit=force_unit(game,'S115',0)
        unit.base_attack=100
        unit.base_max_hp=180
        unit.hp=80
        unit.shield=1
        unit.armor_perm=4
        game._add_poison('S115',2,3,'S83',0)
        statuses=active_statuses(game,'S115')
        view=CardView()
        screen=pygame.Surface((600,600))
        for rect in (pygame.Rect(4,4,148,220),pygame.Rect(170,4,255,380)):
            view.draw(screen,game.cards['S115'],rect,unit,dim=True,
                      statuses=statuses,ready=True,attacks_remaining=1,attacks_total=2)
        self.assertGreaterEqual(len(statuses),3)

    def test_hand_growth_and_quality_are_tied_to_real_card_instance(self):
        game=setup_game(1007)
        card=game.cards['S01']
        for hand_turns in (0,1,2,3,4,6,9):
            card.hand_turns=hand_turns
            with self.subTest(turns=hand_turns):
                info=card_cue(card)
                self.assertEqual(info.ability_level,hand_turns//3)
                self.assertIn('3T',info.upgrade)
                self.assertEqual(info.next_threshold.startswith('ZA') or
                                 info.next_threshold=='POZIOM UTRWALONY',True)


@unittest.skipIf(pygame is None,'Brak pygame-ce')
class MinimalFantasyAppIntegration(unittest.TestCase):
    def setUp(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp()

    def tearDown(self):
        pygame.quit()

    def test_real_card_rectangles_fit_new_canvas_and_do_not_collide(self):
        self.assertEqual(self.app.screen.get_size(),(1480,980))
        app=self.app
        self.assertEqual((app.SLOT_W,app.SLOT_H),(148,220))
        self.assertEqual((app.HAND_W,app.HAND_H),(125,195))
        rects=[app.slot_rect(1,i) for i in range(5)]
        rects+=[app.slot_rect(0,i) for i in range(5)]
        rects+=list(app.hand_layout().values())
        rects+=[app.hero_rect(0),app.hero_rect(1)]
        for i,a in enumerate(rects):
            self.assertTrue(pygame.Rect(0,0,1480,980).contains(a),a)
            for b in rects[i+1:]:
                self.assertFalse(a.colliderect(b),(a,b))
        self.app.draw()

    def test_all_visible_hand_cards_map_to_rendered_hitbox(self):
        from game.ui.layout import canvas_to_window
        view=tuple(self.app._viewport())
        for uid,rect in self.app.hand_layout().items():
            mapped=self.app._physical_to_virtual(canvas_to_window(
                rect.center,view,(1480,980)))
            self.assertEqual(self.app.card_under(mapped),uid)

    def test_attack_highlight_uses_actual_engine_legal_targets(self):
        from test_engine import force_unit
        app=self.app
        game=app.game
        if game.phase=='mulligan':
            game.finish_mulligan(0,[])
        if game.phase!='turn':
            game.finish_mulligan(1,[])
        game.active=0
        if game.players[0].turn_count==0:game.players[0].turn_count=1
        unit=force_unit(game,'S01',0)
        unit.played_turn=0
        defender=force_unit(game,'S33',1)  # provoke must force legal choice
        defender.played_turn=0
        app.selected='S01'
        legal=game.legal_attacks('S01')
        self.assertEqual(legal,['S33'])
        boxes=app._attack_target_rects()
        self.assertEqual(boxes,[app.slot_rect(1,game.players[1].board.index('S33'))])
        self.assertNotIn(app.hero_rect(1),boxes)

    def test_event_animation_is_optional_and_read_only(self):
        game=self.app.game
        previous=(game.phase,game.active,len(game.events))
        self.assertTrue(self.app.animations_enabled)
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_a}))
        self.assertFalse(self.app.animations_enabled)
        game._log('Jednostka otrzymuje 3 obrażenia.')
        self.app._capture_visual_feedback()
        self.assertEqual(self.app._recent_feedback,[])
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_a}))
        self.assertTrue(self.app.animations_enabled)
        game._log('Jednostka otrzymuje tarczę.')
        self.app._capture_visual_feedback()
        self.assertTrue(self.app._recent_feedback)
        self.assertEqual((game.phase,game.active),(previous[0],previous[1]))
        self.assertEqual(len(game.events),previous[2]+2)

    def test_right_click_opens_details_and_left_click_only_selects(self):
        uid,rect=next(iter(self.app.hand_layout().items()))
        self.app.click(rect.center)
        self.assertEqual(self.app.selected,uid)
        self.assertIsNone(self.app.details_card)
        from game.ui.layout import canvas_to_window
        pos=canvas_to_window(rect.center,tuple(self.app._viewport()),(1480,980))
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         {'button':3,'pos':pos}))
        self.assertEqual(self.app.details_card,uid)
        self.app.draw()


if __name__=='__main__':
    unittest.main()
