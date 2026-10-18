# AuctionHammer — gra karciana

**AuctionHammer** to turowa gra karciana fantasy dla jednego gracza przeciwko komputerowi. Obecna wersja korzysta z zatwierdzonych zmian **Game Master v19**. Zawiera 70 unikalnych kart podstawowych, po jednym egzemplarzu każdej. **Aukcje, karty aukcyjne i koszt zagrywania kart nie są jeszcze dostępne.**

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
