# A Picasa fő ablakának elrendezése — a forrásból

A `respack.yt`-ből kinyert **140 `.tre` elrendezés-forrásfájl** alapján. Ezek
a Picasa saját, kényszer-alapú (constraint) UI-leíró nyelvén íródtak, és nem
képernyőkép-mintavételből származnak — a számok **pontosak**.

Kinyerés:

```bash
python3 tools/picasa/respack.py tre \
    research/copy_Picasa_3_7/Picasa3/runtime/respack.yt <celkonyvtar>
```

## A legfelső szint — `panelroot.tre`

A gyökér **egymást váltó, teljes méretű panelekből** áll, nem egymásba
ágyazott dobozokból:

| panel | mikor látszik |
|---|---|
| `mainuipanel` | a normál könyvtár-nézet (ez az alapértelmezett) |
| `makemoviepanel` | filmkészítés |
| `collagepanel` | kollázs |
| `acquirepanel` | importálás |

Mindegyik `m_scaleX` (vízszintesen nyúlik) és `YConstraint 0,0,tabdiv` …
`YConstraint 1,1,0` — vagyis **a `tabdiv` alatti teljes területet elfoglalja**.
A váltás `showtarget`/`hidetarget` párokkal megy, a `globaltabs` sávról.

Minden panelhez tartozik egy `addtofocus` lista — ez adja meg a
**billentyűzet-fókusz sorrendjét**.

## A könyvtár-nézet — `thumbui.tre`

### A hiteles méretek

| konstans | érték | mit jelent |
|---|---|---|
| **`HLISTOFFSET2`** | **240** | **a bal panel szélessége képpontban** |
| `searchtop` | 35 | a felső sáv magassága |
| `publishbottom` | −105 | az alsó sáv magassága (az ablak aljától) |
| `RIGHTDRAWEROFFSET` | 0 | a jobb fiók szélessége (alapból behúzva) |
| `LEFTDRAWEROFFSET` | 0 | |
| `tabdiv` | 0 | a globális fülsáv magassága (alapból nincs) |

> **A bal panel FIX 240 képpont, nem százalék.** A `hlistsizer` elemen ott a
> `Handler hsplitoffset HLISTOFFSET2` — vagyis **húzható elválasztó**, ami ezt
> a változót írja át. Az ablak átméretezésekor a bal panel **nem skálázódik
> arányosan**: a rács nő, a panel marad.

### Az elrendezés

```
mainuipanel
├── (felül, 35 px)          fejléc / keresősáv
├── listdecrect             a bal panel kerete: x 0 … HLISTOFFSET2
│                           y 35 … alul −105
├── hlistsizer              a húzható elválasztó (x = HLISTOFFSET2 − 4)
├── albumsback              a rács háttere: x HLISTOFFSET2 … jobb −RIGHTDRAWEROFFSET
│                           y 35 … alul −105
├── right_drawer            jobb fiók (alapból rejtett)
└── (alul, 105 px)          a képtálca és a vezérlők sávja
```

### Gyökér szintű (az egész ablakra lebegő) elemek

`largethumbs` · `smallthumbs` · `acquirebutton` · `viewswitch` ·
`horizonadjust` · `prev` · `next` · `fit` · `morethumbs` · `lessthumbs` ·
`soloview` · `uploadmgr` · `histogram` · `visitweb` · `circlecursor`

Ezek **nem a panelhierarchia része** — közvetlenül a `root`-hoz kötöttek,
tehát a panelváltás nem érinti őket.

## Eltérés a PicasaPy-tól

| | eredeti | nálunk | teendő |
|---|---|---|---|
| bal panel szélessége | **240 px fix**, húzható | `folderPaneWidth`, alap **230** | 240-re |
| a bal panel viselkedése átméretezéskor | **nem skálázódik** | — | ellenőrizni |
| felső sáv | 35 px | ? | ellenőrizni |
| alsó sáv | 105 px | ? | ellenőrizni |

> **A `design-guide.md` két, egymásnak ellentmondó értéket tartalmaz**
> (386 px ≈ 20 %, illetve 210 px ≈ 26 %), és azt írja, hogy „arányosan
> skálázandó". **Mindkettő téves**: a forrás szerint 240 px, fix, húzható
> elválasztóval. A képernyőkép-mintavételből származó becslést itt a
> forráskód felülírja.

## Elérhető, még fel nem dolgozott elrendezések

A 140 fájlból eddig a `foldermgr`, a `panelroot` és a `thumbui` van
feldolgozva. További, közvetlenül hasznos források:

`editpanel` (szerkesztő) · `oneup` (nagy nézet) · `headerpanel` ·
`peoplepanel` · `tagpanel` · `searchoptions` · `printpanel` ·
`collagepanel` · `makemoviepanel` · `slideshowctrls` · `moviecontrols` ·
`video_control_bar` · `propertiespanel` · `nav` · `rightdrawerpanel`

Mindegyik ugyanígy pontos geometriát ad.
