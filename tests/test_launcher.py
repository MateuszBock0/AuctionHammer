# Przenieś ten plik do tests/test_launcher.py w repozytorium AuctionHammer.
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from launch_auctionhammer import find_projects, check_update


def git(*args, cwd=None):
    return subprocess.run(['git', *map(str, args)], cwd=cwd, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


@unittest.skipUnless(shutil.which('git'), 'git nie jest zainstalowany')
class LauncherGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.project = self.home / 'Desktop' / 'AuctionHammer'
        (self.project/'game').mkdir(parents=True)
        (self.project/'data').mkdir()
        (self.project/'game'/'main.py').write_text('print("game")\n')
        (self.project/'data'/'cards_base_70.json').write_text('[]\n')
        (self.project/'requirements.txt').write_text('# no dependencies\n')
        self.bare = self.home/'origin.git'
        git('init', '--bare', self.bare)
        git('init', '-b', 'main', cwd=self.project)
        git('config', 'user.name', 'Launcher test', cwd=self.project)
        git('config', 'user.email', 'launcher@example.test', cwd=self.project)
        git('add', '.', cwd=self.project)
        git('commit', '-m', 'baseline', cwd=self.project)
        git('remote', 'add', 'origin', self.bare, cwd=self.project)
        git('push', '-u', 'origin', 'main', cwd=self.project)
        self.writer = self.home / 'writer'
        git('clone', '-b', 'main', self.bare, self.writer)
        git('config', 'user.name', 'Launcher test', cwd=self.writer)
        git('config', 'user.email', 'launcher@example.test', cwd=self.writer)

    def publish(self, content):
        (self.writer/'feature.txt').write_text(content)
        git('add', '.', cwd=self.writer)
        git('commit', '-m', 'feature', cwd=self.writer)
        git('push', cwd=self.writer)

    def test_finds_project_inside_profile(self):
        self.assertIn(self.project.resolve(), find_projects(self.home))

    def test_updates_only_after_remote_commit(self):
        self.assertTrue(check_update(shutil.which('git'), self.project, check_only=False))
        self.publish('new version\n')
        previous = git('rev-parse', 'HEAD', cwd=self.project)
        self.assertFalse(check_update(shutil.which('git'), self.project, check_only=True))
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.project), previous)
        self.assertTrue(check_update(shutil.which('git'), self.project, check_only=False))
        self.assertEqual((self.project/'feature.txt').read_text(), 'new version\n')

    def test_does_not_overwrite_untracked_files(self):
        self.publish('remote\n')
        (self.project/'my_changes.txt').write_text('important local changes\n')
        before = git('rev-parse', 'HEAD', cwd=self.project)
        self.assertFalse(check_update(shutil.which('git'), self.project, check_only=False))
        self.assertEqual(before, git('rev-parse', 'HEAD', cwd=self.project))
        self.assertEqual((self.project/'my_changes.txt').read_text(), 'important local changes\n')
        self.assertFalse((self.project/'feature.txt').exists())


if __name__ == '__main__':
    unittest.main()
