"""Ikony z pakietu Minimal Fantasy v1 — 35 oryginalnych wzorów.

Priorytet mają indywidualne PNG; wydanie portable zawiera 40-pikselowy
atlas o 256 kolorach i zachowanej przezroczystości. Brak pliku -> fallback.
"""
from __future__ import annotations

from pathlib import Path
import sys
import pygame

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[2]))
BASE=ROOT/'assets'/'ui'/'icons'

FAMILY={
    'Obrażenia':'obrazenia','Leczenie':'leczenie','ATK ±':'atak_pm',
    'MAX HP ±':'max_pz_pm','Pancerz':'pancerz','Tarcza':'tarcza',
    'Trucizna':'trucizna','Ogłuszenie':'ogluszenie',
    'Regeneracja':'regeneracja','Prowokacja':'prowokacja',
    'Oczyszczanie':'oczyszczanie','Odporność':'odpornosc',
    'Szybki atak':'szybki_atak','Podwójny atak':'podwojny_atak',
}
FACTION={
    'Elfy':'elfy','Dzikie bestie':'dzikie_bestie','Potwory':'potwory',
    'Krasnoludy':'krasnoludy','Ludzie':'ludzie',
}
STATUS={
    'poison':'poison','stun':'stun','regen':'regen','taunt':'taunt',
    'shield':'shield','armor':'armor','quick':'quick','double':'double',
    'atk_up':'atk_up','atk_down':'atk_down','hp_up':'hp_up',
    'hp_down':'hp_down','cleanse':'cleanse_negative',
    # Brak osobnej ikony aury leczenia; nie sugeruj, że to regeneracja.
    'heal_aura':None,
}

# Klucze dokładnie odpowiadają kolejności komórek w atlasie utworzonym
# z 35 oryginalnych osobnych ikon 64 px, dostarczonych przez agenta UI.
ATLAS_FILES=[
    'zdolnosci/atak_pm','zdolnosci/leczenie','zdolnosci/max_pz_pm',
    'zdolnosci/obrazenia','zdolnosci/oczyszczanie','zdolnosci/odpornosc',
    'zdolnosci/ogluszenie','zdolnosci/pancerz','zdolnosci/podwojny_atak',
    'zdolnosci/prowokacja','zdolnosci/regeneracja','zdolnosci/szybki_atak',
    'zdolnosci/tarcza','zdolnosci/trucizna',
    'statusy/armor','statusy/atk_down','statusy/atk_up',
    'statusy/cleanse_negative','statusy/cleanse_positive',
    'statusy/double','statusy/hp_down','statusy/hp_up',
    'statusy/immune_poison','statusy/immune_stun',
    'statusy/poison','statusy/quick','statusy/regen',
    'statusy/shield','statusy/stun','statusy/taunt',
    'frakcje/dzikie_bestie','frakcje/elfy','frakcje/krasnoludy',
    'frakcje/ludzie','frakcje/potwory',
]
ATLAS_INDEX={key:i for i,key in enumerate(ATLAS_FILES)}
ATLAS_SIZE=40


def status_icon_key(status):
    if status.category=='immune':
        return 'immune_stun' if 'ogłusz' in status.name.lower() else 'immune_poison'
    if status.category=='cleanse':
        text=(status.name+' '+status.detail).lower()
        return 'cleanse_positive' if 'pozytywn' in text and 'negatywn' not in text else 'cleanse_negative'
    return STATUS.get(status.category)


class GameIcons:
    def __init__(self):
        self._original={}
        self._cache={}
        self._atlas=None
        self._tried_atlas=False

    def _atlas_image(self):
        if not self._tried_atlas:
            self._tried_atlas=True
            path=BASE/'icon_atlas_35.png'
            if path.is_file():
                try:self._atlas=pygame.image.load(str(path)).convert_alpha()
                except (OSError,pygame.error):self._atlas=None
        return self._atlas

    def get(self,key,group='families',size=20):
        if group=='families':target='zdolnosci/'+FAMILY.get(key,'')
        elif group=='factions':target='frakcje/'+FACTION.get(key,'')
        elif group=='statuses':target='statusy/'+str(key)
        else:raise ValueError(group)
        if target.endswith('/'):return None
        size=int(size)
        cache_key=(target,size)
        if cache_key in self._cache:return self._cache[cache_key]
        image=self._original.get(target)
        if target not in self._original:
            folder,name=target.split('/')
            path=BASE/f'{folder}_64'/f'{name}.png'
            if not path.is_file():path=BASE/folder/f'{name}.png'
            if path.is_file():
                try:image=pygame.image.load(str(path)).convert_alpha()
                except (OSError,pygame.error):image=None
            if image is None:
                atlas=self._atlas_image()
                if atlas is not None and target in ATLAS_INDEX:
                    index=ATLAS_INDEX[target]
                    rect=pygame.Rect((index%7)*ATLAS_SIZE,
                                     (index//7)*ATLAS_SIZE,
                                     ATLAS_SIZE,ATLAS_SIZE)
                    if atlas.get_rect().contains(rect):
                        image=atlas.subsurface(rect).copy()
            self._original[target]=image
        # Icons are pixel art; never blur their edges when shown at HUD sizes.
        result=pygame.transform.scale(image,(size,size)) if image else None
        self._cache[cache_key]=result
        return result
