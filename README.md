# AuctionHammer

### Taktyczna gra karciana fantasy, w której zwycięstwo zależy nie tylko od kart na ręce, ale też od tego, co wylicytujesz.

**AuctionHammer** to darmowa, lokalna gra karciana dla jednego gracza przeciwko komputerowi. Budujesz armię, rozwijasz jednostki, zarządzasz monetami i co kilka rund rywalizujesz o potężne karty na aukcjach. Czasem warto wygrać licytację. Czasem lepiej oszczędzić monety, przeżyć kolejną rundę i poczekać na właściwą kartę.

**Aktualna wersja: 0.9.37 — grywalne demo na Windows** · **70 kart podstawowych** · **17 archetypów aukcyjnych** · **51 wariantów zdolności aukcyjnych** · **rozgrywka offline**

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

Opcjonalnie `URUCHOM_AUCTIONHAMMER.bat` sprawdza na GitHubie dostępność nowszej wersji i uruchamia posiadaną grę także wtedy, gdy sprawdzenie aktualizacji się nie powiedzie. Zachowaj `AuctionHammer.exe` razem z folderem `_internal`; samodzielne przeniesienie tylko pliku EXE może uniemożliwić uruchomienie.

> To rozwijane demo, nie ukończona komercyjna produkcja. Automatyczne testy i wydania Windows są publikowane na GitHubie, ale w grze nadal mogą wystąpić błędy.

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
| Monety | **+1 moneta dla obu graczy po pełnej rundzie**; gracz zaczynający jako drugi dostaje **+3 monety na start**. W nowych meczach v22 na koniec własnej tury otrzymujesz dodatkowo **5 − liczba własnych jednostek** monet |
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

## Sterowanie i przydatne funkcje

| Akcja | Sterowanie |
|---|---|
| Wystaw kartę | Kliknij kartę na ręce, następnie własne pole; możesz też przeciągnąć kartę |
| Zaatakuj | Kliknij gotową jednostkę i legalny cel ataku |
| Wybierz efekt | Kliknij opcję po prawej stronie; **1–6** wybiera opcje na aktualnej stronie |
| Zakończ turę | **Spacja** |
| Informacje o karcie | **I** |
| Historia zdarzeń | **H** |
| Powtórka meczu | **P** |
| Włącz/wyłącz efekty wizualne | **A** |
| Menu i zapis | **M** |
| Pełny ekran | **F11** |
| Nowa partia | **R** |

Podczas aukcji możesz składać oferty w panelu, pasować i wybierać karty myszą. Dostępne są również cyfry oraz **Enter** do zatwierdzenia wpisanej kwoty.

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

Końcówka `v19` oznacza nazwę **formatu zapisu**, a nie wersję aplikacji — również AuctionHammer 0.9.33 używa tego formatu. Dane obejmują m.in. karty, statusy, fazę aukcji i stan losowania, aby można było wznowić mecz. Dodatkowo po każdym zakończonym meczu zapisywany jest czytelny audyt ostatniej partii w formacie JSON **oraz** pełne archiwum wszystkich meczów w plikach JSON.GZ. Otworzysz je w grze przez **Menu → Historia meczów** albo w katalogu `%LOCALAPPDATA%\\AuctionHammer\\historia_meczow\\`. Plik `indeks.json` zawiera skrócone podsumowania, a kolejne zakończone mecze nie nadpisują poprzednich.

## Muzyka — pełny album Fantasy Tavern (PGN Music)

AuctionHammer pozostaje **zawsze darmowym MVP open source**, w pełni
dostępnym na GitHubie na licencji **MIT** (dla kodu źródłowego).

Gra odtwarza **wszystkie 13 utworów** w oryginalnej kolejności,
po czym zaczyna album ponownie — około **47 min 44 s na cykl**.
Muzyka trwa dalej podczas menu, rozgrywki i kolejnych meczów.
Najprościej: umieść **`music_auctionhammer.mp3`** w
`AuctionHammer/assets/music/`. W przenośnej wersji Windows jest to
folder `assets/music` obok pliku `AuctionHammer.exe` (nie w
`_internal`). Gra odtworzy jeden plik MP3 w nieskończonej pętli.
Starsze nazwy pełnego albumu oraz zestaw 13 ponumerowanych utworów
nadal są obsługiwane.

