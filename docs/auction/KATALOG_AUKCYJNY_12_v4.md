# AuctionHammer — 12 kart aukcyjnych / 36 efektów — DRAFT v4 (audyt)
**18.10.2026 · Katalog do zatwierdzenia · Niezaimplementowany w aktualnym AuctionHammer MVP.**

**Źródła:** `sources/KATALOG_AUKCYJNY_12_v3.md` i `.json` (ostatnia propozycja użytkownika), `GRA_KARCIANA_ONLINE_GAME_MASTER_v19/GAME_MASTER.md`, sekcja 12 oraz ramy sekcji 13. **Wszystkie 36 opisów zdolności z v3 zachowano bez zmian**. v4 jedynie proponuje zmianę bazowych profili statystyk pięciu kart i dodaje jawne interpretacje implementacyjne.

## 1. Jak naprawdę przebiega aukcja — korekta fałszywej kombinacji trzech kart

1. Aukcja następuje **po pełnej rundzie 3, 6, 9, ...**, po przyznaniu obu graczom +1 monety. Trzy różne archetypy są **ofertami**; nie są kartami zagrywanymi na planszę.
2. Każda oferta niezależnie losuje rzadkość: **60% podstawowa, 30% rzadka, 10% legendarna**. Oferty tej samej aukcji dotyczą trzech różnych archetypów.
3. Zwycięzca licytacji płaci zadeklarowaną kwotę i bierze **jedną** kartę na rękę; przegrywający wybiera **jedną inną za darmo**. **Trzecia** wraca do puli. Brak płatnych ofert = naprzemienne pierwszeństwo zgodnie z v19.
4. Karty są na ręce. Każdy gracz nadal może **normalnie wystawić tylko jedną kartę na własną turę**, na planszę maksymalnie 5 jednostek. Dodatkowe przywołania będące **efektem zdolności** (Regent/Królowa) nie są dodatkowymi zakupionymi kartami ani normalnymi zagraniami z ręki.
5. Do końca rundy 9 każdy gracz może więc dostać **maksymalnie 3 różne fizyczne karty aukcyjne**, z trzech aukcji, chyba że później nastąpi przejęcie/wymiana na mocy zdolności. Nawet dysponując trzema, trzeba normalnie wystawiać je w różnych turach (przykład: tury własne 4, 7, 10).
6. Losowania w ramach **100 000 niezależnych trójek aukcji** dały P≈**16.46%**, że wszystkie A002/A004/A010 *w ogóle* ukażą się w 9 ofertach oraz P≈**8.88%**, że hipotetycznie dałoby się wybrać po jednej z każdej z trzech aukcji. **To tylko górne ograniczenie możliwości zdobycia zestawu, a nie częstość jego użycia czy win rate**. Bez modelu przeciwnika, licytacji i meczów nie ma podstaw do nerfu kombinacji.

## 2. Formuła statystyk i ewolucja

**Zamrożone bazowe ATK + MAX HP = R + 8** dla R=3,6,9,... oznaczającego rundę **zdobycia**, nie bieżącą rundę. W v4 proponuję podział dla późniejszych rund: `ATK(R) = ATK(3) + (R−3)/3`, `MAX_HP(R) = R+8−ATK(R)`. Oznacza to +1 ATK oraz +2 MAX HP na każde kolejne trzy rundy *oferty*, lecz **już zdobyta karta nigdy nie rośnie w ten sposób**. Formuła to nowy projektowy wybór implementacyjny, nie wynik pomiaru balansu.

Każdego trzeciego zakończonego pełnego obrotu rund **po zdobyciu**: podstawowa→rzadka→legendarna; legendarna bez dalszej ewolucji. Przemiana działa niezależnie od miejsca karty (ręka, talia, plansza, cmentarz), lecz **nie odtwarza zdolności „Przy wystawieniu”**, nie leczy, nie odnawia pancerza, nie zmienia bazowych ATK/HP i nie odnawia zużytej zdolności „raz na mecz”. Premiami na planszy, np. za A010, można zwiększyć *bieżące* statystyki — to nie jest skalowanie na ręce.

