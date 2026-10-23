# AuctionHammer 0.9.61 — Chorąży Zawsze Zdąży (oprawa graficzna)

## Zakres

Trzy zatwierdzone obrazy 2D przedstawiające tego samego młodego chorążego ze
sztandarem oraz osobna kwadratowa ikona powstały dla gry AuctionHammer.
**„Chorąży Zawsze Zdąży” jest nazwą serii ilustracji**, a nie nową kartą.

W obecnym katalogu Game Master v19 istnieje **S34 — Chorąży Królewskiej Kompanii**.
To właśnie tej karcie przypisano grafiki; jej nazwa, ID, zdolność, statystyki
i kolejka zdarzeń nie zostały zmienione.

## Mapowanie, bez wprowadzania nowej rzadkości

| Istniejący poziom zdolności `card.ability_level` | Portret |
|---|---|
| 0 | `assets/cards/chorazy.png` |
| 1 | `assets/cards/chorazy_rzadka.png` |
| 2 lub więcej | `assets/cards/chorazy_legendarna.png` |

Poziom powstaje dokładnie tak jak wcześniej, tj. `hand_turns // 3`.
Po wystawieniu jednostki nie zmieniamy poziomu ani mechaniki: wygląd
wyświetlany na planszy, w ręce i w podglądzie odpowiada temu samemu stanowi
`Card`. Wszystkie trzy pliki są PNG RGBA **96×96**, przycięte z zatwierdzonych
przez użytkownika portretów 1254×1254, z kadrem pokazującym twarz,
sztandar i charakterystyczną zbroję.

## Ikona

- `assets/branding/chorazy_zawsze_zdazy_icon.png` — **128×128 RGBA**,
  portret do paska okna Pygame oraz podglądu w repozytorium.
- `assets/branding/chorazy_zawsze_zdazy.ico` — wielorozdzielcza ikona
  Windows (16, 24, 32, 48, 64, 96, 128, 256 px).
- Workflow budujący Windows podaje `--icon` do PyInstaller, natomiast
  `SoloApp` ładuje PNG przez `pygame.display.set_icon`. W środowisku
  deweloperskim brak PNG nie powoduje błędu uruchomienia.

## Integralność i odbiór

Komplet pięciu plików jest wyszczególniony z sumami SHA-256 w
`assets/branding/manifest.json`. Test
`tests/test_chorazy_art_0961.py` potwierdza integralność, format PNG,
odrębność trzech obrazów, przypisanie progów `0/1/2+`,
render w ręce i na planszy oraz wczytywanie ikony.

W pakiecie Windows uruchomić nowy build i sprawdzić: widoczność
trzech etapów grafiki po wzroście poziomu, spójność ikon w oknie i pliku
EXE, czytelność karty przy skalowaniu DPI 100%, 125% i 150%.

**Nie zmieniono** katalogu 70 kart, aukcyjnego katalogu 17 archetypów,
statystyk, ataków, zdolności, ekonomii, balansu, AI, RNG, logiki zapisu
ani schematu i weryfikacji audytu.

## Źródła

Grafiki źródłowe wygenerowane i zaakceptowane w rozmowie 23.10.2026.
Repozytorium przechowuje **zasoby runtime**; większe źródła 1254×1254
nie są potrzebne do pakietu Windows. Obrazy zoptymalizowano do
docelowych wymiarów z zachowaniem kanału alfa.
