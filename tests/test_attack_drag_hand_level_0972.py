"""0.9.72: board attack drag and hand-level feedback remain purely visual."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from game.core.engine import Match
from game.core.audit import digest, state_snapshot
from game.ui.app import SoloApp
from game.ui.card_view import CardView, card_zones
from game import config as cfg


class AttackDragAndLevel0972(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp, "_desktop_resolution", return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        for seed in range(300,500):
            game=Match(seed,audit_enabled=True,auctions_enabled=True,
                       auction_catalog='v22',
                       starting_compensation='choice_2_5_or_coins')
            if game.first==0:
                break
        else:
            raise AssertionError("No starting seat found")
        self.app.game=game
        self.app.ai.step(game)
        if 1 not in game.mulligan_done:
            self.app.ai.step(game)
        game.finish_mulligan(0,[])
        self.app._reset_hand_growth_tracking()
        self.app.selected=None
        self.app.drag_start=None
        self.app.drag_pointer=None
        self.app.replay_index=None
        self.app.tutorial_welcome_open=False

    def tearDown(self):
        pygame.quit()

    def event(self,kind,point,**kw):
        evt=pygame.event.Event(kind,{'pos':point,**kw})
        with patch.object(self.app,'_physical_to_virtual',side_effect=lambda p:p):
            return self.app.handle(evt)

    def ready_attacker(self):
        game=self.app.game
        uid=game.players[0].hand[0]
        game.play(uid,slot=0)
        self.assertIn(uid,game.players[0].board)
        game.units[uid].played_turn=-1  # test fixture: ready without extra AI turns
        self.assertIn('hero:1',game.legal_attacks(uid))
        self.app._reset_hand_growth_tracking()
        return uid

    def drag(self,uid,to):
        start=self.app.slot_rect(0,self.app.game.slot_of(uid)).center
        self.event(pygame.MOUSEBUTTONDOWN,start,button=1)
        self.event(pygame.MOUSEMOTION,to,buttons=(1,0,0),
                   rel=(to[0]-start[0],to[1]-start[1]))
        return start

    def test_subtle_attack_drag_tracks_cursor_without_changing_game(self):
        uid=self.ready_attacker()
        app=self.app
        app.selected=next(iter(app.game.players[0].hand),None)
        before=digest(state_snapshot(app.game))
        target=app.hero_rect(1).center
        self.drag(uid,target)
        state=app._attack_drag_state()
        self.assertEqual((state[0],state[1],state[2]),(uid,target,'hero:1'))
        self.assertIn(app.hero_rect(1),app._attack_target_rects())
        # A minimal alpha arrow is allowed; no heavy strokes or outlines.
        self.assertTrue(hasattr(app,'_draw_attack_drag'))
        app.draw()
        self.assertEqual(digest(state_snapshot(app.game)),before)
        other=(570,390)
        self.event(pygame.MOUSEMOTION,other,buttons=(1,0,0),rel=(1,1))
        self.assertEqual(app._attack_drag_state()[1],other)
        self.assertIsNone(app._attack_drag_state()[2])
        self.assertEqual(digest(state_snapshot(app.game)),before)

    def test_drag_render_does_not_draw_old_arrow_stroke_or_head(self):
        """A drag still highlights legal targets; no line/grot follows cursor."""
        uid=self.ready_attacker()
        app=self.app
        app.selected=None  # Drag must work without having clicked an attacker.
        target=app.hero_rect(1).center
        self.drag(uid,target)
        before=digest(state_snapshot(app.game))
        with patch("game.ui.app.pygame.draw.line",
                   wraps=pygame.draw.line) as lines:
            with patch("game.ui.app.pygame.draw.polygon",
                       wraps=pygame.draw.polygon) as polygons:
                app.draw()
        forbidden={(109,244,225),(233,177,100),(17,29,38)}
        # Distinctive colors of the removed arrow's shaft, border and tip.
        for mock in (lines,polygons):
            for call in mock.call_args_list:
                if len(call.args)>=2:
                    self.assertNotIn(call.args[1],forbidden)
        self.assertIn(app.hero_rect(1),app._attack_target_rects())
        self.assertEqual(digest(state_snapshot(app.game)),before)

    def test_subtle_arrow_is_rgba_two_pixel_stroke_and_small_tip(self):
        uid=self.ready_attacker()
        app=self.app
        app.selected=None
        target=app.hero_rect(1).center
        self.drag(uid,target)
        before=digest(state_snapshot(app.game))
        real_line=pygame.draw.line
        real_poly=pygame.draw.polygon
        with patch('game.ui.app.pygame.draw.line',wraps=real_line) as strokes:
            with patch('game.ui.app.pygame.draw.polygon',wraps=real_poly) as heads:
                app._draw_attack_drag()
        self.assertEqual(strokes.call_count,1)
        self.assertEqual(heads.call_count,1)
        line=strokes.call_args.args
        triangle=heads.call_args.args
        self.assertEqual(line[1],(207,84,96,77))
        self.assertEqual(line[4],2)
        self.assertEqual(triangle[1],(207,84,96,77))
        self.assertEqual(len(triangle[2]),3)
        self.assertEqual(digest(state_snapshot(app.game)),before)
        # In a non-target part of the board the cue becomes even fainter.
        other=(570,390)
        self.event(pygame.MOUSEMOTION,other,buttons=(1,0,0),rel=(1,1))
        with patch('game.ui.app.pygame.draw.line',wraps=real_line) as strokes:
            app._draw_attack_drag()
        self.assertEqual(strokes.call_args.args[1],(207,84,96,49))
        self.assertEqual(digest(state_snapshot(app.game)),before)

    def test_no_arrow_if_no_attack_drag_or_pointer_still_on_source(self):
        app=self.app
        real_line=pygame.draw.line
        with patch('game.ui.app.pygame.draw.line',wraps=real_line) as strokes:
            app._draw_attack_drag()
            uid=self.ready_attacker()
            start=app.slot_rect(0,app.game.slot_of(uid)).center
            self.event(pygame.MOUSEBUTTONDOWN,start,button=1)
            self.event(pygame.MOUSEMOTION,(start[0]+11,start[1]),
                       buttons=(1,0,0),rel=(11,0))
            app._draw_attack_drag()
        self.assertEqual(strokes.call_count,0)

    def test_release_on_hero_attacks_once(self):
        uid=self.ready_attacker()
        app=self.app
        target=app.hero_rect(1).center
        before=app.game.players[1].hp
        self.drag(uid,target)
        self.assertTrue(self.event(pygame.MOUSEBUTTONUP,target,button=1))
        self.assertLess(app.game.players[1].hp,before)
        self.assertEqual(app.game.units[uid].attacks,1)
        self.assertIsNone(app.drag_start)
        self.assertIsNone(app.drag_pointer)

    def test_invalid_drop_and_exhausted_unit_are_noops(self):
        uid=self.ready_attacker()
        app=self.app
        before=digest(state_snapshot(app.game))
        point=(650,393)  # corridor between the two board rows
        self.drag(uid,point)
        self.assertIsNone(app._attack_drag_state()[2])
        self.assertTrue(self.event(pygame.MOUSEBUTTONUP,point,button=1))
        self.assertEqual(digest(state_snapshot(app.game)),before)
        app.game.units[uid].attacks=2
        before=digest(state_snapshot(app.game))
        self.drag(uid,app.hero_rect(1).center)
        self.assertIsNone(app._attack_drag_state())
        self.assertTrue(self.event(pygame.MOUSEBUTTONUP,app.hero_rect(1).center,button=1))
        self.assertEqual(digest(state_snapshot(app.game)),before)

    def test_short_click_on_attacker_keeps_original_selection(self):
        uid=self.ready_attacker()
        spot=self.app.slot_rect(0,0).center
        self.event(pygame.MOUSEBUTTONDOWN,spot,button=1)
        self.assertIsNone(self.app._attack_drag_state())
        self.event(pygame.MOUSEBUTTONUP,spot,button=1)
        self.assertEqual(self.app.selected,uid)

    def test_level_event_only_on_actual_three_turn_threshold(self):
        app=self.app
        uid=app.game.players[0].hand[0]
        card=app.game.cards[uid]
        card.hand_turns=2
        app._reset_hand_growth_tracking()
        old=(card.attack,card.max_hp)
        app._sync_hand_growth(now=990)
        self.assertNotIn(uid,app._hand_level_fx)
        card.hand_turns=3
        with patch('game.ui.app.pygame.time.get_ticks',return_value=1000):
            app._sync_hand_growth()
            fx=app._hand_level_fx[uid]
            self.assertEqual(fx[1],1)
            self.assertEqual(fx[2:],(card.attack-old[0],card.max_hp-old[1]))
            before=digest(state_snapshot(app.game))
            app._draw_hand_level_fx(uid,app.hand_layout()[uid])
            self.assertEqual(digest(state_snapshot(app.game)),before)
        with patch('game.ui.app.pygame.time.get_ticks',return_value=2051):
            app._sync_hand_growth()
        self.assertNotIn(uid,app._hand_level_fx)

    def test_progress_bar_uses_exact_hand_turns_mod_three(self):
        app=self.app
        uid=app.game.players[0].hand[0]
        card=app.game.cards[uid]
        rect=pygame.Rect(30,30,125,195)
        art=card_zones(rect)['art']
        x=art.x+3+10
        y=art.bottom-4
        screen=pygame.Surface((240,280))
        for steps,expected in ((0,(21,36,33)),(1,(147,235,172)),
                               (2,(147,235,172)),(3,(21,36,33))):
            card.hand_turns=steps
            screen.fill(cfg.BACKGROUND)
            app.cards_view.draw(screen,card,rect)
            self.assertEqual(screen.get_at((x,y))[:3],expected)

    def test_loaded_game_baseline_does_not_create_false_level_event(self):
        app=self.app
        uid=app.game.players[0].hand[0]
        app.game.cards[uid].hand_turns=6
        app._reset_hand_growth_tracking()
        app._sync_hand_growth(now=1000)
        self.assertFalse(app._hand_level_fx)
        self.assertEqual(app._hand_growth_seen[uid][0],6)
        app.animations_enabled=False
        app.game.cards[uid].hand_turns=9
        app._sync_hand_growth(now=1020)
        self.assertFalse(app._hand_level_fx)


if __name__=="__main__":
    unittest.main()
