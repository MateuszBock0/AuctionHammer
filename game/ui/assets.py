"""Proste ładowanie ilustracji PNG, z pamięcią podręczną i awaryjną grafiką."""
# AUCTIONHAMMER_PIXEL_ART_70_v1

from pathlib import Path
import sys
import io
import zipfile
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

    # All 51 authentic rarity portraits are composed over 51 bespoke fantasy
    # atmospheres. The background ZIP stores 102 pixel-art crops (portrait and
    # banner), but the recognizable character ALWAYS comes from the original
    # verified assets/auction/Axxx_rarity.png. No external API / runtime network.
    AUCTION_SCENES_ZIP = 'auction51_scenes.zip'

    def _auction_pixel_scene(self, archetype: str, rarity: str,
                             size: tuple[int,int]) -> pygame.Surface | None:
        kind = 'banner' if size[1] <= 58 else 'portrait'
        name = f'{archetype}_{rarity}_{kind}.png'
        key = 'auction_scene/' + name
        if key not in self._original:
            archive = ROOT_DIR / 'assets' / 'auction' / 'pixel_art' / self.AUCTION_SCENES_ZIP
            if not archive.is_file():
                return None
            try:
                with zipfile.ZipFile(archive) as bundle:
                    scene_bytes = bundle.read(name)
                self._original[key] = pygame.image.load(
                    io.BytesIO(scene_bytes), name).convert_alpha()
            except (KeyError, OSError, pygame.error, zipfile.BadZipFile, ValueError):
                return None
        return self.fit_art(
            self._original[key], size, mode='cover', pixelated=True)

    @staticmethod
    def _compose_original_auction_character(
            scene: pygame.Surface, original: pygame.Surface,
            *, banner: bool) -> pygame.Surface:
        """Keep the correct existing character; new pixel art supplies scenery.

        Figures are scaled with nearest neighbour only, with natural aspect ratio.
        A cropped square portrait must never turn into a miniature inside a wide
        strip or turn into a stretched face. This is display-only compositing.
        """
        w,h = scene.get_size()
        bbox = original.get_bounding_rect(min_alpha=12)
        if bbox.width <= 0 or bbox.height <= 0:
            return scene
        figure = original.subsurface(bbox)
        fw,fh = figure.get_size()
        target_height = max(1, round(h * (1.32 if banner else 0.93)))
        target_width = max(1,round(fw * target_height / fh))
        # Keep some fantasy environment on both sides of the hero.
        if target_width > round(w * 0.76):
            target_width = max(1,round(w * 0.76))
            target_height = max(1,round(fh * target_width / fw))
        sprite = pygame.transform.scale(figure,(target_width,target_height))
        x = (w - target_width) // 2
        y = (-round(h * 0.06) if banner else
             h - target_height - round(h * 0.025))
        scene.blit(sprite,(x,y))
        return scene

    def get_auction_image(self, archetype: str, rarity: str,
                          size: tuple[int, int],
                          mode: str = 'cover') -> pygame.Surface | None:
        """A001–A018: cinematic pixel-art card crop, authentic character.

        Card/hover ('cover') uses one of the 102 composition-specific backgrounds
        and the original 96x96 character on top. Image inspection ('contain')
        continues to show the entire unmodified ORIGINAL sprite. Legacy
        screenshots/replays and non-updated builds still have a safe fallback.
        """
        original_key = self._auction_base(archetype, rarity)
        if original_key is None:
            return None
        cache_key = ('auction', original_key, tuple(size), mode)
        if cache_key not in self._scaled:
            scene = (self._auction_pixel_scene(archetype, rarity, size)
                     if mode == 'cover' else None)
            if scene is not None:
                self._scaled[cache_key] = self._compose_original_auction_character(
                    scene, self._original[original_key],
                    banner=size[1] <= 58)
            else:
                self._scaled[cache_key] = self.fit_art(
                    self._original[original_key],size,mode,
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