**Plik MP3 może być dystrybuowany razem z grą:** właściciel projektu
potwierdził uzyskanie zgody na wykorzystanie i udostępnianie muzyki.
Po dodaniu `assets/music/music_auctionhammer.mp3` przez standardowy
`git push`, album znajdzie się w repozytorium i automatycznie
w paczce ZIP na Windows. **38,2 MB mieści się w limicie Git (100 MiB)**,
choć jest za duże na formularz GitHub w przeglądarce.
Muzyka jest podpisana w **Menu → CREDITS**, README oraz dokumentacji
prawnej. Nagrania mają osobne warunki licencyjne i nie podlegają MIT.
Bez pliku gra nadal uruchamia się bez dźwięku.

[Jak umieścić album](assets/music/README.md) ·
[Pochodzenie, autorzy i licencja muzyki](docs/THIRD_PARTY_MUSIC.md)

## Status, dokumentacja i licencja

**0.9.34 to aktywnie rozwijane demo**, z lokalnym przeciwnikiem i zaimplementowanymi aukcjami v22 (17 archetypów, 51 wariantów). Aktualna wersja zawiera również balans v21 kart podstawowych. Na tym etapie **nie ma multiplayera online**.

- [Pobierz najnowsze wydanie Windows](https://github.com/MateuszBock0/AuctionHammer/releases/latest)
- **0.9.37:** niezależny audyt v23: jawny, podpisany stan `ruleset_version` i oczekującej wypłaty za wolne pola (nowe audyty schema 2, bez modyfikowania hashy starych historii); widoczne na początku opisu zastrzeżenia aukcyjne A014/A015/A018 oraz informacje o efektach awaryjnych S86/S87/S88/S32/S95. Nowe testy reprodukcyjne A014 z Tarczą, fal śmierci A015 i pełne replaye obu schematów.\n- **0.9.36:** zasady v23: suwak aukcyjny, korekty 10 opisów, dochód po zakończeniu fal śmierci, poprawiona A015, A018 na ostatniej aukcji oraz efekty zastępcze S86–S88/S32/S95. Paginacja archiwum po 4; potwierdzenie odtwarzania MP3. Przeczytaj `docs/GAME_MASTER_v23_ADDENDUM.md`.\n- **0.9.35:** delikatne filtry kart na planszy: czerwony (Podwójny atak), srebrny (Prowokacja), żółty (Tarcza/Ochrona), bez filtrów na chwilowe statusy; podświetlenie walczących, spadek widocznych PŻ, wyszarzenie umierającej karty przed zniknięciem. W archiwum widać wersję gry każdego meczu; efekty bez legalnego celu otrzymują wyjaśnienie w dzienniku. Surowe HP w audytach bez zmian; osobno wartość do wyświetlania co najmniej 0.
- **0.9.34:** poprawki S11 (trucizna bohatera), A015 (wybór wrogiego celu), S85 (etykieta leczenia), ocena ATK/PŻ/zdolności przez AI oraz **+1 moneta za każde wolne pole planszy na koniec własnej tury** (0–5, także dla komputera). Stare zapisy zachowują starą ekonomię.
- **0.9.33:** Kartograf odzyskuje karty z cmentarza przy pustej talii; Królowa przywołuje Żołnierzy 1/1, 2/2 lub 3/3, a wszystkie mecze są trwale archiwizowane.
- [Zasady i interpretacje aukcji v22](docs/auction/RELEASE_V22_0931.md) · [Stabilizacja 0.9.32](docs/auction/RELEASE_V22_STABILIZATION_0932.md)
- [Game Master / reguły projektu](AUCTIONHAMMER_MASTER.md)
- [Archiwum wcześniejszego README i historii wydań](docs/README_HISTORIA_DO_0932.md)
- [Zgłoś problem lub propozycję](https://github.com/MateuszBock0/AuctionHammer/issues)

Projekt udostępniany jest na licencji [MIT](LICENSE). Autor: **Mateusz Boćko**.
