# GAME MASTER v23 — aneks do zachowanego v19 / katalogu aukcyjnego v22

**Status:** wdrożenie rozdzielone od historycznych zasad. Nowe gry v22 mają `ruleset_version="v23"`; wcześniejsze zapisy v22, gdy brak pola, zachowują `"v22"`. Historyczne `game_rules_v19.json` i katalog aukcyjny v22 pozostają niezmienione.

## Naprawione niezgodności i reguły v23

1. **Licytacja UI:** jeden suwak od minimum legalnej oferty do posiadanych monet, krok 1, reset do nowego minimum po kolejce rywala; strzałki, Home, End, Enter; tylko `auction_bid` / `auction_pass` mutują stan. Kwota jest płacona dopiero po wygraniu.
2. **Dziesięć opisów** (`S05,S61,S70,S72,S20,S86,S94,S96,S106,S33`): ich dotychczasowy zapis o +3 MAX HP był nieprawidłowy. Rodzina Tarcza/Prowokacja zwiększa na poziom (co 3 własne tury na ręce) **+1 ATK i +2 MAX HP** dodatkowo do wzrostu liniowego; liczbę tarcz i czas prowokacji zostawiono bez zmian.
3. **Dochód za wolne pola:** dla nowych meczów zostaje zatwierdzone `5-len(własna plansza)`, ale jest wypłacany **jeden raz** po wszystkich rozstrzygnięciach końca tury, w tym wspólnych falach śmierci, wyborach, przejęciach i wskrzeszeniach; przed następną aukcją. Pole `pending_vacant_income` jest zapisywane przy otwartym `Pending`. Stare mecze v22 zachowują pierwotny moment wypłaty i starą semantykę zapisów.
4. **A018 legendarna:** przy wystawieniu, jeśli strukturalnie możliwa przyszła legalna aukcja (co najmniej trzy archetypy w woreczku i nieosiągnięty limit), otrzymuje dotychczasową gwarancję wygranej za 0. W przeciwnym wypadku otrzymuje **trwałe +5 ATK, +5 MAX HP i +5 bieżącego HP** zamiast vouchera. Decyzja jest jednokrotna w chwili wystawienia, nigdy retroaktywna.
5. **A014:** zachowuje aktualną konwersję **nominalnej próby leczenia** (nawet przy pełnym PŻ) na obrażenia tego samego celu: podstawowa blokuje, rzadka `ceil(n/2)` obrażeń i `floor(n/2)` leczenia, legendarna `n` obrażeń. Zwykłe Tarcze i pancerz obowiązują.
6. **A015:** w v23 rzadka i legendarna Wieszczka blokują wyłącznie zdolności **przeciwnika** (nie sojusznicze), po sprawdzeniu właściciela każdego źródła; rzadka blokuje Przy śmierci, legendarna Przy wystawieniu/Przy śmierci/Na koniec tury. Podstawowa zachowuje blokadę pierwszej faktycznie ofensywnej wybranej zdolności przy wystawieniu. Równoczesne zgony mają migawkę właścicieli sprzed usunięcia jednostek.
7. **S86/S87/S88 przy śmierci bez innego legalnego sojusznika:** zamiast pustego efektu S86 przyznaje bohaterowi **+3 pancerza**, S87 podejmuje próbę leczenia bohatera o **4 HP**, S88 przyznaje bohaterowi **jedną Tarczę**. Żaden z bonusów nie rośnie z poziomem i nie aktywuje się po wyciszeniu / skutecznej blokadzie.
8. **S32:** gdy istnieją wrogie jednostki, ale wszystkie są już zatrute przez to samo źródło S32, zamiast ponownej trucizny zadaje **2 zwykłe obrażenia** wrogowi o najmniejszym bieżącym PŻ, przy remisie od lewej. Brak wrogów: brak celu.
9. **S95:** gdy nie ma legalnego nowego celu ogłuszenia, ale są wrogowie, zadaje **2 zwykłe obrażenia bez ogłuszenia**, bez aktualizacji pamięci ostatniego celu. Priorytet najniższego ATK, przy remisie lewy.
10. **A010** pozostaje nietknięta: legendarna alternatywa dwóch Żołnierzy 3/3 albo trwałe +3/+3, bez kopiowania najsilniejszej jednostki.
11. **Historia meczów:** paginacja po cztery wpisy, etykieta STRONA X/Y i poprzednia/następna; indeksy i pliki dotychczasowego archiwum są zachowane.

## Zmiany NIEzatwierdzone do produkcji

**AI:** limit licytacji pozostaje na podstawowym `min(monety, 2+2*numer_aukcji)`; warianty oceny kart, rezerwy i zagrożenia wymagają oddzielnego kontrolowanego A/B. Nie zmieniamy statystyk ATK/PŻ, 100 HP, kolejności aukcji ani +3 monet drugiego gracza.

## Muzyka (audyt osobny)

Plik `assets/music/music_auctionhammer.mp3` jest śledzony przez Git i pakowany w ZIP Windows; `FantasyTavernMusic` zapętla cały plik, utrzymuje poziom 30% i gra również w menu. Brak audio jest nieszkodliwy; kontrola zawiera rzeczywisty test dekodera SDL, nie tylko mock.

## Kompatybilność

- Podczas ładowania starego zapisu brakujący `ruleset_version` otrzymuje `v22` w starych grach v22.
- `verify_replay` respektuje wersję podpisanego audytu: nowe v23 odtwarzane są na v23, starsze na v22.
- Historycznych wyników naprawionych dawnych błędów silnika nie można uznać za bitowo odtwarzalne bez odpowiedniej starszej wersji kodu.
- To aneks; nie przepisuje dokumentacji v19 ani oryginalnych variantów aukcyjnych v22.
