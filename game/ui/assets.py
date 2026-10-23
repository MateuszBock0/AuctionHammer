"""Proste ładowanie ilustracji PNG, z pamięcią podręczną i awaryjną grafiką."""
# AUCTIONHAMMER_PIXEL_ART_70_v1

from pathlib import Path
import sys
import pygame

from game import config as cfg

ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


class ImageAssets:
    def __init__(self) -> None:
        self._original: dict[str, pygame.Surface] = {}
        self._scaled: dict[tuple, pygame.Surface] = {}
        self._auction_colors: dict[str, tuple[int, int, int]] = {}

    @staticmethod
    def fit_art(image: pygame.Surface, size: tuple[int,int],
                mode: str='cover', focus: tuple[float,float]=(0.5,0.5),
                background: tuple[int, int, int] | None = None, pixelated: bool = False) -> pygame.Surface:
        """One uniform scale; optional background fills containment margins."""
        import math
        w,h=map(int,size)
        if min(w,h)<=0:raise ValueError('Nonpositive image size')
        if mode not in ('cover','contain'):raise ValueError('Unknown image fit mode')
        if not all(0<=x<=1 for x in focus):raise ValueError('Invalid focus')
        iw,ih=image.get_size()
        if iw<=0 or ih<=0:raise ValueError('Empty source image')
        ratio=(max if mode=='cover' else min)(w/iw,h/ih)
        sw,sh=max(1,math.ceil(iw*ratio)),max(1,math.ceil(ih*ratio))
        fitted=(pygame.transform.scale(image,(sw,sh)) if pixelated
                else pygame.transform.smoothscale(image,(sw,sh)))
        surface=pygame.Surface((w,h),pygame.SRCALPHA)
        surface.fill(cfg.PANEL if background is None else background)
        if mode=='cover':
            ox=round((sw-w)*focus[0])
            oy=round((sh-h)*focus[1])
            surface.blit(fitted,(0,0),pygame.Rect(ox,oy,w,h))
        else:
            surface.blit(fitted,((w-sw)//2,(h-sh)//2))
        return surface

    def get_card_image(self, filename: str, size: tuple[int,int],
                       mode: str='cover',focus: tuple[float,float]=(0.5,0.5),
                       pixelated: bool=False) -> pygame.Surface:
        key=(filename,tuple(size),mode,tuple(focus),pixelated)
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
            self._scaled[key]=self.fit_art(self._original[filename],size,mode,focus,pixelated=pixelated)
        return self._scaled[key]

    @staticmethod
    def dominant_color(image: pygame.Surface) -> tuple[int, int, int]:
        """Most populated 32-step RGB color cluster among opaque pixels.

        Quantization groups neighboring shades in painted illustrations; the
        output is the actual mean RGB of the largest cluster, not an invented
        faction/rarity color. Sampled once on load, not each animation frame.
        Transparent pixels never bias the result toward black.
        """
        samples: dict[tuple[int,int,int], list[int]] = {}
        raw = pygame.image.tobytes(image, "RGBA")
        for index in range(0, len(raw), 16):  # every fourth pixel
            r, g, b, a = raw[index:index + 4]
            if a < 192:
                continue
            group = (r >> 5, g >> 5, b >> 5)
            values = samples.setdefault(group, [0, 0, 0, 0])
            values[0] += 1
            values[1] += r
            values[2] += g
            values[3] += b
        if not samples:
            return cfg.PANEL
        count, red, green, blue = max(samples.values(), key=lambda x:x[0])
        return red // count, green // count, blue // count

    def _auction_base(self, archetype: str, rarity: str) -> str | None:
        from game.core.auction_catalog import V22_CARDS, RARITIES
        if archetype not in V22_CARDS or rarity not in RARITIES:
            return None
        filename = f'{archetype}_{rarity}.png'
        key = 'auction/' + filename
        if key not in self._original:
            path = ROOT_DIR / 'assets' / 'auction' / filename
            if not path.is_file():
                return None
            try:
                self._original[key] = pygame.image.load(str(path)).convert_alpha()
            except (OSError, pygame.error):
                return None
            self._auction_colors[key] = self.dominant_color(self._original[key])
        return key

    def get_auction_color(self, archetype: str,
                          rarity: str) -> tuple[int,int,int] | None:
        """Cached dominant hue of the CURRENT sprite; None for missing art."""
        key = self._auction_base(archetype, rarity)
        return self._auction_colors[key] if key is not None else None

    def get_auction_image(self, archetype: str, rarity: str,
                          size: tuple[int, int],
                          mode: str = 'cover') -> pygame.Surface | None:
        """Current rarity sprite on a matching-color backdrop (cached)."""
        original_key = self._auction_base(archetype, rarity)
        if original_key is None:
            return None
        cache_key = ('auction', original_key, tuple(size), mode)
        if cache_key not in self._scaled:
            self._scaled[cache_key] = self.fit_art(
                self._original[original_key], size, mode,
                background=self._auction_colors[original_key])
        return self._scaled[cache_key]

    @staticmethod
    def _fallback() -> pygame.Surface:
        img=pygame.Surface((300,200),pygame.SRCALPHA)
        img.fill(cfg.PANEL)
        pygame.draw.circle(img,cfg.GOLD,(150,98),50,width=4)
        pygame.draw.line(img,cfg.GOLD,(100,98),(200,98),3)
        pygame.draw.line(img,cfg.GOLD,(150,48),(150,148),3)
        return img
