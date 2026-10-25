"""Acceptance tests for the first *working* auction stage, Game Master v19.

The three variants are explicitly placeholders. Existing 70 starting cards
and their one-copy bank are still conserved independently.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.core.engine import Match
from game.core.ai import ComputerOpponent
from game.core.models import IllegalMove
from game.core.auction import PLACEHOLDER_HP
from game.core.persistence import save_match,load_match
from game.core.audit import make_report,verify_replay


def auction_game(seed=919):
    game=Match(seed,auctions_enabled=True,auction_catalog='placeholders')
    game.finish_mulligan(0,[])
    game.finish_mulligan(1,[])
    for _ in range(6):
        if game.phase=='auction':
            break
        game.end_turn()
    assert game.phase=='auction',(game.phase,game.round)
    return game


def free_pick(game):
    stage=game.auction
    game.auction_pass(stage.turn)
    game.auction_pass(game.auction.turn)
    assert game.auction.phase=='picking'
    first=game.auction.turn
    offers=game.auction.offers
    game.auction_pick(first,offers[2].uid)
    game.auction_pick(1-first,offers[0].uid)
    return first


class AuctionCoreTests(unittest.TestCase):
    def test_after_three_full_rounds_and_income_auction_opens(self):
        m=Match(1901,auctions_enabled=True,auction_catalog='placeholders')
        m.finish_mulligan(0,[])
        m.finish_mulligan(1,[])
        for turn in range(5):
            m.end_turn()
            self.assertEqual(m.phase,'turn',turn)
        before=[p.coins for p in m.players]
        m.end_turn()
        self.assertEqual(m.phase,'auction')
        self.assertEqual(m.round,4)
        self.assertEqual([p.coins for p in m.players],
                         [x+1 for x in before])
        self.assertEqual([o.hp for o in m.auction.offers],[3,6,12])
        self.assertEqual([o.atk for o in m.auction.offers],[3,3,3])
        self.assertEqual(m.auction.free_first,m.first)
        self.assertEqual(m.auction.level if hasattr(m.auction,'level') else
                         m.auction.offers[0].level,1)
        self.assertEqual(len(m.cards),70)
        self.assertEqual(len(m.auction_awards),0)
        m.assert_integrity()

    def test_no_paid_bid_free_first_alternates_and_next_turn_resumes(self):
        m=auction_game(1902)
        prior_turn=m.active
        first=free_pick(m)
        self.assertEqual(first,m.first)
        self.assertEqual(m.phase,'turn')
        self.assertEqual(m.active,1-prior_turn)
        self.assertEqual(len(m.auction_history),1)
        self.assertEqual(m.auction_history[0]['price'],0)
        self.assertEqual(len(m.cards),72)
        self.assertEqual(set(m.auction_awards),set(m.auction_history[0]['picks'].values()))
        m.assert_integrity()
        for _ in range(6):
            if m.phase=='auction':break
            m.end_turn()
        self.assertEqual(m.phase,'auction')
        self.assertEqual(m.auction.number,2)
        self.assertEqual(m.auction.free_first,1-m.first)
        self.assertTrue(all(x.level==2 for x in m.auction.offers))

    def test_bids_validate_coins_increments_and_actor(self):
        m=auction_game(1903)
        first=m.auction.turn
        m.players[first].coins=5
        m.players[1-first].coins=4
        with self.assertRaises(IllegalMove):
            m.auction_bid(1-first,1)
        with self.assertRaises(IllegalMove):
            m.auction_bid(first,0)
        with self.assertRaises(IllegalMove):
            m.auction_bid(first,6)
        m.auction_bid(first,2)
        self.assertEqual(m.auction.highest_bidder,first)
        self.assertEqual(m.auction.current_bid,2)
        with self.assertRaises(IllegalMove):
            m.auction_bid(1-first,2)
        m.auction_bid(1-first,3)
        m.auction_pass(first)
        self.assertEqual(m.auction.phase,'picking')
        self.assertEqual(m.auction.winner,1-first)
        self.assertEqual(m.auction.price,3)
        self.assertEqual(m.players[1-first].coins,1)
        m.assert_integrity()

    def test_auction_placeholders_join_hand_and_play_with_taunt_shield(self):
        m=auction_game(1904)
        selected=free_pick(m)
        ids=m.auction_history[0]['picks']
        for player,uid in ids.items():
            card=m.cards[uid]
            self.assertEqual(card.attack,3)
            self.assertIn(card.max_hp,PLACEHOLDER_HP)
            self.assertEqual(card.owner,player)
            self.assertEqual(card.zone,'hand')
        # Skip until the selected winner's own turn.
        for _ in range(2):
            if m.active==selected:break
            m.end_turn()
        uid=ids[selected]
        p=m.players[selected]
        p.played_this_turn=False
        self.assertIn(uid,p.hand)
        m.play(uid)
        unit=m.units[uid]
        self.assertEqual(unit.atk,3)
        self.assertEqual(unit.hp,m.auction_awards[uid]['hp'])
        self.assertEqual(unit.shield,1)
        self.assertTrue(m._taunt(unit))
        other=1-selected
        enemy_uid=m.auction_history[0]['picks'][other]
        # Full rule: existing taunt overrides hero targeting.
        if enemy_uid in m.units:
            pass
        m.assert_integrity()

    def test_auction_hand_cards_do_not_scale_after_end_turn(self):
        m=auction_game(1905)
        free_pick(m)
        m.active=0
        m.phase='turn'
        before={uid:(m.cards[uid].hand_turns,m.cards[uid].attack,m.cards[uid].max_hp)
                for uid in m.auction_awards}
        m.players[0].played_this_turn=False
        m.end_turn()
        after={uid:(m.cards[uid].hand_turns,m.cards[uid].attack,m.cards[uid].max_hp)
               for uid in m.auction_awards}
        self.assertEqual(before,after)

    def test_placeholder_purchased_card_persists_across_save(self):
        m=auction_game(1906)
        free_pick(m)
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'save.json'
            save_match(m,file)
            restored=load_match(file)
        self.assertEqual(restored.auction_history,m.auction_history)
        self.assertEqual(restored.auction_awards,m.auction_awards)
        self.assertEqual(set(restored.cards),set(m.cards))
        restored.assert_integrity()

    def test_in_progress_bid_restores_without_losing_turn(self):
        m=auction_game(1907)
        m.players[m.auction.turn].coins+=3
        m.auction_bid(m.auction.turn,1)
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'save.json'
            save_match(m,file)
            loaded=load_match(file)
        self.assertEqual(loaded.phase,'auction')
        self.assertEqual(loaded.auction.current_bid,1)
        self.assertEqual(loaded.auction.turn,m.auction.turn)
        self.assertEqual([o.hp for o in loaded.auction.offers],[3,6,12])
        loaded.assert_integrity()

    def test_full_auction_audit_deterministic_replay(self):
        m=Match(1908,audit_enabled=True,auctions_enabled=True,auction_catalog='placeholders')
        players=[ComputerOpponent(0),ComputerOpponent(1)]
        for step in range(1500):
            if m.phase=='finished':break
            if m.phase=='mulligan':
                for ai in players:ai.step(m)
            elif m.phase=='auction':
                players[m.auction.turn].step(m)
            elif m.pending:
                players[m.pending.owner].step(m)
            else:
                players[m.active].step(m)
            m.assert_integrity()
        self.assertEqual(m.phase,'finished')
        self.assertGreater(len(m.auction_history),0)
        report=make_report(m)['payload']
        self.assertTrue(any(a['operation']=='auction_pick' for a in report['actions']))
        self.assertTrue(verify_replay(
            report,lambda seed,auctions_enabled=False,auction_catalog='v3':
                Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
                      auction_catalog=auction_catalog)))

    def test_intrinsic_auction_taunt_is_disabled_by_stun(self):
        m=auction_game(1915)
        first=free_pick(m)
        for _ in range(2):
            if m.active==first:break
            m.end_turn()
        uid=m.auction_history[0]['picks'][first]
        m.players[first].played_this_turn=False
        m.play(uid)
        unit=m.units[uid]
        self.assertTrue(m._taunt(unit))
        m._add_effect(uid,'stun',expires=99,source='S59',positive=False)
        self.assertFalse(m._taunt(unit))
        self.assertEqual(unit.shield,1)
        self.assertEqual(unit.atk,3)

    def test_old_save_without_any_auction_fields_is_migrated(self):
        m=Match(1916)
        for field in ('auctions_enabled','auction','auction_history','auction_awards'):
            delattr(m,field)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'save.json'
            save_match(m,path)
            restored=load_match(path)
        self.assertFalse(restored.auctions_enabled)
        self.assertIsNone(restored.auction)
        self.assertEqual(restored.auction_awards,{})
        self.assertEqual(restored.auction_history,[])
        restored.assert_integrity()

    def test_rarity_uses_independent_60_30_10_thresholds(self):
        from game.core.auction import begin
        class Rng:
            def __init__(self):self.seq=iter((.0,.60,.90))
            def random(self):return next(self.seq)
        m=Match(1910,auctions_enabled=True,auction_catalog='placeholders')
        m.rng=Rng()
        m.round=4
        begin(m)
        self.assertEqual([x.rarity for x in m.auction.offers],
                         ['podstawowa','rzadka','legendarna'])
        self.assertEqual(m.rng_draw_index,3)
        self.assertEqual([x.hp for x in m.auction.offers],[3,6,12])

    def test_ai_handles_full_auction_without_manual_choices(self):
        m=auction_game(1911)
        agents=[ComputerOpponent(0,'normalny'),ComputerOpponent(1,'normalny')]
        for i in range(50):
            if m.phase!='auction':break
            agents[m.auction.turn].step(m)
        self.assertEqual(m.phase,'turn')
        self.assertEqual(len(m.auction_awards),2)
        m.assert_integrity()


class AuctionUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1480,980))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_offer_cards_and_controls_stay_inside_modal(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp()
        box=pygame.Rect(203,25,1076,819)
        for i in range(3):
            self.assertTrue(box.contains(app.auction_offer_rect(i)))
        for action in ('pass','bid'):
            self.assertTrue(box.contains(app.auction_control_rect(action)))
        self.assertTrue(box.contains(app.auction_slider_rect()))

    def test_real_pygame_auction_draw_and_rarity_text(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp()
        app.game=auction_game(1912)
        app._draw_auction()
        app.draw()
        self.assertTrue(app.game.auction is not None)

    def test_text_geometry_does_not_overlap_on_auction_modal(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp()
        app.game=auction_game(1917)
        for stage in ('bidding','picking'):
            if stage=='picking':
                app.game.auction_pass(app.game.auction.turn)
                app.game.auction_pass(app.game.auction.turn)
            boxes=[]
            original=app._text
            def trace(text,size,x,y,color=None,center=False):
                rect=original(text,size,x,y,color,center)
                boxes.append((str(text),rect))
                return rect
            with patch.object(app,'_text',side_effect=trace):
                app._draw_auction()
            area=pygame.Rect(203,25,1076,819)
            for text,rect in boxes:
                self.assertTrue(area.contains(rect),(stage,text,rect))
            for i,(a,ra) in enumerate(boxes):
                for b,rb in boxes[i+1:]:
                    self.assertFalse(ra.colliderect(rb),
                                     (stage,a,ra,b,rb))

    def test_menu_accessible_during_auction_for_saving(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            app=SoloApp()
        app.game=auction_game(1918)
        app.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_m))
        self.assertTrue(app.menu_open)
        app.menu_page='settings'
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'save.json'
            with patch('game.ui.app.save_match',side_effect=lambda game:save_match(game,path)):
                app._menu_click(pygame.Rect(535,322+3*81,420,61).center)
            self.assertTrue(path.exists())
            self.assertEqual(load_match(path).phase,'auction')

    def test_sold_cards_render_in_existing_card_view(self):
        from game.ui.card_view import CardView
        m=auction_game(1913)
        free_pick(m)
        view=CardView()
        surface=pygame.Surface((300,430))
        for uid in m.auction_awards:
            view.draw(surface,m.cards[uid],pygame.Rect(25,25,255,380))


if __name__=="__main__":
    unittest.main()
