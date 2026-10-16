# AUCTIONHAMMER — MASTER PROJECT FILE

**Wersja pakietu:** MVP 0.9.2 SOLO + jednoetapowy instalator GitHub  
**Specyfikacja gry:** GAME MASTER v17.0 (16.10.2026)  
**Forma rozgrywki na teraz:** człowiek kontra komputer, offline (Pygame-ce)  
**Docelowo:** PvP online, ale NIE w tym etapie; aukcje są osobnym przyszłym etapem.

## Odczytaj jako pierwszy

Ten dokument zbiera **instrukcję projektu i pełną dokumentację Game Master v17 bez przeredagowywania treści źródłowej**. Dalsza część, od rozdziału „ORYGINALNY GAME MASTER v17”, jest kopią kanonicznej specyfikacji. Gdy historyczny dokument mówi „nie zaimplementowano silnika”, opisuje stan na moment opublikowania specyfikacji, **nie aktualny stan plików MVP**.

### Jak uruchomić nową instalację

Rozpakuj ZIP i kliknij `URUCHOM_AUCTIONHAMMER.bat`. Plik `tools/bootstrap.py` wykona inicjalizację Git, założy prywatne repozytorium `MateuszBock0/AuctionHammer` przy użyciu oficjalnego `gh` (może wymagać autoryzacji GitHub w przeglądarce), po czym wywoła `launch_auctionhammer.py`, który przygotuje `.venv`, instaluje biblioteki i uruchamia `game/main.py`. Nie podawaj haseł ani tokenów w plikach kodu. Bez GitHub gra uruchamia się lokalnie; `GRAJ_OFFLINE.bat` celowo pomija próbę publikacji.

### Aktualny zakres implementacji

- 70 kart podstawowych (po 1 egzemplarzu), bazowa pula / mulligan `EXCLUDED_FROM_MATCH`.
- Silnik naprzemiennych tur, walka, skalowanie, nagrody, statusy, wykonywanie zdolności kart, przeciwnik AI.
- Widoczność efektów przyznanych innym jednostkom: kolorowe oznaczenia, aktywne statusy, źródła.
- Interfejs Pygame z dopasowaniem proporcji okna i pełnym opisem karty.
- Testy w `tests/`, automatyzacja GitHub Actions w `.github/workflows/tests.yml`.

### Otwarte ryzyka implementacyjne

Wersja prototypowa — testy scenariuszy standardowych i symulowanych meczów nie są równoznaczne z pełnym dowodem zgodności. W szczególności wymagane dalsze sprawdzanie atomowych grup jednoczesnych zgonów, złożonych reakcji, aur i szczegółów 70 zdolności. Nie deklarujemy kompletnej produkcyjnej zgodności z kolejką z sekcji 7 v17 ani pełnego balansu. Gra online, aukcje oraz karty aukcyjne pozostają poza zakresem.

### Mapa źródeł prawdy i odpowiedzialności

| Plik | Rola |
|---|---|
| `AUCTIONHAMMER_MASTER.md` | główny dokument projektu wraz z pełną specyfikacją v17 |
| `data/GAME_MASTER.json` | cała dokumentacja v17 w JSON |
| `data/game_rules_v17.json` | zatwierdzone zasady |
| `data/cards_base_70.json` | dokładnie 70 unikalnych definicji, statystyki, bonusy na ręce |
| `data/starter_bank_v17.json` | fizyczna pula 70×1 |
| `data/event_order_v17.json` | wymagany priorytet rozpatrywania zdarzeń |
| `game/core/*` | silnik w Pythonie |
| `game/ui/*` | klient Pygame |
| `game/core/ai.py` | przeciwnik komputerowy |
| `tests/*` | testy i regresje |

### Wykluczenia

Brak aukcji, ofert i kart aukcyjnych; brak rzadkości dla podstawowych kart; brak kosztów wystawienia kart. Monet nie wydaje się w tym MVP. Nie dodawać aukcyjnych mechanik (kopiowanie, przejęcia, wskrzeszanie, specjalny dobór za zdolności, płatne zdolności).

---

# ORYGINALNY GAME MASTER v17 — PEŁNA SPECYFIKACJA

# GRA KARCIANA ONLINE — GAME MASTER
**Kompletny roboczy dokument projektowy (Game Design Document + katalog danych), wersja 17.0**  
**Data:** 16 października 2026 r.  
**Zakres:** zamknięta specyfikacja podstawowego MVP PvP dla 70 kart, statusy, monety, przyszłe aukcje, dane i plan implementacji.

> **Zasada nadrzędna:** tekst i JSON w tym pakiecie odzwierciedlają aktualnie ustalony stan projektu. Wszędzie, gdzie brakuje decyzji lub kod źródłowy symulacji przyjmuje uproszczenie, jawnie oznaczono to jako **DO USTALENIA** albo **PROTOTYP**. Nie traktuj prototypu symulacji jako pełnego silnika gry.

## 0. Szybki indeks i priorytet źródeł

| Pozycja | Rola |
|---|---|
| `GAME_MASTER.md` | Czytelny, kanoniczny opis zasad i katalog kart |
| `data/GAME_MASTER.json` | Kompletny model reguł, metadanych i kart do odczytu programowego |
| `data/cards_base_70.json` | Dokładnie 70 kart, z profilami wzrostu, opisami i ID |
| `data/game_rules_v17.json` | Parametry i rozstrzygnięte reguły gameplayu |
| `data/event_order_v17.json` | Maszynowy kontrakt jednej nadrzędnej kolejki zdarzeń |
| `data/starter_bank_v17.json` | 70 konkretnych unikatowych egzemplarzy (po jednym ID) centralnego banku |
| `data/auction_reservations.json` | Rezerwacja unikatowych zdolności aukcyjnych, NIE finalne karty |
| `karty_startowe_macierz_efektow_v17.xlsx` | Aktualna macierz 70 kart, arkusz zasad v17 i historyczne arkusze balansu |
| `prototype/symulator_gry_v14.py` | Stary eksperymentalny model bitew/aukcji, nie pełny silnik |
| `research/` | Surowe wyniki eksperymentów symulacyjnych |

**Priorytet przy sprzecznościach:** najnowsza zatwierdzona reguła w sekcjach 1–15 i `game_rules_v17.json` ma pierwszeństwo przed historycznymi komentarzami i arkuszami w Excelu i prototypowymi ustawieniami symulatora. Tekst konkretnej karty opisuje jej cel, siłę i czas efektu, ale **nigdy nie zastępuje nadrzędnej kolejki zdarzeń z sekcji 7**.

## 0A. Stan projektu na potrzeby implementacji — wersja v17

**SPECYFIKACJA PODSTAWOWEJ GRY: ZAMKNIĘTA. IMPLEMENTACJA PRODUKCYJNA: JESZCZE NIE WYKONANA.**

- **Wersja MVP:** działający silnik dla dwóch graczy i 70 podstawowych kart bez generowania ofert aukcyjnych ani kart aukcyjnych. Pozostałe reguły bazowe (tury, statusy, kolejka zdarzeń, monety, skalowanie i warunek zwycięstwa) zachowują pełne znaczenie.
- **Pula startowa:** jeden wspólny bank 70 różnych fizycznych kart, po jednym egzemplarzu każdego archetypu. Po rozdaniu 20 kart pozostaje 50, z których wyłącznie na początku losuje się zamienniki w mulliganie. Odrzucone w mulliganie przechodzą trwale do `EXCLUDED_FROM_MATCH`.
- **Bez timerów:** brak limitów na mulligan, turę, wybory i licytację; brak auto-passa, auto-zakończenia tury i przegranej za nieaktywność.
- **Ekonomia:** pierwszy ma 0 monet, drugi +3 na start; każdy +1 po pełnej rundzie. Oboje startują z 100 HP i 0 dodatkowego pancerza.
- **Jedna kolejka:** sekcja 7 i `data/event_order_v17.json`; techniczny kod nie wprowadza indywidualnych priorytetów dla kolejnych kart.
- **Skalowanie:** co własną turę na ręce łącznie +2 punkty ATK/MAX HP według profilu; co 3 tury wzmacnia się zdolność. Ogłuszenie: +1 obrażenie przy skutecznym nałożeniu; oczyszczanie: +1 leczenia albo obrażeń przy użytecznym oczyszczeniu; odporność: +1 trwałego pancerza przy pierwszej skutecznej aktywacji po wystawieniu — za każdy próg.
- **Etap późniejszy:** ok. 36 odrębnych archetypów aukcyjnych z trzema rzadkościami i poziomowaniem. Katalog **nie jest zatwierdzony**. Historyczny `prototype/` i `research/` służą wyłącznie jako materiały eksperymentalne.
- **Status balansu:** indywidualne 70 kart było kalibrowane w uproszczonym modelu, ale gra nie została zweryfikowana na wiernym silniku, a test +3 monet nadal sugerował przewagę gracza pierwszego. **Nie deklarujemy pełnego balansu.**

Aktualny harmonogram implementacji, zakres MVP i późniejszego etapu aukcyjnego opisano również w `IMPLEMENTATION_BACKLOG.md`. Ten indeks ma pierwszeństwo przed starszymi sformułowaniami „do ustalenia” w historycznych arkuszach.

## 1. Wizja gry i rozdział zawartości

Dwuosobowa, internetowa, turowa gra strategiczno-karciana fantasy: gracz zarządza ręką, własną planszą (maks. 5 jednostek), atakami, statusem bohatera i publicznym saldem monet. Zwykłe jednostki dobiera się z początkowej puli oraz prywatnej talii; aukcje co trzy rundy dostarczają kart o nowych, unikatowych mechanikach. Celem jest sprowadzenie HP wrogiego bohatera do zera.

**Dokładnie 70 podstawowych archetypów ORAZ 70 egzemplarzy fizycznych:** pięć frakcji × czternaście rodzin efektów, po jednej karcie w każdej komórce macierzy. **Każdy archetyp występuje dokładnie raz w jednej wspólnej puli startowej.** Karty podstawowe nie mają rzadkości i nigdy nie zużywają monet na aktywację zdolności.

**Aukcje:** nowe, odrębne mechaniki (m.in. kopiowanie, przejmowanie i wskrzeszenie), a nie jedynie powtórki cech kart startowych. Katalog aukcyjny, liczby i ceny poszczególnych kart nie są zatwierdzone.

## 2. Frakcje, momenty aktywacji i estetyka nazw

| Frakcja | Moment aktywacji | Tożsamość | Liczba kart |
|---|---|---|---:|
| Elfy | Przy wystawieniu | magia, druidyzm, runy, światło, natura | 14 |
| Dzikie bestie | Przy ataku | realne i fantastyczne zwierzęta, pazury, instynkt | 14 |
| Potwory | Przy śmierci | zjawy, nieumarli, klątwy, plagi, horror | 14 |
| Krasnoludy | Na koniec tury | kuźnie, inżynieria, kopalnie, runy | 14 |
| Ludzie | Pasywna | armia, sztandary, dowódcy, medycy | 14 |

Karty elfów odwołują się przede wszystkim do magii, druidów, run i natury; nie nazywamy ich „pikinierami”. Bestie to zwierzęta lub zwierzęco-fantastyczne stworzenia, nie zawodowi żołnierze. Potwory są związane ze śmiercią, klątwą, plagą, widmami i nieumarłymi. Krasnoludy budują przewagę inżynierią i kuźnią; ludzie są armią, zakonem, strażą i dowództwem.

