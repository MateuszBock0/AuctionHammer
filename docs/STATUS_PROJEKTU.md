# AuctionHammer — status projektu

**Data aktualizacji:** 23 października 2026  
**Wersja gałęzi:** MVP 0.9.64 (naprzemienna kolejność graczy w aplikacji solo; walidacja CI)  
**Tryb:** wyłącznie single-player przeciw AI, offline na Windows. Multiplayer, lobby i serwer nie są elementem MVP.

**Źródła aktualności:** `VERSION.json`, `README.md`, `game/core/`, `data/cards_base_70.json` i katalog aukcji v22. Poprzednie sekcje chronologiczne dokumentują historię zmian, nie zastępują bieżącej konfiguracji.

### Etap — 0.9.64 (pierwszy mecz: gracz drugi; drugi mecz: komputer drugi)

- W **sesji klienta SoloApp** pierwszy mecz ma `first=1` (zaczyna komputer), drugi ma `first=0` (zaczyna gracz), kolejne naprzemiennie. Po ponownym uruchomieniu aplikacji cykl zaczyna się od nowa. Drugie miejsce zawsze otrzymuje prawo wyboru +3 monet lub Chorążego 2/1 z 4 pancerza.
- Pierwsze „NOWY MECZ”, „KONTYNUUJ” i „SAMOUCZEK” z ekranu startowego nie pomijają przygotowanej partii. Potwierdzony restart przełącza kolejność tylko raz; anulowany nie zmienia seeda ani stanu.
- `WCZYTAJ ZAPIS` zachowuje oryginalnego pierwszego gracza i pełny stan meczu; następny nowy mecz będzie miał pierwszy ruch po stronie przeciwnej do załadowanej.
- Nie zmieniono deterministycznego `Match.first`: UI wybiera nowe ziarno RNG dające oczekiwaną stronę, dzięki czemu dotychczasowe audyty, replaye, gry historyczne i symulacje pozostają zgodne z silnikiem.
- **Pełna bieżąca dokumentacja:** `docs/CURRENT_MVP_RULES_0964.md`, `data/MVP_RULES_0964.json` i sekcja README. Wersje Game Master v14/v19 są historyczne i nie zostały zmodyfikowane.

### Etap — 0.9.63 (jedno PŻ i cztery pancerza na start)\n\n- Tylko **nowe** partie z wyborem rekompensaty: startowy `SUM_START_GUARD` ma **2 ATK / 1 MAX i bieżące PŻ / 4 trwałego pancerza**, bez samoczynnego odnawiania pancerza.\n- Zabójstwa nadal dają +1 ATK i +2 MAX/bieżących PŻ, maksymalnie 3 razy; wartości bez aur wynoszą 2/1 → 3/3 → 4/5 → 5/7.\n- Wszystkie krótkie i pełne opisy, okno wyboru, HUD i zapis wersji zostały zsynchronizowane z silnikiem. Osobny znacznik w podpisanym stanie zapewnia zachowanie starych audytów 0.9.62 (2/5) oraz starszych odmian historycznych.\n\n### Etap — 0.9.62 (Chorąży „Zawsze zdąży” — za zabójstwa)

- Nowy starter `SUM_START_GUARD` 2/5: **+1 ATK, +2 MAX i bieżącego PŻ** za bezpośrednie zabójstwo wrogiej jednostki własnym standardowym atakiem, **maksymalnie 3 razy**. Kontratak, efekt pośredni i jednoczesna śmierć nie nagradzają Chorążego.
- Trzy grafiki z 0.9.61 poprawnie przeniesiono na `SUM_START_GUARD`: 0 / 1 / 2–3 zabójstw. S34 odzyskał dokładnie poprzedni plik z commita `ea0f4b86`; karta S34 nie otrzymuje premii za zabójstwa.
- Licznik i przełącznik reguły są częścią podpisanego stanu nowej partii. Zapisane wcześniejsze gry oraz historyczne audyty zachowują stare zasady bez migracji obrażeń.
- UI i powiększenie [G] pokazują ten sam wariant. Podstawowa statystyka startera 2/5; maksimum bez dodatkowych aur 5/11.

