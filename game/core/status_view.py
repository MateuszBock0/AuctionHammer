"""Read-only, semantic descriptions of active unit effects for the UI.

The engine remains authoritative; this module never changes game state.
All bestowed effects are derived from the actual Unit/Effect instances (or
live auras) rather than inferred from the card's effect description.
"""
from __future__ import annotations
from dataclasses import dataclass

from . import auction_abilities as auction_ability_rules

# Solid contrasting palette: one colour per type of effect.
STATUS_COLORS = {
    'taunt': (184, 192, 205),
    'poison': (173, 214, 81),
    'stun': (194, 136, 244),
    'regen': (84, 218, 160),
    'shield': (255, 210, 64),
    'armor': (171, 191, 210),
    'quick': (75, 226, 219),
    'double': (227, 69, 78),
    'atk_up': (112, 220, 120),
    'atk_down': (242, 108, 113),
    'hp_up': (135, 225, 152),
    'hp_down': (240, 119, 126),
    'immune': (114, 164, 255),
    'heal_aura': (120, 230, 192),
    'cleanse': (190, 220, 240),
    'other': (195, 195, 195),
}

@dataclass(frozen=True)
class VisibleStatus:
    category: str
    short: str
    name: str
    detail: str
    source: str = ''

    @property
    def color(self):
        return STATUS_COLORS.get(self.category, STATUS_COLORS['other'])


