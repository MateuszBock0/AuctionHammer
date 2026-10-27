# Historia zmian — AuctionHammer

Poniżej opisane są **wydania produktu dla graczy**, a nie wszystkie wewnętrzne commity. Zapis `0.9.x` określa wersję gry; tag `build-xxxxxxxx` wskazuje dokładny commit skompilowanego ZIP-a Windows. Nie wszystkie numery pośrednie były publikowane jako osobne wydania.

Pełne szczegóły historycznych mechanik pozostają w [dokumentacji projektu](docs/STATUS_PROJEKTU.md). Instalacja, aktualizacje i kryteria publikacji: [Proces wydań](docs/RELEASE_PROCESS.md).

## [0.9.103] — 2026-10-27

### Karczemna Burda — podświetlany licznik i czytelna podpowiedź
- Po **najechaniu na napis BURDA: N TUR** etykieta otrzymuje złotą ramkę i przyciemnione tło, a na prawym bocznym panelu pojawia się objaśnienie zasad. Dymek celowo nie leży na polach jednostek, nie przesuwa żadnego elementu gry i znika po odsunięciu kursora.
- Informacja pochodzi z **autorytatywnego stanu Match**, pokazuje pozostałe tury i obrażenia na **następny ukończony koniec tury** (w nowych grach N obrażeń, w starszych 1). Opisuje obrażenia wszystkich jednostek obu stron, pochłanianie przez Tarcze/pancerz, ochronę bohaterów i kart na ręce oraz wydłużenie Burdy o +3 tury po zakupie.
- Dymek działa także przy **BURDA: 0 TUR**, pomagając przed kupnem piwa, i rozpoznaje historyczne zapisy 1 DMG/turę. Ukrywa się przy aukcji, menu, pomocy, powtórkach i modalnych wyborach. Jedynie UI; żadne zasady, zapisy, kliknięcia i sztuczna inteligencja nie zostały zmienione.
- Testy: 3→2→1→0, historyczny licznik 6 tur z 1 DMG, odporność na zamknięte i otwarte okna, granice hitboxów, brak zmiany stanu, brak zasłaniania pól kart.

## [0.9.102] — 2026-10-27

### Normalne AI — realna wartość aukcji zamiast automatycznego podbijania
- Normalny komputer nie podbija już stawki tylko dlatego, że trwa późniejsza aukcja: **usunięto sztywny minimalny limit 4–9 monet**. Ocenia koszt zdobycia pierwszego wyboru wobec darmowej drugiej karty i wartość odmówienia pierwszego wyboru przeciwnikowi.
- Gdy różnice między trzema ofertami są znikome, AI pasuje. Przy naprawdę silnej karcie ustawia wyższy limit; uwzględnia dostępne monety, zachowuje rezerwę na pozostałe aukcje oraz ostrożniej liczy koszt przy małym portfelu. Bonusy licytacji nadal pomniejszają wymaganą **rzeczywistą** stawkę, bez obchodzenia limitu.
- Poziomy łatwy i trudny, ceny piwa, obrażenia Burdy, karty, podpisane audyty i zasady aukcji pozostają bez zmian. Testy: remisy, marginalne korzyści, cenne oferty, wpływ przyszłych aukcji, niska płynność, kupony i zgodność starszych wariantów.

## [0.9.101] — 2026-10-27

### Karczemna Burda — wszystkie poziomy AI podejmują rozważne decyzje i jaśniejszy ogień
- **Nowe partie z mechaniką skalowanych obrażeń:** AI łatwe, normalne i trudne oceniają, czy warto kupić piwo. Szybko porównują marginalne obrażenia na widocznych jednostkach obu stron po dopisaniu 3 tur, uwzględniają jednorazową Tarczę, zużywalny pancerz, PŻ, ATK, ważniejsze zgony, cenę piwa i rezerwę monet przed aukcją. Nie odczytują ręki, talii ani RNG. Łatwe wymaga większej przewagi niż normalne, normalne większej niż trudne. Wszystkie rezygnują przy nieopłacalnym bilansie lub natychmiastowym legalnym ataku kończącym partię.
- Komputer nie kupuje drugiego kufla, gdy Burda ma już co najmniej dwie tury — chroni to przed zapętlaniem zakupów i niepotrzebnym samozniszczeniem. Stare mecze z obrażeniami 1 na turę **zachowują historyczną politykę AI**, a podpisane audyty i zasady pozostają niezmienione.
- **Grafika:** płomyki na zewnętrznych narożnikach wszystkich 10 pól są wyższe i znacznie bardziej kontrastowe — pomarańczowa otoczka, jaśniejszy rdzeń, żółte języki i niezależne iskry. Nadal 4 deterministyczne klatki animacji, z mocą 3+/2/1/0 tur; bez zasłaniania statystyk, przesuwania kart lub nowych efektów rozgrywki.
- Nowe testy obejmują decyzje wszystkich trudności, obronę, ryzyko swoich strat, stare gry, brak odczytu ukrytych informacji, brak mutacji stanu i renderowane poziomy ognia.

## [0.9.100] — 2026-10-27

