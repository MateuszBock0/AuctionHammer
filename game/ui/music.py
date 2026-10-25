"""Optional full-length Fantasy Tavern album loop; tracked MP3 ships with Windows."""
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
    for stem in ("music_auctionhammer", "fantasy_tavern_full"):
        for extension in EXTENSIONS:
            full = folder / (stem + extension)
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


def local_music_folder() -> Path:
    """In a Windows portable build, look beside AuctionHammer.exe first."""
    if getattr(sys, "frozen", False):
        external = Path(sys.executable).resolve().parent / "assets" / "music"
        if album_files(external):
            return external
    return MUSIC_DIR


class FantasyTavernMusic:
    """Play all tracks in order, then repeat; audio never restarts between matches."""

    def __init__(self, folder: Path | None = None, volume: float = 0.40):
        self.volume=max(0.0,min(1.0,float(volume)))
        self.tracks = album_files(Path(folder) if folder is not None else local_music_folder())
        self.index = 0
        self.end_event = None
        self.error = None
        if not self.tracks:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            if len(self.tracks) == 1:
                pygame.mixer.music.set_endevent()
            else:
                self.end_event = pygame.event.custom_type()
                pygame.mixer.music.set_endevent(self.end_event)
            self._play()
        except (pygame.error, OSError) as exc:
            self.error = str(exc)
            self.end_event = None

    def set_volume(self,level: float):
        self.volume=max(0.0,min(1.0,float(level)))
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.volume)
        except pygame.error:
            pass

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
