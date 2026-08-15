# A vörösszem-eszköz terve (#720)

**Státusz:** irodalmi feltárás kész, döntés megvan, megvalósítás nincs.
A funkció **P3** — a Picasa-kompatibilitáshoz nem kell (ld. lent), csak akkor,
ha a PicasaPy **saját** vörösszem-eszközt kap.

**Forrás:** NotebookLM-kutatás, 52 forrás (a notebook azonosítója a privát repó
`memory/hivatkozasok.md`-jében). **Ez irodalmi összefoglaló, nem általunk
ellenőrzött mérés** — a bizalmi foka ennek megfelelő: a képletek és a
nagyságrendek kiindulásnak jók, de mérni nekünk kell.

## ⚠️ Jogi korlát: egy eljárást KI KELL hagyni

A vörösszem-detektálás egyik legpontosabbnak leírt eljárása —
**SVM-osztályozó a jelölt foltok köré vágott 32×32-es képrészleteken**,
gradiens-orientációs hisztogramokkal — a **Xerox Corp. szabadalma**:

> **US7567707B2** és **US20070140556A1** — a források szerint az oltalom
> **2028. január 21-ig** él.

**Ezt az utat nem szabad választani.** Nem jogi tanács, hanem
kockázatkerülés: van három, szabadalmi tehertől mentes alternatíva, amelyek
közül a legjobb amúgy is előrébb végzett a rangsorban.

## A választott irány: YCbCr-szegmentálás alakzatszűrőkkel

Ez végzett elsőnek a pontosság / sebesség / jogtisztaság hármasban.

### Detektálás

1. **YCbCr színtér** (`cv2.cvtColor`) — a vörös pupilla a `Cr` csatornán ad
   erős lokális kiugrást. Ez azért is olcsó, mert a JPEG natívan YCbCr-ben
   tárol, tehát a dekódolásból közvetlenül kinyerhető.
2. **Dinamikus küszöb** a lokális statisztikából:
   `Cr > μ_Cr + k · σ_Cr`, ahol `k ≈ 1,5…2,0`.
3. **Morfológiai zárás** (tágítás + erózió) a zajfoltok kiszűrésére.
4. **Geometriai érvényesítés** — ez tartja kordában a téves találatokat:
   - kerekdedség: `4πA / P² ≥ 0,6`
   - kitöltési tényező: `A / (Δx·Δy) ≥ 0,5`

### Javítás

```
R_uj = G + 0,2 · B                       # a vörös csatorna leszorítása
ha Y > 220: a képpont ÉRINTETLEN         # a csillanás megőrzése
```

A maszkot **3×3 Gauss**-szal el kell mosni, és alfa-keveréssel visszasimítani,
különben látható fekete korong marad („dead eye"):

```
vegso = M_elmosott · javitott + (1 − M_elmosott) · eredeti
```

### Amit ez ad és amit nem

- **Sebesség:** valós idejű 12 megapixelen; nem kell gépi tanulási modellt
  szállítani a szoftverrel.
- **Gyenge pontja:** arcdetektálás nélkül a kerek, piros háttérelemeket
  (ruha, rúzs, lámpa) is megjelölheti, ha a geometriai szűrők lazák.

## A két másik jogtiszta út (ha az első nem válik be)

| eljárás | detektálás | javítás | miért nem ez az első |
|---|---|---|---|
| **Haar-kaszkád + RGB-arány** | `haarcascade_eye.xml` leskálázott képen, majd `R / ((G+B+1)/2) ≥ 1,5…2,1` | `R_uj = (G+B)/2` | pár sorból prototipizálható, de a Haar dőlt/takart arcnál elbukik, és a javítás lilás árnyalatot hagyhat |
| **CIELab többmaszkos** | `a* > 20` vörös maszk + szemfehérje- és bőrmaszk, `P(szem) = P(R)·P(W)·P(S)` | `a* = b* = 0`, `L*` széthúzás | a legjobb téves-riasztás-szűrés, de a CIELab-konverzió 12 MP-en 1–2 másodperc |

A Haar-kaszkádos út **prototípusnak** így is hasznos: gyorsan megmutatja, hogy
a javítási képlet jó irányba visz-e.

## Összevetés a mért Picasa-viselkedéssel

A #371 körében **valódi Picasa-szerkesztett képekből** mértük, mit csinál az
eredeti ([`picasa-ini-format.md`](picasa-ini-format.md)):

| | a mi mérésünk (Picasa) | az irodalom ajánlása |
|---|---|---|
| a vörös új értéke | `R' ≈ max(G, B)` | `R' = G + 0,2·B` (YCbCr-út) vagy `(G+B)/2` (Haar-út) |
| folt mérete | 8–16 képpont 1280×960-on | — |
| csillanás | (nem vizsgáltuk külön) | `Y > 220` felett érintetlen |

A három képlet **ugyanabba az irányba** mutat (a vörös a másik két csatorna
szintjére húzódik), de nem azonos. A `max(G, B)` valamivel világosabb
eredményt ad, mint a `(G+B)/2`.

**Ez nem ütközés:** a mi eszközünk nem köteles a Picasát utánozni. A Picasa
kimenetét csak **változatlanul kell továbbadnunk** (ld. lent) — az új
javításnál szabadon választhatunk.

## ⚠️ Amit a megvalósításnak NEM szabad elrontania

A Picasa a vörösszem-javítást a **mentett képpontokba égeti**, koordinátát
sehol nem tárol (#371, megerősített). Ezért:

> A `redeye=1;` bejegyzést a renderelés során **azonosságként** kell kezelni.
> Ha a saját algoritmusunk ráfutna egy Picasa által már javított képre,
> **kétszer javítanánk**.

A saját eszköz kimenetét tehát **külön kell jelölni** az ini-ben (a mi
kiterjesztésünkkel), nem a csupasz `redeye=1;` alakkal.

## Következő lépés

Prototípus a YCbCr-úton, és **mérés a saját anyagunkon**: a `.picasaoriginals`
mappákban 113 olyan eredeti kép van, amit a Picasa megjavított — ezek
**kész próbakészletet** adnak. A cél nem a Picasa utánzása, hanem hogy a mi
detektálásunk ugyanazokat a szemeket találja meg.

A megvalósítás `picasapy-dev` feladat; ez a lap a **terv**, nem a kód.