| Archetyp | v3 ATK/HP (R3) | v4 ATK/HP (R3) | R6 | R9 | Uwagi |
|---|---:|---:|---:|---:|---|
| A001 Władca Dusz | 3/8 | **3/8** | 4/10 | 5/12 | bez zmian |
| A002 Generał Oddziału Natarcia | 2/9 | **3/8** | 4/10 | 5/12 | **korekta** |
| A003 Matka Kości | 2/9 | **2/9** | 3/11 | 4/13 | bez zmian |
| A004 Regent Krzywych Zwierciadeł | 4/7 | **4/7** | 5/9 | 6/11 | bez zmian |
| A005 Bankier Widm | 1/10 | **2/9** | 3/11 | 4/13 | **korekta** |
| A006 Królowa Zakazanych Słów | 2/9 | **2/9** | 3/11 | 4/13 | bez zmian |
| A007 Strażnik Ostatniego Tchnienia | 1/10 | **2/9** | 3/11 | 4/13 | **korekta** |
| A008 Architekt Pustki | 3/8 | **3/8** | 4/10 | 5/12 | bez zmian |
| A009 Złodziej Wspomnień | 2/9 | **2/9** | 3/11 | 4/13 | bez zmian |
| A010 Królowa Tysiąca Twarzy | 2/9 | **4/7** | 5/9 | 6/11 | **korekta** |
| A011 Jeździec Czarnej Komety | 6/5 | **6/5** | 7/7 | 8/9 | bez zmian |
| A012 Tkaczka Drugiego Losu | 1/10 | **3/8** | 4/10 | 5/12 | **korekta** |

**Uzasadnienie pięciu niewielkich zmian:**
- **A002**: Trwała bardzo silna aura wymaga nieco łatwiejszego usunięcia; -1 HP, +1 ATK.
- **A005**: Efekt daje całą premię od razu; minimalne przesunięcie z obrony w atak.
- **A007**: Zabezpieczenie przed przegraną stanowi już ogromną wartość; mniej HP u źródła ułatwia kontrę.
- **A010**: Kumulujące się buffy na koniec każdej tury są najsilniejszym długofalowo efektem; -2 HP zmniejsza niezawodność uruchomienia wielu razy.
- **A012**: Bardzo silny jednorazowy wpływ na HP bohaterów; mniejsza odporność samej jednostki.

Powyższe przesunięcia mają **charakter hipotez projektowych**, nie zweryfikowanego statystycznie balansu. Zachowują dokładnie sumę 11 w rundzie 3. Przed ustaleniem na stałe należy porównać ich wpływ w pełnych partiach i przy rzeczywistych aukcjach.

## 3. Pełny katalog — 12 archetypów × 3 rzadkości

### A001 — Władca Dusz  (Przy śmierci, R3: 3 ATK / 8 HP)
**Rola:** Przejęcia / łańcuchy.
- **Podstawowa:** Zabij jedną wskazaną wrogą jednostkę. Wywołuje jej zwykłą śmierć i legalne efekty „Przy śmierci”.
- **Rzadka:** Wybierz: zabij jedną wskazaną wrogą jednostkę ALBO przejmij jedną wskazaną wrogą jednostkę na stałe, jeśli masz wolne miejsce na planszy. Przejęta zachowuje rany i statusy.
- **Legendarna:** Wybierz efekt podstawowy, efekt rzadki ALBO przejmij jedną wskazaną wrogą jednostkę i nadaj jej „Przy śmierci: przejmij jedną wskazaną wrogą jednostkę”. Nadanie nie kumuluje się na tej samej jednostce.
**Oryginalne ograniczenia v3:** Przeciwnik może zabić źródło bez przygotowanego miejsca na przejęcie; ogłuszenie/wyciszenie blokuje efekt śmierci.
**Doprecyzowania wynikające z audytu v4:**
- Przejęcie rozpatruje się dopiero, jeśli jest wolne pole po usunięciu źródła i całej fali zgonów; brak wolnego pola = nie można wybrać trybu przejęcia.
- Wersja legendarna dodaje efekt po śmierci tylko przejętej jednostce, nie kopiuje go łańcuchowo bez następnego rzeczywistego zgonu.

