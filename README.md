# AuctionHammer — gra karciana

**AuctionHammer 0.9.23** to lokalna gra karciana fantasy solo przeciwko komputerowi: 70 kart podstawowych (balans v20), **pełne aukcje v4 z 12 archetypami i 36 aktywnymi wariantami zdolności**, bez kosztu zagrania kart. Zachowano reguły bazowe GAME_MASTER_v19 i dotychczasowe AI. Nie planujemy w tej wersji multiplayera ani rozbudowy przeciwnika.

## Nowości 0.9.23 — aktywne zdolności aukcyjne v4

- 12 odrębnych archetypów aukcyjnych (A001–A012), 36 wykonywanych wariantów podstawowych, rzadkich i legendarnych.
- Aukcja co trzy pełne rundy; wzrost statystyk NOWYCH ofert: `ATK(R)=ATK(3)+(R-3)//3`, `PŻ(R)=R+8-ATK(R)`. Karty zakupione wcześniej nie rosną dalej.
- Efekty zgonów, przejmowania, kopiowania, wygnania, przywołania, wymiany rąk, wyciszania, leczenia i ochrony bohatera są wykonywane przez rzeczywistą kolejkę Match.
- Stare zapisy v3 zachowują dawną logikę bez aktywowania nowych zdolności; nowe mecze lokalne używają v4.
- Szczegóły: [implementacja aukcji v4](docs/auction/RELEASE_V4_0923.md).

## Nowości 0.9.22 — poprawki po audycie meczu

- Nie da się już wysyłać z interfejsu licytacji ponad posiadane monety ani zbyt niskich ofert. Niedostępne przyciski są wyszarzone; komunikat podpowiada **PASUJ**.
- Na pełnej planszy (5/5) podświetlane są jednostki, które można zastąpić bez wykorzystanego ataku. Nielegalne próby wystawienia są przechwytywane przed silnikiem.
- Kliknięcia w niedozwolone cele ataku nie generują błędnych komend. Komunikaty objaśniają **Prowokację**, brak gotowości i limit ataków.
- Dodano testy regresyjne interfejsu i kombinacji **S91 + S09** zaobserwowanej w meczu 0.9.21; nie zmieniano wartości kart ani reguł walki.
- Szczegóły: [audyt 0.9.22](docs/UX_AUDIT_0922.md).

**AuctionHammer** to turowa gra karciana fantasy dla jednego gracza przeciwko komputerowi. Obecna wersja korzysta z zatwierdzonych zmian **Game Master v19**. Zawiera 70 unikalnych kart podstawowych, po jednym egzemplarzu każdej. **Od 0.9.19 aktywny jest pierwszy prototyp aukcji z trzema tymczasowymi Strażnikami (3/6/12 PŻ); finalny katalog i płatne zdolności jeszcze nie istnieją. Koszt zagrania kart wynosi zero.**

## Uruchamianie w Windows

