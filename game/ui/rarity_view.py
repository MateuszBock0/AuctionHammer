"""Pure presentation lookup for real, EVOLVING auction-card rarity.

Auction metadata is authoritative when supplied. The definition scaling
also updates after live rarity evolution; legacy cards keep canonical text.
"""
from __future__ import annotations

RARITY_COLORS={
    'podstawowa':(157,126,95),
    'rzadka':(149,192,241),
    'legendarna':(244,193,66),
}
RARITY_LABELS={
    'podstawowa':'PODSTAWOWA',
    'rzadka':'RZADKA',
    'legendarna':'LEGENDARNA',
}


def card_rarity(card, explicit=None):
    if explicit in RARITY_COLORS:return explicit
    if not card.definition.id.startswith('A0'):return None
    text=card.definition.scaling.upper()
    # Recognize exact tier label, not numeric POZIOM which evolves separately.
    for key,label in RARITY_LABELS.items():
        if label in text:return key
    return None


def rarity_color(tier):
    return RARITY_COLORS.get(tier,(171,134,85))
