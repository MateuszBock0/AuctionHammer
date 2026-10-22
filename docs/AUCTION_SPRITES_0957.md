# AuctionHammer 0.9.57 — 51 aukcyjnych ilustracji (etap integracji)

## Walidacja oryginalnego ZIP (22.10.2026)

Otrzymane `AuctionHammer_51_GRAFIK_DO_GRY_96x96(1).zip` zawiera:
- 51 × `assets/auction/Axxx_{podstawowa,rzadka,legendarna}.png`;
- `manifest.json` (mapowanie i SHA-256);
- `README.md`, `PODGLAD_51_KART.png`.

**Nie ma** w tym konkretnym ZIP katalogów `originals_highres/`,
`previews/` ani `triptychs_sources/`. Jest to odmienny, mniejszy
pakiet niż pierwotnie opisany, ale wystarcza do uruchomienia gry.

Zweryfikowano: 51 rzeczywistych plików, każdy 96×96 RGBA PNG,
17×3 mapowań z manifestu (A001–A016, A018), wszystkie 51 SHA-256 zgodne,
brak zduplikowanych hashy. A017 nie istnieje w aktywnym katalogu v22.

## Integracja z interfejsem

- `ImageAssets.get_auction_image`: wczytanie ściśle po ID i **aktualnej**
  rzadkości, jednorazowo; pamięć podręczna wymiarów i kadrowania.
- `CardView.art(...,rarity=...)`: wspólna ścieżka renderingu kart aukcyjnych
  na ręce, planszy i podczas odtwarzania.
- Okno trzech ofert aukcyjnych: portret obok statystyk.
- Podgląd pełnej zdolności: portret w prawym górnym rogu.
- Duży podgląd [G] ILUSTRACJA: sprite aktualnego wariantu.
- Ramki rzadkości, statusy, ATK, PŻ, teksty i mechanika pozostają bez zmian.
- Brak pliku: stary proceduralny obraz zamiast błędnej grafiki innej rzadkości.

## Bezpieczeństwo instalacji

`python tools/install_auction_sprites_0957.py --zip <ARCHIWUM_Z_GRAFIKAMI>`

Instalator przed kopiowaniem weryfikuje **każdy** plik, jego rozmiar,
nagłówek PNG RGBA, mapowanie ID/rarity i SHA-256 względem manifestu.
Kopiuje wyłącznie zatwierdzone 51 PNG do `assets/auction/`, a manifest
do `assets/auction/manifest.json`. Materiały source/previews nie
są pakowane do runtime.

Ponowna weryfikacja:
`python tools/install_auction_sprites_0957.py --check-installed`.

## Status integracji z GitHubem

Użytkownik dodał komplet 51 PNG i manifest bezpośrednio do `main`
w commicie `84000951`. Gałąź `feature/0957-auction-card-sprites`
została następnie połączona z tym commitem bez nadpisywania binariów.

`VERSION.json` i klient Pygame-ce zostały podniesione do 0.9.57.
Brak nowej mechaniki i zmian do katalogów definicji 70/17 kart.
Warunkiem scalenia są zielone testy Pygame, walidacja 51 SHA-256,
minimum 20 pełnych meczów/replayów i regresje Windows. Po scaleniu
osobny workflow publikuje przenośny ZIP Windows.

Ręczny odbiór wizualny na fizycznym Windows (DPI 100%, 125%, 150%)
pozostaje wymaganym dodatkowym testem po automatycznym CI.
