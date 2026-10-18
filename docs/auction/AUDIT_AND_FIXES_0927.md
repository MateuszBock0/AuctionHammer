# AuctionHammer 0.9.27 — audyt prawdziwego meczu i weryfikacja aukcji v4

## Źródło diagnozy

Przeanalizowano audyt rzeczywistego zakończonego meczu 0.9.23
(seed `21451821`, commit `63eb6dbdba3c75a164c2ad5ade29247cd8970c65`,
34 rundy, 330 komend, 575 wpisów historii, 57 zgonów).
Audyt użytkownika nie jest publikowany w repozytorium.

### Tkacz Run nie stracił PŻ pomimo ataku

W akcji 214 (runda 22) Mistrz Tarczy (`S94`) nadał Tarczę
Tkaczowi Run (`S04`). W akcji 218 (runda 23) Widmo Otchłani (`S21`)
zaatakowało Tkacza. Według zapisanych przed/po:
- Tkacz Run: HP `4 → 4`,
- Tarcza `1 → 0`, źródło `S94`,
- Widmo Otchłani zginęło wskutek kontrataku.
Jest to prawidłowy wynik walki z Tarczą, nie błąd odejmowania PŻ.
**Poprawka:** silnik rejestruje fakt blokady i wielkość pochłoniętych
obrażeń; wpis jest widoczny w historii i kolorowym feedbacku interfejsu.

### Błędne „utracone jednostki”

Stary ekran używał `len(p.grave)`, czyli **aktualnego cmentarza**.
Dla audytu 0.9.23 ekran wyświetlał **0 / 1**, ale w całej
partii doszło do **28 / 29** faktycznych zgonów (gracz / komputer).

**Poprawka:** `Match.death_counts` zwiększa licznik tylko podczas
`_remove_unit(..., death=True)`. Zastąpienie 5. jednostki, przejęcie
i wygnanie nie liczą się jako zgony. Karta podstawowa, która po
przetasowaniu wróci i umrze ponownie, zwiększa licznik drugi raz.
Licznik jest zapisywany w savegame i trafia do
`summary.unit_deaths` w wyeksportowanym audycie.

Jeśli starszy zapis posiada kompletny rejestr audytu, odtwarzamy
liczniki z usunięć jednostek i weryfikujemy ich sumę względem wpisów
`Zgon` w dzienniku. Gdy nie da się wiarygodnie odtworzyć całego
meczu, UI **jawnie** opisuje licznik jako zgony od wczytania,
zamiast podawać niepełną liczbę jako sumę całego meczu.

## Zdolności aukcyjne: aktywność a opis

Przed tą poprawką `card_summary.py` i
`card_infographics.py` nadal miały warunek traktujący
**każde `A001–A012` jako „NIEAKTYWNA”**. Dotyczyło to również
aktywnych efektów v4, choć `auction_abilities.py` je wykonywał.

Od 0.9.27:
- tekst na karcie jest dosłownie bieżącym wariantem
  `v4_variant(archetype, rarity)` z pliku
  `data/auction/KATALOG_AUKCYJNY_12_v4.json`;
- karta jest oznaczona jako **AKTYWNA**, ze wskazaniem
  **PODSTAWOWA / RZADKA / LEGENDARNA** zgodnie z aktualnym efektem;
- poziom zakupu jest odczytywany ze stałych metadanych karty,
  bez sugerowania wzrostu statystyk w ręce;
- starszy wariant v3 z `NIEAKTYWNA (planowana)` nadal pokazuje
  nieaktywną umiejętność, zachowując semantykę archiwalnych zapisów;
- wartości liczbowe w opisie aukcji nie są fałszywie wyróżniane jako
  skalowane poziomem trzymania karty na ręce;
- A008 bez celów, A009 bez kart u rywala oraz legendarna A010 bez
  innej własnej jednostki nie oferują przycisków bez żadnego efektu.

## Brak aukcji przy niepełnej puli

Reguła obecna już od 0.9.26 pozostaje bez zmiany.
`Match._drain` sprawdza `len(auction_bag)>=3` przed
uruchomieniem `auction.begin`, które niezależnie ma drugi
warunek bezpieczeństwa. Każda aukcja wymaga trzech różnych
archetypów, przy czym trzecia niekupiona oferta wraca
**wyłącznie do osobnego woreczka aukcyjnego**.

12 fizycznych archetypów, dwie kupione karty na aukcję i jedna
powracająca oznaczają maksymalnie **pięć pełnych aukcji**.
Po piątej pozostają dwa niekupione archetypy: nie ma szóstej
aukcji, a zwykła rozgrywka jest kontynuowana.

## Testy i zakres pewności

- `python -m unittest discover -s tests -v`: 320 testów
  po rozszerzeniu 0.9.27.
- Każdy z **36** wariantów katalogu v4 jest porównywany dosłownie
  z tekstem w UI i sprawdzany pod względem statusu aktywności.
- Dotychczasowe testy wszystkie 36 wariantów uruchamiają w
  rzeczywistym silniku i sprawdzają legalną obsługę `pending`.
- Nowe testy sprawdzają konkretne zachowania: Tarcza i obrażenia,
  licznik zgonów, zapis/wczytanie licznika, dziedziczna zgodność v3,
  Generał A002, wygnanie A008, przejmowanie łańcuchowe A001,
  niezrealizowane wybory A009/A010 oraz wyłączanie aukcji po piątej.
- CI wykonuje regresję UI i renderowanie Pygame bez ekranu.

Testy potwierdzają zidentyfikowane scenariusze i integralność
implementacji, ale nie zastępują oceny balansu z wielu niezależnych
meczów ani ręcznego przeglądu wszystkich możliwych kombinacji kart.

Bez zmiany AI, bez multiplayera i bez prac nad nowym motywem wizualnym.
