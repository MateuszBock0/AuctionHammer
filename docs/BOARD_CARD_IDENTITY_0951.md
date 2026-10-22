# AuctionHammer 0.9.51 — Board & Card Identity

## Nowe partie
- Każda strona ma fizyczne pola 0–4.
- Śmierć, wygnanie i przejęcie zwalniają pole bez przesuwania innych jednostek.
- Kliknięcie lub przeciągnięcie karty z ręki na wolne pole wybiera jego konkretny numer. Wymiana zajmuje dawny slot jednostki.
- Wskrzeszenia, kopie, żołnierze, AI i przejęcia wybierają deterministycznie pierwsze wolne pole, nigdy nie przesuwają innych.
- Zdolność S34 preferuje rzeczywiście sąsiadujące pole z prawej, alternatywnie lewe; osłabia wyłącznie wroga naprzeciw.
- S108 reaguje na jednostkę na przeciwległym slocie; zapamiętuje UID, więc nie reaguje ponownie na ten sam cel.

## Rzadkości
- Podstawowa: subtelny brązowy obrys.
- Rzadka: dwie warstwy srebrno-błękitnej ramy i cztery nity.
- Legendarna: ornamentowana złota rama i dyskretnie rozświetlany klejnot.
- Tylko obwódka — nie zasłania nazw, efektów, statusów, ATK ani PŻ.
- Wizualizacja korzysta z rzeczywistego poziomu rzadkości metadata, który awansuje razem z kartą. W widoku archiwalnym potrafi rozpoznać rzadkość z bieżącego opisu `scaling`.
- Pulsowanie wyłącza globalny przełącznik animacji.

## Wsteczna zgodność
- `Match(fixed_board_slots=False)` zachowuje oryginalną semantykę dla symulacji i starych podpisanych rozgrywek.
- Nowy klient SoloApp włącza `fixed_board_slots=True`.
- Nowe `state_snapshot` zawiera tylko w nowym trybie `board_layout`. Starsze podpisy pozostają niezmienione, zamiast fałszywej migracji.
- `load_match` używa starszej semantyki dla starych plików, w nowych waliduje mapę.
- Ręczny odbiór DPI 100/125/150% pozostaje oddzielnym zadaniem.

## Walidacja
- Testy śmierci, zajmowania slotów, podmiany, przejęcia, wygnania i kopii; S34/S108, replay, save/load i rzadkość w trzech formatach.
- Windows EXE oraz CI i 100 pełnych audytowanych rozgrywek.

## Ostateczna walidacja produkcyjnego trybu pól

Workflow `AuctionHammer - testy` wykonuje dodatkowo `python -m tools.check_fixed_board_0951 --games 20`: 20 pełnych partii AI na stałych polach z rekompensatą startową zgodną z aplikacją, kontrolą integralności po każdej komendzie, osobnym zapisem każdego zakończonego audytu i pełnym podpisanym odtworzeniem. Test UI sprawdza kliknięcie pola nr 5. Legacy testy pozostają oddzielne i nie zastępują tego sprawdzianu.
