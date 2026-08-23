# A gyári projekt-mappák (#1131, 2026-08-23)

A **Projektek** gyűjtemény tételei nem véletlenszerű mappák: mindegyiket a
saját funkciója hozza létre a `Picasa\<mappanév>` alatt, és a besorolást a
`.picasa.ini` `[Picasa] P2category` kulcsa adja (#1029).

---

## 1. A hat mappa

| mappa (angol → magyar) | erőforrás-kulcs | mikor kerül bele anyag |
|---|---|---|
| `Collages` → **Kollázsok** | `CCollageManager::CollagesFolder` (`0x00ca778c`) | kollázs mentésekor (piszkozat és kész is) |
| `Movies` → **Mozgófilmek** / **Filmek** | `CMakeMoviePanel::SlideshowFolder` (`0x00c9ce3c`) | filmkészítéskor |
| `Screen Captures` → **Képernyőfelvételek** | `Scrapture::capturepath` | képernyőfelvétel készítésekor |
| `Captured Videos` → **Rögzített videoklipek** | `CCaptureFrame::CaptureFolder` | videórögzítéskor (webkameráról) |
| `Exported Pictures` → **Exportált képek** | `IDS_EXPORTED_CATEGORY` | exportáláskor |
| `Other Stuff` → **Egyebek** | `IDS_DEFAULTCAT` | a be nem sorolt mappák gyűjtője |

A magyar alakok a `Picasa3i18n.dll` hivatalos fordításai (`stringres.xml`).

---

## 2. ⚠️ A mappanév MAGA IS honosított — ezért lehet több ugyanabból

A `Scrapture::capturepath` nem egy mappa *címkéje*, hanem **maga az
útvonal**, fordítható erőforrásként:

```
Scrapture::capturepath   Picasa\Screen Captures\   →   Picasa\Képernyőfelvételek\
```

**Más nyelvű Picasa tehát MÁS mappát hoz létre, és a régit nem költözteti
át.** A tulajdonos NAS-korpusza ezt megerősíti — három film-mappa áll
egymás mellett:

```
/mnt/photo/Picasa/Movies
/mnt/photo/Picasa/Filmek
/mnt/photo/Picasa/Mozgófilmek
```

plusz `Captured Videos` **és** `Rögzített videoklipek`.

➡️ **Ez az eredeti viselkedése, nem hiba.** De nekünk döntenünk kell, mit
használunk — és a döntés a 3. szakasz.

---

## 3. A mi szabályunk: a MEGLÉVŐ nyer, újat csak ha nincs

`src/picasapy/app/project_folder_names.py`:

1. ha a **mai nyelv szerinti** mappa létezik → az (a felhasználó
   aktuális Picasájának mappája);
2. ha nem, de **bármelyik más ismert alak** létezik → az;
3. ha egyik sem → a mai nyelv szerinti nevet hozzuk létre.

Így **mi nem nyitunk néma harmadikat** a felhasználó gépén. Fájlt sosem
nézünk mappának.

---

## 4. A KÉT „Kollázsok" — ez a MI nyomunk volt

A tulajdonos képernyőképén két Kollázsok állt, **mindkettő magyarul**:
tehát nem nyelvi duplikátum. A #1088 előtt a PicasaPy a
`home\Pictures\Picasa\Kollázsok`-ba írt, a valódi Picasa pedig a
rendszer valódi képmappájába (`Képek\Picasa\Kollázsok`). Mindkettő
megkapta a `P2category` jelölést, ezért mindkettő látszik.

A #1088 óta az **új mentések a helyes mappába** mennek. A **régi mappa
ott marad** — és ez szándékos:

> ⚠️ **Némán törölni tilos.** A felhasználó fájljai vannak benne.

**Nyitva marad** (külön döntés, önálló jegy): mutassuk-e a régi,
elárvult mappát, rejtsük, vagy ajánljuk fel az egyesítést. Ez a lap
csak azt rögzíti, hogy **nem keletkezik újabb**.

---

## 5. Bizonyítottsági fok

**Megerősített**: a hat mappa és az erőforrás-kulcsaik (string-tábla), a
honosított útvonal ténye (`Scrapture::capturepath` értéke mindkét
nyelven), és a több-mappás együttállás (a tulajdonos NAS-korpusza).

**Nincs kimérve**: mit tesz az eredeti, ha MINDKÉT nyelvű mappa létezik —
oda ír-e, amelyiket a mai nyelve mondja, vagy a régit használja. A mi
szabályunk (a mai nyelv nyer, ha létezik) ésszerű választás, nem mérés.