### Karczemna Burda — płomienie reagują na czas, obrażenia 3→2→1
- **Nowe partie:** na koniec każdej tury każda jednostka obu plansz otrzymuje tyle **zwykłych obrażeń**, ile pozostało tur Burdy **przed zmniejszeniem licznika**. Jeden kufel: kolejno 3, 2 i 1 (łącznie 6 na jednostkę). Dwa kufle od razu: 6, 5, 4, 3, 2, 1 (łącznie 21). Dodatkowe kufle zwiększają licznik o 3 tak jak dotąd. Tarcza pochłania pojedyncze uderzenie, pancerz przyjmuje normalne obrażenia, a zgon wielu jednostek jest rozstrzygany jedną falą.
- **Historyczne mecze, zapisy i podpisane powtórki** bez znacznika `tavern_scaled_damage_enabled` zachowują dokładnie stare 1 obrażenie na zakończoną turę, wraz z dawnym zapisem zdarzeń. Nowa reguła jest jawnie podpisana w audycie nowych partii i zachowana przy zapisie/odczycie.
- **Grafika:** cztery niezależnie przesunięte w fazie klatki maleńkich płomieni przy wszystkich 10 slotach; różne wysokości i iskry. Przy 3+ turach ogień żywszy, przy 2 średni, przy 1 pojedynczy żar, przy 0 gaśnie. Karty, opisy, hitboxy i przyciski bez zmian; klawisz A wyłącza animację. Lewy kufel nadal usunięty (0.9.99).
- Licznik i panel pokazują bieżące DMG na nadchodzący koniec tury. Testy dla 3→2→1, 6 tur, Tarcz/pancerza, nowych i starych podpisanych audytów, zapisów oraz płomieni.

## [0.9.99] — 2026-10-26

### Karczemna Burda — kufel po prawej, płomyki wokół wszystkich pól
- Usunięto nierówny, dziwnie wyglądający kufel po lewej. Świece pozostają na ramie planszy; jeden kufel pojawia się tylko podczas rzeczywiście opłaconego nalewania przy prawym końcu dolnego rzędu kart, przewraca się, rozlewa piwo na dolne obrzeże i znika po 1450 ms.
- Ogień idzie od prawej do lewej i delikatnie migocze przy zewnętrznych narożnikach **10 pól jednostek**, także zajętych. Nie zasłania statystyk i nie zmienia hitboxów.
- **Gdy BURDA ma 0 tur, ogień całkowicie znika**. Pierwszy kufel daje 3 końce tur, każdy następny dodaje kolejne 3 na dotychczasowych zasadach. Wczytana aktywna partia pokazuje ogień z samego stanu gry. Klawisz A wyłącza animacje.
- Wyłącznie wizualna poprawka: bez zmian obrażeń, cen, kart, AI, zapisów i audytów. Osobne testy limitu tur, lewej pustej dekoracji i obu rzędów pól.

## [0.9.98] — 2026-10-26

### Karczemna Burda — świeca na ramie planszy, rozlane piwo i ogień
- W miejsce prostokątnych, przyklejonych do boków symboli trafiają bogato cieniowane, przezroczyste **sprite’y pixel art** świecy, płomienia i kufla, opracowane na podstawie zaakceptowanego wyglądu. Wosk, metal i piana mają spójną, 48-kolorową paletę i ostre, niewygładzone krawędzie.
- Świece są **zamocowane na drewniano-mosiężnym obrzeżu samej planszy**, w tej samej projekcji co pole gry. Kufle są tuż przy nim; po autorytatywnym zakupie widać nalewanie (600 ms), przechylanie się kufli, spływanie piwa na powierzchnię planszy, pianę, zapłon wzdłuż krawędzi i dogasający żar.
- Obie strony pokazują tę samą sekwencję. Ogień dociera do powierzchni planszy, ale nie zasłania wartości ATK/PŻ, kart ani przycisków; po naciśnięciu **A** dynamiczne efekty znikają. Nie zmieniono hitboxów i nie dodano obrażeń: Karczemna Burda nadal zadaje **1 zwykłe obrażenie obu stronom na koniec każdej tury**, zgodnie z 0.9.95.
- Tylko warstwa wizualna: istniejące zapisy, podpisane replaye, ekonomia 0.9.97, aukcje, AI i bilans kart bez zmian. Dodane regresje dla atlasu sprite’ów, czasu animacji i obu krawędzi; ręczne sprawdzenie na fizycznym Windows pozostaje wymagane.

## [0.9.97] — 2026-10-26

