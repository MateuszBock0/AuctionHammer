"""Read-only, source-of-truth text for the Karczemna Burda HUD hover.

All descriptions derive from current Match flags/counters. No second timer,
UI-owned damage formula, RNG, new save fields or combat-side operations.
"""


def brawl_help_lines(game):
    """Text for the brawl explainer, including pre-0.9.100 saved rules.

    The actual next tick occurs at the end of a COMPLETED player turn.
    Damage affects deployed units on both boards through shields/armor.
    """
    if not getattr(game,'tavern_beer_enabled',False):
        return ()
    remaining=max(0,int(getattr(game,'beer_turns_remaining',0)))
    scaled=bool(getattr(game,'tavern_scaled_damage_enabled',False))
    min_hp=bool(getattr(game,'tavern_min_hp_damage_enabled',False))
    if remaining:
        damage=remaining if scaled else 1
        first=(f'AKTYWNA: {remaining} tur do wygaśnięcia.',
               (f'NASTĘPNY TICK: max({damage} DMG, 10% MAX PŻ celu).'
                if min_hp else
                f'NASTĘPNY KONIEC TURY: {damage} DMG na jednostkę.'))
    else:
        first=('NIEAKTYWNA: 0 pozostałych tur.',
               'Kup kufel [B], aby uruchomić Burdę.')
    if min_hp:
        return first+(
            'MINIMUM: 10% całkowitego MAX PŻ każdej jednostki,',
            'zaokrąglone W GÓRĘ; nie od aktualnego PŻ.',
            'Trafia jednostki obu graczy, także własne.',
            'Tarcza blokuje cios, pancerz pochłania DMG.',
            'Bohaterowie i karty na ręce są bezpieczne.',
            'Licznik maleje co turę; kolejny kufel: +3 tury.',
        )
    rule=('W nowych grach obrażenia maleją o 1 z każdą turą.'
          if scaled else
          'Ta starsza partia: zawsze 1 DMG na koniec tury.')
    additional=('Kolejny kufel: +3 tury i większe następne DMG.'
                if scaled else
                'Kolejny kufel: +3 tury, nadal 1 DMG.')
    return first+(
        'Na koniec każdej tury trafia WSZYSTKIE jednostki',
        'obu graczy na planszy (także własne).',
        'Tarcza blokuje cios; pancerz pochłania obrażenia.',
        'Bohaterowie i karty na ręce nie otrzymują DMG.',
        'Po każdym zakończeniu tury licznik maleje o 1.',
        additional,
        rule,
    )
