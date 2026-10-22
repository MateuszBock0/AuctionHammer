"""Short, truthful attack recaps calculated from two committed Match snapshots.

Only the presentation layer consumes these objects. No predicted damage,
independent combat resolution, game commands or audit mutations are involved.
"""
from __future__ import annotations

from dataclasses import dataclass


STATUS_NAMES = {
    "poison": "Trucizna", "stun": "Ogłuszenie",
    "silence": "Wyciszenie", "regen": "Regeneracja",
    "taunt": "Prowokacja", "quick": "Szybki atak",
    "double": "Podwójny atak",
    "immune_poison": "Odporność na truciznę",
    "immune_stun": "Odporność na ogłuszenie",
}


@dataclass(frozen=True)
class AttackOutcome:
    """One latest completed attack, not a FIFO of stale combat log entries."""
    journal_length: int
    lines: tuple[str, ...]
    hidden: int = 0
    attacker: str = ''
    target: str = ''
    details: tuple[str, ...] = ()


def _display_name(game, uid: str) -> str:
    if uid.startswith("hero:"):
        return game.players[int(uid.split(":", 1)[1])].name
    card = game.cards.get(uid)
    return card.definition.name if card is not None else uid


def committed_attack_outcome(game, prior: dict, current: dict,
                             events: list, journal_length: int) -> AttackOutcome | None:
    """Summarize actual HP/shield changes after a recorded attack.

    Diffing snapshots accounts for retaliation and chained effects. Removed
    units count as deaths only when the engine recorded a Zgon event, so a
    replacement or banishment cannot masquerade as a kill.
    """
    attacks = [evt["text"] for evt in events if " atakuje: " in evt["text"]]
    if not attacks:
        return None
    attacker, last_target = attacks[-1].split(" atakuje: ", 1)
    last_target = last_target.rstrip(".")
    confirmed_deaths = {
        uid for uid in prior if uid not in current and not uid.startswith("hero:")
        and any(evt["text"].startswith(f"Zgon {_display_name(game, uid)}.")
                for evt in events)
    }
    changes = []
    for uid, old in prior.items():
        new = current.get(uid)
        if new is None and uid not in confirmed_deaths:
            continue
        name = _display_name(game, uid)
        old_hp = max(0, old["hp"])
        new_hp = max(0, new["hp"]) if new is not None else 0
        old_shield = old["shield"]
        new_shield = new["shield"] if new is not None else 0
        old_armor = old.get("armor", 0)
        new_armor = new.get("armor", 0) if new is not None else 0
        old_status = set(old.get("status", ()))
        new_status = set(new.get("status", ())) if new is not None else set()
        fragments = []
        if new_hp != old_hp:
            fragments.append(f"PŻ {old_hp}→{new_hp}")
        # A dead unit leaves the board. Its missing defenses are not proof
        # they were *consumed by this hit*. Only compare protection for
        # surviving combatants; death is reported as its own consequence.
        if new is not None:
            if new_shield != old_shield:
                fragments.append(f"tarcza {old_shield}→{new_shield}")
            if new_armor != old_armor:
                fragments.append(f"pancerz {old_armor}→{new_armor}")
            if new_status - old_status:
                translated=(STATUS_NAMES.get(kind,kind)
                            for kind in sorted(new_status - old_status))
                fragments.append("nowe efekty: " + ", ".join(translated))
        if uid in confirmed_deaths:
            fragments.append("ZGON")
        if not fragments:
            continue
        # Present the actual attacked target first, then other consequences
        # such as retaliation, splash damage, or a chained death.
        primary = int(name != last_target and name not in last_target)
        changes.append((primary, f"{name}: {', '.join(fragments)}"))
    changes.sort(key=lambda item: item[0])
    if not changes:
        return AttackOutcome(
            journal_length, ("Brak zmiany PŻ / ochrony; szczegóły [H].",),
            attacker=attacker, target=last_target,
            details=("Nie wykryto zmiany PŻ, tarczy, pancerza ani statusów.",))
    hidden = max(0, len(changes) - 2)
    visible = [line for _, line in changes[:2]]
    if hidden:
        visible[-1] += f" · +{hidden} [H]"
    return AttackOutcome(journal_length, tuple(visible), hidden,
                         attacker=attacker, target=last_target,
                         details=tuple(line for _, line in changes))
