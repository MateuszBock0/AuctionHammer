"""A staged, rules-resolved AuctionHammer trailer scene, not a player replay.

SETUP ONLY injects a late-game position (cards, buffs, wounded HP).
Every attack, beer purchase, played card, brawl tick and death from that
point onwards is performed through the original Match public commands.
Rendering goes through the original SoloApp Pygame board and animations.
No shipping gameplay rules or UI code are changed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.core.engine import Match
from game.core.models import Unit
from tools.native_trailer import NativeExporter


FOES = ("S103", "S104", "S111", "S115", "S39")
TAUNT = "S33"  # Strażnik Bram (natural, authentic taunt)
QUICK = "S114"  # Instruktor Błyskawicznego Natarcia (innate quick)


def stage_game():
    game = Match(
        seed=20261027, audit_enabled=False, auctions_enabled=True,
        auction_catalog="v22", starting_compensation="coins",
        fixed_board_slots=True, tavern_beer_enabled=True,
        tavern_price_v2_enabled=True, tavern_scaled_damage_enabled=True,
        tavern_min_hp_damage_enabled=True,
    )
    # Stage a valid late-game *position* instead of rewriting combat rules.
    # Return initial sample hands/decks to the common unopened bank.
    for p in game.players:
        for uid in p.hand + p.deck:
            game.cards[uid].owner = None
            game.cards[uid].zone = "bank"
            game.bank.append(uid)
        p.hand.clear()
        p.deck.clear()
    game.first = 0
    game.active = 0
    game.phase = "turn"
    game.round = 5
    game.players[0].turn_count = 5
    game.players[1].turn_count = 4
    game.players[0].hp = 5
    game.players[1].hp = 1
    game.players[0].coins = 80
    game.players[1].coins = 12
    game.players[0].played_this_turn = False
    game.players[1].played_this_turn = False

    def move(uid, owner, zone, slot=None, hp=None):
        assert uid in game.bank, f"Missing staged card {uid}"
        game.bank.remove(uid)
        card = game.cards[uid]
        card.owner = owner
        card.zone = zone
        if zone == "hand":
            game.players[owner].hand.append(uid)
            return
        assert zone == "board"
        u = Unit(uid, owner, card.attack, card.max_hp,
                 card.max_hp if hp is None else hp,
                 card.ability_level, played_turn=0)
        game.units[uid] = u
        game._place_on_board(uid, owner, slot)

    move(TAUNT, 0, "hand")
    move(QUICK, 0, "hand")
    # One enemy unit has a previous permanent buff: 5 ATK / 7 MAX HP,
    # and is currently wounded to 6 HP. Thus it survives its counterattack.
    for slot, uid in enumerate(FOES):
        move(uid, 1, "board", slot=slot, hp=4)
    game._add_effect("S103", "atk", value=1, source="S34")
    game._add_effect("S103", "max_hp", value=2, source="S35")
    game.units["S103"].hp = 6
    # Another foe has existing taunt from an earlier ability.
    game._add_effect("S39", "taunt", source="S61")
    game._update_auras()
    assert len(game.players[1].board) == 5
    assert game._taunt(game.units["S39"])
    assert game.units["S103"].atk == 5
    assert game.units["S103"].hp == 6
    game.assert_integrity()
    return game


def run_scene(output):
    game = stage_game()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    exporter = NativeExporter({}, output, [], fps=24)
    app = exporter.app
    app.game = game
    app.menu_open = False
    app.history_open = False
    app.replay_index = None
    app.details_card = None
    app.selected = None
    app.animations_enabled = True
    app.combat_visuals = exporter.CombatVisuals()
    app.combat_visuals.sync(game, app.slot_rect, app.hero_rect, exporter.ms)
    app.ability_feedback.reset(game)
    app._last_logged_event = len(game.event_journal)
    # Init actual game's beer renderer before issuing the paid order.
    with patch.object(exporter.pg.time, "get_ticks", return_value=exporter.ms):
        app._sync_tavern_fx()
    timeline = []

    def check_step(name, seconds, call=None, checks=None, selected=None):
        if selected is not None:
            app.selected = selected
        if call is not None:
            call()
        if checks:
            checks()
        with patch.object(exporter.pg.time, "get_ticks", return_value=exporter.ms):
            app._sync_tavern_fx()
        app.combat_visuals.sync(game, app.slot_rect, app.hero_rect, exporter.ms)
        event = dict(step=name, at_s=round(exporter.total/exporter.fps, 3),
                     player_hp=game.players[0].hp, enemy_hp=game.players[1].hp,
                     own_board=list(game.players[0].board),
                     foe_board=list(game.players[1].board),
                     burning_turns=game.beer_turns_remaining,
                     winner=game.winner)
        timeline.append(event)
        exporter.frames(round(seconds * exporter.fps))

    def assert_after_player_end():
        assert game.active == 1, ("expected enemy turn", game.active, game.phase)
        assert game.units[TAUNT].hp == 5
        assert len(game.players[1].board) == 5
        assert game.beer_turns_remaining == 2

    def assert_after_taunt():
        assert TAUNT not in game.units, "Prowokacja must die in enemy attack"
        assert "S103" in game.units, "First attacker must survive until BURDA"
        assert game.players[0].hp == 5

    def assert_after_hero_hit():
        assert game.players[0].hp == 1, "EXACTLY ONE hero HP required"
        assert game.players[1].hp == 1

    def assert_after_brawl():
        assert game.phase == "turn", (game.phase, game.pending)
        assert game.active == 0
        assert game.players[0].hp == 1
        assert not game.players[0].board, game.players[0].board
        assert not game.players[1].board, game.players[1].board
        assert game.beer_turns_remaining == 1
        assert game.winner is None

    def assert_after_quick():
        assert QUICK in game.units
        assert game._fast(game.units[QUICK])
        assert "hero:1" in game.legal_attacks(QUICK)

    def assert_final():
        assert game.phase == "finished", game.phase
        assert game.winner == 0
        assert game.players[0].hp == 1
        assert game.players[1].hp <= 0

    try:
        check_step("Pięć wrogich jednostek / mój bohater 5 HP", 1.1)
        check_step("KLIK: KARCZEMNA BURDA — zakup kufla, podpalenie",
                   2.5, lambda: game.order_beer(0))
        check_step("Wystawiam STRAŻNIKA BRAM (Prowokacja)",
                   1.3, lambda: game.play(TAUNT))
        check_step("Koniec mojej tury — pierwsza fala Burdy (-3)",
                   1.2, game.end_turn, assert_after_player_end)
        check_step("Wróg ZABIJA Prowokację", 1.5,
                   lambda: game.attack("S103", TAUNT), assert_after_taunt)
        check_step("Wróg bije mojego bohatera: 5 → 1 PŻ", 1.8,
                   lambda: game.attack("S104", "hero:0"), assert_after_hero_hit)
        check_step("Koniec tury wroga: Burda ZABIJA CAŁĄ PLANSZĘ", 2.4,
                   game.end_turn, assert_after_brawl)
        check_step("MOJA TURA — mam 1 PŻ, wróg bez Prowokacji", 0.9)
        check_step("Wystawiam Instruktora Błyskawicznego Natarcia", 1.3,
                   lambda: game.play(QUICK), assert_after_quick)
        check_step("SZYBKI ATAK — ostatni cios w bohatera 1 PŻ", 2.1,
                   lambda: game.attack(QUICK, "hero:1"), assert_final,
                   selected=QUICK)
        exporter.captured.append("STAGED_SCENE")
    except BaseException:
        exporter.abort()
        raise
    else:
        exporter.close()

    report = output.with_suffix(".timeline.json")
    report.write_text(json.dumps(timeline, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"SUCCESS {output}, frames={exporter.total}, "
          f"bytes={output.stat().st_size}, result={game.winner}, "
          f"hero={game.players[0].hp} HP, enemy={game.players[1].hp} HP")
    return output


if __name__ == "__main__":
    run_scene(Path("preview/AuctionHammer_BURDA_1HP_SZYBKI_ATAK.mp4"))
