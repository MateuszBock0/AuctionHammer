# Raport QA — AuctionHammer aukcje, DRAFT v4 (18.10.2026)

## Potwierdzenie logiki aukcji

- Oferty w aukcji: **3 różne archetypy**.
- Przydzielone po aukcji: **2 fizyczne karty**, po **1 na każdego gracza**; trzecia nie jest przydzielona ani zagrana.
- Te dwie trafiają na rękę, nie bezpośrednio na planszę; podstawowa akcja wystawienia to maksymalnie jedna karta z ręki na własną turę.
- Przywołania z umiejętności A004/A010 są wyjątkiem od limitu kart **z ręki**, ale nie dają dodatkowych zakupionych kart ani nie mogą przekroczyć 5 pól.
- Pula 12 archetypów wystarcza tylko przy dopuszczeniu ponownych ofert archetypu w następnych aukcjach; w tej samej aukcji nie ma dwóch egzemplarzy tego samego archetypu. Każdy nabytek dostaje unikatowe ID.

## Testowane zakresy

35 automatycznych testów jednostkowych w izolowanym narzędziu referencyjnym, katalog 12×3, walidacja sumy statystyk dla R od 3 do 120, przydział 1/1, zabronienie podwójnego zakupu, legalność stawek, utrzymanie statystyk przy awansie, Bankier, Tkaczka, Królowa, mnożenie ataku Generała i niekumulowanie aur, kopie Regenta oraz reprezentacja snapshotu zgonów.

**Status: PASS 35/35 w izolowanym module — nie jest to test całego AuctionHammer.**

## Losowanie 100 000 zestawów pierwszych 3 aukcji

- Zestaw A002 + A004 + A010 obecny przynajmniej raz w 9 ofertach: **16,459%**.
- Zestaw da się hipotetycznie przydzielić jednemu graczowi jako po jednej karcie na trzy oddzielne aukcje: **8,882%** (optymistyczna górna granica wykonalności bez modelu stawek, decyzji, wcześniejszego końca partii, rozkładu rzadkości i przetrwania jednostek).
- Obliczenia nie są modelem mechaniki walki ani win rate i nie uzasadniają automatycznego osłabienia synergii.

## Zidentyfikowane ryzyka i plan obsługi

| Ryzyko | Waga | Weryfikacja / zabezpieczenie |
|---|---|---|
| Trzy karty wystawione przez samo zakończenie aukcji | Krytyczne | Zabronione: aukcja tylko przydziela 2 karty na 2 ręce; trzecia odpada. Test przydziału. |
| A004 kopia Regenta wywołująca rekursję | Krytyczne | Kopia Regenta nie uruchamia drugiego kopiowania; odrębne UID i efemeryczność. Test. |
| A011 masowa śmierć zmienia kolejność efektów | Krytyczne | Snapshot całej fali + deduplikacja instancji; pełna integracja z silnikiem v19 nadal do wykonania. |
| A010 lawinowe +4/+4 i kopiowanie statystyk | Wysokie | Zgodnie z życzeniem użytkownika nie ograniczamy zdolności; ustawiamy 4/7 zamiast 2/9 w R3 i testujemy przeżywalność. |
| A002 trwałe podwójne obrażenia i dwa ataki | Wysokie | Multiplikator nie kumuluje się; maks. 2 ataki; odporność źródła lekko obniżona: 3/8. |
| A009 zmiana właściciela | Wysokie | Atomowe przeniesienie instancji i stref; odrzuty po wymianie do cmentarza nowego właściciela. |
| A012 manipulacja HP i końcem meczu | Wysokie | Ustalenie kierunku kopiowania, clamp leczenia, progi monet, reakcja Strażnika na śmiertelny drenaż. |
| Ewolucja na planszy oraz „Przy wystawieniu” | Wysokie | Rzadkość zmienia zdolność pasywną, ale sama nie tworzy nowego wejścia na planszę; nie resetuje limitów. |
| Aktywacje monetami | Średnie | Nie dodawać nieustalonych kosztów pasywnym/triggerowym kartom. |
| Dobór statystyk po R3 | Średnie | Zaproponowano jawny profil R+8, +1 ATK/+2 HP co kolejne 3 rundy aukcji, zamrożony po zakupie. |

## Ograniczenia

- NIE zintegrowano aukcji z repozytorium `MateuszBock0/AuctionHammer` ani nie testowano Pygame, AI i licytacji serwerowej.
- NIE wyprowadzono rzeczywistego balansu kart z wyników meczów; korekty HP/ATK są propozycją pod testy A/B.
- Nie każde z 36 efektów jest wykonywane przez narzędzie referencyjne; pełne pokrycie semantyczne to przyszły zakres integracyjny.
- Bazowych 70 kart i ich rozgrywki w Game Master v19 nie zmieniono.
