# Lencse-jegyzék — egy nézőpont, egy menet

**Mi ez.** Átnézési körben nem „nézd meg mindenből" prompt fut, hanem
**lencsénként külön menet**. Az *Iteration Without Drift* hivatkozott mérése
(IFScale, Jaroslawicz et al., 2025) szerint a legjobb modellek is ~68%-ra
esnek 500 egyidejű utasításnál — a „nézd meg 10 szempontból" prompt
szempontonként romlik. Egy lencse = egy nézőpont, sorosan.

**Nem „még egy ágens".** A lencse itt **nézőpont egy körben**: ugyanaz a
munkamenet veszi elő egymás után. Ez a költség-szabályból következik
(`memory/munkafolyamat.md:137–145`: a párhuzamos worktree+agent overhead
kicsi, egymást érintő feladatoknál drágább a sorosnál).

**Belépő feltétel: magvetett hibán bizonyítottan tüzelnie kell.** Ugyanaz a
ceremónia, mint az őr-teszteknél (`PROTOKOLL.md`: *„Az őrnek legyen foga"*).
Validálatlan lencse magabiztos csendet gyárt.

---

## A három élő lencse

### 1. Kirajzolt felület (#651)

| | |
|---|---|
| **kiváltó** | `*.qml` vagy felületi vezérlő változott |
| **a kérdés** | *Mit LÁT ebből a felhasználó, és melyik teszt nézi a KIRAJZOLT állapotot — nem a property-t?* |
| **mit kell megtalálnia** | a property helyes, a felület mégis néma vagy láthatatlan |
| **gépi fedezet ma** | **nincs** — csak fegyelmi szabály (`PROTOKOLL.md:97`) |

**Magvető minta:** egy `ToolButton`, amin az `enabled` property helyes marad,
de bekerül egy `visible: false`. A meglévő property-szintű teszt
(`assert gomb.property("enabled") is True`) **zöld marad**.

**Validálás (2026-08-27): TÜZEL.** A magvetett fájlban a kirajzolt állapotot
néző állítás száma **0**, a property-állításé 1 — a lencse kérdése pontosan
erre a különbségre kérdez rá.

### 2. Jelöletlen SAJÁT FUNKCIÓ (#1187)

| | |
|---|---|
| **kiváltó** | olyan viselkedés változik, ami eltér az eredeti Picasától |
| **a kérdés** | *Ez az eltérés szándékos? Ha igen, hol a `SAJÁT FUNKCIÓ` jelölés és a jegyzék-sora? Ha nincs jelölés, akkor vagy hiba, vagy jelöletlen saját funkció — a kettő közül melyik?* |
| **mit kell megtalálnia** | szándékos bővítést, amit egy kutatói kör „eltérésként kijavítana" |
| **gépi fedezet ma** | `scripts/check_protected_features.py` — de **csak a már megjelölt** elemeket veti össze; a hiányzó jelölést nem látja |

**Magvető minta:** a keresés hatóköre kibővül az albumcímekre (az eredeti csak
fájlnévre és címkére keres), `SAJÁT FUNKCIÓ` jelölés nélkül.

**Validálás (2026-08-27): TÜZEL — de a validálás egy csapdát is feltárt.**
Az első magvetőm a saját magyarázó mondatában leírta a `SAJÁT FUNKCIÓ`
kifejezést, ezért egy nyers `grep` **jelöltnek** látta a jelöletlen fájlt.
Ebből a lencse kötelező eleme lett: **a puszta kulcsszó-keresés nem elég** —
a lencsének az EREDETI viselkedést kell referenciának vennie, és azzal
összevetnie. Javított magon: 0 jelölés, 0 jegyzék-sor, a lencse tüzel.

### 3. Visszavont döntés (#616 ↔ #422)

| | |
|---|---|
| **kiváltó** | olyan elrendezési/viselkedési kérdés, amiről születhetett már döntés |
| **a kérdés** | *Volt-e már döntés erről? Keresd a `docs/decisions/` lapokat **téma szerint**, ne fájlnév szerint.* |
| **mit kell megtalálnia** | korábban kifejezetten elvetett megoldás csendes visszatérését |
| **gépi fedezet ma** | `scripts/check_decision_links.py` (#1623) — **részleges**, ld. lent |

**Magvető minta:** a szerkesztő felső sávjába visszakerül a kereső és az
Importálás gomb, „kényelmetlen a hiányuk" indoklással — a
`docs/decisions/szerkeszto-bal-panel.md` 1. pontja viszont kimondja, hogy
szerkesztés közben **csak** a „Vissza a könyvtárhoz" gomb látszik. A PR
tesztet is hoz, ami a HIBÁT rögzíti szerződésként (ez a #616 pontos mintája).

**Validálás (2026-08-27): TÜZEL, és NEM redundáns.** Lefuttattam a magvetett
változásra a #1623 új őrét: **0 eltérést jelez** — mert a döntési lapot a
változás nem érinti, és minden `Kötés`-útvonal létezik. A gépi őr a
*deklarált* éleket ellenőrzi; azt, hogy egy változás **tartalmilag**
ellentmond egy döntésnek, nem tudja eldönteni. A lencse kérdése viszont
megtalálja: témára keresve a `docs/decisions/`-ben a
`szerkeszto-bal-panel.md` előjön.

---

## A három nyugdíjazott lencse — a hibaosztályt már gép fogja

Ezek **nem törlődtek**, hanem **változás által kiváltottá** váltak: csak akkor
futnak, ha a hozzájuk tartozó terület változott. Minden más körben ~0 hozamúak.

| lencse | a gépi őr, ami átvette | kiváltó, amikor mégis fut |
|---|---|---|
| platform-varrat (#1217) | `tests/test_platform_seam_1217.py` | platformfüggő kód vagy `skipif` változik |
| csomag-tartalom (#646) | CI-job: „Csomag-tartalom (a felépített wheel)" | `pyproject.toml`, csomagolás, adatfájlok |
| i18n-`vanished` | `tests/app/test_i18n_completeness.py` | `.ts`, `qsTr`, kötött fordítás |

---

## Hozam-napló

Lencsénként egy sor: hány kört futott, hány **valódi** leletet hozott. A nulla
hozamú lencse nyugdíjazható — a jegyzék akkor ér valamit, ha rövidülhet is.

| lencse | kör | valódi lelet | megjegyzés |
|---|---|---|---|
| kirajzolt felület | 0 | 0 | bevezetve 2026-08-27 |
| jelöletlen SAJÁT FUNKCIÓ | 0 | 0 | bevezetve 2026-08-27 |
| visszavont döntés | 0 | 0 | bevezetve 2026-08-27; a #1623 őre miatt szűkebb hatókörrel |

## A költség MEGMÉRVE (2026-08-27, #28) — a soros menet NEM kötelező

| ág | idő | találat a 3 magvetett hibából |
|---|---|---|
| 3 soros lencse-menet, alacsony gondolkodási szint | **89 s** | **2 / 3** |
| 1 alapos menet, magas gondolkodási szint | **115 s** | **3 / 3** |

**Az eredeti állítás megdőlt:** a lencse-ág 77%-nyi idő alatt kevesebbet
talált. És a mérés **A-nak kedvezett** — a korpuszt a lencse-definíciókból
építettem, mindhárom magvetett hiba pontosan egy lencse hatókörébe esett.
Valódi diffnél ez az előny nincs meg.

⚠️ **Korlát:** a `gpt-5.1-codex-mini` nem érhető el a fiókon, ezért a
költség-tengely gondolkodási szint lett, nem modellosztály. Az eredeti,
modellosztályra vonatkozó állítást a mérés nem dönti el közvetlenül.

### A validálási ceremónia határa — ezt a mérés tanította

A **jelöletlen SAJÁT FUNKCIÓ** lencse a saját célját hibázta el: a neki szánt
magvetett hibát (keresési hatókör bővülése) kihagyta, közben a másik kettőre
tüzelt. **A magvetéses validálás tehát azt igazolja, hogy a lencse nem néma —
nem azt, hogy a saját hibaosztályát megfogja.** Aki lencsét vesz fel, ezt
tudja be a validálás értékébe.

### Mit jelent ez a jegyzékre

**A lencsék használata OPCIONÁLIS.** Ha egy kör tudja, melyik hibaosztályra
gyanakszik, a lencse kérdése hasznos horgony. Kötelező soros menetet a
skillekbe nem írunk elő — az alapértelmezés az egy alapos menet marad.
