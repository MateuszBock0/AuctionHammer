"""Deterministic audio-loop mocks; real MP3 decode is covered by test_music_live_asset_v23."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pygame
from game.ui.music import FantasyTavernMusic, album_files


class SoundtrackTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_no_audio_is_optional(self):
        with patch.object(pygame.mixer, "get_init") as mixer:
            player = FantasyTavernMusic(self.folder)
        mixer.assert_not_called()
        self.assertEqual(player.tracks, ())
        self.assertIsNone(player.error)

    def test_missing_one_track_disables_playlist(self):
        for number in range(1, 13):
            (self.folder / f"{number:02d}.mp3").touch()
        self.assertEqual(album_files(self.folder), ())

    def test_single_full_album_loops_indefinitely(self):
        path = self.folder / "fantasy_tavern_full.ogg"
        path.touch()
        with (patch.object(pygame.mixer, "get_init", return_value=True),
              patch.object(pygame.mixer, "music") as audio):
            player = FantasyTavernMusic(self.folder)
            audio.load.assert_called_once_with(str(path))
            audio.play.assert_called_once_with(loops=-1)
            self.assertIsNone(player.end_event)

    def test_thirteen_tracks_in_order_repeat_from_one(self):
        for number in range(1, 14):
            (self.folder / f"{number:02d} - track.mp3").touch()
        with (patch.object(pygame.mixer, "get_init", return_value=True),
              patch.object(pygame.mixer, "music") as audio,
              patch.object(pygame.event, "custom_type", return_value=pygame.USEREVENT + 15)):
            player = FantasyTavernMusic(self.folder)
            self.assertEqual(len(player.tracks), 13)
            for number in range(1, 14):
                self.assertTrue(player.handle_event(pygame.event.Event(pygame.USEREVENT + 15)))
                self.assertEqual(player.index, number % 13)
            self.assertEqual(audio.play.call_count, 14)
            self.assertEqual(audio.load.call_args.args[0], str(self.folder / "01 - track.mp3"))
            audio.play.assert_called_with(loops=0)

    def test_requested_mp3_name_is_selected_and_entire_file_loops(self):
        path = self.folder / "music_auctionhammer.mp3"
        path.touch()
        with (patch.object(pygame.mixer, "get_init", return_value=True),
              patch.object(pygame.mixer, "music") as audio):
            player = FantasyTavernMusic(self.folder)
            self.assertEqual(player.tracks, (path,))
            audio.load.assert_called_once_with(str(path))
            audio.play.assert_called_once_with(loops=-1)

    def test_portable_windows_reads_mp3_next_to_exe_not_internal(self):
        from game.ui.music import local_music_folder
        package = self.folder / "portable" / "AuctionHammer"
        audio_dir = package / "assets" / "music"
        audio_dir.mkdir(parents=True)
        (audio_dir / "music_auctionhammer.mp3").touch()
        with (patch("game.ui.music.sys.frozen", True, create=True),
              patch("game.ui.music.sys.executable", str(package / "AuctionHammer.exe"))):
            self.assertEqual(local_music_folder(), audio_dir.resolve())

    def test_credits_button_opens_music_attribution_without_gameplay_changes(self):
        from game.ui.app import SoloApp

        app = SoloApp.__new__(SoloApp)
        app.menu_page = "main"
        app.menu_message = ""
        app._menu_click((925, 300))
        self.assertEqual(app.menu_page, "credits")
        app._menu_click((745, 713))
        self.assertEqual(app.menu_page, "main")

    def test_invalid_file_does_not_crash_game(self):
        (self.folder / "fantasy_tavern_full.mp3").touch()
        with (patch.object(pygame.mixer, "get_init", return_value=True),
              patch.object(pygame.mixer, "music") as audio):
            audio.load.side_effect = pygame.error("invalid audio")
            player = FantasyTavernMusic(self.folder)
        self.assertEqual(player.error, "invalid audio")


if __name__ == "__main__":
    unittest.main()
