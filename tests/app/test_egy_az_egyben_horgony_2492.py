"""#2492: az „1:1" a kép VALÓDI képpont-méretét adja — a horgony őre.

## Miért külön fájl, és miért nem volt elég a meglévő őr

A #2563 a csúszka LEKÉPEZÉSÉT hozta a mértre (0 = illesztés, 0,5 = valódi
méret, 1 = 400 %), és 21 állítással őrzi. Mind a 21 ZÖLD volt — miközben
az „1:1" a valóságban 3–4-szer nagyobbra nagyított a kelleténél.

Mert a leképezés-őrök az `r`-t (a valódi és az illesztett méret arányát)
a FUTÓ kódtól kérdezték, és ahhoz viszonyítottak. Az `r` viszont maga
volt rossz:

```qml
photo.sourceSize.width / photo.paintedWidth     // a régi, hibás alak
...
sourceSize.width: 2560                          // ugyanazon az elemen
```

A Qt olvasáskor a BEÁLLÍTOTT `sourceSize`-t adja vissza, nem a betöltött
kép méretét — a képlet tehát a valódi mérettől függetlenül 2560-cal
számolt.

⇒ **Ez az őr a KIRAJZOLT mérethez köt**: a képernyőn megjelenő szélesség
(a ténylegesen festett szélesség × a nagyítás) a fájl valódi
képpont-szélessége kell legyen. Ezt a rossz `r` nem tudja teljesíteni,
bármilyen szép is a görbe.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer

#: A `qml_app` fixtúra képei (`tests/app/conftest.py`): a.jpg 320 × 160,
#: b.jpg 100 × 100. MINDKETTŐ jóval kisebb a 2560-as `sourceSize`-plafonnál
#: — épp ezért mutatja meg a hibát: a régi képlet 2560-cal számolt volna.
A_KEP_SZELESSEGE = 320
B_KEP_SZELESSEGE = 100


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _hivd(qt_app, obj, nev, *args):
    QMetaObject.invokeMethod(
        obj, nev, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


def _var(qt_app, ms):
    hurok = QEventLoop()
    QTimer.singleShot(ms, hurok.quit)
    hurok.exec()
    qt_app.processEvents()


def _nyisd_meg(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = _child(window, "photoViewer")
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    kep = _child(window, "viewerImage")
    for _ in range(30):
        if kep.property("paintedWidth") > 0:
            return viewer, kep
        _var(qt_app, 100)
    raise AssertionError("a néző képe nem töltődött be")


def _kirajzolt_szelesseg(viewer, kep) -> float:
    """A képernyőn MEGJELENŐ szélesség: a festett szélesség × a nagyítás.

    A `viewerImage` `scale`-je a `viewer.zoomFactor` (`PhotoViewer.qml`),
    tehát ez a tényleges, látható méret — nem újraszámolt képlet."""
    return kep.property("paintedWidth") * viewer.property("zoomFactor")


class TestAzEgyAzEgyben:
    def test_a_kirajzolt_szelesseg_a_VALODI_keppontszam(self, qml_app, qt_app):
        """A tulajdonos jelentésének magja: „az »1:1« nem akkorára nagyít,
        mint az igazi picasa". Az eredeti buboréksúgója szerint az `1to1`
        »Display Photo at actual size« — tehát a kép a saját képpontjaiban
        látszik."""
        window, _controller, _lib, _engine = qml_app
        viewer, kep = _nyisd_meg(window, qt_app, 0)

        _hivd(qt_app, viewer, "zoomActual")

        assert abs(_kirajzolt_szelesseg(viewer, kep) - A_KEP_SZELESSEGE) < 1.0, (
            f"az 1:1 a kép valódi {A_KEP_SZELESSEGE} képpontja helyett "
            f"{_kirajzolt_szelesseg(viewer, kep):.0f}-et rajzol"
        )

    def test_MASIK_kepen_is_a_sajat_merete(self, qml_app, qt_app):
        """⚠️ Ez a próba választja el a javítást a puszta konstans-cserétől:
        ha valaki egy másik FIX számra cserélné a 2560-at, ez bukna."""
        window, _controller, _lib, _engine = qml_app
        viewer, kep = _nyisd_meg(window, qt_app, 1)

        _hivd(qt_app, viewer, "zoomActual")

        assert abs(_kirajzolt_szelesseg(viewer, kep) - B_KEP_SZELESSEGE) < 1.0

    def test_a_400_szazalek_a_valodi_meret_negyszerese(self, qml_app, qt_app):
        """A csúszka jobb vége a MÉRT `4·r` (`0x00a601fb`–`0x00a60221`) —
        tehát a valódi méret négyszerese, nem a plafoné."""
        window, _controller, _lib, _engine = qml_app
        viewer, kep = _nyisd_meg(window, qt_app, 0)

        _hivd(qt_app, viewer, "setZoomValue", 1.0)

        assert abs(
            _kirajzolt_szelesseg(viewer, kep) - 4 * A_KEP_SZELESSEGE
        ) < 4.0

    def test_az_illesztes_NEM_valtozott(self, qml_app, qt_app):
        """⚠️ Regresszió-őr: a bal vég továbbra is a beillesztett méret —
        a javítás nem nyúlhat hozzá."""
        window, _controller, _lib, _engine = qml_app
        viewer, kep = _nyisd_meg(window, qt_app, 0)
        illesztett = kep.property("paintedWidth")

        _hivd(qt_app, viewer, "zoomFit")

        assert viewer.property("zoomFactor") == 1.0
        assert abs(_kirajzolt_szelesseg(viewer, kep) - illesztett) < 0.5


class TestAModellAdja:
    def test_a_modell_SZAM_alakban_adja_a_kepmeretet(self, qml_app, qt_app):
        """A `resolution` szerep formázott sztring (`"320x160"`); a
        nagyításhoz szám kell. QML-ben sztringet szétszedni törékeny —
        ezért van saját slot."""
        window, controller, _lib, _engine = qml_app
        model = controller.property("photos")
        assert model is not None
        assert model.pixelWidthAt(0) == A_KEP_SZELESSEGE
        assert model.pixelHeightAt(0) == 160

    def test_ervenytelen_indexre_NULLA(self, qml_app, qt_app):
        """Nem kivétel és nem kitalált érték: a hívó (a néző) a 0-ra
        tartalék-ágra vált."""
        window, controller, _lib, _engine = qml_app
        model = controller.property("photos")
        assert model.pixelWidthAt(-1) == 0
        assert model.pixelWidthAt(9999) == 0
