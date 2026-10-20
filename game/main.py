"""Punkt startowy gry AuctionHammer.

Działa zarówno jako `python game/main.py`, jak i `python -m game.main`.
"""

from pathlib import Path
import sys
import os
import traceback
from datetime import datetime

def run_with_crash_report(entrypoint):
    """Keep the portable Windows launcher from disappearing without diagnosis.

    Crash reports go to LOCALAPPDATA, outside any replaceable game directory.
    This boundary only catches uncaught exceptions; it never pretends success.
    """
    try:
        entrypoint()
        return 0
    except Exception:
        report = traceback.format_exc()
        directory = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "AuctionHammer"
        filename = directory / "crash_latest.log"
        try:
            directory.mkdir(parents=True, exist_ok=True)
            details = (f"AuctionHammer unhandled exception — {datetime.now().isoformat()}\n"
                       f"Python: {sys.version}\n\n{report}")
            filename.write_text(details, encoding="utf-8")
        except OSError:
            filename = None
        if sys.stderr is not None:
            try:
                sys.stderr.write(report)
            except (OSError, ValueError):
                pass
        if os.name == "nt" and os.environ.get("SDL_VIDEODRIVER") != "dummy":
            try:
                import ctypes
                location = str(filename) if filename else "Nie udało się zapisać raportu."
                ctypes.windll.user32.MessageBoxW(
                    None,
                    "AuctionHammer napotkał błąd.\n\n"
                    f"Raport awarii:\n{location}\n\n"
                    "Prześlij plik crash_latest.log, aby można było naprawić błąd.",
                    "AuctionHammer — raport awarii", 0x10)
            except (OSError, AttributeError):
                pass
        return 1

# Umożliwia uruchomienie pliku bezpośrednio z głównego folderu projektu.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.ui.app import run


if __name__ == "__main__":
    raise SystemExit(run_with_crash_report(run))