### A002 — Generał Oddziału Natarcia  (Pasywna, R3: 3 ATK / 8 HP)
**Rola:** Aura ofensywna / podwójne ataki i obrażenia.
- **Podstawowa:** Gdy Generał jest na polu bitwy, wszystkie jednostki na obu planszach (także wrogie i sam Generał) mają +1 ATK. Premia znika po opuszczeniu przez Generała planszy.
- **Rzadka:** Gdy Generał jest na polu bitwy, jedna wybrana własna jednostka otrzymuje Podwójny atak i zadaje podwójne obrażenia swoimi atakami. Premia działa tylko, gdy Generał jest na planszy.
- **Legendarna:** Gdy Generał jest na polu bitwy, każda NOWO zagrana przez Ciebie jednostka otrzymuje Podwójny atak i zadaje podwójne obrażenia swoimi atakami. Premia działa tylko, gdy Generał jest na planszy.
**Oryginalne ograniczenia v3:** Zgodnie z dosłownym „wszystkie” podstawowa premia obejmuje obie strony. Rzadka i legendarna dotyczą własnej armii (interpretacja robocza). Podwójny atak nadal daje maksymalnie 2 ataki, nie 4; podwojenie obrażeń dotyczy normalnych obrażeń z ataku, nie efektów trucizny ani umiejętności. Nowa rzadka wersja wybiera beneficjenta przy pojawieniu się Generała lub jego ewolucji; zmiana celu po śmierci beneficjenta jest jeszcze do zatwierdzenia.
**Doprecyzowania wynikające z audytu v4:**
- PODSTAWOWA: zgodnie z dosłownym słowem „wszystkie” +1 ATK dotyczy obu armii i samego Generała.
- RZADKA: aktywny beneficjent to jedna własna jednostka wskazana przy wejściu Generała/zmianie rzadkości; gdy umrze, cel przepada aż do ponownego uzyskania zdolności na nowej instancji Generała.
- LEGENDARNA: aura dotyczy własnych jednostek zagranych lub przywołanych PO uzyskaniu legendarnej zdolności, w tym legalnie zagranych kopii; nie działa wstecz. Bonus istnieje wyłącznie przy aktywnym Generale na planszy.
- Podwójny atak: maksymalnie 2 ataki, a podwojenie standardowych obrażeń z każdego uderzenia nie zwiększa efektów umiejętności ani toksyn. Dwie takie aury nie tworzą czterokrotnych obrażeń (niekumulujące się flagi).

### A003 — Matka Kości  (Przy śmierci, R3: 2 ATK / 9 HP)
**Rola:** Cmentarz / wskrzeszanie.
- **Podstawowa:** Wybierz jedną inną własną podstawową jednostkę z cmentarza. Przenieś ją na rękę.
- **Rzadka:** Wybierz efekt podstawowy ALBO przywróć jedną inną własną podstawową jednostkę z cmentarza bezpośrednio na prawe wolne pole planszy z 1 HP, bez aktywowania „Przy wystawieniu”; jeśli brak pola, przenieś ją na rękę.
- **Legendarna:** Wybierz efekt podstawowy, rzadki ALBO przywróć do dwóch różnych innych własnych podstawowych jednostek z cmentarza: pierwszą na wolne prawe pole z pełnym MAX HP, drugą na rękę. Jeśli brak pola, obie na rękę. Nie uruchamiaj „Przy wystawieniu”.
**Oryginalne ograniczenia v3:** Nie wskrzesza samej siebie, kart wykluczonych z mulliganu ani kopii efemerycznych. Zdolności śmierci wskrzeszonych kart działają dopiero przy kolejnej rzeczywistej śmierci.
**Doprecyzowania wynikające z audytu v4:**
- Wskrzeszenie z cmentarza nie jest wygrywaniem aukcji; maksymalnie jedno zwykłe wystawienie z ręki na turę wciąż obowiązuje.

