# AuctionHammer 0.9.29 — awaria Królowej i przegląd kandydatów v21/v22

## 1. Przyczyna i naprawa crasha A010

**Błąd z wersji Windows 0.9.28:** po wybraniu `Przywołaj jednostki` przez Królową Tysiąca Twarzy pojawiał się `KeyError: 'SUM0000007'` (zrzut ekranu od gracza).

Mechanizm `A010` w `game/core/auction_abilities.py::_spawn` tworzy legalne, efemeryczne obiekty `Card` z identyfikatorami `SUM0000001`, `SUM0000002` itd. Są to **dodatkowe jednostki**, a nie fizyczne karty S01–S115 z podstawowego katalogu. Silnik potrafił je przywołać i zapisać; widok planszy wywoływał jednak `ability_summary()`, który po rozpoznaniu podstawowych kart wykonywał bezwarunkowo `SPECS[d.id]`. Identyfikatora `SUM...` tam nie ma, co zatrzymywało aplikację po prawidłowym przywołaniu.

Poprawki:
- `game/ui/card_summary.py`: jawna obsługa `SUM...` poza tabelą 70 podstawowych kart.
- `game/ui/card_infographics.py`: osobna ścieżka dla przywołanych jednostek, bez poziomowania na ręce i fałszywych oznaczeń.
- `game/core/auction_abilities.py`: żołnierz 1/1 bez zdolności ma kategorię **Bez zdolności**, a 2/2 z Prowokacją — **Prowokacja**. Poprzednio podstawowy żołnierz miał mylący identyfikator rodziny **Tarcza** mimo braku Tarczy.
- **Nie rozszerzono liczby podstawowych rodzin kart**: zatwierdzone 14 rodzin nadal opisuje 70 podstawowych kart.
- `tests/test_queen_summon_render_0929.py`: regresje wszystkich rzadkości, faktycznego Pygame `CardView.draw`, całego `SoloApp.draw`, panelu szczegółów, zapisu i odczytu oraz efemerycznego usuwania żołnierzy po zgonie.

## 2. Ocena przesłanego pakietu

Otrzymano archiwum `AuctionHammer_BALANS_v21_AUKCJE_17_v22_DRAFT (1).zip` (19.10.2026).

**Kontrola źródłowa:** archiwum ZIP jest prawidłowe, 11 plików wymienionych w manifeście ma zgodne SHA-256. Uruchomiono **16/16 testów katalogu kandydackiego — sukces**. To testy danych, a NIE wykonania nowych umiejętności w silniku.

### Balans kart podstawowych v21 — CANDIDATE

- Nadal **70 kart podstawowych**, po jednym fizycznym egzemplarzu.
- `data/balance_changes_70.json`: **46 kart** ma proponowane nowe przyrosty w ręce lub rozłożenie przyrostów wynikających z jakości.
- `data/cards_base_70_v21_CANDIDATE.json`: proponowany przyszły katalog.
- `data/comparison_70_at_0_3_6_9_12.csv`: porównanie stanu po 0/3/6/9/12 turach w ręce.
- W wersji naprawczej 0.9.29 **pozostaje aktywny dotychczasowy balans v20**. Wdrożenie v21 wymaga oddzielnej regresji 70 kart, statystyk i zgodności z silnikiem.

### Aukcje v22 — 17 DRAFT archetypów

- Aktualnie działają **A001–A012** (12 archetypów × 3 warianty = 36).
- W projekcie zaproponowano **pięć kolejnych**: A013, A014, A015, A016, A018, łącznie **17 archetypów × 3 = 51 wariantów**. Identyfikator **A017 usunięty**, bez zmiany numeracji pozostałych.
- `KATALOG_AUKCYJNY_17_v22_DRAFT.json` i `NOWE_5_A013_A018_BEZ_A017_v22.json` zawierają projekt danych i opisy, ale **nie zawierają gotowej integracji wykonywania nowych mechanik**.
- Szczególnie wymagają implementacji: przekierowanie leczenia A014; filtr wyzwalaczy A015; zagrywanie z cudzej talii A016; jednorazowa przewaga i automatyczne zwycięstwo w aukcji A018.
- Samo podmienienie JSON-a na 17 kart nie uruchomi nowych zdolności i mogłoby uszkodzić aktualne testy, integralność aukcji, zapisy lub interfejs.

### Otwarte decyzje z `ZMIANY_I_INTERPRETACJE_v22.md`

- **A014:** połowa leczenia 5 oznacza 2 PŻ leczenia i 3 obrażeń tego samego celu; konwersja korzysta ze zwykłej kolejności ochrony.
- **A015:** projekt wersji rzadkiej i legendarnej dotyczy globalnie także *własnych* wyzwalaczy, co należy potwierdzić.
- **A016:** rzadka karta poza dobraniem pozwala zagrać kartę spośród 3 własnych + 1 wrogiej; przejście własności i limitu wystawiania jednostek należy dokładnie zdefiniować.
- **A018:** legenda proponuje pierwszy wybór bez płacenia; przy dwóch takich żetonach projekt proponuje wzajemne zniesienie, a przy braku kolejnych aukcji przepadają. Wymaga zatwierdzenia.
- Przed aktywacją kandydatów należy sprawdzić pełne reguły priorytetu kolejki i migrację starych zapisów (12 → 17 archetypów).

## 3. Zakres wydania

0.9.29 to **naprawa krytycznego błędu rysowania** bez zmiany ekonomii, bazowej puli 70 kart, AI, multiplayera czy aktywnego katalogu aukcyjnego. Kandydackie pliki balansu oraz pięć nowych archetypów nie są częścią uruchamianej aplikacji. Ich wprowadzenie to osobny etap po potwierdzeniu interpretacji.

Weryfikacja wydania: pełny `unittest discover -s tests -v`, rzeczywisty render Pygame, testy zapisu/odczytu i Windows portable. Dodatkowe 16 testów pakietu nie są doliczane do regresji uruchamianej produkcyjnej gry.