## 3. Stan gry — bohater, pola, talie, ręka i zasoby

- Dokładnie 2 graczy. Obaj bohaterowie startują ze **100/100 HP**. Leczenie nie przekracza maksimum.
- Pierwszy gracz wybierany losowo. **Pierwszy otrzymuje 0 monet, drugi otrzymuje 3 monety na starcie.** Brak dodatkowego startowego pancerza i brak bonusa startowego HP.
- Każdy gracz ma osobną rękę, stos dobierania, cmentarz oraz własną planszę o maksymalnie **5 jednostkach**. Saldo monet jest widoczne dla obydwu graczy; nie ma limitu monet.
- Każda jednostka ma m.in. ATK, aktualne HP, MAX HP, ładunki tarczy (globalny limit 1), osobne pule pancerza czasowego i trwałego, modyfikatory i statusy.
- Karty startowe dostępne są w jednym bazowym wariancie; karty aukcyjne zachowują rzadkość i poziom zdobycia.
- **Pula startowa jest zamknięta: dokładnie 70 kart fizycznych = dokładnie 1 egzemplarz każdego z 70 archetypów.** Po rozdaniu 20 kart w banku zostaje 50. Karty oddane podczas początkowej wymiany są przenoszone do osobnej strefy `EXCLUDED_FROM_MATCH` (wyłączone z bieżącego meczu). Nigdy nie wracają do banku, ręki, talii ani cmentarza żadnego gracza; nie mogą być dobrane ani przez właściciela, ani przez przeciwnika. Nowe karty do wymiany pochodzą wyłącznie z niewydanego banku i nie tworzą duplikatów.

## 4. Przygotowanie meczu i mulligan

1. Wylosuj gracza pierwszego; jego przeciwnik uzyskuje 3 monety.
2. Rozdaj każdemu **10 kart podstawowych** z centralnej puli: **5 do ręki, 5 do własnego stosu dobierania**. Bank nie może rozdawać ponad dostępną liczbę egzemplarzy.
3. Każdy gracz **równocześnie i niejawnie** wybiera **0–3 różne** karty ze swojej początkowej ręki. Serwer przyjmuje oba wybory i **trwale wyłącza wskazane egzemplarze z bieżącego meczu** (`EXCLUDED_FROM_MATCH`). Odrzucone karty **nigdy nie wracają do centralnego banku**, nie przechodzą do cmentarza i nie mogą być wylosowane przez żadnego gracza. Serwer losuje bez zwracania każdemu graczowi tyle nowych, różnych kart z **50 egzemplarzy pozostałych po rozdaniu początkowym**, ile gracz wyłączył. Łącznie maksymalnie 6 nowych kart, bez duplikatów, z autorytatywnego RNG. Żaden gracz nie widzi wyborów rywala przed zatwierdzeniem obu. Czekanie na potwierdzenie wyboru nie jest ograniczone zegarem.
4. Własne stosy dobierania tasuje się. Wylosowany pierwszy gracz zaczyna. Pozostałe, nierozdane karty banku nie należą do prywatnych talii i nie są automatycznie dobierane podczas tury.

**Rozróżnienie stref:** odrzucenie w mulliganie = `EXCLUDED_FROM_MATCH` (definitywnie niedostępne do końca tego meczu); śmierć jednostki podczas partii lub jej zastąpienie na planszy = własny `GRAVEYARD`, który normalnie może być przetasowany do prywatnej talii. Te zdarzenia mają odrębne znaczenie i nie wolno używać dla nich tego samego kodu `DISCARD`.

**Brak limitów czasu (wersja bazowa):** mulligan, każda tura gracza, wybory celu, wybory po aukcji i licytacje nie mają czasu maksymalnego. Silnik nie planuje końca tury, auto-passa, auto-licytacji ani przegranej po upływie zegara. Fazy kończą się w wyniku wyraźnych akcji graczy lub zamknięcia meczu. Obsługa awarii i rozłączeń jest zadaniem infrastrukturalnym, a nie pretekstem do wprowadzania timera rozgrywki.

## 5. Tury, jednostki, granice rundy i dochód

**Bez zegara:** nie ma ograniczenia czasu jednej tury ani kar za bezczynność. Zakończenie tury odbywa się wyłącznie po poprawnej komendzie `END_TURN` aktywnego gracza. Wszystkie warunki legalności działań pozostają bez zmian.

**Początek własnej tury:** nalicz skutki trucizny po fazie dobierania, ale przed wykonaniem akcji; dobierz z prywatnego stosu do **co najmniej 5 kart na ręce** (brak górnego limitu). Gdy talia się wyczerpie, przetasuj własny cmentarz do stosu dobierania; jeśli nadal nie można dobrać — bez kary i bez zmęczenia.

**Akcje:** w całej swojej turze gracz może wystawić **maksymalnie jedną kartę jednostki**, bez kosztu. Może też zrezygnować z wystawienia. Ataki jednostek i wystawienie wolno wykonywać w dowolnej kolejności; można zrezygnować z poszczególnych ataków. Zwykła jednostka nie atakuje w turze wystawienia (wyjątkiem jest aktywny Szybki atak). Każda jednostka atakuje co do zasady raz na własną turę, Podwójny atak daje możliwość maksymalnie dwóch ataków.

**Plansza:** nowa jednostka trafia zawsze na skrajne prawe pole; względna kolejność ocalałych jednostek jest zachowywana. Luki zwijają się w lewo. Dobrowolne przestawianie jest zabronione. Przy pełnych pięciu jednostkach wolno zagrać jedną jednostkę, **zastępując dowolną własną jednostkę, która jeszcze w tej turze nie zaatakowała**. Zastąpiona karta trafia na cmentarz, ale **nie umiera** w sensie mechaniki: nie uruchamia zdolności „Przy śmierci” ani nie daje monet za zabicie. Nowa wchodzi skrajnie z prawej.

**Koniec własnej tury:** (1) zdolności „Na koniec tury” na planszy od lewej do prawej, (2) regeneracja, (3) skalowanie wszystkich własnych podstawowych kart nadal na ręce, (4) wygaśnięcie odpowiednich efektów do końca tury. Zdolność jednostki zmarłej przed swoją kolejnością wykonania nie zachodzi.

**Koniec pełnej rundy** następuje po turach obu graczy. Każdy dostaje wtedy **+1 monetę**, przed ewentualną aukcją. Po pełnych rundach o numerach 3, 6, 9 itd. uruchamia się aukcja.

## 6. Atak i walka jednostek

- Atak wolno kierować w dowolną wrogą jednostkę lub wrogiego bohatera, o ile nie ma czynnej wrogiej jednostki z Prowokacją; w takim przypadku atakująca jednostka musi wybrać dopuszczalny cel z Prowokacją.
- Zdolność „Przy ataku” rozpatruje się **przed zwykłą walką**. Może dotyczyć jednostki i bohatera, chyba że opis zawęża cel. Jeśli uśmierci cel przed walką standardową, ta walka nie dochodzi do skutku; atak zostaje zużyty.
- Standardowa walka dwóch jednostek zadaje **jednoczesne obrażenia równe aktualnemu ATK obu jednostek**. Bohater zaatakowany przez jednostkę nie kontratakuje.
- Rany jednostek są trwałe między turami. Jednostka z HP ≤ 0 ginie i przemieszcza się na cmentarz odpowiedniego właściciela.
- Ogłuszenie blokuje ataki i wszystkie specjalne zdolności danej jednostki, również pasywną i śmierci. Wyciszenie blokuje tylko jej zdolności, a nie zwykłe ataki.
- Szybki atak + Podwójny atak mogą łączyć się i pozwolić na dwa ataki w turze wystawienia; ich działanie i czas trwania zawsze wynikają z konkretnej karty.

## 7. Jedna nadrzędna kolejność zdarzeń — REGUŁA OSTATECZNA (od v15)

**Nie tworzymy osobnych priorytetów dla kolejnych kart.** Każda akcja (`PLAY_CARD`, `ATTACK`, `END_TURN`, przyszłe `ACTIVATE_PAID_ABILITY`) oraz wywołany nią efekt przechodzi przez ten sam deterministyczny silnik. Serwer jest jedynym arbitrem; klient tylko deklaruje akcje i wybory.

### 7.1. Priorytet jednej deklarowanej akcji

1. **Sprawdzenie i rezerwacja akcji.** Zweryfikuj aktualną fazę, prawo do wykonania, koszt, dostępność karty/źródła, liczbę ataków, Prowokację, cele i niezbędne wybory. Niepoprawna akcja nie zmienia stanu. Po poprawnej deklaracji ataku wykorzystaj jedno prawo ataku, nawet jeśli zwykłe uderzenie potem nie nastąpi.
2. **Zmiana stanu rozpoczynająca akcję.** Wystawienie przenosi kartę z ręki na prawe skrajne pole (a zastępowanie przenosi wskazaną jednostkę do cmentarza **bez śmierci i nagrody**). Aktualizuj pozycje, aktywne stałe aury i uprawnienia. Zmiana ustawienia może stworzyć pojedyncze, zdarzeniowe wyzwalacze pasywne (np. pierwszy raz naprzeciw Trębacza).
3. **Efekt główny przed walką.** Dla `PLAY_CARD` uruchom „Przy wystawieniu”; dla `ATTACK` uruchom „Przy ataku”. Dla pozostałych akcji — ich własny efekt bezpośredni. Nieaktywna (ogłuszona/wyciszona) jednostka nie uruchamia zdolności. Efekt złożony wykonuje własne kroki w kolejności tekstu.
4. **Reakcje na zdarzenie.** Rozstrzygnij pasywne reakcje obrońcy lub innych jednostek na zdarzenie, jeśli ich warunek zaszedł i jednostka wciąż może użyć zdolności (np. odwet przy deklaracji ataku, po efekcie „Przy ataku”, lecz przed zwykłym uderzeniem). Reakcja nigdy nie wznawia już zakończonego efektu.
5. **Standardowa walka** tylko jeśli po etapach 3–4 atakujący i deklarowany cel wciąż istnieją, a atak jest dopuszczalny. Walka jednostka–jednostka zadaje sobie obrażenia **jednocześnie**; bohater nie kontratakuje. Jeśli cel lub atakujący zniknął wcześniej, zwykła walka jest anulowana i **nie dobiera się nowego celu**.
6. **Pojedyncza fala konsekwencji.** Nałóż obrażenia, leczenie, statusy i modyfikacje, uwzględniając tarczę/pancerz; następnie wykryj wszystkie jednostki z HP ≤ 0 **w jednym przeglądzie**. Jednoczesne zgony tworzą jedną grupę. Wypłać nagrody za rzeczywiste zgony i pierwsze spadki HP bohaterów przez progi. Po usunięciu jednostek przelicz aury i pozycje.
7. **„Przy śmierci” z tej samej grupy uruchamia się razem.** Zrób migawkę umierających jednostek z momentu śmierci; ogłuszone i wyciszone nie dodają efektu. Pozostałe zdolności dostają cele i deklaracje na tym samym stanie początkowym grupy, a następnie ich rezultaty tworzą **jedną wspólną falę**. Żaden skutek pierwszego efektu śmierci nie odbiera drugiemu prawa uruchomienia w tej grupie. Nowe zgony powstałe w tej fali stanowią **kolejną grupę**, nie tę samą.
8. **Kaskada aż do uspokojenia.** Dla każdej nowej grupy powtórz wykrycie śmierci → wyzwalacze → konsekwencje → aktualizację aur i statusów. Stan przelicza się po każdej **całej** fali, nigdy w połowie równoczesnej grupy. Dopiero gdy kolejka jest pusta, przyjmij następną deklarację gracza.
9. **Sprawdzenie końca meczu** po każdej zamkniętej fali. Gdy jeden bohater osiągnął HP ≤ 0, od razu kończ mecz i odrzuć zdarzenia niewchodzące jeszcze do tej fali. Gdy **obaj** zeszli do HP ≤ 0 w tej samej fali — zastosuj uzgodniony tie-break. Nie traktuj zgonów w różnych falach jako jednoczesnych.

