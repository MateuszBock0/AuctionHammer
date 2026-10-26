# Jak grać w AuctionHammer?

**AuctionHammer** to jednoosobowa, turowa gra karciana fantasy przeciwko komputerowi. Na każdej planszy jest pięć pól na jednostki. Celem jest sprowadzenie PŻ bohatera przeciwnika do **0**, zanim Twój bohater zostanie pokonany.

> Chcesz najpierw zobaczyć grę? [Pobierz wersję Windows](https://github.com/MateuszBock0/AuctionHammer/releases/latest) i uruchom **SAMOUCZEK** z głównego menu.

## Pierwsza partia

1. **Kto zaczyna?** W pierwszej nowej partii po uruchomieniu aplikacji zaczyna komputer; w drugiej Ty. Kolejne mecze zmieniają tę kolejność naprzemiennie.
2. **Rekompensata drugiego gracza.** Drugi uczestnik wybiera bonus: **+3 monety** lub specjalnego Chorążego (2 ATK, 1 PŻ, 4 trwałego pancerza).
3. **Wymiana początkowa.** Możesz wymienić do trzech kart z ręki, w tym zero kart.
4. **Twoja tura.** Zasadniczo możesz wystawić jedną kartę. Po wskazaniu karty zobaczysz dozwolone własne pola lub legalną zamianę na pełnej planszy.
5. **Ataki.** Kliknij swoją jednostkę, a następnie dozwolony cel, albo przytrzymaj i przeciągnij jednostkę na cel, po czym puść przycisk myszy. Podświetlone ramki i ostre narożniki wskazują legalne cele bez zasłaniania ilustracji. Podczas wyboru celu duży automatyczny podgląd innej karty nie blokuje planszy. Podczas przeciągania widoczna jest bardzo delikatna, półprzezroczysta czerwona strzałka — nie zasłania już kart tak jak dawna gruba linia. Prowokacja, ogłuszenie, osłony i inne efekty mogą ograniczać ataki.
6. **Koniec tury.** Kliknij **ZAKOŃCZ TURĘ** lub naciśnij **SPACJĘ**. Jeśli pozostały legalne zagrania lub ataki, musisz potwierdzić chęć ich pominięcia.

## Karty i pięć frakcji

W talii podstawowej jest **70 niepowtarzalnych kart**. Ich frakcje sugerują moment działania zdolności:

| Frakcja | Najczęstszy moment aktywacji |
|---|---|
| Elfy | Wystawienie jednostki |
| Dzikie bestie | Atak jednostki |
| Potwory | Śmierć jednostki |
| Krasnoludy | Koniec tury |
| Ludzie | Pasywny efekt na planszy |

Karty podstawowe mogą zyskiwać statystyki podczas tur spędzonych **na ręce** i rozwijać zdolność co trzy takie tury. Pasek rozwoju pokazuje postęp, a krótka animacja — rzeczywiste osiągnięcie nowego poziomu.

Przy kartach z aurami (np. Chorąży `S34`, Komendant `S35` i Zbrojmistrz `S105`) wskazanie ich lub wspieranej jednostki pokazuje faktyczne powiązania i aktualne modyfikatory. Premie z kilku źródeł mogą się sumować; widoczna etykieta przy połączeniu jest wkładem **jednego źródła**.

## Jak działa plansza?

Obie strony mają po **pięć fizycznych miejsc**. Po śmierci jednostki inne karty nie przesuwają się automatycznie. Położenie ma znaczenie dla części efektów, zwłaszcza aur sąsiednich i reakcji na przeciwnika stojącego naprzeciwko.

ATK to siła ataku, PŻ to bieżące zdrowie, a MAX PŻ określa maksymalne zdrowie. Tarcza, pancerz oraz statusy działają według zasad konkretnej karty. Zielone i czerwone zmiany statystyk oraz liczby obrażeń odzwierciedlają aktualny stan, nie obiecują przyszłego rezultatu.

## Po co są monety?

**Zwykłe karty nie kosztują monet.** Monety przydają się przede wszystkim podczas aukcji. Co trzy ukończone rundy może odbyć się aukcja trzech ofert, o ile pula aukcyjna na to pozwala. Licytujesz pierwszeństwo wyboru, a nie komplet trzech kart. Dostępne jest **17 archetypów** aukcyjnych, w trzech rzadkościach (podstawowa, rzadka, legendarna) — łącznie **51 wariantów zdolności**.

Rzadkość kupionej karty może awansować w miarę upływu kolejnych pełnych rund. O wyborach i potencjalnych skutkach czytaj bezpośrednio na ekranie aukcji; dłuższe opisy znajdziesz przez **PEŁNA ZDOLNOŚĆ**.

## Czytelne aktywacje zdolności (0.9.92)

Gdy zadziała potwierdzony efekt, gra krótko podświetla jego źródło i rzeczywistych odbiorców. W wolnym pasku między własnym bohaterem a ręką pokazuje **ŹRÓDŁO → CEL → SKUTEK** (np. `Kapłan → 5 celów · REGEN 2/2`). Regeneracja, wzrost ATK, wzmocnienia MAX PŻ, statusy i potwierdzone zmiany zdrowia nie są prognozą — pochodzą z zatwierdzonych działań. Gdy gra nie potrafi jednoznacznie przypisać skutku do konkretnej zdolności, nie rysuje mylącego powiązania. Przy wzmocnieniu wszystkich sojuszników pokazuje jedną zbiorczą etykietę. Naciskając **A**, wyłączasz te animacje razem z innymi efektami wizualnymi; nie zmienia to wyniku partii.

## Głośność muzyki i efektów

W menu **USTAWIENIA** są dwa niezależne przyciski: **MUZYKA** (domyślnie **40%**) oraz **EFEKTY** (domyślnie **10%**). Każde kliknięcie podnosi poziom o 10 punktów procentowych; po 100% następuje 0%, czyli wyciszenie. Wartości są zapamiętywane lokalnie, także po zamknięciu gry. Dźwięki nie wpływają na wynik meczu.

## Karczemna Burda — wizualizacje i zakupy komputera (od 0.9.96)

Po zamówieniu piwa, jeśli animacje są włączone, przez 600 ms nalewa się piwo. Od 0.9.99 świeczki stoją na ramie planszy, ale nie ma już wiszącego kufla po lewej. Opłacony kufel pojawia się na prawo od dolnego rzędu kart, przechyla się i wylewa piwo na dolne obrzeże planszy. Po około 1,45 sekundy znika. Ogień dociera do wszystkich 10 pól jednostek (pustych i zajętych) jako dyskretne, migoczące płomyki. Gasną one dokładnie, gdy licznik Burdy wynosi zero. Kolejny zakup przedłuża Burdę o 3 tury. **[A]** wyłącza animacje. Karty i pola kliknięcia nie obracają się ani nie przesuwają, więc nadal można grać w swoim tempie.

Komputer na poziomie **TRUDNYM** potrafi zamówić piwo, gdy przewidywane szkody po stronie gracza są wyraźnie większe niż szkody w jego własnych jednostkach. Wydaje jedynie dostępne monety, zostawia rezerwę na aukcję i nie stosuje ukrytych informacji. Na poziomie łatwym i normalnym nie dokonuje automatycznych zakupów. Od 0.9.97 normalne AI jest za to bardziej zdecydowane podczas licytowania kart aukcyjnych.

## Karczemna Burda — zamawianie piwa (od 0.9.95)
Po obu stronach ramy planszy stoją świece. Kufel pojawia się tylko podczas animacji zakupu, po prawej krawędzi planszy. W swojej turze możesz kliknąć **KUP [B]** lub nacisnąć **B**.
- W nowych partiach od **0.9.97** pierwszy kufel kosztuje każdego gracza **10 monet**, drugi jego własny kufel **20**, trzeci **30** itd. Do tego dolicz **1 monetę za każde 2 rozpoczęte tury obu graczy łącznie**: `10 + 10 × (wcześniejsze własne kufle) + floor(rozpoczęte tury obu graczy/2)`. Przykład: po 12 turach pierwszy kufel kosztuje 16, a drugi 26 monet, niezależnie od posiadanego salda.
- Stare mecze rozpoczęte w 0.9.95–0.9.96 zachowują poprzedni cennik `max(10 + rozpoczęte tury, ceil(monety/10))`.
- Każdy kufel dodaje **3 tury** do licznika Burdy. Na końcu każdej tury **wszystkie jednostki obu plansz** otrzymują po **1 normalnym obrażeniu**; osłony i pancerze absorbują je według standardowych zasad. Efekty po śmierci działają normalnie. Bohaterowie i karty na ręce nie są ranne.
- Kolejne piwo wydłuża efekt o 3 tury; nie zwiększa liczby obrażeń. Nie ma dopłaty za kolejny kufel.
- Historyczne zapisy i podpisane powtórki zachowują swoje oryginalne reguły. W 0.9.98 zastąpiono starsze proste dekoracje dwoma bogato cieniowanymi świecami i przechylanymi kuflami zamocowanymi na ramie planszy. Nalewanie trwa 600 ms, następnie piwo spływa na planszę i zapala się wzdłuż krawędzi. Świece migają w czterech klatkach (co 130 ms), a naciśnięcie A zatrzymuje animacje. To efekt wizualny, bez dodatkowego natychmiastowego obrażenia. Trudne AI może kupować piwo od 0.9.96.

## Jak działa Generał A002? (od 0.9.93)

**Generał Oddziału Natarcia zawsze premiuje wyłącznie własną planszę:**
- Podstawowy: +1 ATK wszystkim własnym jednostkom na planszy, w tym Generałowi, dopóki pozostaje aktywny.
- Rzadki: tylko jedna wybrana własna jednostka otrzymuje możliwość do dwóch ataków i podwójne obrażenia swoich standardowych ataków.
- Legendarny: tylko NOWO zagrani/przywołani sojusznicy po jego awansie lub wystawieniu otrzymują podwójny atak i podwójne obrażenia standardowe. Nie obejmuje wrogów ani starszych sojuszników.
- Każdy wariant v24 przy wejściu dostaje Tarczę; rzadki +2, legendarny +4 trwałego pancerza.

Starsze podpisane partie, których reguły miały premię podstawowego Generała na obu planszach, są nadal odtwarzane według **oryginalnej** wersji. W nowych partiach taka premia nie wzmacnia przeciwnika.

## Jak licytuje komputer? (0.9.91)

Na poziomie **trudnym**, od 0.9.94, dodatkowa szybka analiza kilku ataków potrafi wykorzystać kombinację zdjęcia Tarczy i zadania końcowego ciosu, bez długiego namysłu lub podglądania ręki gracza. 

Na poziomie **trudnym**, od 0.9.93, komputer dodatkowo ocenia wszystkie legalne pary atakujący–cel, planuje potencjalne zakończenie meczu, porównuje odwet i ryzyko uruchomienia zdolności śmierci.

Na poziomie **łatwym** komputer wydaje na jedną aukcję najwyżej połowę monet, które ma w chwili licytacji (zaokrąglenie w dół). Na **normalnym** wycenia korzyść z pierwszego wyboru, pamiętając, że przy przegranej aukcji nadal dostanie drugą kartę za darmo. Na **trudnym** uwzględnia dodatkowo publiczny stan planszy przeciwnika, wartość zachowania monet i to, jakie archetypy pozostają w puli. AI nie podgląda ręki ani talii gracza. Żaden poziom nie gwarantuje zwycięstwa lub porażki w każdej partii.

## Najważniejsze skróty

| Klawisz | Znaczenie |
|---|---|
| `SPACJA` | Koniec tury lub potwierdzenie ostrzeżenia |
| `I` | Szczegóły wybranej karty |
| `F1` | Wbudowana instrukcja |
| `T` | Wskazówki i samouczek |
| `H` | Historia zdarzeń |
| `P` | Powtórka |
| `M` | Menu |
| `R` | Nowy mecz |
| `A` | Animacje |
| `B` | Zamów piwo za wyświetloną cenę podczas swojej tury |
| `F8` | Szybkość prezentacji ruchów AI |
| `F11` | Tryb pełnoekranowy |

## Koniec meczu, zapisy i statystyki

Po zakończeniu gry zobaczysz zwycięzcę, długość meczu, statystyki działań i najciekawsze osiągnięcia. Szczegóły wymagające pełnej historii są pomijane przy starszych, niekompletnych zapisach, aby nie podawać niepewnych wartości. Możesz otworzyć **Księgę Starć** oraz zapisane audyty.

Na Windows zapisy, diagnostyka i historia pozostają lokalnie w `%LOCALAPPDATA%\AuctionHammer\`. Komputer ma poziomy trudności **łatwy, normalny i trudny**. Nie ma trybu wieloosobowego ani logowania.

**Pomoc:** [Problemy i FAQ](TROUBLESHOOTING.md) · [Bieżące szczegółowe zasady](CURRENT_MVP_RULES_0964.md) · [Historia wydań](../CHANGELOG.md).
