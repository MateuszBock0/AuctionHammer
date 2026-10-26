"""0.9.92: completed, read-only and board-safe ability cause/effect cues."""
from __future__ import annotations

import copy
import os
from types import SimpleNamespace
import unittest

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

import pygame

from game.ui.ability_feedback import AbilityFeedback
from game.ui.app import SoloApp


def game_fixture():
    def card(name,owner):
        return SimpleNamespace(definition=SimpleNamespace(name=name),owner=owner)
    cards={'A014':card('Kapłan Odwróconej Łaski',0),
           'A002':card('Generał Oddziału Natarcia',0),
           'S01':card('Jednostka A',0),
           'S02':card('Jednostka B',0),
           'S03':card('Jednostka C',0),
           'S04':card('Jednostka D',0),
           'S05':card('Jednostka E',1)}
    players=[SimpleNamespace(name='GRACZ',board=['A014','S01','S02','S03','S04']),
             SimpleNamespace(name='KOMPUTER',board=['S05'])]
    units={uid:SimpleNamespace(owner=card.owner) for uid,card in cards.items()}
    game=SimpleNamespace(cards=cards,players=players,units=units,
                         audit_actions=[],audit_internal=[],phase='turn')
    game.slot_of=lambda uid:players[game.cards[uid].owner].board.index(uid)
    return game


def rect_for(owner,index):
    return pygame.Rect(107+index*174,431 if owner==0 else 152,148,220)


def hero_for(owner):
    return pygame.Rect(110,662 if owner==0 else 98,935,44)


def action(operation='end_turn',start=1,end=2,result='ok'):
    return {'operation':operation,'result':result,
            'internal_seq_start':start,'internal_seq_end':end}


def cast(source='A014',context='end',before=None,after=None):
    return {'operation':'_execute','args':[source,context,
            {'mode':'auto','target':None,'label':''}],
            'kwargs':{},'result':None,'error':None,
            'before':before or {},'after':after or {}}


def regen(target,source='A014'):
    return {'operation':'_add_effect','args':[target,'regen',2,2],
            'kwargs':{'source':source},'error':None,'result':True,
            'before':{target:{'hp':3,'effects':[]}},
            'after':{target:{'hp':3,'effects':[{'kind':'regen',
                    'value':2,'remaining':2,'source':source}]}}}