### Etap — 0.9.61 (Chorąży — trójstopniowa grafika i ikona)

- Historycznie wydanie 0.9.61 przypisało trzy portrety do S34; przypisanie zostało skorygowane w 0.9.62 na jednostkę startową.
- Seria wizualna nosi roboczą nazwę „Chorąży Zawsze Zdąży”; definicja i nazwa karty `S34` pozostają „Chorąży Królewskiej Kompanii”.
- Kwadratowy portret 128×128 służy jako ikona okna, plik `.ico` jako ikona pliku wykonywalnego PyInstaller. Wszystkie pięć zasobów ma zapisane SHA-256 w `assets/branding/manifest.json`.
- Zmiany wyłącznie w zasobach i UI, nie w `Match`, walkach, ekonomii, zdolnościach, katalogach 70/17 ani audytach.

### Etap — 0.9.60 (UX wybierania zdolności)

- Królowa Tysiąca Twarzy A010: kliknięcie Królowej wybiera `grow`, a kliknięcie wolnego własnego pola wybiera `summon`, tylko gdy istnieją odpowiednie legalne opcje w `pending.choices`; inne wybory i sterowanie klawiaturą pozostają bez zmian.
- Karta ogłuszona pokazuje stan „OGŁUSZONY” zamiast dostępnego, lecz nielegalnego w danej chwili ataku „ATAKI 1/1”, również przy równoległym Szybkim Ataku.
- Zmiany w interfejsie, bez wpływu na `Match.choose`, przywołanie jednostek, balans, audyty, RNG i zapisy. Ręczne sprawdzenie DPI na fizycznym Windows nadal potrzebne.

### Etap — 0.9.59 (hotfix zgodności)

- Przywrócono historyczną postać komunikatów Generała w nowych rozgrywkach, by wcześniejsze podpisane audyty nadal przechodziły `verify_replay`.
- Dla dokładnie rozpoznanych buildów 0.9.58 po PR #82 odtwarzanie zachowuje ich ówczesne, rozszerzone komunikaty; nie zmienia to stanu mechaniki ani SHA archiwum.
- Księga Starć ponownie wyprowadza opisy premii ze stanu podpisanych akcji zamiast ufać starej, zbuforowanej analizie, a karty pokazują mnożnik ×2 na widocznym pasku statusów.
- Zmiana nie modyfikuje statystyk, reguł, RNG, AI, ekonomii ani formatu archiwalnego. Fizyczny odbiór Windows DPI nadal pozostaje do wykonania.

### Nowy etap — 0.9.58\n\n- Tło wokół ilustracji kart aukcyjnych ma dominujący odcień wyliczany z realnego sprite’a PNG, osobno dla 17 kart i 3 rzadkości.\n- Paski przy dopasowaniu proporcji (`contain`) oraz obramowane płytki portretów aukcyjnych korzystają z tego samego koloru; sam sprite, ATK, PŻ i teksty pozostają nienaruszone.\n- Kolory są obliczane i cache’owane tylko przy pierwszym wczytaniu grafiki; nie trzeba obliczać ich co klatkę animacji.\n- Brak zmian zasad, AI, aukcji i grafik kart podstawowych; odbiór ręczny fizycznego Windows DPI nadal pozostaje otwarty.\n\n### Etap — 0.9.57

