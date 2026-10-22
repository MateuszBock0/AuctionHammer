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

## Warunek ukończenia i scalenia

**Nie scalać samego kodu bez 51 binarnych plików PNG i manifestu!**
GitHubowe API użyte do aktualizacji tekstu nie przenosi automatycznie
binariów z załącznika rozmowy. PR pozostaje draft, aż binaria zostaną
dodane do tej samej gałęzi i CI potwierdzi zestaw oraz Windows ZIP.
Do chwili potwierdzenia runtime w repo ma tylko fallback, a wersja
`VERSION.json` pozostaje 0.9.56.

Odbiór ręczny Windows 100/125/150% DPI nadal wymaga testu na komputerze.
