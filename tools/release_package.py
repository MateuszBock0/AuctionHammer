"""Verify the EXACT public Windows folder and its ZIP are usable offline.

Unlike a repo-only link check, this rejects release archives missing any
document/image to which their enclosed README points.
"""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

from tools.release_meta import LOCAL_HTML_LINK, LOCAL_MARKDOWN_LINK


REQUIRED = frozenset({
    "AuctionHammer.exe", "VERSION.json", "BUILD_VERSION.txt", "README.md",
    "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE",
    "URUCHOM_AUCTIONHAMMER.bat", "GRAJ_BEZ_INTERNETU.bat",
    "COFNIJ_AKTUALIZACJE.bat", "tools/portable_launcher.ps1",
})


class InvalidRelease(ValueError):
    pass


def readme_local_paths(text: str) -> set[str]:
    targets=set()
    for raw in LOCAL_MARKDOWN_LINK.findall(text)+LOCAL_HTML_LINK.findall(text):
        address=raw.strip()
        u=urlsplit(address)
        if u.scheme or address.startswith(("#", "//", "mailto:")):
            continue
        if not u.path:
            continue
        path=unquote(u.path).replace("\\","/")
        p=PurePosixPath(path)
        if (p.is_absolute() or any(part==".." for part in p.parts)
                or path.startswith("./../")):
            raise InvalidRelease(f"Unsafe README target: {path}")
        targets.add(str(p))
    return targets


def missing_paths(all_paths: set[str], readme: str) -> set[str]:
    return (REQUIRED | readme_local_paths(readme)) - all_paths


def verify_folder(folder: Path) -> None:
    if not (folder/"README.md").is_file():
        raise InvalidRelease("Missing packaged README.md")
    names={p.relative_to(folder).as_posix()
           for p in folder.rglob("*") if p.is_file()}
    # PyInstaller's _internal is a directory, not a file.
    if not (folder/"_internal").is_dir():
        raise InvalidRelease("Missing PyInstaller _internal runtime")
    missing=missing_paths(names,(folder/"README.md").read_text(encoding="utf-8"))
    if missing:
        raise InvalidRelease("Missing package content: "+", ".join(sorted(missing)))


def verify_zip(archive: Path) -> None:
    with ZipFile(archive) as bundle:
        names=bundle.namelist()
        if any(not name.startswith("AuctionHammer/") for name in names):
            raise InvalidRelease("ZIP must contain one AuctionHammer/ root")
        rel={name[len("AuctionHammer/"):] for name in names}
        readme_name="AuctionHammer/README.md"
        if readme_name not in names:
            raise InvalidRelease("Missing packaged README.md in ZIP")
        content=bundle.read(readme_name).decode("utf-8")
        missing=missing_paths(rel,content)
        if missing:
            raise InvalidRelease("Missing ZIP content: "+", ".join(sorted(missing)))
        if not any(n.startswith("AuctionHammer/_internal/") for n in names):
            raise InvalidRelease("Missing PyInstaller _internal runtime in ZIP")


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--folder",type=Path,required=True)
    parser.add_argument("--zip",dest="zip_file",type=Path,required=True)
    args=parser.parse_args()
    verify_folder(args.folder)
    verify_zip(args.zip_file)
    print("PASS: Windows folder and ZIP include every README image/link, "
          "release docs, EXE, launcher and runtime.")


if __name__=="__main__":
    main()
