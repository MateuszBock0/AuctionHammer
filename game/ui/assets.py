"""Proste ładowanie ilustracji PNG, z pamięcią podręczną i awaryjną grafiką."""

from pathlib import Path
import sys
import pygame

from game import config as cfg

ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


class ImageAssets:
    def __init__(self) -> None:
        self._original: dict[str, pygame.Surface] = {}
        self._scaled: dict[tuple, pygame.Surface] = {}

    @staticmethod
    def fit_art(image: pygame.Surface, size: tuple[int,int],
                mode: str='cover', focus: tuple[float,float]=(0.5,0.5)) -> pygame.Surface:
        """One uniform scale, then centered/focus crop; never stretch source art."""
        import math
        w,h=map(int,size)
        if min(w,h)<=0:raise ValueError('Nonpositive image size')
        if mode not in ('cover','contain'):raise ValueError('Unknown image fit mode')
        if not all(0<=x<=1 for x in focus):raise ValueError('Invalid focus')
        iw,ih=image.get_size()
        if iw<=0 or ih<=0:raise ValueError('Empty source image')
        ratio=(max if mode=='cover' else min)(w/iw,h/ih)
        sw,sh=max(1,math.ceil(iw*ratio)),max(1,math.ceil(ih*ratio))
        fitted=pygame.transform.smoothscale(image,(sw,sh))
        surface=pygame.Surface((w,h),pygame.SRCALPHA)
        surface.fill(cfg.PANEL)
        if mode=='cover':
            ox=round((sw-w)*focus[0])
            oy=round((sh-h)*focus[1])
            surface.blit(fitted,(0,0),pygame.Rect(ox,oy,w,h))
        else:
            surface.blit(fitted,((w-sw)//2,(h-sh)//2))
        return surface

    def get_card_image(self, filename: str, size: tuple[int,int],
                       mode: str='cover',focus: tuple[float,float]=(0.5,0.5)) -> pygame.Surface:
        key=(filename,tuple(size),mode,tuple(focus))
        if key not in self._scaled:
            if filename not in self._original:
                path=ROOT_DIR/'assets'/'cards'/filename
                if path.is_file():
                    try:
                        self._original[filename]=pygame.image.load(str(path)).convert_alpha()
                    except (pygame.error,OSError) as exc:
                        import warnings
                        warnings.warn(f'Nie można odczytać grafiki {filename}: {exc}',RuntimeWarning)
                        self._original[filename]=self._fallback()
                else:
                    import warnings
                    warnings.warn(f'Brak grafiki karty: {filename}',RuntimeWarning)
                    self._original[filename]=self._fallback()
            self._scaled[key]=self.fit_art(self._original[filename],size,mode,focus)
        return self._scaled[key]

    def get_auction_image(self, archetype: str, rarity: str,
                          size: tuple[int, int],
                          mode: str = 'cover') -> pygame.Surface | None:
        """Use exact 96px auction sprite for the current, actual rarity.

        Auction artwork is optional for old source checkouts, but once the
        0.9.57 asset bundle is installed its files are cached on first use.
        Never show a different rarity when one asset is missing.
        """
        from game.core.auction_catalog import V22_CARDS, RARITIES
        if archetype not in V22_CARDS or rarity not in RARITIES:
            return None
        filename = f'{archetype}_{rarity}.png'
        key = ('auction', filename, tuple(size), mode)
        if key in self._scaled:
            return self._scaled[key]
        original_key = 'auction/' + filename
        if original_key not in self._original:
            path = ROOT_DIR / 'assets' / 'auction' / filename
            if not path.is_file():
                return None
            try:
                self._original[original_key] = pygame.image.load(str(path)).convert_alpha()
            except (OSError, pygame.error):
                return None
        scaled = self.fit_art(self._original[original_key], size, mode)
        self._scaled[key] = scaled
        return scaled

    @staticmethod
    def _fallback() -> pygame.Surface:
        img=pygame.Surface((300,200),pygame.SRCALPHA)
        img.fill(cfg.PANEL)
        pygame.draw.circle(img,cfg.GOLD,(150,98),50,width=4)
        pygame.draw.line(img,cfg.GOLD,(100,98),(200,98),3)
        pygame.draw.line(img,cfg.GOLD,(150,48),(150,148),3)
        return img
