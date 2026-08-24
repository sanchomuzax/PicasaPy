# A „Hisztogram és fényképezőgép-adatok" panel (`nerdview`) — MÉRT geometria

*Kutatói kör: 2026-08-24, a tulajdonos egymás melletti képernyőképe nyomán.*

A néző bal alsó doboza. Belső neve **`nerdview`**, a felirata a
`nerdview/nvhead` elem.

## 1. A teljes panel: 238 × 144

A `respack.yt` rétegfejléceiből (13 bájt, `int16 x0,y0,x1,y1`), a
`nerdview/docbounds`-hoz **relatív** koordinátákkal:

| elem | respack-név | x0,y0 | x1,y1 | **méret** |
|---|---|---|---|---|
| a panel doboza | `nerdview/docbounds` · `#rect: floater` | 0, 0 | 238, 144 | **238 × 144** |
| **a felirat** | `static(Histogram & Camera Information): nvhead` | **13, 4** | 113, 15 | **100 × 11** |
| a hisztogram háttere | `rect: histoback` | 13, 25 | 226, 84 | **213 × 59** |
| a hisztogram | `histogram(editpanel/previewimage): histo` | 13, 25 | 226, 84 | **213 × 59** |
| kameraadat, **bal** oszlop | `text: detail1` | **13, 82** | 151, 123 | **138 × 41** |
| kameraadat, **jobb** oszlop | `text: detail2` | **157, 82** | 226, 123 | **69 × 41** |
| bezáró gomb | `#button: close` | 207, 5 | 218, 16 | 11 × 11 |

**Amit ebből tudni kell:**

- a felirat **egyetlen sor, 11 képpont magas** — a doboz nem enged
  többsorosat, és a panel 238 képpont széles, tehát a magyar szöveg is elfér;
- a hisztogram rajzterülete **213 × 59** (ezt a #864 már helyesen kimérte, és
  a megvalósításunk követi is);
- a két kameraadat-oszlop **nem egyforma**: bal **138**, jobb **69**, a rés
  köztük 151→157 = **6 képpont**;
- a tartalom `y = 123`-nál véget ér, a panel 144 magas → **21 képpont alsó
  térköz**;
- a bezáró gomb a `.tre`-ben **ki van kommentezve** (`#nerdview/close: root`),
  tehát a 3.9-ben **nem látszik**.

## 2. A felirat betűje

`nerdview.tre`:

```
nerdview/nvhead: root
m_displayfont14
```

Az `m_displayfont14` a Picasa erőforrás-nyelvének **font-token neve**, nem
Qt-pontméret. A **mérvadó a doboz magassága: 11 képpont**, egy sorra.

> ⛔ **A `.tre`-ben SEMMI nem jelöl félkövéret.** A `nvhead` egyetlen
> tulajdonsága a fenti font-token. Bármilyen félkövér/nagyméretű cím a
> mi kitalálásunk.

Szövegforrás (`editpaneltext.tre`):

```
Text nerdview/nvhead
Histogram & Camera Information
```

magyarul: **„Hisztogram és fényképezőgép-adatok"**.

## 3. Elhelyezés a szerkesztőben

`editpanel.tre`:

```
editpanel/nerdview_container: root
XConstraint 0, 0, LEFTDRAWEROFFSET, 20
YConstraint 1, 1, -95

nerdview/histo: nerdview/histoback
m_centerXY
```

⇒ A panel az ablak **aljához** horgonyzott (−95 képpont), balról
`LEFTDRAWEROFFSET + 20`. A hisztogram a háttérrétegére **középre** kerül.

## 4. Eredeti / nálunk

*A #1344 (2026-08-24) óta a `HistogramBox.qml` a mért geometriát követi: a
`ColumnLayout` + 8-as margó helyett fix, koordinátás elrendezés van. A
„nálunk korábban" oszlop a javítás ELŐTTI állapotot rögzíti.*

| | eredeti (mért) | nálunk korábban | ma (`HistogramBox.qml`) |
|---|---|---|---|
| felirat betűvastagság | **normál** (nincs jelölés) | `font.bold: true` | ✅ `font.bold: false` |
| felirat mérete | **11 képpont soronként**, egy sor | `font.pointSize: 14` (~19 képpont) | ✅ `height: 11`, `font.pixelSize: 11` |
| felirat tördelése | **nincs** — egy sor, a 238-as panelben elfér | `wrapMode: WordWrap`, `maximumLineCount: 2` | ✅ egysoros (`NoWrap`) |
| felirat helye | x = 13, y = 4 | `ColumnLayout` 8-as margóval | ✅ x = 13, y = 4 |
| hisztogram | 213 × 59 | ✅ **213 × 59** (#864) | ✅ 13, 25-től 213 × 59 |
| kameraadat-oszlopok | **138 + 6 + 69** | egyenlő oszlopok | ✅ 138 + 6 + 69 |
| panel mérete | 238 × 144 | tartalomtól függő magasság | ✅ rögzített 238 × 144 |
| alsó térköz | 21 képpont | 8-as margó | ✅ 21 (a sáv 123-nál zárul) |
| bezáró gomb | **nincs** (kikommentezve) | nincs | nincs |

A `detail1` teteje (82) 2 képponttal a `histoback` alja (84) FÖLÉ ér — ez
az eredetiben is így van, a megvalósítás átveszi. Az őrteszt ezért 2
képpont átfedést enged, de azt állítja, hogy a geometria a szöveg
mennyiségétől független
(`tests/app/qml_functional/test_histogram_panel_geometry_1344.py`).

## 5. Miért tért el — a felelősség helye

A hisztogram **rajzterületét** egy korábbi kör (#864) helyesen kimérte, és a
megvalósítás követi is. A **feliratot, a panel dobozát és a két
adatoszlopot viszont soha senki nem mérte ki** — a spec nem tartalmazta
őket, tehát a fejlesztőnek nem volt mit követnie, és kitöltötte a hiányt
(#235: „a cím mindig teljes" → két sorra tördelés + félkövér 14 pont).

> **Ez kutatási hiány, nem fejlesztői hiba.** A tanulság: ha egy panelnek
> egy elemét kimérjük, a **többi elemét is ki kell**, különben a hiányzó
> részekre találgatás épül — és a találgatás zöld teszt mellett is elmegy.

*Bizonyítottsági fok: **megerősített** — a geometria a `respack.yt`
rétegfejléceiből, a font-token és a hiányzó félkövér-jelölés a `.tre`-ből,
a szöveg az `editpaneltext.tre`-ből.*
