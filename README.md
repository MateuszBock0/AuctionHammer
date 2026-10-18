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
| `data/cards_base_70.json` | **Jedyne bieżące źródło definicji 70 kart**, wczytywane przez silnik |
| `docs/V19_INTEGRATION_AND_UI.md` | Zmiany zasad v19 i ich implementacja |
| `docs/GAME_MASTER_v17.md` | **Archiwum** wcześniejszej specyfikacji v17 — nie jest katalogiem aktualnych kart |
| `data/event_order_v17.json` | Historyczny dokument kolejności zdarzeń nadal przywoływany w zasadach; atomowe fale zgonów wymagają dalszej weryfikacji |
| `game/core/` | Silnik meczu |
| `game/ui/` | Interfejs gry |
| `tests/` | Automatyczne testy |

Zmiany S66, S67, S79, S114 i S115 z v19 są zaimplementowane, podobnie jak zatwierdzone zmiany S20, S82, S90, S91, S105 i S109. Mechanizm grup **jednoczesnych zgonów** wymaga nadal dalszych testów zgodności z zasadą wspólnej fali. Nie przedstawiamy bieżącego prototypu jako ostatecznie zbalansowanej ani w pełni zweryfikowanej wersji gry.

## Rozwój i aktualizacje

Po zatwierdzeniu zmian w gałęzi `main` GitHub automatycznie uruchamia testy i przygotowuje przenośne wydanie dla Windows. Kod można edytować lokalnie po zainstalowaniu Pythona i zależności z `requirements.txt`. **Do zwykłego grania te narzędzia nie są potrzebne.**
