# AuctionHammer 0.9.62 — Chorąży „Zawsze zdąży”: poprawne przypisanie i easter egg

## Korekta 0.9.61

Trzy zatwierdzone obrazy serii „Chorąży Zawsze Zdąży” należą do **`SUM_START_GUARD`** (Chorąży 2/5 wybierany jako rekompensata przez gracza zaczynającego jako drugi), a nie do karty bazowej **S34 — Chorąży Królewskiej Kompanii**. Wersja 0.9.61 omyłkowo połączyła je z S34. W 0.9.62 oryginalny portret S34 został przywrócony *dokładnie*, poprzez stary Git blob `3807f79343f1f789a38a4db70f2b5325be89096e` (źródło: `ea0f4b86`), do `assets/cards/chorazy_krolewskiej_kompanii.png`. Mechanika S34 pozostała niezmieniona.

## Ulepszanie przez zabójstwa

W **nowym** meczu z wyborem startowego Chorążego 2/5, bezpośrednie zabójstwo wrogiej jednostki **własnym standardowym atakiem** zwiększa jego **ATK o 1, MAX PŻ o 2 i bieżące PŻ o 2**. Limit: **3 zabójstwa**. Po uzyskaniu trzeciej premii kolejne zabójstwa nie podnoszą statystyk.

| Zabójstwa | Podstawowe ATK / MAX PŻ (bez aur) | Ilustracja |
|---|---|---|
| 0 | 2/5 | `assets/cards/chorazy.png` |
| 1 | 3/7 | `assets/cards/chorazy_rzadka.png` |
| 2 | 4/9 | `assets/cards/chorazy_legendarna.png` |
| 3 lub więcej | 5/11 (limit) | `assets/cards/chorazy_legendarna.png` |

Nie liczą się obrażenia pośrednie, trucizna, zastąpienie jednostki, kontratak, ani atak na bohatera. Jeśli w tym samym starciu Chorąży ginie, nie zostaje uratowany premią. Przywołanego raz startowego Chorążego nie można ponownie umieścić w talii.

## Historia, zasoby i prezentacja

- Trzy odrębne pliki są PNG RGBA **96×96**; manifest pięciu oryginalnych zasobów graficznych i ikon z sumami SHA-256: `assets/branding/manifest.json`.
- Osobna zachowana grafika S34 ma udokumentowany hash Git blob i nie korzysta z trzech wariantów.
- `starter_guard_kill_rule` i `starter_guard_kills` są zapisywane i podpisywane tylko dla **nowych** partii zgodnych z tą regułą. Starsze zapisy/replaye bez znacznika zachowują poprzednie obliczenia.
- Na karcie widoczny jest licznik `ZABÓJSTWA N/3`, a powiększenie [G] korzysta z właściwego obrazka.
- Ikona okna (128×128) i ikona EXE (.ico, wiele rozdzielczości) z wydania 0.9.61 są niezmienione.
- Tło ilustracji: `cfg.PANEL` (`#192431`) w przezroczystych marginesach. Gra nie zmienia danych bazowych katalogu 70 kart ani 17 archetypów aukcyjnych.

Na fizycznym Windows potrzebny jest końcowy przegląd czytelności przy skalach DPI 100%, 125%, 150%.
