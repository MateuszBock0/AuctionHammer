# AuctionHammer 0.9.13 — czytelność opisów kart

Zgłoszenie użytkownika: przy rodzinach **Obrażenia** (S09) i **Odporność**
(S64) napisy w obszarze zdolności na małych kartach były niepełne lub trudno
czytelne, szczególnie po skalowaniu obrazu w Windows.

## Zmiany

- Nadal Minimal Fantasy, rozmiary 125×195, 148×220 i 255×380.
- Strefa opisu ma więcej miejsca kosztem niewielkiej części ilustracji.
- Dla rodzin bez osobnej liczby (np. Odporność) usunięto redundantne
  „ODP”, zostawiając więcej miejsca na cel i działanie.
- Skróty S09 i S64 informują wprost o celu i warunku działania;
  nie powtarzają wartości pokazanej wyżej.
- Opisy używają większych fontów (12–13 w małych formatach).
- Przepełnienie kończy się zawsze „…”, zamiast cicho gubić dalsze wiersze.
  Pełny opis dynamiczny jest w panelu bocznym i [I].
- Usunięto ozdobniki rodzin, które na Windows mogły wyglądać jak
  nieobsługiwane znaki, oraz tekst przyrostu nachodzący na opis w dużej karcie.
- Przepisano niejasny skrót ulepszenia Odporności na „1× +1 PANC / 3T”.

## Regresja

`python -m unittest discover -s tests -v`

Testuje się rzeczywiste rozmiary fontów Pygame, poprawność prostokątów tekstu
i ich niekolidowanie z nagłówkiem, liczbą zdolności i paskiem rozwoju dla
wszystkich 70 kart w trzech rozmiarach. Osobne asercje dotyczą pełnych
nieuciętych skrótów S64 i S09 w obu małych formatach.

`python tools/render_minimal_fantasy_preview.py` tworzy dodatkowy PNG
`preview/S64_S09_CZYTELNOSC_0913.png` oraz komplet 70 kart w trzech rozmiarach.

## Ograniczenia

Test pikselowego rozmieszczenia na logicznym płótnie nie zastępuje ręcznej
oceny czytelności po skalowaniu okna Windows przy DPI 100%, 125% i 150%.
Silnik, dane 70 kart, Game Master v19 i aukcje pozostają nietknięte.
