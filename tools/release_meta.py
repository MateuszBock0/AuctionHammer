"""Release metadata and public documentation gates for AuctionHammer.

VERSION.json -> mvp is the single product-version source. Exact build tags
remain SHA-derived by the Windows release workflow. Standard library only.

Usage:
    python -m tools.release_meta check
    python -m tools.release_meta bump 0.9.80
    python -m tools.release_meta notes --output release-notes.md
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"0\.[0-9]+\.[0-9]+\Z")
README_VERSION = re.compile(r"((?:\\*\\*|<strong>)Wersja MVP: )(0\\.[0-9]+\\.[0-9]+)((?:\\*\\*|</strong>))")
CONFIG_VERSION = re.compile(r"(MVP )(0\.[0-9]+\.[0-9]+)")
CHANGELOG_HEADER = re.compile(r"(?m)^## \[(0\.[0-9]+\.[0-9]+)\](?:[^\n]*)\n")
LOCAL_MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]\n]*\])\(([^)\n]+)\)")
LOCAL_HTML_LINK = re.compile(r'(?:src|href)="([^"]+)"')


class ReleaseMetadataError(ValueError):
    """The release or public documentation is inconsistent."""


def read_text(root: Path, name: str) -> str:
    return (root / name).read_text(encoding="utf-8")


def current_version(root: Path = ROOT) -> str:
    payload = json.loads(read_text(root, "VERSION.json"))
    version = payload.get("mvp")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise ReleaseMetadataError(f"Invalid VERSION.json.mvp: {version!r}")
    return version


def current_changelog_section(root: Path = ROOT, version: str | None = None) -> str:
    version = version or current_version(root)
    changelog = read_text(root, "CHANGELOG.md")
    headings = list(CHANGELOG_HEADER.finditer(changelog))
    if not headings:
        raise ReleaseMetadataError("CHANGELOG.md has no release headings.")
    if headings[0].group(1) != version:
        raise ReleaseMetadataError(
            f"Top CHANGELOG.md release {headings[0].group(1)} "
            f"does not match VERSION.json {version}.")
    end = headings[1].start() if len(headings) > 1 else len(changelog)
    section = changelog[headings[0].start():end].strip()
    if "TODO" in section:
        raise ReleaseMetadataError("Complete the current CHANGELOG.md TODO before release.")
    if not re.search(r"(?m)^- \S", section):
        raise ReleaseMetadataError("Current CHANGELOG.md release needs real changes.")
    return section


def validate_readme_paths(root: Path = ROOT) -> list[str]:
    """Check the landing page's tracked, relative URLs without using the network."""
    readme = read_text(root, "README.md")
    links = LOCAL_MARKDOWN_LINK.findall(readme) + LOCAL_HTML_LINK.findall(readme)
    problems = []
    for raw in links:
        # URL syntax in normal README link destinations never contains whitespace.
        address = raw.strip()
        url = urlsplit(address)
        if url.scheme or address.startswith(("#", "//", "mailto:")):
            continue
        target = unquote(url.path)
        if not target or target.startswith("/"):
            continue
        path = (root / target).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            problems.append(address)
    return sorted(set(problems))


def validate(root: Path = ROOT) -> str:
    version = current_version(root)
    config = read_text(root, "game/config.py")
    labels = [match.group(2) for match in CONFIG_VERSION.finditer(config)]
    if len(labels) < 2 or any(value != version for value in labels):
        raise ReleaseMetadataError(
            f"game/config.py labels {labels!r} do not match MVP {version}.")
    readme = read_text(root, "README.md")
    intro = README_VERSION.findall(readme)
    if len(intro) != 1 or intro[0][1] != version:
        raise ReleaseMetadataError(
            f"README version {intro!r} does not match VERSION.json {version}.")
    current_changelog_section(root, version)
    bad_links = validate_readme_paths(root)
    if bad_links:
        raise ReleaseMetadataError(
            "Broken relative paths in README.md: " + ", ".join(bad_links))
    return version


