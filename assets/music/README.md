# PGN Music: Fantasy Tavern Album (opcjonalne audio)

AuctionHammer jest całkowicie darmowym MVP, a kod źródłowy ma licencję MIT.
Oryginalne nagrania PGN Music nie są objęte tą licencją i nie są dodawane
do repozytorium.

W celu odtwarzania całego albumu w pętli umieść tutaj **jeden plik
`music_auctionhammer.mp3`**. Gra odtworzy go od początku do końca,
po czym automatycznie zacznie ponownie. Nie ma potrzeby rozdzielania
go na 13 utworów.

Działa to zarówno w projekcie źródłowym Pythona, jak i w wydaniu
Windows: umieść plik w folderze `AuctionHammer/assets/music/` leżącym
**obok pliku `AuctionHammer.exe`**, a nie w `_internal`.

Dla zgodności wstecznej obsługiwane są też pliki
`fantasy_tavern_full.ogg`, `fantasy_tavern_full.mp3` i
`fantasy_tavern_full.wav`.

Alternatywnie użyj 13 plików .mp3, .ogg lub .wav, ponumerowanych od
01 do 13 w kolejności albumu, np. `01 - Embers in the Wind.mp3`
oraz `13 - Enter the Traveling Beauty.mp3`. Gra odtworzy całą
trzynastkę w kolejności, po czym rozpocznie od 01.

Brak plików muzycznych nigdy nie blokuje uruchomienia gry.
Oficjalna strona: https://pgnmusic.bandcamp.com/album/fantasy-tavern-album

Przed dodaniem plików audio do publicznego GitHuba sprawdź zasady
redystrybucji u właściciela nagrań.
Zobacz: ../../docs/THIRD_PARTY_MUSIC.md