### Karczma: przystępniejsze piwo, mocniejsze licytacje i wyraźniejsze dekoracje
- W **nowych meczach** cena pierwszego kufla u każdego gracza zaczyna się od 10 monet. Każdy kolejny własny kufel podnosi cenę o 10 monet, a co dwie rozpoczęte tury łącznie cena zwiększa się o 1 monetę: `10 + 10 × wcześniejsze własne kufle + floor(tury obu graczy/2)`. Saldo monet przestaje wpływać na cenę. Stare zapisane mecze oraz podpisane replaye używają starego wzoru.
- **Normalne AI** wyraźniej walczy o pierwszeństwo wyboru kart podczas aukcji, również gdy dwie oferty są podobne. Zachowuje niewielką rezerwę na przyszłe aukcje. Łatwe i trudne AI w licytacji bez zmian.
- Dwie stylizowane pixel-artowe świece na każdej z dwóch drewniano-mosiężnych listew (łącznie cztery): knot, wosk, krople wosku, delikatna poświata i niezależne 4 klatki animacji po 130 ms, przesunięcie płomienia do 1 px. Kanciaste retro kufle z pianą, uchwytem i animacją nalewania. Po napełnieniu (600 ms) obie strony pokazują jednocześnie rozlanie piwa i mocniejszy płomień świec. Rozbłysk trwa krótko, wyłącza się klawiszem A i nie dotyka kart, hitboxów ani obrażeń na koniec tury.
- Nowe regresje w `tests/test_tavern_price_visual_0997.py`, w tym zgodność podpisanych powtórek i wczytywania starszych zapisów. Ręczny przegląd na fizycznym Windows pozostaje wymagany.

## [0.9.96] — 2026-10-26

### Karczemna Burda — etap 2: lekkie nalewanie i mądre zakupy komputera
- Po faktycznie opłaconym kuflu przez maksymalnie 600 ms pojawia się złoty strumień nalewanego piwa i napełnianie kufla, a płomienie na bocznych dekoracjach kołyszą się maksymalnie o 2 px. Komendy gry ani rysowanie kart nigdy nie czekają na zakończenie animacji.
- Warstwa dekoracyjna zachowuje wszystkie hitboxy, statystyki, pozycje, kolejność i skalowanie kart. Żadnego obracania sceny ani kosztownego tworzenia powierzchni w każdej klatce. Wyłączenie animacji klawiszem **A** natychmiast pokazuje widok statyczny.
- **Tylko trudne AI** może kupić piwo automatycznie, opierając się na najwyżej 10 jawnych jednostkach obu plansz. Ostrożnie porównuje trzy spodziewane obrażenia przez Tarcze/pancerz, unika kupowania przy braku wrogich jednostek, zostawia monety na przyszłą aukcję, nie kupuje kolejnego kufla dopóki globalny efekt ma więcej niż 1 turę i priorytetyzuje pewny śmiertelny atak. Łatwy i normalny nie zmieniają zachowania.
- **Wszystkie reguły 0.9.95 bez zmian:** cena max(10 + suma rozpoczętych tur obu graczy, ceil(10% bieżących monet)), +3 tury za każdą dolewkę, 1 zwykłe obrażenie obu plansz co zakończoną turę, brak limitu zakupów dla gracza. Zero nerfów legend i zmian signed replay/save.
- Testy: `tests/test_tavern_visual_ai_0996.py` (czas i zakres animacji, brak RNG i mutacji, kupno opłacalne i nieopłacalne, ochrona budżetu, CPU p95 <20 ms dla samej heurystyki). Przed scaleniem wymagane wszystkie poprzednie bramki CI oraz zatwierdzone 0.9.95 na gałęzi main.

## [0.9.95] — 2026-10-26

### Karczemna Burda — etap 1: ognie, kufle i grywalny efekt
- Dwie lekkie pochodnie i dwa kufle w istniejących bocznych marginesach planszy. Pikselowe figury Pygame bez nowych assetów, bibliotek i przebudowy hitboxów. Własny przycisk **KUP [B]**.
- Cena KAŻDEGO kufla wynosi `max(10 + T, ceil(M / 10))`, gdzie `T` oznacza łączną liczbę **rozpoczętych tur obu graczy**, nie pełne rundy aukcyjne, a `M` to posiadane monety kupującego przed płatnością. Brak dodatkowej dopłaty za kolejne zamówienia.
- Każdy zakup dodaje dokładnie **3 zakończenia tur** do wspólnej Karczemnej Burdy. Na końcu każdej tury 1 zwykłe obrażenie otrzymuje każda **jednostka obu plansz**, nie bohaterowie ani karty na ręce. Tarcza/pancerz chronią normalnie, zgony zachowują wspólną falę efektów. Kolejne zamówienia wydłużają czas, nie zwiększają obrażeń.
- Mechanika podpisana tylko dla nowych meczów v22; wszystkie stare podpisane audyty, zapisy i replaye bez znacznika odtwarzają dotychczasowe reguły. Nie zmieniono kart, legend, statystyk, aukcji ani AI.
- Następny etap: wizualny przechył/chwianie otoczenia i rozsądne zakupy AI; na razie bez obrotu hitboxów, kosztownego renderingu i nowych animowanych assetów.
- Testy ceny i zaokrąglenia, obu stron, wspólnej fali śmierci, Tarcz/pancerza, wielokrotnego kupowania, zapisów i odmowy zakupu. Ręczny odbiór na fizycznym Windows: oczekuje.

## [0.9.94] — 2026-10-26

