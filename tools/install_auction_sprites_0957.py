"""Strict installer and verifier for the 51 supplied auction sprites.

No network, Pillow or engine mutations. Run from the repository checkout:
  python tools/install_auction_sprites_0957.py --zip path/to/sprites.zip
  python tools/install_auction_sprites_0957.py --check-installed
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import zipfile

from game.core.auction_catalog import V22_CARDS, RARITIES

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
EXPECTED = {
    f"assets/auction/{card_id}_{tier}.png"
    for card_id in V22_CARDS for tier in RARITIES
}


def _verify_png(data: bytes, name: str) -> None:
    if (len(data) < 26 or not data.startswith(PNG_MAGIC)
            or data[12:16] != b"IHDR"):
        raise ValueError(f"Invalid PNG header: {name}")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (96, 96):
        raise ValueError(f"Not a 96x96 sprite: {name}")
    if data[25] != 6:  # PNG color type 6: truecolor with alpha.
        raise ValueError(f"Expected PNG RGBA: {name}")


def validate_manifest(manifest: dict, read_bytes) -> list[str]:
    """Validate EVERY exact manifest mapping against packaged data."""
    rows = manifest.get("assets", ())
    expected_ids = set(V22_CARDS)
    if (len(rows) != 51 or manifest.get("total_images") != 51
            or manifest.get("total_cards") != 17
            or set(manifest.get("card_ids", ())) != expected_ids
            or set(manifest.get("rarities", ())) != set(RARITIES)):
        raise ValueError("Manifest must describe 17 real v22 cards × 3 rarities")
    found = set()
    hashes = set()
    for row in rows:
        card_id, rarity, path = row["id"], row["rarity"], row["target_path"]
        expected = f"assets/auction/{card_id}_{rarity}.png"
        if (path != expected or path not in EXPECTED
                or row.get("filename") != Path(path).name
                or row.get("target_size") != [96, 96]
                or path in found):
            raise ValueError(f"Invalid or duplicate asset mapping: {path}")
        image = read_bytes(path)
        digest = hashlib.sha256(image).hexdigest()
        if digest != row["output_sha256"]:
            raise ValueError(f"SHA-256 mismatch: {path}")
        _verify_png(image, path)
        found.add(path)
        hashes.add(digest)
    if found != EXPECTED or len(hashes) != 51:
        raise ValueError("Missing, extra or duplicated sprite variant")
    return sorted(found)


def validate_zip(filename: Path) -> tuple[dict, list[str]]:
    with zipfile.ZipFile(filename) as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        paths = validate_manifest(manifest, archive.read)
        actual = {p for p in archive.namelist() if p.startswith("assets/auction/") and p.endswith(".png")}
        if actual != EXPECTED:
            raise ValueError("Archive sprite set differs from the manifest")
    return manifest, paths


def validate_installed(repo_root: Path) -> list[str]:
    root = Path(repo_root)
    manifest = json.loads((root / "assets/auction/manifest.json").read_text(encoding="utf-8"))
    return validate_manifest(manifest, lambda name: (root / name).read_bytes())


def install_zip(filename: Path, repo_root: Path) -> list[str]:
    manifest, paths = validate_zip(Path(filename))
    folder = Path(repo_root) / "assets" / "auction"
    folder.mkdir(parents=True, exist_ok=True)
    # Do not touch existing assets until every archive entry has passed checks.
    with tempfile.TemporaryDirectory(prefix=".auction-sprites-", dir=str(folder)) as scratch:
        stage = Path(scratch)
        with zipfile.ZipFile(filename) as archive:
            for relative in paths:
                dest = stage / Path(relative).name
                dest.write_bytes(archive.read(relative))
        manifest_path = stage / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for path in paths:
            os.replace(stage / Path(path).name, folder / Path(path).name)
        os.replace(manifest_path, folder / "manifest.json")
    validate_installed(repo_root)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, help="Uploaded sprite pack")
    parser.add_argument("--project", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check-installed", action="store_true")
    args = parser.parse_args()
    if args.check_installed:
        paths = validate_installed(args.project)
    elif args.zip:
        paths = install_zip(args.zip, args.project)
    else:
        parser.error("Provide --zip or --check-installed")
    print(f"PASS: {len(paths)} PNG 96x96; 17 x 3; all SHA-256 verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
