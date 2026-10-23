# AuctionHammer 0.9.65 — pixel art 70 kart podstawowych

70 oryginalnych kart podstawowych (5 frakcji × 14) ma po dwie ilustracje: portret 295×209 oraz pasek 295×78. 140 osobnych plików w `assets/cards/pixel_art/`, bez tekstów kart i bez ramek. Produkcja oparta na pięciu arkuszach wygenerowanego pixel artu. Obrazy do wydania skompresowano do palet 256-kolorowych; manifest podaje SHA-256 oryginalnych wdrożonych PNG.

W `game/ui/assets.py` obraz z `pixelated=True` jest skalowany nearest-neighbor, natomiast inne ilustracje nadal używają smoothscale. `game/ui/card_view.py` podmienia grafikę każdej z 70 bazowych kart, dobierając pasek dla niskich pól ilustracji (ręka/plansza) i portret w dużym podglądzie; `game/ui/app.py` korzysta z portretu podczas powiększenia [G].

S34 Chorąży Królewskiej Kompanii jest kartą podstawową; specjalna nagroda `SUM_START_GUARD` z trzema ilustracjami rozwoju pozostaje oddzielona. Mechanika walki, kolejka zdarzeń, RNG, AI, aukcje, zapisy, audyty i bilans nie są zmieniane.

**Testy:** `python -m unittest tests.test_base70_pixelart -v` i pełne `python -m unittest discover -s tests -v`; render Pygame; Windows Portable PyInstaller `--add-data "assets;assets"`. Ręczna weryfikacja DPI 100/125/150% pozostaje odrębna od zielonego CI.

**Nie wymaga:** klucza OpenAI API, generowania u użytkownika, ręcznego instalowania grafik lub dodatkowych płatności.
