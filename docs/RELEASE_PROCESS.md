# Wersjonowanie i publikowanie AuctionHammer

Ten dokument dotyczy wydawania wersji gry, a nie zasad samej rozgrywki. Z perspektywy gracza punktem wejścia są [README](../README.md) i [Releases](https://github.com/MateuszBock0/AuctionHammer/releases/latest).

## Dwa niezależne identyfikatory wydania

| Identyfikator | Przykład | Przeznaczenie |
|---|---|---|
| Wersja produktu | `0.9.79` | Czytelna wersja widoczna dla gracza i w changelogu |
| Tag buildu | `build-xxxxxxxx` | Dokładny commit zbudowanej i opublikowanej paczki Windows |

**Jedynym źródłem numeru wersji produktu jest `VERSION.json` → `mvp`.** Z niego synchronizowane są `game/config.py`, README, changelog i treść GitHub Release. Poszczególne tagi `build-...` nie są numerami wersji; mogą istnieć dwa poprawnie zweryfikowane buildy tej samej wersji produktu.

Przed wydaniem 1.0 numeracja `0.9.N` oznacza kolejne etapy MVP, także techniczne lub wyłącznie dokumentacyjne. Nie ma obowiązku wypełniania każdego pośredniego numeru, ale changelog nie powinien udawać, że brakujące wersje zostały opublikowane.

## Aktualizowanie wersji

```bash
# Sprawdza format i spójność wersji, changelog i lokalne linki README
python -m tools.release_meta check

# Gdy planujesz nową wersję, zwiększ numer i edytuj nowy wpis TODO w CHANGELOG
python -m tools.release_meta bump 0.9.80

# Podejrzyj dokładną treść opisu przeznaczonego dla GitHub Releases
python -m tools.release_meta notes

# Uruchom testy
python -m unittest discover -s tests -v
```

Komenda `bump` synchronizuje **`VERSION.json`**, **`game/config.py`**, **`README.md`** i nagłówek wpisu w **`CHANGELOG.md`**. Dopóki wpis pozostaje oznaczony `TODO`, `check` blokuje publikację. Przy zwykłych wewnętrznych commitach wersji nie podnosi się automatycznie.

## Ścieżka wydania

1. Zatwierdź zakres zmiany i jej wpływ na graczy.
2. Przygotuj numer wersji oraz wpis **na samej górze `CHANGELOG.md`**; opisuj faktycznie wdrożone funkcje.
3. Uruchom `python -m tools.release_meta check` i kompletne testy silnika/interfejsu.
4. Otwórz PR; GitHub Actions musi potwierdzić Linux, Windows i testy regresyjne (w tym launcher i audyt, jeśli dotyczą zmian).
5. Po scaleniu na `main` workflow `.github/workflows/windows-portable.yml` uruchamia się automatycznie. Zaczyna od niezależnych bramek Linux i pełnych audytowanych meczów; dopiero po ich sukcesie buduje EXE, weryfikuje kompletność rzeczywistej paczki (folder i ZIP) oraz SHA-256 i testuje instalator/rollback.
6. **Dopiero po pozytywnej walidacji** workflow tworzy/aktualizuje GitHub Release dla taga `build-<8 znaków SHA commita>`, z numerem z `VERSION.json`, notatkami z odpowiedniego wpisu `CHANGELOG.md` oraz plikami `AuctionHammer-Windows.zip` i `AuctionHammer-Windows.zip.sha256`.
7. Sprawdź zakładkę Releases oraz czy oba załączniki rzeczywiście istnieją. Brak taga lub assetów oznacza **brak potwierdzonego wydania** — zielony PR nie gwarantuje udanego ZIP-a.
8. Osobno wykonaj ręczny test na fizycznym Windows: uruchomienie, rozdzielczość/DPI, wczytywanie zapisów, nowy mecz, tryb offline i cofnięcie aktualizacji. **GitHub Actions nie dowodzi przejścia fizycznych testów monitora.**

Nie publikuj samego źródłowego ZIP-a GitHuba jako substytutu pakietu z EXE.

## Warunki dopuszczenia Windows Release (od 0.9.80)

Release nie może rozpocząć budowy ani publikacji przed sukcesem wszystkich **wymaganych bramek tego samego commita**, skonfigurowanych w `.github/workflows/windows-portable.yml`:

- `linux-regressions`: pełne testy automatyczne, render Pygame, 20 pełnych partii na stałych polach z weryfikacją podpisanych replayów i kontrola katalogu 121 opisów kart.
- `forensic-100`: 100 niezależnych, ukończonych partii normal-vs-normal oraz **100/100** ponownie odtworzonych podpisanych historii.
- `signed-cohorts`: trzy kohorty 400/300/300 meczów przy różnych ustawieniach AI; każda partia ma zakończenie i zweryfikowaną powtórkę (**1000/1000**).
- `windows` ma jawne `needs: [linux-regressions, forensic-100, signed-cohorts]`. Każdy FAIL lub anulowanie w dowolnej wymaganej bramce oznacza, że Windows nie przechodzi do tworzenia EXE/Release.

Własne testy joba Windows obejmują regresje, launcher PowerShell, render, PyInstaller, sumę SHA-256, instalację **rzeczywistego ZIP-a** i kontrolę odnośników `README.md` na podstawie *naprawdę zapakowanych plików*, nie tylko zawartości repozytorium. Weryfikator `python -m tools.release_package --folder release/AuctionHammer --zip AuctionHammer-Windows.zip` odrzuca brakujące `CHANGELOG.md`, `CONTRIBUTING.md`, zasoby/ilustracje linkowane z README, launcher i runtime.

Pozostałe historyczne workflow mogą działać niezależnie do analiz. Nie stanowią dodatkowej, niejawnej blokady — komplet wymaganych **testów kwalifikacyjnych wydania** został włączony do workflow publikacyjnego.

## Zgodność zapisów i odtwarzania

Nowe elementy UI z etapów 0.9.71–0.9.78 nie zmieniają zasad ani schematu plików historii. To nie oznacza, że każda dowolna przyszła wersja zachowa identyczną semantykę. Każda zmiana `Match`, katalogu aukcji, losowania lub serializacji wymaga osobnej oceny kompatybilności istniejących zapisów, audytów i replayów.

Dane użytkownika na Windows są przechowywane poza folderem aktualizowanej gry, w `%LOCALAPPDATA%\AuctionHammer\`. Szczegóły zabezpieczeń aktualizatora: [Quality & Release 0.9.43](QUALITY_RELEASE_0943.md).

## Strona GitHub i materiały dla graczy

- `README.md`: krótki opis gry, obrazy, pobieranie i szybki start — **bez kroniki technicznej**.
- `CHANGELOG.md`: pełna lista zmian produktu; źródło opisu wydania.
- `docs/PLAYER_GUIDE.md`: przewodnik pierwszej rozgrywki.
- `docs/TROUBLESHOOTING.md`: pomoc dla graczy i zgłaszanie problemów.
- `docs/DEVELOPMENT.md` i `CONTRIBUTING.md`: materiały dla twórców.
- `docs/STATUS_PROJEKTU.md`: wewnętrzna kronika implementacji i niezamknięte kontrole.

## Uczciwe oznaczanie statusów

| Status | Co faktycznie oznacza |
|---|---|
| PR merged | Kod trafił do gałęzi `main` |
| CI PASS | Automatyczne testy danego commita zakończyły się sukcesem |
| Build tag exists | Wskazany commit ma identyfikator wydania (nie potwierdza kompletności assetów) |
| Release ZIP verified | Workflow sprawdził archiwum i jego SHA-256 oraz zakończył się pozytywnie |
| Manual Windows accepted | Ktoś uruchomił pakiet na fizycznym Windows i udokumentował próbę |

Nie używaj kolejnego statusu jako synonimu poprzedniego.
