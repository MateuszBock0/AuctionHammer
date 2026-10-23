"""0.9.41 acceptance: second mover chooses Chorazy 2/5 or 3 coins."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.engine import Match
from game.core.models import IllegalMove
from game.core.audit import state_snapshot,digest,make_report,verify_replay
from game.core.persistence import save_match,load_match
from game.ui.app import SoloApp
from game.ui.assets import ImageAssets
from game.ui.card_view import CardView,card_zones
from tools.simulate_v22 import simulate_one

TOKEN='SUM_START_GUARD'
MODE='choice_2_5_or_coins'

def fresh(seed=39888):
    return Match(seed,auctions_enabled=True,auction_catalog='v22',
                 audit_enabled=True,starting_compensation=MODE)

def factory(seed,auctions_enabled=False,auction_catalog='v3',
            starting_compensation='coins'):
    return Match(seed,auctions_enabled=auctions_enabled,
                 auction_catalog=auction_catalog,
                 audit_enabled=True,starting_compensation=starting_compensation)

class SecondPlayerChoice(unittest.TestCase):
    def test_initial_state_has_neither_bonus_and_second_alone_chooses(self):
        seats=set()
        for seed in range(39880,39920):
            g=fresh(seed)
            second=1-g.first;seats.add(second)
            self.assertEqual((g.players[0].coins,g.players[1].coins),(0,0))
            self.assertNotIn(TOKEN,g.cards)
            self.assertEqual(g.audit_state_schema,4)
            self.assertEqual(g.starting_compensation_choice,None)
            with self.assertRaises(IllegalMove):
                g.choose_starting_compensation(g.first,'coins')
            self.assertEqual(g.starting_compensation_choice,None)
            g.assert_integrity()
        self.assertEqual(seats,{0,1})

    def test_ai_uses_both_compensation_options_on_different_hands(self):
        from game.core.ai import ComputerOpponent
        observed=set()
        for seed in range(39000,39100):
            game=fresh(seed)
            bot=ComputerOpponent(player=1-game.first)
            bot.step(game)
            observed.add(game.starting_compensation_choice)
            self.assertEqual(len(game.audit_actions),1)
        self.assertEqual(observed,{'coins','unit_2_5'})

    def test_choose_two_five_and_cannot_choose_twice(self):
        for seed in (39881,39882,39883):
            g=fresh(seed);second=1-g.first
            g.choose_starting_compensation(second,'unit_2_5')
            self.assertEqual(g.starting_compensation_choice,'unit_2_5')
            self.assertEqual((g.units[TOKEN].atk,g.units[TOKEN].hp,
                              g.units[TOKEN].max_hp,g.units[TOKEN].armor),
                             (2,1,1,4))
            self.assertEqual(g.cards[TOKEN].definition.name,'Chorąży')
            self.assertIn('Chorąży zawsze zdąży.',g.cards[TOKEN].definition.effect)
            self.assertIn('4 trwałego pancerza',g.cards[TOKEN].definition.effect)
            self.assertEqual(len(g.cards),71)
            self.assertEqual(len(g.defs),70)
            self.assertEqual((g.players[0].coins,g.players[1].coins),(0,0))
            self.assertIn(TOKEN,g.ephemeral_ids)
            with self.assertRaises(IllegalMove):
                g.choose_starting_compensation(second,'coins')
            g.assert_integrity()

    def test_choose_coins_does_not_create_guard(self):
        g=fresh()
        g.choose_starting_compensation(1-g.first,'coins')
        self.assertNotIn(TOKEN,g.cards)
        self.assertEqual(g.players[1-g.first].coins,3)
        self.assertEqual(g.players[g.first].coins,0)
        self.assertEqual(len(g.cards),70)
        g.assert_integrity()

    def test_cannot_finish_second_mulligan_without_choice(self):
        g=fresh()
        with self.assertRaises(IllegalMove):
            g.finish_mulligan(1-g.first,[])
        self.assertEqual(g.mulligan_done,set())
        g.choose_starting_compensation(1-g.first,'unit_2_5')
        g.finish_mulligan(0,[])
        g.finish_mulligan(1,[])
        self.assertEqual(g.phase,'turn')
        g.end_turn()
        self.assertEqual(g.active,1-g.first)
        self.assertEqual(g.legal_attacks(TOKEN),[])
        g.end_turn();g.end_turn()
        self.assertIn('hero:'+str(g.first),g.legal_attacks(TOKEN))

    def test_choice_survives_save_resume_and_is_signed(self):
        for option in ('coins','unit_2_5'):
            g=fresh(39123)
            g.choose_starting_compensation(1-g.first,option)
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'choice.json'
                save_match(g,path)
                h=load_match(path)
                self.assertEqual(h.starting_compensation_choice,option)
                self.assertEqual(digest(state_snapshot(g)),digest(state_snapshot(h)))
                self.assertEqual(state_snapshot(h)['ruleset_state']['starting_compensation_choice'],option)
                h.assert_integrity()

    def test_audited_replay_for_both_explicit_choices_and_ai_policy(self):
        for option in ('coins','unit_2_5',None):
            with self.subTest(option=option):
                g,_=simulate_one(39124,starting_compensation=MODE,
                                 forced_starting_choice=option)
                report=make_report(g)['payload']
                self.assertTrue(verify_replay(report,factory))
                self.assertEqual(report['initial_state']['ruleset_state']['audit_schema'],4)

    def test_old_guard_modes_are_still_replayable(self):
        for mode in ('coins','unit_5_5','unit_3_5'):
            g,_=simulate_one(39124,starting_compensation=mode)
            self.assertTrue(verify_replay(make_report(g)['payload'],factory))

class UITests(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
    def tearDown(self):
        pygame.quit()
    def test_human_second_explicit_keyboard_and_mouse_both(self):
        seed=next(x for x in range(39200,39400) if fresh(x).first==1)
        for selection,key in (('unit_2_5',pygame.K_1),('coins',pygame.K_2)):
            self.app.game=fresh(seed)
            self.assertTrue(self.app._bonus_selection_due())
            before=digest(state_snapshot(self.app.game))
            self.app.draw()
            self.assertEqual(digest(state_snapshot(self.app.game)),before)
            self.app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':key}))
            self.assertEqual(self.app.game.starting_compensation_choice,selection)
            self.assertFalse(self.app._bonus_selection_due())
            self.app.game.assert_integrity()
        self.app.game=fresh(seed)
        ev=pygame.event.Event(pygame.MOUSEBUTTONUP,{'button':1,'pos':(0,0)})
        with patch.object(self.app,'_physical_to_virtual',return_value=(600,485)):
            self.app.handle(ev)
        self.assertEqual(self.app.game.starting_compensation_choice,'unit_2_5')
    def test_details_g_zoom_is_read_only(self):
        uid=self.app.game.players[0].hand[0]
        self.app._open_details(uid)
        state=digest(state_snapshot(self.app.game))
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_g}))
        self.assertTrue(self.app.details_image_zoom)
        self.app.draw()
        self.assertEqual(digest(state_snapshot(self.app.game)),state)
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,{'key':pygame.K_g}))
        self.assertFalse(self.app.details_image_zoom)

class AssetAndStatus(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((360,260))
    def tearDown(self):
        pygame.quit()
    def test_fit_preserves_uniform_scale_and_caches(self):
        img=pygame.Surface((540,315))
        original=pygame.transform.smoothscale
        seen=[]
        def observe(image,size,*args,**kwargs):
            seen.append(size)
            return original(image,size,*args,**kwargs)
        with patch('game.ui.assets.pygame.transform.smoothscale',side_effect=observe):
            cover=ImageAssets.fit_art(img,(115,22))
        self.assertEqual(cover.get_size(),(115,22))
        self.assertEqual(len(seen),1)
        sw,sh=seen[0]
        self.assertAlmostEqual(sw/540,sh/315,delta=.005)
        contain=ImageAssets.fit_art(img,(180,240),'contain')
        self.assertEqual(contain.get_size(),(180,240))
    def test_hand_grants_draw_markers_on_outer_border(self):
        from game.core.engine import Match
        from game.ui.card_view import CardView
        g=Match(20001)
        c=g.cards['S01']
        view=CardView()
        screen=pygame.Surface((250,250))
        rect=pygame.Rect(30,20,125,195)
        colors=[(250,20,30),(20,240,20),(30,50,245)]
        status=[SimpleNamespace(category='other',color=color,short='X')
                for color in colors]
        view.draw(screen,c,rect,statuses=status)
        art=card_zones(rect)['art']
        for k,color in enumerate(colors):
            self.assertEqual(screen.get_at((rect.x+1,art.y+k*7))[:3],color)

if __name__=='__main__':unittest.main()
