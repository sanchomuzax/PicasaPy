# Hogyan mérünk — a lapok kötelező fejléce

Ez a lap nem mérés, hanem a **mérés-lapok szerződése**. Azért van, mert egy
szám önmagában nem lelet: ha nem tudjuk, milyen gépen és milyen állapotban
készült, később nem dönthető el, mit jelent.

## A kiváltó eset (2026-09-12, #3080)

A `#1612` alapvonala a QML-betöltésre **1914 ms** (2026-08-27). Egy későbbi
kör ugyanazt **3649 ms**-nak mérte — két futásban konzisztensen (3649,0 és
3644,5), tehát a mérő nem ingadozott. A gépen viszont
`load average: 5,20 / 6,50 / 6,35` volt **négy magon**, mert párhuzamos
munkamenetek tesztjei futottak.

A két szám nem vethető össze. És mivel az **alapvonal terhelése nincs
feljegyezve**, az sem tudható, hogy az 1914 ms tétlen gépen készült-e. A
„romlott-e a betöltés?" kérdés így **nem dönthető el** — nem azért, mert
kevés a mérés, hanem mert hiányzik egy mező.

## Amit minden mérés-lap fejlécének tartalmaznia kell

| mező | miért |
|---|---|
| **dátum** (év-hó-nap, óra:perc) | melyik kódállapotra vonatkozik |
| **commit** (rövid SHA) | a kódállapot pontosan |
| **gép** (modell/CPU, magszám, RAM) | a magszám nélkül a terhelés értelmezhetetlen |
| **terhelés** a mérés előtt ÉS után (1/5/15 perc) | ez dönti el, összevethető-e |
| **mit futtatott még a gép** | ha tudható (párhuzamos tesztek, más munkamenet) |
| **a futások SZÁMA és mindegyik értéke** | egy szám nem mérés; az ingadozás is adat |

Ha egy mező nem megszerezhető, **a lap mondja ki, hogy hiányzik** — a
kihagyás rosszabb, mint a bevallott hiány, mert később mérésnek látszik.

## Amit a mérő magától ad

A `scripts/indulas_meres.py` a `#1653-JSON` rekordba beírja a `magok`,
`terheles_elott` és `terheles_utan` mezőket, és az olvasható jelentés alá is
kiír egy terhelés-sort. Windowson a `getloadavg` nem létezik: ott a mező
`null`, és a sor ezt kimondja — kitalált számot nem teszünk a helyére.

## Amit ez NEM mond meg

Azt nem, hogy mekkora terhelés mellett használható még egy mérés. Erre nincs
mérésünk; a lapok addig a **tétlen gépet** tekintik az alapvonalnak, és a
terhelt futást csak akkor közlik, ha a terhelést is közlik vele.