### 7.2. Reguły wspólne dla wszystkich fal

- **Kolejność przy identycznym priorytecie (o ile nie jest to fala jednoczesna):** najpierw zdolność jednostki wykonującej zadeklarowaną akcję, potem reakcje celu, dalej pozostałe efekty. W obrębie tej samej grupy kolejka od **lewej do prawej** dla bieżącego gracza, następnie od lewej do prawej dla rywala. Ostateczny remis rozstrzyga **unikalny `instance_id`**, nie nazwa ani archetyp. Przy automatycznym wskazaniu celu z remisem wybierz **najbardziej lewy legalny cel**.
- **Jednoczesność oznacza migawkę i zbiorowy skutek.** W jednej grupie przygotuj wszystkie wyniki przed zmianą stanu; obszarowe obrażenia i obrażenia dwustronnej walki nakładaj wspólnie. Gdy kilka efektów sięga po ten sam **zużywalny** zasób (np. jedyną tarczę), przydziel go według powyższego stabilnego porządku źródeł, ale nie przerywaj pozostałych efektów tej samej grupy z powodu wcześniejszego śmiertelnego trafienia.
- **Tarcza → redukcja procentowa → pancerz tymczasowy → pancerz trwały → HP.** Tarcza zużywa się dla pierwszego zdarzenia obrażeń o wejściowej wartości co najmniej 1, także gdy redukcja mogłaby dać zero. Trucizna całkowicie omija te warstwy. Redukcje procentowe mnożą się; wynik zaokrąglaj **w dół do całkowitych obrażeń** po obliczeniu redukcji. Dodatkowo sprawdzaj reguły zmiany MAX HP i możliwe zgony po cofnięciu efektów.
- **Cel znika:** gdy legalnie wskazany cel zniknie przed faktycznym wykonaniem danego (nierównoczesnego) kroku, efekt tego kroku przepada. Bez automatycznego ponawiania wyboru. Gdy przy aktywacji brak legalnego celu, pomiń efekt, nie samą kartę.
- **Efekty ciągłe nie wyzwalają się w nieskończoność.** Aury są przeliczanym stanem, nie powtarzanym zagraniem. Pasywne „gdy X po raz pierwszy” rejestrują `trigger_key` dla wskazanego celu i obecności źródła na planszy. Jedno zdarzenie jest obsługiwane przez daną jednostkę tylko raz na spełniony warunek. Zabezpieczenie serwera przed nieskończonym łańcuchem jest błędem walidowanym/logowanym, nie ukrytą zmianą zasad.
- **Czas statusów:** „do końca tury” kończy się w fazie wygaszania wskazanej tury; „do końca najbliższej własnej tury celu” kończy się przy pierwszym takim zakończeniu, **nie wcześniej**. Trucizny i regeneracje przechowują oddzielne `remaining_ticks` i tracą po jednym naliczeniu na właściwych granicach tur. Ogłuszenie blokuje działanie natychmiast, nalicza własne tury kontrolera (także aktualną, jeśli status powstał w tej turze), sumuje niezależne okresy i wygasa na odpowiedniej granicy przed następnymi akcjami. Wyciszenie blokuje zdolności, nie zwykły atak.

### 7.3. Nadrzędne granice tur i rund

- **Początek własnej tury:** (1) odśwież uprawnienia i rozpatrz wygasłe statusy, (2) dobierz do minimum 5, (3) obrażenia od trucizn jako jedną falę na cel, (4) wykonaj ich kaskadę zgonów i ewentualny koniec gry, (5) dopiero wtedy odblokuj akcje.
- **Akcje gracza:** wystawienie i ataki w dowolnej kolejności, ale **każda akcja całkowicie rozstrzygnięta wraz z kolejką** przed następną.
- **Koniec własnej tury:** (1) zdolności „Na koniec tury” działających jednostek od lewej do prawej, **każda z pełną kaskadą przed następną**, (2) regeneracja jako faza z kaskadą, (3) skalowanie wszystkich własnych kart podstawowych, które wciąż są na ręce, (4) wygaszenie efektów przypisanych do końca tej tury, przeliczenie aur i ewentualna kaskada.
- **Po obu turach:** koniec pełnej rundy → obaj dostają +1 monetę → jeżeli numer rundy jest wielokrotnością 3, aukcja (gdy katalog aukcyjny zostanie wdrożony). Przejście do następnej fazy tylko przy pustej kolejce.

**To jedyna nadrzędna procedura rozstrzygania.** Nie otwieramy od nowa dyskusji o kolejności dla poszczególnych archetypów; każdy nowy efekt podlega tej procedurze i ma tylko opis typu, celu, czasu trwania oraz wyniku.

## 8. Modyfikatory, pancerz i tarcza

- Dodatnie zmiany MAX HP zwiększają równocześnie aktualne HP o tę samą wartość. Ujemne MAX HP ogranicza aktualne HP do nowego pułapu, ale nie zadaje dodatkowych obrażeń samym faktem zmniejszenia maksimum.
- Gdy przemija bonus MAX HP, znika też odpowiadająca premia aktualnego HP (może to uśmiercić jednostkę). Wygaśnięcie ujemnego ograniczenia MAX HP nie leczy jednostki.
- Skuteczny ATK nigdy nie spada poniżej zera, ale modyfikatory pod spodem pozostają i mogą ujawnić się po zdjęciu osłabienia. Wiele niezależnych bonusów/malusów może się kumulować.
- Jednostka może posiadać jedną tarczę. Tarcza blokuje zdarzenie obrażeń o wartości wejściowej **co najmniej 1**, przed redukcjami procentowymi, po czym znika. Nie blokuje trucizny.
- Dwie pule pancerza: **tymczasowa zużywana pierwsza**, następnie trwała. Punkty wewnątrz danej puli sumują się. Pancerz nie regeneruje się wskutek leczenia.
- Wielokrotne procentowe redukcje obrażeń (aukcyjne) mnożą się, a po zaokrągleniu mogą dać 0. Szczegóły zaokrągleń pozostają do zapisania w specyfikacji serwera.
- Pancerz i tarcza mogą dotyczyć bohaterów, jeśli wskazuje ich zdolność. Trucizna ignoruje tarcze, pancerz i redukcje.

## 9. Statusy i czasy trwania

**Trucizna:** obrażenia zachodzą po dobraniu kart na początku tury kontrolera zatrutej jednostki, przed jego akcjami. Wiele trucizn kumuluje wartości obrażeń jako jedno zdarzenie, lecz zachowuje osobne czasy trwania. Ignoruje wszystkie obrony. Szczególne ograniczenie S32: od jednego źródła nie dokłada się drugiej aktywnej porcji trucizny na ten sam cel.

**Regeneracja:** uruchamiana po zdolnościach końca tury, przed skalowaniem ręki. Osobne porcje zachowują osobne okresy, a wysokości leczenia sumują się; nie przekraczają MAX HP.

**Ogłuszenie:** natychmiast uniemożliwia ataki i wszystkie zdolności, w tym wyzwalane po śmierci. Czas liczy własne tury kontrolera; nałożone podczas jego bieżącej tury wlicza już tę turę. Czas trwania z wielu ogłuszeń może się kumulować. Konkretna karta S95 nie może ponawiać ogłuszenia tego samego celu w dwóch następujących po sobie własnych turach źródła.

**Wyciszenie:** blokuje zdolności własne jednostki (również pasywne/taunt wbudowany w kartę), ale nie blokuje zwykłego ataku. Nie usuwa innych, niezależnie nałożonych statusów. Zewnętrznie nadana Prowokacja jest statusem, a nie wrodzoną zdolnością.

**Odporność:** usuwa już istniejące odpowiednie statusy i zapobiega ponownemu nałożeniu ich przez czas działania. Zakres odporności wynika z karty.

**Prowokacja:** jeśli aktywna, przeciwnik atakuje wyłącznie jednostki z aktywną prowokacją. Nie nadaje odporności na zdolności niewykonujące ataku.

**Oczyszczanie:** podstawowy wariant usuwa wszystkie czasowe negatywy z własnej jednostki lub czasowe pozytywy z wrogiej, zgodnie z tekstem karty. Bardziej zaawansowane warianty zdolności aukcyjnych mogą usuwać również statusy bez daty końcowej, a na najwyższym poziomie także trwałe modyfikacje i zdobyte wcześniej skalowanie.

**Wyjście z planszy:** usuwa statusy i tymczasowe/trwałe w sensie „dopóki na planszy” modyfikacje przypisane jednostce; resetuje także przyrost skalowania kart podstawowych. Przejęcie jednostki zachowuje jej rany i niezależne statusy, ale odczepia aury poprzedniego właściciela.

## 10. Skalowanie podstawowych kart na ręce

**W KAŻDEJ własnej turze zakończonej z kartą na ręce** rosną jej statystyki o sumę +2 punktów, według indywidualnego profilu: ofensywny (+2 ATK/+0 MAX HP), defensywny (+0 ATK/+2 MAX HP), zrównoważony (+1 ATK/+1 MAX HP). Nie rosną podczas tury przeciwnika, leżenia na planszy, w stosie dobierania ani na cmentarzu. Wzrost jest bez limitu. Każdy egzemplarz skaluje się niezależnie.

**Po KAŻDYCH 3 własnych turach** tej samej karty na ręce rośnie ponadto jej zdolność. Dla liczbowych obrażeń, leczenia, premii/pomniejszenia ATK i MAX HP, pancerza, trucizny oraz regeneracji roboczy wzrost to zwykle +1 do odpowiedniej wartości, dokładnie według pola `scaling` danej karty.

| Rodzina cechy | Dodatkowy efekt co 3 tury na ręce |
|---|---|
| Szybki atak | +2 ATK oraz +1 MAX HP, oprócz standardowego +2 pkt/turę |
| Podwójny atak | +2 ATK, oprócz standardowego +2 pkt/turę |
| Tarcza | +3 MAX HP, bez dodatkowych tarcz |
| Prowokacja | +3 MAX HP, bez zmiany działania prowokacji |

**Ostateczna wspólna reguła ulepszeń jakościowych co 3 własne tury na ręce (od v15):**

