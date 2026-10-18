# AuctionHammer MVP 0.9.10 — kolejka wspólnych fal zgonów

**Specyfikacja:** Game Master v19, rozdział 7 oraz `data/event_order_v19.json`.  
**Status:** implementacja z testami regresyjnymi, bez deklaracji wyczerpującego sprawdzenia wszystkich kombinacji kart.

## Problem usunięty w 0.9.10

W starszej kolejce `_kill_batch()` usuwała jednocześnie zmarłe jednostki, ale `_drain()` dopiero podczas wykonywania poszczególnych efektów „Przy śmierci” szukała legalnych celów. Późniejszy Potwór z tej samej grupy mógł zatem otrzymać inny zestaw możliwości w wyniku działania wcześniejszego Potwora.

**Obecnie** każda grupa zgonów jest rejestrowana jako osobna fala z niezmienną listą zmarłych źródeł i ich legalnych wyborów.

## Jak działa jedna fala

1. **Ustalenie grupy:** silnik wykrywa wszystkie jednostki, które zmarły wskutek wspólnego rozstrzygnięcia. W zwykłej walce dwustronne obrażenia liczone są przed usunięciem któregokolwiek uczestnika; trucizna na początku tury jest rozpatrywana jednym przeglądem.
2. **Kolejność źródeł:** od lewej do prawej dla aktualnego gracza, następnie dla rywala; ostateczny remis rozstrzyga niepowtarzalny identyfikator instancji.
3. **Usunięcie i nagrody:** wszystkie jednostki opuszczają planszę; każda faktyczna śmierć daje przeciwnikowi właściciela dokładnie jedną monetę. Poziom zdolności i informacja o ogłuszeniu/wyciszeniu są utrwalone przed usunięciem.
4. **Wspólna migawka:** wszystkie uprawnione zdolności „Przy śmierci” ustalają dostępne wybory na tym samym stanie gry. Nie są jeszcze wykonywane. **Każda następna grupa pobiera własną migawkę dopiero po zamknięciu poprzedniej**, nawet jeżeli jej zgony zostały wykryte wcześniej przy utracie aury.
5. **Komplet decyzji:** wymagane decyzje gracza lub komputera zbiera się po kolei. Panel wyboru pozostaje obowiązkowy; żadna zdolność z tej grupy nie modyfikuje wcześniej planszy ani ręki.
6. **Zbiorowe konsekwencje:** usuwanie starych, kwalifikujących się efektów następuje względem stanu z początku rozstrzygania; nowe statusy są nakładane osobno. Cała ochrona, pancerz i tarcze grupy poprzedzają obrażenia. Równoczesne nadanie odporności **nie cofa ogłuszenia ani trucizny legalnie zadeklarowanych przy tej samej migawce**. Obrażenia i leczenie są rejestrowane dla całej fali, a następnie stosowane przed przeglądem nowych zgonów.
7. **Kaskada:** jednostki zabite wskutek konsekwencji tworzą **nową falę**. Nie odbierają uprawnień umierającym źródłom z wcześniejszej grupy i nie są dopisywane do jej listy.
8. **Wynik meczu:** śmierć bohaterów jest oceniana dopiero po rozpatrzeniu całej fali, dzięki czemu równoczesne obrażenia i leczenie nie przerywają przedwcześnie pozostałych efektów.

Jeżeli cel z wcześniejszej fali nie istnieje w chwili wykonywania jego zdolności, efekt wygasa bez wybierania zastępczego celu.

## Losowe premie S90 i S91

Przed losowaniem karty na ręce są ujmowane w **posortowanej migawce identyfikatorów**, a wynik pochodzi z powtarzalnego generatora meczu. Dziennik zdarzeń zapisuje identyfikator źródła, kandydatów, wylosowane karty i kolejny numer losowania. Kolejność graficznego ułożenia ręki nie zmienia listy kandydatów dla tego samego stanu.

## Testy

Plik `tests/test_death_waves_0910.py` sprawdza m.in.:

- kilka zgonów po obu stronach i uporządkowanie źródeł;
- utrwalenie dwóch zestawów wyborów przed wykonaniem pierwszej zdolności;
- wyczerpywanie ochrony i pancerza w jednej fali;
- nową truciznę, która nie znika od równoczesnego oczyszczania;
- usuwanie wcześniejszej trucizny, bez naruszenia nowej;
- zgon wywołany zmianą MAX PŻ, uruchamiający osobną falę;
- brak aktywacji zdolności „Przy śmierci” u ogłuszonej jednostki;
- brak przedwczesnego kończenia meczu, gdy w tej samej fali bohater zostaje uleczony;
- równoczesną śmierć obu bohaterów i dotychczasowe zasady rozstrzygnięcia wyniku;
- niepowtarzalność losowania S90 przy różnym ułożeniu ręki.

Dodatkowo nadal uruchamiane są wszystkie wcześniejsze testy 70 kart, efektów, skalowania i interfejsu. Testy pełnej rozgrywki można uruchomić poleceniem:

`python -m unittest discover -s tests -v`

## Granice implementacji

To istotna naprawa kolejkowania i grupowania efektów zgonów, ale **nie dowód stuprocentowej zgodności wszystkich możliwych wielofalowych kombinacji**. W szczególności brak jeszcze szerokiej walidacji statystycznej pełnych meczów przeciwko komputerowi i wszystkich rzadkich kombinacji kilku aur. Mechaniki aukcji nadal nie są częścią tego MVP.
