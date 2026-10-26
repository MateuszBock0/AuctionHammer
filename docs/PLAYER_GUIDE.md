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

## Jak licytuje komputer? (0.9.91)

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
| `F8` | Szybkość prezentacji ruchów AI |
| `F11` | Tryb pełnoekranowy |

## Koniec meczu, zapisy i statystyki

Po zakończeniu gry zobaczysz zwycięzcę, długość meczu, statystyki działań i najciekawsze osiągnięcia. Szczegóły wymagające pełnej historii są pomijane przy starszych, niekompletnych zapisach, aby nie podawać niepewnych wartości. Możesz otworzyć **Księgę Starć** oraz zapisane audyty.

Na Windows zapisy, diagnostyka i historia pozostają lokalnie w `%LOCALAPPDATA%\AuctionHammer\`. Komputer ma poziomy trudności **łatwy, normalny i trudny**. Nie ma trybu wieloosobowego ani logowania.

**Pomoc:** [Problemy i FAQ](TROUBLESHOOTING.md) · [Bieżące szczegółowe zasady](CURRENT_MVP_RULES_0964.md) · [Historia wydań](../CHANGELOG.md).
