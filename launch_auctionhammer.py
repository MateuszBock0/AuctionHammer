#!/usr/bin/env python3
"""AuctionHammer: znajdź projekt w profilu Windows, zaktualizuj Git, uruchom grę.

Komendy:
  py launch_auctionhammer.py                # aktualizuj (bezpiecznie) i uruchom
  py launch_auctionhammer.py --list         # znajdź wszystkie instalacje
  py launch_auctionhammer.py --check-only   # sprawdź GitHub, bez zmian i bez gry
  py launch_auctionhammer.py --no-update    # uruchom bez sprawdzania internetu
  py launch_auctionhammer.py --project C:\\...\\AuctionHammer

Nie aktualizuje innych aplikacji ani katalogów spoza rozpoznanego projektu.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

APP_NAME = "AuctionHammer"
SKIP_NAMES = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    "appdata", "$recycle.bin", "windows", "program files", "program files (x86)",
    ".cache", ".npm", ".rustup", ".cargo", ".vscode", "site-packages",
    "temp", "tmp", "dist", "build", "unity", ".next", ".nuget",
}
MAX_FOLDERS = 12000
MAX_DEPTH = 6


def is_game_dir(path: Path) -> bool:
    return (
        path.name.lower() == APP_NAME.lower()
        and (path / "game" / "main.py").is_file()
        and (path / "data" / "cards_base_70.json").is_file()
        and (path / "requirements.txt").is_file()
    )


def discovery_roots(home: Path) -> list[Path]:
    roots = [home / "Desktop", home / "Documents", home / "Downloads",
             home / "Projects", home / "dev", home / "source", home / "OneDrive"]
    onedrive = os.environ.get("OneDrive")
    if onedrive:
        roots.append(Path(onedrive))
    return list(dict.fromkeys(r for r in roots if r.is_dir()))


def find_projects(home: Path, extra_root: Path | None = None) -> list[Path]:
    """Szukaj tylko AuctionHammer; ogranicz głębokość i omijaj katalogi systemowe."""
    roots = discovery_roots(home)
    if extra_root is not None:
        roots.insert(0, extra_root)
    found: dict[str, Path] = {}
    visited = 0
    for root in roots:
        if is_game_dir(root):
            p = root.resolve()
            found[str(p).casefold()] = p
        for dirpath, dirnames, _ in os.walk(root, topdown=True, followlinks=False):
            visited += 1
            if visited > MAX_FOLDERS:
                print("Uwaga: osiągnięto limit skanowania; podaj --project dla dokładnej ścieżki.")
                return sorted(found.values(), key=lambda p: str(p).casefold())
            folder = Path(dirpath)
            depth = len(folder.relative_to(root).parts)
            if depth >= MAX_DEPTH:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d.casefold() not in SKIP_NAMES]
            if folder.name.lower() == APP_NAME.lower():
                if is_game_dir(folder):
                    p = folder.resolve()
                    found[str(p).casefold()] = p
                # Nie szukaj zagnieżdżonej drugiej kopii w środku projektu.
                dirnames[:] = []
    return sorted(found.values(), key=lambda p: str(p).casefold())


def find_git() -> str | None:
    found = shutil.which("git")
    if found:
        return found
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/cmd/git.exe",
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/git.exe",
            Path("C:/Program Files/Git/cmd/git.exe"),
        ]
        for c in candidates:
            if c.is_file():
                return str(c)
    return None


def run_git(git: str, project: Path, *args: str, timeout: int = 75) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [git, "-C", str(project), *args], capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess([], 124, "", "Przekroczono limit czasu")
    except OSError as exc:
        return subprocess.CompletedProcess([], 126, "", str(exc))


def git_ok(git: str, project: Path, *args: str) -> str | None:
    result = run_git(git, project, *args)
    return result.stdout.strip() if result.returncode == 0 else None


def has_origin(git: str, project: Path) -> bool:
    return git_ok(git, project, "remote", "get-url", "origin") is not None


def is_git_project(git: str, project: Path) -> bool:
    toplevel = git_ok(git, project, "rev-parse", "--show-toplevel")
    if not toplevel:
        return False
    try:
        return Path(toplevel).resolve() == project.resolve()
    except OSError:
        return False


def choose_project(projects: list[Path], script_dir: Path, git: str | None) -> Path | None:
    if not projects:
        return None
    if script_dir in projects:
        return script_dir
    # Preferuj repozytorium z origin, a nie starszą kopię z rozpakowanego ZIP-a.
    if git:
        tracked = [p for p in projects if is_git_project(git, p) and has_origin(git, p)]
        if tracked:
            return tracked[0]
    return projects[0]


def check_update(git: str | None, project: Path, check_only: bool) -> bool:
    """Zwróć True wyłącznie jeśli potwierdzono zgodność z gałęzią zdalną.

    Nigdy nie stosuj reset --hard, stash, rebase, force ani nadpisania lokalnych zmian.
    """
    if not git:
        print("[Git] Git nie jest dostępny w PATH. Pomijam sprawdzenie aktualizacji.")
        return False
    if not is_git_project(git, project):
        print("[Git] Ten folder nie jest repozytorium Git. Gra pozostaje lokalna.")
        print("      Instrukcja jednorazowego podłączenia: docs/GIT_WORKFLOW.md")
        return False
    if not has_origin(git, project):
        print("[Git] Brakuje origin (adresu repozytorium na GitHubie).")
        print("      Po utworzeniu repozytorium: git remote add origin ADRES_REPO")
        return False
    branch = git_ok(git, project, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch:
        print("[Git] Jesteś w detached HEAD; aktualizacja wymaga zwykłej gałęzi.")
        return False
    remote = git_ok(git, project, "remote", "get-url", "origin")
    print(f"[Git] Źródło aktualizacji: {remote}")
    print(f"[Git] Lokalna gałąź: {branch}")
    fetching = run_git(git, project, "fetch", "--prune", "origin", timeout=90)
    if fetching.returncode != 0:
        print("[Git] Nie można sprawdzić GitHuba (sieć/logowanie/uprawnienia).")
        print("      ", (fetching.stderr or "").strip()[:500])
        return False

    upstream = git_ok(git, project, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if not upstream or not upstream.startswith("origin/"):
        upstream = f"origin/{branch}"
    remote_sha = git_ok(git, project, "rev-parse", "--verify", f"refs/remotes/{upstream}")
    if remote_sha is None:
        print(f"[Git] Brak zdalnej gałęzi {upstream}; nie zgaduję, z czego aktualizować.")
        print("      Sprawdź, czy wypchnąłeś swoją lokalną gałąź: git push -u origin main")
        return False
    local_sha = git_ok(git, project, "rev-parse", "HEAD")
    if not local_sha:
        print("[Git] Brak lokalnego commita. Najpierw wykonaj git add / git commit.")
        return False
    delta = git_ok(git, project, "rev-list", "--left-right", "--count", f"HEAD...{upstream}")
    try:
        ahead, behind = [int(x) for x in (delta or "").split()]
    except (ValueError, TypeError):
        print("[Git] Nie można porównać historii commitów.")
        return False
    print(f"[Git] Lokalny commit: {local_sha[:10]} | online: {remote_sha[:10]}")
    if ahead and behind:
        print(f"[Git] Rozbieżna historia ({ahead} lokalnych, {behind} zdalnych commitów).")
        print("      Niczego nie nadpisuję. Rozwiąż konflikt ręcznie w Git Bash / VS Code.")
        return False
    if ahead:
        print(f"[Git] Masz {ahead} lokalnych commitów, których jeszcze nie ma na GitHubie.")
        print("      Aby zsynchronizować repozytorium: git push")
        return False
    if behind == 0:
        print("[Git] Masz najnowszą wersję gałęzi z GitHuba.")
        return True
    print(f"[Git] Dostępnych jest {behind} nowszych commitów.")
    if check_only:
        print("[Git] Tryb --check-only: nie pobieram zmian do plików roboczych.")
        return False
    status = git_ok(git, project, "status", "--porcelain", "--untracked-files=normal")
    if status is None:
        print("[Git] Nie można sprawdzić zmian lokalnych. Pomijam aktualizację.")
        return False
    if status:
        print("[Git] Lokalne zmiany lub nieśledzone pliki: NIE aktualizuję, aby ich nie nadpisać.")
        print("      Zapisz zmiany w commicie lub świadomie przenieś je przed aktualizacją.")
        return False
    merging = run_git(git, project, "merge", "--ff-only", upstream, timeout=90)
    if merging.returncode != 0:
        print("[Git] Aktualizacja nie powiodła się; stan lokalny został zachowany.")
        print("      ", (merging.stderr or merging.stdout).strip()[:500])
        return False
    print("[Git] Aktualizacja zakończona, tylko zmienione pliki/obiekty.")
    return True



def pygame_ready(executable: Path) -> bool:
    """Check pygame-ce itself without pip or Internet; ignore missing/broken Pythons."""
    if not executable.is_file():
        return False
    check = (
        "import importlib.metadata as md; "
        "v = md.version('pygame-ce'); "
        "parts = v.split('.'); "
        "assert len(parts) >= 2 and (2, 5) <= (int(parts[0]), int(parts[1])) < (3, 0); "
        "import pygame"
    )
    try:
        result = subprocess.run(
            [str(executable), '-c', check], capture_output=True,
            text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def prepare_python(project: Path) -> Path:
    """Prefer any verified local pygame-ce install; use pip only as last resort.

    This supports an older .venv in the user profile, used before the project
    was recreated. No Internet or new installation is necessary in that case.
    """
    venv = project / '.venv'
    target = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    req = project / 'requirements.txt'
    stamp = venv / '.auctionhammer_requirements.sha256'
    digest = hashlib.sha256(req.read_bytes()).hexdigest() if req.is_file() else None
    # Current MVP only requires pygame-ce; if other packages are introduced,
    # use the installation stamp instead of claiming all deps are satisfied.
    known_single_requirement = bool(req.is_file() and
        req.read_text(encoding='utf-8').strip().replace(' ', '')
        == 'pygame-ce>=2.5.0,<3')

    home = Path(os.environ.get('USERPROFILE', str(Path.home())))
    external = home / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    candidates = [target]
    setting = os.environ.get('AUCTIONHAMMER_PYTHON')
    if setting:
        candidates.append(Path(setting).expanduser())
    candidates.extend([Path(sys.executable), external])
    checked: set[str] = set()
    for candidate in candidates:
        identity = str(candidate).casefold()
        if identity in checked:
            continue
        checked.add(identity)
        if not candidate.is_file():
            continue
        # Recognize existing installation even if old launcher never wrote a stamp.
        if not pygame_ready(candidate):
            continue
        if not known_single_requirement and digest is not None:
            if not stamp.is_file() or stamp.read_text(encoding='utf-8').strip() != digest:
                continue
        print(f'[Python] Znalazłem działające pygame-ce: {candidate}')
        if candidate != target:
            print('[Python] Używam istniejącej instalacji, bez pobierania z Internetu.')
        elif digest is not None and not stamp.is_file():
            stamp.write_text(digest + '\n', encoding='utf-8')
        return candidate

    # No compatible install was found. Only now is a network pip install needed.
    if not target.is_file():
        print('[Python] Tworzę środowisko .venv w katalogu projektu...')
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True, cwd=project)
    if req.is_file():
        print('[Python] Nie znaleziono pygame-ce lokalnie. Próbuję instalacji...')
        print('[Python] Jeśli pojawi się błąd pypi.org, sprawdź Internet/DNS.')
        try:
            subprocess.run(
                [str(target), '-m', 'pip', 'install', '--retries', '0',
                 '--timeout', '8', '--disable-pip-version-check', '-r', str(req)],
                check=True, cwd=project, timeout=90,
            )
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(
                'Nie mogę zainstalować pygame-ce: brak dostępu do pypi.org '
                'lub inny błąd pip. Możesz użyć wcześniejszego środowiska '
                'wcześniejszego środowiska użytkownika albo przywrócić Internet.'
            ) from exc
        if digest is not None:
            stamp.write_text(digest + '\n', encoding='utf-8')
    if not pygame_ready(target):
        raise RuntimeError('pygame-ce nie działa w przygotowanym środowisku.')
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Znajdź, sprawdź i uruchom AuctionHammer z GitHuba.")
    parser.add_argument("--project", type=Path, help="Dokładna ścieżka do folderu AuctionHammer")
    parser.add_argument("--root", type=Path, help="Dodatkowy katalog do przeszukania")
    parser.add_argument("--list", action="store_true", help="Wypisz wszystkie znalezione instalacje gry")
    parser.add_argument("--check-only", action="store_true", help="Sprawdź GitHub bez modyfikacji i bez uruchamiania")
    parser.add_argument("--no-update", action="store_true", help="Nie łącz się z GitHubem")
    parser.add_argument("--require-latest", action="store_true", help="Nie uruchamiaj, jeśli nie udało się potwierdzić aktualnej wersji")
    args = parser.parse_args()
    home = Path(os.environ.get("USERPROFILE", str(Path.home()))).expanduser().resolve()
    script_dir = Path(__file__).resolve().parent
    git = find_git()
    if args.project is not None:
        selected = args.project.expanduser().resolve()
        if not is_game_dir(selected):
            print(f"[BŁĄD] Nie znaleziono poprawnego folderu AuctionHammer: {selected}")
            return 2
        projects = [selected]
    else:
        projects = find_projects(home, args.root.expanduser().resolve() if args.root else None)
        if is_game_dir(script_dir) and script_dir not in projects:
            projects.append(script_dir)
        selected = choose_project(projects, script_dir, git)
    if not projects or selected is None:
        print("[BŁĄD] Nie znaleziono AuctionHammer w profilu użytkownika.")
        print("       Umieść launcher w folderze gry lub użyj --project C:\\...\\AuctionHammer")
        return 2
    print("Znalezione instalacje AuctionHammer:")
    for p in projects:
        print(f" {'*' if p == selected else '-'} {p}")
    if args.list:
        return 0
    print(f"Wybrano: {selected}")
    fresh = False
    if not args.no_update:
        fresh = check_update(git, selected, args.check_only)
    else:
        print("[Git] Kontrola aktualizacji wyłączona (--no-update).")
    if args.check_only:
        return 0
    if args.require_latest and not fresh:
        print("[BŁĄD] Nie można potwierdzić najnowszej wersji. Nie uruchamiam gry.")
        return 3
    if not fresh and not args.no_update:
        print("[Uwaga] Uruchamiam wersję lokalną. Jej aktualność nie została potwierdzona.")
    try:
        python_exe = prepare_python(selected)
    except (RuntimeError, subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"[BŁĄD] Nie udało się przygotować Pythona: {exc}")
        return 4
    print("[Gra] Uruchamiam AuctionHammer...")
    try:
        return subprocess.call([str(python_exe), str(selected / "game" / "main.py")], cwd=selected)
    except OSError as exc:
        print(f"[BŁĄD] Nie udało się uruchomić gry: {exc}")
        return 5


if __name__ == "__main__":
    sys.exit(main())