- 51 grafik PNG 96×96: 17 aktywnych kart aukcyjnych × 3 rzadkości, wszystkie obecne w `assets/auction/` wraz z manifestem SHA-256.
- Wspólna obsługa grafik karty w ręce, na planszy, przy ofertach aukcji, inspekcji zdolności i w powiększeniu; widok zawsze wybiera aktualną rzadkość.
- `tools/install_auction_sprites_0957.py --check-installed` i `tests/test_auction_sprites_0957.py` weryfikują pliki bez wpływu na rozgrywkę.
- Mechanika, AI, ekonomia, statystyki, audyty i replaye bez zmian. Ręczny odbiór Windows DPI pozostaje do wykonania.

### Etap — 0.9.56\n\n- Po ataku można odczytać rzeczywiste zmiany PŻ, tarczy, pancerza i nowych statusów; najechanie na panel zdarzeń pokazuje szczegółowy wynik większą czcionką.\n- Podświetlenie wskazuje odbiorcę aury S34 lub pole reakcji S108, wyliczając je z aktualnych pięciu fizycznych pozycji.\n- Klawisz **F8** przełącza trzy prędkości odtwarzania akcji AI (750/480/280 ms), bez zmiany polityki AI i deterministyczności meczu.
- Panel rundy pokazuje warunkowy licznik do następnej aukcji; podczas własnej tury podaje tylko **szacunek TERAZ** bonusu za wolne miejsca (przed efektami końca tury).\n- Testy regresyjne: `tests/test_gameplay_clarity_0956.py`. Silnik, statystyki kart, balans, audyty i AI pozostają bez zmian.\n- Fizyczny odbiór na Windows i skalowaniu DPI pozostaje **PENDING**.\n\n### Etap — 0.9.55

- Skrócono opóźnienie akcji AI z 850 do 480 ms, bez modyfikowania algorytmu AI.
- Kursor podświetla wyłącznie legalne cele. Panel **SKUTKI ATAKU** podaje rzeczywiste zmiany PŻ, tarczy i potwierdzone zgony.
- Trafienia mają spójną kolejność animacji; obowiązkowe wybory zdolności kończą się przed pokazaniem rezultatu.
- Testy PR: 663/663 PASS, 20 pełnych partii i 5115 komend, 100 odrębnych audytowanych partii/replayów. Testy Windows i UI PASS.
- Odbiór na fizycznym Windows DPI 100/125/150% pozostaje **PENDING**.
- **Bez zmian w silniku, kartach, balansie, audytach i zasadach.** [Kontrola](PLAYER_FEEDBACK_0955.md).

### Etap — 0.9.54

- Legendarnym kartom aukcyjnym dodano ciemnoametystową głębię wokół obrazu, ciepłą złotą poświatę na samej ilustracji, ornamentowane narożniki i zachowany pulsujący klejnot.
- Oferta aukcyjna i pełny podgląd oferty legendarnej otrzymują spójny złoto-ornamentowany motyw oraz oznaczenie rzadkości.
- Przełącznik animacji wyłącza efekty czasowe, nie usuwa identyfikacji rzadkości; teksty, wartości i statusy pozostają na kryjących panelach.
- **Bez zmian w regułach, katalogu kart, balansie, AI, RNG, zapisach i audytach.** Testy: `tests/test_legendary_visual_0954.py`.
- Ręczny odbiór UI na fizycznym Windows DPI 100/125/150 nadal **PENDING**.

### Najnowszy etap — 0.9.53

- Opisy kart i okien aukcyjnych są zawijane według rzeczywistej szerokości fontu; długie ciągi bez spacji nie wychodzą poza ramkę.
- Podgląd oferty pokazuje maksymalnie cztery linie, a pominięcie tekstu sygnalizuje wielokropkiem; pełny opis aukcji można przewijać.
- Nowy test mierzy ramki i szerokości opisów 70 kart podstawowych oraz 51 wariantów aukcyjnych w trzech rozmiarach.
- Uproszczono README pod kątem użytkownika Windows i przygotowano aktualną notatkę kontekstową dla projektu ChatGPT.
- Ręczna weryfikacja na fizycznym Windows (DPI 100/125/150%, audio, mysz, polskie znaki) pozostaje **PENDING**.
- **Bez zmian w silniku, statystykach, aukcjach, algorytmie RNG i istniejących audytach.**

