"""0.9.89 low-volume SFX: preferences and confirmed-action-only playback."""
import os
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import wave
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock,patch
import unittest

import pygame

from game.ui.sfx import (QuietSFX,DEFAULT_MUSIC,DEFAULT_SFX,
                         synthesize_wav,load_levels,save_levels,_PRESETS)
from game.ui.app import SoloApp


class SoundPolish0989(unittest.TestCase):
    def test_defaults_and_persistence_are_independent_of_game_save(self):
        self.assertEqual((DEFAULT_MUSIC,DEFAULT_SFX),(.4,.1))
        with TemporaryDirectory() as temp:
            path=Path(temp)/'audio.json'
            self.assertEqual(load_levels(path),{'music':.4,'sfx':.1})
            self.assertTrue(save_levels({'music':.8,'sfx':0},path))
            self.assertEqual(load_levels(path),{'music':.8,'sfx':0})
            path.write_text('{"music": -99, "sfx": 3}',encoding='utf-8')
            self.assertEqual(load_levels(path),{'music':.4,'sfx':.1})
            path.write_text('not json',encoding='utf-8')
            self.assertEqual(load_levels(path),{'music':.4,'sfx':.1})

    def test_all_eight_soft_sounds_are_short_and_peak_limited(self):
        self.assertEqual(len(_PRESETS),8)
        for name in _PRESETS:
            with self.subTest(name=name):
                payload=synthesize_wav(name)
                with wave.open(BytesIO(payload),'rb') as wav:
                    self.assertEqual(wav.getframerate(),22050)
                    self.assertEqual(wav.getsampwidth(),2)
                    self.assertEqual(wav.getnchannels(),1)
                    self.assertLess(wav.getnframes(),12000)
                    self.assertGreater(wav.getnframes(),3000)

    def test_settings_buttons_step_ten_percent_without_touching_game(self):
        app=SoloApp.__new__(SoloApp)
        app.menu_page='settings'
        app.audio_levels={'music':.4,'sfx':.1}
        app.music=Mock()
        app.sfx=Mock()
        with patch('game.ui.app.save_levels',return_value=True) as save:
            app._menu_click((500,299))
            app._menu_click((800,299))
            self.assertAlmostEqual(app.audio_levels['music'],.5)
            self.assertAlmostEqual(app.audio_levels['sfx'],.2)
            app.music.set_volume.assert_called_once_with(.5)
            app.sfx.set_volume.assert_called_once_with(.2)
            self.assertEqual(save.call_count,2)
        app.audio_levels['sfx']=1
        with patch('game.ui.app.save_levels'):
            app._menu_click((800,299))
        self.assertEqual(app.audio_levels['sfx'],0)

    def test_only_successful_audited_action_triggers_cue(self):
        cues=QuietSFX(volume=0)
        cues.volume=.1
        cues.sounds={name:Mock() for name in _PRESETS}
        game=SimpleNamespace(audit_actions=[])
        visuals=SimpleNamespace(pulses=[])
        cues.reset(game)
        game.audit_actions.append({'operation':'attack','result':'error'})
        cues.observe(game,visuals,1000)
        self.assertFalse(any(x.play.called for x in cues.sounds.values()))
        game.audit_actions.append({'operation':'attack','result':'ok'})
        cues.observe(game,visuals,1200)
        self.assertEqual(cues.sounds['attack_swoosh'].play.call_count,1)
        # New confirmed damage after the swoosh arrives later, never early.
        visuals.pulses.append(SimpleNamespace(kind='damage'))
        cues.observe(game,visuals,1380)
        self.assertEqual(cues.sounds['hit'].play.call_count,1)
        cues.observe(game,visuals,1550)
        self.assertEqual(cues.sounds['hit'].play.call_count,1)

    def test_modal_consumes_feedback_without_playback_after_unpausing(self):
        cues=QuietSFX(volume=0)
        cues.volume=.1
        cues.sounds={name:Mock() for name in _PRESETS}
        game=SimpleNamespace(audit_actions=[])
        visuals=SimpleNamespace(pulses=[])
        cues.reset(game)
        game.audit_actions.append({'operation':'play','result':'ok'})
        cues.observe(game,visuals,500,allowed=False)
        cues.observe(game,visuals,1000,allowed=True)
        cues.sounds['card_place'].play.assert_not_called()

    def test_audio_device_failure_keeps_game_running(self):
        with patch.object(pygame.mixer,'get_init',return_value=None), \
             patch.object(pygame.mixer,'init',side_effect=pygame.error('no device')):
            cues=QuietSFX(volume=.1)
        self.assertEqual(cues.error,'no device')
        self.assertFalse(cues.sounds)


if __name__=='__main__':
    unittest.main()
