"""0.9.21: 12×3 draft catalog foundation; no unimplemented combat skills."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.core.engine import Match
from game.core.auction import advance_rarity
from game.core.auction_catalog import CATALOG,RARITIES,stats,rarity_from_roll,evolve
from game.core.ai import ComputerOpponent
from game.core.audit import make_report,verify_replay,state_snapshot
from game.core.persistence import save_match,load_match


def ready(seed=2101,legacy=False):
    m=Match(seed,auctions_enabled=True,
            auction_catalog="placeholders" if legacy else "v3")
    for p in (0,1):
        if m.phase=="mulligan":m.finish_mulligan(p,[])
    for _ in range(6):
        if m.phase=="auction":break
        m.end_turn()
    assert m.phase=="auction",m.phase
    return m


def take_two(m):
    m.auction_pass(m.auction.turn)
    m.auction_pass(m.auction.turn)
    offers=m.auction.offers[:]
    m.auction_pick(m.auction.turn,offers[0].uid)
    m.auction_pick(m.auction.turn,offers[1].uid)
    return offers


class CatalogFoundationTests(unittest.TestCase):
    def test_twelve_archetypes_with_exactly_three_draft_rarities(self):
        self.assertEqual(set(CATALOG),{"A%03d"%i for i in range(1,13)})
        for cid,record in CATALOG.items():
            with self.subTest(card=cid):
                self.assertEqual(record.id,cid)
                self.assertTrue(record.name)
                self.assertEqual(len(record.abilities),3)
                self.assertTrue(all(record.abilities))
                self.assertGreater(record.atk,0)

    def test_r_plus_eight_formula_for_all_twelve_and_rounds(self):
        for cid in CATALOG:
            for completed_round in (3,6,9,12,21,42):
                attack,hp=stats(cid,completed_round)
                with self.subTest(cid=cid,r=completed_round):
                    self.assertEqual(attack+hp,completed_round+8)
                    self.assertEqual(attack,CATALOG[cid].atk)
                    self.assertGreater(hp,0)
        with self.assertRaises(ValueError):stats("A001",2)

    def test_explicit_rarity_probability_thresholds(self):
        self.assertEqual([rarity_from_roll(v) for v in
                          (0.,.59,.60,.89999,.90,.99999)],
                         ["podstawowa","podstawowa","rzadka","rzadka",
                          "legendarna","legendarna"])
        for value in (-.1,1):
            with self.assertRaises(ValueError):rarity_from_roll(value)

    def test_evolution_caps_at_legendary(self):
        self.assertEqual(evolve("podstawowa"),"rzadka")
        self.assertEqual(evolve("rzadka"),"legendarna")
        self.assertEqual(evolve("legendarna"),"legendarna")
        self.assertEqual(evolve("podstawowa",2),"legendarna")

    def test_real_auction_offers_three_distinct_archetypes(self):
        for seed in (2102,2103,2104,2105):
            m=ready(seed)
            offers=m.auction.offers
            self.assertEqual(len(offers),3)
            self.assertEqual(len({o.archetype for o in offers}),3)
            self.assertEqual(len({o.uid for o in offers}),3)
            self.assertEqual(m.auction.completed_round,3)
            for offer in offers:
                with self.subTest(seed=seed,card=offer.archetype):
                    self.assertIn(offer.archetype,CATALOG)
                    self.assertEqual(offer.atk+offer.hp,11)
                    self.assertIn(offer.rarity,RARITIES)
                    self.assertEqual(offer.level,1)

    def test_purchased_v3_cards_have_stats_and_inactive_ability_text(self):
        m=ready(2106)
        selected=take_two(m)
        ids=set(m.auction_awards)
        self.assertEqual(ids,{x.uid for x in selected[:2]})
        self.assertEqual(len(m.cards),72)
        for uid,metadata in m.auction_awards.items():
            with self.subTest(uid=uid):
                card=m.cards[uid]
                self.assertEqual(card.definition.id,metadata["archetype"])
                self.assertEqual(card.attack+card.max_hp,11)
                self.assertEqual(card.owner in (0,1),True)
                self.assertTrue(card.definition.effect.startswith("NIEAKTYWNA"))
                self.assertFalse(metadata["ability_implemented"])
                self.assertEqual(card.definition.growth_atk,0)
                self.assertEqual(card.definition.growth_hp,0)
                self.assertEqual(metadata["purchase_round"],3)
        m.assert_integrity()

    def test_evolves_at_round_6_and_9_without_changing_base_stats(self):
        m=ready(2107)
        take_two(m)
        uid=next(iter(m.auction_awards))
        meta=m.auction_awards[uid]
        # Explicitly start at base tier, regardless of initial rarity roll.
        meta["rarity"]="podstawowa"
        meta["last_evolve_round"]=3
        card=m.cards[uid]
        card.definition=__import__('dataclasses').replace(
            card.definition,scaling="POZIOM 1 · PODSTAWOWA · NIE SKALUJE SIĘ")
        original=(card.attack,card.max_hp,card.hand_turns)
        advance_rarity(m,5)
        self.assertEqual(meta["rarity"],"podstawowa")
        advance_rarity(m,6)
        self.assertEqual(meta["rarity"],"rzadka")
        self.assertIn("RZADKA",card.definition.scaling)
        self.assertTrue(card.definition.effect.startswith("NIEAKTYWNA"))
        advance_rarity(m,6)  # idempotence after save/restart
        self.assertEqual(meta["rarity"],"rzadka")
        advance_rarity(m,9)
        self.assertEqual(meta["rarity"],"legendarna")
        advance_rarity(m,12)
        self.assertEqual(meta["rarity"],"legendarna")
        self.assertEqual((card.attack,card.max_hp,card.hand_turns),original)

    def test_rarity_evolution_integrated_with_completed_rounds(self):
        m=ready(2108)
        take_two(m)
        for _ in range(6):
            if m.phase=="auction":break
            m.end_turn()
        self.assertEqual(m.phase,"auction")
        self.assertEqual(m.auction.completed_round,6)
        for meta in m.auction_awards.values():
            self.assertEqual(meta["last_evolve_round"],6)
        m.assert_integrity()

    def test_rarity_reward_is_1_2_3_coins_at_unit_death(self):
        from game.core.models import Unit
        for rarity,reward in (("podstawowa",1),("rzadka",2),
                              ("legendarna",3)):
            m=ready(2190)
            take_two(m)
            uid=next(iter(m.auction_awards))
            owner=m.cards[uid].owner
            m.auction_awards[uid]["rarity"]=rarity
            m.cards[uid].zone="board"
            m.players[owner].hand.remove(uid)
            m.players[owner].board.append(uid)
            card=m.cards[uid]
            m.units[uid]=Unit(uid,owner,card.attack,card.max_hp,card.max_hp,
                              card.ability_level,m.players[owner].turn_count)
            before=m.players[1-owner].coins
            m._kill_batch([uid])
            with self.subTest(rarity=rarity):
                self.assertEqual(m.players[1-owner].coins-before,reward)
                self.assertEqual(m.cards[uid].zone,"grave")
                m.assert_integrity()

    def test_save_load_during_v3_bid_and_after_picking(self):
        m=ready(2109)
        m.auction_bid(m.auction.turn,1)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"match.json"
            save_match(m,path)
            restored=load_match(path)
        self.assertEqual(restored.auction_catalog,"v3")
        self.assertEqual(restored.auction.current_bid,1)
        self.assertEqual([x.archetype for x in restored.auction.offers],
                         [x.archetype for x in m.auction.offers])
        restored.auction_pass(restored.auction.turn)
        restored.auction_pick(restored.auction.turn,restored.auction.offers[0].uid)
        restored.auction_pick(restored.auction.turn,restored.auction.offers[1].uid)
        restored.assert_integrity()

    def test_legacy_mode_remains_three_guardians_after_reload(self):
        m=ready(2110,legacy=True)
        self.assertEqual([o.hp for o in m.auction.offers],[3,6,12])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"match.json"
            save_match(m,path)
            restored=load_match(path)
        self.assertEqual(restored.auction_catalog,"placeholders")
        self.assertEqual([o.hp for o in restored.auction.offers],[3,6,12])

    def test_original_seventy_card_bank_unchanged(self):
        m=ready(2111)
        take_two(m)
        m.assert_integrity()
        bank_cards=[uid for uid in m.cards if uid not in m.auction_awards]
        self.assertEqual(len(bank_cards),70)

    def test_draft_skills_cannot_steal_coins_as_if_implemented(self):
        m=None
        for seed in range(2112,2150):
            candidate=ready(seed)
            if any(o.archetype=="A005" for o in candidate.auction.offers):
                m=candidate
                break
        self.assertIsNotNone(m)
        offer=next(o for o in m.auction.offers if o.archetype=="A005")
        m.auction_pass(m.auction.turn)
        m.auction_pass(m.auction.turn)
        first=m.auction.turn
        m.auction_pick(first,offer.uid)
        m.auction_pick(m.auction.turn,
                       next(o.uid for o in m.auction.offers if o.uid!=offer.uid))
        if m.active!=first:m.end_turn()
        if m.phase!='turn' or m.active!=first:
            self.skipTest("Next auction reached before player's turn")
        m.players[first].played_this_turn=False
        before=[p.coins for p in m.players]
        m.play(offer.uid)
        self.assertEqual([p.coins for p in m.players],before)
        self.assertEqual(m.units[offer.uid].shield,0)
        self.assertFalse(m._taunt(m.units[offer.uid]))

    def test_ai_auction_and_live_audit_replay_catalog_v3(self):
        m=Match(2151,auctions_enabled=True,audit_enabled=True)
        ai=[ComputerOpponent(0),ComputerOpponent(1)]
        for step in range(150):
            if m.phase=="finished":break
            if m.phase=="mulligan":
                for opponent in ai:opponent.step(m)
            elif m.phase=="auction":
                ai[m.auction.turn].step(m)
            elif m.pending is not None:
                ai[m.pending.owner].step(m)
            else:
                ai[m.active].step(m)
            m.assert_integrity()
        self.assertGreater(len(m.auction_history),0)
        # An unfinished match cannot be publicly exported (hidden decks).
        # Internal replay verification is still valid and does not need a
        # fabricated terminal state; it reconstructs every command.
        report={
            "seed":m.seed,
            "initial_state":m.audit_initial,
            "actions":m.audit_actions,
            "event_journal":list(m.event_journal),
            "internal_events":m.audit_internal,
            "final_state":state_snapshot(m)
        }
        self.assertEqual(report["initial_state"]["auction_catalog"],"v3")
        self.assertTrue(verify_replay(report,
            lambda seed,auctions_enabled=False,auction_catalog="v3":
                Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled,
                      auction_catalog=auction_catalog)))


class CatalogUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1480,980))
    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_real_pygame_offers_show_all_three_archetypes(self):
        from game.ui.app import SoloApp
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            app=SoloApp()
        app.game=ready(2113)
        recorded=[]
        actual=app._text
        def wrapper(value,size,x,y,color=None,center=False):
            rect=actual(value,size,x,y,color,center)
            recorded.append((str(value),rect))
            return rect
        with patch.object(app,"_text",side_effect=wrapper):
            app._draw_auction()
        self.assertTrue(any("12 ARCHETYPÓW" in label for label,_ in recorded))
        self.assertTrue(any("PLANOWANA" in label for label,_ in recorded))
        screen=pygame.Rect(0,0,1480,980)
        for label,rect in recorded:
            self.assertTrue(screen.contains(rect),(label,rect))

    def test_card_details_do_not_masquerade_as_active_skills(self):
        from game.ui.card_view import CardView
        from game.ui.card_summary import ability_summary
        from game.ui.card_infographics import card_cue
        m=ready(2114)
        take_two(m)
        surface=pygame.Surface((300,440))
        for uid in m.auction_awards:
            card=m.cards[uid]
            self.assertIn("NIEAKTYWNA",ability_summary(card).short)
            self.assertIn("NIEAKTYWNA",card_cue(card).base)
            CardView().draw(surface,card,pygame.Rect(20,20,255,380))


if __name__=="__main__":
    unittest.main()