| Rodzina | Premia za każdy ukończony próg (`k=floor(t/3)`) | Co NIE wzrasta |
|---|---|---|
| **Ogłuszenie** | +1 bezpośrednich obrażeń przy skutecznym nałożeniu ogłuszenia na legalny cel | Bez wydłużania ogłuszenia i bez kolejnych celów |
| **Oczyszczanie** | +1 leczenia celu sojuszniczego ALBO +1 obrażenie celu wrogiego **jeśli rzeczywiście usunięto co najmniej jeden stosowny efekt** | Bez poszerzania zakresu oczyszczania |
| **Odporność** | +1 trwałego pancerza chronionemu celowi, za każdy próg, **jednorazowo przy pierwszej skutecznej aktywacji odporności po wystawieniu źródła** | Bez zmiany listy blokowanych statusów i bez wielokrotnego pancerza na kolejnych wyzwoleniach tej samej karty |

Premie są **dodatkowe** do standardowego +2 łącznych punktów ATK/MAX HP na każdą własną turę na ręce. Wartość `k` zostaje zamrożona przy wystawieniu danej karty. Ulepszenie nie działa, jeśli zdolność jest zablokowana (np. ogłuszeniem) lub nie ma legalnego celu. Dla zdolności pasywnej pierwszą aktywacją może być uruchomienie aury przy wystawieniu; dla zdolności „Przy śmierci” pierwszą aktywacją jest zdarzenie śmierci, więc chroniony cel musi być inną jednostką, która nadal znajduje się na planszy.

**Wzór do implementacji:** przy `t` własnych zakończonych turach w ręce i `k=floor(t/3)` progach: `ATK(t)=ATK0 + t*g_ATK + k*bonus_cechy_ATK`, `MAX_HP(t)=HP0+t*g_HP+k*bonus_cechy_HP`. Zdolność opisuje osobno funkcja `ability_level=k`; nie wszystkie zdolności są skalarne. Po zagraniu nie przybywają kolejne punkty wskutek starzenia na ręce.

## 11. Monety i nagrody

| Zdarzenie | Monety |
|---|---:|
| Start jako pierwszy gracz | 0 |
| **Start jako drugi gracz** | **3** |
| Każda pełna runda (każdemu graczowi) | +1 |
| Zabicie jednostki podstawowej / aukcyjnej podstawowej | +1 dla przeciwnika obecnego właściciela |
| Zabicie jednostki aukcyjnej rzadkiej | +2 dla przeciwnika obecnego właściciela |
| Zabicie jednostki aukcyjnej legendarnej | +3 dla przeciwnika obecnego właściciela |
| Pierwsze przekroczenie w dół przez 75, 50, 25 HP własnego bohatera | +2 za każdy próg, jednokrotnie |
| Zastąpienie własnej jednostki na pełnej planszy | 0, brak zgonu |

Moneta za zabicie jednostki trafia **do przeciwnika jej aktualnego właściciela**, nawet jeśli źródłem śmiertelnych obrażeń jest sam właściciel. Po przejęciu jednostki jej późniejsza śmierć nagradza przeciwnika nowego właściciela. Progi 75/50/25 nagradzają tylko pierwsze zejście poniżej odpowiedniej granicy, niezależnie od późniejszego leczenia.

## 12. Aukcje — przebieg

1. Po co trzeciej pełnej rundzie i wypłacie +1 monety obojgu graczom pokazuje się trzy **różne** archetypy aukcyjne tego samego poziomu. Pierwsza aukcja ma poziom 1, druga 2 itd., bez ustalonego limitu.
2. Losowanie rzadkości każdej oferty jest niezależne: 60% podstawowa, 30% rzadka, 10% legendarna. Rzadkość wpływa na **funkcjonalność umiejętności**, nie na ilość bazowego ATK/HP lub mnożnik obrażeń.
3. Gracze licytują prawo pierwszego wyboru z podbijaniem co najmniej o jedną monetę. Przy braku płatnej oferty pierwszeństwo darmowego wyboru zmienia się naprzemiennie między aukcjami; na pierwszej przypada graczowi rozpoczynającemu cały mecz.
4. Zwycięzca płaci zwycięską kwotę, bierze jeden z trzech przedmiotów; przeciwnik bierze inny **bez opłaty**. Trzecia karta nie jest rozdawana, wraca do puli aukcyjnej.
5. Karty trafiają natychmiast na rękę; limit pięciu kart ręki nie istnieje. Gdy zostaną zdobyte, zachowują poziom i rzadkość z danej aukcji; nie skalują się później w ręce.
6. Wersja podstawowa płatnej zdolności ma jedno użycie na egzemplarz w meczu, rzadka jedno na własną turę, legendarna dowolną liczbę użyć w ramach dostępnych monet. Koszt jednostkowy określi przyszły katalog kart.

**DO USTALENIA**: finalny katalog około 36 unikatowych aukcyjnych archetypów, precyzyjne koszty płatnych aktywacji, algorytm licytacji w serwerze oraz poziomowanie parametrów każdej karty. `prototype/` zawiera wyłącznie 12 testowych pozycji i uproszczony algorytm ofert.

## 13. Unikatowe mechaniki aukcyjne — uzgodnione ramy

**Wskrzeszenie:** z cmentarza bezpośrednio na prawe skrajne wolne pole planszy, pełne HP, brak efektu „Przy wystawieniu”, brak wykorzystania limitu zagrania karty, obowiązuje choroba przywołania.

**Przejęcie:** tylko gdy nowy kontroler ma wolne pole. Jednostka zmienia właściciela na stałe, trafia na jego planszę na prawo; nie atakuje do następnej własnej tury nowego kontrolera. Zachowuje obrażenia, własne modyfikatory i statusy z niezależnych źródeł; przestają działać aury strony poprzedniej, zaczynają możliwe aury nowej. Po śmierci trafia do cmentarza nowego właściciela.

**Kopiowanie:** podstawowa kopia przyjmuje bazowe statystyki i rany celu, bez bonusów/statusów; rzadka przejmuje całość statusów i modyfikacji; legendarna tylko pozytywne wraz z ranami. Kopia dziedziczy archetyp, rzadkość i poziom celu, ale stanowi niezależną prywatną kartę. Kopia trafiająca do ręki przy pierwszym wystawieniu ma pełne HP; kopia przywołana bezpośrednio na planszę zachowuje rany celu. Własne zdolności kopii na wejściu są wyciszone; status można oczyścić, w przeciwnym razie znika przy opuszczeniu planszy.

**Oczyszczanie zaawansowane:** podstawowe usuwa czasowe statusy; rzadkie również statusy bez określonego wygaśnięcia; legendarne potrafi zresetować trwałe modyfikacje do bazowej wartości, a także wcześniejsze skalowanie na ręce. Przy resetowaniu statystyk bieżące HP nie rośnie, jedynie zostaje ograniczone do aktualnego maksimum.

**Inne zarezerwowane mechaniki aukcji:** specjalne przyznawanie monet, dobieranie kart, redukcja obrażeń, płatne zdolności, efekty ciszy/wyciszenia. Nie są dostępne w puli startowej.

## 14. Koniec meczu, jednoczesny zgon i tie-break

Mecz kończy się natychmiast po pierwszym zgonie bohatera. Jeśli w tym samym rozstrzygnięciu obaj mają HP ≤ 0, kolejność wyboru zwycięzcy jest następująca: (1) wyższy końcowy wynik HP bohatera, dopuszczalne wartości ujemne; (2) więcej kart łącznie na ręce i w prywatnym stosie dobierania; (3) mocniejsza jednostka na planszy według **ATK + aktualne HP** (maksimum pośród własnych jednostek); (4) gdy nadal remis, wygrywa **drugi gracz**. Nie dopuszczamy remisu.

## 15. Wszystkie 70 kart — kompletny katalog v13, obowiązujący dla v14

Ta tabela ma odzwierciedlać rzeczywisty plik źródłowy `data/cards_base_70.json` bez skrótów statystyk. ATK/MAX HP to statystyki **na karcie bez przetrzymywania na ręce**. Nazwy nie oznaczają innych statystyk niż zapisane w danych. Zmiana gospodarki +3 monet nie zmieniła samych 70 kart.

### 15.1. Elfy — Przy wystawieniu

| ID | Karta | Rodzina | ATK | MAX HP | Profil wzrostu na ręce |
|---|---|---|---:|---:|---|
| S01 | Mag Zorzy | Obrażenia | 1 | 4 | +1 ATK / +1 HP na turę |
| S02 | Kapłanka Srebrnego Blasku | Leczenie | 3 | 5 | +0 ATK / +2 HP na turę |
| S04 | Tkacz Run | ATK ± | 1 | 4 | +2 ATK / +0 HP na turę |
| S08 | Mag Tkanki Życia | MAX HP ± | 2 | 7 | +0 ATK / +2 HP na turę |
| S03 | Zaklinacz Runicznej Zbroi | Pancerz | 2 | 7 | +0 ATK / +2 HP na turę |
| S05 | Strażniczka Księżycowej Pieczęci | Tarcza | 3 | 6 | +0 ATK / +2 HP na turę |
| S58 | Alchemik Jadowych Korzeni | Trucizna | 1 | 5 | +2 ATK / +0 HP na turę |
| S59 | Tkaczka Uśpienia | Ogłuszenie | 1 | 6 | +1 ATK / +1 HP na turę |
| S60 | Druid Odnowy | Regeneracja | 3 | 6 | +0 ATK / +2 HP na turę |
| S61 | Władczyni Leśnych Więzów | Prowokacja | 3 | 7 | +0 ATK / +2 HP na turę |
| S07 | Kapłanka Oczyszczenia | Oczyszczanie | 2 | 6 | +1 ATK / +1 HP na turę |
| S64 | Strażnik Zaklęć Ochronnych | Odporność | 4 | 6 | +0 ATK / +2 HP na turę |
| S66 | Mag Migotliwego Kroku | Szybki atak | 2 | 4 | +2 ATK / +0 HP na turę |
| S67 | Zaklinacz Podwójnego Uderzenia | Podwójny atak | 1 | 5 | +2 ATK / +0 HP na turę |

