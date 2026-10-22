# AuctionHammer

**Taktyczna gra karciana fantasy dla jednego gracza przeciwko komputerowi.** Budujesz pięcioosobową armię na stałych polach, rozwijasz karty na ręce i zdobywasz nowe jednostki na aukcjach. Wszystko działa lokalnie, bez serwera i bez konta.

**Aktualna wersja: 0.9.53** · Windows · offline · język polski · **70 kart podstawowych** · **17 archetypów aukcyjnych / 51 wariantów zdolności**.

[**Pobierz najnowszą wersję Windows**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) · [Zgłoś problem](https://github.com/MateuszBock0/AuctionHammer/issues) · [Zobacz zasady](AUCTIONHAMMER_MASTER.md)

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

## 2. Jak wygrać?

Celem jest zmniejszenie PŻ bohatera komputera z **100 do 0**, zanim on zrobi to samo z Twoim bohaterem. Gra jest **turowa**, ale w swojej turze możesz wykonać dostępne ataki i wystawić kartę w wybranej kolejności.

| Element | Zasada |
|---|---|
| Początek meczu | Każdy ma 5 kart na ręce i 5 w talii; karty pochodzą ze wspólnej puli 70 różnych jednostek |
| Pierwsza decyzja | Wymiana do 3 kart z początkowej ręki (można wymienić 0) |
| Wystawianie | Zasadniczo **1 karta na własną turę**, bez kosztu w monetach |
| Plansza | **5 fizycznych pól** po każdej stronie; zgon nie przesuwa sąsiadów |
| Pełna plansza | Możesz zastąpić jednostkę w dozwolony sposób — nowa pozostaje na jej polu |
| Jednostki | Mają ATK, PŻ, frakcję, aktywację zdolności i postęp rozwoju na ręce |
| Atak | Kliknij swoją gotową jednostkę, potem legalny cel; Prowokacja i statusy mogą ograniczać wybór |
| Monety | Służą przede wszystkim do aukcji, **nie do zagrywania zwykłych kart** |
| Rekompensata za drugi ruch | Drugi gracz wybiera **Chorążego 2 ATK / 5 PŻ** albo **+3 monety** |
| Ekonomia dodatkowa | +1 moneta dla obu po pełnej rundzie; w aktualnym wariancie v22 dochód za własne puste pola na koniec tury |

**Ważne:** Chorąży nie atakuje w swojej pierwszej turze. Zapisane mecze ze starszych wersji zachowują swoje historyczne reguły.

### Pięć frakcji

- **Elfy** — zdolność przy wystawieniu.
- **Dzikie bestie** — zdolność przy ataku.
- **Potwory** — zdolność przy śmierci.
- **Krasnoludy** — zdolność na koniec tury.
- **Ludzie** — zdolności pasywne.

**Ważne rozróżnienie kart:** **S34** (Chorąży Królewskiej Kompanii) to karta podstawowa, wzmacniająca sąsiada lub osłabiająca wroga naprzeciwko; **A002** (Generał Oddziału Natarcia) jest wyłącznie kartą aukcyjną z inną zdolnością.\n\nKarty podstawowe zyskują statystyki podczas kolejnych tur spędzonych na ręce, a ich zdolności rozwijają się co trzy takie tury. Szczegóły konkretnej karty otworzysz przyciskiem **I**.

## 3. Aukcje w skrócie

Co trzy ukończone rundy może rozpocząć się aukcja. System losuje **trzy oferty** z dostępnych archetypów; gracze licytują **prawo pierwszego wyboru**, a nie cały zestaw. Każdy może otrzymać po jednej karcie aukcyjnej. Takie karty nie należą do podstawowej puli dobierania.

| Rzadkość | Szansa w ofercie | Oprawa |
|---|---:|---|
| Podstawowa | 60% | Brązowa |
| Rzadka | 30% | Srebrno-błękitna |
| Legendarna | 10% | Złota |

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
| `game/ui/` | Interfejs pygame-ce, grafika kart, przycinanie i zawijanie tekstów |
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
- [Czytelność opisów 0.9.53](docs/UI_TEXT_ACCEPTANCE_0953.md) — ograniczenia paneli, testy oraz checklista Windows.
- [Historyczne dokumenty](docs/README_HISTORIA_DO_0932.md) — wcześniejsze etapy projektu.

MVP jest aktywnie rozwijane. Zielone testy automatyczne potwierdzają badane scenariusze, ale **nie zastępują ręcznego testowania** na prawdziwym ekranie Windows i z różnymi skalami DPI.

## 8. Muzyka, prawa i autorstwo

W grze wykorzystano muzykę **Fantasy Tavern Music / Fantasy Tavern Album** (2021, 13 utworów), skomponowaną przez **Aleka Kaczana (Alek Kaczan)** i wydaną przez **PGN Music (Paradox Gaming Network)**. [Album](https://pgnmusic.bandcamp.com/album/fantasy-tavern-album) · [Pełne credits i zasady wykorzystania](docs/THIRD_PARTY_MUSIC.md).

Kod autorski i własna dokumentacja są udostępniane na licencji [MIT](LICENSE). Muzyka i inne materiały podmiotów trzecich **nie** stają się objęte MIT. Autor projektu: **Mateusz Boćko**.

---

[**Pobierz grę**](https://github.com/MateuszBock0/AuctionHammer/releases/latest) · [**Zgłoś błąd**](https://github.com/MateuszBock0/AuctionHammer/issues)
