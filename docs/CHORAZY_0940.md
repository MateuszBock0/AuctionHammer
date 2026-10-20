# AuctionHammer v0.9.40 — Chorąży 3/5 (specyfikacja i odbiór)

Punkt bazowy: `main a84283948f73a3eb6d9b79b428576bd02a017095` (v0.9.39).

## Zatwierdzona zmiana
Nowe mecze uruchamiają `starting_compensation='unit_3_5'`.
Gracz wykonujący **drugi** ruch ma od startu na planszy jednego **Chorążego**, **3 ATK / 5 PŻ**, bez +3 monet.
Dokładny opis karty: **„Chorąży zawsze zdąży.”**.
Zdanie jest flavor textem, nie zdolnością. Zero Prowokacji, Tarczy, Pancerza, Szybkiego ataku i zdolności aktywnych. 
Jednostka zajmuje jedno z pięciu pól, nie atakuje w pierwszej własnej turze, nie występuje w puli 70 kart ani aukcji, po zejściu z planszy znika bez powrotu do talii.

## Migracja bez zmiany historii
- `coins`: nadal **+3 monety**, bez tokena; zachowuje dawne podpisy audytu.
- `unit_5_5`: identyczny Strażnik Drugiego Gracza **5/5** z v0.9.39 (również tekst definicji). 
- `unit_3_5`: nowy Chorąży **3/5**.
- Tokeny wykorzystują historyczne `SUM_START_GUARD`; nie tworzymy nowej karty S34. 
- Oba warianty jednostek używają audytu schema 3 z podpisanym `ruleset_state.starting_compensation`; `verify_replay` odczytuje dokładny tryb.
- Stare zapisy bez pola trybu zachowują domyślne `coins`. Stare dokumenty v0.9.38/39 pozostają dokumentami historycznymi.

## Ryzyko balansu i pomiar
W v0.9.39, w 400 pełnych meczach normalny-normalny (seedy 39000–39399), rozpoczynający wygrał 133/400 (33,25%; 66,75% dla drugiego). Dla wcześniejszych +3 monet w odrębnym eksperymencie v22 było 151/200 (75,5%) pierwszego.
**Nie porównywać tych dwóch niezależnych prób jako sparowanych danych.**
Dokładnie ten sam seed i bot po każdej ze stron musi być wykorzystany dla wszystkich trzech wariantów. Skrypt `tools/balance_ab.py` raportuje Wilson 95%, sparowane przełączenia wyniku i test McNemara; nie zmienia zasad.
Jeśli 3/5 nadal daje wyraźną przewagę którejś stronie, zaproponować alternatywy (2/5, 3/4 lub 4/5) jako hipotezy, lecz **nie wdrażać** bez decyzji właściciela.

## QA
- `python -m unittest discover -s tests -v` (+ `tests/test_chorazy_0940.py`), offscreen Pygame SDL dummy.
- 1000 pełnych meczów i 1000/1000 podpisanych replayów na tym samym SHA (400 normalny-normalny, 300 łatwy-trudny, 300 trudny-łatwy) — `.github/workflows/chorazy-0940.yml`.
- Sparowany eksperyment A/B `coins` / `unit_5_5` / `unit_3_5` z identycznymi seedami, wyniki publikowane jako JSON i CSV.
- Manualnie na Windows: F11, A, H, 1366×768 / Full HD, 100/125/150% DPI, boczny opis i okno I, wczytanie starych zapisów.
- Nie utożsamiać poprawnych replayów z potwierdzeniem balansu AI/PvP.

## Osobne kwestie wydaniowe
Transakcyjny aktualizator z rollbackiem, warunki praw do muzyki i przegląd replayów archiwalnych z menu wymagają osobnych prac. Nie są częścią małej zmiany mechaniki Chorążego.