**S01 — Mag Zorzy** · Obrażenia · 1 ATK / 4 HP  
- Efekt: Zadaj 3 obrażenia wybranej wrogiej jednostce.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do obrażeń zdolności (za każdy ukończony próg).  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S02 — Kapłanka Srebrnego Blasku** · Leczenie · 3 ATK / 5 HP  
- Efekt: Ulecz wybraną sojuszniczą jednostkę lub własnego bohatera o 4 HP.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do leczenia ze zdolności.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S04 — Tkacz Run** · ATK ± · 1 ATK / 4 HP  
- Efekt: Wybierz: przyznaj własnej jednostce +1 ATK albo nałóż −1 ATK na wrogą jednostkę; efekt trwa do opuszczenia planszy przez cel.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu premii lub osłabienia ATK.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S08 — Mag Tkanki Życia** · MAX HP ± · 2 ATK / 7 HP  
- Efekt: Wybierz: przyznaj własnej jednostce +4 MAX HP i +4 aktualnego HP albo zmniejsz MAX HP wrogiej jednostki o 4 (aktualne HP ogranicz do nowego maksimum). Efekt trwa do opuszczenia planszy przez cel.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu zmiany MAX HP.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S03 — Zaklinacz Runicznej Zbroi** · Pancerz · 2 ATK / 7 HP  
- Efekt: Przyznaj 4 trwałego pancerza wybranej sojuszniczej jednostce.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do pancerza przyznanego/odebranego przez zdolność.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S05 — Strażniczka Księżycowej Pieczęci** · Tarcza · 3 ATK / 6 HP  
- Efekt: Przyznaj tarczę wybranej sojuszniczej jednostce i 1 trwałego pancerza temu samemu celowi.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (nie zwiększaj liczby tarcz).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S58 — Alchemik Jadowych Korzeni** · Trucizna · 1 ATK / 5 HP  
- Efekt: Nałóż na wybraną wrogą jednostkę truciznę: 2 obrażenia przez 2 jej własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNYCH obrażeń z jednej porcji trucizny; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S59 — Tkaczka Uśpienia** · Ogłuszenie · 1 ATK / 6 HP  
- Efekt: Ogłusz wybraną wrogą jednostkę na 1 jej własną turę i zadaj jej 1 obrażenie.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: zdolność przy nałożeniu ogłuszenia zadaje dodatkowo +1 obrażenie; czas ogłuszenia nadal 1 własna tura.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S60 — Druid Odnowy** · Regeneracja · 3 ATK / 6 HP  
- Efekt: Nałóż na wybraną sojuszniczą jednostkę regenerację 3 HP przez 2 jej własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNEGO leczenia z jednej porcji regeneracji; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S61 — Władczyni Leśnych Więzów** · Prowokacja · 3 ATK / 7 HP  
- Efekt: Nadaj wybranej sojuszniczej jednostce prowokację do jej opuszczenia planszy.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (czas prowokacji bez zmian).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S07 — Kapłanka Oczyszczenia** · Oczyszczanie · 2 ATK / 6 HP  
- Efekt: Usuń z wybranej własnej jednostki wszystkie tymczasowe negatywne efekty albo z wrogiej wszystkie tymczasowe pozytywne efekty; dodatkowo ulecz własny cel o 1 HP, jeżeli taki był wybrany.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: za każde użyteczne oczyszczenie ulecz własny cel o dodatkowe 1 HP lub zadaj wrogiemu celowi dodatkowe 1 obrażenie.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S64 — Strażnik Zaklęć Ochronnych** · Odporność · 4 ATK / 6 HP  
- Efekt: Nadaj wybranej własnej jednostce odporność na truciznę do jej opuszczenia planszy.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: przy pierwszej aktywacji zdolności po wystawieniu przyznaj dodatkowo 1 trwałego pancerza chronionej jednostce (za każdy poziom).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S66 — Mag Migotliwego Kroku** · Szybki atak · 2 ATK / 4 HP  
- Efekt: Ta jednostka może zaatakować w turze, w której została wystawiona.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK i +1 MAX HP.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S67 — Zaklinacz Podwójnego Uderzenia** · Podwójny atak · 1 ATK / 5 HP  
- Efekt: Ta jednostka otrzymuje Podwójny atak: może atakować dwa razy w każdej własnej turze do opuszczenia planszy.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK (liczba ataków bez zmian).  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.


### 15.2. Dzikie bestie — Przy ataku

| ID | Karta | Rodzina | ATK | MAX HP | Profil wzrostu na ręce |
|---|---|---|---:|---:|---|
| S09 | Wilk Szponiasty | Obrażenia | 2 | 5 | +2 ATK / +0 HP na turę |
| S10 | Nietoperz Krwiożerca | Leczenie | 2 | 6 | +0 ATK / +2 HP na turę |
| S68 | Dzik Bursztynowych Kłów | ATK ± | 1 | 6 | +2 ATK / +0 HP na turę |
| S69 | Nosorożec Żelaznoskóry | MAX HP ± | 3 | 7 | +0 ATK / +2 HP na turę |
| S12 | Żarłacz Pancerzy | Pancerz | 4 | 5 | +0 ATK / +2 HP na turę |
| S70 | Żółw Rogaty | Tarcza | 3 | 6 | +0 ATK / +2 HP na turę |
| S11 | Jadowita Żmija | Trucizna | 1 | 5 | +2 ATK / +0 HP na turę |
| S15 | Niedźwiedź Grzmotu | Ogłuszenie | 1 | 6 | +1 ATK / +1 HP na turę |
| S71 | Salamandra Odnowy | Regeneracja | 2 | 6 | +0 ATK / +2 HP na turę |
| S72 | Bawół Strażnik | Prowokacja | 2 | 8 | +0 ATK / +2 HP na turę |
| S74 | Lis Oczyszczający | Oczyszczanie | 1 | 6 | +1 ATK / +1 HP na turę |
| S76 | Miodożer Nieugięty | Odporność | 4 | 6 | +0 ATK / +2 HP na turę |
| S78 | Gepard Burzowy | Szybki atak | 2 | 4 | +2 ATK / +0 HP na turę |
| S79 | Dwugłowa Hiena | Podwójny atak | 1 | 5 | +2 ATK / +0 HP na turę |

**S09 — Wilk Szponiasty** · Obrażenia · 2 ATK / 5 HP  
- Efekt: Przed standardową walką zadaj 1 dodatkowe obrażenie celowi ataku.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do obrażeń zdolności (za każdy ukończony próg).  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S10 — Nietoperz Krwiożerca** · Leczenie · 2 ATK / 6 HP  
- Efekt: Przed standardową walką ulecz tę jednostkę o 2 HP.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do leczenia ze zdolności.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S68 — Dzik Bursztynowych Kłów** · ATK ± · 1 ATK / 6 HP  
- Efekt: Przed standardową walką wybierz: przyznaj sobie +1 ATK albo nałóż −1 ATK na atakowaną wrogą jednostkę, do końca bieżącej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu premii lub osłabienia ATK.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S69 — Nosorożec Żelaznoskóry** · MAX HP ± · 3 ATK / 7 HP  
- Efekt: Przed standardową walką wybierz: przyznaj sobie +1 MAX HP i +1 aktualnego HP albo obniż MAX HP atakowanej jednostki o 1 do końca jej najbliższej własnej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu zmiany MAX HP.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S12 — Żarłacz Pancerzy** · Pancerz · 4 ATK / 5 HP  
- Efekt: Przed standardową walką usuń do 2 punktów pancerza z celu ataku.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do pancerza przyznanego/odebranego przez zdolność.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S70 — Żółw Rogaty** · Tarcza · 3 ATK / 6 HP  
- Efekt: Przed standardową walką daj sobie 1 tarczę, jeśli jeszcze jej nie posiadasz.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (nie zwiększaj liczby tarcz).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S11 — Jadowita Żmija** · Trucizna · 1 ATK / 5 HP  
- Efekt: Nałóż na cel ataku truciznę: 1 obrażenie przez 2 jego własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNYCH obrażeń z jednej porcji trucizny; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S15 — Niedźwiedź Grzmotu** · Ogłuszenie · 1 ATK / 6 HP  
- Efekt: Gdy atakujesz jednostkę, ogłusz ją na 1 jej własną turę przed standardową walką.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: zdolność przy nałożeniu ogłuszenia zadaje dodatkowo +1 obrażenie; czas ogłuszenia nadal 1 własna tura.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S71 — Salamandra Odnowy** · Regeneracja · 2 ATK / 6 HP  
- Efekt: Przed standardową walką nałóż na tę jednostkę regenerację 1 HP przez 2 własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNEGO leczenia z jednej porcji regeneracji; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S72 — Bawół Strażnik** · Prowokacja · 2 ATK / 8 HP  
- Efekt: Przed standardową walką nadaj tej jednostce prowokację do końca jej najbliższej własnej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (czas prowokacji bez zmian).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S74 — Lis Oczyszczający** · Oczyszczanie · 1 ATK / 6 HP  
- Efekt: Gdy atakujesz jednostkę, usuń z niej wszystkie tymczasowe pozytywne efekty przed standardową walką.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: za każde użyteczne oczyszczenie ulecz własny cel o dodatkowe 1 HP lub zadaj wrogiemu celowi dodatkowe 1 obrażenie.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S76 — Miodożer Nieugięty** · Odporność · 4 ATK / 6 HP  
- Efekt: Przed standardową walką zyskaj odporność na ogłuszenie do końca własnej najbliższej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: przy pierwszej aktywacji zdolności po wystawieniu przyznaj dodatkowo 1 trwałego pancerza chronionej jednostce (za każdy poziom).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S78 — Gepard Burzowy** · Szybki atak · 2 ATK / 4 HP  
- Efekt: Przed standardową walką nadaj wybranej innej sojuszniczej jednostce wystawionej w tej turze możliwość atakowania już teraz.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK i +1 MAX HP.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S79 — Dwugłowa Hiena** · Podwójny atak · 1 ATK / 5 HP  
- Efekt: Gdy wykonujesz pierwszy atak w tej turze, otrzymaj Podwójny atak do końca bieżącej tury: możesz zaatakować drugi raz.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK (liczba ataków bez zmian).  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.


### 15.3. Potwory — Przy śmierci

| ID | Karta | Rodzina | ATK | MAX HP | Profil wzrostu na ręce |
|---|---|---|---:|---:|---|
| S21 | Widmo Otchłani | Obrażenia | 1 | 4 | +2 ATK / +0 HP na turę |
| S17 | Duch Ostatniej Łaski | Leczenie | 3 | 8 | +0 ATK / +2 HP na turę |
| S23 | Klątwonosiciel | ATK ± | 1 | 3 | +2 ATK / +0 HP na turę |
| S81 | Krwawy Homunkulus | MAX HP ± | 4 | 7 | +0 ATK / +2 HP na turę |
| S82 | Golem Grobowy | Pancerz | 3 | 7 | +0 ATK / +2 HP na turę |
| S20 | Strażnik Mauzoleum | Tarcza | 4 | 7 | +0 ATK / +2 HP na turę |
| S83 | Nosiciel Plagi | Trucizna | 1 | 5 | +2 ATK / +0 HP na turę |
| S84 | Banshee Krzyku | Ogłuszenie | 1 | 4 | +1 ATK / +1 HP na turę |
| S85 | Życiodajne Widmo | Regeneracja | 3 | 6 | +0 ATK / +2 HP na turę |
| S86 | Trupi Wartownik | Prowokacja | 3 | 9 | +0 ATK / +2 HP na turę |
| S87 | Widmo Rozproszenia | Oczyszczanie | 1 | 6 | +1 ATK / +1 HP na turę |
| S88 | Grobowy Antymag | Odporność | 4 | 7 | +0 ATK / +2 HP na turę |
| S90 | Koszmar Błyskawic | Szybki atak | 2 | 4 | +2 ATK / +0 HP na turę |
| S91 | Dwuszczęki Horror | Podwójny atak | 1 | 5 | +2 ATK / +0 HP na turę |

