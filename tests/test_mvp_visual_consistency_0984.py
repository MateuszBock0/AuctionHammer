"""0.9.84: measurable MVP-only pixel-art, combat, auction and HUD regressions."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.audit import digest,state_snapshot
from game.ui.app import SoloApp
from game.ui.aura_links import live_aura_links
from game.ui.assets import ImageAssets
from game.ui.combat_visuals import CombatVisuals,Pulse
from test_engine import setup_game,force_unit
from test_auction_foundation_0921 import ready as auction_ready


class MVPVisualConsistency0984(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self.app.tutorial_welcome_open=False
        g=setup_game(984001)
        g.fixed_board_slots=True
        g.phase='turn'
        g.active=0
        self.app.game=g
        self.app.selected=None

    def tearDown(self):
        pygame.quit()

    def test_all_same_owner_aura_segments_avoid_cards_hero_bars_and_phase_hud(self):
        app=self.app
        phase=pygame.Rect(96,372,952,56)
        for owner in (0,1):
            ownhero=app.hero_rect(owner)
            for source in range(5):
                for target in range(5):
                    if source==target:
                        continue
                    path=app._aura_connector_path(
                        app.slot_rect(owner,source),
                        app.slot_rect(owner,target),owner,owner)
                    self.assertEqual(len(path),4)
                    lane=path[1][1]
                    self.assertEqual(lane,656 if owner==0 else 147)
                    for a,c in zip(path,path[1:]):
                        self.assertTrue(a[0]==c[0] or a[1]==c[1])
                        self.assertFalse(phase.clipline(a,c),
                                         (owner,source,target,a,c))
                        self.assertFalse(ownhero.clipline(a,c),
                                         (owner,source,target,a,c))
                        for column in range(5):
                            block=app.slot_rect(owner,column).inflate(-2,-2)
                            self.assertFalse(block.clipline(a,c),
                                             (owner,source,target,column))

    def test_cross_row_aura_keeps_factual_badge_without_hud_crossing_lines(self):
        app=self.app
        g=app.game
        src=force_unit(g,'S34',0,slot=2)
        src.ability_level=1
        src.aura_mode='enemy'
        force_unit(g,'S09',1,slot=2)
        g._update_auras()
        self.assertEqual(len(live_aura_links(g,'S34')),1)
        app.selected='S34'
        before=digest(state_snapshot(g))
        with patch.object(app,'_aura_focus',return_value='S34'):
            with patch('game.ui.app.pygame.draw.line',
                       wraps=pygame.draw.line) as strokes:
                app._draw_aura_links()
        self.assertEqual(strokes.call_count,0)
        self.assertEqual(digest(state_snapshot(g)),before)

    def test_preview_does_not_obscure_targets_while_attacker_selected(self):
        app=self.app
        g=app.game
        src=force_unit(g,'S01',0,slot=0)
        src.played_turn=-1
        src.attacks=0
        force_unit(g,'S09',1,slot=2)
        self.assertTrue(g.legal_attacks('S01'))
        app._hover_uid='S09'
        app._hover_start_ms=0
        now=app.HOVER_PREVIEW_DELAY_MS+200
        app.selected='S01'
        self.assertFalse(app._hover_preview_ready(now=now))
        app.selected=None
        self.assertTrue(app._hover_preview_ready(now=now))

    def test_viewport_uses_nearest_neighbour_scaling_even_on_fractional_sizes(self):
        app=self.app
        app.window=pygame.Surface((1000,740))
        with patch.object(app,'_viewport',return_value=pygame.Rect(0,0,1000,740)):
            with patch('game.ui.app.pygame.transform.smoothscale',
                       side_effect=AssertionError('Blurry global pixel-art scaling')):
                with patch('game.ui.app.pygame.transform.scale',
                           wraps=pygame.transform.scale) as resize:
                    app._present()
        resize.assert_called_once()
        self.assertIs(resize.call_args.args[0],app.screen)
        self.assertEqual(resize.call_args.args[1],(1000,740))

    def test_auction_hover_brackets_only_for_selectable_offer(self):
        app=self.app
        app.game=auction_ready(984002)
        app.auction_inspect_index=None
        # During bidding no card is selectable; the cursor must not promise it.
        rect=app.auction_offer_rect(0)
        with patch.object(app,'mouse_pos',return_value=rect.center):
            with patch.object(app,'_pixel_attack_corners',
                              wraps=app._pixel_attack_corners) as brackets:
                app._draw_auction()
        brackets.assert_not_called()
        # After both passes, the picker can actually select an offer.
        a=app.game.auction
        app.game.auction_pass(a.turn)
        app.game.auction_pass(app.game.auction.turn)
        a.turn=0
        before=digest(state_snapshot(app.game))
        with patch.object(app,'mouse_pos',return_value=rect.center):
            with patch.object(app,'_pixel_attack_corners',
                              wraps=app._pixel_attack_corners) as brackets:
                app._draw_auction()
        self.assertEqual(brackets.call_count,1)
        self.assertEqual(digest(state_snapshot(app.game)),before)

    def test_target_hover_draws_only_frame_and_corners_not_text_over_faces(self):
        app=self.app
        rect=pygame.Rect(300,152,148,220)
        with patch.object(app,'_attack_target_rects',return_value=[rect]):
            with patch.object(app,'mouse_pos',return_value=rect.center):
                with patch.object(app,'_pixel_attack_corners',
                                  wraps=app._pixel_attack_corners) as corners:
                    with patch('game.ui.app.pygame.Surface.blit',
                               wraps=pygame.Surface.blit) as blit:
                        app._draw_attack_targets()
        corners.assert_called_once()
        # The actual target-feedback renderer creates no rendered ATAKUJ
        # plaque above faces; image and card art remain untouched.
        self.assertEqual(blit.call_count,0)

    def test_legacy_auction_sprite_fallback_is_crisp(self):
        assets=ImageAssets()
        source=pygame.Surface((2,2),pygame.SRCALPHA)
        source.fill((245,22,24),pygame.Rect(0,0,1,2))
        source.fill((22,51,239),pygame.Rect(1,0,1,2))
        assets._original['auction/archive.png']=source
        assets._auction_colors['auction/archive.png']=(60,60,60)
        with patch.object(assets,'_auction_final',return_value=None):
            with patch.object(assets,'_auction_base',
                              return_value='auction/archive.png'):
                with patch('game.ui.assets.pygame.transform.smoothscale',
                           side_effect=AssertionError('Pixel art must not blur')):
                    image=assets.get_auction_image('A001','rzadka',
                                                   (80,60),mode='contain')
        self.assertEqual(image.get_at((20,30))[:3],(245,22,24))
        self.assertEqual(image.get_at((60,30))[:3],(22,51,239))


class PixelCombatImpact0984(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_attack_projectile_uses_8bit_rectangles_not_round_glow(self):
        visuals=CombatVisuals()
        visuals.pulses=[Pulse('attack',(250,125),100,origin=(60,70))]
        screen=pygame.Surface((380,250))
        font=pygame.font.Font(None,16)
        with patch('game.ui.combat_visuals.pygame.draw.circle',
                   side_effect=AssertionError('Round attack aura is not pixel art')):
            visuals.draw(screen,260,font)
        self.assertEqual(len(visuals.pulses),1)

    def test_committed_impact_outline_uses_only_hard_pixel_brackets(self):
        visuals=CombatVisuals()
        screen=pygame.Surface((380,260),pygame.SRCALPHA)
        rect=pygame.Rect(101,20,148,220)
        with patch('game.ui.combat_visuals.pygame.draw.rect',
                   wraps=pygame.draw.rect) as rectangles:
            with patch('game.ui.combat_visuals.pygame.draw.line',
                       wraps=pygame.draw.line) as lines:
                visuals._combat_outline(screen,rect,0)
        self.assertEqual(lines.call_count,8)
        rectangles.assert_not_called()


if __name__=='__main__':
    unittest.main()
