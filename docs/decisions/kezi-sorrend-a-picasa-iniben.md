# ADR-014: A kézi sorrend a `.picasa.ini`-be megy, nem a `db3`-ba

Dátum: 2026-09-16 · Státusz: ELFOGADVA · jegy: #1721

## A helyzet

A rács sorrendjét ma kizárólag szabályok adják (`date` · `name` · `size` ·
`color`, `app/photo_sort.py`). A **kézi** átrendezés (fogd-és-vidd) nincs meg,
és nincs hol tárolni sem.

A #1645 kutatási köre kimérte, hogy az eredeti Picasa a kézi sorrendet
(prioritást) a **központi `db3/albums_0.db`** fájlban tartja — a
`.picasa.ini`-ben nyoma sincs.

## A döntés

**A kézi sorrend a mappa saját `.picasa.ini`-jébe kerül**, képszakaszonként egy
`priority=` kulcsba. A `db3`-at **nem írjuk**.

### Miért

1. **A `db3` írása aránytalan kockázat.** Bináris, központi, és a felhasználó
   FUTÓ Picasája is használja (a tulajdonos párhuzamosan teszteli a két
   programot ugyanazon a NAS-mappán). Egy általunk írt `db3` egy hibás bájton
   az ő élő könyvtárát viszi.
2. **Az `ini`-t már bírjuk.** Ütközésbiztos írás, round-trip, mappánkénti
   hatókör — a projekt adatréteg-invariánsa szerint a `.picasa.ini`-t
   kizárólag az `ini/` csomag írja, és az már megvan.
3. **A mappával együtt utazik.** Ha a felhasználó átmásolja a mappát, a kézi
   sorrend vele megy — a `db3`-as tárolás ezt nem tudja.

## ⚠️ Ez SZÁNDÉKOS ELTÉRÉS — és jelölni kell

A tárolás helye eltér az eredetitől, a *funkció* (kézi sorrend) viszont
létezik a Picasában is. Ezért:

* a **rendezési menü** „Prioritás szerint" tétele a
  `sajat-funkciok-jelolese.md` szerinti **kék jelölést** viseli, mert a mi
  megvalósításunk máshol tárol, és ezt a felhasználónak látnia kell;
* a kulcsot a kódban **ki kell mondani** saját kiegészítésként (a
  `vedett-sajat-funkciok.md` jegyzékébe is bekerül).

## ⛔ Amit ez az ADR NEM állít

**Nem tudjuk, hogy az eredeti Picasa megőrzi-e a `priority=` kulcsot**, amikor
ő írja ugyanazt a `.picasa.ini`-t.

* A MI oldalunk megőrzi — mérve: egy `priority=0.5` sort tartalmazó
  szakaszba írt új kulcs után a sor bitre a helyén marad (`ini/io.py`
  round-trip).
* Az eredeti oldala **nincs kimérve**. Az ini-értelmezője a `0x008fb120`
  (3257 b, `_atol`/`_atof`/`_sscanf` sorozat kulcsnév-összevetéssel); hogy az
  ÍRÓ-ág átveszi-e a nem felismert kulcsokat, külön mérés.

⇒ Ha eldobja, a kézi sorrend **nem vész el** (a PicasaPy olvassa vissza), csak
a „hordozhatóság" érve gyengül arra az esetre, amikor közben az eredeti is ír
ugyanabba a mappába. A döntést ez nem fordítja meg: a `db3` írásának kockázata
nagyobb, mint egy esetleg eldobott kulcs.

## A kulcs formátuma

| | |
|---|---|
| kulcs | `priority` a kép szakaszában |
| érték | tizedes szám, **pont** tizedesjellel (a gépi számok írásmódja, `tizedesjel.md`) |
| hiányzó érték | „nincs kézi hely" — a rendezés az ilyen képeket a végére teszi, fájlnév szerint |
| ütközés (azonos érték) | fájlnév dönt, hogy a sorrend determinisztikus legyen |

⚠️ A számozás **nem** egész: beszúráskor két szomszéd közé fél érték kerül, így
egy áthelyezés nem írja át az egész mappát (és nem termel tucatnyi
`.picasa.ini`-írást).

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/photo_sort.py`
- **Őrzi:** `tests/app/test_photo_sort.py`