**S21 — Widmo Otchłani** · Obrażenia · 1 ATK / 4 HP  
- Efekt: Zadaj 4 obrażenia wrogiemu bohaterowi.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do obrażeń zdolności (za każdy ukończony próg).  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S17 — Duch Ostatniej Łaski** · Leczenie · 3 ATK / 8 HP  
- Efekt: Ulecz własnego bohatera o 6 HP.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do leczenia ze zdolności.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S23 — Klątwonosiciel** · ATK ± · 1 ATK / 3 HP  
- Efekt: Wybierz: przyznaj pozostałej własnej jednostce +2 ATK albo nałóż −2 ATK na wrogą jednostkę; efekt trwa do opuszczenia planszy przez cel.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu premii lub osłabienia ATK.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S81 — Krwawy Homunkulus** · MAX HP ± · 4 ATK / 7 HP  
- Efekt: Wybierz: przyznaj pozostałej własnej jednostce +5 MAX HP i +5 aktualnego HP albo zmniejsz MAX HP wrogiej jednostki o 5. Efekt trwa do opuszczenia planszy przez cel.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu zmiany MAX HP.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S82 — Golem Grobowy** · Pancerz · 3 ATK / 7 HP  
- Efekt: Przyznaj 6 trwałego pancerza wybranej pozostałej sojuszniczej jednostce.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do pancerza przyznanego/odebranego przez zdolność.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S20 — Strażnik Mauzoleum** · Tarcza · 4 ATK / 7 HP  
- Efekt: Przyznaj tarczę wybranej pozostałej sojuszniczej jednostce i 2 trwałego pancerza temu samemu celowi.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (nie zwiększaj liczby tarcz).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S83 — Nosiciel Plagi** · Trucizna · 1 ATK / 5 HP  
- Efekt: Nałóż na wybraną wrogą jednostkę truciznę: 2 obrażenia przez 3 jej własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNYCH obrażeń z jednej porcji trucizny; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S84 — Banshee Krzyku** · Ogłuszenie · 1 ATK / 4 HP  
- Efekt: Ogłusz wybraną wrogą jednostkę na 1 jej własną turę i zadaj jej 2 obrażenia.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: zdolność przy nałożeniu ogłuszenia zadaje dodatkowo +1 obrażenie; czas ogłuszenia nadal 1 własna tura.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S85 — Życiodajne Widmo** · Regeneracja · 3 ATK / 6 HP  
- Efekt: Nałóż na wybraną pozostałą sojuszniczą jednostkę regenerację 3 HP przez 3 jej własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNEGO leczenia z jednej porcji regeneracji; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S86 — Trupi Wartownik** · Prowokacja · 3 ATK / 9 HP  
- Efekt: Pozostała wybrana sojusznicza jednostka otrzymuje prowokację do swojego opuszczenia planszy.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (czas prowokacji bez zmian).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S87 — Widmo Rozproszenia** · Oczyszczanie · 1 ATK / 6 HP  
- Efekt: Usuń z wybranej pozostałej własnej jednostki wszystkie tymczasowe negatywne efekty oraz przyznaj jej 2 trwałego pancerza.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: za każde użyteczne oczyszczenie ulecz własny cel o dodatkowe 1 HP lub zadaj wrogiemu celowi dodatkowe 1 obrażenie.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S88 — Grobowy Antymag** · Odporność · 4 ATK / 7 HP  
- Efekt: Nadaj wybranej pozostałej własnej jednostce odporność na truciznę i ogłuszenie do jej opuszczenia planszy.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: przy pierwszej aktywacji zdolności po wystawieniu przyznaj dodatkowo 1 trwałego pancerza chronionej jednostce (za każdy poziom).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S90 — Koszmar Błyskawic** · Szybki atak · 2 ATK / 4 HP  
- Efekt: Twoja najbliższa wystawiona jednostka może zaatakować w turze jej wystawienia.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK i +1 MAX HP.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S91 — Dwuszczęki Horror** · Podwójny atak · 1 ATK / 5 HP  
- Efekt: Wybrana pozostała sojusznicza jednostka otrzymuje Podwójny atak do opuszczenia planszy.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK (liczba ataków bez zmian).  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.


### 15.4. Krasnoludy — Na koniec tury

| ID | Karta | Rodzina | ATK | MAX HP | Profil wzrostu na ręce |
|---|---|---|---:|---:|---|
| S27 | Kusznik Runiczny | Obrażenia | 1 | 6 | +1 ATK / +1 HP na turę |
| S25 | Medyk Górniczy | Leczenie | 2 | 7 | +0 ATK / +2 HP na turę |
| S28 | Mistrz Run Bitewnych | ATK ± | 1 | 5 | +2 ATK / +0 HP na turę |
| S93 | Kowal Życiostali | MAX HP ± | 3 | 6 | +0 ATK / +2 HP na turę |
| S26 | Kowal Żelaznej Kuźni | Pancerz | 2 | 6 | +0 ATK / +2 HP na turę |
| S94 | Mistrz Tarczy | Tarcza | 1 | 8 | +0 ATK / +2 HP na turę |
| S32 | Alchemik Kopalnianych Trucizn | Trucizna | 1 | 5 | +2 ATK / +0 HP na turę |
| S95 | Młotnik Wstrząsów | Ogłuszenie | 1 | 6 | +1 ATK / +1 HP na turę |
| S31 | Znachor Klanowy | Regeneracja | 2 | 6 | +0 ATK / +2 HP na turę |
| S96 | Wartownik Szybu | Prowokacja | 2 | 8 | +0 ATK / +2 HP na turę |
| S97 | Czyściciel Run | Oczyszczanie | 1 | 6 | +1 ATK / +1 HP na turę |
| S99 | Górski Odtruwacz | Odporność | 3 | 7 | +0 ATK / +2 HP na turę |
| S101 | Konstruktor Sprężyn | Szybki atak | 2 | 4 | +2 ATK / +0 HP na turę |
| S102 | Mechanik Dwóch Ostrzy | Podwójny atak | 1 | 5 | +2 ATK / +0 HP na turę |

**S27 — Kusznik Runiczny** · Obrażenia · 1 ATK / 6 HP  
- Efekt: Zadaj 1 obrażenie wrogiej jednostce z najniższym aktualnym HP.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do obrażeń zdolności (za każdy ukończony próg).  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S25 — Medyk Górniczy** · Leczenie · 2 ATK / 7 HP  
- Efekt: Ulecz wybraną sojuszniczą jednostkę o 2 HP.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do leczenia ze zdolności.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S28 — Mistrz Run Bitewnych** · ATK ± · 1 ATK / 5 HP  
- Efekt: Wybierz: przyznaj sojuszniczej jednostce +1 ATK albo nałóż −1 ATK na wrogą jednostkę do końca jej najbliższej własnej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu premii lub osłabienia ATK.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S93 — Kowal Życiostali** · MAX HP ± · 3 ATK / 6 HP  
- Efekt: Wybierz: przyznaj sojuszniczej jednostce +1 MAX HP i +1 aktualnego HP albo obniż MAX HP wrogiej jednostki o 1 do końca jej najbliższej własnej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu zmiany MAX HP.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S26 — Kowal Żelaznej Kuźni** · Pancerz · 2 ATK / 6 HP  
- Efekt: Przyznaj 2 tymczasowego pancerza wybranej sojuszniczej jednostce do końca jej najbliższej własnej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do pancerza przyznanego/odebranego przez zdolność.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S94 — Mistrz Tarczy** · Tarcza · 1 ATK / 8 HP  
- Efekt: Daj wybranej sojuszniczej jednostce 1 tarczę, jeśli jeszcze jej nie posiada.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (nie zwiększaj liczby tarcz).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S32 — Alchemik Kopalnianych Trucizn** · Trucizna · 1 ATK / 5 HP  
- Efekt: Na koniec tury nałóż na wybraną wrogą jednostkę truciznę: 1 obrażenie przez 2 jej własne tury. Jedna jednostka może mieć tylko jedną aktywną truciznę pochodzącą od tego Alchemika; trucizny różnych źródeł nadal się sumują.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNYCH obrażeń z jednej porcji trucizny; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S95 — Młotnik Wstrząsów** · Ogłuszenie · 1 ATK / 6 HP  
- Efekt: Na koniec tury ogłusz wrogą jednostkę z najniższym aktualnym ATK na 1 jej własną turę. Nie możesz ogłuszać tej samej jednostki w dwóch kolejnych własnych turach.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: zdolność przy nałożeniu ogłuszenia zadaje dodatkowo +1 obrażenie; czas ogłuszenia nadal 1 własna tura.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S31 — Znachor Klanowy** · Regeneracja · 2 ATK / 6 HP  
- Efekt: Nałóż na wybraną sojuszniczą jednostkę regenerację 1 HP przez 2 jej własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNEGO leczenia z jednej porcji regeneracji; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S96 — Wartownik Szybu** · Prowokacja · 2 ATK / 8 HP  
- Efekt: Nadaj wybranej sojuszniczej jednostce prowokację do końca jej najbliższej własnej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (czas prowokacji bez zmian).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S97 — Czyściciel Run** · Oczyszczanie · 1 ATK / 6 HP  
- Efekt: Usuń wszystkie tymczasowe negatywne efekty z wybranej sojuszniczej jednostki.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: za każde użyteczne oczyszczenie ulecz własny cel o dodatkowe 1 HP lub zadaj wrogiemu celowi dodatkowe 1 obrażenie.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S99 — Górski Odtruwacz** · Odporność · 3 ATK / 7 HP  
- Efekt: Nadaj wybranej sojuszniczej jednostce odporność na truciznę do końca jej najbliższej własnej tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: przy pierwszej aktywacji zdolności po wystawieniu przyznaj dodatkowo 1 trwałego pancerza chronionej jednostce (za każdy poziom).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S101 — Konstruktor Sprężyn** · Szybki atak · 2 ATK / 4 HP  
- Efekt: Na koniec tury wybierz jedną kartę jednostki z ręki; otrzymuje Szybki atak wyłącznie jeśli wystawisz ją w swojej następnej turze. Bonus nie przechodzi na kolejne tury i nie kumuluje się.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK i +1 MAX HP.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S102 — Mechanik Dwóch Ostrzy** · Podwójny atak · 1 ATK / 5 HP  
- Efekt: Na koniec tury wybrana sojusznicza jednostka otrzymuje Podwójny atak wyłącznie w swojej najbliższej własnej turze; premia nie kumuluje się.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK (liczba ataków bez zmian).  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.


### 15.5. Ludzie — Pasywna

| ID | Karta | Rodzina | ATK | MAX HP | Profil wzrostu na ręce |
|---|---|---|---:|---:|---|
| S103 | Weteran Odwetu | Obrażenia | 4 | 5 | +0 ATK / +2 HP na turę |
| S104 | Kapelan Garnizonu | Leczenie | 4 | 5 | +0 ATK / +2 HP na turę |
| S34 | Chorąży Królewskiej Kompanii | ATK ± | 1 | 6 | +2 ATK / +0 HP na turę |
| S35 | Komendant Straży | MAX HP ± | 3 | 7 | +0 ATK / +2 HP na turę |
| S105 | Zbrojmistrz Garnizonu | Pancerz | 2 | 7 | +0 ATK / +2 HP na turę |
| S106 | Chorąży z Pawężą | Tarcza | 3 | 7 | +0 ATK / +2 HP na turę |
| S107 | Chemik Wojskowy | Trucizna | 2 | 6 | +2 ATK / +0 HP na turę |
| S108 | Królewski Trębacz | Ogłuszenie | 1 | 6 | +1 ATK / +1 HP na turę |
| S109 | Kapelan Odnowy | Regeneracja | 2 | 7 | +0 ATK / +2 HP na turę |
| S33 | Strażnik Bram | Prowokacja | 2 | 8 | +0 ATK / +2 HP na turę |
| S111 | Chirurg Frontowy | Oczyszczanie | 2 | 7 | +1 ATK / +1 HP na turę |
| S39 | Alchemik Antytoksyk | Odporność | 4 | 7 | +0 ATK / +2 HP na turę |
| S114 | Instruktor Błyskawicznego Natarcia | Szybki atak | 1 | 4 | +2 ATK / +0 HP na turę |
| S115 | Mistrz Dwóch Ostrzy | Podwójny atak | 1 | 5 | +2 ATK / +0 HP na turę |

