"""0.9.80: P1 aura geometry and shipped Windows docs/links."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from zipfile import ZipFile

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.core.audit import digest, state_snapshot
from game.ui.app import SoloApp
from tools.release_package import InvalidRelease, REQUIRED, verify_folder, verify_zip
from test_engine import setup_game, force_unit


def crosses_interior(a, b, box):
    box=box.inflate(-12,-12)
    if a[0]==b[0]:
        return box.left < a[0] < box.right and max(a[1],b[1]) > box.top and min(a[1],b[1]) < box.bottom
    if a[1]==b[1]:
        return box.top < a[1] < box.bottom and max(a[0],b[0]) > box.left and min(a[0],b[0]) < box.right
    raise AssertionError("A non-orthogonal aura segment crossed the board")


class AuraGeometry0980(unittest.TestCase):
    def setUp(self):
        with patch.object(SoloApp, "_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp(start_in_menu=True)
        self.app.menu_open=False
        self.app.tutorial_welcome_open=False
        g=setup_game(980123)
        g.fixed_board_slots=True
        self.app.game=g
        self.app.selected=None

    def tearDown(self):
        pygame.quit()

    def check_route(self,src,dst,source_owner,target_owner):
        app=self.app
        p=app._aura_connector_path(app.slot_rect(source_owner,src),
                                   app.slot_rect(target_owner,dst),
                                   source_owner,target_owner)
        self.assertEqual(len(p),4)
        for a,b in zip(p,p[1:]):
            self.assertTrue(a[0]==b[0] or a[1]==b[1])
            for owner in (0,1):
                for slot in range(5):
                    self.assertFalse(crosses_interior(a,b,app.slot_rect(owner,slot)),
                                     (source_owner,src,target_owner,dst,owner,slot,p))
        source=app.slot_rect(source_owner,src)
        target=app.slot_rect(target_owner,dst)
        self.assertIn(p[0],(source.midtop,source.midbottom))
        self.assertIn(p[-1],(target.midtop,target.midbottom))

    def test_long_friendly_row_avoids_all_five_cards(self):
        for src,dst in ((0,4),(4,0),(1,3),(2,4)):
            for owner in (0,1):
                with self.subTest(owner=owner,src=src,dst=dst):
                    self.check_route(src,dst,owner,owner)

    def test_cross_row_diagonals_use_central_corridor(self):
        for a,c in ((0,4),(4,0),(2,2)):
            self.check_route(a,c,0,1)
            self.check_route(a,c,1,0)

    def test_actual_live_s35_full_board_renders_non_obscuring_segments(self):
        app=self.app
        for uid,slot in (("S35",0),("S01",1),("S02",2),("S09",3),("S04",4)):
            force_unit(app.game,uid,0,slot=slot)
        app.game._update_auras()
        app.selected="S35"
        before=digest(state_snapshot(app.game))
        actual=[]
        original=pygame.draw.line
        def observe(surface,color,a,b,width=1):
            actual.append((tuple(a),tuple(b),width))
            return original(surface,color,a,b,width)
        with patch.object(app,"card_under",return_value=None):
            with patch("game.ui.app.pygame.draw.line",side_effect=observe):
                app._draw_aura_links()
        self.assertGreater(len(actual),4)
        for a,b,width in actual:
            for owner in (0,1):
                for slot in range(5):
                    self.assertFalse(crosses_interior(a,b,app.slot_rect(owner,slot)))
        self.assertEqual(digest(state_snapshot(app.game)),before)


class WindowsReleasePackage0980(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"AuctionHammer"
        self.root.mkdir()
        for name in REQUIRED:
            dest=self.root/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text("fixture",encoding="utf-8")
        (self.root/"_internal").mkdir()
        (self.root/"_internal/runtime.dat").write_bytes(b"runtime")
        (self.root/"docs").mkdir()
        (self.root/"docs/PLAYER_GUIDE.md").write_text("guide",encoding="utf-8")
        (self.root/"assets/pixel").mkdir(parents=True)
        (self.root/"assets/pixel/hero.png").write_bytes(b"asset")
        (self.root/"README.md").write_text(
            '# AuctionHammer\n'
            '[Changelog](CHANGELOG.md) [Contributor](CONTRIBUTING.md) '
            '[Manual](docs/PLAYER_GUIDE.md)\n'
            '<img src="assets/pixel/hero.png" alt="art" />\n'
            '[Internet](https://github.com/MateuszBock0/AuctionHammer)\n',
            encoding="utf-8")
        self.archive=Path(self.tmp.name)/"AuctionHammer-Windows.zip"

    def package(self):
        with ZipFile(self.archive,"w") as z:
            for p in self.root.rglob("*"):
                if p.is_file():
                    z.write(p,p.relative_to(self.root.parent).as_posix())

    def test_full_package_passes_folder_and_zip_checks(self):
        verify_folder(self.root)
        self.package()
        verify_zip(self.archive)

    def test_missing_changelog_is_detected_in_folder_and_zip(self):
        (self.root/"CHANGELOG.md").unlink()
        with self.assertRaisesRegex(InvalidRelease,"CHANGELOG.md"):
            verify_folder(self.root)
        self.package()
        with self.assertRaisesRegex(InvalidRelease,"CHANGELOG.md"):
            verify_zip(self.archive)

    def test_missing_linked_image_is_detected_in_final_zip(self):
        (self.root/"assets/pixel/hero.png").unlink()
        self.package()
        with self.assertRaisesRegex(InvalidRelease,"assets/pixel/hero.png"):
            verify_zip(self.archive)

    def test_outside_path_in_readme_rejected(self):
        (self.root/"README.md").write_text("[file](../outside.txt)\n")
        with self.assertRaisesRegex(InvalidRelease,"Unsafe"):
            verify_folder(self.root)

    def test_missing_runtime_blocks_release(self):
        (self.root/"_internal/runtime.dat").unlink()
        (self.root/"_internal").rmdir()
        with self.assertRaisesRegex(InvalidRelease,"runtime"):
            verify_folder(self.root)

    def test_archive_with_wrong_root_is_rejected(self):
        with ZipFile(self.archive,"w") as z:
            z.writestr("wrong/README.md","README")
        with self.assertRaisesRegex(InvalidRelease,"one AuctionHammer"):
            verify_zip(self.archive)


if __name__=="__main__":
    unittest.main()
