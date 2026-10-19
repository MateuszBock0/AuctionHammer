# AuctionHammer 0.9.31 — aktywny katalog aukcyjny v22

> **Uaktualnienie 0.9.32:** naprawiono brak ewolucji rzadkości w trybie v22
> i odrzucanie kart aukcyjnych przez A009 do zwykłego cmentarza.
> [Poprawki, testy i kompatybilność](RELEASE_V22_STABILIZATION_0932.md).
> Pozostałe zasady niniejszego dokumentu pozostają obowiązujące.

**Status: LIVE.** 17 niepowtarzalnych archetypów (A001–A016, A018;
bez A017) × 3 rzadkości = **51 wariantów opisów i zdolności**.
Przyszłe aukcje są dostępne wyłącznie w nowych meczach
`auction_catalog='v22'`. Zapisane gry `v3` i `v4`
zachowują dawny 12-elementowy katalog (albo odpowiedni prototyp).

## Zasady aukcji, fizycznych kart i obiegu

Aukcja zaczyna się co 3 zakończone rundy, o ile w woreczku są co
najmniej **3 różne niekupione archetypy**. Dwa egzemplarze zostają
kupione, po jednym na gracza. Trzeci archetyp, który został pokazany,
ale nie wybrany, wraca WYŁĄCZNIE do przyszłych ofert aukcyjnych.
Raz kupiony archetyp nie jest już dostępny do ponownego zakupu.
Wystawiona, a następnie utracona karta aukcyjna nie przechodzi
do zwykłego tasowania 70 kart bazowych. Przy 17 archetypach
możliwe jest do **8 kompletnych aukcji**, po których zostaje 1
niekupiony archetyp i nie ma kolejnej aukcji.

ATK/PŻ nowo nabytych kart zależą wyłącznie od zakończonej rundy
R=3,6,...: `ATK=ATK_R3+(R-3)//3`;
`MAX_PŻ=R+8-ATK`. Po zakupie statystyki pozostają stałe, a
rzadkość może rosnąć co trzy rundy od zakupu.

## Aktywne nowe karty i jawne reguły interpretacji DRAFT

| Archetyp | Podstawowa | Rzadka | Legendarna |
|---|---|---|---|
| **A013 Łamacz Bastionów** | 25% MAX PŻ | 40% MAX PŻ | 60% MAX PŻ, najpierw zdejmuje Tarczę |
| **A014 Kapłan Odwróconej Łaski** | Blokuje wrogie leczenie | Zmienia połowę leczenia w obrażenia | Zamienia całe leczenie w obrażenia |
| **A015 Wieszczka Zerwanych Zaklęć** | Anuluje pierwsze wymierzone we własną stronę Przy wystawieniu | To samo + globalna blokada Przy śmierci | Globalna blokada Przy wystawieniu, Przy śmierci, Na koniec tury |
| **A016 Kartograf Utraconych Ścieżek** | Dobiera jedną z trzech wierzchnich kart własnej talii | Dobiera jedną, następnie dodatkowo zagrywa z 3 własnych lub 1 wrogiej | Zagrywa jedną z 3 własnych lub 3 wrogich |
| **A018 Licytator Złamanego Paktu** | +2 monety i +2 skutecznej oferty następnej aukcji | +2 monety i +5 skutecznej oferty | Automatyczny pierwszy wybór następnej aukcji |

**Ustalone rozstrzygnięcia**, które były oznaczone jako do zatwierdzenia
w projekcie użytkownika, a są konieczne do deterministycznego dema:

- A013 liczy ułamek od **bieżącego MAX PŻ** i zaokrągla w górę.
  Zawsze ignoruje pancerz; na podstawowej/rzadkiej Tarcza pochłania
  całe obrażenia, a na legendarnej zostaje zdjęta przed ciosem.
- A014 rzadka przy H=5 zamienia **3 w obrażenia i 2 w leczenie**
  dla tego samego celu; odwrócone obrażenia respektują Tarczę/pancerz.
  Obliczenie następuje od nominalnego leczenia, także przy pełnym PŻ.
  Regeneracja podlega konwersji; ustawianie PŻ i bonus MAX PŻ nie.
  **Przy wielu Kapłanach działa najwyższa aktywna rzadkość**, bez
  sumowania i bez pętli. Wyciszenie Kapłana wyłącza jego pasyw.
- A015 podstawowa/rzadka anulują **jedną** pierwszą wrogą zdolność
  Przy wystawieniu wymierzoną w stronę właściciela — na jedno
  fizyczne wystawienie Wieszczki. Blokada efektów Przy śmierci
  (rzadka) i trzech wyzwalaczy (legendarna) jest **globalna i dotyczy
  również jednostek własnych**. W fali jednoczesnych zgonów obecność
  Wieszczki jest oceniana **przed usunięciem źródeł**.
  Ataki oraz pasywy niewymienionych rodzajów pozostają aktywne.
- A016 rzadka zachowuje dobranie jednej własnej karty ze zdolności
  podstawowej, a następnie pozwala natychmiast wystawić jedną spośród
  do 3 kolejnych własnych i 1 górnej wrogiej. Wroga karta zostaje
  **przejęta**, nie kopiowana. Legendarna wybiera z 3+3 i nie daje
  dodatkowego dobrania. Zagranie z talii **nie zużywa limitu jednej
  zwykłej karty z ręki**, jednak NIE omija limitu pięciu jednostek.
  Przy pełnej planszy nie pojawia się oferta darmowego wystawienia.
- A018 podstawowa/rzadka: wypłata +2 monet następuje od razu,
  jednorazowa premia działa tylko na następną aukcję, ale **nie
  zwiększa faktycznie płaconego bidu**. Legendarna gwarantuje
  pierwszy wybór **za zero monet**. Dwie gwarancje na tej samej
  aukcji **znoszą się** i odbywa się normalna licytacja. Kupony
  trwają nawet po zejściu źródła z planszy; znikają po użyciu.
  Kupon bez kolejnej aukcji wygasa z meczem.

## Zakres stabilizacji i kompatybilność

- **Balans 70 kart v21** działa od 0.9.30; efekty v20 utrzymano.
- 36 istniejących wariantów v4 pozostaje objętych regresją;
  piętnaście nowych otrzymało dedykowane testy stanów.
- Osobny tryb `v22` rozdziela historię zapisów v4 (12 archetypów)
  od nowych gier (17 archetypów), zamiast na siłę przerabiać
  dotychczasową historię aukcyjną.
- Kontrole: liczba fizycznych kart, zony hand/deck/board/grave,
  maks. pięć jednostek, brak podwójnej własności A016,
  wyciszenie A014, blokada wyzwalaczy A015,
  atomowe fale zgonów, wykorzystanie kuponów A018, wystąpienie
  mniej niż trzech kart do aukcji i zapis z otwartym wyborem.
- Pozostaje lokalna gra solo przeciw dotychczasowemu AI.
  Dopasowano jedynie **legalność** jego licytacji do bonusów A018,
  bez nowego poziomu trudności, strategii czy multiplayera.

**Ograniczenie weryfikacji:** automatyczne testy potwierdzają
konkretne przejścia stanów i scenariusze, ale nie są dowodem
wyważenia siły wszystkich kombinacji w losowych meczach.
