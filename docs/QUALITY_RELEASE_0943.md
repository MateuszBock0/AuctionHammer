# AuctionHammer 0.9.43 — Quality & Release

## Cel

Aktualizacja przenośnej wersji Windows przez `URUCHOM_AUCTIONHAMMER.bat`, bez uszkodzenia dotychczasowej gry, bez instalowania Pythona, Gita czy pygame-ce. Zakres 0.9.43 jest techniczny: **bez zmiany reguł, kart, AI, aukcji i balansu**.

## Rzeczywisty stan poprzedniego launchera

W wersji 0.9.42 `tools/portable_launcher.ps1` po pobraniu ZIP kopiował jego zawartość rekurencyjnie do aktywnego katalogu. Błąd w środku pozostawiał niejednorodną instalację; napis „keeping the existing installation” nie gwarantował cofnięcia skopiowanych plików.

## Nowy model instalacji 0.9.43

```text
AuctionHammer/
├── URUCHOM_AUCTIONHAMMER.bat    # obecny punkt wejścia do gry
├── GRAJ_BEZ_INTERNETU.bat       # brak odpytywania GitHub
├── COFNIJ_AKTUALIZACJE.bat      # ręczny rollback
├── tools/portable_launcher.ps1  # stabilny launcher PowerShell 5.1
├── AuctionHammer.exe            # stary EXE, zachowany jako fallback (opcjonalny)
├── _internal/                   # stary runtime, nienaruszany (opcjonalny)
├── ACTIVE_RELEASE.txt           # atomowo podmieniany znacznik
├── PREVIOUS_RELEASE.txt         # opcjonalny poprzedni znacznik
└── .auctionhammer-versions/
    ├── build-xxxxxxxx/
    │   ├── AuctionHammer.exe
    │   ├── _internal/
    │   ├── BUILD_VERSION.txt
    │   └── ...
    └── build-yyyyyyyy/
```

1. BAT uruchamia PowerShell z katalogu `tools/`. Po sprawdzeniu API `releases/latest` pobierane są **dwa** załączniki: `AuctionHammer-Windows.zip` i `AuctionHammer-Windows.zip.sha256`.
2. Sumę SHA-256 rzeczywistego pliku liczy lokalnie `Get-FileHash`. Jeżeli brakuje SHA lub jest niezgodna, update nie uruchamia instalacji; lokalna gra jest nadal dostępna.
3. Rozpakowanie do osobnego katalogu tymczasowego na **tym samym dysku**, walidacja bezpiecznej ścieżki ZIP i wymaganych plików (`AuctionHammer.exe`, `_internal/`, `VERSION.json`, `BUILD_VERSION.txt`, launcher).
4. Po poprawnej walidacji zmiana nazwy katalogu na `.auctionhammer-versions/build-xxxxxxxx/`.
5. Dopiero wtedy zapisywany jest `PREVIOUS_RELEASE.txt` i atomowo wymieniany `ACTIVE_RELEASE.txt` (Windows `File.Replace` z plikiem backupu; nie kasujemy starego wskazania przed zapisem). Jeżeli krok zawiedzie, poprzednia instalacja nadal działa.
6. Uruchamiany jest EXE z wybranego katalogu, **nie** mieszanka częściowo skopiowanych plików. Starsze wersje pozostają na dysku na potrzeby rollbacku.

Przy braku internetu lub błędach sieciowych launcher uruchamia dotychczas poprawnie zainstalowany EXE. Dane partii pozostają w `%LOCALAPPDATA%\AuctionHammer\` i **nie są kopiowane ani usuwane**. Aktualizator nie czyści też `.git`, `.venv`, projektowych plików użytkownika czy prywatnych dokumentów.

### Jak cofnąć aktualizację?

W folderze gry kliknąć `COFNIJ_AKTUALIZACJE.bat` albo uruchomić:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools\portable_launcher.ps1" -Rollback
```

`-Rollback` przełącza aktywne wydanie na poprzednią **zweryfikowaną lokalną wersję**. Nie cofa ani nie usuwa bieżącego zapisu gry.

### Jak uruchomić offline?

`GRAJ_BEZ_INTERNETU.bat` używa opcji `-SkipUpdate`. Nie wysyła zapytań HTTP, nie pobiera ZIP i korzysta z ostatniej sprawnej lokalnej wersji, z fallbackiem na stary główny EXE.

### Ważna uwaga przy migracji ze starszego launchera

**BAT 0.9.42 i starszy nadal uruchamia stary `tools/portable_launcher.ps1`, który aktualizował pliki bezpośrednio w katalogu.** Nie można nadpisać istniejącego skryptu w komputerze użytkownika przez zmianę repozytorium. Żeby uniknąć ryzyka pierwszej migracji, należy **raz pobrać pełny ZIP 0.9.43, rozpakować go do nowego folderu i tam kliknąć `URUCHOM_AUCTIONHAMMER.bat`**. Kolejne aktualizacje z tego folderu są już wersjonowane i zabezpieczone.

## Automatyczne testy (Windows PowerShell 5.1)

`tests/windows/test_portable_launcher_0943.ps1` używa syntetycznych wydań i izolowanych katalogów. Obejmuje:

- pierwszą instalację bez naruszenia dawnego EXE;
- instalację nowej wersji obok poprzedniej i zmianę znacznika;
- symulowane przerwanie po walidacji przed aktywacją;
- uszkodzone pobranie (SHA-256 mismatch);
- niewłaściwe archiwum z poprawnym SHA (struktura ZIP);
- paczkę niekompletną, bez EXE;
- tryb bez internetu;
- ręczny rollback w obie strony;
- brak działającej gry w folderze źródłowym;
- błąd zapisu lub brak dostępu do katalogu instalacji;
- zachowanie pliku użytkownika i starego EXE.

Workflow `.github/workflows/quality-release-0943.yml` uruchamia te testy na `windows-latest` i pełną regresję Pythona/pygame-ce. Właściwy workflow `windows-portable.yml` dodatkowo buduje ZIP i publikuje jego SHA-256. Status PASS musi zostać potwierdzony w GitHub Actions.

## Kontrola fizycznego Windows — NOT TESTED automatycznie

Do końcowego odbioru na komputerze użytkownika:

- rzeczywiste Windows 10/11: ekran 1366×768 i Full HD, DPI 100/125/150%;
- `URUCHOM_AUCTIONHAMMER.bat` po pierwszej pełnej instalacji oraz ponownym uruchomieniu;
- `GRAJ_BEZ_INTERNETU.bat` po wyłączeniu sieci;
- `COFNIJ_AKTUALIZACJE.bat` po skutecznej aktualizacji;
- realny fullscreen F11, najeżdżanie myszką na kartę/statusy, przeciąganie kart, dźwięk;
- zapis/wczytanie meczu i historia po aktualizacji/rollbacku;
- działanie antywirusa i Windows SmartScreen, jeśli ostrzega przed nowym niezaufanym EXE.

Nie deklarujemy takiego fizycznego odbioru jako PASS bez testu na prawdziwym komputerze z ekranem. Prawa do dystrybucji muzyki nadal wymagają osobnego potwierdzenia (issue #56).