### Lekkie planowanie walki (Hard AI) — bez wydłużania tury
- Wyłącznie **trudny** komputer: przegląd **maksymalnie 3 ciosów** z pięcioma zachowywanymi wariantami na poziom, najwięcej pięć dostępnych jednostek i pięć celów. Używa jawnej planszy, legalnych ataków oraz policzonych obrażeń przez osłony i pancerz, w tym podwójnych ataków.
- Plan wykrywa zakończenie gry kilkoma kolejnymi uderzeniami (np. słaby atak konsumuje Tarczę bohatera przed silniejszym) oraz tanie usunięcie Tarczy jednostki umożliwiające dobitkę. Nie przewiduje ukrytych kart ani reakcji uruchamiających nieznane wybory.
- **Bez klonowania Match, bez wirtualnych komend silnika i bez RNG**. Gdy nie można wiarygodnie ustalić korzystnej sekwencji, zostaje stara, sprawdzona ocena 0.9.93. Łatwy i normalny pozostają nietknięci.
- Izolowany pomiar wydajności i p95 na GitHub runnerze (akceptacja poniżej 100 ms na decyzję), 64 pełne audytowane partie z zamianą stron na wspólnych seedach przeciw dokładnej polityce 0.9.93, raport JSON. Wyniki pomiarów i skuteczności muszą być faktycznie potwierdzone przed scaleniem.
- Bez zmian zasad, statystyk, AI aukcji, premiowania Generała A002, legacy audytów, UI ani dźwięków. Wizualny test na fizycznym Windows pozostaje osobnym etapem.

## [0.9.93] — 2026-10-26

### Mocniejsze AI w trybie trudnym oraz premia Generała wyłącznie dla własnej planszy
- **Trudny komputer** ocenia pary wszystkich gotowych atakujących i legalnych celów, zamiast wybierać pierwszego gotowego atakującego. Priorytet mają rozpoznane ciosy kończące partię, także z kombinacji kilku gotowych jednostek. Uwzględnia aktualny pancerz, Tarczę, podwojenie obrażeń od Generała, odwet, utratę własnej ważnej aury i zagrożenie zgonowymi zdolnościami wroga. Bez ukrytej ręki, zaglądania do RNG lub mutowania planszy podczas oceny. Poziomy łatwy i normalny bez zmian.
- **Generał Oddziału Natarcia A002**: podstawowy stale dodaje **+1 ATK tylko każdej jednostce na swojej planszy** (w tym samemu Generałowi), nigdy wrogom. Rzadki wskazuje tylko jedną jednostkę własnej armii, nadając podwójny atak i podwójne standardowe obrażenia. Legendarny premiuje tylko **nowych własnych** sojuszników na swojej planszy, bez udzielania premii przeciwnikowi. Tarcza i zatwierdzone trwałe 0/2/4 pancerza zostają; legendy bez nerfów.
- Reguła Generała jest **podpisanym opt-in nowych meczów v22**. Historyczne savegame i signed replays zachowują swoją autentyczną dawną logikę oraz SHA; oryginalny katalog tekstowy pozostaje nienaruszony, a opisy karty nowych meczów oraz podgląd aukcji odzwierciedlają nowe działanie.
- Testy regresyjne jednostek Generała obu graczy, rzadkiej i legendarnej premii, starych zapisów, podglądu, audytów oraz pełnych parowanych meczów porównujących trudne AI z wcześniejszą polityką ataków. Próg przewagi jest sprawdzany empirycznie (nie ma gwarancji wygranej każdej partii).
- Statystyki i zdolności samych kart, historie starych meczów, dźwięki i oprawa wizualna pozostają bez innych zmian.

## [0.9.92] — 2026-10-26

### Czytelne aktywacje zdolności — źródło → cel → rezultat
- Pokazuj przez około 1,2 sekundy **kto aktywował zdolność, kogo dotknęła i co rzeczywiście się zmieniło**: regeneracja (także A014 v24), statusy, wzmocnienie ATK/MAX PŻ, leczenie, strata PŻ lub zużycie ochrony, jeżeli źródło jest jednoznacznie potwierdzone.
- Źródło i odbiorcy otrzymują krótkie, pikselowe znaczniki narożne; po tej samej stronie cienka linia przebiega wyłącznie przez wolną szczelinę przy pasku bohatera. Między przeciwnymi stronami nie rysuje się połączenia przez centralny HUD.
- Napis pojawia się w wolnym pasku między dolnym paskiem bohatera a ręką (y=710–741), a nie na kartach; w przypadku efektów na kilku sojusznikach pokazuje liczbę **rzeczywistych odbiorców**, bez kilku nakładających się etykiet.
- Dane pochodzą z **poprawnie zakończonych komend audytu** i rzeczywistych zmian w śladach wewnętrznych. Nie wyświetlają się niepotwierdzone decyzje, przewidywane obrażenia ani mylone z atakiem zwykłe uderzenia broni.
- Wyłączenie animacji [A], historia, replay i modalne okna wyłączają wizualizację oraz konsumują zdarzenia bez opóźnionego odtwarzania. Bez nowych zasobów, dźwięków lub zależności. Bez zmian `Match`, RNG, kart, balansu v24, AI, zapisów i historycznych audytów.
- Testy jednostkowe oraz Pygame dla źródła, grupowania, negatywnych prób, ochrony statystyk i resetu po załadowaniu. Odbiór wizualny na fizycznym Windows nadal wymagany.

## [0.9.91] — 2026-10-25

