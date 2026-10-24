# AuctionHammer

**Taktyczna gra karciana fantasy dla jednego gracza przeciwko komputerowi.** Budujesz pięcioosobową armię na stałych polach, rozwijasz karty na ręce i zdobywasz nowe jednostki na aukcjach. Wszystko działa lokalnie, bez serwera i bez konta.

**Aktualna wersja: 0.9.70** · Windows · offline · język polski · **70 kart podstawowych** · **17 archetypów aukcyjnych / 51 wariantów zdolności**.

[**Pobierz najnowszą wersję Windows**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) · [Zgłoś problem](https://github.com/MateuszBock0/AuctionHammer/issues) · [Zobacz aktualne zasady](docs/CURRENT_MVP_RULES_0964.md) · [Game Master / historia](AUCTIONHAMMER_MASTER.md)

> **English:** A free, offline, single-player fantasy card game against AI. Build a five-unit board, grow cards in your hand and bid for unique auction cards. The interface is in Polish. Windows builds do not require Python.

## 1. Pobierz i zagraj (Windows)

1. Otwórz [**najnowsze wydanie**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) i pobierz `AuctionHammer-Windows.zip`.
2. Rozpakuj ZIP w wybranym folderze.
3. Uruchom `AuctionHammer.exe` z folderu `AuctionHammer`. Możesz także użyć `GRAJ_BEZ_INTERNETU.bat`.

Nie instalujesz Pythona ani dodatkowych bibliotek. Po pobraniu gra działa bez internetu.

| Plik | Do czego służy |
|---|---|
| `AuctionHammer.exe` | Bezpośrednie uruchomienie aktualnie rozpakowanej gry |
| `GRAJ_BEZ_INTERNETU.bat` | Start lokalny bez sprawdzania aktualizacji |
| `URUCHOM_AUCTIONHAMMER.bat` | Sprawdzenie nowej wersji i bezpieczna aktualizacja |
| `COFNIJ_AKTUALIZACJE.bat` | Powrót do wcześniej działającej wersji |

Aktualizator sprawdza sumę **SHA-256**, instaluje wydania obok siebie i nie nadpisuje plików zapisanych meczów. Pierwszą instalację starszą niż 0.9.43 najlepiej rozpocząć od nowego ZIP. Szczegóły: [QA instalatora](docs/QUALITY_RELEASE_0943.md).

## Nowość 0.9.70 — 51 pięknych kart aukcyjnych w finalnym pixel arcie

Wszystkie **17 kart aukcyjnych w 3 rzadkościach** dostały kompletną nową oprawę, dopasowaną do stylu 70 kart podstawowych: **51 portretów 295×209** oraz **51 szerokich bannerów 295×78**. Oznaczenia, nazwy i ramki rysuje gra — same ilustracje są czyste, bez napisów i ramek.

- W ręce i na planszy używane są **gotowe szerokie ilustracje**; w powiększonym podglądzie po najechaniu i w [G] — gotowe portrety.
- Poprzedni system z 0.9.69, który nakładał nieprzezroczyste kwadratowe obrazki postaci na nowe tła, **został wyłączony i usunięty z renderera**. Nie powstają prostokątne nakładki.
- Bez rozmywania pikseli (nearest-neighbour) i bez obcego generatora/API podczas działania gry. Oryginalne 96×96 PNG pozostają wyłącznie awaryjną kompatybilnością, gdyby któregoś nowego pliku brakowało.
- `assets/auction/final/manifest.json` przechowuje SHA-256 wszystkich 102 grafik. Test `tests/test_auction51_final_0970.py` sprawdza 51 ID/rzadkości, faktyczne PNG, ich użycie w Pygame oraz fallback.
- **Bez zmian mechaniki gry**, zdolności, RNG, aukcji i podglądów kart.

## Nowość 0.9.69 — 51 spójnych kompozycji pixel art dla kart aukcyjnych

- Wszystkie **17 archetypów aukcyjnych × 3 rzadkości = 51 grafik** dostały nową oprawę, z dwiema kompozycjami każda: **295×78 (pasek)** i **295×209 (portret)**.
- **Rozpoznawalna postać jest zawsze tą samą postacią z oryginalnego pliku** `assets/auction/Axxx_rzadkosc.png`. Nowo wygenerowany pixel art buduje szerokie tło; na pierwszym planie Pygame nakłada autentyczną grafikę odpowiedniego archetypu i rzadkości.
- Żadnego bezmyślnego przycinania postaci, rozciągania głów lub małych kwadratów na środku paska. Obrazy są składane raz i cache'owane. Nie trzeba płatnego API, kluczy ani zewnętrznego generatora.
- W dużym podglądzie [G] pozostaje pełna **oryginalna** ilustracja karty. Podgląd hover planszy i ręki pozostaje aktywny.
- Nowe tła i ich 102 podpisane sumy SHA-256 znajdują się w `assets/auction/pixel_art/auction51_scenes.zip`; test `tests/test_auction51_pixelart_0969.py` weryfikuje je wraz z autentycznymi kartami.

## Nowość 0.9.68 — podgląd jednostek na planszy i pełne grafiki aukcyjne

- Najechanie na **dowolną wystawioną jednostkę**, swoją lub przeciwnika, przez ok. **420 ms** pokazuje dużą kartę tak jak dla ręki, z bieżącym ATK bojowym, PŻ, pancerzem, statusami i licznikiem ataków. Podgląd nie zmienia wyboru jednostki ani zasad gry.
- Okno podglądu umieszczamy poza jednostką pod kursorem. Wyjaśnienia statusów nadal mają pierwszeństwo, a podczas modalnych decyzji/aukcji podgląd się nie pojawia.
- **Karty aukcyjne** na planszy i w ręce skalowane są proporcjonalnie w trybie `cover`, wypełniając całe pole grafiki, tak jak podstawowe karty, zamiast pozostawać małą kwadratową miniaturą.
- W widoku powiększonej oryginalnej ilustracji [G] zachowujemy `contain`, aby było widać całą grafikę.
- Test regresyjny: `tests/test_board_hover_auction_art_0968.py`.

## Nowość 0.9.67 — zielone/czerwone statystyki, srebrny pancerz i ATK Generała

- **ATK na karcie jest wartością bojową.** Jeśli jednostka ma 9 ATK, a Generał Oddziału Natarcia podwaja obrażenia zwykłych ataków, pokazuje się **18 na zielono**, zamiast dawnego `9→18`. Gdy Generał zniknie, karta pokazuje 9. Nie występuje drugi mnożnik obrażeń.
- **Zielony ATK** oznacza wzmocnienie, **czerwony ATK** osłabienie; normalna wartość jest złota. Wykorzystujemy faktyczne statystyki i aktywną premię, nie szacowanie na podstawie treści karty.
- **PŻ** pokazuje bieżące życie oraz `/MAX`; gdy MAX PŻ jest podniesione/obniżone, **koloruje się część `/MAX`** na zielono/czerwono. Same rany nie są mylone z debuffem MAX PŻ.
- **Pancerz** jednostki widoczny jest jako mały **srebrny medalion z liczbą** przy prawym górnym brzegu statystyki PŻ.
- Balans, zapisy, replay i reguła walki nie zostały zmienione: Generał już wcześniej podwajał obrażenia standardowego ataku. Zmiana dotyczy *widocznego ATK bojowego*; inne efekty zależne od zwykłej statystyki ATK nie zostały wzmocnione.

## Nowość 0.9.66 — czytelne obrażenia po premii Generała

Przy premii Generała Oddziału Natarcia na karcie jednostki wyświetlamy **ATK → obrażenia**, np. **9→18**, a panel boczny i podgląd [I] rozpisują `9 × 2 = 18` jako obrażenia **przed tarczą i pancerzem**. Sama statystyka ATK pozostaje 9; Generał zwiększa obrażenia zwykłego ataku, nie ATK. Podwojona liczba ataków nadal jest oddzielnym efektem. Po utracie aktywnej premii licznik wraca automatycznie do 9. Żadne zasady walki, replay ani balans nie zostały zmienione.

## Nowość 0.9.65 — komplet 70 kart podstawowych w pixel arcie

Każda z **70 zwykłych kart** ma własną ilustrację w pixel arcie (140 plików PNG: po jednym portrecie i poziomej miniaturce dla każdej karty). W ręce, na planszy i w podglądzie [G] gra używa nowych ilustracji bez rozmywania pikseli (nearest-neighbor). Portrety i ich sumy SHA-256: [manifest](assets/cards/pixel_art/manifest.json). Wykonane bez zewnętrznego API, abonamentów i generowania po stronie gracza. **S34 jest zwykłą kartą podstawową**, natomiast specjalny token `SUM_START_GUARD` zachowuje trzy osobne portrety awansu. Silnik, AI, aukcje, statusy, zapisy i balans bez zmian. [Testy i dokumentacja artu](docs/PIXEL_ART_70.md).

## Nowość 0.9.64 — zawsze ustalona kolejność pierwszych meczów

**Pierwszy mecz po uruchomieniu aplikacji rozpoczyna komputer, czyli Ty grasz jako drugi. Drugi nowy mecz rozpoczynasz Ty, a komputer jest drugi.** Następne mecze powtarzają ten układ naprzemiennie (3. komputer, 4. Ty itd.). Ta kolejność resetuje się przy **nowym uruchomieniu aplikacji**. Nie zapisuje się jej na stałe między uruchomieniami.

**NOWY MECZ** z pierwszego menu, **KONTYNUUJ** oraz pierwszy **SAMOUCZEK** wykorzystują przygotowaną pierwszą partię i nie pomijają jej. Dopiero kolejny nowy mecz przełącza kolejność. Anulowanie potwierdzenia restartu niczego nie przełącza. **WCZYTAJ ZAPIS** zachowuje kolejność z pliku, a następny nowy mecz otrzymuje kolejność przeciwną do wczytanego meczu.

W każdym meczu **drugi gracz** (Ty albo komputer) wybiera bonus: **+3 monety** lub **Chorążego „Zawsze zdąży” 2 ATK / 1 PŻ / 4 pancerza**. Silnik nadal losuje kolejność deterministycznie z seeda; aplikacja dobiera seed odpowiadający tej naprzemiennej kolejności, dlatego archiwalne audyty i symulacje nie zmieniają zasad.

**[Aktualny Game Master MVP 0.9.64](docs/CURRENT_MVP_RULES_0964.md)** · [Dane do odczytu maszynowego](data/MVP_RULES_0964.json).

## 2. Jak wygrać?

Celem jest zmniejszenie PŻ bohatera komputera z **100 do 0**, zanim on zrobi to samo z Twoim bohaterem. Gra jest **turowa**, ale w swojej turze możesz wykonać dostępne ataki i wystawić kartę w wybranej kolejności.

| Element | Zasada |
|---|---|
| Kolejność rozpoczynania meczów | **Mecz 1: komputer zaczyna, gracz jest drugi. Mecz 2: gracz zaczyna, komputer jest drugi.** Kolejne mecze naprzemiennie w tej samej sesji aplikacji |\n| Początek meczu | Każdy ma 5 kart na ręce i 5 w talii; karty pochodzą ze wspólnej puli 70 różnych jednostek |
| Pierwsza decyzja | Wymiana do 3 kart z początkowej ręki (można wymienić 0) |
| Wystawianie | Zasadniczo **1 karta na własną turę**, bez kosztu w monetach |
| Plansza | **5 fizycznych pól** po każdej stronie; zgon nie przesuwa sąsiadów |
| Pełna plansza | Możesz zastąpić jednostkę w dozwolony sposób — nowa pozostaje na jej polu |
| Jednostki | Mają ATK, PŻ, frakcję, aktywację zdolności i postęp rozwoju na ręce |
| Atak | Kliknij swoją gotową jednostkę, potem legalny cel; Prowokacja i statusy mogą ograniczać wybór |
| Monety | Służą przede wszystkim do aukcji, **nie do zagrywania zwykłych kart** |
| Rekompensata za drugi ruch | Drugi gracz wybiera **Chorążego 2 ATK / 1 PŻ / 4 trwałego pancerza** albo **+3 monety** |
| Ekonomia dodatkowa | +1 moneta dla obu po pełnej rundzie; w aktualnym wariancie v22 dochód za własne puste pola na koniec tury |

**Ważne:** Chorąży nie atakuje w swojej pierwszej turze. Zapisane mecze ze starszych wersji zachowują swoje historyczne reguły.

### Pięć frakcji

- **Elfy** — zdolność przy wystawieniu.
- **Dzikie bestie** — zdolność przy ataku.
- **Potwory** — zdolność przy śmierci.
- **Krasnoludy** — zdolność na koniec tury.
- **Ludzie** — zdolności pasywne.

**Ważne rozróżnienie kart:** **S34** (Chorąży Królewskiej Kompanii) to karta podstawowa, wzmacniająca sąsiada lub osłabiająca wroga naprzeciwko; **A002** (Generał Oddziału Natarcia) jest wyłącznie kartą aukcyjną z inną zdolnością.\n\nKarty podstawowe zyskują statystyki podczas kolejnych tur spędzonych na ręce, a ich zdolności rozwijają się co trzy takie tury. Szczegóły konkretnej karty otworzysz przyciskiem **I**.

**Czytelność walki (0.9.55):** legalny cel ataku reaguje na najechanie kursorem; po ataku panel **SKUTKI ATAKU** pokazuje rzeczywistą zmianę PŻ i tarczy, a pełny dziennik jest pod **H**. Ruchy AI są szybsze, animacje trafień krótsze. Ataki z wyborem zdolności pokazują wynik dopiero po rozstrzygnięciu wyboru.

**Czytelność decyzji (0.9.56):** Trzy tempa AI zmienisz klawiszem **F8** (spokojne / standardowe / szybkie; bez zmiany decyzji komputera).  panel ostatniego ataku pokazuje PŻ, tarczę, pancerz i nowe statusy, a po najechaniu na jego miejsce rozwija pełniejszy raport. Po zaznaczeniu S34 lub S108 gra wskazuje faktyczny obszar działania na stałych polach; nie gwarantuje aktywacji statusu. W prawej kolumnie zobaczysz szacowany przychód za obecnie wolne pola oraz rundy do najbliższej aukcji, o ile są dostępne oferty. Prognoza nie uwzględnia przyszłych efektów końca tury.\n\n## 3. Aukcje w skrócie

Co trzy ukończone rundy może rozpocząć się aukcja. System losuje **trzy oferty** z dostępnych archetypów; gracze licytują **prawo pierwszego wyboru**, a nie cały zestaw. Każdy może otrzymać po jednej karcie aukcyjnej. Takie karty nie należą do podstawowej puli dobierania.

| Rzadkość | Szansa w ofercie | Oprawa |
|---|---:|---|
| Podstawowa | 60% | Brązowa |
| Rzadka | 30% | Srebrno-błękitna |
| Legendarna | 10% | Złota, z ornamentami i świetlistą ilustracją |

**Korekta wytrzymałości Chorążego (0.9.63):** Nowy startowy Chorąży „Zawsze zdąży” ma **2 ATK / 1 PŻ / 4 trwałego pancerza**. Pancerz pochłania obrażenia i nie odnawia się po zabójstwach; kolejne zabójstwa podnoszą ATK i PŻ o dotychczasowe wartości. Po 3 zabójstwach jego bazowe statystyki to **5 ATK / 7 MAX PŻ**, a pozostały pancerz zależy od otrzymanych ciosów. Opisy wyboru, karty i podglądu wskazują prawdziwą zdolność. Mecze zapisane w 0.9.62 i wcześniej zachowują swoje początkowe 2/5.\n\n**Easter egg Chorążego „Zawsze zdąży” (0.9.62):** Jeżeli drugi gracz wybierze na starcie **Chorążego** (`SUM_START_GUARD`), każdy pokonany jego własnym standardowym atakiem przeciwnik daje **+1 ATK, +2 MAX PŻ i +2 bieżące PŻ**. Premia nalicza się najwyżej **3 razy**: po 0/1/2+ zabójstwach Chorąży pokazuje grafikę podstawową/rzadką/legendarną. Kontratak, efekt pośredni i obustronna śmierć nie liczą się. **S34 Chorąży Królewskiej Kompanii odzyskał swoją oryginalną, niezmienną grafikę.** Stare zapisane mecze i audyty pozostają zgodne ze swoimi historycznymi regułami.

**Oprawa graficzna Chorążego (0.9.61 → 0.9.62):** Trzy zatwierdzone portrety 96×96 pozostają w grze, ale od 0.9.62 należą do **startowego Chorążego „Zawsze zdąży”**, a nie S34. Wersję grafiki określa liczba bezpośrednich zabójstw. Ikony okna i pliku `AuctionHammer.exe` nie uległy zmianie. [Grafiki i manifest SHA-256](docs/CHORAZY_ART_0961.md).

<img src="assets/branding/chorazy_zawsze_zdazy_icon.png" alt="Chorąży — ikona fantasy z królewskim sztandarem" width="112">

**Sterowanie i czytelność walki (0.9.60):** Podczas wyboru zdolności Królowej Tysiąca Twarzy (A010) kliknij samą Królową, aby wybrać **WZMOCNIJ**, albo dowolne wolne własne pole, aby wybrać **PRZYWOŁAJ** (faktyczne rozmieszczenie przywołanych jednostek pozostaje zgodne z regułami silnika). Legalne cele są podświetlone; przy pełnej planszy dostępne jest tylko wzmocnienie. Jednostka ogłuszona pokazuje wyraźne **OGŁUSZONY** zamiast mylącego licznika ataków mimo Szybkiego Ataku. Sterowanie przyciskami wyboru pozostaje dostępne. Zasady, obrażenia, AI, RNG i archiwalne audyty bez zmian.

**Hotfix 0.9.59 — czytelność efektów i archiwalne audyty:** Na kartach na planszy i w prawym panelu priorytet otrzymuje potwierdzona premia Generała do dwóch ataków i obrażeń standardowego ataku ×2. Księga Starć odtwarza dane prezentacyjne z podpisanej historii akcji, również ze starszych audytów, bez modyfikowania pliku JSON. Odtwarzanie zachowuje zgodność z dawnymi komunikatami A002 oraz krótkotrwałym wariantem dziennika z buildu 0.9.58. Bez zmian mechaniki walki, balansu i zapisów.

**Tło ilustracji aukcyjnych (0.9.58):** Kolor przestrzeni wokół grafiki wynika automatycznie z dominującego odcienia jej bieżącego wariantu PNG. Tło dopasowuje się do rzadkości karty i nie wymaga ręcznego ustawiania palety. Zachowujemy proporcje ilustracji, czytelność podpisów oraz dotychczasowy wygląd kart podstawowych.\n\n**Ilustracje kart aukcyjnych (0.9.57):** Wszystkie 17 archetypów posiada 3 osobne ilustracje (podstawowa, rzadka, legendarna): łącznie 51 plików PNG 96×96. Grafika zmienia się wraz z aktualną rzadkością karty i jest widoczna podczas aukcji, na planszy, w ręce oraz w podglądzie. Integralność każdej grafiki sprawdza `assets/auction/manifest.json` (SHA-256). [Szczegóły i weryfikacja](docs/AUCTION_SPRITES_0957.md).\n\n**Wygląd legendarnych kart (0.9.54):** ciemnoametystowe tło, ciepły złoty blask w obrębie ilustracji, rzeźbione narożniki i klejnot z subtelną animacją. Ten sam motyw zdobi legendarne oferty aukcyjne. Wyłączenie animacji klawiszem **A** usuwa pulsowanie, ale zachowuje ozdoby. Wszystkie nazwy, opisy, statusy oraz ATK/PŻ pozostają na nieprzezroczystych, czytelnych panelach.

Karta aukcyjna awansuje na kolejny stopień rzadkości co trzy pełne rundy od zakupu (maksymalnie do legendarnej). Zmienia się wariant jej zdolności, **nie** bazowe ATK i PŻ ustalone podczas zakupu. Katalog zawiera 17 archetypów i 51 wariantów zdolności.

Na ekranie aukcji wybierz **PEŁNA ZDOLNOŚĆ**, aby przejrzeć kompletny opis, a dłuższy tekst przewijaj kółkiem myszy. [Dokładne zasady aukcji v22](docs/auction/RELEASE_V22_0931.md).

## 4. Sterowanie

| Co chcesz zrobić? | Jak? |
|---|---|
| Wystawić kartę | Kliknij kartę na ręce i własne pole albo **przeciągnij** ją na pole |
| Zaatakować | Kliknij swoją gotową jednostkę, następnie podświetlony cel |
| Wybrać cel zdolności | Kliknij podświetlony cel lub opcję w panelu; cyfry **1–6** wybierają widoczne opcje |
| Skończyć turę | **Spacja** |
| Otworzyć pełny opis karty | **I** |
| Podejrzeć historię | **H** |
| Odtworzyć zapisane w pamięci stany | **P** |
| Otworzyć menu | **M** |
| Otworzyć pomoc | **F1** |
| Włączyć/wyłączyć podpowiedzi | **T** |
| Włączyć/wyłączyć animacje | **A** |
| Przełączyć pełny ekran | **F11** |
| Rozpocząć nową partię | **R** |

Złote obrysy oznaczają legalne pola wystawienia, turkusowe — legalne cele ataku, a fioletowe — cele wyboru zdolności. Karty na ręce można oglądać bez zagrywania. Zdolności i liczby na mniejszych kartach bywają skracane **z widocznym wielokropkiem**; pełne objaśnienie pozostaje pod **I**.

## 5. Samouczek, poziomy trudności i zapisy

W menu możesz rozpocząć **samouczek** lub zwykły mecz. Pomoc F1 wyjaśnia rozgrywkę, walkę i aukcje. Komputer oferuje poziomy trudności **łatwy, normalny i trudny**.

Grę można zapisywać i wczytywać. Na Windows zapisy znajdują się w `%LOCALAPPDATA%\AuctionHammer`. Po zakończeniu meczu powstaje podpisany audyt, a pełniejsze materiały diagnostyczne obejmują archiwum meczów i **Księgę Starć** (HTML).

To jest **gra tylko przeciw AI** — nie ma lobby, trybu dwóch osób ani serwera multiplayer.

## 6. Uruchomienie z kodu źródłowego

Wymagany Python 3.12 i biblioteki z `requirements.txt`, w tym pygame-ce.

```bash
git clone https://github.com/MateuszBock0/AuctionHammer.git
cd AuctionHammer
python -m pip install -r requirements.txt
python -m game.main
```

Testy automatyczne:

```bash
python -m unittest discover -s tests -v
python -m tools.check_fixed_board_0951 --games 20
```

| Katalog / plik | Przeznaczenie |
|---|---|
| `game/core/` | Autorytatywne zasady gry, AI, aukcje, zapisy i audyty |
| `game/ui/` | Interfejs pygame-ce, grafika kart, przycinanie i zawijanie tekstów |\n| `assets/auction/` | 51 oryginalnych sprite’ów aukcyjnych i manifest SHA-256 |
| `data/cards_base_70.json` | 70 definicji podstawowych kart |
| `data/auction/` | Aktywny katalog aukcyjny v22 i dane kompatybilności |
| `docs/` | Specyfikacja, kontrola jakości, wyniki symulacji i historia zmian |
| `tests/` | Testy silnika i prezentacji, bez wpływania na mechanikę |
| `VERSION.json` | Bieżąca wersja aplikacji i metadane |

## 7. Dokumentacja i ograniczenia MVP

- [Status projektu](docs/STATUS_PROJEKTU.md) — bieżący zakres, potwierdzone testy i nierozstrzygnięte kwestie.
- [Dokument główny](AUCTIONHAMMER_MASTER.md) i [aneks reguł v23](docs/GAME_MASTER_v23_ADDENDUM.md) — opis działania mechanik.
- [Aukcje v22](docs/auction/RELEASE_V22_0931.md) — katalog i reguły licytacji.
- [Stałe pola i rzadkości](docs/BOARD_CARD_IDENTITY_0951.md) — taktyka planszy.
- [Wygląd legendarnych kart 0.9.54](docs/LEGENDARY_VISUAL_0954.md) — zmiany wyłącznie wizualne i testy.
- [Czytelność opisów 0.9.53](docs/UI_TEXT_ACCEPTANCE_0953.md) — ograniczenia paneli, testy oraz checklista Windows.
- [Historyczne dokumenty](docs/README_HISTORIA_DO_0932.md) — wcześniejsze etapy projektu.

MVP jest aktywnie rozwijane. Zielone testy automatyczne potwierdzają badane scenariusze, ale **nie zastępują ręcznego testowania** na prawdziwym ekranie Windows i z różnymi skalami DPI.

## 8. Muzyka, prawa i autorstwo

W grze wykorzystano muzykę **Fantasy Tavern Music / Fantasy Tavern Album** (2021, 13 utworów), skomponowaną przez **Aleka Kaczana (Alek Kaczan)** i wydaną przez **PGN Music (Paradox Gaming Network)**. [Album](https://pgnmusic.bandcamp.com/album/fantasy-tavern-album) · [Pełne credits i zasady wykorzystania](docs/THIRD_PARTY_MUSIC.md).

Kod autorski i własna dokumentacja są udostępniane na licencji [MIT](LICENSE). Muzyka i inne materiały podmiotów trzecich **nie** stają się objęte MIT. Autor projektu: **Mateusz Boćko**.

---

[**Pobierz grę**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) · [**Zgłoś błąd**](https://github.com/MateuszBock0/AuctionHammer/issues)
