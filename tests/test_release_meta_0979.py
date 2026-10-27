"""0.9.79 public release metadata, end-user links and safe version bumps."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from tools.release_meta import (
    ROOT, ReleaseMetadataError, bump_version, current_changelog_section,
    current_version, release_notes, validate, validate_readme_paths,
)


class ReleaseMetadata0979(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'game').mkdir()
        (self.root/'docs').mkdir()
        (self.root/'docs/guide.md').write_text('A guide',encoding='utf-8')
        (self.root/'docs/art.png').write_bytes(b'just-a-link-fixture')
        (self.root/'VERSION.json').write_text(
            '{"app": "AuctionHammer", "mvp": "0.9.78"}',
            encoding='utf-8')
        (self.root/'game/config.py').write_text(
            '"""AuctionHammer MVP 0.9.78"""\n'
            'WINDOW_TITLE = "AuctionHammer MVP 0.9.78"\n',encoding='utf-8')
        (self.root/'README.md').write_text(
            '**Wersja MVP: 0.9.78**\n'
            '[Instrukcja](docs/guide.md)\n'
            '<img src="docs/art.png" alt="Art" />\n'
            '<a href="https://github.com/x">External</a>\n',
            encoding='utf-8')
        (self.root/'CHANGELOG.md').write_text(
            '# Changelog\n\n## [0.9.78]\n\n### Dodano\n'
            '- Linki aktywnych aur.\n\n'
            '## [0.9.76]\n\n### Dodano\n- Potwierdzenie końca tury.\n',
            encoding='utf-8')

    def test_live_repo_public_metadata_is_consistent(self):
        self.assertEqual(validate(ROOT),current_version(ROOT))

    def test_fixture_consistency(self):
        self.assertEqual(validate(self.root),'0.9.78')
        self.assertEqual(current_version(self.root),'0.9.78')
        self.assertEqual(validate_readme_paths(self.root),[])

    def test_release_notes_not_contaminated_with_previous_version(self):
        notes=release_notes(self.root)
        self.assertIn('Linki aktywnych aur.',notes)
        self.assertNotIn('Potwierdzenie końca tury.',notes)
        self.assertNotIn('## [0.9.76]',notes)
        self.assertIn('AuctionHammer-Windows.zip.sha256',notes)
        self.assertIn('AuctionHammer 0.9.78',notes)

    def test_bad_readme_link_rejected(self):
        path=self.root/'README.md'
        path.write_text(path.read_text(encoding='utf-8')
                        +'[Brak](docs/missing.md)\n',encoding='utf-8')
        with self.assertRaisesRegex(ReleaseMetadataError,'Broken relative paths'):
            validate(self.root)

    def test_bad_html_image_src_rejected(self):
        path=self.root/'README.md'
        path.write_text(path.read_text(encoding='utf-8')
                        +'<img src="docs/missing.png" />\n',encoding='utf-8')
        self.assertEqual(validate_readme_paths(self.root),
                         ['docs/missing.png'])

    def test_wrong_config_version_rejected(self):
        path=self.root/'game/config.py'
        path.write_text('"""AuctionHammer MVP 0.9.78"""\n'
                        'WINDOW_TITLE = "AuctionHammer MVP 0.9.77"\n',
                        encoding='utf-8')
        with self.assertRaisesRegex(ReleaseMetadataError,'game/config.py'):
            validate(self.root)

    def test_missing_changelog_current_release_rejected(self):
        path=self.root/'CHANGELOG.md'
        path.write_text('# Changelog\n\n## [0.9.76]\n\n'
                        '### Dodano\n- Old.\n',encoding='utf-8')
        with self.assertRaisesRegex(ReleaseMetadataError,'does not match'):
            validate(self.root)

    def test_todo_blocks_releases(self):
        path=self.root/'CHANGELOG.md'
        text=path.read_text(encoding='utf-8')
        path.write_text(text.replace('Linki aktywnych aur.',
                                     'TODO: Linki aktywnych aur.'),
                        encoding='utf-8')
        with self.assertRaisesRegex(ReleaseMetadataError,'TODO'):
            validate(self.root)

    def test_bump_updates_four_files_and_requires_release_notes(self):
        bump_version(self.root,'0.9.80',date(2026,10,24))
        self.assertEqual(current_version(self.root),'0.9.80')
        self.assertIn('MVP 0.9.80',(self.root/'game/config.py').read_text())
        self.assertIn('Wersja MVP: 0.9.80',(self.root/'README.md').read_text())
        self.assertIn('## [0.9.80] — 2026-10-24',
                      (self.root/'CHANGELOG.md').read_text())
        with self.assertRaisesRegex(ReleaseMetadataError,'TODO'):
            validate(self.root)
        path=self.root/'CHANGELOG.md'
        path.write_text(path.read_text().replace(
            'TODO: Opisz konkretne zmiany dla graczy.',
            'Usprawniono czytelność.'),encoding='utf-8')
        self.assertEqual(validate(self.root),'0.9.80')
        self.assertIn('Usprawniono czytelność.',release_notes(self.root))

    def test_bump_older_or_equal_version_rejected_without_files_changes(self):
        before={p:(self.root/p).read_bytes() for p in
                ('README.md','VERSION.json','CHANGELOG.md','game/config.py')}
        for version in ('0.9.78','0.9.76','v0.9.99','v1.0.0',
                        '01.0.0','1.00.0','1.0.00','1.0.0-rc1','1.0'):
            with self.subTest(version=version):
                with self.assertRaises(ReleaseMetadataError):
                    bump_version(self.root,version,date(2026,10,24))
        after={p:(self.root/p).read_bytes() for p in before}
        self.assertEqual(after,before)

    def test_promote_to_first_stable_1_0_0(self):
        # An actual release bump stays blocked until non-TODO notes exist.
        bump_version(self.root,'1.0.0',date(2026,10,27))
        self.assertEqual(current_version(self.root),'1.0.0')
        self.assertIn('MVP 1.0.0',
                      (self.root/'game/config.py').read_text(encoding='utf-8'))
        self.assertIn('Wersja MVP: 1.0.0',
                      (self.root/'README.md').read_text(encoding='utf-8'))
        self.assertIn('## [1.0.0] — 2026-10-27',
                      (self.root/'CHANGELOG.md').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ReleaseMetadataError,'TODO'):
            validate(self.root)
        changelog=self.root/'CHANGELOG.md'
        changelog.write_text(changelog.read_text(encoding='utf-8').replace(
            'TODO: Opisz konkretne zmiany dla graczy.',
            'Stabilne wydanie gry solo na Windows.'
        ),encoding='utf-8')
        self.assertEqual(validate(self.root),'1.0.0')
        self.assertIn('AuctionHammer 1.0.0',release_notes(self.root))
        self.assertNotIn('## [0.9.78]',release_notes(self.root))

    def test_semver_major_rollforward_without_truncation(self):
        bump_version(self.root,'2.0.0',date(2027,1,1))
        self.assertEqual(current_version(self.root),'2.0.0')
        self.assertIn('## [2.0.0]',current_changelog_section(self.root))
        # A lower version cannot replace the already promoted major.
        with self.assertRaises(ReleaseMetadataError):
            bump_version(self.root,'1.99.99',date(2027,1,1))

    def test_bad_mvp_field_is_rejected(self):
        path=self.root/'VERSION.json'
        obj=json.loads(path.read_text())
        obj['mvp']='latest'
        path.write_text(json.dumps(obj),encoding='utf-8')
        with self.assertRaisesRegex(ReleaseMetadataError,'Invalid'):
            validate(self.root)


if __name__=='__main__':
    unittest.main()
