# AuctionHammer MVP 0.9.2 — weryfikacja nadawania efektów i czytelności

Źródło reguł: pakiet `GRA_KARCIANA_ONLINE_GAME_MASTER_v17` (GAME_MASTER.md, `event_order_v17.json`, katalog 70 kart). Zakres **wyłącznie podstawowych 70 kart (70×1)**, bez aukcji i kosztów zagrywania.

## Jak wyświetlamy stan

UI `game/core/status_view.py` oblicza statusy **tylko na podstawie aktualnego silnika**: `Unit.effects`, tarczy, pancerza, pasywnych zdolności i dynamicznych aur. Nie odgaduje aktywności po samym opisie karty. Etykiety i obwódki w `game/ui/card_view.py`, lista z nazwami źródeł w `game/ui/app.py` i szczegółowy modal `[I]` korzystają z jednego zestawu statusów.

- Prowokacja: żółto-pomarańczowa (`PROW`); dodatkowo weryfikowana z `legal_attacks`.
- Ogłuszenie: fioletowa (`OGŁ`); trucizna: jasnozielona (`TRUC`); regeneracja: zielona (`REGEN`).
- Tarcza: niebieska (`TARCZ`); pancerz trwały i tymczasowy: stalowy (`P<number>`), z wartościami i źródłami.
- Nadany szybki i podwójny atak: turkusowy (`SZYB`) i pomarańczowy (`2×`).
- Odporność: niebieska (`ODP`); aury/modyfikatory ATK i MAX HP: zielone dodatnie, czerwone ujemne.
- S104: na odbiorcach widoczna aura zwiększonego leczenia.
- S101: nadane Szybki atak widoczne już na ręce; S90: oczekująca następna karta widoczna w interfejsie.

Dokładna wartość, źródło i czas trwania każdego statusu to tekst w oknie szczegółów (`I`), przewijanym kółkiem myszy. Statusy wielokrotne są pokazane osobno w szczegółach, nawet jeśli mają tę samą krótką etykietę na miniaturze.

## Mechaniki zweryfikowane scenariuszami

1. **S61** przyznaje Prowokację wskazanej *innej* jednostce; pozostaje widoczna na odbiorcy i faktycznie ogranicza cele ataków.
2. **S96** przyznaje sojusznikowi tymczasową Prowokację, z informacją o wygaśnięciu.
3. **S102/S78/S101/S90** przyznają odpowiednio podwójny/szybki atak jednostce lub karcie na ręce; status jest widoczny na właściwym obiekcie.
4. **S04/S08/S05/S03/S64/S60** przyznają jednostce zmiany ATK, MAX HP, tarczę, pancerz, odporność, regenerację; źródła są prezentowane poprawnie.
5. **S35/S104/S105** dynamicznie zmieniają statusy na odbiorcach; wyjście źródła aury z planszy usuwa odpowiedni efekt. S34 działa analogicznie na ATK.
6. **S58/S59/S33**: trucizna i ogłuszenie są widoczne; po zakończeniu trucizny znika etykieta. Wrodzona prowokacja nie jest oznaczana jako aktywna, gdy jednostka została ogłuszona.
7. **Zasoby ochronne**: po zużyciu tarczy usuwa się jej widoczna etykieta. Pancerz przyznany przez kilka kart ma odrębne źródła i jest prawidłowo dekrementowany.
8. **S12 vs S26**: Żarłacz Pancerzy poprawnie usuwa najpierw rzeczywisty pancerz tymczasowy z innej karty, przed trwałym. Oczyszczenie usuwające tymczasowy marker usuwa również odpowiadające mu punkty pancerza (naprawione rozminięcie interfejsu i danych).
9. **Rzeczywiste zagranie**: `play('S61') -> pending choices -> choose()` daje Prowokację wybranej jednostce; sprawdzane również dla unikatowej puli 70×1.

## Wyniki

- **38 testów** `python -m unittest discover -s tests -v`: PASS. Dotychczasowe 24 testy + 14 nowych testów widoczności, nadawania i synchronizacji efektów.
- **200 partii AI-vs-AI** `python tools/simulate.py 200`: wszystkie zakończone bez błędów integralności puli kart.
- `python -m compileall game`: PASS. GUI pygame nie dało się uruchomić w środowisku roboczym bez pygame-ce, więc nie twierdzimy, że zrzuty/skalowanie wizualne zostały na Windows zweryfikowane.

## Wcześniejsze zastrzeżenia pozostają aktualne

Pełna zgodność globalnej kolejki *atomowych fal jednoczesnych zgonów* z v17 oraz kombinacji wszystkich 70 wyjątkowych zdolności nie jest jeszcze udowodniona. Testy scenariuszowe wymienione powyżej dotyczą przyznawania i prezentowania statusów, nie są kompletną formalną walidacją wszystkich przypadków bitwy.