### A004 — Regent Krzywych Zwierciadeł  (Przy wystawieniu, R3: 4 ATK / 7 HP)
**Rola:** Kopiowanie jednostek.
- **Podstawowa:** Wskaż jedną inną własną jednostkę na planszy. Stwórz jej efemeryczną kopię i od razu zagraj ją na swoją planszę.
- **Rzadka:** Wskaż dowolną inną jednostkę na dowolnej planszy. Stwórz jej efemeryczną kopię i od razu zagraj ją na swoją planszę.
- **Legendarna:** Wskaż dowolną inną jednostkę na dowolnej planszy. Stwórz jej efemeryczną kopię, zachowując jej bieżące bonusy i efekty, nadaj kopii Tarczę i od razu zagraj ją na swoją planszę.
**Oryginalne ograniczenia v3:** Kopia trafia na wolne pole (maks. 5); brak wolnego pola = brak przywołania. To dodatkowe zagranie poza limitem jednej zwykłej karty na turę; jej zdolność „Przy wystawieniu” uruchamia się, chyba że została ogłuszona albo wyciszona. Podstawowa i rzadka kopia zachowują bazowy archetyp/statystyki/zdolność, ale nie przejmują dotychczasowych buffów i statusów celu. Legendarna przenosi także stan i modyfikatory bieżące. Kopie mają unikalny identyfikator, nie można kopiować kopii; po opuszczeniu planszy znikają z meczu. Źródła i czasy wygaśnięcia skopiowanych efektów należy poprawnie przypisać nowej instancji.
**Doprecyzowania wynikające z audytu v4:**
- Wybranie i wystawienie Regenta z ręki zużywa limit jednej karty; wywołana kopia może dodatkowo wejść na wolne pole.
- Kopia jest efemeryczna z unikalnym ID. Jej zdolność Przy wystawieniu może zadziałać, ale jeśli kopia jest Regentem, nie powtarza efektu kopiowania.
- Podstawowa/rzadka wersja bierze bazowe ATK, MAX HP i bazową zdolność celu oraz bieżące obrażenia (rany), lecz nie przenosi aktualnych buffów/statusów. Legendarna przenosi aktualne modyfikatory i statusy oraz dodaje tarczę; bez kopiowania pola owner, event_id i czasu „raz na mecz”.
- Następna karta aukcyjna nadal wymaga kolejnej tury do normalnego zagrania; kopia z efektu nie jest nowym zdobytym przedmiotem aukcyjnym i znika na dobre po opuszczeniu planszy.

### A005 — Bankier Widm  (Przy wystawieniu, R3: 2 ATK / 9 HP)
**Rola:** Monety / ekonomia.
- **Podstawowa:** Ukradnij przeciwnikowi do 3 monet (przenieś je do swojego salda), a następnie DODATKOWO otrzymaj 3 nowe monety.
- **Rzadka:** Ukradnij przeciwnikowi do większej z wartości: 3 monety albo połowa jego aktualnego salda (zaokrąglona w górę). Następnie DODATKOWO otrzymaj 4 nowe monety.
- **Legendarna:** Ukradnij przeciwnikowi wszystkie jego monety, a następnie DODATKOWO otrzymaj 5 nowych monet.
**Oryginalne ograniczenia v3:** Kradzież nigdy nie może przekroczyć rzeczywistego salda przeciwnika; jeśli przeciwnik ma 0 monet, nadal tworzysz 3/4/5 nowych monet. To dwie osobne operacje: transfer + generowanie dodatkowych monet. Przykład bazowy: wróg ma 2, więc Ty dostajesz 2 skradzione + 3 nowe = +5.
**Doprecyzowania wynikające z audytu v4:**
- RZADKA: „co najmniej 3” oznacza próbę min(saldo_wroga, max(3, ceil(saldo_wroga/2))) — ujemne saldo jest niedozwolone.
- Wygenerowane dodatkowe monety 3/4/5 to NOWE monety, a nie transfer; do salda doliczamy zarówno przelew, jak i bonus.

### A006 — Królowa Zakazanych Słów  (Przy wystawieniu, R3: 2 ATK / 9 HP)
**Rola:** Wyciszenie / kontrkontrola.
- **Podstawowa:** Wycisz jedną wskazaną wrogą jednostkę do końca jej najbliższej własnej tury.
- **Rzadka:** Wycisz do dwóch różnych wskazanych wrogich jednostek do końca ich najbliższej własnej tury.
- **Legendarna:** Wycisz wszystkie jednostki przeciwnika obecne na planszy do końca ich najbliższej własnej tury.
**Oryginalne ograniczenia v3:** Wyciszenie blokuje zdolności, w tym „Przy śmierci”, ale nie usuwa samych kart z planszy; oczyszczanie może je zdjąć. Nie cofa już rozpatrzonych zdarzeń.
**Doprecyzowania wynikające z audytu v4:**
- Wyciszenie nie cofa wcześniej rozpatrzonych zdolności; cel nadal może atakować standardowo, chyba że inny status go blokuje.

