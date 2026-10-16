"""Punkt startowy gry AuctionHammer.

Działa zarówno jako `python game/main.py`, jak i `python -m game.main`.
"""

from pathlib import Path
import sys

# Umożliwia uruchomienie pliku bezpośrednio z głównego folderu projektu.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.ui.app import run


if __name__ == "__main__":
    run()
