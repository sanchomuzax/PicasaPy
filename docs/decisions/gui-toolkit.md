# ADR-001: GUI toolkit = PySide6 (Qt 6)

Dátum: 2026-07-16 · Státusz: ELFOGADVA · research-plan #1 lezárva

## Döntés

A PicasaPy GUI-ja **PySide6 (Qt 6)** alapon készül: a képrács és a néző
**QML** (GPU-gyorsított GridView, aszinkron képbetöltés), natív ablakkeret.

## A mérés

Három jelölt, azonos thumbnail-rács demó (5000 elem, valódi fotók, RPi5,
Wayland/labwc, Raspberry Connect-en át értékelve):
`tools/benchmarks/gui/{qml_grid,gtk_grid,dpg_grid}.py` + `run_bench.sh`.

| Jelölt | Indulás→ablak | Felhasználói értékelés |
|---|---|---|
| PySide6/QML GridView | 0,36 s | jó, sima |
| GTK4 GridView | 0,36 s | jó, sima — érzésre azonos a QML-lel |
| Dear PyGui | 3,47 s | **legrosszabb** |

- **Dear PyGui kiesett:** nincs virtualizált listája — mind a 981 egyedi
  textúrát előre kellett tölteni (2,95 s); 140k képes könyvtárnál ez a
  megközelítés eleve alkalmatlan. Ráadásul egyszer import-segfaultot is
  produkált (aarch64 wheel, egyszeri, memórianyomás gyanú).
- **QML ≈ GTK4:** a VNC-átvitel (Raspberry Connect) korlátozza az érzékelhető
  különbséget; helyi kijelzőn lehetne differenciáltabb, de a döntést nem ez
  viszi el (ld. lentebb).

## Miért a PySide6 (a GTK4-gyel szembeni holtversenyből)

1. **Keresztplatform-terv (2. rögzített döntés):** Qt-vel a Windows/macOS port
   gyakorlatilag ingyen van (hivatalos wheelek mindhárom platformra, egységes
   viselkedés). A PyGObject/GTK4 Windows/macOS alatt fájdalmas (MSYS2,
   csomagolási nehézségek, idegen kinézet).
2. **Szerkesztő-pipeline (2. fázis):** a Qt RHI/QML custom material +
   QRhi/OpenGL integráció kiforrott út a GPU-s shader-lánchoz; GTK4-ben a
   GtkGLArea + a listakezelés összeházasítása több kézimunka.
3. **Telepítés RPi5-ön:** hivatalos aarch64 pip wheel (6.11) ÉS Debian-csomag
   (6.8) is van — CI-ban és felhasználóknál is egyszerű.
4. **Licenc:** PySide6 = LGPL-3 → kompatibilis a projekt GPL-3.0 licencével.
5. A NotebookLM-forrásanyag ajánlása is Qt/QML volt a Picasa-szerű, gyors,
   billentyűzet-vezérelt UI-hoz.

## Következmények

- Tech stack rögzítve: Python 3.12+ / PySide6 / QML frontend.
- A thumbnail-rács referencia-implementációja a `qml_grid.py` demóból nő ki
  (aszinkron Image, cacheBuffer, sourceSize — már most 5000 elemet visz).
- A GTK4 demó megmarad a repóban összehasonlítási alapnak.
- Kockázat (elfogadva): a QML-hez QML-tudás kell; a Widgets-fallback
  (QListView + delegate) bármikor nyitva áll ugyanabban a lib-ben.