### A007 — Strażnik Ostatniego Tchnienia  (Pasywna, R3: 2 ATK / 9 HP)
**Rola:** Ratunek bohatera.
- **Podstawowa:** Raz na mecz: jeżeli własny bohater miałby zginąć od obrażeń, poświęć tę jednostkę i pozostaw bohatera z 1 HP.
- **Rzadka:** Raz na mecz: zamiast śmierci bohatera poświęć tę jednostkę i ustaw HP bohatera na 20.
- **Legendarna:** Raz na mecz: zamiast śmierci bohatera poświęć tę jednostkę, ustaw HP bohatera na 25 i ogłusz wszystkie aktualne wrogie jednostki do końca ich najbliższej własnej tury.
**Oryginalne ograniczenia v3:** Działa wyłącznie, jeżeli Strażnik stoi na planszy na początku śmiertelnej fali obrażeń. Poświęcenie zużywa efekt trwale dla tego egzemplarza, także po ewolucji lub ewentualnym wskrzeszeniu.
**Doprecyzowania wynikające z audytu v4:**
- Tylko zgon od obrażeń / bezpośredniej utraty HP kwalifikuje się do ratunku; ustawienie HP za pomocą A012 nie uruchamia strażnika, jeżeli reguła ustawia HP powyżej zera.
- Ten sam fizyczny egzemplarz ratuje dokładnie raz w całym meczu, niezależnie od wskrzeszenia i ewolucji; ofiara nie aktywuje własnego efektu Przy śmierci, jeśli go nie ma.

### A008 — Architekt Pustki  (Przy wystawieniu, R3: 3 ATK / 8 HP)
**Rola:** Wygnanie / usuwanie zasobów.
- **Podstawowa:** Naznacz jedną wskazaną wrogą jednostkę: po zakończeniu jej najbliższej własnej tury zostanie wygnana, jeżeli nadal jest na planszy i znacznik nie został oczyszczony.
- **Rzadka:** Wygnaj natychmiast jedną wskazaną wrogą jednostkę oraz jedną losową kartę z ręki przeciwnika (o ile takie cele istnieją).
- **Legendarna:** Wygnaj natychmiast do trzech wskazanych wrogich jednostek oraz jedną losową kartę z ręki przeciwnika.
**Oryginalne ograniczenia v3:** Wygnanie usuwa kartę trwale z meczu, bez śmierci, bez monety za zabicie i bez efektów „Przy śmierci”. Nie dotyczy bohaterów.
**Doprecyzowania wynikające z audytu v4:**
- Wygnanie nie jest śmiercią i nie wyzwala jej efektów ani nagrody za zabicie; kopie efemeryczne zamiast trafiać do wygnania po prostu znikają.

### A009 — Złodziej Wspomnień  (Przy wystawieniu, R3: 2 ATK / 9 HP)
**Rola:** Ręka / kontrola kart.
- **Podstawowa:** Wymień jedną wskazaną kartę ze swojej ręki na jedną losową kartę z ręki przeciwnika.
- **Rzadka:** Podejrzyj rękę przeciwnika i wymień jedną wskazaną kartę ze swojej ręki na jedną wybraną kartę przeciwnika.
- **Legendarna:** Zamień całe aktualne ręce obu graczy miejscami, łącznie z własnością fizycznych egzemplarzy. Następnie przeciwnik wybiera i odrzuca 2 karty ze swojej nowej ręki (lub wszystkie, jeśli ma mniej niż 2).
**Oryginalne ograniczenia v3:** Odrzucone po legendarnej wymianie karty trafiają do prywatnego cmentarza przeciwnika, NIE do strefy EXCLUDED_FROM_MATCH z mulliganu; mogą później wrócić w cyklu talii. Przy wymianie zachowują się aktualne ulepszenia i premie przypisane do egzemplarzy. Nowy właściciel otrzymuje kontrolę nad tymi kartami.
**Doprecyzowania wynikające z audytu v4:**
- Zmiana właściciela kart aktualizuje prywatne strefy i prawa sterowania w jednym atomowym zdarzeniu.
- Dwie karty odrzucone po legendarnej wymianie wybiera przeciwnik ze swojej NOWEJ ręki; cmentarz jest przypisany do nowego właściciela.

