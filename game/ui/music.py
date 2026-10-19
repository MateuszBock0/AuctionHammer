"""Optional full-length PGN Fantasy Tavern Album loop. No audio files are bundled."""
from __future__ import annotations

from pathlib import Path
import re
import sys
import pygame

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
MUSIC_DIR = ROOT / "assets" / "music"
EXTENSIONS = (".ogg", ".mp3", ".wav")


def album_files(folder: Path) -> tuple[Path, ...]:
    if not folder.is_dir():
        return ()
    for extension in EXTENSIONS:
        full = folder / ("fantasy_tavern_full" + extension)
        if full.is_file():
            return (full,)
    available = sorted(f for f in folder.iterdir()
                       if f.is_file() and f.suffix.lower() in EXTENSIONS)
    tracks = []
    for i in range(1, 14):
        found = [f for f in available
                 if re.match(rf"^{i:02d}(?:$|[^0-9])", f.stem)]
        if len(found) != 1:
            return ()
        tracks.append(found[0])
    return tuple(tracks)


class FantasyTavernMusic:
    """Play all tracks in order, then repeat; audio never restarts between matches."""

    def __init__(self, folder: Path | None = None):
        self.tracks = album_files(Path(folder) if folder is not None else MUSIC_DIR)
        self.index = 0
        self.end_event = None
        self.error = None
        if not self.tracks:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.set_volume(0.3)
            if len(self.tracks) == 1:
                pygame.mixer.music.set_endevent()
            else:
                self.end_event = pygame.event.custom_type()
                pygame.mixer.music.set_endevent(self.end_event)
            self._play()
        except (pygame.error, OSError) as exc:
            self.error = str(exc)
            self.end_event = None

    def _play(self):
        pygame.mixer.music.load(str(self.tracks[self.index]))
        pygame.mixer.music.play(loops=-1 if len(self.tracks) == 1 else 0)

    def handle_event(self, event) -> bool:
        if self.end_event is None or event.type != self.end_event:
            return False
        self.index = (self.index + 1) % len(self.tracks)
        try:
            self._play()
        except (pygame.error, OSError) as exc:
            self.error = str(exc)
            self.end_event = None
        return True