def active_statuses(game, uid: str) -> list[VisibleStatus]:
    """All current buffs/debuffs, including bestowed and aura effects.

    Includes intrinsic active traits, but does NOT claim that an ability
    was bestowed if it is currently disabled or expired.
    """
    u = game.units.get(uid)
    if u is None:
        return []
    d = game.cards[uid].definition
    player = game.players[u.owner]
    out: list[VisibleStatus] = []

    def source_name(src):
        if not src:
            return 'nieznane'
        # Temporary armor markers can use source IDs with an @ suffix.
        if ', ' in src:
            return ', '.join(source_name(part) for part in src.split(', '))
        identity = src.split('@', 1)[0]
        if identity in game.cards:
            return game.cards[identity].definition.name
        return 'efekt tymczasowy' if identity == 'temporary' else identity

    def add(key, short, name, detail, src=''):
        out.append(VisibleStatus(key, short, name, detail, source_name(src) if src else ''))

    for e in u.effects:
        key=e.kind
        duration=[]
        if e.remaining>0:
            duration.append(f'pozostałe aktywacje: {e.remaining}')
        if e.expires is not None:
            duration.append(f'wygaśnie na koniec własnej tury nr {e.expires}')
        if e.expire_action is not None:
            duration.append('do końca bieżącej tury')
        until='; '.join(duration) if duration else 'do opuszczenia planszy / według reguły karty'
        if key=='poison':
            add('poison','TRUC', 'Trucizna', f'{e.value} obraż. na aktywację'+(f'; +{e.bonus_once} przy najbliższym tyknięciu' if e.bonus_once and e.remaining==e.initial_ticks else '')+'; '+until,e.source)
        elif key=='regen':
            add('regen','REGEN','Regeneracja',f'{e.value} HP na aktywację'+(f'; +{e.bonus_once} przy najbliższej aktywacji' if e.bonus_once and e.remaining==e.initial_ticks else '')+'; '+until,e.source)
        elif key=='stun':add('stun','OGŁ','Ogłuszenie','Nie może atakować ani aktywować własnych zdolności; '+until,e.source)
        elif key=='taunt':add('taunt','PROW','Prowokacja','Wrogie ataki muszą celować w jednostki z prowokacją; '+until,e.source)
        elif key=='quick':add('quick','SZYB','Szybki atak','Może atakować w turze wystawienia; '+until,e.source)
        elif key=='double':add('double','2×','Podwójny atak','Maksymalnie dwa ataki w turze; '+until,e.source)
        elif key=='immune_poison':add('immune','ODP','Odporność na truciznę','Zapobiega truciznom; '+until,e.source)
        elif key=='immune_stun':add('immune','ODP','Odporność na ogłuszenie','Zapobiega ogłuszeniu; '+until,e.source)
        elif key=='atk':
            add('atk_up' if e.value>=0 else 'atk_down',f'ATK{e.value:+}', 'Zmiana ATK', f'{e.value:+} ATK; {until}',e.source)
        elif key=='max_hp':
            add('hp_up' if e.value>=0 else 'hp_down',f'HP{e.value:+}', 'Zmiana MAX HP', f'{e.value:+} MAX HP; {until}',e.source)
        elif key=='temp_armor_marker':
            armor=u.temporary_armor.get(e.source,0)
            if armor>0:add('armor',f'P{armor}', 'Pancerz tymczasowy', f'{armor} punktów; {until}',e.source)
        else:
            add('other',key.upper()[:5],key,until,e.source)

    if u.shield>0:
        add('shield','TARCZ', 'Tarcza', f'{u.shield} ładunek; blokuje najbliższe zwykłe zdarzenie obrażeń',getattr(u,'shield_source','') or (uid if d.id=='S106' else ''))
    if u.armor_perm>0:
        known=0
        for src,value in u.armor_perm_grants.items():
            if value>0:
                add('armor',f'P{value}', 'Pancerz trwały', f'{value} punktów trwałego pancerza (nie leczy się)',src)
                known+=value
        other=max(0,u.armor_perm-known)
        if other:
            add('armor',f'P{other}', 'Pancerz trwały', f'{other} punktów trwałego pancerza, źródło nieoznaczone')
    if u.armor_temp>0:
        add('armor',f'P{u.armor_temp}', 'Pancerz tymczasowy',f'{u.armor_temp} punktów tymczasowego pancerza',getattr(u,'armor_temp_source',''))
    for src, val in u.aura_armor.items():
        if val>0:add('armor',f'P{val}', 'Pancerz z aury', f'{val} punktów, działa gdy źródło aury jest aktywne',src)
    def aura_sources(card_id):
        sources=[]
        for src,p in game.units.items():
            if game.cards[src].definition.id!=card_id or game._disabled(p):continue
            friend=game.players[p.owner].board
            enemy=game.players[1-p.owner].board
            position=game.slot_of(src)
            if card_id=='S34':
                affected=[]
                if p.aura_mode=='ally':
                    if game.fixed_board_slots:
                        neighbor=(game.unit_at(p.owner,position+1) or
                                  game.unit_at(p.owner,position-1))
                        if neighbor is not None:affected=[neighbor]
                    elif len(friend)>1:
                        affected=[friend[position+1] if position+1<len(friend) else friend[position-1]]
                elif game.fixed_board_slots:
                    target=game.unit_at(1-p.owner,position)
                    if target is not None:affected=[target]
                elif position<len(enemy):
                    affected=[enemy[position]]
            else:
                affected=[x for x in (friend if p.aura_mode=='ally' else enemy) if x!=src]
            if uid in affected:sources.append(src)
        return sources
    if u.aura_atk:
        add('atk_up' if u.aura_atk>0 else 'atk_down',f'ATK{u.aura_atk:+}', 'Aura ATK', f'{u.aura_atk:+} ATK, efekt dynamiczny', ', '.join(aura_sources('S34')))
    if u.aura_hp:
        add('hp_up' if u.aura_hp>0 else 'hp_down',f'HP{u.aura_hp:+}', 'Aura MAX HP', f'{u.aura_hp:+} MAX HP, efekt dynamiczny', ', '.join(aura_sources('S35')))

    # General A002 stores its grants outside Unit.effects. Keep this display
    # derived from exactly the same live predicate used by engine combat.
    if (game.auction_catalog in ('v4','v22') and
            auction_ability_rules.boosted_attack(game,uid)):
        generals=[]
        for src,target in game.auction_general_targets.items():
            leader=game.units.get(src)
            if (target==uid and leader is not None and leader.owner==u.owner
                    and auction_ability_rules.rarity(game,src)==1
                    and not game._disabled(leader)):
                generals.append(src)
        for src,recipients in game.auction_general_grants.items():
            leader=game.units.get(src)
            if (uid in recipients and leader is not None and leader.owner==u.owner
                    and auction_ability_rules.rarity(game,src)==2
                    and not game._disabled(leader)):
                generals.append(src)
        add('double','DMG×2','Premia Generała Oddziału Natarcia',
            'OBRAŻENIA STANDARDOWE ×2; maksymalnie 2 ataki w turze; '
            'ATK na karcie bez zmian; premia znika po utracie Generała',
            ', '.join(generals))

    if u.fallback_double_pending and (u.played_turn != player.turn_count or game._fast(u)) and not game._has(u,'stun'):
        add('double','2×','Podwójny atak — awaryjny (S91)','Pierwsza własna tura, w której możliwy jest legalny atak; maksymalnie dwa ataki', 'S91')
    disabled=game._disabled(u)
    active_kinds={e.kind for e in u.effects}
    if d.id=='S33' and not disabled and 'taunt' not in active_kinds:
        add('taunt','PROW','Prowokacja (wrodzona)','Wrogie ataki muszą celować w jednostki z prowokacją',uid)
    if d.id == 'S114' and not disabled and 'quick' not in active_kinds:
        add('quick','SZYB','Szybki atak (wrodzony)','Może atakować w turze wystawienia',uid)
    if d.id in ('S115','S79') and not disabled and (d.id!='S79' or u.attacks>0) and 'double' not in active_kinds:
        add('double','2×','Podwójny atak (wrodzony)','Maksymalnie dwa ataki w turze',uid)
    if d.id=='S39' and not disabled and 'immune_poison' not in active_kinds:
        add('immune','ODP','Odporność na truciznę (wrodzona)','Nie otrzymuje trucizny',uid)
    if d.id=='S111' and not disabled:
        add('cleanse','OCZ','Samooczyszczanie (wrodzone)','Nowe czasowe negatywne efekty są automatycznie usuwane',uid)

    heal_sources=[x for x in player.board if x in game.units and game.cards[x].definition.id=='S104' and not game._disabled(game.units[x])]
    if heal_sources:
        amount=sum(2+game.units[x].ability_level for x in heal_sources)
        add('heal_aura',f'LECZ+{amount}','Aura zwiększonego leczenia',f'+{amount} HP, gdy jednostka jest leczona przez zdolność',', '.join(heal_sources))

    return out


def hand_grants(game, uid: str) -> list[VisibleStatus]:
    """Show every actual instance-scoped bonus waiting on a card in hand."""
    c=game.cards.get(uid)
    if c is None or c.zone!='hand':return []
    result=[]
    if c.quick_next_turn is not None and c.owner is not None:
        result.append(VisibleStatus('quick','SZYB','Nadany Szybki atak',f'Tylko jeśli wystawisz kartę w swojej turze nr {c.quick_next_turn}','Konstruktor Sprężyn'))
    if c.quick_on_first_summon:
        result.append(VisibleStatus('quick','SZYB','Szybki atak na pierwsze wystawienie','Bonus zostanie zużyty przy najbliższym wystawieniu tej konkretnej karty','S66 / S90'))
    if c.double_on_first_eligible:
        result.append(VisibleStatus('double','2×','Podwójny atak (pierwsza legalna tura)','Jedna najbliższa własna tura, w której jednostka może zaatakować po wystawieniu','S91'))
    return result