### A010 — Królowa Tysiąca Twarzy  (Na koniec tury, R3: 4 ATK / 7 HP)
**Rola:** Przywołania / przewaga planszy.
- **Podstawowa:** Na koniec własnej tury wybierz: przywołaj na wolne pole własnej planszy efemerycznego Żołnierza 1 ATK / 1 HP ALBO nadaj Królowej trwałe +1 ATK i +1 MAX HP (oraz +1 bieżącego HP).
- **Rzadka:** Na koniec własnej tury wybierz: przywołaj na wolne pola do dwóch efemerycznych Żołnierzy 2 ATK / 2 HP z Prowokacją ALBO nadaj Królowej trwałe +4 ATK, +4 MAX HP (+4 bieżącego HP) i Prowokację.
- **Legendarna:** Na koniec własnej tury wybierz: przywołaj na wolne pola do dwóch efemerycznych kopii najsilniejszej innej własnej jednostki, z jej aktualnymi ATK i MAX HP, lecz BEZ zdolności; ALBO nadaj Królowej trwały bonus +ATK równy ATK tej jednostki i +MAX HP równy jej MAX HP (wraz z odpowiednim przyrostem bieżącego HP).
**Oryginalne ograniczenia v3:** Każdy wybór następuje raz na koniec własnej tury Królowej; bonusy własne kumulują się pomiędzy turami i są buffami na planszy, nie skalowaniem karty na ręce. Najsilniejsza inna własna jednostka = największe bieżące ATK+MAX HP, przy remisie najbardziej z lewej. Brak innego sojusznika uniemożliwia warianty legendarne zależne od jego statystyk. Kopie i Żołnierze nie aktywują „Przy wystawieniu”, nie są kartami aukcyjnymi ani bazowymi, nie powracają do talii po śmierci; maksymalnie 5 jednostek na planszy.
**Doprecyzowania wynikające z audytu v4:**
- Raz na KONIEC własnej tury Królowej. Nie oznacza to możliwości zagrania dwóch kart z ręki; przywołane Żołnierze i kopie są tokenami.
- Wzmocnienie jest trwałe na planszy i może kumulować się między turami, ale nie jest skalowaniem samego egzemplarza aukcyjnego w ręce.
- Legendarna liczy najsilniejszą inną własną jednostkę z bieżących ATK+MAX HP, przy remisie wybiera najbardziej lewą; token z tej zdolności nie posiada zdolności.

### A011 — Jeździec Czarnej Komety  (Przy śmierci, R3: 6 ATK / 5 HP)
**Rola:** Katastrofa / czyszczenie planszy.
- **Podstawowa:** Przy śmierci zadaj 5 obrażeń każdej wrogiej jednostce jednocześnie.
- **Rzadka:** Przy śmierci zadaj 5 obrażeń każdej wrogiej jednostce jednocześnie oraz 5 obrażeń wrogiemu bohaterowi.
- **Legendarna:** Przy śmierci zniszcz WSZYSTKIE inne jednostki na obu planszach w jednej wspólnej fali (w tym własne) i zadaj 10 obrażeń wrogiemu bohaterowi.
**Oryginalne ograniczenia v3:** Legendarna wersja NIE daje wyboru starszego wariantu: zawsze uruchamia totalne zniszczenie + 10 obrażeń bohaterowi. Zniszczenie powoduje zwykłe zgony i legalne efekty „Przy śmierci” z tej samej atomowej fali. Obrażenia bohatera rozpatruje się według normalnej kolejki i systemu ochrony. Zdolność samego Jeźdźca nie uruchamia się, jeśli był ogłuszony/wyciszony.
**Doprecyzowania wynikające z audytu v4:**
- Wariant legendarny: zaznacz wszystkich pozostałych żyjących uczestników fali jednocześnie, usuń ich po zamrożeniu snapshotu i dopiero potem ustaw kolejkę ich Przy śmierci.
- Jeździec nie może ponownie wyzwalać tego samego zgonu; własne poświęcenie czy zgon już rozliczony nie uruchamia zdolności drugi raz.
- 10 obrażeń wrogiemu bohaterowi jest częścią tej samej akcji, ale podlega tarczy/pancerzowi i strażnikowi — to nie bezpośrednie „ustaw HP”.

