"""Model stanu silnika — bez zależności od pygame."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json
import random
from typing import Any

FACTIONS = ("Elfy", "Dzikie bestie", "Potwory", "Krasnoludy", "Ludzie")
FAMILIES = ("Obrażenia", "Leczenie", "ATK ±", "MAX HP ±", "Pancerz", "Tarcza", "Trucizna", "Ogłuszenie", "Regeneracja", "Prowokacja", "Oczyszczanie", "Odporność", "Szybki atak", "Podwójny atak")
TRIGGERS = {"Elfy":"Przy wystawieniu", "Dzikie bestie":"Przy ataku", "Potwory":"Przy śmierci", "Krasnoludy":"Na koniec tury", "Ludzie":"Pasywna"}


@dataclass(frozen=True)
class CardDefinition:
    id: str
    name: str
    faction: str
    family: str
    trigger: str
    atk: int
    hp: int
    effect: str
    scaling: str
    growth_atk: int
    growth_hp: int


def load_catalog(path: Path) -> dict[str, CardDefinition]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data["cards"] if isinstance(data, dict) else data
    result: dict[str, CardDefinition] = {}
    for row in raw:
        ident = row["id"]
        if ident in result:
            raise ValueError("Duplicate card: " + ident)
        g = row["hand_growth"]
        card = CardDefinition(ident, row["name"], row["faction"], row["family"], row["trigger"],
                              int(row["atk"]), int(row["hp"]), row["effect"], row["scaling"],
                              int(g["atk_per_hand_turn"]), int(g["hp_per_hand_turn"]))
        if card.faction not in FACTIONS or card.family not in FAMILIES or card.trigger != TRIGGERS[card.faction]:
            raise ValueError("Invalid faction/family/trigger: " + ident)
        if (card.growth_atk, card.growth_hp) not in ((2,0),(1,1),(0,2)):
            raise ValueError("Invalid growth: " + ident)
        result[ident] = card
    if len(result) != 70 or len({x.name for x in result.values()}) != 70:
        raise ValueError("Expected exactly 70 unique cards")
    for f in FACTIONS:
        if {x.family for x in result.values() if x.faction == f} != set(FAMILIES):
            raise ValueError("Missing family in faction " + f)
    if isinstance(data,dict) and data.get('copy_count_each') != 1:
        raise ValueError("MVP requires one copy per archetype")
    # 70 distinct definitions themselves are the 70 physical instances (70x1).
    return result


@dataclass
class Effect:
    kind: str
    value: int = 0
    remaining: int = 0  # poison/regen ticks; 0 for other timed effects
    expires: int | None = None  # turn ordinal of controller, at end of turn
    source: str = ""
    positive: bool = True
    bonus_once: int = 0
    expire_action: int | None = None
    initial_ticks: int = 0


@dataclass
class Card:
    uid: str
    definition: CardDefinition
    owner: int | None = None
    zone: str = "bank"
    hand_turns: int = 0
    # Granted only to the specified card for its immediately upcoming play
    quick_next_turn: int | None = None
    quick_on_first_summon: bool = False  # v19 S66 / S90 target, bound to this card instance
    double_on_first_eligible: bool = False  # v19 S91 fallback, bound to card instance

    @property
    def ability_level(self) -> int:
        return self.hand_turns // 3

    @property
    def attack(self) -> int:
        extra = 2 * self.ability_level if self.definition.family in ("Szybki atak", "Podwójny atak") else 0
        return self.definition.atk + self.definition.growth_atk * self.hand_turns + extra

    @property
    def max_hp(self) -> int:
        extra = (1 if self.definition.family == "Szybki atak" else 3 if self.definition.family in ("Prowokacja", "Tarcza") else 0) * self.ability_level
        return self.definition.hp + self.definition.growth_hp * self.hand_turns + extra


@dataclass
class Unit:
    uid: str
    owner: int
    base_attack: int
    base_max_hp: int
    hp: int
    ability_level: int
    played_turn: int
    attacks: int = 0
    shield: int = 0
    armor_perm: int = 0
    armor_temp: int = 0
    temporary_armor: dict[str, int] = field(default_factory=dict)
    aura_armor: dict[str, int] = field(default_factory=dict)
    effects: list[Effect] = field(default_factory=list)
    aura_atk: int = 0
    aura_hp: int = 0
    aura_mode: str = "ally"
    used_shield_aura: bool = False
    seen_opponents: set[str] = field(default_factory=set)
    last_stun_target: str = ""
    last_stun_turn: int = -10
    fallback_double_pending: bool = False
    fallback_double_started: bool = False
    passives_triggered: set[str] = field(default_factory=set)
    # Diagnostic provenance for shield and armor; authoritative numeric value stays above.
    shield_source: str = ""
    armor_perm_source: str = ""
    armor_temp_source: str = ""
    armor_perm_grants: dict[str,int] = field(default_factory=dict)

    @property
    def max_hp(self) -> int:
        return max(0, self.base_max_hp + self.aura_hp + sum(e.value for e in self.effects if e.kind == "max_hp"))

    @property
    def atk(self) -> int:
        return max(0, self.base_attack + self.aura_atk + sum(e.value for e in self.effects if e.kind == "atk"))

    @property
    def armor(self) -> int:
        return self.armor_temp + self.armor_perm + sum(self.temporary_armor.values()) + sum(self.aura_armor.values())


@dataclass
class Player:
    idx: int
    name: str
    hand: list[str] = field(default_factory=list)
    deck: list[str] = field(default_factory=list)
    grave: list[str] = field(default_factory=list)
    board: list[str] = field(default_factory=list)
    hp: int = 100
    coins: int = 0
    turn_count: int = 0
    played_this_turn: bool = False
    thresholds: set[int] = field(default_factory=set)
    hero_effects: list[Effect] = field(default_factory=list)
    hero_armor: int = 0
    hero_shield: int = 0
    mulligan_selected: list[str] = field(default_factory=list)
    next_fast: bool = False


@dataclass(frozen=True)
class Choice:
    mode: str
    target: str | None
    label: str


@dataclass
class Pending:
    uid: str
    owner: int
    context: str
    choices: list[Choice]
    attack_target: str | None = None


class IllegalMove(ValueError):
    pass