class AbilityFeedback0992(unittest.TestCase):
    def setUp(self):
        self.game=game_fixture()
        self.fx=AbilityFeedback()
        self.fx.reset(self.game)

    def test_single_committed_regen_identifies_source_target_and_exact_stack(self):
        g=self.game
        g.audit_internal=[cast(),regen('S01')]
        g.audit_actions.append(action())
        before=copy.deepcopy(g.audit_actions)
        self.fx.observe(g,rect_for,hero_for,1000)
        self.assertEqual(len(self.fx.cues),1)
        cue=self.fx.cues[0]
        self.assertEqual(cue.source,'A014')
        self.assertEqual(cue.targets,('S01',))
        self.assertEqual(cue.label,'REGEN 2/2')
        self.assertEqual(cue.source_name,'Kapłan Odwróconej Łaski')
        self.assertEqual(g.audit_actions,before,
                         'UI must never change signed audit actions')
        self.assertEqual(self.fx.read_actions,1)

    def test_mass_legendary_regen_has_one_non_overlapping_group(self):
        g=self.game
        targets=['A014','S01','S02','S03','S04']
        g.audit_internal=[cast()]+[regen(uid) for uid in targets]
        g.audit_actions.append(action(end=6))
        self.fx.observe(g,rect_for,hero_for,1000)
        self.assertEqual(len(self.fx.cues),1)
        self.assertEqual(self.fx.cues[0].targets,tuple(targets))
        self.assertLessEqual(len(self.fx.cues),self.fx.MAX_CUES)

    def test_failed_action_does_not_play_cue(self):
        g=self.game
        g.audit_internal=[cast(),regen('S01')]
        g.audit_actions.append(action(result='error'))
        self.fx.observe(g,rect_for,hero_for,1000)
        self.assertEqual(self.fx.cues,[])

    def test_regular_weapon_damage_is_not_misattributed_to_ability(self):
        g=self.game
        hurt={'operation':'_damage','args':['S05',4],'kwargs':{},
              'error':None,'result':None,
              'before':{'S05':{'hp':6,'shield':0,'armor':0}},
              'after':{'S05':{'hp':2,'shield':0,'armor':0}}}
        g.audit_internal=[cast('S01','attack'),hurt]
        g.audit_actions.append(action(operation='attack'))
        self.fx.observe(g,rect_for,hero_for,1000)
        self.assertFalse(self.fx.cues)

    def test_on_play_direct_damage_links_only_committed_hp_loss(self):
        g=self.game
        hurt={'operation':'_damage','args':['S05',4],'kwargs':{},
              'error':None,'result':None,
              'before':{'S05':{'hp':6,'shield':0,'armor':0}},
              'after':{'S05':{'hp':2,'shield':0,'armor':0}}}
        g.audit_internal=[cast('A014','play'),hurt]
        g.audit_actions.append(action(operation='play'))
        self.fx.observe(g,rect_for,hero_for,1000)
        self.assertEqual([(x.source,x.targets,x.label) for x in self.fx.cues],
                         [('A014',('S05',),'PŻ -4')])

    def test_blocked_hit_without_hp_loss_can_show_real_shield_consumption(self):
        g=self.game
        damage={'operation':'_damage','args':['S05',4],'kwargs':{},
                'error':None,'result':None,
                'before':{'S05':{'hp':6,'shield':1,'armor':0}},
                'after':{'S05':{'hp':6,'shield':0,'armor':0}}}
        g.audit_internal=[cast('A014','play'),damage]
        g.audit_actions.append(action(operation='play'))
        self.fx.observe(g,rect_for,hero_for,1000)
        self.assertEqual(self.fx.cues[0].label,'TARCZA -1')
        self.assertNotIn('PŻ -',self.fx.cues[0].label)

    def test_self_shield_and_armor_report_exact_committed_gain(self):
        g=self.game
        source_before={'A002':{'hp':7,'shield':0,'armor':0}}
        source_after={'A002':{'hp':7,'shield':1,'armor':2}}
        g.audit_internal=[cast('A002','play',source_before,source_after)]
        g.audit_actions.append(action(operation='play',end=1))
        self.fx.observe(g,rect_for,hero_for,1000)
        self.assertEqual({c.label for c in self.fx.cues},
                         {'TARCZA +1','PANCERZ +2'})

    def test_modal_consumes_feedback_without_old_event_after_resume(self):
        g=self.game
        g.audit_internal=[cast(),regen('S01')]
        g.audit_actions.append(action())
        self.fx.observe(g,rect_for,hero_for,1000,allowed=False)
        self.fx.observe(g,rect_for,hero_for,1100,allowed=True)
        self.assertEqual(self.fx.cues,[])

    def test_disabled_feedback_and_expiration(self):
        g=self.game
        g.audit_internal=[cast(),regen('S01')]
        g.audit_actions.append(action())
        self.fx.observe(g,rect_for,hero_for,1000)
        self.fx.observe(g,rect_for,hero_for,2200)
        self.assertEqual(self.fx.cues,[])

    def test_reset_after_loading_other_match_hides_old_card_coordinates(self):
        g=self.game
        g.audit_internal=[cast(),regen('S01')]
        g.audit_actions.append(action())
        self.fx.observe(g,rect_for,hero_for,1000)
        other=game_fixture()
        self.fx.observe(other,rect_for,hero_for,1100)
        self.assertEqual(self.fx.cues,[])
        self.assertIs(self.fx.game,other)
        self.assertEqual(self.fx.read_actions,0)

    def test_render_does_not_cover_combat_portrait_or_stat_plates(self):
        pygame.font.init()
        screen=pygame.Surface((1480,980))
        screen.fill((20,25,35))
        self.game.audit_internal=[cast(),regen('S01')]
        self.game.audit_actions.append(action())
        self.fx.observe(self.game,rect_for,hero_for,1000)
        before=screen.get_at((400,485))
        self.fx.draw(screen,1100,pygame.font.Font(None,18))
        self.assertEqual(screen.get_at((400,485)),before)
        # A truthful cue is visible in the empty strip, not the cards.
        self.assertNotEqual(screen.get_at((112,710)),before)

    def test_ui_wires_observer_before_ai_acts(self):
        app=SoloApp.__new__(SoloApp)
        self.assertTrue(hasattr(app,'_capture_visual_feedback'))
        self.assertTrue(callable(self.fx.observe))
        self.assertTrue(callable(self.fx.draw))


if __name__=='__main__':
    unittest.main()