### A012 — Tkaczka Drugiego Losu  (Przy wystawieniu, R3: 3 ATK / 8 HP)
**Rola:** Manipulacja HP bohaterów.
- **Podstawowa:** Przy wystawieniu ustaw bieżące HP obu bohaterów na średnią ich aktualnych HP (zaokrągloną w dół), po czym ulecz swojego bohatera o 10 HP (nie ponad jego MAX HP).
- **Rzadka:** Przy wystawieniu wybierz JEDEN tryb: (1) ustaw swoje bieżące HP na bieżące HP przeciwnika, pozostawiając jego HP bez zmian; ALBO (2) ustaw bieżące HP przeciwnika na swoje bieżące HP, pozostawiając swoje HP bez zmian. Następnie ulecz swojego bohatera o 10 HP, nie ponad MAX HP.
- **Legendarna:** Przy wystawieniu zabierz 20 bieżącego HP wrogiemu bohaterowi i ulecz swojego bohatera o 20 HP (maksymalnie do jego MAX HP).
**Oryginalne ograniczenia v3:** Podstawowa i rzadka: ustawienie HP, nie zwykłe obrażenia; nie jest blokowane przez tarczę/pancerz. Legendarna: drenaż HP bezpośrednio zmniejsza bieżące HP wroga o 20 i leczy własnego bohatera o 20; nadwyżka leczenia przepada. Jeżeli przeciwnik ma ≤20 HP, może od tego zginąć. Progi monet za spadek HP obowiązują normalnie. UWAGA interpretacyjna: zapis rzadkiej wersji „wybierz” potraktowano jako dwa kierunki kopiowania HP, a NIE równoczesną zamianę obu wartości.
**Doprecyzowania wynikające z audytu v4:**
- PODSTAWOWA: średnia floor((HP_twoje+HP_wroga)/2); potem ulecz siebie o 10 do maksimum.
- RZADKA: wybierz KIERUNEK nadpisania HP (własne:=wroga ALBO wroga:=własne), a następnie ulecz siebie o 10. To nie jednoczesna zamiana dwóch wartości.
- LEGENDARNA: przeciwnik traci 20 HP, Ty odzyskujesz do 20 HP; brak leczenia ponad maksymalne HP. Efekt omija pancerz/tarczę jak bezpośredni drenaż, ale reakcja Strażnika na śmiertelną utratę HP nadal jest możliwa.

## 4. Granice kombinacji i reguły bezpieczeństwa

**A002 + A004 + A010:** Wspólne występowanie jest możliwe dopiero po trzech osobnych aukcjach, ich osobnym zdobyciu, normalnym wystawieniu w różnych turach i przeżyciu na planszy. Regent wymaga **jednego dodatkowego pustego pola** po własnym wejściu na planszę; inaczej kopia nie powstanie. Przy Królowej obowiązuje ten sam limit pięciu pól. Legendarna aura Generała dotyczy tylko jednostek wchodzących na planszę od momentu jej aktywacji (przywołania są objęte, nie rozdawane automatycznie przez aukcję); przyznany podwójny atak ani podwojenie obrażeń nie mnożą się przez posiadanie kolejnych takich samych aur.

**A004 (pętle):** Wolno kopiować karty i ich legalne „Przy wystawieniu”, ale kopia Regenta nie może sama kopiować dalej. Efemeryczna kopia nigdy nie jest nową nagrodą aukcyjną; nie zostawia trwałego egzemplarza na cmentarzu i nie można jej kopiować. Każdy zapis musi mieć własny `instance_uid` i `source_uid`. Kopie podstawowe/rzadkie odtwarzają statystyki bazowe i utracone HP (rany), legendarne zachowują aktualne bonusy/statusy oraz dostają Tarczę. Wariant v3 ma **pierwszeństwo** nad starszym rezerwowym szkicem kopiowania w GM v19; nie mieszać dwóch definicji.

