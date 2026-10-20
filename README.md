# AuctionHammer

### Taktyczna gra karciana fantasy, w której zwycięstwo zależy nie tylko od kart na ręce, ale też od tego, co wylicytujesz.

**AuctionHammer** to darmowa, lokalna gra karciana dla jednego gracza przeciwko komputerowi. Budujesz armię, rozwijasz jednostki, zarządzasz monetami i co kilka rund rywalizujesz o potężne karty na aukcjach. Czasem warto wygrać licytację. Czasem lepiej oszczędzić monety, przeżyć kolejną rundę i poczekać na właściwą kartę.

**Aktualna wersja: 0.9.48 — grywalne demo na Windows** · **70 kart podstawowych** · **17 archetypów aukcyjnych** · **51 wariantów zdolności aukcyjnych** · **rozgrywka offline**

> **English:** AuctionHammer is a free, single-player fantasy card-game demo with tactical battles, cards that grow while held in your hand, and recurring auctions for powerful units. The interface is in Polish. No account, server connection or Python installation is needed for the Windows release.

[**Pobierz grę — Windows ZIP**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) · [Zgłoś błąd lub pomysł](https://github.com/MateuszBock0/AuctionHammer/issues) · [Zasady aukcji v22](docs/auction/RELEASE_V22_0931.md)

## Dlaczego warto spróbować?

- **Każda partia tworzy inną armię.** Karty trafiają do graczy z jednej wspólnej, losowanej puli, a limit pięciu jednostek na planszy wymusza podejmowanie decyzji.
- **Czekanie też jest strategią.** Podstawowe karty stają się silniejsze, gdy trzymasz je na ręce. Możesz wystawić jednostkę od razu albo rozwinąć ją przed kluczową walką.
- **Aukcje zmieniają przebieg meczu.** Trzy rzadkie możliwości, dwóch rywali i tylko dwie kupione karty. Licytujesz przede wszystkim **prawo pierwszego wyboru**.
- **Zdolności łączą się w kombinacje.** Tarcza, Prowokacja, trucizna, ogłuszenie i leczenie spotykają się z przejęciami jednostek, kopiowaniem, wskrzeszaniem, wygnaniem czy blokowaniem zdolności.
- **Widzisz, co się wydarzyło.** Historia walki wyjaśnia obrażenia, pochłanianie przez Tarczę i pancerz, leczenie oraz zmiany statusów. Mecz można zapisać i przeanalizować.

## Pobieranie i uruchamianie

### Chcę po prostu zagrać — Windows

1. Wejdź w [**Releases — najnowsze wydanie**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) i pobierz **`AuctionHammer-Windows.zip`**.
2. Rozpakuj archiwum. Otwórz otrzymany folder **`AuctionHammer`**.
3. Uruchom **`AuctionHammer.exe`** lub **`GRAJ_BEZ_INTERNETU.bat`**.

Nie musisz instalować Pythona, dodatkowych bibliotek ani Gita. **Gra nie wymaga internetu** — po pobraniu możesz grać offline.

**Jednym kliknięciem:** `URUCHOM_AUCTIONHAMMER.bat` pobiera ZIP i sumę SHA-256, weryfikuje je i instaluje **obok poprzedniej wersji**. Dopiero po sprawdzeniu kompletności przełącza grę na nowe wydanie. Gdy internet nie działa lub pobranie się nie powiedzie, uruchamia dostępną wersję. Nie nadpisuje starszego EXE ani plików zapisanych meczów.

**Offline:** `GRAJ_BEZ_INTERNETU.bat` uruchamia aktywną wersję bez kontaktu z GitHubem.

**Cofnięcie aktualizacji:** uruchom `COFNIJ_AKTUALIZACJE.bat`, ewentualnie `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\\portable_launcher.ps1 -Rollback`.

**Migracja ze starszej wersji:** jeżeli masz launcher 0.9.42 lub starszy, najbezpieczniej **raz pobrać i rozpakować cały ZIP 0.9.43 do nowego folderu**. Stary BAT wywołuje poprzedni aktualizator, który nie gwarantował przywrócenia plików przy przerwanym kopiowaniu. Kolejne aktualizacje 0.9.43+ nie nadpisują działającej instalacji. Zachowaj folder `_internal` przy EXE. Zapisy w `%LOCALAPPDATA%\\AuctionHammer` są wspólne i bezpieczne.

Szczegóły: [QA aktualizatora Windows 0.9.43](docs/QUALITY_RELEASE_0943.md).

> To rozwijane demo, nie ukończona komercyjna produkcja. Automatyczne testy i wydania Windows są publikowane na GitHubie, ale w grze nadal mogą wystąpić błędy.

## Gameplay UX Polish i audyt opisów kart (0.9.48)

Wersja 0.9.48 domyka poprawki po 0.9.47. Wspólny pasek **samouczka i bieżącej tury** zawsze pokazuje możliwość wystawienia i liczbę gotowych jednostek. Złoto oznacza **faktyczne miejsce dodania jednostki** po prawej stronie planszy, a nie dowolny wolny slot. Wyniki walki wyświetlane są kolejno w czytelnym dzienniku zdarzeń: tarcza, obrażenia, śmierć itd. Pełne zdarzenia pozostają pod klawiszem H.

Zweryfikowana, dostarczona przez autora paczka poprawia opisy **13 kart podstawowych**, **5 warunkowych zasad v23** i **7 aktywnych wariantów aukcyjnych**. Aukcja ma dodatkowy przycisk **PEŁNA ZDOLNOŚĆ**, działający bez przypadkowego zakupu karty. Stare definicje v22 i v4, zapisy, RNG i mechanika pozostały bez zmian. Więcej: [audyt 0.9.48](docs/GAMEPLAY_UX_POLISH_0948.md).

## Czytelność rozgrywki (0.9.47)

- Pasek tury pokazuje **KARTA 0/1 lub 1/1** oraz **GOTOWE DO ATAKU: N**, oparte na rzeczywistej legalności zagrań i ataków. N oznacza liczbę gotowych jednostek, nie liczbę trafień.
- Po wybraniu karty z ręki **złote obrysy** wskazują legalne wolne pola lub zastąpienia; **turkusowe** obrysy wskazują legalne cele ataku, a **fioletowe** — cele zdolności.
- Panel karty pokazuje kontekstowy status: **ZAGRAJ KARTĘ**, **ATAK GOTOWY**, **ATAK WSTRZYMANY**, **KARTA RYWALA**.
- Przycisk **ZAKOŃCZ TURĘ [SPACJA]** wyróżnia się mocniej po wykorzystaniu dostępnych akcji. Wcześniejsze zakończenie tury nadal jest dozwolone.
- Krótkie komunikaty na dole panelu opisują prawdziwe, zatwierdzone zdarzenia: obronę tarczą/pancerzem, obrażenia, leczenie, statusy i zgony. Działają również przy wyłączonych animacjach.

Zmiany mają charakter tylko wizualny i nie modyfikują reguł, kart, AI, aukcji, RNG ani podpisanego audytu. Szczegóły: [Gameplay Clarity 0.9.47](docs/GAMEPLAY_CLARITY_0947.md).

## Jak wygląda rozgrywka?

**Twój cel:** sprowadzić punkty życia (PŻ) bohatera komputera do zera, zanim komputer pokona Ciebie. Obaj bohaterowie rozpoczynają z **100 PŻ**.

| Element | Zasada |
|---|---|
| Tryb | 1 gracz kontra komputer, lokalnie |
| Początek partii | 5 kart na ręce i 5 we własnej talii dla każdego gracza |
| Wymiana początkowa | Możesz wymienić do 3 kart przed rozpoczęciem meczu |
| Początek tury | Dobierasz z własnej talii, aż masz 5 kart na ręce lub skończą się dostępne karty |
| Wystawianie | Zwykle **jedna karta z ręki na własną turę**, bez opłaty w monetach |
| Plansza | Maksymalnie **5 jednostek** na stronę; na pełnej planszy możesz zgodnie z regułami zastąpić własną jednostkę |
| Walka | Jednostki atakują wroga lub jego bohatera, jeśli nie blokuje tego Prowokacja |
| Monety | **+1 moneta dla obu graczy po pełnej rundzie**; w nowych meczach gracz zaczynający jako drugi wybiera **Chorążego 2 ATK / 5 PŻ albo +3 monety** (opis: „Chorąży zawsze zdąży.”; nie daje Szybkiego ataku). Chorąży nie atakuje w pierwszej własnej turze i po śmierci nie wraca do talii. Dawne zapisy i archiwalne audyty zachowują pierwotne +3 monety, Strażnika 5/5 albo Chorążego 3/5. W nowych meczach v22 na koniec własnej tury otrzymujesz dodatkowo **5 − liczba własnych jednostek** monet |
| Koniec meczu | Pokonaj bohatera przeciwnika; przy jednoczesnym pokonaniu obu obowiązują reguły rozstrzygania remisu |

**Runda** oznacza wykonanie po jednej turze przez obu graczy. Każdy może wystawić zwykle jedną kartę z ręki, ale nie ma kosztu zagrania. **Monety służą przede wszystkim do licytowania kart aukcyjnych**, a nie do opłacania zwykłych jednostek.

### Karty i walka

W podstawowej puli jest **70 unikatowych kart** z pięciu frakcji: **Elfy, Dzikie bestie, Potwory, Krasnoludy i Ludzie**. Karty mają **ATK (atak)**, **PŻ (punkty życia)**, frakcję, rodzaj zdolności oraz warunek jej aktywacji.

Zależnie od jednostki zdolność uruchamia się m.in. **przy wystawieniu**, **podczas ataku**, **przy śmierci**, **na koniec tury** lub działa **pasywnie**.

Przykłady ważnych efektów:

- **Prowokacja** — ogranicza przeciwnikowi wybór celów ataku.
- **Tarcza** — pochłania następne trafienie, po czym znika; **pancerz** zmniejsza przyjmowane obrażenia.
- **Trucizna, ogłuszenie, wyciszenie** — przeszkadzają jednostkom walczyć lub korzystać ze zdolności.
- **Regeneracja i leczenie** — przedłużają obecność jednostek i bohaterów na polu bitwy.
- **Szybki lub podwójny atak** — pozwalają działać wcześniej albo zaatakować więcej niż raz.

Podczas standardowego starcia dwóch jednostek obie mogą zadać sobie obrażenia **jednocześnie**. Zwykła jednostka nie atakuje od razu w turze wystawienia, chyba że odpowiedni efekt na to pozwala. Kiedy jednostka ginie, jej zdolność „Przy śmierci” może jeszcze wpłynąć na wynik potyczki.

**Przykład często mylonych kart:** podstawowy **Chorąży Królewskiej Kompanii (S34)** daje +1 ATK najbliższemu sojusznikowi albo −1 ATK wrogowi naprzeciwko. Aukcyjny **Generał Oddziału Natarcia (A002)** w podstawowej rzadkości daje +1 ATK wszystkim jednostkom po obu stronach. To różne karty z różnych pul.

### Karty stają się silniejsze na ręce

W AuctionHammer nie każdą kartę opłaca się zagrywać natychmiast. **Karty podstawowe otrzymują przyrost statystyk za ukończone własne tury spędzone na ręce**. W aktualnym balansie v21:

- **58 kart** zyskuje **+1 ATK i +1 PŻ** za turę na ręce;
- **12 kart** zyskuje **+2 ATK** za turę na ręce.

Co trzy takie tury wybrane rodzaje zdolności otrzymują dodatkową premię: np. **Tarcza i Prowokacja +1 ATK / +2 PŻ**, a **Szybki atak +2 ATK / +1 PŻ**. Po zagraniu jednostki jej rozwój na ręce się kończy.

To zachęca do wyboru między **siłą teraz** a **silniejszą kartą później**.

## Aukcje — najważniejsza mechanika AuctionHammer

**Po każdej trzeciej pełnej rundzie** (3., 6., 9., 12. itd.) pojawia się aukcja, o ile w osobnej puli pozostają przynajmniej trzy niewykupione archetypy. Aukcje są integralną częścią meczu, a nie osobnym sklepem.

### Jak przebiega aukcja?

1. Gra losuje **3 różne karty aukcyjne** z dostępnej puli oraz niezależnie ustala ich rzadkości.
2. Ty i komputer **licytujecie monetami lub pasujecie**. Każda kolejna skuteczna oferta musi przebić poprzednią.
3. **Zwycięzca licytacji płaci swoją ofertę i wybiera pierwszy** jedną z trzech kart.
4. Drugi gracz **za darmo wybiera jedną z dwóch pozostałych**. Ostatecznie każdy otrzymuje po jednej karcie na rękę.
5. **Trzecia, niewykupiona karta nie przepada**: jej archetyp wraca do **wyłącznie aukcyjnej puli** i może pojawić się później, z nowo wyliczonymi statystykami i nowym losowaniem rzadkości.

Jeśli obaj gracze spasują bez żadnej oferty, prawo pierwszego wyboru przypada graczowi określonemu przez reguły kolejności aukcji. Wygrać licytację nie znaczy więc zabrać wszystkich kart — **kupujesz pierwszeństwo wyboru jednej**.

**Przykład:** Na aukcji pojawiają się trzy karty. Ty oferujesz 8 monet, komputer pasuje. Płacisz 8 i wybierasz tę, która najlepiej uzupełnia Twoją armię. Komputer dostaje drugą wybraną przez siebie, a niewykupiony archetyp wraca do kolejnych aukcji.

### Rzadkość, siła i ograniczona podaż

| Cecha | Jak działa |
|---|---|
| Katalog | **17 archetypów aukcyjnych** — w tym pięć dodanych w v22 |
| Warianty | **Podstawowa (60%)**, **rzadka (30%)**, **legendarna (10%)** — losowane dla każdej oferty |
| Zdolności | **51 wariantów**: każdy archetyp ma trzy możliwe opisy i efekty |
| Statystyki | ATK i maksymalne PŻ oferty zależą od rundy aukcji; karty oferowane później są statystycznie silniejsze |
| Po zakupie | Statystyki kupionej karty **zostają ustalone na stałe** — karta nie rośnie na ręce |
| Awans rzadkości | Co **3 ukończone rundy od zakupu**: podstawowa → rzadka → legendarna; zmienia się zdolność, nie ATK/PŻ |
| Dostępność | Kupiony archetyp jest usuwany z puli; niewykupiony może wrócić |
| Koniec aukcji | Z 17 archetypów da się rozstrzygnąć maksymalnie **8 pełnych aukcji**; przy mniej niż 3 dostępnych nie odbywa się następna |

**Karty aukcyjne nigdy nie trafiają do zwykłego dobierania 70 kart.** Możesz je uzyskać wyłącznie przez zakup na aukcji. Po zdobyciu pojawiają się na ręce i obowiązuje je normalny limit wystawiania. Gdy zakupiona karta zostanie usunięta z gry, nie wraca do zwykłego cmentarza i talii.

### Co można wylicytować?

Oprócz mocnych jednostek aukcje wprowadzają znacznie bardziej nietypowe zdolności: **przejęcia jednostek wroga, wskrzeszanie, kopiowanie, wygnanie, wymianę kart z ręki, wyciszanie, manipulację zdrowiem bohaterów, ratowanie przed śmiercią, przywoływanie nowych żołnierzy** oraz **aury**, które zmieniają możliwości całej planszy.

W katalogu v22 znajdziesz również karty nastawione na przebijanie wysokiego PŻ, odwracanie leczenia w obrażenia, blokowanie zdolności, wyciąganie kart z talii oraz specjalne bonusy do kolejnych aukcji.

Szczegółowe opisy każdej wersji znajdują się w [katalogu 17 kart aukcyjnych (JSON)](data/auction/KATALOG_AUKCYJNY_17_v22.json) i [dokumentacji aukcji v22](docs/auction/RELEASE_V22_0931.md).

## Widoczny samouczek i podręczna pomoc (0.9.46.1)

Nowość: samouczek najpierw wyświetla **duży ekran powitalny** z pięcioma etapami. **Enter / Rozpocznij naukę** uruchamia wskazówki; **Esc / Pomiń** zaczyna zwykłą grę. Podczas nauki środkowy pasek ma wyraźną złotą ramkę, licznik etapów i podświetla złotym obrysem karty oraz pola, w które warto teraz kliknąć. Możesz nadal zagrać dowolną legalną akcję. Nie zmienia się ani silnik, ani audyt.

W **Menu → Samouczek** rozpoczniesz nowy, prowadzony mecz. Samouczek reaguje na rzeczywiste akcje: wymianę startową, zagranie karty, pierwszy atak i aukcję. Podpowiedzi są krótkie, nie blokują sterowania i nie wpływają na logikę ani losowanie. Przy rozpoczęciu samouczka podczas trwającej partii gra pyta, czy zapisać ją przed rozpoczęciem nowej.

Naciśnij **F1**, aby otworzyć podręcznik z czterema stronami: pierwszy mecz, walka i statusy, monety i aukcje, sterowanie i diagnostyka. Strony zmieniasz strzałkami, a zamykasz F1 lub Esc. **T** włącza albo wyłącza wskazówki podczas normalnej rozgrywki. Gdy jednostka nie może zaatakować, wskazówka na planszy wyjaśnia wynik aktualnych kontroli legalności silnika, zamiast zgadywać zasady.

## Sterowanie i przydatne funkcje

| Akcja | Sterowanie |
|---|---|
| Wystaw kartę | Kliknij kartę na ręce, następnie własne pole; możesz też przeciągnąć kartę |
| Zaatakuj | Kliknij gotową jednostkę i legalny cel ataku |
| Wybierz efekt | Kliknij opcję po prawej stronie; **1–6** wybiera opcje na aktualnej stronie |
| Zakończ turę | **Spacja** |
| Informacje o karcie | **I** |
| Historia zdarzeń | **H** — pełny dziennik, ostatnie zdarzenie w panelu bocznym |
| Powtórka meczu | **P** |
| Animacje walki (wł./wył.) | **A** — nie wycisza muzyki ani nie zmienia zasad |
| Menu i zapis | **M** |
| Pełny ekran | **F11**, także na ekranie startowym |
| Nowa partia | **R** |

Podczas aukcji kwotę wybierasz **suwakiem** (od minimalnej legalnej oferty do salda monet). Działają też **←/→**, **Home/End**, **Enter** (licytuj) i **Esc** (pasuj).

Grę można **zapisać i wczytać** z menu. Historia zdarzeń oraz eksport audytu ostatniej partii ułatwiają sprawdzenie, dlaczego jednostka przeżyła atak albo jak zadziałały połączone efekty. Funkcje powtórki i audytu mają charakter diagnostyczny — nie jest to tryb gry wieloosobowej.

## Uruchomienie ze źródeł (dla programistów)

Gra jest napisana w **Pythonie 3.12** z użyciem **pygame-ce**. Kod i silnik działają lokalnie; nie ma wymaganego serwera.

```bash
git clone https://github.com/MateuszBock0/AuctionHammer.git
cd AuctionHammer
python -m pip install -r requirements.txt
python -m game.main
```

W środowisku Windows polecenie `python` możesz zastąpić `py -3.12`, jeśli tak skonfigurowany jest Twój interpreter. Do uruchamiania wydania portable **nie** potrzeba tych komend — są przeznaczone dla osób pracujących z kodem.

Automatyczne testy silnika, aukcji i interfejsu:

```bash
python -m unittest discover -s tests -v
```

## Struktura projektu i formaty plików

```text
AuctionHammer/
├── game/
│   ├── main.py                 # Punkt startowy aplikacji
│   ├── core/                   # Zasady, aukcje, zdolności, AI, zapis i audyt
│   └── ui/                     # Interfejs i prezentacja kart w Pygame
├── data/
│   ├── cards_base_70.json      # Aktualne 70 kart podstawowych
│   ├── GAME_MASTER.json        # Ustrukturyzowana dokumentacja reguł
│   └── auction/
│       ├── KATALOG_AUKCYJNY_17_v22.json  # Aktualne aukcje
│       └── KATALOG_AUKCYJNY_12_v4.json   # Starszy katalog, zgodność zapisów
├── assets/                     # Grafika i elementy interfejsu
├── tests/                      # Testy automatyczne
├── tools/                      # Narzędzia, symulacje i diagnostyka
├── docs/                       # Szczegółowe zasady, raporty i historia zmian
├── reference/                  # Arkusze referencyjne kart
├── .github/workflows/          # Testy oraz budowanie wydania Windows
├── requirements.txt            # Zależność pygame-ce
└── README.md                   # Opis gry i instrukcja
```

W repozytorium używane są następujące formaty:

| Format | Przeznaczenie |
|---|---|
| **`.py`** | Kod gry, silnik zasad, przeciwnik komputerowy, testy i narzędzia |
| **`.json`** | Definicje kart, katalog aukcyjny, reguły, zapisy meczów i audyty |
| **`.md`** | Dokumentacja Markdown: README, zasady, raporty, historia prac |
| **`.xlsx`, `.csv`** | Arkusze i zestawienia do projektowania oraz weryfikacji kart |
| **`.png`** | Elementy graficzne i podglądy interfejsu |
| **`.yml`** | Konfiguracja automatycznych testów i kompilacji w GitHub Actions |
| **`.exe`, `.bat`, `.ps1`** | Uruchamianie gry i aktualizatora w Windows |
| **`.zip`** | Gotowa, przenośna paczka Windows z grą i wymaganymi plikami |

**Gdzie zapisuje się gra?** Na Windows zapis meczu ma format JSON i znajduje się domyślnie pod ścieżką:

```text
%LOCALAPPDATA%\AuctionHammer\savegame_v19.json
```

Końcówka `v19` oznacza nazwę **formatu zapisu**, a nie wersję aplikacji — również AuctionHammer 0.9.38 używa tego formatu. Dane obejmują m.in. karty, statusy, fazę aukcji i stan losowania, aby można było wznowić mecz. Dodatkowo po każdym zakończonym meczu zapisywany jest czytelny audyt ostatniej partii w formacie JSON **oraz** pełne archiwum wszystkich meczów w plikach JSON.GZ. Otworzysz je w grze przez **Menu → Historia meczów** albo w katalogu `%LOCALAPPDATA%\\AuctionHammer\\historia_meczow\\`. Plik `indeks.json` zawiera skrócone podsumowania, a kolejne zakończone mecze nie nadpisują poprzednich.

## Muzyka i credits

W grze odtwarzany jest album **Fantasy Tavern Music** (13 utworów, około 48 minut), w pętli podczas menu i rozgrywki. Bez odpowiedniego pliku audio gra działa bez muzyki.

**Pełne cytowanie:** Alek Kaczan (kompozytor), *Fantasy Tavern Music* / *Fantasy Tavern Album* (2021, 13 utworów), PGN Music (Paradox Gaming Network), wyd. 10.09.2021. [Oficjalny opis wydawcy](https://pgnmusic.com/album.php?title=Fantasy+Tavern+Music) · [Wydanie albumu i lista utworów](https://pgnmusic.bandcamp.com/album/fantasy-tavern-album) · [Strona PGN Music](https://pgnmusic.com/).

**Attribution (English):** *Fantasy Tavern Music* / *Fantasy Tavern Album* (2021), composed by **Alek Kaczan**, published by **PGN Music (Paradox Gaming Network)**. [Official album](https://pgnmusic.bandcamp.com/album/fantasy-tavern-album) · [Publisher](https://pgnmusic.com/).

Nagrania pozostają materiałem podmiotów trzecich i **nie podlegają licencji MIT kodu gry**. Więcej: [pełna lista 13 utworów, źródła i informacje o prawach](docs/THIRD_PARTY_MUSIC.md). Indywidualne ustalenia licencyjne nie są częścią publicznego README.

## Status, dokumentacja i licencja

**Aktualny status: 0.9.46 — grywalne demo offline, aktywnie rozwijane.** Dostępne są rozgrywka przeciw AI, 70 kart podstawowych, 17 archetypów i 51 wariantów aukcyjnych, animacje walki, zapis i archiwum meczów. Multiplayer online nie jest jeszcze dostępny.

**Ostatnie aktualizacje w skrócie:** stabilizacja silnika i poprawki pierwszej rozgrywki 0.9.38 (macierz 70+51, silniejsze niezmienniki własności i stref kart, testy akcji niedozwolonych i zapisów w toku wyboru), zasady v23, suwak licytacji, paginacja archiwum, czytelniejsze opisy warunkowych zdolności i dokładniejsze audyty z odtwarzaniem meczów. Szczegółowych poprawek nie powielamy tutaj — pełne informacje są w dokumentacji:

- [Status projektu i ograniczenia bieżącej wersji](docs/STATUS_PROJEKTU.md)
- [Raport stabilizacji silnika 0.9.38](docs/ENGINE_STABILIZATION_0938.md)
- [Pierwsze kroki, klawisze F11/A i czytelna historia](docs/QA_GUIDED_TURNS_0938.md)
- [Macierz 121 kart i wariantów](docs/ENGINE_COVERAGE_MATRIX_0938.csv)
- [Zasady i zmiany v23](docs/GAME_MASTER_v23_ADDENDUM.md)
- [Raport drugiego audytu v23](docs/QA_V23_SECOND_PASS_20261019.md)
- [Poprawki animacji i oznaczeń kart](docs/QA_UI_COMBAT_0935.md)
- [Katalog aukcji v22](docs/auction/RELEASE_V22_0931.md)
- [Historia starszych wydań](docs/README_HISTORIA_DO_0932.md)
- [Pełna dokumentacja zasad](AUCTIONHAMMER_MASTER.md)

**Licencja:** autorski kod źródłowy i własna dokumentacja AuctionHammer — [MIT](LICENSE). Muzyka i inne materiały podmiotów trzecich mogą podlegać osobnym warunkom. Autor projektu: **Mateusz Boćko**. [Dokładne credits i zasady wykorzystania muzyki](docs/THIRD_PARTY_MUSIC.md).

[**Pobierz najnowszą wersję Windows**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) · [Zgłoś błąd](https://github.com/MateuszBock0/AuctionHammer/issues)

## Szczegółowy audyt walk — 0.9.44

Po zakończeniu meczu gra automatycznie zapisuje **Księgę Starć** w `%LOCALAPPDATA%\\AuctionHammer\\AuctionHammer-KSIEGA-STARC.html` obok podpisanego JSON `AuctionHammer-OSTATNI-MECZ.json`. Na ekranie wyniku kliknij **KSIĘGA STARC [W]**, aby otworzyć raport w przeglądarce. Możesz filtrować po graczu, karcie, walce zakończonej zgonem; każdy atak pokazuje stan jednostek **PRZED / PO** (ATK, HP/MAX, pancerz, tarcza, statusy, licznik ataków), zapisane mikrooperacje oraz dziennik zdarzeń. W przypadku ataku z wyborem zdolności raport obejmuje również późniejszą komendę `choose`.

Oryginalny audyt zawiera teraz `payload.combat_analysis.attacks` i `summary.combat_attacks`. Silnik, reguły, RNG i format replay nie ulegają zmianie. Starsze podpisane pliki audytów można przeanalizować bez modyfikowania ich zawartości poleceniem `python -m game.core.combat_html \"ścieżka-do-audytu.json\"` w repozytorium źródłowym.

### 0.9.44 — sterowanie i stan jednostek

- Widoczny przycisk **WYJDŹ** w prawym górnym rogu planszy i **WYJDŹ Z GRY** w głównym menu. W trakcie niezapisanej partii zachowane potwierdzenie zapisu.
- Delikatne złoto-mosiężne podświetlenie ramki karty pod kursorem (karty na ręce i planszy).
- Przygaszone, szare **ilustracje** jednostek ogłuszonych, z wykorzystanym limitem ataków lub świeżo wystawionych bez Szybkiego ataku. Statystyki i statusy pozostają czytelne. Podwójny atak i Szybki atak bazują na faktycznym stanie silnika, nie na zgadywaniu przez UI. Oczekiwanie na turę samo w sobie nie przygasza jednostek.

