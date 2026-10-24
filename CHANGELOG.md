# Historia zmian — AuctionHammer

Poniżej opisane są **wydania produktu dla graczy**, a nie wszystkie wewnętrzne commity. Zapis `0.9.x` określa wersję gry; tag `build-xxxxxxxx` wskazuje dokładny commit skompilowanego ZIP-a Windows. Nie wszystkie numery pośrednie były publikowane jako osobne wydania.

Pełne szczegóły historycznych mechanik pozostają w [dokumentacji projektu](docs/STATUS_PROJEKTU.md). Instalacja, aktualizacje i kryteria publikacji: [Proces wydań](docs/RELEASE_PROCESS.md).

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