**A010 (kumulacja):** Wzmocnienie +1/+1, +4/+4 lub dodanie ATK/MAX HP sojusznika może rosnąć co własną turę, podczas gdy źródło żyje i nie jest wyciszone/ogłuszone. To najwyższe ryzyko lawinowego wzrostu. Zamiast usuwać Twoje efekty, w planie testowym mierzymy liczbę przeżytych tur i maksymalną wartość, a balansujemy wytrzymałość źródła i kontrę kontrolną.

**A011 (fala śmierci):** Zgony innych jednostek z legendarnego Jeźdźca są jednoczesne. Zamrozić listę poległych i ich stan przed rozpatrywaniem efektów, po czym przetworzyć legalne efekty „Przy śmierci” jeden raz na instancję. Współistniejące Władcy Dusz i Matki Kości nie mogą zmieniać snapshotu już ustalonej fali.

**A012 (HP bohaterów):** Ustawianie HP w odmianie podstawowej i rzadkiej ignoruje pancerz/tarcze, ale nadal uwzględnia jednorazowe progi monet po utracie HP. Legendarna kradzież zdejmuje 20 HP przeciwnika, nawet jeśli ma mniej niż 20; może zakończyć grę. Efekt leczący jest ograniczony do maksymalnych 100 HP; pozostała część przepada. Przy bezpośrednim śmiertelnym drenażu Strażnik Ostatniego Tchnienia może zareagować zgodnie z opisem ratunku.

**A005 (pieniądze):** Rzadka wersja próbuje ukraść `max(3, ceil(monet_przeciwnika/2))`, ale nigdy nie więcej niż faktycznie posiada przeciwnik. Następnie generuje dodatkowo +4. Nie interpretować tego jako kradzież „co najmniej 3” z ujemnym saldem.

**Płatne aktywacje:** 12 kart ma automatyczne/pasywne/trigerowe efekty; w tym katalogu **nie nadano im kosztów manualnego aktywowania**, więc nie wolno dopisać kosztu monet za zagranie. Historyczna reguła podstawowa 1/mecz, rzadka 1/turę, legendarna wielokrotnie dotyczy przyszłych **płatnych aktywowanych zdolności**, jeżeli zostaną zdefiniowane osobno, a nie biernych i jednorazowych „Przy wystawieniu”.

## 5. Raport weryfikacji i gotowość wdrożenia

- Sprawdzono, że **12/12** archetypów jest unikatowych i posiada **3/3** warianty; **36/36 oryginalnych efektów v3** zachowano dosłownie w JSON-ie.
- Wszystkie **12 profili** sumują się do 11 w rundzie 3; dla R=3..120 co 3 wszystkie kombinacje mają dokładną sumę R+8. Bez zmiany statystyk po zakupie.
- Izolowany moduł `tools/auction_reference.py` testuje reguły przydziału, limity, awans, liczby dla Bankiera/Tkaczki/Królowej/Generała, sposób reprezentacji kopii oraz snapshot zgonów; **nie implementuje pełnego silnika 36 zdolności**.
- **35/35 testów izolowanych** przeszło (uruchom `python -m unittest discover -s tests -v`).
- Wykonano **100 000 prób** Monte Carlo wyłącznie na dostępności ofert. Wyniki nie dowodzą balansu PvP ani bezpieczeństwa wszystkich 36 mechanik w działającym silniku.
- **Bez zmian w repo GitHub AuctionHammer**. Wydanie z aukcjami, koszty/aukcyjne AI/UX, serwer licytacji i pełna atomowa kolejka śmierci wymagają osobnego etapu implementacji.

**Decyzja audytowa:** pozostawić 36 efektów użytkownika bez nerfowania kombinacji, zaproponować 5 niewielkich przesunięć HP/ATK w obrębie tego samego budżetu oraz jawne zabezpieczenia techniczne. Katalog nadal oznaczony DRAFT, nie udawać przetestowanego balansu.
