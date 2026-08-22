"""A kék sáv több kijelölt képnél a KIJELÖLÉS összesítését mutassa (#1189).

## A tulajdonos jelentése (v0.8.29)

> „Ha kijelölök indexképeket, akkor az alsó kék sávban nem a kiválasztás
> száma és lemezmérete látható."

## Az eredeti — bizonyíték

A sávot a `CThumbUI` `thumbui/infotext` eleme mutatja
(`referencia/tre-eroforrasok/thumbui.tre:683`, középre igazított,
`m_displayfont12`), a tartalmát a **`GetSelectionInfo`** (`0x0056fbc0`)
állítja elő. A függvény ÖT honosított alakot használ
(`referencia/i18n-hu/stringres.xml`):

| kulcs | magyar alak |
|---|---|
| `il_GetSelectionInfo::1` | `Nincs kijelölés` |
| `il_GetSelectionInfo::2` | `%1$s     %2$s     %3$dx%4$d képpont     %5$s` |
| `il_GetSelectionInfo::3` | `%s képek` |
| `il_GetSelectionInfo::4` | `     %1$s-%2$s     %3$s a lemezen` |
| `il_GetSelectionInfo::5` | `     %1$s      %2$s/lemez` |

Valódi Picasa-képernyőképpel megerősítve
(`research/testdata/screenshot/2026-07-17 20 55 20.png`):

```
25 képek     2026. január 2., péntek-2026. május 18., hétfő     37,5 MB a lemezen
```

és egy kép kijelölésekor (ugyanabból a sorozatból):

```
2026-02-19-18-05-05-202.jpg     2026. 02. 20. 3:28:06     1920x1080 képpont     1,4 MB
```

## Nálunk mi volt

A `TrayBar` a sávot háromfelé ágaztatta: néző → `viewerInfo`, PONTOSAN
egy kijelölt → `photoInfo`, **minden más** → `statusText`. A `statusText`
viszont a MAPPA egészének összesítése, nem a kijelölésé — ezért N>1
kijelölésnél a mappa adatai maradtak a sávban.
"""

from pathlib import Path


from support.jpeg_factory import make_jpeg


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _tobb_kepes_mappa(qml_app, qt_app):
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    (lib / "sok").mkdir(exist_ok=True)
    for i in range(5):
        make_jpeg(lib / "sok" / f"k{i}.jpg", size=(120, 90))
    _ujraolvas(controller, qt_app)
    return window, controller


def _sav_szovege(window):
    """A kék sáv MEGJELENÍTETT szövege — a kötésen át, nem a controllerből."""
    for elem in _bejar(window.contentItem()):
        if elem.objectName() == "trayInfoText":
            return str(elem.property("text"))
    raise AssertionError("a kék sáv szövegmezője (trayInfoText) nem található")


def _bejar(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _bejar(gyerek)


def _jelolj(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[-1] if sorok else -1)
    qt_app.processEvents()


class TestKekSav:
    def test_tobb_kijelolesnel_a_kijeloles_osszesitese(self, qml_app, qt_app):
        """⚠️ A jegy magja: eddig a MAPPA összesítése maradt a sávban."""
        window, controller = _tobb_kepes_mappa(qml_app, qt_app)
        osszes = controller.photos.rowCount()
        assert osszes >= 4, "a méréshez legalább négy kép kell"

        _jelolj(window, qt_app, [0, 1])
        szoveg = _sav_szovege(window)

        assert "2" in szoveg, f"a darabszám nem a kijelölésé: {szoveg!r}"
        assert str(osszes) not in szoveg.split()[0], (
            f"a sáv a mappa egészét mutatja: {szoveg!r}"
        )

    def test_a_meret_a_kijelolt_kepeke(self, qml_app, qt_app):
        window, controller = _tobb_kepes_mappa(qml_app, qt_app)
        _jelolj(window, qt_app, [0, 1])
        ketto = _sav_szovege(window)
        _jelolj(window, qt_app, list(range(controller.photos.rowCount())))
        mind = _sav_szovege(window)
        assert ketto != mind, (
            "a kijelölés bővítése nem változtatta a sáv szövegét"
        )

    def test_egy_kijelolesnel_a_kep_adatai(self, qml_app, qt_app):
        """Megőrző: egy kijelöltnél a fájl saját sora marad."""
        window, controller = _tobb_kepes_mappa(qml_app, qt_app)
        _jelolj(window, qt_app, [0])
        szoveg = _sav_szovege(window)
        nev = controller.photos.filePathAt(0).rsplit("/", 1)[-1]
        assert nev in szoveg, f"nem a kép neve látszik: {szoveg!r}"
