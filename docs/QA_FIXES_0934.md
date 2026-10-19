# AuctionHammer 0.9.34 — naprawy audytu 100 meczów

## Zakres wydania

Potwierdzone przez historię 100 zakończonych meczów i kontrolę kodu:

| Defekt | Objaw historyczny | Naprawa | Test |
| --- | --- | --- | --- |
| S11 Jadowita Żmija | +1 jakości trucizny przepadał przy efekcie na bohaterze | `hero_effects` otrzymują `bonus_once` **i** `initial_ticks`; pierwszy tyk nalicza premię tylko raz | realny atak oraz dwa tyknięcia na poziomie 0/1/2, porównanie z jednostką |
| A015 Wieszczka | anulowała S04/S08, zanim gracz wybrał buff/debuff | mieszane zdolności czekają na `Match.choose()`, ochrona znika wyłącznie po wybranym ofensywnym efekcie; działa też dla aury `enemy` bez jawnego celu | własne buffy S04/S08, wybrany debuff, jednorazowość ochrony, przerwane `pending` i odtworzenie zapisu |
| S85 Życiodajne Widmo | tekst „ochrona” zamiast leczenia | etykieta „Ulecz własnego bohatera o N PŻ” z uwzględnieniem jakości | śmierć bez innego sojusznika, poziomy 0/1/2 |
| AI aukcyjne | 151 ofert A011 w 100 grach i 0 kupionych | ocena **ATK + PŻ + rzadkość + wycena efektu i jawna sytuacja planszy**, deterministyczna, bez podglądu kart przeciwnika | kontrola priorytetów i 100 rzeczywistych meczów v22 |

Zmieniono tylko model wyboru **kart aukcyjnych** w katalogu v22 na poziomach `normalny`/`trudny`. Limit ofert licytacyjnych nie jest automatycznie podnoszony. v4 i AI łatwe zachowują dotychczasową kolejność wyborów.

## Wczesne wyniki obciążeniowe

W pierwszym pełnym biegu po zmianie oceny kart (identyczne 100 seedów, `normalny` vs `normalny`, aktywne v22) wszystkie 100 meczów zakończyło się poprawnie. Odsetek zwycięstw pierwszego gracza zmalał z **77/100 do 56/100**. Wszystkie 17 archetypów znalazły nabywcę w próbie (A011 aż 79 razy). **To pomiar dla AI i tych seedów, nie gwarancja wyważenia PvP człowiek–człowiek.**

## Mechaniki świadomie nietknięte

- Zatwierdzona v22 **A010**: Żołnierze 1/1, 2/2 z Prowokacją, 3/3; nie przywracano mechaniki kopiowania z historycznej propozycji.
- **A014**: stosuje bieżącą zasadę konwersji leczenia, którą akceptują istniejące testy.
- **A015 rzadka/legendarna**: globalne ograniczenia dotykają obu stron zgodnie z aktualną v22, bez samowolnego przewartościowania.
- **A018** na ostatniej aukcji oraz **S86/S87/S88** bez pozostałych sojuszników: brak użytecznego celu to znany przypadek projektowy, a nie awaria wykonania. Nie dodano wymyślonych bonusów bojowych bez odrębnej decyzji o balansie.
- **Ekonomia:** +3 monety dla drugiego gracza na start i +1 dla obu po pełnej rundzie pozostają. W nowych meczach v22 dodatkowy dochód wynosi `5 - liczba własnych jednostek` na koniec WŁASNEJ tury, po rozpatrzeniu efektów końca tury; gracz i komputer są symetryczni. Pełna plansza 5 kart: +0, jedna karta: +4, pusta: +5. Stare zapisy są kontynuowane na poprzednich zasadach. Nowe A/B na poprawionym AI dało **58,0% -> 49,0%** (normalny) i **58,5% -> 55,5%** (trudny) wygranych pierwszego gracza na 200 dopasowanych seedach każdego poziomu. 800/800 meczów ukończonych bez błędów. Nadal możliwa inflacja portfeli — nie oznacza to, że balans jest finalny.

## Integracja, kompatybilność, audyty

Format `savegame_v19.json` pozostaje aktualny; nowe pole `vacant_income_enabled` jest zachowywane w zapisie. Starszym zapisom pole to domyślnie przypisuje się `False`, aby nie zmieniać reguł w połowie meczu. Nie zmieniono schematu podstawowych kart ani 51 efektów v22. Stare audyty pozostają czytelne i weryfikowalne kryptograficznie, ale **pełny replay audytu stworzonego na starszym, wadliwym silniku może nie odtworzyć błędnej historycznej zdolności** po aktualizacji kodu; te audyty należy odtwarzać z wersją źródłową, której dotyczą. Nowe audyty oznaczane są wersją `0.9.34`.

Automatyczne testy obejmują pełną macierz jednostkową, 100 audytowanych meczów v22, replays i oddzielne porównanie alternatywnej ekonomii na dopasowanych seedach.
