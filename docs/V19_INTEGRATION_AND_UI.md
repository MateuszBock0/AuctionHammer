# AuctionHammer — wdrożenie zasad Game Master v19 i interfejs kart

**Podstawa zmian:** dostarczone archiwum `GRA_KARCIANA_ONLINE_GAME_MASTER_v19(1).zip`, a w szczególności lista zmian v19, audyt mechanik, katalog 70 kart i referencyjne fragmenty implementacji nadanych zdolności. Moduły referencyjne z archiwum nie są samodzielnym, kompletnym silnikiem. Zasady wdrożono do istniejącej klasy `Match` gry AuctionHammer.

## Zmiany kart zatwierdzone w v19

| Karta | Obowiązujące działanie |
| --- | --- |
| S66 — Mag Migotliwego Kroku | Po wystawieniu wybiera Szybki atak **dla siebie** albo dla **jednej innej konkretnej karty jednostki na ręce**. Wybory się wykluczają. Bonus przypisany karcie na ręce zużywa się przy jej najbliższym wystawieniu |
| S67 — Zaklinacz Podwójnego Uderzenia | Po wystawieniu wybiera siebie lub inną sojuszniczą jednostkę na planszy, aby przyznać jej Podwójny atak. Nie daje trzeciego ataku ani prawa do ataku w turze wystawienia bez Szybkiego ataku |
| S79 — Dwugłowa Hiena | **2 ATAK / 6 PŻ**. Drugi atak jest możliwy dopiero po pierwszym legalnym ataku, jeśli zdolność nie jest zablokowana |
| S114 — Instruktor Błyskawicznego Natarcia | **1 ATAK / 5 PŻ**. Wrodzony Szybki atak działa wyłącznie na tę jednostkę |
| S115 — Mistrz Dwóch Ostrzy | **1 ATAK / 6 PŻ**. Wrodzony Podwójny atak działa wyłącznie na tę jednostkę |

## Utrzymane zmiany wcześniejsze, obowiązujące również w v19

- **S20** — po śmierci daje tarczę i dwa punkty trwałego pancerza innej własnej jednostce albo własnemu bohaterowi, jeśli nie pozostała żadna sojusznicza jednostka.
- **S82** — po śmierci daje sześć punktów trwałego pancerza innej własnej jednostce albo własnemu bohaterowi, jeśli nie pozostała żadna sojusznicza jednostka.
- **S90** — po śmierci wybiera losowo do dwóch *różnych* kart na ręce, którym daje Szybki atak przy najbliższym wystawieniu. Bonusy nie kumulują się.
- **S91** — po śmierci nadaje Podwójny atak innej jednostce na planszy; gdy nie ma takiej jednostki, wybiera losowo jedną kartę na ręce. W wariancie awaryjnym bonus obowiązuje w jej pierwszej własnej turze z możliwością legalnego ataku.
- **S105** — aura nadaje jednorazową pulę pancerza przy objęciu ochroną. Pancerz zużyty przez obrażenia nie odtwarza się przy ponownym przeliczeniu aury.
- **S109** — każdy poziom rozwoju wzmacnia samoleczenie na koniec **każdej własnej tury**.
- **S74, S87, S97, S111** — warunkowe wzmocnienie oczyszczania działa wyłącznie po rzeczywistym usunięciu kwalifikującego się efektu.

Wszystkie 70 kart pozostają unikatowe. Ich statystyki i opisy są przechowywane w `data/cards_base_70.json`. Nie dodano aukcji, kart aukcyjnych ani kosztów wystawiania jednostek.

## Polski interfejs

Obowiązujące nazwy zdolności i efekty są wyświetlane **po polsku**, także na małych kartach. Zamiast angielskich skrótów stosuje się:

| Oznaczenie | Znaczenie |
| --- | --- |
| OBR | Obrażenia |
| LECZ | Leczenie |
| PANC | Pancerz |
| PŻ | Punkty życia |
| TRUC | Trucizna |
| OGŁ | Ogłuszenie |
| PROW | Prowokacja |
| OCZ | Oczyszczanie |
| ODP | Odporność |
| SZYBKI | Szybki atak |
| 2 ATAKI | Podwójny atak |
| ŁĄCZ | Premia do sumarycznego efektu |

Wszystkie karty pokazują swój **moment aktywacji**, rodzinę efektu, wyróżnioną wartość oraz pas rozwoju co trzy własne tury na ręce. Rozszerzony podgląd pogrubia tylko wartość podlegającą skalowaniu. Nie należy pogrubiać czasu ogłuszenia, liczby dozwolonych ataków ani dodatkowo wzmacniać każdej osobnej aktywacji trucizny lub regeneracji.

Wybór celu i wariantu zajmuje odrębny panel. Legalne cele na planszy oraz — w przypadku S66 — na ręce są wyróżnione. Podczas wymiany kart oznaczone egzemplarze mają złote obramowanie i numer wyboru. Rozmiar okna dostosowuje się do ekranu i skalowania obrazu w Windows.

## Źródła zasad i wersjonowanie

`AUCTIONHAMMER_MASTER.md` i `data/GAME_MASTER.json` wskazują aktualną specyfikację **Game Master v19**. `docs/GAME_MASTER_v17.md` i pliki kolejności zdarzeń ze wskazaniem v17 pozostają materiałami historycznymi. Wersja historyczna **nie może nadpisywać** zatwierdzonych zmian katalogu v19.

## Testy i znane ograniczenia

Testy uruchamia się poleceniem `python -m unittest discover -s tests -v`. Testy v19 znajdują się w `tests/test_v19_integration.py`; sprawdzają m.in. wybory S66/S67, powiązanie premii z konkretną kartą, skutki śmierci S20/S82/S90/S91, brak odnawiania pancerza S105, regenerację S109 i rysowanie wszystkich 70 kart.

**Ważne ograniczenie:** silnik w dalszym ciągu wymaga odrębnego audytu grup jednoczesnych zgonów. Testy nie dowodzą pełnej zgodności atomowej kolejki zdarzeń ani zbalansowania wszystkich zestawień kart. Żaden dokument nie powinien przedstawiać tych zagadnień jako zakończonych.

## MVP 0.9.10 — atomowe fale jednoczesnych zgonów

Zaimplementowano wspólne migawki i zbiorowe konsekwencje źródeł „Przy śmierci”. Testy są w `tests/test_death_waves_0910.py`, a opis, ograniczenia i scenariusze w `docs/FALY_ZGONOW_v19_MVP_0910.md`. Obowiązujący dokument kolejności to `data/event_order_v19.json`; starsze dokumenty v17 są archiwalne. Pełna wielofalowa walidacja wszystkich kombinacji kart pozostaje otwarta.