def release_notes(root: Path = ROOT) -> str:
    """Extract only the version's own details, never stale historic releases."""
    version = validate(root)
    section = current_changelog_section(root, version)
    return (
        f"# AuctionHammer {version} — wydanie Windows\n\n"
        + section + "\n\n"
        + "## Pobierz i uruchom\n\n"
        + "Pobierz `AuctionHammer-Windows.zip` oraz "
        + "`AuctionHammer-Windows.zip.sha256` z sekcji Assets. "
        + "Rozpakuj katalog `AuctionHammer` i uruchom "
        + "`AuctionHammer.exe`. Python nie jest potrzebny.\n\n"
        + "Aktualizacje: `URUCHOM_AUCTIONHAMMER.bat`. "
        + "Tryb offline: `GRAJ_BEZ_INTERNETU.bat`. "
        + "Wydania są sprawdzane SHA-256 i instalowane obok poprzednich.\n\n"
        + "[Instrukcja gry](https://github.com/MateuszBock0/AuctionHammer/blob/main/docs/PLAYER_GUIDE.md)"
        + " · [Pomoc](https://github.com/MateuszBock0/AuctionHammer/blob/main/docs/TROUBLESHOOTING.md)"
        + " · [Historia zmian](https://github.com/MateuszBock0/AuctionHammer/blob/main/CHANGELOG.md)"
        + "\n"
    )


def bump_version(root: Path, new: str, today: date | None = None) -> None:
    """Bump product version, leaving a REQUIRED changelog TODO for review."""
    if not SEMVER.fullmatch(new):
        raise ReleaseMetadataError(f"Bad requested version: {new!r}")
    old = validate(root)
    if tuple(map(int, new.split("."))) <= tuple(map(int, old.split("."))):
        raise ReleaseMetadataError("New version must be greater than current version.")
    raw = read_text(root, "VERSION.json")
    before = f'"mvp": "{old}"'
    if raw.count(before) != 1:
        raise ReleaseMetadataError("Cannot uniquely identify VERSION.json MVP field.")
    old_config = read_text(root, "game/config.py")
    matches = CONFIG_VERSION.findall(old_config)
    if len(matches) < 2 or any(item[1] != old for item in matches):
        raise ReleaseMetadataError("game/config.py version labels not unique/consistent.")
    old_readme = read_text(root, "README.md")
    if len(README_VERSION.findall(old_readme)) != 1:
        raise ReleaseMetadataError("README release badge ambiguous.")
    old_changelog = read_text(root, "CHANGELOG.md")
    first = CHANGELOG_HEADER.search(old_changelog)
    if first is None:
        raise ReleaseMetadataError("CHANGELOG.md release list missing.")
    stamp = (today or date.today()).isoformat()
    stub = (f"## [{new}] — {stamp}\n\n"
            "### Zmieniono\n- TODO: Opisz konkretne zmiany dla graczy.\n\n")
    updated = {
        "VERSION.json": raw.replace(before, f'"mvp": "{new}"'),
        "game/config.py": CONFIG_VERSION.sub(
            lambda match: match.group(1) + new, old_config),
        "README.md": README_VERSION.sub(
            lambda match: match.group(1) + new + match.group(3), old_readme),
        "CHANGELOG.md": old_changelog[:first.start()]
                        + stub + old_changelog[first.start():],
    }
    # Prepare all outputs before writing to keep error cases non-destructive.
    for relative, text in updated.items():
        (root / relative).write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Validate all public release metadata.")
    bump = commands.add_parser("bump", help="Bump product version and create changelog TODO.")
    bump.add_argument("new_version")
    notes = commands.add_parser("notes", help="Generate release notes from CHANGELOG.md.")
    notes.add_argument("--output", type=Path,
                       help="Write UTF-8 notes to the given path instead of stdout.")
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "check":
            print("PASS: AuctionHammer " + validate(ROOT)
                  + " — release metadata, CHANGELOG and README paths.")
        elif arguments.command == "bump":
            bump_version(ROOT, arguments.new_version)
            print("Changed to " + arguments.new_version
                  + "; edit CHANGELOG TODO before merging.")
        else:
            content = release_notes(ROOT)
            if arguments.output:
                arguments.output.write_text(content, encoding="utf-8")
                print("Wrote " + str(arguments.output))
            else:
                print(content, end="")
    except (ReleaseMetadataError, OSError, json.JSONDecodeError) as error:
        print("Release validation failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
