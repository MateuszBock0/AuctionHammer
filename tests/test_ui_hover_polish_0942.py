"""0.9.42 visual UX: information is truthful, read-only and nonintrusive."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame

from game.core.audit import digest,state_snapshot
from game.core.engine import Match
from game.core.status_view import active_statuses,hand_grants
from game.ui.app import SoloApp
from game.ui.card_view import CardView,card_zones
from game.ui.attack_view import attack_display

def bonus_match(human_second=True):
    for seed in range(40000,40100):
        match=Match(seed,audit_enabled=True,auctions_enabled=True,
                    auction_catalog='v22',
                    starting_compensation='choice_2_5_or_coins')
        if (match.first==1)==human_second:return match
    raise AssertionError('Expected both randomized first-player seats')

class HoverAndTavernAcceptance(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp,'_desktop_resolution',return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        # A new game may randomly put the human second. Resolve its blocking
        # compensation modal before generic hand-hover tests.
        if self.app._bonus_selection_due():
            self.app._choose_bonus('coins')
    def tearDown(self):
        pygame.quit()

    def test_card_dwell_not_immediate_and_no_state_change(self):
        app=self.app
        uid,area=next(iter(app.hand_layout().items()))
        before=digest(state_snapshot(app.game))
        app._update_hover_target(area.center,now=1000)
        self.assertEqual(app._hover_uid,uid)
        self.assertFalse(app._hover_preview_ready(now=1419))
        self.assertTrue(app._hover_preview_ready(now=1420))
        with patch.object(app,'mouse_pos',return_value=area.center):
            with patch('game.ui.app.pygame.time.get_ticks',return_value=1500):
                app._draw_hover_guidance()
        self.assertEqual(digest(state_snapshot(app.game)),before)
        # The preview disappears immediately on pointer exit.
        app._update_hover_target((1500,930),now=1501)
        self.assertIsNone(app._hover_uid)
        self.assertFalse(app._hover_preview_ready(now=2300))

    def test_hover_stays_closed_in_every_blocking_state(self):
        app=self.app
        uid,area=next(iter(app.hand_layout().items()))
        for name,value in (('menu_open',True),('history_open',True),
                           ('confirm_action','restart'),('details_card',uid),
                           ('replay_index',0),('drag_start',(area.center,uid))):
            with self.subTest(overlay=name):
                old=getattr(app,name)
                setattr(app,name,value)
                app._update_hover_target(area.center,now=1000)
                self.assertFalse(app._hover_preview_ready(now=2000))
                setattr(app,name,old)
        app.game=bonus_match(human_second=True)
        self.assertTrue(app._bonus_selection_due())
        app._update_hover_target(area.center,now=1000)
        self.assertFalse(app._hover_preview_ready(now=2000))

    def test_granted_status_hitbox_matches_actual_hand_marker(self):
        app=self.app
        uid,rect=next(iter(app.hand_layout().items()))
        card=app.game.cards[uid]
        card.quick_on_first_summon=True
        before=digest(state_snapshot(app.game))
        sts=hand_grants(app.game,uid)
        self.assertTrue(sts)
        badge=app.cards_view.visible_status_hitboxes(rect,sts,board=False)[0]
        status,hit,_=badge
        self.assertEqual(status.name,sts[0].name)
        self.assertTrue(hit.collidepoint((rect.x+1,card_zones(rect)['art'].y)))
        self.assertEqual(app._hovered_status((rect.x+1,card_zones(rect)['art'].y))[0],status)
        with patch.object(app,'mouse_pos',return_value=hit.center):
            app._draw_hover_guidance()
        self.assertEqual(digest(state_snapshot(app.game)),before)

    def test_2_visible_statuses_and_exact_remaining_counter(self):
        game=Match(102)
        card=game.cards['S01']
        statuses=active_statuses(game,card.uid)
        # VisibleStatus objects are only for UI; no changes to real game effects.
        from game.core.status_view import VisibleStatus
        statuses=[VisibleStatus('shield','TARCZ','Tarcza','Jedna tarcza','S20'),
                  VisibleStatus('taunt','PROW','Prowokacja','Chroni bohatera','S61'),
                  VisibleStatus('poison','TRUC','Trucizna','2 przez 3','S58')]
        view=CardView()
        r=pygame.Rect(110,152,148,220)
        hits=view.visible_status_hitboxes(r,statuses,board=True)
        self.assertEqual(len(hits),3)
        self.assertEqual([x[0].category for x in hits[:2]],['taunt','poison'])
        self.assertIsNone(hits[2][0])
        self.assertEqual(len(hits[2][2]),1)
        self.assertEqual(hits[2][2][0].category,'shield')
        art=card_zones(r)['art']
        self.assertTrue(all(art.contains(h[1]) for h in hits))

    def test_new_bonus_plaques_preserve_old_clickable_rectangles(self):
        app=self.app
        app.game=bonus_match(human_second=True)
        before=digest(state_snapshot(app.game))
        texts=[]
        old=app._text
        def spy(value,*args,**kwargs):
            texts.append(str(value))
            return old(value,*args,**kwargs)
        with patch.object(app,'_text',side_effect=spy):
            app._draw_bonus_selection()
        self.assertTrue(any('Chorąży zawsze zdąży' in t for t in texts))
        self.assertTrue(any('+3 MONETY' in t for t in texts))
        self.assertEqual(digest(state_snapshot(app.game)),before)
        event=pygame.event.Event(pygame.MOUSEBUTTONUP,{'button':1,'pos':(0,0)})
        with patch.object(app,'_physical_to_virtual',return_value=(750,483)):
            app.handle(event)
        self.assertEqual(app.game.starting_compensation_choice,'unit_2_5')

    def test_finished_sidebar_has_no_duplicate_restart_cta(self):
        app=self.app
        game=app.game
        game.phase='finished';game.winner=0
        labels=[]
        old=app._button
        def track(rect,label,*args,**kwargs):
            labels.append(str(label))
            return old(rect,label,*args,**kwargs)
        with patch.object(app,'_button',side_effect=track):
            app._draw_sidebar()
        self.assertNotIn('NOWY MECZ  [R]',labels)
        with patch.object(app,'_button',side_effect=track):
            app._draw_gameover()
        self.assertIn('NOWY MECZ',labels)

    def test_read_only_phase_hint_during_pre_mulligan_choice(self):
        app=self.app
        app.game=bonus_match(human_second=True)
        before=digest(state_snapshot(app.game))
        self.assertIn('[1] CHORĄŻY 2/5',app._phase_guidance())
        self.assertIn('[2] +3 MONETY',app._phase_guidance())
        self.assertEqual(digest(state_snapshot(app.game)),before)

    def test_version_matches_metadata(self):
        from game import config
        data=json.loads((Path(__file__).resolve().parents[1]/'VERSION.json').read_text(encoding='utf-8'))
        self.assertEqual(data['mvp'],'0.9.43')
        self.assertIn('0.9.43',config.WINDOW_TITLE)
        self.assertEqual(data['starting_compensation_audit_schema'],4)
        self.assertIn('choice_2_5_or_coins',data['starting_compensation_available_modes'])

if __name__=='__main__':unittest.main()
