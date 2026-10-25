# Historia zmian — AuctionHammer

Poniżej opisane są **wydania produktu dla graczy**, a nie wszystkie wewnętrzne commity. Zapis `0.9.x` określa wersję gry; tag `build-xxxxxxxx` wskazuje dokładny commit skompilowanego ZIP-a Windows. Nie wszystkie numery pośrednie były publikowane jako osobne wydania.

Pełne szczegóły historycznych mechanik pozostają w [dokumentacji projektu](docs/STATUS_PROJEKTU.md). Instalacja, aktualizacje i kryteria publikacji: [Proces wydań](docs/RELEASE_PROCESS.md).

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
