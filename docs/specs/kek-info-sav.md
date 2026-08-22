# Az alsó kék információs sáv (`thumbui/infotext`)

*Forrás: `Picasa3/runtime/thumbui.tre`, a `Picasa3.exe` bináris index
(`GetSelectionInfo` = `0x0056fbc0`, `BigView` = `0x00566a70`), a
`Picasa3i18n.dll` magyar erőforrásai (`stringres.xml`), valamint valódi
Picasa-képernyőképek. Készült a #1189-hez, 2026-08-22.*

## 1. Mi ez az elem

A könyvtárablak alján, a fotótálca fölött futó kék sáv középre igazított
szövege. A felület leírójában:

```
thumbui/infotext: thumbui/infotext_clip      # thumbui.tre:683
m_offsetT
m_scaleX
m_displayfont12
Property textalign center
Property forceuidirection 1

thumbui/infotext_clip: thumbui/basecontrolset
XConstraint 0, 0, 20
XConstraint 1, 1, -20
```

Tehát: a sáv teljes szélességét kitölti 20-20 képpont margóval,
**középre igazított**, `displayfont12` betűvel. A `.tre` **nem ad hozzá
feliratot** — a tartalmat kód írja.

Két függvény írja:

| függvény | mikor |
|---|---|
| `0x0056fbc0` (`GetSelectionInfo`) | a rácsban, a **kijelölés** alapján |
| `0x00566a70` (`BigView`) | a nagy nézetben, az **épp mutatott kép** alapján |
| `0x005706b0` | a sáv ürítése/beállítása (338 bájt, csak az elemnevet hivatkozza) |

## 2. A `GetSelectionInfo` öt alakja

A függvény öt honosított formátumot használ. A kulcs → magyar szöveg
párosítás a `Picasa3i18n.dll` `stringres.xml`-jéből (mentve:
`referencia/i18n-hu/stringres.xml`):

| kulcs | angol (bináris) | magyar (i18n) |
|---|---|---|
| `il_GetSelectionInfo::1` | `No Selection` | `Nincs kijelölés` |
| `il_GetSelectionInfo::2` | `%s     %s     %dx%d pixels     %s` | `%1$s     %2$s     %3$dx%4$d képpont     %5$s` |
| `il_GetSelectionInfo::3` | `%s pictures` | `%s képek` |
| `il_GetSelectionInfo::4` | `     %s to %s     %s on disk` | `     %1$s-%2$s     %3$s a lemezen` |
| `il_GetSelectionInfo::5` | `     %s      %s on disk` | `     %1$s      %2$s/lemez` |

Az elválasztó **öt szóköz** (a `%s     %s` alakokban is), a `::4`/`::5`
pedig már öt szóközzel **kezdődik** — vagyis a darabszám után fűződik.

### 2.1 A négy üzemmód

| állapot | a sáv tartalma |
|---|---|
| nincs kijelölés | `Nincs kijelölés` (`::1`) |
| **egy** kép | `név     dátum-idő     SZxM képpont     méret` (`::2`) |
| **több** kép, eltérő dátum | `N képek` (`::3`) + `     legkorábbi-legkésőbbi     összméret a lemezen` (`::4`) |
| **több** kép, azonos dátum | `N képek` (`::3`) + `     dátum      összméret/lemez` (`::5`) |

### 2.2 Képernyőképes megerősítés

`research/testdata/screenshot/2026-07-17 20 55 20.png` (magyar Picasa 3):

```
25 képek     2026. január 2., péntek-2026. május 18., hétfő     37,5 MB a lemezen
```

Ugyanabból a sorozatból, egy kijelölt képnél:

```
2026-02-19-18-05-05-202.jpg     2026. 02. 20. 3:28:06     1920x1080 képpont     1,4 MB
```

Ebből két dolog **mérve**, nem következtetve:

1. a **több** kijelöltnél használt dátum **hosszú, napnevessel**
   (`2026. január 2., péntek`), a két végpont között **szóköz nélküli
   kötőjel**;
2. az **egy** kijelöltnél használt dátum **rövid, numerikus, időponttal**
   (`2026. 02. 20. 3:28:06`).

## 3. A nagy nézet (`BigView`, `0x00566a70`)

Ugyanezt az elemet írja, de a saját formátumaival:

| kulcs | magyar |
|---|---|
| `il_BigView::1` | `%1$s     %2$s     %3$dx%4$d képpont     %5$s` |
| `il_BigView::2` | `     (%2$d / %1$d)` |
| `il_BigView::3` | `(nincs)` |
| `il_BigView::4` | `%1$d / %2$d` |

Vagyis a nagy nézetben ugyanaz a négymezős sor fut, **kiegészítve a
sorszámmal** (`(3 / 25)`). A `(nincs)` a hiányzó mező helyőrzője.

## 4. A mi megvalósításunk — tételes összevetés

| eset | eredeti | nálunk | állapot |
|---|---|---|---|
| egy kép | név, dátum-idő, SZxM képpont, méret | ugyanaz (`photoInfo` → `formatting.photo_info_text`) | ✅ megvan |
| **több kép** | `N képek` + dátum(tartomány) + összméret | **a MAPPA egészének** összesítése | ❌ **hiba volt — ez a jegy javítja** (`selectionInfo`) |
| több kép, azonos dátum | külön alak (`::5`) | a dátumtartomány egyetlen dátumra rövidül (`formatting.status_text`) | ✅ egyenértékű |
| nagy nézet | négymezős sor + `(i / N)` | `viewerInfo` — ugyanaz | ✅ megvan |
| nincs kijelölés | `Nincs kijelölés` | a mappa összesítése | ⚠️ **eltér, szándékosan** — ld. 4.1 |

### 4.1 A „nincs kijelölés" eset — miért NEM vettük át

Az eredetiben a bal hasábon **mappát választva a mappa képei
kijelöltté válnak** (a tálca buborékja is ezt mondja: „Kiválasztott mappa
– 25 fotó"), ezért a `Nincs kijelölés` állapot a gyakorlatban ritka.
Nálunk a mappaválasztás nem jelöl ki semmit, így a `Nincs kijelölés`
felirat a sáv **állandó** tartalma lenne — a mappa összesítése
hasznosabb, és pontosan azt az adatot mutatja, amit az eredeti a
mappa-kijelöléskor.

Ha a mappaválasztás egyszer átveszi az eredeti kijelölő viselkedését, ez
az eltérés magától megszűnik. Külön jegy: a mappaválasztás mint kijelölés.

## 5. Amit NEM vizsgáltunk

Kimondva, hogy ne látszódjon késznek:

- **videó** kijelölésekor mit ír a sáv (a `BigView` hivatkozik egy
  `videolink` elemre, de a formátum-ág nincs kimérve);
- **hiányzó/sérült** fájl esetén (a `(nincs)` = `il_BigView::3` helyőrző
  hova kerül pontosan);
- **több mappából** származó kijelölés — az eredetiben ilyen nincs
  (a kijelölés mindig egy mappáé, #1145/#1219), nálunk a mostani
  megvalósítás a kapott sorokat összesíti, mappától függetlenül;
- a sáv **egyéb üzenetei** (folyamatjelzés, hibaüzenet) — a `0x005706b0`
  szerepe csak részben tisztázott.