### Obowiązujące zasady aktualnych nowych meczów

- 70 niepowtarzalnych kart podstawowych, bez opłaty za wystawienie; 17 archetypów i 51 wariantów aktywnych kart aukcyjnych.
- 5 stałych fizycznych pól na stronę; śmierć i wygnanie nie przesuwają sąsiadów.
- Drugi gracz wybiera na początku Chorążego 2/5 lub +3 monety.
- Dochód: +1 dla obu po pełnej rundzie oraz bonus za wolne pola w aktywnym wariancie v22.
- Co trzy pełne rundy może odbyć się aukcja; szczegółowy katalog v22 i mechanika v23.
- Historia i stare podpisane audyty zachowują dawne wersje reguł.

## Zaimplementowane

- 70 kart podstawowych, wspólna pula początkowa, talie graczy, rozwój kart na ręce, 5 pól na stronę i walka z bohaterem o 100 PŻ.
- Aukcje co trzy pełne rundy: 17 unikalnych archetypów, 3 poziomy rzadkości (51 wariantów zdolności), zakup prawa pierwszego wyboru.
- Silnik reguł v23: dochód za puste pola po rozstrzygnięciu fal śmierci, efekty awaryjne wybranych kart, reguły A014/A015/A018.
- Przeciwnik komputerowy, zapis/wczytanie rozgrywki, pełna historia i archiwum zakończonych meczów, replaye i kontrola integralności.
- Polska wersja interfejsu, suwak aukcji, wizualizacja walczących kart, animacja utraty PŻ oraz zgonu; filtry trzech cech (Podwójny atak, Prowokacja, Tarcza).
- Opcjonalne odtwarzanie albumu muzycznego podczas gry.

**Ważne rozróżnienie:** `S34` (Chorąży Królewskiej Kompanii) jest kartą **podstawową** z efektem +1 ATK sąsiadowi albo −1 ATK wrogowi naprzeciwko. `A002` (Generał Oddziału Natarcia) jest kartą **aukcyjną**; jej podstawowa rzadkość daje +1 ATK jednostkom na obu planszach. Zakupione karty aukcyjne nie są tasowane do podstawowej puli.

## Stabilizacja 0.9.38

Dodana macierz 121 przypadków aktywacji (70 bazowych + 51 aukcyjnych), silniejsze niezmienniki dla lokalizacji kart i własności, testy atomowego odrzucania niedozwolonych akcji oraz wczytywania zapisu podczas wyborów. To kontrola integracyjna, nie pełny dowód wszystkich kombinacji zdolności. [Raport](ENGINE_STABILIZATION_0938.md).

## Testy i ograniczenia

W wydaniu 0.9.37 przeprowadzono 492 testy oraz dwie serie po 100 meczów (w tym kontrolę 100/100 pełnych replayów). Nie gwarantuje to bezbłędności każdej kombinacji efektów. Brak fizycznej walidacji odtwarzania audio i UI na wszystkich konfiguracjach Windows.

**Poza zakresem MVP:** multiplayer online, lobby i serwer. Ulepszenia AI oraz testy A/B strategii licytacji są możliwymi kolejnymi etapami, bez automatycznej zmiany balansu produkcyjnego.

## Dokumentacja i prawa

- [README](../README.md) — funkcje gry, instalacja, najważniejsze reguły i credits.
- [Game Master](../AUCTIONHAMMER_MASTER.md) i [aneks v23](GAME_MASTER_v23_ADDENDUM.md) — reguły mechaniczne.
- [Audyt v23](QA_V23_SECOND_PASS_20261019.md) — testy i znane ograniczenia.
- [Licencja MIT](../LICENSE) — autorskie oprogramowanie i własna dokumentacja.
- [Pełne przypisanie muzyki](THIRD_PARTY_MUSIC.md) — Alek Kaczan, PGN Music, album, 13 utworów i osobne informacje prawne.

