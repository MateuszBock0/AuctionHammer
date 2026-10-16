"""Proste ładowanie ilustracji PNG, z pamięcią podręczną i awaryjną grafiką."""

from pathlib import Path
import sys
import pygame

from game import config as cfg

ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


class ImageAssets:
    def __init__(self) -> None:
        self._original: dict[str, pygame.Surface] = {}
        self._scaled: dict[tuple[str, int, int], pygame.Surface] = {}

    def get_card_image(self, filename: str, size: tuple[int, int]) -> pygame.Surface:
        key = (filename, *size)
        if key not in self._scaled:
            if filename not in self._original:
                path = ROOT_DIR / "assets" / "cards" / filename
                if path.is_file():
                    try:
                        self._original[filename] = pygame.image.load(str(path)).convert_alpha()
                    except pygame.error:
                        self._original[filename] = self._fallback()
                else:
                    self._original[filename] = self._fallback()
            self._scaled[key] = pygame.transform.smoothscale(self._original[filename], size)
        return self._scaled[key]

    @staticmethod
    def _fallback() -> pygame.Surface:
        img = pygame.Surface((300, 200), pygame.SRCALPHA)
        img.fill(cfg.PANEL)
        pygame.draw.circle(img, cfg.GOLD, (150, 98), 50, width=4)
        pygame.draw.line(img, cfg.GOLD, (100, 98), (200, 98), 3)
        pygame.draw.line(img, cfg.GOLD, (150, 48), (150, 148), 3)
        return img
