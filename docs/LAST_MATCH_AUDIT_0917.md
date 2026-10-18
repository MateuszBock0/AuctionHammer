# AuctionHammer 0.9.17 — audyt OSTATNIEJ ukończonej partii

## Jak udostępnić raport po meczu

1. Rozegraj mecz do ekranu **ZWYCIĘSTWO / PORAŻKA**.
2. Gra sama zapisze kompletny audyt w jednym pliku:

   `%LOCALAPPDATA%\\AuctionHammer\\AuctionHammer-OSTATNI-MECZ.json`

   Na Windows folder można otworzyć skrótem **O** lub przyciskiem
   **OTWÓRZ FOLDER** na ekranie końcowym. Przycisk **EKSPORT AUDYTU [E]**
   pozwala ponowić zapis ręcznie.
3. Przeciągnij plik **AuctionHammer-OSTATNI-MECZ.json** do rozmowy ChatGPT.
   Wystarczy ten jeden plik: nie trzeba robić zrzutów ani eksportować
   `savegame_v19.json`.
4. Po zakończeniu **kolejnego** meczu ten sam plik zostanie zastąpiony.
   Nie powstaje archiwum wcześniejszych partii. Jeśli chcesz zatrzymać
   konkretny audyt na dłużej, skopiuj go osobno przed kolejnym meczem.

Plik zawiera również ręce i talie obu stron oraz seed RNG, dlatego
**eksport jest dostępny dopiero po zakończeniu meczu**.
Nie wysyłaj tego pliku innym graczom podczas trwania rozgrywki.

## Co jest w raporcie?

- **Seed i początkowy stan gry:** kolejność rozdania, pierwszy gracz,
  monety, ręce, talie i wszystkie 70 instancji kart.
- **Każda komenda silnika:** mulligan (łącznie z zaznaczeniami),
  zagranie, ewentualna wymiana jednostki, atak i cel, koniec tury,
  wybrany wariant zdolności. Także błędne/niedozwolone próby.
- **Wewnętrzna chronologia efektów:** aktywacja zdolności,
  obrażenia, leczenie, nałożenie statusu, trucizny, oczyszczenie,
  rozstrzygnięcie fali śmierci, wejście i zejście jednostek,
  przetworzenie końca/początku tury.
- **Stan obiektów przed i po:** PŻ, ATAK, tarcze, pancerz, statusy
  z czasem/źródłem, pozycje jednostek, karty w rękach, kolejki,
  aktywny wybór, talie, bank, stan RNG (hash) i licznik losowań.
- **Pełny tekstowy dziennik zdarzeń:** bez ograniczenia do ostatnich
  160 wpisów.
- **Audytowalność:** kolejne numery akcji, numery operacji wewnętrznych,
  odniesienia do komunikatów silnika oraz hash SHA-256 stanu
  przed/po każdym poleceniu i suma kontrolna całego raportu.

Rejestrowanie działa w rzeczywistym kliencie gry. Masowe symulacje
Python pozostają lekkie — domyślnie audyt jest dla nich wyłączony.
Wszystkie ślady są tylko obserwacyjne i **nie wpływają na zasady v19**.

## Sprawdzenie integralności i odtworzenie rozgrywki

W folderze projektu:

```powershell
python tools/verify_last_match.py
```

Możesz także podać konkretną ścieżkę:

```powershell
python tools/verify_last_match.py "C:\\Users\\...\\AuctionHammer-OSTATNI-MECZ.json"
```

Skrypt sprawdza sumę SHA-256 raportu, a następnie tworzy nowy silnik
v19 z zapisanym seed i odtwarza **kolejne publiczne komendy**.
Porównuje stan po każdej akcji, cały tekstowy dziennik i wewnętrzną
kolejność efektów. Dzięki temu potrafi wskazać numer pierwszej
niezgodności. Nie używa pickle ani `eval` i nie wykonuje dowolnego
kodu dostarczonego w JSON.

## Granice precyzji i zgodność

Audyt zapisuje migawki przed/po każdej komendzie oraz ślady
wywołań istotnych funkcji silnika wewnątrz jej rozstrzygnięcia.
Daje to wgląd w efekty pośrednie, ale **nie rejestruje każdej
instrukcji Pythona ani każdej klatki animacji Pygame**.
Nie zastępuje to zabezpieczenia przed oszustwem w multiplayerze.

Jeśli wczytasz plik `savegame_v19.json` utworzony przed wersją
0.9.17, gra nie może odtworzyć zdarzeń, których wcześniej nie
zapisano. Taki raport jest oznaczony jako **niepełny od początku**
i nadal może pomóc w diagnostyce dalszej części rozgrywki.

Dziennik audytu ma tylko **jedno miejsce na ostatni ukończony mecz**.
Plik znajduje się poza katalogiem aktualizowanej wersji portable,
więc automat GitHub/BAT go nie nadpisuje podczas instalacji.

Nie zmieniano definicji 70 kart, reguł losowania, balansu, AI,
mechaniki fal śmierci ani kosztów kart. Aukcje nadal nie istnieją
w tym etapie implementacji.
