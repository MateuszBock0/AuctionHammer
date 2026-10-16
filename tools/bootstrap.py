#!/usr/bin/env python3
"""AuctionHammer first-run setup: creates private GitHub repo (via gh CLI) if permitted, starts the game.

Does not erase existing files, use force-push, or store credentials.
Runs normally offline even when GitHub setup is unavailable.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LOGIN = "MateuszBock0"
REPO_NAME = "AuctionHammer"
REMOTE = f"https://github.com/{EXPECTED_LOGIN}/{REPO_NAME}.git"


def exe(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    if os.name != "nt":
        return None
    pf = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    home = Path(os.environ.get("LOCALAPPDATA", str(Path.home()/"AppData/Local")))
    variants = {
        "git": [pf/"Git/cmd/git.exe", pf/"Git/bin/git.exe", home/"Programs/Git/cmd/git.exe"],
        "gh": [pf/"GitHub CLI/gh.exe", home/"Programs/GitHub CLI/gh.exe"],
    }
    return next((str(p) for p in variants.get(name, []) if p.is_file()), None)


def run(args: list[str], *, capture: bool = False, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, check=False, text=True, encoding="utf-8", errors="replace",
                          capture_output=capture, timeout=timeout)


def git_run(git: str, *args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return run([git, *args], capture=capture)


def maybe_install(tool: str, winget_id: str) -> str | None:
    located = exe(tool)
    if located:
        return located
    winget = exe("winget")
    if not winget:
        print(f"[GitHub] Brak {tool}; instalacja automatyczna niedostępna (winget nie znaleziony).")
        return None
    print(f"[GitHub] Instaluję {tool} przez Windows Package Manager ({winget_id})...")
    try:
        outcome = run([winget, "install", "--id", winget_id, "-e", "--source", "winget",
                       "--accept-source-agreements", "--accept-package-agreements"], timeout=500)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[GitHub] Nie udało się automatycznie zainstalować: {exc}")
        return None
    if outcome.returncode:
        print(f"[GitHub] Instalacja {tool} nie zakończyła się powodzeniem ({outcome.returncode}).")
    return exe(tool)


def gh_output(gh: str, *args: str) -> str | None:
    try:
        p = run([gh, *args], capture=True, timeout=90)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def ensure_github() -> None:
    """Runs only if the current project has not yet been connected to origin.
    User authorizes by signing into GitHub through gh CLI; no token is ever handled here.
    """
    git = maybe_install("git", "Git.Git")
    if not git:
        print("[GitHub] Git niedostępny. Gra uruchomi się lokalnie.")
        return

    is_repo = git_run(git, "rev-parse", "--show-toplevel", capture=True)
    if is_repo.returncode == 0:
        try:
            if Path(is_repo.stdout.strip()).resolve() != ROOT.resolve():
                print("[GitHub] Folder jest wewnątrz INNEGO repozytorium; nie zmieniam jego konfiguracji.")
                return
        except OSError:
            return
    else:
        print("[GitHub] Inicjalizuję repozytorium...")
        if git_run(git, "init").returncode:
            print("[GitHub] git init nie powiódł się.")
            return

    old_origin = git_run(git, "remote", "get-url", "origin", capture=True)
    if old_origin.returncode == 0:
        print(f"[GitHub] Repozytorium już jest podłączone: {old_origin.stdout.strip()}")
        return

    gh = maybe_install("gh", "GitHub.cli")
    if not gh:
        print("[GitHub] GitHub CLI nie jest jeszcze dostępne. Gra uruchomi się lokalnie; uruchom ponownie po instalacji.")
        return

    try:
        if run([gh, "auth", "status", "-h", "github.com"], capture=True).returncode:
            print("\n[GitHub] Wymagane jednorazowe logowanie. Postępuj zgodnie z kodem/linkiem w terminalu.")
            result = run([gh, "auth", "login", "--web", "--hostname", "github.com", "--git-protocol", "https"],
                         timeout=900)
            if result.returncode:
                print("[GitHub] Logowanie nie zostało zakończone. Gra ruszy offline.")
                return
        account = gh_output(gh, "api", "user", "--jq", ".login")
        if not account or account.lower() != EXPECTED_LOGIN.lower():
            print(f"[GitHub] Zalecane konto: {EXPECTED_LOGIN}, aktualnie: {account or 'nieustalone'}. Nie publikuję w innym koncie.")
            return

        # Setup git credentials using official GitHub CLI; tokens remain with gh, outside the project.
        run([gh, "auth", "setup-git"], capture=True)
        email = f"112616750+{account}@users.noreply.github.com"
        git_run(git, "config", "--local", "user.name", account)
        git_run(git, "config", "--local", "user.email", email)
        if git_run(git, "add", "-A").returncode:
            print("[GitHub] Nie udało się przygotować commitów; gra ruszy lokalnie.")
            return
        changes = git_run(git, "diff", "--cached", "--quiet")
        if changes.returncode == 1:
            if git_run(git, "commit", "-m", "AuctionHammer: wersja startowa MVP 0.9.2 / Game Master v17").returncode:
                return
        elif changes.returncode:
            print("[GitHub] Nie udało się sprawdzić stanu plików.")
            return
        if git_run(git, "branch", "-M", "main").returncode:
            return

        repo = run([gh, "repo", "view", f"{account}/{REPO_NAME}", "--json", "nameWithOwner"], capture=True)
        if repo.returncode != 0:
            print(f"[GitHub] Tworzę PRYWATNE repozytorium: {account}/{REPO_NAME}")
            created = run([gh, "repo", "create", f"{account}/{REPO_NAME}", "--private",
                           "--source", str(ROOT), "--remote", "origin", "--push"], timeout=180)
            if created.returncode:
                print("[GitHub] Repozytorium nie zostało utworzone/wysłane. Gra nadal działa lokalnie.")
                return
        else:
            print("[GitHub] Repozytorium o tej nazwie już istnieje. Nie nadpisuję istniejącej historii.")
            existing = gh_output(gh, "api", f"repos/{account}/{REPO_NAME}", "--jq", ".size")
            # An existing, populated repo must be reconciled manually to avoid overwriting someone else's work.
            if existing != "0":
                print(f"[GitHub] Istniejące repo nie jest puste (size={existing}). Nie wypycham lokalnych commitów.")
                return
            if git_run(git, "remote", "add", "origin", REMOTE).returncode:
                return
            pushed = git_run(git, "push", "-u", "origin", "main")
            if pushed.returncode:
                print("[GitHub] Wysyłka do pustego repo nie powiodła się.")
                return
        print(f"\n[GitHub] Repozytorium gotowe: https://github.com/{account}/{REPO_NAME}\n")
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[GitHub] Nie udało się zakończyć konfiguracji: {exc}. Gra ruszy lokalnie.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Jednoklikowy start AuctionHammer i konfiguracja prywatnego GitHuba")
    parser.add_argument("--offline", action="store_true", help="Pomiń konfigurację GitHub")
    opts = parser.parse_args()
    if not opts.offline:
        ensure_github()
    print("\n[AuctionHammer] Uruchamiam grę...")
    cmd = [sys.executable, str(ROOT/"launch_auctionhammer.py"), "--project", str(ROOT)]
    if opts.offline:
        cmd.append("--no-update")
    return run(cmd, timeout=60*60*12).returncode


if __name__ == "__main__":
    raise SystemExit(main())
