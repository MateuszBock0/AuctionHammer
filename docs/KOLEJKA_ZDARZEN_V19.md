# Wspólne fale zgonów — implementacja MVP 0.9.10

**Obowiązująca podstawa:** dostarczony pakiet **Game Master v19**, sekcja 7 oraz `data/event_order_v19.json`. Interfejs gry i opis zdolności pozostają w języku polskim. Zmiana nie modyfikuje statystyk 70 kart ani zasad aukcji.

## Dlaczego zmieniono silnik

Dawniej metoda `_kill_batch()` usuwała naraz jednostki, ale dopisywała zdolności „Przy śmierci” do zwykłej kolejki. `_drain()` wykonywał pierwszą zdolność od razu; mógł przez to zabić, ogłuszyć, zmodyfikować lub usunąć cel drugiej zdolności **przed ustaleniem jej wyboru**. Było to sprzeczne z nadrzędną zasadą wspólnej migawki.

## Zasady po zmianie

1. **Wykrycie grupy:** po wspólnej fazie obrażeń i przeglądzie HP silnik rejestruje fizyczne identyfikatory wszystkich umierających jednostek. Wspólny zgon w starciu oraz zgon wywołany utratą aury mogą prowadzić do oddzielnych kolejnych fal.
2. **Uprawnienia z chwili śmierci:** ogłuszone i wyciszone jednostki nie dodają własnej zdolności „Przy śmierci”. Zgon i wypłata monet następują tylko raz.
3. **Stały porządek:** źródła rozpatrywane są od lewej do prawej u aktywnego gracza, następnie od lewej do prawej u przeciwnika, a przy remisie według identyfikatora egzemplarza.
   Jeśli w wyniku usunięcia aury następna grupa zgonów zostanie wykryta już wcześniej, jej **lista legalnych celów jest ustalana dopiero po zamknięciu poprzedniej grupy**, a nie podczas wcześniejszego wykrycia.
4. **Jedna migawka legalnych celów:** dla *wszystkich* aktywnych źródeł tworzone są listy wyborów przed zastosowaniem dowolnego efektu tej grupy. Gracz lub komputer podejmują wszystkie konieczne decyzje, gdy żaden rezultat tej grupy nie zmienił jeszcze planszy.
5. **Przygotowanie wyników:** dla każdej zdolności przygotowywana jest lista operacji. Są to m.in. obrażenia bohatera, leczenie, trucizna, ogłuszenie, modyfikacja ATK/MAX PŻ, pancerz, tarcza, regeneracja, oczyszczanie, odporność oraz nadanie cech wskazanym egzemplarzom kart na ręce. Dobór losowy korzysta z deterministycznego ziarna meczu i listy posortowanej po identyfikatorach egzemplarzy.
6. **Wspólna fala skutków:** nie usuwa się kolejnych jednostek między efektami jednego zestawu. Oczyszczanie dotyczy stanów obecnych przed rozpoczęciem wspólnej grupy, natomiast nowe statusy tej samej grupy są dodawane po fazie oczyszczania. Przyznanie odporności z tej samej grupy nie cofa wcześniej przygotowanej deklaracji ogłuszenia. Tarcze i pancerz są zużywane w stałej kolejności.
7. **Koniec fali:** silnik przelicza aury i pozycje, wykrywa nowe jednostki z HP nie większym od zera i umieszcza je w **następnej grupie**. Po zamknięciu grupy sprawdza śmierć bohaterów. Jeśli mecz się skończył, następne grupy nie są już uruchamiane.
8. **Kaskada:** kroki są powtarzane aż do opróżnienia kolejki. Nie można zadeklarować kolejnej akcji gracza w środku rozstrzygania.

## Przypadki przeanalizowane w testach

| Sytuacja | Oczekiwany wynik |
| --- | --- |
| Jednoczesna śmierć dwóch Potworów | Obie zdolności otrzymują legalne cele ze wspólnej migawki |
| Zdolność pierwszego Potwora uśmierca cel drugiego | Drugi efekt został już zadeklarowany; nie znika przez wcześniejszą śmierć celu |
| Ogłuszenie i śmiertelne obrażenia od S84 | Zdolność śmierci ofiary jest zablokowana, ponieważ przy śmierci jest ogłuszona |
| Obniżenie maksymalnych PŻ powoduje śmierć kolejnego Potwora | Jego zdolność trafia do następnej grupy i rozpatruje się po zamknięciu poprzedniej |
| Zgon źródła aury powoduje śmierć zależnej jednostki | Powstaje osobna grupa śmierci z nowymi skutkami |
| Oczyszczanie i nowy status z jednej grupy | Nowy status nie jest usuwany jakby istniał przed migawką |
| Nadanie odporności i ogłuszenia w jednej grupie | Obie deklaracje były legalne przy wspólnej migawce |
| Dwie strony tracą jednostki w jednym standardowym starciu | Jeden wykryty zestaw zgonów, a następnie konsekwencje |
| S90/S91 uruchomione z tej samej grupy | Premie odnoszą się do fizycznych, niepowtarzalnych egzemplarzy kart |
| Bohater osiąga 0 PŻ po wspólnej fali | Sprawdzenie zwycięstwa przed uruchomieniem następnej grupy |
| Próg monet 75/50/25 przy obrażeniach i leczeniu | Nagroda za pierwsze przekroczenie przyznana najwyżej raz |
| Wielokrotnie wykryty identyfikator umierającej jednostki | Zgon i nagroda za zabicie są liczone tylko raz |

## Struktura kodu

- `Match.death_waves` — kolejka zamrożonych grup zgonów.
- `Match._kill_batch()` — zebranie zgonów, ich porządek i wyznaczenie wspólnej listy możliwych wyborów.
- `Match.choose()` i `Match._drain()` — gromadzenie decyzji dotyczących całej grupy przed wykonaniem jej zdolności.
- `Match._compile_death_intents()` — przygotowanie rezultatów z grupowej migawki.
- `Match._resolve_death_wave()` — wspólna faza skutków i przekazanie dalszych zgonów do następnej grupy.
- `Match.death_wave_log` — uporządkowany ślad wykrycia, rozstrzygania i zamknięcia grup.
- `tests/test_atomic_death_waves_v19.py` — regresje złożonych interakcji.

## Granice zakończonego zadania

MVP 0.9.10 **wdraża i testuje grupowe rozpatrywanie zgonów oraz wynikające stąd kaskady**. Nie jest to deklaracja ukończenia pełnej autorytatywnej gry wieloosobowej, wszystkich pozostałych priorytetów reakcji, kompletnego systemu odtwarzania meczów czy statystycznego balansu. W szczególności testy obejmują konkretne złożone scenariusze, ale nie wyczerpują matematycznie wszystkich możliwych kombinacji 70 zdolności.

Do końcowej kontroli: `python -m unittest discover -s tests -v`.