### Smart Auction AI — pierwszeństwo wyboru, limity i ocena ryzyka
- **Łatwy:** nigdy nie licytuje więcej niż `floor(własne_monety/2)`, także w obecności bonusu do skutecznej oferty; dodatkowo zachowuje zachowawczy limit związany z numerem aukcji.
- **Normalny:** wycenia korzyść z pierwszego wyboru względem darmowej karty pozostałej po pierwszym wyborze przeciwnika; umiarkowanie uwzględnia pozbawienie rywala jego preferowanej oferty i przyszłe aukcje.
- **Trudny:** uwzględnia publiczne preferencje i planszę obu graczy, ryzyko pozostania bez monet, silne archetypy w puli oraz krytyczne zagrożenie zdrowia.
- Uwzględnia sześć buffów v24 obowiązujących w nowych partiach. Nie osłabia kart, nie zmienia reguł ani RNG, nie zagląda do ukrytej ręki lub talii przeciwnika.
- Symulator `tools/simulate_smart_auction_0990.py` porównuje pełne mecze łatwy/normalny i normalny/trudny na wspólnych seedach, z zamienianiem stron. Nie wymusza 100% zwycięstw; raportuje statystykę empiryczną.

## [0.9.90] — 2026-10-25

### Święto aukcji: sześć dodatkowych wzmocnień (buff-only)
- **A014 Kapłan:** rzadka daje losowemu sojusznikowi regenerację 2 PŻ przez 2 tury; legendarna nadaje ją wszystkim własnym jednostkom co turę. Porcje kumulują się, wszystkie dotychczasowe aury antyleczenia pozostają.
- **A003 Matka Kości:** gdy brak karty na cmentarzu, tworzy bezumiejętnościowego Szkieleta 6/6, 7/7 lub 8/8, zależnie od rzadkości, ewentualnie z większymi statystykami wskazanymi przez najsilniejszą kartę na ręce.
- **A004 Regent oraz A016 Kartograf:** przy pełnej planszy otrzymują Tarczę (podstawowa), Tarczę + połowę statystyk innej jednostki (rzadka) albo Tarczę + pełne statystyki (legendarna) zamiast niemożliwej kopii lub dodatkowego wystawienia.
- **A009 Złodziej Wspomnień:** po wymianie wszystkie karty na nowej własnej ręce otrzymują trwale +1/+1, +2/+2 lub +3/+3.
- **A002 Generał:** Tarcza i dodatkowo 0/2/4 trwałego pancerza zależnie od rzadkości; przy awansie uzupełnienie różnicy, bez podwójnego naliczania.
- Bez osłabiania wcześniejszych mocnych kart. Legendarne pozostają celowo OP; warianty historycznego audytu D-01–D-05 zachowano jako osobną dokumentację, nie jako automatyczny zestaw zmian.
- Nowe reguły v24 dotyczą nowych meczów; starsze zapisy i podpisane audyty pozostają w poprzednich zasadach.

**Testy i szczegóły:** [Patch v24](docs/BALANCE_PATCH_V24_0990.md) i `tests/test_balance_buff_v24_0990.py`. Fizyczna akceptacja Windows jest nadal wymagana.

## [0.9.89] — 2026-10-25

### Dyskretna warstwa dźwiękowa (40% muzyka / 10% efekty)
- Ustawiono **40% głośności muzyki** i **10% głośności efektów** jako domyślne wartości dla nowych ustawień. W menu USTAWIENIA pojawiły się osobne przyciski MUZYKA i EFEKTY, przełączające co 10% od 0% (wyciszenie) do 100%.
- Preferencje zapisują się lokalnie do `audio_settings.json`, niezależnie od meczu i jego audytów.
- Dodano **osiem autorskich, bardzo cichych efektów** generowanych z krótkich deterministycznych przebiegów PCM: karta podnoszona/wystawiona, atak, trafienie, tarcza lub pancerz, aktywacja zdolności, śmierć jednostki oraz rozstrzygnięcie aukcji.
- Sygnały akcji odczytywane są z zatwierdzonych wpisów `Match.audit_actions`; trafienia, bloki i śmierci z rzeczywiście wyemitowanych wizualnych zmian stanu. Ograniczono częstotliwość, liczbę jednoczesnych powiadomień i zaległe dźwięki.
- Gdy urządzenie audio nie działa, gra działa nadal bez błędu. Bez cudzych próbek i bez nowych plików muzycznych; muzyka Fantasy Tavern pozostaje bez zmian.

**Bez zmian:** obrazy, tekst, reguły, AI, balans, RNG, zapis, replay i audyty. Fizyczna akceptacja dźwięków na Windows nadal wymagana.

## [0.9.88] — 2026-10-25

### Kadrowanie ku górze w kwadratowych ofertach aukcji
- Oryginalne portrety 295×209 przy zwykłym `cover` do 116×116 nie mają żadnego pionowego zapasu; samo ustawienie `focus_y` niczego by nie zmieniło.
- Wyłącznie w trzech kwadratowych miniportretach aukcji dodano delikatne **powiększenie 1,08×** i **zakotwiczenie u góry**. Twarz i górny fragment postaci pozostają w kadrze, a niewielki fragment dolnego tła jest przycinany. Kadr poziomy pozostaje centralny.
- W pamięci podręcznej grafik rozróżniane są parametry powiększenia i punktu kadrowania. Ilustracje na ręce, podglądy pełnej zdolności, karty i napisy pozostają bez zmian.
- Nowe testy sprawdzają rzeczywistą zmianę kadru (nie no-op), pierwszą linię obrazu, cache, zgodność pozostałych widoków oraz wszystkie 51 wariantów aukcyjnych.

