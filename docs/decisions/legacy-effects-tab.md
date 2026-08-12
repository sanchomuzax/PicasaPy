# ADR-003: „Régi effektek" fül — tudatos eltérés az eredetitől

Dátum: 2026-08-12 · Státusz: ELFOGADVA · jegy: #571

## A helyzet

A Picasa 3.9 motorja **jóval több szűrőt ismer**, mint amennyihez felület
tartozik. A `filterdesc.xml`-ben és a natív regisztrációs táblában ott van
egy sor olyan név (`radtint`, `linblur`, `dir_sat`, `dir_brite`, `dir_sharp`,
`triple`, `colorfix`, `shadow`, `gamma`, `contrast`, `colortemp`, `blur`,
`backlight`, `fill`, `rainbow`, `whitept`, `autocontrast`, `autobacklight`),
amelyet a 3.9 kezelőfelülete **nem mutat**: régebbi verziókból maradtak bent.

A motor egy régi `.picasa.ini`-ből még **elolvassa és alkalmazza** őket — a
felhasználó viszont **nem tudja előhívni**, és ezért **lemérni sem** az
eredeti programban.

## A döntés

**A PicasaPy külön fülön („Régi effektek", a szerkesztő 7. füle) elérhetővé
teszi ezt a készletet.**

Ez az egyetlen pont, ahol **szándékosan eltérünk** a Picasa felületétől: itt
tudatosan **többet** adunk. Egy későbbi „hűségjavítás" ezt a fület **ne
vegye ki** — a fül léte maga is szerződés, teszt őrzi
(`tests/app/qml_functional/test_editor_legacy_tab_571.py`).

A fül nevét a projekt tulajdonosa választotta a jegy két javaslata és egy
harmadik közül: **„Régi effektek"** — a legköznapibb magyar megfogalmazás,
nem programozói szó.

## Miért nem elég a láncot megőrizni

A `filters=` lánc megőrzése ma is bájtra pontos, de:

- a felhasználó **nem látja**, mi van a képén;
- **Mentéskor** (a pixelek beégetésekor) a nem renderelt hatás **véglegesen
  elveszik** — ez a #444 figyelmeztetésének tárgya;
- és nem tudja **kikapcsolni** vagy **átállítani** azt, amit egy régi
  Picasával valaha beállított.

## Hogyan épül fel

1. **A gombok a katalógusból generálódnak**
   (`picasapy.render.legacy_effects.LEGACY_EFFECTS`), nem kézzel a QML-be
   írva. A csúszkák a `filterdesc.xml`-ből származó `FILTER_REGISTRY`-ből
   jönnek (felirat, tartomány, eltolás, log, alapérték) a meglévő
   paraméter-alpanel útján.
2. **Hogy melyik gomb ÉL, azt a renderelő dönti el**
   (`chain.can_render_filter`), nem egy párhuzamosan karbantartott lista.
   Ettől nem lehet aktívnak látszó, de valójában nem ható gomb: egy effekt
   bekötése automatikusan élővé teszi a gombját.
3. **A még megfejtetlen szűrők látszanak, de szürkék.** Ez a jegy explicit
   kérése és a tulajdonos megerősített döntése: egy régi képen ott lehet az
   effekt, és a felhasználónak tudnia kell róla. A buboréksúgó megmondja,
   miért nem használható.
4. **A halott név más magyarázatot kap.** A `focalpixelate` (#567) nem
   „még nincs megfejtve": a Picasa 3.9 natív regiszterében **sincs** hozzá
   feldolgozó, konfigurációs maradvány. A két ok külön szöveget kap.
5. **A `debug` kimarad.** „For debugging" — fejlesztői eszköz volt, nem
   felhasználói effekt.
6. **Ha a megnyitott kép láncában ilyen effekt van, a fül jelzőpontot kap**
   (`EditController.legacyEffectsInChain`), hogy a felhasználó tudja, hol
   nézze meg.

## Ami ettől a fültől független

A fül nem tesz semmit „elérhetővé", aminek nincs modellje: a szürke gombok
akkor válnak élővé, amikor a natív kernelük megfejtése (#568 és utódai)
elkészül. A fül csak a **helyet** adja meg nekik — és addig is a
**láthatóságot**, ami eddig hiányzott.