**S103 — Weteran Odwetu** · Obrażenia · 4 ATK / 5 HP  
- Efekt: Każda wroga jednostka, która atakuje tę jednostkę, otrzymuje 1 obrażenie przed standardową walką.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do obrażeń zdolności (za każdy ukończony próg).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S104 — Kapelan Garnizonu** · Leczenie · 4 ATK / 5 HP  
- Efekt: Dopóki ta jednostka jest na planszy, każda własna jednostka odzyskuje dodatkowe 2 HP podczas leczenia ze zdolności.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do leczenia ze zdolności.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S34 — Chorąży Królewskiej Kompanii** · ATK ± · 1 ATK / 6 HP  
- Efekt: Wybierz tryb aury przy wystawieniu: najbliższa inna sojusznicza jednostka (preferuj po prawej, w przeciwnym razie po lewej) ma +1 ATK ALBO wroga jednostka bezpośrednio naprzeciw Chorążego ma −1 ATK. Tryb jest stały do opuszczenia planszy.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu premii lub osłabienia ATK.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S35 — Komendant Straży** · MAX HP ± · 3 ATK / 7 HP  
- Efekt: Wybierz tryb aury przy pojawieniu się na planszy: pozostałe własne jednostki mają +1 MAX HP i +1 aktualnego HP ALBO wrogie mają −1 MAX HP (aktualne HP ogranicz do maksimum), dopóki zdolność działa.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do modułu zmiany MAX HP.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S105 — Zbrojmistrz Garnizonu** · Pancerz · 2 ATK / 7 HP  
- Efekt: Dopóki ta zdolność działa, pozostałe sojusznicze jednostki mają po 2 tymczasowego pancerza ze źródła tej aury; wygaśnięcie aury usuwa tę ochronę.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do pancerza przyznanego/odebranego przez zdolność.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S106 — Chorąży z Pawężą** · Tarcza · 3 ATK / 7 HP  
- Efekt: Dopóki ta zdolność działa, ta jednostka ma tarczę. Tarcza z aury nie odnawia się po zużyciu podczas tego wystawienia.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (nie zwiększaj liczby tarcz).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S107 — Chemik Wojskowy** · Trucizna · 2 ATK / 6 HP  
- Efekt: Gdy wroga jednostka zadaje tej jednostce standardowe obrażenia w walce, otrzymuje truciznę: 1 obrażenie przez 2 własne tury.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNYCH obrażeń z jednej porcji trucizny; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S108 — Królewski Trębacz** · Ogłuszenie · 1 ATK / 6 HP  
- Efekt: Gdy wroga jednostka po raz pierwszy znajdzie się naprzeciw Trębacza, jest ogłuszona na 1 własną turę. Ta sama jednostka nie może być ogłuszona ponownie przez Trębacza podczas jego bieżącego wystawienia.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: zdolność przy nałożeniu ogłuszenia zadaje dodatkowo +1 obrażenie; czas ogłuszenia nadal 1 własna tura.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S109 — Kapelan Odnowy** · Regeneracja · 2 ATK / 7 HP  
- Efekt: Ta jednostka ma regenerację 2 HP na koniec każdej własnej tury, dopóki działa ta zdolność.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: +1 do ŁĄCZNEGO leczenia z jednej porcji regeneracji; czas trwania bez zmian.  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S33 — Strażnik Bram** · Prowokacja · 2 ATK / 8 HP  
- Efekt: Ta jednostka posiada prowokację; wrogie jednostki muszą atakować cele z prowokacją.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +3 MAX HP (czas prowokacji bez zmian).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S111 — Chirurg Frontowy** · Oczyszczanie · 2 ATK / 7 HP  
- Efekt: Dopóki ta zdolność działa, tymczasowe negatywne efekty nakładane na tę jednostkę są natychmiast usuwane.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: za każde użyteczne oczyszczenie ulecz własny cel o dodatkowe 1 HP lub zadaj wrogiemu celowi dodatkowe 1 obrażenie.  
- Standardowy przyrost na ręce: +1 ATK i +1 MAX HP na własną turę.

**S39 — Alchemik Antytoksyk** · Odporność · 4 ATK / 7 HP  
- Efekt: Ta jednostka jest odporna na truciznę; istniejące trucizny zostają usunięte.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: przy pierwszej aktywacji zdolności po wystawieniu przyznaj dodatkowo 1 trwałego pancerza chronionej jednostce (za każdy poziom).  
- Standardowy przyrost na ręce: +0 ATK i +2 MAX HP na własną turę.

**S114 — Instruktor Błyskawicznego Natarcia** · Szybki atak · 1 ATK / 4 HP  
- Efekt: Ta jednostka ma Szybki atak: może atakować od razu po wystawieniu, dopóki zdolność działa.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK i +1 MAX HP.  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

**S115 — Mistrz Dwóch Ostrzy** · Podwójny atak · 1 ATK / 5 HP  
- Efekt: Ta jednostka ma Podwójny atak: może atakować dwa razy w każdej własnej turze, dopóki działa zdolność.  
- Wzmocnienie co 3 własne tury na ręce: Co 3 własne tury na ręce: dodatkowo +2 ATK (liczba ataków bez zmian).  
- Standardowy przyrost na ręce: +2 ATK i +0 MAX HP na własną turę.

## 16. Balans — dwa niezależne wymiary oceny

**Statyczna wycena:** porównujemy hipotetyczną wartość `V0` wystawienia karty od razu i `V3` po trzech pełnych turach na ręce. Heurystyczny agregat `V0 + V3` ma być zbliżony między kartami, ale nie wolno dopasowywać do identycznej sumy kosztem zachowania mechaniki i faktycznych wyników rozgrywek. Oddzielnie kontrolujemy przyrost `V3−V0` i koszt opóźnionego zagrania.

**Empiryczny test kart v13 (UPROSZCZONY SYMULATOR):** po iteracjach balansu wszystkie 70 archetypów znalazło się w przedziale ±4 punktów procentowych oszacowanego indywidualnego wpływu na wynik w tym samym, ograniczonym modelu. Nie jest to dowód równowagi pełnej gry, która potrzebuje finalnych kart aukcyjnych i zasad serwera.

**Symulacje przewagi pierwszego gracza v14 (UPROSZCZONY SYMULATOR):**

| Ustawienia | Liczba partii | Wygrane pierwszego | 95% orientacyjny przedział |
|---|---:|---:|---|
| Aukcje, +1 moneta [reguła] | 1100 | 58.09% | 55.18%–61.01% |
| Aukcje, +3 monety | 1100 | 57.27% | 54.35%–60.20% |

**Zatwierdzona decyzja po tych próbach:** drugi gracz otrzymuje **3 monety** na start, bez bonusowych HP lub pancerza. Testy wariantu 20 pancerza były diagnostyczne i nie tworzą reguły gry. Istotna przewaga pierwszego gracza może nadal istnieć — wymagana walidacja na właściwym silniku i z pełnymi aukcjami.

## 17. Minimalna architektura serwera i model danych

Należy utrzymać *autorytatywny serwer* i deterministyczną kolejkę zdarzeń. Klient wysyła deklaracje działań, ale nie oblicza wyniku walki ani nie może arbitralnie zwiększać monet czy HP.

Proponowane obiekty: `MatchState`, `PlayerState`, `HeroState`, `CardDefinition` (niezmienny archetyp), `CardInstance` (konkretny egzemplarz), `UnitState` (stan na planszy), `EffectInstance` (źródło, cel, typ, stosy, duration, expires_at), `AuctionState` (level, offers, bids, priority), `EventLog` (wszystkie zdarzenia). Każdy egzemplarz musi posiadać unikalny identyfikator, niezależny od identyfikatora archetypu `Sxx`.

Proponowana lista rozkazów klienta: `PLAY_CARD(card_instance_id, replace_unit_id?)`, `ATTACK(attacker_id, target_id)`, `END_TURN`, `MULLIGAN(card_instance_ids)`, `AUCTION_BID(amount)`, `AUCTION_PASS`, `AUCTION_PICK(offer_id)`, `ACTIVATE_PAID_ABILITY(source_id,target_ids)`, `CHOOSE_EFFECT_BRANCH(branch,target_id)`. Każdą komendę waliduj pod kątem fazy, aktywnego gracza, limitów, dostępności pieniędzy, życia celu i możliwości ataku.

Dla powtórek i debugowania stosuj: ziarno RNG, numer rundy/tury, rosnący `event_id`, lokalny `action_id`, lista jednostek w kolejności od lewej do prawej, snapshot przed/po złożonych zdarzeniach oraz wersja definicji kart. Zapis stanów musi odtwarzać historyczne poziomy aukcyjne i zużyte zdolności.

## 18. Proponowane testy akceptacyjne silnika

