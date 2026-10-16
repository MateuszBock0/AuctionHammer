# Portable build Windows

Workflow `.github/workflows/windows-portable.yml` builds 64-bit Windows folder with `AuctionHammer.exe` and `_internal/` using PyInstaller on `windows-latest`. Sources are included alongside compiled executable, but no Python installation is needed to play. PyInstaller builds must happen on Windows: no cross-compiled EXE in the source ZIP.

## One-time migration

1. `OPUBLIKUJ_NA_GITHUB.bat` from source folder on PC with Git (Git Bash was previously installed).
2. GitHub Actions builds and publishes Release `AuctionHammer-Windows.zip`.
3. Download ZIP and extract single folder `AuctionHammer`; run `.bat` or `.exe`.

## Later

The launcher checks `releases/latest` via Windows PowerShell, downloads the changed release only if build tag changed, and falls back to local EXE when offline. Source updates in release overwrite corresponding source files, so commit local changes before updating.