**Bez zmian:** pliki źródłowe PNG, zasady gry, silnik, balans, AI, RNG, zapisy i układ interfejsu. Fizyczna kontrola na Windows nadal wymagana.

## [0.9.87] — 2026-10-25

### Czytelniejsze podglądy i kwadratowe portrety aukcji
- Statusy i napisy `ATAKI 1/1` na ilustracjach powiększonych kart nie są ponownie skalowane nearest-neighbour razem z postacią; ich prostokąty są wyłączane z ostrej warstwy i zachowują czytelne wygładzone glify z 0.9.86.
- Na dużych podglądach większa typografia płytek statusów, informacji o gotowości oraz podpisu maksymalnych PŻ; rozmiar kart na planszy i hitboxy pozostają dotychczasowe.
- Jedynie kwadratowe fotografie trzech ofert aukcyjnych używają kadrowania `cover`, bez poziomej granicy między ilustracją a sztucznie przedłużonym tłem. Oryginalny pionowy zakres postaci pozostaje w kadrze, przycinane są boczne fragmenty scenerii. Pełne podglądy, powiększenia oraz paski na kartach nadal używają `contain`.
- Testy 0.9.87 pilnują geometrii wyłączeń tekstu, 51 prawdziwych wariantów aukcyjnych i braku poziomych obcięć w square art.

**Bez zmian:** mechanika gry, balans, RNG, katalogi, zapisy, audyty i pliki PNG. Ręczna akceptacja Windows 100/125/150% nadal wymagana.

## [0.9.86] — 2026-10-25

### Czytelność fontów bez rozmywania ilustracji
- Skalowanie całego interfejsu do rozmiaru okna wykorzystuje filtr interpolacyjny poprawiający czytelność niewielkich liter przy ułamkowej skali (np. mniejsze okno i Windows DPI 125%).
- Same portrety kart i aukcji są kompozytowane osobno przez nearest-neighbour z końcowej klatki; ilustracje PNG pozostają bez zmian. Warstwy modalne nie przywracają obrazów planszy nad menu.
- Test renderingu wymaga jednocześnie wygładzonych napisów oraz ostrych pikseli portretów; zachowano istniejące testy aukcji.

**Zakres:** wyłącznie prezentacja obrazu, bez zmian zasad, AI, balansu, kart i zapisów. Odbiór ręczny na fizycznym Windows (DPI 100/125/150%) jest nadal wymagany.

## [0.9.85] — 2026-10-25

### Naprawiono — czytelność aukcji
- Okno aukcji wykorzystuje wcześniej niewykorzystaną przestrzeń u góry. Trzy panele ofert są o 97 pikseli wyższe, ale kończą się nad panelem licytacji.
- Ilustracje mają osobną strefę bez żadnych etykiet. Rzadkość (`PODSTAWOWA`, `RZADKA`, `LEGENDARNA`) oraz moment aktywacji (`KONIEC TURY`, `PASYWNA` itd.) są rozdzielone na dwa wyraźne paski **poniżej obrazu**. Opis zdolności ma pięć wierszy i własne ciemne tło; przycisk pełnego opisu oraz status oferty znajdują się poniżej. Nie zmieniono samych pięknych ilustracji pixel art.
- Naprawiono panel `PROWADZI: KOMPUTER/GRACZ` i `TWOJA OFERTA`: oba pola mają osobne nagłówki, liczby i wewnętrzne odstępy. Faktyczna płatność, skuteczna oferta i minimum pozostają rozdzielone. Podsumowanie bonusów nie nachodzi na obramowanie, suwak ani przyciski.
- Zaktualizowano pozycje kliknięć, pełnej inspekcji, suwaka, przycisków i komunikatów, tak aby odpowiadały nowej geometrii. Dodano testy realnego renderu Pygame i wykrywania kolizji tekstu/portretu.

**Bez zmian** zasad licytacji, kosztów, AI, mechaniki kart, obrażeń, zapisów, audytów i plików oryginalnych grafik.

## [0.9.84] — 2026-10-25

### Poprawiono — tylko UX/UI istniejącego MVP
- **Pixel art:** pełne okno jest skalowane ostro, metodą nearest-neighbor, również przy nietypowej wielkości okna. Starsze grafiki aukcyjne używają tej samej zasady zamiast rozmycia.
- **Walka:** potwierdzone trafienia używają krótkich pikselowych elementów zamiast okrągłych poświat; wskazywanie legalnego celu pozostaje czytelne, ale nie zakrywa ilustracji napisem `ATAKUJ`. Duży podgląd karty nie otwiera się nad przeciwnikami, gdy wybrana własna jednostka może atakować.
- **Aukcja:** subtelne pikselowe narożniki wskazują tylko te oferty, które można naprawdę wybrać. Wcześniejsze oznaczenia zdolności, rzadkość, pełne portrety i dokładna prezentacja ceny pozostają bez zmian.
- **Interfejs:** same-stronowe połączenia aur biegną przez wąski bezpieczny pas przy bohaterze. Aury między stronami pokazują dokładne etykiety i obramowania źródła/odbiorcy, ale nie przecinają kreskami 56-pikselowego komunikatu tury.
- Dodano testy rozdzielczości, HUD-u, zachowania podglądów, archiwalnych assetów, efektów trafienia i wskazywania ofert. Raport: `docs/MVP_VISUAL_AUDIT_0984.md`.

