"""Integration and visual checks for actual rarity/tier abilities and V3 auctions."""
import os
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.audit import make_report,verify_replay
from game.core.auction_catalog import CATALOG,stats
from game.core.auction_skills import options
from test_auction_v3_0920 import game_for,add,choose


class AuctionV3IntegrationTests(unittest.TestCase):
    def test_full_game_completes_and_audit_replays_exactly(self):
        game=Match(9320,audit_enabled=True,auctions_enabled=True,auction_catalog_mode='v3')
        agents=(ComputerOpponent(0,'normalny'),ComputerOpponent(1,'normalny'))
        seen=0
        for _ in range(1800):
            if game.phase=='finished':break
            if game.phase=='mulligan':
                for agent in agents:agent.step(game)
            elif game.phase=='auction':
                seen+=1
                agents[game.auction.turn].step(game)
            elif game.pending:
                agents[game.pending.owner].step(game)
            else:
                agents[game.active].step(game)
            game.assert_integrity()
        self.assertEqual(game.phase,'finished')
        self.assertGreater(seen,0)
        self.assertGreater(len(game.auction_history),0)
        data=make_report(game)['payload']
        self.assertTrue(verify_replay(
            data,lambda seed,auctions_enabled=False,auction_catalog_mode='placeholders':
                Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
                      auction_catalog_mode=auction_catalog_mode)))

    def test_v3_offer_labels_and_cards_do_not_overlap_on_canvas(self):
        from game.ui.app import SoloApp
        pygame.init()
        try:
            with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
                app=SoloApp()
            game=Match(9321,auctions_enabled=True,auction_catalog_mode='v3')
            game.finish_mulligan(0,[]);game.finish_mulligan(1,[])
            for _ in range(6):game.end_turn()
            self.assertEqual(game.phase,'auction')
            app.game=game
            texts=[]
            original=app._text
            def watch(t,size,x,y,color=None,center=False):
                rect=original(t,size,x,y,color,center)
                texts.append((str(t),rect))
                return rect
            with patch.object(app,'_text',side_effect=watch):
                app._draw_auction()
            bound=pygame.Rect(203,112,1076,732)
            for name,rect in texts:
                self.assertTrue(bound.contains(rect),(name,rect))
            for i,(a,ra) in enumerate(texts):
                for b,rb in texts[i+1:]:
                    self.assertFalse(ra.colliderect(rb),(a,ra,b,rb))
        finally:
            pygame.quit()

    def test_catalog_is_implemented_separately_from_old_70_cards(self):
        old=Match(9322)
        new=Match(9322,auctions_enabled=True,auction_catalog_mode='v3')
        self.assertEqual(set(old.defs),set(new.defs))
        self.assertEqual(len(CATALOG),12)
        self.assertEqual(len(old.cards),70)
        self.assertEqual(len(new.cards),70)


if __name__=='__main__':unittest.main()
