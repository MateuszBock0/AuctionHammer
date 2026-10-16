# AuctionHammer — master folder i wersja portable Windows

Tu znajduje się **cała gra i jej kod źródłowy**: solo vs komputer, 70 kart startowych (po jednej kopii każdego typu), Game Master v17. **Brak aukcji, kart aukcyjnych i kosztów wystawiania kart.**

## Chcę tylko grać — nowy komputer Windows 10/11

1. Pobierz **[AuctionHammer-Windows.zip z najnowszego wydania](https://github.com/MateuszBock0/AuctionHammer/releases/latest/download/AuctionHammer-Windows.zip)**.
2. Rozpakuj archiwum do jednego folderu **`AuctionHammer`** (nie uruchamiaj EXE wewnątrz ZIP).
3. Uruchom **`URUCHOM_AUCTIONHAMMER.bat`** albo bez internetu **`GRAJ_BEZ_INTERNETU.bat`**.

Pobrałeś kompletny folder z `AuctionHammer.exe`, `_internal/` i kodem źródłowym. **Nie trzeba instalować Pythona, pygame-ce, pip, Git, VS Code ani używać terminala.** Dostęp do GitHub potrzebny jest tylko do pobrania/aktualizacji; offline gra nadal działa. Połączenie z internetem nie jest potrzebne do samej rozgrywki.

## Pierwsze uruchomienie projektu źródłowego (repozytorium jest jeszcze puste)

Jeśli masz ZIP ze **źródłami bez EXE**, rozpakuj go do folderu `AuctionHammer`, a następnie uruchom **`OPUBLIKUJ_NA_GITHUB.bat`**. Skrypt korzysta z Gita już obecnego na komputerze, pobiera bieżące repozytorium, przekazuje komplet źródeł i otwiera GitHub Actions. Może być potrzebna jednorazowa autoryzacja konta w oknie Git Credential Manager. Nie potrzeba do tego Python ani pip.

Po zielonym zakończeniu workflow pobierz `AuctionHammer-Windows.zip` z zakładki **[Releases](https://github.com/MateuszBock0/AuctionHammer/releases/latest)**. Jeśli działania GitHub Actions są wyłączone, włącz je w ustawieniach repozytorium.

## Edycja kodu w VS Code

W folderze `AuctionHammer` masz `game/`, `data/`, `docs/` i `tests/`. Otwórz `AuctionHammer` przez `OTWORZ_W_VS_CODE.bat` albo File → Open Folder. Gra przez EXE nie potrzebuje interpretera; debugowanie źródeł w VS Code wymaga Pythona i pygame-ce. Do aktualizowania źródeł służy GitHub i Git.

## Pliki startowe

- `URUCHOM_AUCTIONHAMMER.bat` — sprawdza nowe wydanie GitHub, następnie uruchamia EXE; offline używa posiadanej wersji.
- `GRAJ_BEZ_INTERNETU.bat` — natychmiast uruchamia lokalne EXE.
- `OPUBLIKUJ_NA_GITHUB.bat` — jednorazowe wysłanie folderu źródeł do repozytorium; wymaga Gita.
- `OTWORZ_W_VS_CODE.bat` — otwiera kod do edycji.
- `START_DEVELOPER.bat` — alternatywny rozruch przez Pythona dla programisty.
- `AUCTIONHAMMER_MASTER.md` — dokument źródłowy projektu i specyfikacja zasad.

## Testy i ograniczenia

CI uruchamia wszystkie testy na Windows przed budową. Wersja prototypowa nadal wymaga walidacji złożonych łańcuchów zdarzeń przeciw Game Master v17. Publikacja Release wymaga, żeby GitHub Actions miał prawo zapisu `contents: write` (workflow ustawia wymagane uprawnienie).

## GitHub

[MateuszBock0/AuctionHammer](https://github.com/MateuszBock0/AuctionHammer) — repozytorium publiczne. Nie dodawaj do niego prywatnych danych, haseł ani tokenów. Wersję wyłącznie dla własnego użytku można zmienić na prywatną w ustawieniach repozytorium, ale wtedy bezpośrednie pobieranie wydań wymaga logowania.