Muzyka i materiały podmiotów trzecich nie stają się objęte MIT przez sam fakt użycia w AuctionHammer. Publiczna dokumentacja podaje credits i źródła, a nie treść odrębnych indywidualnych ustaleń.

## Etap 0.9.39 — nowe mecze

Rekompensata dla gracza wykonującego drugi ruch: na jego planszy pojawia się neutralny **Strażnik 5/5** zamiast 3 monet. Zajmuje pole, nie ma zdolności, nie atakuje w swojej pierwszej turze, po usunięciu znika bez powrotu do talii. Historyczne mecze zachowują +3 monety i oryginalne podpisy audytu. Interfejs zyskuje ochronę przed przypadkowym restartem/wyjściem, globalny resize, dwuwierszowe podpowiedzi i zachowanie stanu animacji podczas restartu. Szczegóły: [UIUX_0939_ACCEPTANCE.md](UIUX_0939_ACCEPTANCE.md).

## 0.9.40 — startowy Chorąży 3/5

W nowych meczach tylko drugi gracz otrzymuje Chorążego 3 ATK / 5 PŻ, opis „Chorąży zawsze zdąży.”. Bez Prowokacji, Tarczy, Szybkiego ataku i bonusu monet. Historyczne +3 monety (`coins`) oraz Strażnik 5/5 (`unit_5_5`) pozostają wczytywane i odtwarzane dokładnie według swoich wersji. Aneks: [CHORAZY_0940.md](CHORAZY_0940.md). Wynik porównania A/B pozostaje do oceny, nie deklarujemy jeszcze wyrównania rozgrywki.

## 0.9.41 — świadomy wybór drugiego gracza

Każdy nowy mecz ma `starting_compensation='choice_2_5_or_coins'`.
Drugi gracz wybiera Chorążego 2 ATK / 5 PŻ **albo** +3 monety.
Wybór jest komendą audytu (`choose_starting_compensation`) i musi zakończyć się przed jego własnym mulliganem. Historyczne `coins`, `unit_5_5`, `unit_3_5` pozostają niezmienione. Schema podpisanego audytu dla wyboru: 4. W grze z komputerem AI używa deterministycznej decyzji na podstawie wyłącznie własnej ręki.

W `game/ui/assets.py` ilustracje dopasowywane są bez deformacji; podgląd I ma tryb powiększenia grafiki [G] i podsumowanie ATK/MAX PŻ. Nie zmieniono ani nie wygenerowano żadnych grafik PNG. Dokładny zakres i kryteria QA: [CHOICE_AND_UI_0941.md](CHOICE_AND_UI_0941.md).

## 0.9.43 — Quality & Release (Windows)

Przenośny launcher Windows nie kopiuje już plików ZIP do działającego katalogu. Zweryfikowane checksumą SHA-256 wydania znajdują się w lokalnym `.auctionhammer-versions/build-xxxxxxxx/`. Aktywną wersję przełącza atomowo wymieniany `ACTIVE_RELEASE.txt`; `PREVIOUS_RELEASE.txt` przechowuje starszą, sprawną wersję do cofnięcia. `URUCHOM_AUCTIONHAMMER.bat` działa online/offline; `GRAJ_BEZ_INTERNETU.bat` nigdy nie wykonuje zapytań GitHub; `COFNIJ_AKTUALIZACJE.bat` zapewnia ręczny rollback. Zmiany nie dotyczą reguł gry, zapisu ani danych w `%LOCALAPPDATA%`.

Zakres testów i ograniczenia: [QUALITY_RELEASE_0943.md](QUALITY_RELEASE_0943.md). Testy na realnym komputerze Windows i różnych DPI/audio pozostają do ręcznego odbioru — testy na runnerze GitHub nie zastępują fizycznego ekranu.
