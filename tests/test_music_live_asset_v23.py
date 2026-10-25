"""Decode and briefly play the REAL tracked soundtrack, not an empty mock file.

Use SDL's dummy audio driver, so this test is stable on headless GitHub CI.
"""
import os
import unittest
from pathlib import Path

os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import pygame

from game.ui.music import MUSIC_DIR,album_files,FantasyTavernMusic


class TrackedMusicIntegration(unittest.TestCase):
    def test_real_album_decodes_and_loops_without_restarting_between_views(self):
        track=MUSIC_DIR/'music_auctionhammer.mp3'
        self.assertTrue(track.is_file(),f'Missing tracked soundtrack: {track}')
        self.assertGreater(track.stat().st_size,1_000_000)
        self.assertEqual(album_files(MUSIC_DIR),(track,))
        pygame.init()
        try:
            player=FantasyTavernMusic(MUSIC_DIR)
            self.assertIsNone(player.error,player.error)
            self.assertEqual(len(player.tracks),1)
            self.assertIsNone(player.end_event)
            self.assertTrue(pygame.mixer.music.get_busy())
            self.assertAlmostEqual(pygame.mixer.music.get_volume(),.4,places=2)
            before=pygame.mixer.music.get_pos()
            self.assertFalse(player.handle_event(pygame.event.Event(pygame.USEREVENT)))
            self.assertTrue(pygame.mixer.music.get_busy())
            self.assertGreaterEqual(pygame.mixer.music.get_pos(),before)
        finally:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            pygame.quit()


if __name__=='__main__':
    unittest.main()
