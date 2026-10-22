"""0.9.50: engine-level acceptance of the user's 0.9.48 ZIP QA checks.

Uses real Match handlers for damage, stun and immunity. Never mocks engine.
"""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from game.core.models import Choice, Effect
from game.core.audit import digest,state_snapshot
from game.core.persistence import save_match,load_match
from game.ui.card_summary import ability_summary
from game.ui.card_infographics import card_cue
from test_auction_v22_0931 import ready as ready_v22,award as award_v22
from test_auction_v4_engine import ready as ready_v4,award as award_v4,place_basic


def field(cid,level,immune=False,ruleset='v23'):
    game=ready_v22(950100+level)
    game.ruleset_version=ruleset
    game.cards[cid].hand_turns=3*level
    src=place_basic(game,cid,0)
    dst=place_basic(game,'S01',1)
    for uid in (src,dst):
        game.units[uid].base_max_hp=100
        game.units[uid].hp=100
    if immune:
        game.units[dst].effects.append(Effect('immune_stun',positive=True))
    return game,src,dst


class StunEngineAcceptance(unittest.TestCase):
    def test_T04_S15_only_successful_stun_deals_extra_damage(self):
        for lvl in (0,1,3):
            for immune in (False,True):
                with self.subTest(lvl=lvl,immune=immune):
                    g,src,dst=field('S15',lvl,immune)
                    old=g.units[dst].hp
                    g._execute(src,'attack',Choice('auto',dst,''),attacked=dst)
                    self.assertEqual(old-g.units[dst].hp,0 if immune else 1+lvl)
                    self.assertEqual(any(e.kind=='stun' for e in g.units[dst].effects),
                                     not immune)
                    self.assertEqual(card_cue(g.cards[src],g.units[src]).effect_value,
                                     1+lvl)
                    g.assert_integrity()

    def test_T05_T06_S59_and_S84_base_damage_if_immune(self):
        for cid,base,context in (('S59',3,'play'),('S84',4,'death')):
            for lvl in (0,1,3):
                for immune in (False,True):
                    with self.subTest(cid=cid,lvl=lvl,immune=immune):
                        g,src,dst=field(cid,lvl,immune)
                        old=g.units[dst].hp
                        g._execute(src,context,Choice('target',dst,''))
                        self.assertEqual(old-g.units[dst].hp,
                                         base+(0 if immune else lvl))
                        self.assertEqual(any(e.kind=='stun' for e in g.units[dst].effects),
                                         not immune)
                        self.assertEqual(card_cue(g.cards[src],g.units[src]).base,
                                         f'{base}→{base+lvl} OBR')
                        g.assert_integrity()

    def test_T07_S108_once_per_opponent_even_when_resisted(self):
        for lvl in (0,1,3):
            for immune in (False,True):
                with self.subTest(lvl=lvl,immune=immune):
                    g,src,dst=field('S108',lvl,immune)
                    old=g.units[dst].hp
                    g._apply_position_reactions()
                    self.assertEqual(old-g.units[dst].hp,0 if immune else 1+lvl)
                    self.assertIn(dst,g.units[src].seen_opponents)
                    after=g.units[dst].hp
                    g._apply_position_reactions()
                    self.assertEqual(g.units[dst].hp,after)
                    g.assert_integrity()

    def test_T08_S95_immune_and_v23_no_new_target_fallback(self):
        for lvl in (0,1,3):
            for immune in (False,True):
                with self.subTest(kind='stun',lvl=lvl,immune=immune):
                    g,src,dst=field('S95',lvl,immune)
                    old=g.units[dst].hp
                    g._execute(src,'end',Choice('auto',None,''))
                    self.assertEqual(old-g.units[dst].hp,
                                     0 if immune else 1+lvl)
                    g.assert_integrity()
            for ruleset,expected in (('v23',2),('v22',0)):
                with self.subTest(kind='no_new_target',lvl=lvl,ruleset=ruleset):
                    g,src,dst=field('S95',lvl,ruleset=ruleset)
                    u=g.units[src]
                    u.last_stun_target=dst
                    u.last_stun_turn=g.players[0].turn_count-1
                    old=g.units[dst].hp
                    g._execute(src,'end',Choice('auto',None,''))
                    self.assertEqual(old-g.units[dst].hp,expected)
                    self.assertFalse(any(e.kind=='stun' for e in g.units[dst].effects))
                    g.assert_integrity()


class LegacyModesAcceptance(unittest.TestCase):
    def test_T10_A010_synthetic_v4_v22_saves_preserve_digest_and_effect(self):
        # Synthetic old-mode fixtures; NOT the user's old external archives.
        for catalog,make,grant in (('v4',ready_v4,award_v4),
                                   ('v22',ready_v22,award_v22)):
            for tier in (0,1,2):
                with self.subTest(catalog=catalog,tier=tier):
                    g=make(950200+tier)
                    uid=grant(g,'A010',tier,owner=0,zone='hand')
                    effect=g.cards[uid].definition.effect
                    before=digest(state_snapshot(g))
                    with tempfile.TemporaryDirectory() as tmp:
                        p=Path(tmp)/'historical-mode.json'
                        save_match(g,p)
                        restored=load_match(p)
                    self.assertEqual(digest(state_snapshot(restored)),before)
                    self.assertEqual(restored.cards[uid].definition.effect,effect)
                    self.assertIn(effect,ability_summary(restored.cards[uid]).full)
                    self.assertEqual(restored.auction_catalog,catalog)
                    restored.assert_integrity()


if __name__=='__main__':
    unittest.main()