**Bez zmian** kart, zasad walki, wyników obrażeń, zdolności, AI, balansu, waluty, losowania, zapisów i audytów.

## [0.9.83] — 2026-10-25

### Ulepszono wygląd i wygodę
- Portrety wszystkich 51 wariantów aukcyjnych zachowują pełny centralny obraz. Puste marginesy zastąpiono niewygładzanym, **pikselowym przedłużeniem faktycznego tła ilustracji** w kafelkach 4 px. Pixel art kart podstawowych pozostaje wzorcem stylistycznym: bez rozmycia, gradientów i deformacji postaci.
- Ikony frakcji oraz rodzin zdolności są skalowane najbliższym sąsiadem. Na ofertach aukcyjnych dodano dwa małe symbole 8-bitowe wraz z wyjaśnieniem aktywacji i mechaniki po najechaniu.
- W licytacji wyraźniej pokazane są skuteczna oferta lidera, rzeczywista własna cena, minimalna wymagana kwota, bonus A018 i monety pozostałe po wygranej.
- Celowanie otrzymało dyskretne pikselowe narożniki na wybranym atakującym i legalnym celu. Nielegalne cele mogą wyświetlić krótkie wyjaśnienie w panelu bocznym; dotychczasowa cienka czerwona strzałka pozostaje bez zmian.
- Dodano regresje renderowania, pixel art i zgodności stanu z podpisanym audytem.

**Bez zmian** zasad walki, działania aukcji, mechaniki zdolności, AI, losowania, zapisu i powtórek.

## [0.9.82] — 2026-10-25

### Ulepszono interfejs
- Przy przeciąganiu własnej jednostki do ataku ponownie pojawia się strzałka celowania, ale jest bardzo dyskretna: cienka czerwona linia 2 px, półprzezroczystość alpha 49/255 poza celem i 77/255 na legalnym celu, mały grot i brak ciężkiej obwódki. Celowanie nadal podświetla legalne cele, a kliknięcie lub upuszczenie na celu korzystają z dotychczasowej mechaniki silnika.
- Poprawiono kadrowanie 51 wariantów ilustracji kart aukcyjnych. Małe paski kart używają wyśrodkowanych, nieobcinanych bannerów, a duże karty/podglądy i miniatury ofert pokazują pełny portret zamiast przycinać górę głowy, hełm i skraje sceny. Marginesy dopasowują się do dominującej barwy konkretnej ilustracji.
- Dodano testy zachowania całej wysokości oryginalnych ilustracji oraz przezroczystości, grubości i warunków rysowania strzałki. Żaden plik źródłowy pixel art nie został zmieniony.

**Bez zmian** zasad ataku, legalności celów, obrażeń, AI, aukcji, RNG, zapisów i formatu audytów.

## [0.9.81] — 2026-10-25

### Uproszczono
- Usunięto dużą strzałkę z grotem podążającą za kursorem podczas przeciągania ataku własną jednostką na przeciwnika lub wrogiego bohatera. Nie zasłania ona już kart ani planszy.
- Zachowano wyraźne ramki podświetlające **rzeczywiście legalne cele** oraz etykietę `ATAKUJ`. Ataki działają zarówno przez kliknięcie jednostki i celu, jak i przeciągnięcie jednostki na cel i puszczenie przycisku myszy.
- Zaktualizowano przewodnik i testy renderowania ataku; strzałki wskazujące aktywne aury są osobną funkcją i pozostały bez zmian.

**Bez zmian** mechaniki ataku, AI, logiki kart, RNG, ekonomii, schematów zapisu i audytów.

## [0.9.80] — 2026-10-24

### Naprawiono
- Strzałki aktywnych aur poprowadzono ortogonalnie przez wolne korytarze między rzędami lub wzdłuż ich zewnętrznych krawędzi, aby nie przecinały środka innych kart.
- Wydanie Windows zawiera teraz `CHANGELOG.md` i `CONTRIBUTING.md`. Weryfikator sprawdza lokalne linki i ilustracje README w rzeczywistym folderze gry oraz w gotowym ZIP-ie przed publikacją.
- Publikacja GitHub Release została uzależniona od pełnej regresji Linux, 20 podpisanych pełnych meczów, 100 niezależnych meczów forensic oraz trzech kohort 400/300/300 (łącznie 1000 podpisanych powtórek). Build Windows rozpoczyna się dopiero po sukcesie tych bramek; później przechodzi własne testy, kompilację i kontrolę ZIP-a.

**Bez zmian** zasad, AI, kart, balansu, losowania, formatu zapisów i schematów audytu.

## [0.9.79] — 2026-10-24

