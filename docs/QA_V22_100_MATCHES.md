# Weryfikacja pełnych meczów — AuctionHammer v22

## Cel

Wykonać **100 rzeczywistych meczów AI vs AI** w tym samym silniku, z którego korzysta gra Windows: Game Master v19, **aukcje v22 aktywne**, 70 kart bazowych, 17 archetypów aukcyjnych oraz wszystkie realne kolejki i wybory. Raport nie jest statycznym zliczeniem kart ani symulacją uproszczonych zasad.

## Reprodukcja

Z katalogu głównego repozytorium:

```powershell
python tools/simulate_v22.py --games 100 --start-seed 220000 --max-steps 3000 --verify-every 10 --output-dir reports/v22_100
```

Uruchomienie bez argumentów daje ten sam zakres seedów i dwa boty **normalny vs normalny**. Można ustawić `--level-0` i `--level-1` na `łatwy`, `normalny` albo `trudny` oraz zmienić liczbę meczów.

**WAŻNE:** folder wyników jest niezależny od zapisów gracza w `%LOCALAPPDATA%\\AuctionHammer`. Nie korzysta z profilu, zapisów ani archiwów użytkownika.

## Zabezpieczenia

1. Obie strony wysyłają wyłącznie publiczne komendy `Match`, przez tego samego `ComputerOpponent` co w grze; dotyczy to również mulliganu i aukcji.
2. `assert_integrity()` wykonywane jest po **każdej publicznej komendzie**, a dodatkowy strażnik wykrywa brak postępu.
3. Mecz jest niezaliczony, jeśli nie kończy się przed limitem, ma niepoprawnego zwycięzcę lub podczas działania pojawi się wyjątek.
4. Każdy zakończony mecz jest archiwizowany jako pełny `.json.gz` (własny indeks i SHA-256); ostatni pozostaje również czytelnym `.json`.
5. Co dziesiąty mecz oraz ostatni są **odtwarzane od początku** z komend audytu, z weryfikacją stanów i zdarzeń. Parametr `--verify-every 1` sprawdza tym sposobem każde spotkanie.
6. W razie błędu zapisywany jest `failures/seed_<numer>.json` z fazą, turą, stanem i końcowymi zdarzeniami. Proces kończy się niezerowym kodem, ale kontynuuje następne seedy.

## Pliki wynikowe

| Plik | Zawartość |
| --- | --- |
| `raport_100_meczow.json` | Wyniki, fazy, zwycięstwa, seedy, liczba rund, statystyki aukcji, pokrycie archetypów i rzadkości |
| `wyniki_meczow.csv` | Tabela jednego wiersza na mecz, do dalszej analizy |
| `AuctionHammer-OSTATNI-MECZ.json` | Pełny audyt ostatniego meczu |
| `historia_meczow/*.json.gz` | **Wszystkie** zakończone mecze, pełne komendy i zdarzenia |
| `historia_meczow/indeks.json` | Zwięzły indeks audytów |
| `failures/seed_*.json` | Diagnostyka niezakończonych lub błędnych spotkań |

Na GitHubie wyniki są publikowane przez workflow **AuctionHammer - 100 meczow v22 z audytami**, jako artefakt `AuctionHammer-V22-100-Matches`.

## Jak interpretować

Wynik **100/100 zakończonych** i poprawne odtwarzanie sprawdzanych meczów to silny test stabilności na wybranych seedach i przy tej heurystyce AI, **nie dowód pełnej poprawności 51 wariantów**. Raport pokazuje, które archetypy faktycznie zaoferowano/kupiono, nie utożsamia tego z uruchomieniem każdej zdolności. Rozkład zwycięstw może sugerować problemy balansu, ale 100 meczów dwóch identycznych heurystyk nie jest oceną siły człowieka ani testem PvP online.

Nie zaleca się zmiany balansu na podstawie pojedynczej krótkiej próby bez dodatkowych symulacji i testów scenariuszowych.
