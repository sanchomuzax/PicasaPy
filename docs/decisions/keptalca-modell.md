# ADR: A képtálca EGY modell — a kollázs „Klipek" lapja ugyanez, más szűréssel

Dátum: 2026-08-27 · Státusz: ELFOGADVA · jegy: #455 (kapcsolódik: #1276, #1153)

## A helyzet

A képtálca (`scratch`, felirata „Selection") és a kollázs-szerkesztő
**„Klipek" lapja** két külön felületnek látszik, és nálunk eddig két külön
adatforrásra épült: a tálca a `TrayMixin` saját id-listájára, a Klipek lap a
`controller.collageNodes`-ra (a kollázsra MÁR feltett elemekre).

A 2026-08-27-i kollázs-kutatás kimutatta, hogy **a Picasában ez ugyanaz a
munkafolyamat**. Három, egymástól független szöveg mondja ki:

| forrás | szöveg |
|---|---|
| `collagepanel/deleteclips` súgója | „Remove selected clips from the **tray**" |
| `collagepanel/getmoreclips` súgója | „Get more clips from the **Library**" |
| `collagepanel/filmstrip_title` | **`Unused Pictures`** |

A lap tehát **készlet**, amiből válogatsz: a Könyvtárból a **tálcára** hozol
képet, onnan teszed a kollázsra, és a felhasznált kikerül a listából.

Ehhez jön egy negyedik, számszerű nyom. Két, egymástól függetlenül feltárt
számláló-hurok **ugyanazt a bájtot kérdezi ugyanazon az eltoláson**:

| hurok | mit számol | feltétel |
|---|---|---|
| `0x00716cb0` — a tálca „régóta tartott elemek" küszöbe | a **nem kizárt** elemek | `[elem+0x5a] == 0` |
| `0x0083b590` — a „Klipek (%d)" fülfelirat száma | a **fel nem használt** elemek | `[elem+0x5a] == 0` |

⚠️ A `+0x5a` pontos jelentése **nem megerősített** (mindkét spec-lap így
rögzíti). Amit a két hurok együtt bizonyít, az annyi, hogy **ugyanannak az
elemosztálynak ugyanazt a jelzőjét** kérdezik — vagyis a tálca elemei és a
Klipek lap elemei egy és ugyanazok.

## A döntés

**Egy modell van, felület-független magban: `src/picasapy/tray/`.**

```
TrayItem(photo_id, held, used)      TrayState(items, remembered_count)
```

- **`photo_id`** a kulcs, nem a rács sor-indexe — az mappánként/szűrésenként
  mást jelentene, és a tálca épp attól tálca, hogy átnyúlik rajtuk.
- **`held`** — „Kijelölés megtartása": a következő kijelölés nem söpri el.
- **`used`** — felhasználtság. **Az adatmodellben van, nem a nézetben**: a
  Klipek lapnak elég a `used === false` elemeket kirajzolnia („Unused
  Pictures"), a főablak tálcája pedig mindet mutatja. Két külön lista két
  külön igazsággal pár művelet után szétcsúszna.
- Minden művelet **új állapotot ad vissza**; a `TrayState` fagyasztott.

A Qt-s réteg (`app/tray_controller.py`) csak **fordít**: rács-sorból
azonosító, azonosítóból útvonal/bélyegkép, és jelzés a felület felé.

### Hogyan ül rá a Klipek lap (#1276)

| a lap eleme | a modell művelete |
|---|---|
| a filmszalag tartalma | `trayItems`, `used === false` szerint szűrve |
| „Klipek (N)" száma | `trayUnusedCount` |
| „+" (felvétel a kollázsra) | `markTrayUsed([...])` — a kép a tálcán MARAD |
| „–" (*Remove selected clips from the tray*) | `removeHeldRows` / `tray.without` |
| „Továbbiak…" | a Könyvtárból való válogatás → `holdRows` |

## Amit a modell szándékosan NEM csinál

**Nem tartós.** A tálca tartalma a program bezárásával elvész. Három
független ellenőrzés mondta ki (`docs/specs/picasa-keptalca.md` 1.): nincs
`]scratch` token a valódi `albumdata_token.pmp` 2371 sorában, nincs
tálca-fájl a `Picasa2` profilmappában, és nincs tálca-témájú `Preferences`
kulcs a bináris sztringtárában. **Megőrizni eltérés lenne, nem javítás.**

## Két saját döntés, kimondva

1. **A felhasznált elemet a következő kijelölés sem söpri el.** Az eredeti
   söprési szabálya nincs kimérve erre az esetre. A felhasználtság olyan
   állapot, amit a kijelölésből nem lehet visszaállítani — elsöpörni néma
   adatvesztés volna. Ez a mi döntésünk, nem mérés.
2. **A jelvény (`holdadorner`) csak a RÖGZÍTETT képen jelenik meg**, nem
   mindenen, ami a tálcán van. A tálca alapból a kijelölés tükre, és minden
   kijelölt képre kitett jelvény csak a kijelölés-keretet ismételné meg.

## Ami készen áll, de felület nélkül

A **`il_ClearFromTray`** felkínált takarítás („El szeretné távolítani a
tálcán régóta tárolt elemeket?"). A SZABÁLYA megvan és tesztelt
(`needs_old_items_prompt` / `with_remembered_count`): **nem idő-alapú**,
hanem darabszám-növekedés — a nem kizárt elemek száma nagyobb-e a legutóbb
megjegyzettnél (`0x00571e50`, a `+0x3194` mező). Hogy az eredeti melyik
pillanatban teszi fel a kérdést, **nincs kimérve**, ezért a párbeszédet nem
építettük meg: kitalálni rosszabb volna, mint hiányozni hagyni.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/tray/model.py`,
  `src/picasapy/app/tray_controller.py`,
  `src/picasapy/app/qml/PicasaPy/TrayBar.qml`
- **Őrzi:** `tests/tray/test_tray_model.py`,
  `tests/app/qml_functional/test_keptalca_455.py`,
  `tests/app/test_tray_controller.py`