### Zmieniono
- Całkowicie przebudowano stronę główną GitHuba pod nowych graczy: opis rozgrywki, oryginalne ilustracje, szybka instalacja, sterowanie, pomoc i informacje o projekcie.
- Uporządkowano wszystkie ostatnie wersje w jednym publicznym changelogu, oddzielonym od dokumentacji technicznej.
- Dodano podręcznik gracza, poradnik diagnostyczny, instrukcje dla kontrybutorów i przewodnik dla programistów.
- Dodano formalny proces wydawniczy, sprawdzanie spójności numerów wersji oraz generowanie notatek GitHub Releases z odpowiedniej sekcji tego pliku.
- Dodano publiczne szablony zgłaszania błędów i propozycji funkcji.

**Bez zmian** w kartach, AI, mechanice gry, RNG, historii audytów i formacie zapisów.

## [0.9.78]

### Dodano
- Graficzne połączenia aktywnych aur między jednostkami na planszy — wskazanie źródła lub odbiorcy ujawnia kierunek i konkretny modyfikator.
- Obsługę `S34` (premia/kara ATK), `S35` (maksymalne PŻ), `S105` (pozostały pancerz z konkretnej aury) oraz podstawowego `A002` (ATK +1 wszystkim).
- Odróżnienie wyciszonych/ogłuszonych źródeł od działających aur. `S108` nadal oznacza *możliwą reakcję*, a nie zatwierdzony efekt.

Zmiana wyłącznie wizualna. [PR #101](https://github.com/MateuszBock0/AuctionHammer/pull/101).

## [0.9.76]

### Dodano
- Inteligentny przycisk zakończenia tury: natychmiastowe zakończenie, jeśli nie ma już legalnych akcji.
- Nieblokujące ostrzeżenie o dostępnych atakach i możliwości zagrania karty, gdy gracz chce zakończyć turę przedwcześnie.
- Drugie kliknięcie lub naciśnięcie spacji w ciągu 4,2 s potwierdza decyzję. Kolejny ruch unieważnia ostrzeżenie.

Bez zmian zasad tury. [PR #100](https://github.com/MateuszBock0/AuctionHammer/pull/100).

## [0.9.75]

### Dodano
- Rozbudowany ekran zwycięstwa/porażki: końcowa runda, PŻ, monety, rozegrane akcje i rozwój kart.
- Wyróżnienia: jednostka o najwyższym zaobserwowanym `ATK + MAX PŻ`, największy zarejestrowany ubytek PŻ i lider awansów kart gracza.
- W starych niekompletnych zapisach szczegóły wymagające pełnego audytu są niedostępne zamiast prezentować wartości zmyślone.

[PR #99](https://github.com/MateuszBock0/AuctionHammer/pull/99).

## [0.9.74]

### Dodano
- Wyświetlanie faktycznych obrażeń i leczenia bezpośrednio nad jednostkami lub bohaterami.
- Oddzielne liczby dla zużytej tarczy i pancerza oraz efekty trafień z krótkim kosmetycznym drgnięciem karty.
- Niezależne pozycje komunikatów przy kilku równoczesnych zmianach.

Mechanika obrażeń bez zmian. [PR #98](https://github.com/MateuszBock0/AuctionHammer/pull/98).

## [0.9.72]

### Dodano
- Atakowanie przez przeciągnięcie strzałki z własnej jednostki na legalny cel; zwykłe kliknięcia nadal działają.
- Pasek postępu awansu kart podstawowych na ręce i krótki rozbłysk pokazujący rzeczywistą zmianę poziomu, ATK i PŻ.

[PR #97](https://github.com/MateuszBock0/AuctionHammer/pull/97).

## [0.9.71]

### Dodano
- Płynne przeciąganie karty z ręki na pięć własnych pól.
- Podświetlenie legalnych pól, zachowanie punktu chwycenia i kosmetyczny powrót po upuszczeniu poza planszą.

## [0.9.70]

### Zmieniono
- Finalna, spójna oprawa 51 wariantów aukcyjnych kart pixel art w dwóch proporcjach.
- Gra używa gotowych ilustracji bez nakładania odrębnych kwadratowych portretów na tło.

## [0.9.69]

### Dodano
- Osobne kompozycje ilustracji dla 17 archetypów aukcyjnych w trzech rzadkościach, wraz z archiwum materiałów graficznych i SHA-256.

## [0.9.68]

### Dodano
- Duży podgląd wystawionych jednostek po najechaniu kursorem i poprawione skalowanie obrazów kart aukcyjnych.

## [0.9.67]

### Ulepszono
- Kolorowanie wzmocnionego i osłabionego ATK oraz maksymalnego PŻ; lepsze oznaczenie pancerza.
- Wyświetlanie bieżącej siły standardowego ataku z premią Generała.

## [0.9.65]

### Dodano
- Pełne ilustracje pixel art 70 kart podstawowych: po osobnym portrecie i poziomej ilustracji każdej z nich.

## [0.9.64]

### Zmieniono
- Naprzemienną kolejność rozpoczynania nowych meczów w aplikacji: najpierw komputer, w kolejnym meczu gracz.
- Wybór rekompensaty za drugi ruch i jego prezentację w menu początku partii.

Dalsze starsze zmiany i zasady w [archiwum dokumentacji](docs/README_HISTORIA_DO_0932.md) oraz [opisie aktywnego MVP](docs/CURRENT_MVP_RULES_0964.md).
