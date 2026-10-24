# Współtworzenie AuctionHammer

Dziękujemy za zainteresowanie! Przed zmianą kodu zapoznaj się ze [stroną projektu](README.md), [historią wydań](CHANGELOG.md) i [zasadami aktualnego MVP](docs/CURRENT_MVP_RULES_0964.md).

## Co można zgłaszać?

- Błędy interfejsu, zasad i zapisów, najlepiej z małym scenariuszem odtworzenia.
- Usprawnienia dostępności, czytelności i instrukcji gracza.
- Testy i poprawki dokumentacji.
- Propozycje rozwiązań mechanicznych — **przed** zmianami zasad przedstaw dyskusję w Issues. Zdolności kart, ekonomia, aukcje, AI i format audytu wymagają ostrożnej weryfikacji.

## Jak przygotować Pull Request?

1. Otwórz Issue lub sprawdź, czy temat nie został już zgłoszony.
2. Utwórz gałąź z aktualnego `main`.
3. Wprowadź minimalną zmianę, zachowując rozdział `game/core/` (silnik) od `game/ui/` (prezentacja).
4. Dodaj testy, a w przypadku UI sprawdź, że samo renderowanie nie modyfikuje `Match`.
5. Uruchom `python -m unittest discover -s tests -v` oraz `python -m tools.release_meta check`.
6. Otwórz PR z krótkim opisem, krokami testowania, konsekwencjami dla zapisów i ewentualnym screenshotem.

Zwykły PR **nie musi zwiększać wersji**. Numer wersji, changelog i Windows Release są przygotowywane przy planowanej publikacji. Nie twórz ręcznie taga `build-*` — powstaje on po poprawnym zbudowaniu przenośnego pakietu na GitHub Actions.

## Licencje

Kod projektu i oryginalne teksty korzystają z [MIT](LICENSE). Nie przesyłaj cudzych grafik, nagrań ani innych materiałów bez zgody i jasnego potwierdzenia warunków dystrybucji. Muzyka wykorzystana w grze ma odrębne zasady — [credits](docs/THIRD_PARTY_MUSIC.md).

[Instalacja i testowanie](docs/DEVELOPMENT.md) · [Proces wydań](docs/RELEASE_PROCESS.md)
