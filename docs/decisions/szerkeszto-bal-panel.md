# Döntés: a szerkesztő bal panelje

**Állapot:** eldöntve · **Dátum:** 2026-08-15 · **Döntő:** a tulajdonos

## A döntés

1. **A felület PONTOSAN úgy nézzen ki, mint az eredeti Picasa.** Ez az
   alapértelmezés minden elrendezési, méret-, térköz- és viselkedéskérdésre.
   Ahol a kutatás megadja az eredeti mért geometriáját
   ([`../specs/ui-audit-editor.md`](../specs/ui-audit-editor.md) 2.9), azt
   kell követni.

   Ebből következően a szerkesztő felső sávjában **szerkesztés közben csak a
   „Vissza a könyvtárhoz" gomb látszik** — az Importálás gomb és a kereső
   nem. Az eredetiben a szerkesztő felső 40 képpontos sávjában egyetlen elem
   van (`editpanel/albumview`, 122 × 22 px).

2. **A fülsávban HÉT fül marad**, az eredeti öt helyett. Ez **tudatos
   kivétel** az 1. pont alól: nem vesztünk el funkciót az egységes kinézetért.
   A fülek ennek megfelelően keskenyebbek lesznek (55 px helyett ~39 px).

## ⛔ Ezt a két kérdést NEM kell újra feltenni

Mindkettő eldőlt. Ha egy jövőbeli kör elrendezési kérdésbe fut, a válasz az
1. pont — kérdés nélkül. A fülszámot pedig egyáltalán ne hozza fel.

## Indoklás

A projekt célja a Picasa **teljes újraírása**, és a felhasználó a régi
programot napi szinten használja: a megszokott elrendezés nem kozmetika,
hanem a használhatóság része. A fülszám azért kivétel, mert ott a hűség
funkcióvesztéssel járna (a „Régi effektek" fül és a negyedik effekt-fül
tartalma máshová szorulna).

## A végrehajtandó méretek

A döntés 1. pontjának teljes, kötelező számlistája:
[`../specs/szerkeszto-panel-meretek.md`](../specs/szerkeszto-panel-meretek.md).
Ott van levezetve a 2. pont (hét fül) számszerű következménye is:
39 · 39 · 40 · 39 · 40 · 39 · 40 = 276 képpont.

## Következmények

- A bal panel tartalom-oszlopa **276 px**, a fülsáv **25 px** magas.
- Az 1. fül eszközcsempéi **44 × 30 px**, oszlopköz **81**, sorköz **64**.
- A Derítőfény ikonja szintén 44 × 30, a rács első oszlopával azonos x-en.
- A Visszavonás / Újra gomb **132 × 28 px**.
- A 3–5. effekt-fül rácsa (csempe 86 px, osztásköz 88 × 71) **már helyes**.

A javítás jegye: **#741**. A mérés forrása a `respack.yt` rétegtéglalapjai —
nem képernyőkép.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/qml/PicasaPy/EditorPanel.qml`
  (a 276 képpontos tartalom-oszlop és a 132 × 28-as gombpár),
  `src/picasapy/app/qml/PicasaPy/EditorTabBar.qml` (a 25 képpontos
  fülsáv és a hét fül), `src/picasapy/app/qml/PicasaPy/ToolTile.qml`
  (a 44 × 30-as eszközcsempe), `src/picasapy/app/qml/Main.qml`
  (a döntésből következő legkisebb ablakszélesség, #641)
- **Őrzi:** `tests/app/qml_functional/test_editor_panel_geometry_741.py`
