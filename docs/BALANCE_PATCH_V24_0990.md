# AuctionHammer 0.9.90 — patch balansu v24 (BUFF ONLY)

Data: 2026-10-25. **Zmiany zatwierdzone przez użytkownika.** Kart legendarnych nie osłabiono — celowo mają być OP, a aukcja spektakularnym wydarzeniem.

**Zakres:** A014, A003, A004, A009, A016, A002. Wszystkie dawne efekty pozostają; wyjątkiem są zastępcze rozstrzygnięcia w sytuacji, kiedy obecny efekt jest niemożliwy (brak pola / celu).

## A014 — Kapłan Odwróconej Łaski

- Podstawowa: dotychczasowa aura blokująca leczenie wroga.
- Rzadka: zachowuje konwersję wrogiego leczenia; na koniec każdej swojej tury przyznaje **jednej losowej własnej jednostce** regenerację **2 HP przez 2 własne tury celu**, wliczając samego Kapłana.
- Legendarna: zachowuje pełną konwersję wrogiego leczenia w obrażenia; na koniec każdej swojej tury nadaje tę samą regenerację **wszystkim własnym jednostkom**, także sobie.
- Porcje regeneracji z kolejnych tur **kumulują się**. Pierwszy tick występuje na końcu tury przyznania porcji, zgodnie ze standardową mechaniką silnika.
- Uzasadnienie parametrów: 2×2 daje odczuwalną korzyść bez jednorazowego, nieodwracalnego burst-healu; efekt obszarowy i kumulacja czynią legendę zdecydowanie ponadprzeciętną.

## A003 — Matka Kości

Jeżeli w chwili zdolności śmierci brak legalnej innej podstawowej karty z cmentarza, Matka próbuje przywołać jednego **Szkieleta bez umiejętności** na wolne pole. Minimum P/R/L to **6/6, 7/7, 8/8**. Jeśli własna ręka zawiera mocniejszą kartę, wybierz **jedną kartę** o najwyższej sumie ATK+MAX HP (remis: wyższy ATK, potem HP, potem ID) i dla ATK oraz MAX HP niezależnie weź maksimum z jej bieżącej statystyki i minimum jakości. Nie wolno przekroczyć limitu pięciu jednostek. Istniejące wskrzeszanie/odzyskiwanie bez zmian, gdy cmentarz zawiera cel.

## A004 — Regent Krzywych Zwierciadeł

Jeżeli po wystawieniu nie ma wolnego pola na kopię, Regent **zamiast kopii** otrzymuje:
- P: Tarczę;
- R: Tarczę oraz +połowa ATK i +połowa MAX HP wybranej innej jednostki (zaokrąglanie w górę);
- L: Tarczę oraz +pełne ATK i +pełne MAX HP wybranej innej jednostki.

Wybrana jednostka może być własna albo wroga dla R/L. Dodatkowy MAX HP podnosi bieżące HP o tę samą wartość. Gdy na obu planszach brak innego celu, zostaje Tarcza.

## A009 — Złodziej Wspomnień

Po **zakończeniu wymiany** każda karta znajdująca się na **nowej własnej ręce** otrzymuje trwale +1/+1 (P), +2/+2 (R), +3/+3 (L) do ATK/MAX HP. Dotyczy również przejętych kart, nigdy oddanych przeciwnikowi. Po pełnej wymianie legendarnej bonus nalicza się tylko raz. Przy braku możliwej wymiany podstawowej/rzadkiej bonus i tak wzmacnia całą posiadaną rękę.

## A016 — Kartograf Utraconych Ścieżek

Gdy nie ma miejsca na dodatkową jednostkę, zadziała **taki sam awaryjny buff jak A004**: P Tarcza, R Tarcza + połowa wskazanych statystyk, L Tarcza + całość wskazanych statystyk. Zachowuje wszystkie legalne etapy doboru, a zamieniany jest wyłącznie niemożliwy etap zagrania dodatkowej jednostki. Premia jest przyznawana raz na wystawienie, nie za każdą oglądaną kartę.

## A002 — Generał Oddziału Natarcia

Przy wystawieniu zyskuje Tarczę: P tylko Tarczę, R dodatkowo 2 trwałego pancerza, L dodatkowo 4 trwałego pancerza. Tarcza nie odnawia się co turę. Przy ulepszeniu na planszy odnawia się, a pancerz jest **uzupełniany różnicą** do nowego poziomu, nigdy przyznawany drugi raz przez sam odczyt. Podwójne ataki oraz mnożniki obrażeń zostają bez zmian.

## Kompatybilność i granice patcha

- Nowe mecze mają `Match.balance_patch_v24=True`; historyczne zapisy, w których flaga nie istnieje, zachowują oryginalną mechanikę.
- 17 archetypów / 51 wariantów aukcyjnych oraz 70 podstawowych kart pozostają bez zmian liczby i struktury.
- Oryginalny audyt krytyczny v24 i warianty A/B/C nie zostały zmodyfikowane ani automatycznie wybrane; zawierają projekty do dalszych decyzji. Ten patch wdraża **sześć jednoznacznie zatwierdzonych buffów**.
- Testy: `tests/test_balance_buff_v24_0990.py`; szerszy regres całej gry i Windows QA powinny przejść przed zbudowaniem wydania.

Źródło decyzji: pakiet `AuctionHammer_v24_AUDYT_PLUS_ZATWIERDZONE_BUFFY_6_KART.zip` z projektu i późniejsze polecenie oszacowania regeneracji A014.