1. **TEST-01** Nowa gra: pierwszy ma 0 monet, drugi 3, obaj 100/100 HP i 0 pancerza.
2. **TEST-02** Każdy otrzymuje dokładnie 5 kart ręki i 5 w prywatnym stosie dobierania.
3. **TEST-03** Mulligan od 0 do 3 kart; niedozwolone 4 i więcej.
4. **TEST-04** Start tury dobiera do min. 5 kart; brak odrzucania nadmiaru.
5. **TEST-05** Przetasowanie cmentarza, gdy talia pusta, bez kary za pustą pulę.
6. **TEST-06** Maksymalnie jedna zwykła karta z ręki na własną turę.
7. **TEST-07** Nowa jednostka wchodzi na skraj prawego rzędu, kolejność innych się nie zmienia.
8. **TEST-08** Przy 5 jednostkach można zastąpić jednostkę, która jeszcze nie atakowała; zastąpienie nie uruchamia śmierci ani nagrody za kill.
9. **TEST-09** Brak ataku w turze wystawienia bez Szybkiego ataku.
10. **TEST-10** Podwójny atak umożliwia dokładnie dwa ataki, nie trzy.
11. **TEST-11** Szybki atak + Podwójny atak: dokładnie dwa ataki w turze wystawienia.
12. **TEST-12** Prowokacja blokuje ataki jednostek w bohatera i zwykłe wrogie jednostki.
13. **TEST-13** Atak jednostka–jednostka zadaje zwykłe obrażenia jednocześnie.
14. **TEST-14** Efekt Przy ataku może zabić cel przed zwykłymi obrażeniami.
15. **TEST-15** Zdolności na koniec tury wykonują się od lewej do prawej.
16. **TEST-16** Regeneracja przed skalowaniem kart na ręce.
17. **TEST-17** Karta starter z profilem 2/0 po 3 turach na ręce zyskuje +6 ATK i jeden poziom zdolności.
18. **TEST-18** Karta starter z profilem 1/1 po 6 turach zyskuje +6 ATK, +6 MAX HP, dwa poziomy zdolności.
19. **TEST-19** Tarcza po 3 turach na ręce daje dodatkowo +3 HP, a nie kolejną tarczę.
20. **TEST-20** Podwójny atak po 3 turach daje dodatkowo +2 ATK, nie trzeci atak.
21. **TEST-21** Trucizna działa po dobraniu, przed akcjami i omija ochrony.
22. **TEST-22** Tarcza blokuje zdarzenie o wartości wejściowej co najmniej 1 i zużywa ładunek.
23. **TEST-23** Pancerz tymczasowy zużywany przed trwałym.
24. **TEST-24** Ogłuszony nie atakuje ani nie wyzwala własnych zdolności, w tym śmierci.
25. **TEST-25** Czyszczenie czasowych statusów usuwa właściwą kategorię w zależności od własnego/wrogiego celu.
26. **TEST-26** Pierwsze zejście poniżej 75/50/25 HP daje 2 monety za próg tylko raz.
27. **TEST-27** Po każdej pełnej rundzie oba salda zwiększają się o 1 przed aukcją.
28. **TEST-28** Aukcje po 3,6,9... pełnych rundach, nie w połowie rundy.
29. **TEST-29** Za zabicie własnej jednostki monetę otrzymuje przeciwnik obecnego właściciela.
30. **TEST-30** Przejęcie zachowuje rany i niezależne efekty; przenosi kartę do cmentarza nowego właściciela po śmierci.
31. **TEST-31** Wskrzeszenie nie aktywuje zdolności Przy wystawieniu i nie zużywa limitu zagrania.
32. **TEST-32** Podczas remisowej jednoczesnej śmierci obu bohaterów działa pełna sekwencja tie-break.
33. **TEST-33** Karty aukcyjne nie skalują się na ręce, nawet po wielu turach.
34. **TEST-34** 3 monety drugiego gracza są widoczne w UI i dostępne podczas pierwszej aukcji.
35. **TEST-35** Bank centralny ma 70 fizycznych kart: 70 różnych `archetype_id`, dokładnie po 1 egzemplarzu.
36. **TEST-36** Po rozdaniu 10+10 w banku jest 50; dwaj gracze nigdy nie otrzymują tego samego egzemplarza.
37. **TEST-37** Równoczesny mulligan 3+3 wyłącza sześć oddanych egzemplarzy z meczu na stałe; po wymianach bank ma 44 karty, `EXCLUDED_FROM_MATCH` ma 6 kart, ręce mają po 5 kart i łącznie nie ma duplikatów.
38. **TEST-38** Efekt „Przy ataku” rozstrzyga się przed reakcją obrońcy i przed standardową walką; anulowana walka nie cofa zużytego ataku.
39. **TEST-39** Jednoczesny zgon dwóch potworów uruchamia oba aktywne efekty „Przy śmierci” z jednej migawki; nowe zgony są nową falą.
40. **TEST-40** Pasywne aury aktualizują się przy przesunięciu jednostki, ale nie wyzwalają ponownie efektu „po raz pierwszy” na tym samym celu.
41. **TEST-41** Ogłuszenie po `t=6` turach na ręce zadaje +2 bezpośrednich obrażeń, nadal trwa 1 turę.
42. **TEST-42** Oczyszczanie po `t=6`: użyteczne oczyszczenie własnej jednostki zapewnia +2 leczenia; bezużyteczne nie przyznaje bonusu.
43. **TEST-43** Odporność po `t=6`: pierwsza skuteczna aktywacja przyznaje +2 trwałego pancerza; powtórzona aktywacja na tej samej planszy nie przyznaje go ponownie.
44. **TEST-44** W jednej fali tarczę zużywa tylko pierwsze zdarzenie, a pozostałe obrażenia nie są anulowane; rozliczenie jest deterministyczne.
45. **TEST-45** Śmierć jednego bohatera kończy rozgrywkę po zamknięciu bieżącej fali, przed uruchomieniem kolejnej.
46. **TEST-46** Karta oddana w mulliganie jest oznaczona `EXCLUDED_FROM_MATCH` i nie pojawia się w żadnej ręce, talii, cmentarzu ani centralnym banku przez cały mecz.
47. **TEST-47** Po wyczerpaniu prywatnego stosu dobierania przetasowanie cmentarza NIE przywraca kart wyłączonych podczas mulliganu.
48. **TEST-48** Gracze mogą dokonywać wymiany, podejmować działania i licytować bez upływającego licznika; żadne zdarzenie `TIMEOUT`, automatyczna końcówka ani auto-pass nie są emitowane.
49. **TEST-49** Brak reakcji gracza sam w sobie nie zmienia stanu gry i nie kończy meczu; komendy podejmowane później nadal przechodzą normalną walidację.

## 19. Status projektu i prace pozostałe po zamknięciu zasad bazowych (v17)

**Zamknięte i nie wymagają ponownego zatwierdzania przed MVP:** 70 unikatowych fizycznych kart w banku (po 1 na archetyp); mulligan trwale wyłącza oddane egzemplarze dla obu graczy; **brak limitów czasu** we wszystkich fazach; pełna nadrzędna kolejka zdarzeń w sekcji 7; +3 monety drugiego gracza; przyrost statystyk co turę i ulepszenia wszystkich 14 rodzin efektów co 3 tury.

| Priorytet | Rzeczywiście otwarta kwestia |
|---|---|
| KRYTYCZNE NA ETAP AUKCJI | Opracować ostateczne archetypy aukcyjne, warianty rzadkości, koszty i poziomowanie. Nie należy ich implementować w etapie bazowym `AuctionHammer`. |
| WYSOKIE IMPLEMENTACJA | Zaimplementować kolejkę z sekcji 7 i automatyczne testy wszystkich 70 kart, wraz ze współbieżnymi zgonami i łańcuchami. To zadanie programistyczne, nie nowe pytanie o reguły. |
| WYSOKIE IMPLEMENTACJA | Przetestować balans pełnej gry i wpływ +3 monet drugiego gracza na wiernym silniku po dodaniu aukcji. |
| ŚREDNIE IMPLEMENTACYJNE | Techniczne odzyskiwanie sesji po rozłączeniu. **Nie** dodaje żadnego limitu czasu, auto-passa ani przegranej za bezczynność. |
| ŚREDNIE PRODUKTOWE | Czytelność UI/statusów i informowanie o kolejnym progu wzmocnienia karty na ręce. |

**Decyzje projektowe dotyczące podstawowych kart są zamknięte na potrzeby MVP.** Pozycje powyżej to zadania implementacyjne, badawcze i późniejszy katalog aukcyjny, a nie pretekst do ponownego pytania o kolejność zdarzeń, bonus drugiego gracza, kopie startowe lub timery.

Pozostałe priorytety, wygaszanie i tie-breaki rozstrzyga **sekcja 7**, a nie kolejne uznaniowe dopiski przy kartach.

## 20. Sugerowana kolejność prac programistycznych

1. `CardDefinition`, walidacja 70 archetypów (5 frakcji × 14 rodzin) i tworzenie **jednego fizycznego egzemplarza każdego**; zachowaj ID i nie generuj drugiej kopii.
2. Reduktor `MatchState` i testy deterministyczne: tura, zagranie, atak, zgony, statusy.
3. Skalowanie w ręce i testy profili, progów 3/6/9 oraz resetów.
4. Pełna kolejka aktywacji umiejętności; dane deklaratywne / parser umiejętności zamiast polegania wyłącznie na wolnym tekście.
5. Ekonomia (+3 drugi gracz, kill bounty, progi HP, dochód rundy).
6. **Po zamknięciu MVP i odrębnej akceptacji katalogu aukcyjnego:** aukcja oraz instancje z poziomem i rzadkością. W podstawowym MVP nie generuj hipotetycznych ofert.
7. Prosty klient sieciowy oraz autorytatywna walidacja każdej komendy.
8. Agenty do samogry i analizy zmian, replay/logi, A/B zmiennych dotyczących przewagi pierwszego gracza.
9. Po walidacji balansu: UX, grafiki frakcji, onboarding, system rankingowy.

## 21. Historia decyzji (ważne korekty)

- v5: ATK± i MAX HP± połączone w dwie rodziny; monety usunięte z podstawowych kart.
- v6: pięć frakcji przypisanych do momentów aktywacji; „Wściekły” przemianowano na „Podwójny atak”.
- v8: bazowy wzrost karty starter +2 ATK/HP łącznie na każdą własną turę w ręce; zdolność rośnie co trzy takie tury.
- v9: wzmocnienia cech jakościowych: Szybki atak +2 ATK/+1 HP, Podwójny atak +2 ATK, Tarcza/Prowokacja +3 HP co próg.
- v10: zmiana nazewnictwa 75 kart według pięciu frakcji; pomocnicze Value Proposition.
- v11: redukcja ze 75 do **70 archetypów**, po jednej karcie na kombinację momentu i rodziny; `V0 + V3`.
- v12: kalibracja wartości zdolności względem użyteczności i liczby rzeczywistych aktywacji.
- v13: korekty ATK, HP i 10 opisów na podstawie uproszczonych symulacji.
- v14: **drugi gracz otrzymuje na początku 3 monety, nie 1; 0 pancerza bonusowego; 100 HP bez zmian.**
- v15: **pula to dokładnie 70 fizycznych kart bez duplikatów**; jedna nadrzędna deterministyczna kolejka efektów i rozstrzygnięcie trzech ostatnich rodzin skalowania (ogłuszenie, oczyszczanie, odporność).
- v16: **odrzucenie podczas mulliganu usuwa egzemplarz z bieżącego meczu dla obu graczy**; brak timerów mulliganu, tur i aukcji. Bez zmian w 70 kartach i kolejce efektów.
- v17: **zamknięcie specyfikacji podstawowego MVP**; jedna kanoniczna wersja dokumentacji i danych; jawny rozdział pomiędzy zasadami zatwierdzonymi, implementacją silnika i dopiero przyszłym projektem kart aukcyjnych. Nie dokonano zmian statystyk lub tekstów 70 kart.

## 22. Ograniczenia i interpretacja danych

Katalog podstawowy v13 pozostaje kanoniczny co do nazw, statystyk i indywidualnych tekstów wszystkich 70 kart; v14 zmienił początkowe monety drugiego gracza, a v15 zamknął liczbę egzemplarzy i reguły kolejności/skalowania jakościowego. Profil skalowania każdej karty został odczytany z Excela v13. Część tekstów zdolności pozostaje zapisem w języku naturalnym i do produkcyjnego silnika potrzebuje osobnej specyfikacji typowanych efektów. W eksperymentalnym symulatorze nie wszystkie statusy, cele, zmiany pozycji i aukcyjne interakcje działają 1:1 ze specyfikacją.

**W tej wersji nie twierdzimy, że gra jest już zbalansowana ani że istnieje pełny działający silnik.** v13 wyrównał karty w uproszczonym modelu, a test v14 z trzema monetami nadal pokazał przybliżone 57,27% zwycięstw pierwszego (1100 prób). Jest to podstawa do dalszego testowania, nie do kolejnej automatycznej zmiany reguł.

---
**Koniec dokumentu Game Master v17.0.** Dane maszynowe: `data/GAME_MASTER.json`.
