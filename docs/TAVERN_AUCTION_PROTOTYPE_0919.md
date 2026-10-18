# AuctionHammer 0.9.19 — karczemne akcenty i pierwszy prototyp aukcji

## Decyzja o paczce Tavern UI Pack v2

Przejrzano `AuctionHammer_Tavern_UI_Pack_v2_Procedure.zip`:
cztery kompletne arkusze PNG plus trzy dokumenty i manifest.
Ocena po obejrzeniu obrazów:

- **Warto wdrożyć** ciepłą fakturę drewnianego stołu i prostą mosiężną
  listwę. Z oryginalnych plików przygotowano dwa małe pliki:
  `assets/ui/tavern/wood_ambient.png` (około 36 KB) i
  `assets/ui/tavern/gold_divider.png` (około 4 KB).
  Są z paczki użytkownika, nie stanowią nowego losowego zestawu grafik.
- **Nie wdrażać bezpośrednio** pełnego, szczegółowego tła karczmy:
  kominek, meble, światła i dekoracje za kartami przeciążyłyby środkowe
  pole bitwy i obniżyły czytelność napisów. Zachowano kamienny, kontrastowy
  motyw 0.9.16 i położono subtelny półprzezroczysty rysunek drewna **pod**
  panelami i kartami.
- **Nie nakładać całych arkuszy paneli i przycisków na hitboxy**:
  mają dekoracje (np. latarnie, grube ramy, flagi) wystające poza bryły.
  Mogłyby nachodzić na karty, opisy i liczniki ATAK/PŻ.
- Drobny mosiężny separator dekoruje teraz tylko ekran aukcji, z dala
  od tekstów i obszarów klikania. Pliki są ładowane offline, z fallbackiem
  na proceduralny motyw, gdy brak grafiki.

Wymiary kart, rozmiar płótna i geometria pól nie uległy zmianom.

## Prototyp aukcji — działa w rozgrywce solo

**UWAGA: to pierwszy etap mechanik aukcyjnych, nie finalny katalog.**
Game Master v19 sekcja 12 definiuje rzeczywiste zasady kolejności,
które są teraz implementowane:

1. Aukcja uruchamia się **po zakończonych rundach 3, 6, 9...**, po
   wypłacie **+1 monety obojgu graczom** i opróżnieniu kolejek.
2. Trzy odrębne oferty to tymczasowe warianty jednostki:
   - Strażnik aukcji **3 PŻ**, **3 ATAK**, **Prowokacja + 1 Tarcza**.
   - Strażnik aukcji **6 PŻ**, **3 ATAK**, **Prowokacja + 1 Tarcza**.
   - Strażnik aukcji **12 PŻ**, **3 ATAK**, **Prowokacja + 1 Tarcza**.
   Te trzy wartości HP nie są trzema dodatkowymi życiami, tylko
   bezpośrednio bazowym zdrowiem otrzymanej jednostki.
3. Każda oferta losuje rzadkość osobno **60% podstawowa / 30% rzadka /
   10% legendarna**. Rzadkość i numer aukcji/poziom są zapamiętywane,
   ale **jeszcze nie zmieniają zdolności ani bazowych statystyk**
   testowego Strażnika.
4. Licytacja jest **bez zegara**: każdy ruch to oferta >= aktualna+1
   w granicach swoich monet albo PAS. Komputer wykonuje własne ruchy.
5. Przy braku płatnej oferty pierwsze darmowe wskazanie przypada
   graczowi zaczynającemu mecz na aukcji 1, przeciwnikowi na aukcji 2,
   itd. Przy płatnej ofercie zwycięzca płaci ustaloną kwotę.
6. Zwycięzca wybiera **pierwszą** kartę, przegrany jedną z dwóch
   pozostałych za darmo. Niewybrany wariant nie trafia do żadnej ręki.
7. Obie karty otrzymuje się na rękę. Mogą przekroczyć 5 sztuk;
   nie skalują się w ręce. Na planszy zachowują ograniczenie
   jednego zagrania na turę, limit 5 jednostek, chorobę przywołania
   i standardowe zasady ataku oraz obrażeń. Prowokacja jest
   **wrodzoną zdolnością**, więc ogłuszenie ją wyłącza, a
   **jednorazowa Tarcza** nakładana jest po wystawieniu.
8. Gra wraca po aukcji do właściwej następnej tury, w szczególności
   nie gubi fazy dobierania ani efektów początku tury.

### Sterowanie

Na ekranie aukcji:
- W licytacji wybierz **PASUJ**, **PODBIJ +1** albo wpisz kwotę
  klawiaturą numeryczną i naciśnij **ENTER / LICYTUJ**.
- W wyborze kliknij jedną z trzech ofert lub naciśnij **1–3**.
- **M** otwiera menu i pozwala zapisać grę nawet w trakcie aukcji.
- AI działa z tymi samymi dopuszczalnymi poleceniami silnika; bez
  samodzielnego manipulowania jego stanem.

### Zachowana zgodność

- Nadal dokładnie **70 unikalnych bazowych kart** i oryginalny bank
  po 1 egzemplarzu. Aukcyjne egzemplarze mają osobne unikalne ID
  `AUC...`; nie uczestniczą w banku mulliganu.
- Brak kosztu zagrywania kart podstawowych i aukcyjnych. Monety
  wydaje się **wyłącznie w licytacji**, nie przy wystawianiu.
- Bez wskrzeszenia, przejmowania, kopiowania, płatnych zdolności,
  procentowych redukcji obrażeń, ciszy ani docelowych 36 archetypów.
  Będą dodane po zatwierdzeniu finalnego katalogu.
- Stare zapisane mecze są zgodne, ale **nie otrzymują nieistniejącej
  wcześniejszej historii aukcji**; pozostają w trybie bez aukcji.
- Nowe zapisane mecze mogą być wznowione w środku licytacji;
  w JSON audytu trafiają wszystkie oferty, płatności, wybory,
  numery aukcji, rzadkości i fizyczne egzemplarze.
- Rozszerzono narzędzie weryfikacji audytu o
  `Match(... auctions_enabled=True)`, żeby przeliczało również
  licytacje w odtwarzanej partii.

## Weryfikacja

```powershell
python -m unittest discover -s tests -v
python tools/render_minimal_fantasy_preview.py
```

Najważniejsze zrzuty rzeczywistego Pygame:
- `preview/VISUAL_0919_AUKCJA_LICYTACJA.png`
- `preview/VISUAL_0919_AUKCJA_WYBOR_KART.png`
- `preview/VISUAL_0919_AUKCJA_WYBOR_PO_1.png`
- `preview/VISUAL_0919_TAWERNA_PLANSZA.png`
- `preview/VISUAL_0919_STRAZNIK_3_ROZMIARY.png`

Dodatkowe testy dotyczą fazy po 3 rundach, pieniędzy, kolejności,
braku duplikacji, wstrzymania przejścia do kolejnej tury, trwałości
Tarczy, Prowokacji, zapisu/wczytywania w fazie licytacji, AI oraz
odtwarzania *rzeczywistego* meczu z aukcją na silniku v19.

Właściwe 3/6/12 PŻ to **przyjęta interpretacja obecnego wymagania**:
„3 ATK, Prowokacja, Tarcza, wersje z 3, 6 i 12 życiami”.
