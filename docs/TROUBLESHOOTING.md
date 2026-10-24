# Pomoc techniczna i FAQ — AuctionHammer

## Gra nie uruchamia się na Windows

1. Pobierz aktualne `AuctionHammer-Windows.zip` wyłącznie z [GitHub Releases](https://github.com/MateuszBock0/AuctionHammer/releases/latest).
2. Rozpakuj **cały** folder `AuctionHammer` przed uruchomieniem. Sam `AuctionHammer.exe` poza folderem nie zawiera wszystkich zależności.
3. Uruchom `AuctionHammer.exe` albo `GRAJ_BEZ_INTERNETU.bat` w tym folderze.
4. Jeśli uruchomienie kończy się błędem, sprawdź `%LOCALAPPDATA%\AuctionHammer\crash_latest.log`. Plik powstaje po nieobsłużonym wyjątku; może nie istnieć przy awarii systemowej przed startem Pythona.
5. Utwórz [zgłoszenie błędu](https://github.com/MateuszBock0/AuctionHammer/issues/new/choose). Dołącz wersję z `VERSION.json`, wersję Windows, kroki odtworzenia i fragment logu bez danych prywatnych.

**Windows SmartScreen / program antywirusowy:** niezależne, niepodpisane wydania EXE mogą wywoływać ostrzeżenia. Sprawdź źródło pobrania i integralność archiwum. Nie wyłączaj globalnie zabezpieczeń systemu tylko po to, aby uruchomić grę.

## Jak sprawdzić, czy ZIP pobrał się poprawnie?

Pobierz obok ZIP-a plik `AuctionHammer-Windows.zip.sha256` z tego samego wydania. Otwórz PowerShell w folderze pobrania:

```powershell
(Get-FileHash .\AuctionHammer-Windows.zip -Algorithm SHA256).Hash.ToLowerInvariant()
Get-Content .\AuctionHammer-Windows.zip.sha256
```

Sześćdziesiąt cztery znaki wyświetlonej sumy powinny odpowiadać wartości z pliku `.sha256`. Jeśli się nie zgadzają, **nie instaluj paczki** i pobierz ją ponownie.

## Czy gra działa bez internetu?

Tak, po pobraniu gry. `GRAJ_BEZ_INTERNETU.bat` nie sprawdza nowych wydań. `URUCHOM_AUCTIONHAMMER.bat` może sprawdzić i zainstalować nowe wydanie; w razie błędu powinien zachować poprzednią działającą instalację.

## Aktualizacja, wersje i cofanie zmian

- Każde wydanie ma numer w `VERSION.json` i odrębny tag w formie `build-<8 znaków SHA>`.
- Aktualizator w wersjach od 0.9.43 instaluje nową paczkę obok wcześniejszej i sprawdza jej SHA-256, zanim ją aktywuje.
- Aby cofnąć aktualizację, użyj `COFNIJ_AKTUALIZACJE.bat` **jeśli** była wcześniej poprawnie zainstalowana inna wersja.
- **Przejście ze starszego launchera (przed 0.9.43):** pobierz nowy ZIP i rozpakuj do nowego folderu. Nie zaczynaj migracji od nadpisywania starych plików.

Dokładniejszy opis techniczny: [Quality & Release](QUALITY_RELEASE_0943.md).

## Gdzie są zapisy?

W folderze `%LOCALAPPDATA%\AuctionHammer\`. Pliki wersji gry i pliki użytkownika znajdują się w różnych lokalizacjach. Aktualizacja nie powinna usuwać zapisów, ale przed eksperymentami z wersjami możesz skopiować folder jako kopię zapasową.

## Sterowanie jest za małe albo coś nachodzi na siebie

Spróbuj trybu pełnoekranowego `F11` lub dopasuj rozmiar okna. Jeśli problem występuje przy DPI 125%/150%, dołącz do zgłoszenia rozdzielczość, ustawioną skalę Windows i zrzut ekranu. Testy automatyczne nie zastępują odbioru na każdym fizycznym monitorze.

## Nie mogę zakończyć tury jednym kliknięciem

Jeżeli możesz jeszcze zagrać kartę albo wykonać legalny atak, gra poprosi o potwierdzenie. Kliknij przycisk ponownie lub naciśnij ponownie `SPACJĘ` w ciągu ok. 4,2 sekundy. Gdy nie ma żadnych dostępnych akcji, wystarczy jedno naciśnięcie. Akcje wymagające rozstrzygnięcia wybranego celu nie mogą być pominięte.

## Jak zgłosić problem?

Użyj [formularza GitHub Issues](https://github.com/MateuszBock0/AuctionHammer/issues/new/choose). Nie publikuj plików zapisów, logów lub ścieżek zawierających dane osobowe, jeśli nie sprawdziłeś ich zawartości.

[Wróć na stronę gry](../README.md) · [Historia zmian](../CHANGELOG.md)
