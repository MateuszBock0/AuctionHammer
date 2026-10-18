# AuctionHammer 0.9.15 — audyt i ulepszenie ikon Minimal Fantasy

## Podstawa decyzji

Przesłany `AuctionHammer_Ikony_Minimal_Fantasy_v1(2).zip` jest identyczny
z paczką v1 wcześniej wykorzystaną w wersji 0.9.14. SHA-256 ZIP:
`4859b8652a81e7976a32f5cc7f661665449f0011aea8065638109e47654311d7`.
Pakiet zawiera 35 ikon (14 rodzin zdolności, 16 statusów, 5 frakcji)
w wariantach 64/128/256 px, oryginalnych RGBA.

W 0.9.14 wszystkie 35 symboli trafiły do atlasu 24×24 px o ograniczonej
palecie 24 kolorów. Oryginały zachowują lepsze przejścia tonalne,
szczególnie tarczę, oczyszczanie, regenerację oraz szybki atak.

## Wdrożony kompromis

- Z oryginalnych ikon RGBA 64×64 px przygotowano atlas 7×5 komórek
  **40×40 px**, z paletą **256 kolorów** i kanałem przezroczystości;
  rozmiar pliku to około **29 KB**.
- Nie dołączamy wszystkich 105 plików PNG 64/128/256 do aplikacji,
  ponieważ UI rysuje je głównie w 13–20 px. Duże pliki nie poprawią
  czytelności małego napisu ani nie zwiększą wymiarów kart.
- `game/ui/game_icons.py` odczytuje teraz komórki po 40 px, bez zmiany
  ich kolejności czy kluczy. Zachowano możliwość nadpisania atlasu
  osobnymi PNG i tekstowy fallback, gdy brak zasobu.
- Wymiary kart **125×195, 148×220, 255×380** pozostają niezmienione.
  ATK, PŻ, opisy zdolności, limity ataków i statusy nadal są
  rysowane dynamicznie.
- Bez zmian mechaniki, Game Master v19, AI, ekonomii, aukcji, kosztów
  zagrywania i kolejności zdarzeń.

## Analiza liczbowo-obrazowa

Przy porównywaniu grafiki na jednolitym tle zastosowano MAE
(średnią różnicę bezwzględną między kanałami RGB). W tej samej
próbie 35 ikon po zmniejszeniu do docelowych rozmiarów:

| Źródło | MAE przy 13 px | MAE przy 20 px |
| --- | ---: | ---: |
| Atlas 0.9.14, 24 px/24 kolory | 9.60 | 10.60 |
| Atlas 0.9.15, 40 px/256 kolorów | 2.01 | 2.46 |

Punktem odniesienia są oryginalne pojedyncze ikony PNG 64 px.
To **miara utraty informacji względem oryginałów**, nie metryka
subiektywnej czytelności interfejsu.

## Weryfikacja

`python -m unittest discover -s tests -v`

`python tools/render_minimal_fantasy_preview.py`

Nowe testy sprawdzają 35/35 rzeczywistych ikon w formatach 13 i
20 px, kanał alfa, brak pustych piktogramów, rozdzielenie wariantów
odporności oraz to, że atlas nie cofnął się do 24 kolorów.
Dotychczasowy zestaw nadal sprawdza 70 kart w 3 rozmiarach.

Podgląd z **rzeczywistego Pygame**:
`preview/IKONY_35_WYSOKA_JAKOSC_0915.png`.

DPI 100/125/150% oraz czytelność symboli w oknie o małej
rozdzielczości wymagają końcowej oceny przez użytkownika.
Jeżeli piktogram 13 px pozostaje mało czytelny, rozwiązaniem
będzie redesign jego kształtu/kontrastu albo układu karty,
a nie stosowanie pliku 256 px w tym samym miejscu.
