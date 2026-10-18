# AuctionHammer 0.9.12 — semantyka informacji na kartach (Game Master v19)

Ta aktualizacja zachowuje Minimal Fantasy, trzy wymiary kart (125×195, 148×220,
255×380), istniejące sterowanie, zasady 70 podstawowych kart oraz brak aukcji.

## Co zmieniono
- `game/ui/card_summary.py`: 70 ręcznie opisanych archetypów, każdy ze
  skrótem i dokładniejszą interpretacją celu oraz warunku. Liczby skalowane są
  obliczane ze stanu bieżącej karty/jednostki.
- Trucizna i ograniczona regeneracja: opis rozróżnia wartość na aktywację,
  liczbę aktywacji oraz łączny bonus poziomu.
- `game/ui/attack_view.py`: niezależne wyliczenie wykorzystanych i pozostałych
  ataków oraz legalności ataku w tej chwili. Tura przeciwnika nie kasuje
  wskaźnika. S79 ma drugi atak warunkowo po pierwszym.
- Zmieniono skróty na kartach, opis w panelu bocznym i podgląd [I].
  Podgląd rozróżnia współczesną interpretację liczbową od oryginalnego
  bazowego brzmienia tekstu z katalogu v19.

## Testy
`python -m unittest discover -s tests -v`

Nowe kontrole obejmują 70/70 rekordów, S02 i szczególne karty v19,
skalowanie, truciznę, regenerację, S79 i licznik podczas tury przeciwnika.
Dotychczasowe testy Pygame zapewniają rysowanie 70 kart w trzech rozmiarach,
strefy, DPI, obsługę kliknięć, statusy i zachowanie silnika.

## Kontrola manualna
Na Windows przy DPI 100%, 125% i 150% obejrzyj trzy wielkości kart,
w szczególności długie polskie teksty po skalowaniu okna na 1366×768 i
1536×864. Nie zakładaj, że poprawny układ logiczny gwarantuje czytelność
dla każdego monitora. Zweryfikuj także S02, S66, S67, S79, S91 oraz
poziomy 0/1/2/3/6/9 tur trzymania na ręce.

## Zakres
Brak jakichkolwiek zmian w `game/core/`, `data/cards_base_70.json`,
parametrach kart, ekonomii, falach zgonów, AI i aukcjach.
