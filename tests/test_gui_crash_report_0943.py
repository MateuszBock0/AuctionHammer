"""A GUI crash must leave a readable diagnostic instead of silently closing BAT."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game.main import run_with_crash_report


class WindowsCrashReportAcceptance(unittest.TestCase):
    def test_uncaught_gui_exception_creates_latest_report(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ,{'LOCALAPPDATA':td,'SDL_VIDEODRIVER':'dummy'}):
                def fail():
                    raise RuntimeError('drag replay diagnostic sentinel')
                self.assertEqual(run_with_crash_report(fail),1)
            logfile=Path(td)/'AuctionHammer'/'crash_latest.log'
            self.assertTrue(logfile.is_file())
            contents=logfile.read_text(encoding='utf-8')
            self.assertIn('RuntimeError: drag replay diagnostic sentinel',contents)
            self.assertIn('Python:',contents)

    def test_normal_gui_exit_has_no_report(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ,{'LOCALAPPDATA':td,'SDL_VIDEODRIVER':'dummy'}):
                self.assertEqual(run_with_crash_report(lambda: None),0)
            self.assertFalse((Path(td)/'AuctionHammer'/'crash_latest.log').exists())


if __name__=='__main__':
    unittest.main()