Pobierz [najnowsze wydanie gry](https://github.com/MateuszBock0/AuctionHammer/releases/latest), rozpakuj folder `AuctionHammer`, a następnie kliknij dwukrotnie plik **`URUCHOM_AUCTIONHAMMER.bat`**. Nie musisz instalować Pythona, dodatkowych bibliotek, Gita ani edytora kodu.

- **`URUCHOM_AUCTIONHAMMER.bat`** sprawdza dostępność aktualizacji i uruchamia grę. Gdy nie ma internetu, uruchamia dostępną wersję lokalną.
- **`GRAJ_BEZ_INTERNETU.bat`** uruchamia zainstalowaną grę bez sprawdzania aktualizacji.
- **`AuctionHammer.exe`** uruchamia grę bezpośrednio.

Plik `AuctionHammer.exe` musi znajdować się w tym samym folderze co katalog `_internal`. Internet jest potrzebny do pobrania aktualizacji, **nie do rozgrywki**.

## Sterowanie

1. Kliknij kartę na ręce, a następnie wolne pole własnej planszy. Możesz również przeciągnąć kartę.
2. Zaznacz gotową do ataku jednostkę i kliknij dopuszczalny cel: wrogą jednostkę albo bohatera przeciwnika. Jeśli wróg ma aktywną **Prowokację**, wybór celu jest ograniczony do jednostek z tą cechą.
3. Gdy zdolność wymaga decyzji, wybierz odpowiedni wariant w osobnym panelu po prawej stronie. Legalne cele są podświetlone, również na ręce (np. w przypadku S66). Jeżeli nie ma żadnego legalnego celu, gra pomija efekt, ale pozwala wystawić kartę.
4. Klawisze **1–6** odpowiadają pozycjom na bieżącej stronie wyboru. Strony zmienia się strzałkami lub przyciskami na panelu.
5. **I** otwiera pełne informacje o wskazanej karcie. Kółko myszy przewija opis.
6. **Spacja** kończy turę. **F11** przełącza tryb pełnoekranowy. **R** rozpoczyna nowy mecz.

Przy pierwszym rozdaniu można wymienić do trzech wybranych kart. Zaznaczone karty mają złotą ramkę i numer wyboru.

## Nowości 0.9.14 — animacje, historia, menu i zapis

- Po uruchomieniu gry pojawia się **menu główne**. **M** otwiera je ponownie
  podczas meczu. Menu pozwala rozpocząć nową grę, kontynuować bieżącą
  rozgrywkę, wczytać zapis i wejść w ustawienia.
- W **ustawieniach** można przełączać animacje i pełny ekran, wybrać
  poziom AI (**łatwy, normalny, trudny**) oraz **zapisać mecz**.
  Zapis trafia do `%LOCALAPPDATA%\\AuctionHammer\\savegame_v19.json`
  (w systemach bez LOCALAPPDATA — do katalogu danych użytkownika).
  Zapis obejmuje wszystkie stany kart, statusy, aktywne wybory i RNG.
- **A** włącza lub wyłącza efekty walki. Efekty obrażeń, leczenia,
  tarczy, pancerza, trucizny, ogłuszenia, zgonu oraz pociski ataków
  wynikają z zatwierdzonych działań silnika. Nie wpływają na rozgrywkę.
- **H** otwiera pełną **historię zdarzeń**; kółkiem myszy i strzałkami
  można przewijać dziennik, bez limitu poprzednich 160 wpisów.
- **P** otwiera **powtórkę aktualnej partii**. Strzałki lewo/prawo
  pozwalają oglądać kolejne zapisane stany planszy, **P/Esc** wraca
  do gry. Migawki są tylko do odczytu; obejmują maks. 480 ostatnich zmian
  stanu i nie są zapisywane na dysku. Pełny dziennik jest zachowywany
  w pliku zapisu meczu.
- 35 ikon **Minimal Fantasy** z dostarczonego pakietu agenta UI
  zostało dołączonych do wersji portable w skompresowanym atlasie PNG.
  Ikony nie zawierają dynamicznych wartości ATAK/PŻ ani poziomu zdolności.
- **Narzędzie AI:** `python tools/simulate_ai_levels.py --games 1000`
  porównuje poziomy AI na rzeczywistym silniku. Poziom trudny korzysta
  z lepszych heurystyk, nie z pełnego przeszukiwania drzewa gry.

Zmiany nie dodają aukcji ani kosztów zagrania i nie zmieniają Game Master v19.

## Aktualizacja 0.9.15 — ikony wysokiej jakości

Po kontroli przesłanej paczki ikon usunięto stratną wizualnie wersję
atlasu 24 px/24 kolory. Nowy atlas ma 40 px na piktogram, 256 kolorów
i przezroczystość, a mimo to zajmuje tylko około 29 KB. Wszystkie
35 wzorów są takie same, jak w paczce źródłowej; pozostają zachowane
ich znaczenia (14 rodzin zdolności, 16 statusów, 5 frakcji).

Wszystkie opisy, wartości ATAK/PŻ oraz rozmiary kart pozostają
niezmienione. Bez zmian zasad Game Master v19.
Podgląd Pygame: `preview/IKONY_35_WYSOKA_JAKOSC_0915.png`.
Szczegóły audytu: [Ikony Minimal Fantasy — 0.9.15](docs/IKONY_MINIMAL_FANTASY_0915.md).

## Aktualizacja 0.9.16 — Visual Polish

Oprawa gry przeszła całościowy pass Minimal Fantasy:
- ciemne kamienne tło z grawerowanymi symbolami, wydzielone strefy
  komputer/gracz/ręka i winietowanie;
- zdobione sloty, panele i przyciski (hover/pressed/disabled),
  metaliczne obramowania kart oraz subtelne ornamenty;
- ulepszone animacje ataku, obrażeń, leczenia i statusów, iskry zgonu,
  pojawianie się jednostki oraz sygnalizacja zmiany tury;
- korekty czytelności: rozdzielony nagłówek instrukcji, prawdziwe
  mierzenie szerokości logu, statusy oddzielone od przycisku [I],
  ekran końcowy z przyciskiem w panelu wyniku.

Wszystkie 70 kart, ich statystyki i umiejętności działają jak dotąd.
Żadne nowe mechaniki, aukcje ani koszty kart nie zostały dodane.

Testy automatycznie sprawdzają ułożenie tekstów i klikalność na
logicznych DPI 100%, 125% oraz 150% (wymagany również test na
rzeczywistym monitorze). Zrzuty nowych ekranów:
`preview/VISUAL_0916_*.png`.

[Raport z poprawek i ograniczeń](docs/VISUAL_POLISH_0916.md).

## Aktualizacja 0.9.17 — prześlij cały ostatni mecz do audytu

Po zakończeniu gry AuctionHammer automatycznie tworzy **jeden plik JSON**
z pełną historią komend, wyborów, stanów planszy i wewnętrznych
rozstrzygnięć zdolności oraz fal śmierci:

`%LOCALAPPDATA%\\AuctionHammer\\AuctionHammer-OSTATNI-MECZ.json`

Na ekranie końcowym naciśnij **O** (lub **OTWÓRZ FOLDER**) i
prześlij plik **AuctionHammer-OSTATNI-MECZ.json** do ChatGPT.
**E** ponawia eksport. [O] działa także z menu głównego.

Nowy **ukończony** mecz nadpisuje ten sam plik. Nie przechowujemy
wielu zakończonych partii; starszy audyt jest zastępowany automatycznie.
Plik znajduje się poza folderem z aktualizacjami EXE i nie znika
podczas aktualizacji przez BAT.

Raport obejmuje również **ukryte karty komputera** i seed losowy,
więc pojawia się dopiero po zakończeniu gry. Zawiera sumę SHA-256
i pozwala ponownie odtworzyć komendy na silniku v19 poleceniem
`python tools/verify_last_match.py`. Starsze wczytane zapisy
będą poprawnie oznaczone jako częściowe, zamiast sugerować
nieistniejącą pełną historię.

[Dokładna specyfikacja i instrukcja](docs/LAST_MATCH_AUDIT_0917.md).

## Aktualizacja 0.9.18 — czytelne PŻ i dokładniejszy audyt

- Bohater pokonany śmiertelnym ciosem wyświetla **0/100 PŻ** w UI
  (również na ekranie zakończenia). Rzeczywista ujemna wartość
  pozostaje w silniku i w JSON, aby nie zgubić informacji o obrażeniach.
- Testy regresji sprawdzają oczyszczanie, truciznę (w tym odporność),
  ogłuszenie (w tym wygaśnięcie) i Podwójny atak S115/S79/S67.
- Audyt ostatniego meczu przechowuje **początkową trudność AI,
  każdą zmianę jej poziomu, poziom przy poszczególnych akcjach
  oraz pełny 40-znakowy SHA commita gry**.
- Wydanie Windows umieszcza identyfikator buildu w środku EXE
  i sprawdza go w GitHub Actions. Brak oryginalnego commita
  oznaczamy jako `unknown`, zamiast zgadywać.
- Zapis gry zachowuje ustawienie AI i przywraca je po wczytaniu.

Nowy obraz Pygame: `preview/VISUAL_0918_KONIEC_0_PZ.png`.

[Szczegóły testów i metadanych](docs/COMBAT_AUDIT_HOTFIX_0918.md).

## Aktualizacja 0.9.19 — karczemne UI i testowe aukcje

**Wybrane elementy Tavern UI Pack v2:** drewniana faktura stołu jako
subtelna warstwa pod panelami i mosiężny separator na ekranie aukcji.
Nie użyto pełnego tła bogato wyposażonej karczmy ani ciężkich ramek
wokół kart — zasłaniałyby teksty i miejsca interakcji. Cały interfejs
pozostaje offline i zachowuje dotychczasowy kontrast.

**Aukcje po rundach 3, 6, 9...:** po wypłaceniu obu graczom +1 monety
rozpoczyna się licytacja bez limitu czasu. Wystawiane są trzy tymczasowe
karty, każda **3 ATAK, Prowokacja i jednorazowa Tarcza**, o PŻ odpowiednio
**3, 6 i 12**. Rzadkości losowane są niezależnie 60/30/10%; pozostają
informacyjne aż do wdrożenia rzeczywistego katalogu aukcyjnego.
Numer aukcji jest poziomem zapisanym na zdobytym egzemplarzu.

Przebieg: oferuj co najmniej o 1 monetę więcej, pasuj lub przebij ofertę
komputera. Zwycięzca płaci za **pierwszy wybór**, rywal bierze jedną
z pozostałych kart **za darmo**, trzeci wariant nie jest rozdawany.
Gdy obaj pasują bez oferty, darmowy pierwszy wybór przysługuje
naprzemiennie rozpoczynającemu mecz i jego rywalowi.
Wybrane karty trafiają na ręce (bez limitu 5), zachowują stałe statystyki,
nie skalują się w ręce i po wystawieniu grają jak jednostki bazowe.

- **Klawiatura:** cyfry + Enter do złożenia oferty; w fazie wyboru
  **1/2/3** wybiera odpowiednią ofertę.
- **Przyciski:** PASUJ, PODBIJ +1, LICYTUJ lub kliknij wybraną kartę.
- **M:** można otworzyć menu i zapisać grę nawet podczas aukcji.

Stare zapisy 0.9.18 pozostają w dotychczasowym trybie bez aukcji,
bez dopisywania historycznie nieodbytych licytacji. Audyt JSON z
nowego meczu zapisuje wszystkie nowe akcje aukcyjne.

**Nie ma jeszcze** żadnych płatnych aktywacji zdolności, kopiowania,
przejmowania, wskrzeszania czy finalnego katalogu 36 kart aukcyjnych.
Mechaniki i balans pozostałych 70 kart nie zostały zmienione.

[Analiza paczki i szczegóły implementacji](docs/TAVERN_AUCTION_PROTOTYPE_0919.md).

## Wydanie 0.9.20 — pełny wygląd drewnianej karczmy

Warstwa graficzna **Tavern UI Pack v2** jest teraz widoczna w całej grze:
tło z kominkiem i drewnianymi stołami, ciemne drewniane strefy
planszy, mosiężne ramy slotów, przyciski i ornamenty menu/aukcji.
Wykorzystano skompresowane, dostarczone wcześniej oryginalne grafiki,
bez pobierania czegokolwiek przez internet podczas rozgrywki.

Zachowano nieprzezroczyste strefy pod kartami i napisami. Teksty,
rozmiary kart i hitboxy nie uległy zmianom. **Wydanie 0.9.20 nie
zmienia zasad aukcji 0.9.19 ani zestawu 70 podstawowych kart.**

Podglądy: `preview/VISUAL_0920_TAWERNA_PELNA_PLANSZA.png`,
`preview/VISUAL_0920_DREWNIANE_MENU.png` i
`preview/VISUAL_0920_DREWNIANA_AUKCJA.png`.

## Wydanie 0.9.21 — 12 archetypów aukcyjnych i ewolucja rzadkości

Nowa partia korzysta z roboczego katalogu v3: **12 unikalnych
archetypów** i **36 tekstów wariantów** (podstawowa / rzadka /
legendarna). Na aukcji losowane są trzy różne archetypy;
rzadkości niezależnie **60% / 30% / 10%**. Statystyki karty
wynikają z zakończonej rundy: **ATK + MAX PŻ = R + 8**.
Po zakupie ATK i MAX PŻ nie rosną, także w ręce.

**Rzadkość ewoluuje co 3 pełne rundy od zakupu** aż do
legendarnej. Pokonanie karty aukcyjnej daje odpowiednio
**1 / 2 / 3 monety** według rzadkości.

**Złożone zdolności A001–A012 nie działają jeszcze.**
Na ekranie aukcji i na kartach są jawnie oznaczone jako
*NIEAKTYWNA / PLANOWANA*. Nazwy i docelowe opisy są
dostępne, ale żadne niezaprojektowane rozstrzygnięcie
kopiowania, wyciszenia, przejęcia czy wskrzeszenia nie
jest wykonywane. Są to grywalne jednostki o swoich
bazowych ATK i PŻ, bez zdolności specjalnych.

**Wczytane partie z 0.9.19/0.9.20** zachowują dawnych
Strażników 3/6/12 i ich Prowokację + Tarczę, bez zmiany
reguł istniejącego meczu. Audyt JSON zapisuje tryb katalogu
oraz każdą ewolucję rzadkości.

[Opis etapu i testów](docs/AUCTION_FOUNDATION_0921.md) ·
[Oryginalny katalog v3](docs/KATALOG_AUKCYJNY_12_v3.md).

## Karty, efekty i skalowanie

Wszystkie **napisy widoczne w grze są po polsku**. Karty pokazują moment aktywacji zdolności: **Przy zagraniu, Przy ataku, Przy śmierci, Na koniec tury, Pasywna**. Obok pojawia się symbol rodziny efektu, jego bieżąca wartość oraz zielony pasek wzrostu.

Przykładowe oznaczenia: **OBR** — obrażenia, **LECZ** — leczenie, **PANC** — pancerz, **PŻ** — punkty życia, **SZYBKI** — Szybki atak, **2 ATAKI** — Podwójny atak, **PROW** — Prowokacja.

Karty otrzymują indywidualny przyrost statystyk po każdej zakończonej własnej turze na ręce. Zdolności zwiększają poziom **co trzy takie tury** (po 3, 6, 9 itd.). Zielony pasek wskazuje *co dokładnie* się wzmacnia. W dużym podglądzie pogrubiona zielona liczba oznacza wartość podlegającą skalowaniu, ale nie czas trwania statusu ani liczbę dozwolonych ataków.

## Dopasowanie do ekranu

Gra automatycznie dostosowuje początkowy rozmiar okna do dostępnej przestrzeni, w tym do skalowania obrazu w Windows. Można zmieniać rozmiar okna bez rozciągania kart i bez przesuwania obszarów klikalnych względem grafiki. Klawisz **F11** przełącza pełny ekran.

## Obowiązujące zasady i dokumenty

| Plik | Przeznaczenie |
| --- | --- |
| `AUCTIONHAMMER_MASTER.md` | Aktualny opis projektu i wskazanie obowiązujących źródeł |
| `data/GAME_MASTER.json` | Aktualny uporządkowany zapis zasad i katalogu v19 |
| `data/game_rules_v19.json` | Aktualny, odrębny zbiór zasad v19; zgodny z `GAME_MASTER.json` |
| `data/event_order_v19.json` | Obowiązująca kolejność zdarzeń, wspólne fale zgonów i kaskady |
| `docs/FALE_ZGONOW_v19_MVP_0910.md` | Opis naprawy kolejki zdarzeń i testów |
| `data/cards_base_70.json` | **Jedyne bieżące źródło definicji 70 kart**, wczytywane przez silnik |
| `docs/V19_INTEGRATION_AND_UI.md` | Zmiany zasad v19 i ich implementacja |
| `docs/GAME_MASTER_v17.md` | **Archiwum** wcześniejszej specyfikacji v17 — nie jest katalogiem aktualnych kart |
| `data/event_order_v17.json` | Historyczny dokument kolejności zdarzeń; wersję aktualną określa `event_order_v19.json` |
| `game/core/` | Silnik meczu |
| `game/ui/` | Interfejs gry |
| `tests/` | Automatyczne testy |

Zmiany S66, S67, S79, S114 i S115 z v19 są zaimplementowane, podobnie jak zatwierdzone zmiany S20, S82, S90, S91, S105 i S109. Mechanizm grup **jednoczesnych zgonów** został przebudowany i objęty testami w MVP 0.9.10, lecz nadal nie przeprowadzono wyczerpującej walidacji wszystkich możliwych kombinacji. Nie przedstawiamy bieżącego prototypu jako ostatecznie zbalansowanej ani w pełni zweryfikowanej wersji gry.

## MVP 0.9.10 — jednoczesne zgony i kolejka zdarzeń

Grupy jednostek ginących jednocześnie są obecnie rozpatrywane we **wspólnej fali**. Najpierw ustalane są wszystkie legalne cele i zbierane wybory, a dopiero potem wykonywane są konsekwencje. Kolejne zgony wywołane tą falą trafiają do następnej grupy. Uzupełniono testy kaskad, osłon, statusów i śmierci bohaterów, a losowania kart S90/S91 zapisują odtwarzalne informacje w dzienniku. Szczegółowe zasady i ograniczenia znajdują się w [opisie wdrożenia fal śmierci](docs/FALE_ZGONOW_v19_MVP_0910.md).

Dane autorytatywnej kolejności zdarzeń przechowuje `data/event_order_v19.json`. Historyczny plik `data/event_order_v17.json` służy wyłącznie do porównywania starszych decyzji.

## Rozwój i aktualizacje

Po zatwierdzeniu zmian w gałęzi `main` GitHub automatycznie uruchamia testy i przygotowuje przenośne wydanie dla Windows. Kod można edytować lokalnie po zainstalowaniu Pythona i zależności z `requirements.txt`. **Do zwykłego grania te narzędzia nie są potrzebne.**

## Minimal Fantasy — wyższe karty (MVP 0.9.11)

Nowy, uproszczony wygląd z zachowaniem klimatu fantasy: **125 × 195 px** na ręce, **148 × 220 px** na planszy i **255 × 380 px** w podglądzie. Dynamiczne, wyraźne plakietki **ATAK** i **PŻ** pozostają widoczne ponad ilustracjami oraz przyciemnieniem, a zdolności zachowują pełną zgodność z Game Master v19.

- Lewy przycisk wybiera kartę i służy do zagrywania lub ataku; **I** i prawy przycisk otwierają duży podgląd.
- Zielony pasek oznacza ulepszenie zdolności co trzy własne tury na ręce; oddzielny postęp jest widoczny tylko na ręce.
- Złota ramka oznacza zaznaczoną kartę, turkusowa — legalny cel ataku, fioletowa — legalny cel zdolności.
- Krótkie animowane podświetlenie wpisów dziennika zdarzeń można wyłączyć i ponownie włączyć klawiszem **A**.
- Wszystkie karty są generowane z aktualnych danych 70 kart; nie ma statystyk zapisanych na sztywno w ilustracjach.

Zrzuty ekranu wygenerowane prawdziwym rendererem Pygame znajdują się w katalogu `preview/` wydania Windows oraz w artefaktach GitHub Actions.

**Instrukcja wdrożenia, lista testów i opis cofania:** [Minimal Fantasy — wysokie karty](docs/MINIMAL_FANTASY_WYSOKIE_KARTY.md).
