"""Regression tests for offline pygame-ce interpreter discovery.
Run from AuctionHammer: python -m unittest discover -s tests -v
"""
from __future__ import annotations
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from launch_auctionhammer import prepare_python, pygame_ready


class OfflineLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.project = self.home / 'Desktop' / 'AuctionHammer'
        self.project.mkdir(parents=True)
        (self.project / 'requirements.txt').write_text('pygame-ce>=2.5.0,<3\n', encoding='utf-8')
        self.executable_name = 'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
        self.project_py = self.project / '.venv' / self.executable_name
        self.global_py = self.home / '.venv' / self.executable_name

    @patch('launch_auctionhammer.pygame_ready')
    def test_uses_previously_installed_user_profile_environment_without_pip(self, ready):
        self.project_py.parent.mkdir(parents=True)
        self.project_py.write_text('dummy local exe')
        self.global_py.parent.mkdir(parents=True)
        self.global_py.write_text('dummy global exe')
        ready.side_effect = lambda p: p == self.global_py
        with patch.dict(os.environ, {'USERPROFILE': str(self.home)}), \
             patch('launch_auctionhammer.subprocess.run') as installer:
            selected = prepare_python(self.project)
        self.assertEqual(selected, self.global_py)
        installer.assert_not_called()

    @patch('launch_auctionhammer.pygame_ready')
    def test_uses_previously_installed_project_venv_without_pip(self, ready):
        self.project_py.parent.mkdir(parents=True)
        self.project_py.write_text('dummy project exe')
        ready.side_effect = lambda p: p == self.project_py
        with patch.dict(os.environ, {'USERPROFILE': str(self.home)}), \
             patch('launch_auctionhammer.subprocess.run') as installer:
            selected = prepare_python(self.project)
        self.assertEqual(selected, self.project_py)
        installer.assert_not_called()

    @patch('launch_auctionhammer.pygame_ready', return_value=False)
    def test_pip_is_last_resort_and_retries_zero(self, ready):
        self.project_py.parent.mkdir(parents=True)
        self.project_py.write_text('dummy exe')
        with patch.dict(os.environ, {'USERPROFILE': str(self.home)}), \
             patch('launch_auctionhammer.subprocess.run') as installer:
            with self.assertRaises(RuntimeError):
                prepare_python(self.project)
        command = installer.call_args.args[0]
        self.assertIn('--retries', command)
        self.assertEqual(command[command.index('--retries') + 1], '0')

    def test_missing_python_returns_false(self):
        self.assertFalse(pygame_ready(self.home / 'does-not-exist.exe'))


if __name__ == '__main__':
    unittest.main()
