"""A #864 hisztogram-algoritmus KIRAJZOLT, képpontos regressziótesztje.

Nem belső property-t vagy a rajzolás elindulását ellenőrizzük: valódi
``QQuickView`` képernyőképéből olvassuk vissza azt a négy képpontszínt,
amelyet a visszafejtett ``+85`` RGBA-keverés előír.

## A HÁTTÉR a képlet BEMENETE (#2625)

Az orákulum eredetileg **fehér** hátteret égetett bele, és a négy
konstansa (``#555555``, ``#aaaa55``, ``#ffaaaa``, ``#ffffff``) ennek az
egy esetnek felelt meg. A #2625 kimérte, hogy az eredeti Picasa
rajzterületének **nincs saját háttere** (a `respack.yt`
``nerdview/rect: histoback`` tömör kitöltése BGRA(0,0,0,0), és a
tulajdonos felvételén a rajzterület üres része 232 — pontosan annyi, mint
a panelé). Amikor a `HistogramBox` háttere átlátszóvá vált, ez a fájl
elbukott — és a bukás értéke (``#a1a14c``) **pontosan az volt, amit a
képlet előír**:

    eredmény = 85 · aktív + háttér · (1 − 85 · aktívDarab / 255)

228-as háttérrel, két aktív csatornával: 85 + 228/3 = **161 = 0xa1**, a
harmadik csatorna 76 = **0x4c**. ⇒ **nem ellentmondás volt, hanem
hiányzó paraméter.**

⚠️ Amit ez NEM tesz: nem hangolja hozzá az őrt a képernyőképhez. A
binárisból visszafejtett rész — a csatornánkénti **+85** járulék és a
premultiplied összegzés — VÁLTOZATLAN; csak a háttér lett paraméter. A
``test_a_feher_hatteru_eset_valtozatlan`` ezt őrzi: 255-tel behelyettesítve
a képlet ma is a négy eredeti konstansot adja.
"""

from __future__ import annotations

import math
import time

import pytest

from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

_KEEPALIVE: list[object] = []


def _var_a_kirajzolasra(view: QQuickView, qt_app, masodperc: float = 10.0) -> bool:
    """Megvárja, amíg a kirajzolt kép MEGÁLLAPODIK — a fix beállás UTÁN.

    #1463: itt korábban CSAK egy fix `for _ in range(5): processEvents();
    QTest.qWait(20)` állt — 100 ezredmásodpercnyi fogadás arra, hogy
    addigra a QML-kötések, a tördelés és a rajzolás mind lefutottak.
    Terhelt, négymagos futón ez kevés lehet, és a képpontos állítás
    hamis pirosat ad.

    ⚠️ A fix beállást NEM lehetett elhagyni. Mérve (2026-08-25, 6+6
    futás): ha csak a „két egymást követő azonos `grabWindow()`"
    feltételre vártunk, a poll TÚL KORÁN állt meg — két egyforma, még
    nem kész felvétel is azonos —, és a
    `test_additive_rgba_mix_is_visible_in_rendered_pixels` 6 futásból
    1-szer elbukott, miközben az eredeti változat 6/6-ot ment. A
    fali-óra tehát itt PADLÓ, nem plafon:

    1. előbb a régi, fix beállás (változatlan alsó korlát),
    2. utána — és csak utána — a felvétel-stabilitásra várunk, bőkezű
       határidővel.

    Így a teszt sosem indul korábban, mint eddig, terhelt gépen viszont
    tovább tud várni. A padló + kiterjesztés alakkal 8 futásból 8 zöld.

    Az őr foga változatlan: ha a kép sosem áll be, a határidő lejár, a
    hívó ugyanúgy elolvassa a képpontokat, és a képpontos állítás bukik.
    Mutációval igazolva: a `HistogramBitmap.qml` additív keverésének
    elrontása (`case 7: "#555555"` → `"#112233"`) pirosra váltja.

    ⚠️ Aki ezt „feleslegesen bonyolultnak" látja és visszaegyszerűsíti
    puszta pollozásra, a fenti 1/6-os bukást hozza vissza.
    """
    # 1. a régi, fix beállás — alsó korlát, nem szinkronpont
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)

    # 2. bőkezű hosszabbítás: két egymást követő azonos felvétel
    elozo = None
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        mostani = view.grabWindow()
        if elozo is not None and mostani == elozo:
            return True
        elozo = mostani
        time.sleep(0.01)
    qt_app.processEvents()
    return False


def _histogram_box(qt_app, histogram=None) -> tuple[QQuickView, QQuickItem]:
    """A valódi ``HistogramBox`` 238 × 144-es ablakban kirajzolva."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(
        view.engine(),
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "HistogramBox.qml")
        ),
    )
    assert [error.toString() for error in component.errors()] == []

    # Alulról 20 px-ig R+G+B, 40 px-ig R+G, 60 px-ig csak R.
    # Minden bin azonos, így a 256→213 kicsinyítés vízszintesen homogén.
    if histogram is None:
        histogram = {
            "r": [60 / 70] * 256,
            "g": [40 / 70] * 256,
            "b": [20 / 70] * 256,
        }
    root = component.createWithInitialProperties(
        {"histogramData": histogram, "cameraSummary": "Gép\t1/125 s"}
    )
    assert root is not None
    root.setWidth(238)
    root.setHeight(144)
    root.setParentItem(view.contentItem())
    view.resize(238, 144)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)

    _KEEPALIVE.extend((view, root, component))
    return view, root


def _histogram_bitmap(qt_app) -> tuple[QQuickView, QQuickItem]:
    """A 256 × 70-es belső kép önállóan, fehér háttér előtt."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.setColor(QColor("white"))
    component = QQmlComponent(
        view.engine(),
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "HistogramBitmap.qml")
        ),
    )
    assert [error.toString() for error in component.errors()] == []
    histogram = {
        "r": [60 / 70] * 256,
        "g": [40 / 70] * 256,
        "b": [20 / 70] * 256,
    }
    root = component.createWithInitialProperties({"histogramData": histogram})
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(256, 70)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)
    _KEEPALIVE.extend((view, root, component))
    return view, root


def _pixel_at_fraction_from_bottom(
    image, plot: QQuickItem, fraction: float
) -> QColor:
    """A rajzterület közepén, az aljától mért aránynál vett képpont."""
    point = plot.mapToScene(
        QPointF(plot.width() / 2, plot.height() * (1.0 - fraction))
    ).toPoint()
    return image.pixelColor(point.x(), point.y())


def _assert_rgb(actual: QColor, expected: str) -> None:
    """Legfeljebb egy szintnyi renderelői kerekítést enged."""
    target = QColor(expected)
    assert max(
        abs(actual.red() - target.red()),
        abs(actual.green() - target.green()),
        abs(actual.blue() - target.blue()),
    ) <= 1, f"várt {target.name()}, kapott {actual.name()}"


#: A csatornánkénti járulék — ez a BINÁRISBÓL visszafejtett rész (#864).
JARULEK = 85

#: A `HistogramBitmap` önálló próbája fehér vászonra rajzol (`setColor`).
FEHER_HATTER = 255


def _kevert(active, hatter: int) -> QColor:
    """A `+85`-ös premultiplied keverés `hatter` színű alapon.

    A puffer a nulláról indul, és minden aktív csatorna `JARULEK`-et ad
    hozzá — ezzel együtt `JARULEK` alfát is. A maradék alfán a HÁTTÉR
    látszik át:

        eredmény = JARULEK · aktív + háttér · (1 − JARULEK · darab / 255)

    `hatter = 255` mellett ez pontosan a #864 eredeti négy konstansa.
    """
    darab = sum(active)
    marad = hatter * (1.0 - JARULEK * darab / 255.0)
    return QColor(*(round(JARULEK * int(e) + marad) for e in active))


def _doboz_hattere(image, root) -> int:
    """A DOBOZ háttere a kirajzolt képen — a rajzterület fölötti sávból.

    Nem beégetett szám: a téma változhat, és a #2625 épp azt állítja, hogy
    a rajzterület EZT a színt viszi. A mintát a doboz bal szélén vesszük,
    a rajzterület fölött — ott sem szöveg, sem görbe nincs.
    """
    szin = image.pixelColor(4, 12)
    assert szin.red() == szin.green() == szin.blue(), (
        f"a doboz háttere nem semleges szürke: {szin.name()}"
    )
    return szin.red()


def _valtozo_binek() -> tuple[dict[str, list[float]], dict[str, list[int]]]:
    """Minden binben eltérő, egész belső magasságú tesztmintát ad."""
    heights = {
        "r": [(index * 13 + 3) % 71 for index in range(256)],
        "g": [(index * 29 + 11) % 71 for index in range(256)],
        "b": [(index * 47 + 23) % 71 for index in range(256)],
    }
    return (
        {
            channel: [height / 70 for height in channel_heights]
            for channel, channel_heights in heights.items()
        },
        heights,
    )


def _vart_kijelzo_szin(
    heights: dict[str, list[int]], x: int, y: int, hatter: int = FEHER_HATTER
) -> QColor:
    """Független orákulum a 256 × 70 → 213 × 59 legközelebbi mintához."""
    # A legközelebbi texel középpontos leképezése; pontos félúton a kisebb
    # index nyer, ezért ``ceil(...)-1`` és nem a Python bankárkerekítése.
    source_x = min(255, math.ceil((x + 0.5) * 256 / 213) - 1)
    source_y = min(69, math.ceil((y + 0.5) * 70 / 59) - 1)
    bottom_y = 69 - source_y
    active = tuple(heights[channel][source_x] > bottom_y for channel in "rgb")
    return _kevert(active, hatter)


def test_additive_rgba_mix_is_visible_in_rendered_pixels(qt_app):
    """A +85-ös szorzott-alfa keverés négy tartománya képpontos."""
    view, root = _histogram_box(qt_app)
    plot = root.findChild(QObject, "histogramPlot")
    assert isinstance(plot, QQuickItem)
    image = view.grabWindow()

    # #2625: a háttér MÉRT, nem beégetett — a rajzterületnek nincs saját
    # kitöltése, a doboz színe látszik át. A négy tartomány színe ebből és
    # a bináris `+85` járulékból SZÁMÍTOTT.
    hatter = _doboz_hattere(image, root)
    esetek = (
        (10 / 70, (True, True, True)),
        (30 / 70, (True, True, False)),
        (50 / 70, (True, False, False)),
        (65 / 70, (False, False, False)),
    )
    vartak = [_kevert(aktiv, hatter) for _, aktiv in esetek]
    assert len({szin.name() for szin in vartak}) == 4, (
        f"a négy tartomány nem különbözik ({[s.name() for s in vartak]}) — "
        "az állítás vákuumban menne át"
    )
    for (fraction, _aktiv), vart in zip(esetek, vartak, strict=True):
        _assert_rgb(
            _pixel_at_fraction_from_bottom(image, plot, fraction), vart.name()
        )


def test_a_rajzterulet_URES_resze_a_DOBOZ_szine(qt_app):
    """#2625 — KIRAJZOLT képpontokon: a rajzterületnek nincs saját háttere.

    A testvérfájl (`test_histogram.py`) a `color` tulajdonságot nézi; az
    viszont nem mondja meg, mi látszik a KÉPERNYŐN (egy fölé rajzolt réteg
    vagy egy opacity-kötés némán felülírhatná). Ez a próba a doboz
    hátterét és a rajzterület ÜRES részét ugyanabból a felvételből olvassa
    ki, és azt állítja, hogy a kettő EGYEZIK.

    A mérés forrása: `respack.yt` → `nerdview/rect: histoback` tömör
    kitöltése BGRA(0,0,0,0), és a tulajdonos A/B felvétele (232 == 232).
    """
    view, root = _histogram_box(qt_app)
    plot = root.findChild(QObject, "histogramPlot")
    assert isinstance(plot, QQuickItem)
    image = view.grabWindow()

    hatter = _doboz_hattere(image, root)
    # a görbék alulról nőnek; a felső sáv (65/70) mindenütt üres
    ures = _pixel_at_fraction_from_bottom(image, plot, 65 / 70)
    assert max(
        abs(ures.red() - hatter),
        abs(ures.green() - hatter),
        abs(ures.blue() - hatter),
    ) <= 1, (
        f"a rajzterület üres része {ures.name()}, a doboz háttere "
        f"RGB({hatter},{hatter},{hatter}) — a kettőnek egyeznie kell"
    )


def test_az_EXIF_szoveg_tintaja_NEM_ut_at_a_rajzteruletre(qt_app):
    """#2625/#2648 — a 2 képpontos átfedés nem engedhet át idegen tintát.

    A #1344 mérése szerint az EXIF-terület teteje (82) 2 képponttal a
    hisztogram alja (84) fölé ér, és a döntés az, hogy **a plot rajzolódik
    a szöveg fölött**. Amikor a #2625 első változata a rajzterületet
    `"transparent"`-re vitte, ez a takarás megszűnt, és a windows-lábon az
    EXIF-szöveg tintája átütött:

        (24, 57): várt #a04ba0, kapott #5e095d
        (159, 57): várt #4ba0a0, kapott #095e5d

    A kapott értékek pontosan a `_kevert` képlet ~27-es (sötét betű)
    háttérrel — vagyis nem rajzolási hiba volt, hanem a HÁTTÉR cserélődött
    ki egyetlen képpontra.

    Ez a próba magas, ékezetes nagybetűkkel tölti fel az EXIF-sávot (a
    legmagasabb tinta, ami a felső 2 képpontba érhet), és a rajzterület
    ALSÓ két sorát méri: minden képpontnak a hisztogram képletét kell
    követnie, idegen tinta nélkül.

    ⚠️ **Ez a próba a WINDOWS-láb őre.** Linuxon MÉRTEN nem reprodukálja a
    hibát: az alapbetű tintája ott nem ér fel a 2 képpontos sávba, ezért
    `"transparent"` mellett is zöld marad (kipróbálva). Egy őr, ami csak az
    egyik platformon fog, önmagában kevés — ezért áll mellette a
    `test_a_rajzterulet_hattere_ATLATSZATLAN`, ami a takarás FELTÉTELÉT
    méri, platformfüggetlenül.
    """
    magas = "ÁÉÍÓŐÚŰ\tÁÉÍÓŐÚŰ\nÁÉÍÓŐÚŰ\tÁÉÍÓŐÚŰ"
    view = QQuickView()
    import picasapy.app.application as app_module

    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(
        view.engine(),
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "HistogramBox.qml")
        ),
    )
    assert [hiba.toString() for hiba in component.errors()] == []
    root = component.createWithInitialProperties(
        {
            "histogramData": {
                "r": [60 / 70] * 256,
                "g": [40 / 70] * 256,
                "b": [20 / 70] * 256,
            },
            "cameraSummary": magas,
        }
    )
    assert root is not None
    root.setWidth(238)
    root.setHeight(144)
    root.setParentItem(view.contentItem())
    view.resize(238, 144)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)
    _KEEPALIVE.extend((view, root, component))

    plot = root.findChild(QObject, "histogramPlot")
    assert isinstance(plot, QQuickItem)
    image = view.grabWindow()
    hatter = _doboz_hattere(image, root)
    origin = plot.mapToScene(QPointF(0, 0))

    # az alsó két sor: ott mind a három csatorna aktív (a görbék alulról nőnek)
    vart = _kevert((True, True, True), hatter)
    idegen: list[str] = []
    for y in (57, 58):
        for x in range(213):
            szin = image.pixelColor(round(origin.x() + x), round(origin.y() + y))
            if max(
                abs(szin.red() - vart.red()),
                abs(szin.green() - vart.green()),
                abs(szin.blue() - vart.blue()),
            ) > 1:
                idegen.append(f"({x}, {y}): {szin.name()} != {vart.name()}")
    assert not idegen, (
        "idegen tinta a rajzterület alsó soraiban — az EXIF-szöveg átüt "
        "a rajzterületen:\n" + "\n".join(idegen[:10])
    )


def test_a_rajzterulet_hattere_ATLATSZATLAN(qt_app):
    """#2648 — a takarás FELTÉTELE, platformfüggetlenül.

    A #1344 döntése: „a plot a szöveg FÖLÖTT rajzolódik; a 2 képpontos
    átfedés megmarad, csak a takarás iránya rögzített." Takarni viszont
    csak ÁTLÁTSZATLAN kitöltéssel lehet — a `"transparent"` (alfa 0)
    átengedi az EXIF-szöveg tintáját, és a windows-lábon meg is tette
    (#2648: `(24, 57)` és `(159, 57)`).

    Ugyanakkor a #2625 mérése szerint a rajzterületnek **a doboz színét**
    kell mutatnia. A kettő együtt: átlátszatlan, és a doboz színe.
    """
    _view, root = _histogram_box(qt_app)
    hatter = root.findChild(QObject, "histogramPlotBackground")
    doboz_szine = QColor(root.property("color"))
    plot_szine = QColor(hatter.property("color"))
    assert plot_szine.alpha() == 255, (
        "a rajzterület háttere nem átlátszatlan — így nem takarja el az "
        f"alatta futó EXIF-szöveget (alfa {plot_szine.alpha()})"
    )
    assert plot_szine == doboz_szine, (
        f"a rajzterület nem a doboz színét viszi ({plot_szine.name()} vs "
        f"{doboz_szine.name()})"
    )


def test_a_feher_hatteru_eset_valtozatlan():
    """#2625 — a háttér paraméterré tétele nem mozdítja a #864 orákulumát.

    Ez a próba a KÉPLETET méri, nem a képernyőt: 255-ös háttérrel a
    `_kevert` ma is pontosan azt a négy konstansot adja, amit a #864
    visszafejtett. Ha valaki a `JARULEK`-hez vagy az összegzéshez nyúl, ez
    bukik — akkor is, ha közben a képernyő „szépen néz ki".
    """
    vart = {
        (True, True, True): "#555555",
        (True, True, False): "#aaaa55",
        (True, False, False): "#ffaaaa",
        (False, False, False): "#ffffff",
    }
    for aktiv, szin in vart.items():
        assert _kevert(aktiv, FEHER_HATTER).name() == szin, (
            f"{aktiv}: {_kevert(aktiv, FEHER_HATTER).name()} != {szin}"
        )


def test_internal_bitmap_matches_binary_spec_pixel_for_pixel(qt_app):
    """A teljes belső kép egyezik a binárisból levezetett referenciával."""
    view, _ = _histogram_bitmap(qt_app)
    image = view.grabWindow()

    # A várt kép nem a termékkód képletét hívja: közvetlenül a visszafejtett
    # +85 RGBA-konstansok fehér háttérre kompozitált eredményét rögzíti.
    expected_rows = (
        (range(0, 10), "#ffffff"),
        (range(10, 30), "#ffaaaa"),
        (range(30, 50), "#aaaa55"),
        (range(50, 70), "#555555"),
    )
    for rows, expected in expected_rows:
        for y in rows:
            for x in range(256):
                _assert_rgb(image.pixelColor(x, y), expected)


def test_internal_and_display_geometry_is_exact(qt_app):
    """A 256 × 70-es kép a 213 × 59-es rajzterületre kerül."""
    _, root = _histogram_box(qt_app)
    plot = root.findChild(QObject, "histogramPlot")
    bitmap = root.findChild(QObject, "histogramBitmap")
    assert isinstance(plot, QQuickItem)
    assert isinstance(bitmap, QQuickItem)
    assert (plot.width(), plot.height()) == (213, 59)
    assert (bitmap.width(), bitmap.height()) == (256, 70)


def test_final_213x59_output_scales_every_varying_bin(qt_app):
    """A végső plot minden képpontja független skálázási orákulumot követ."""
    histogram, heights = _valtozo_binek()
    view, root = _histogram_box(qt_app, histogram)
    plot = root.findChild(QObject, "histogramPlot")
    assert isinstance(plot, QQuickItem)
    image = view.grabWindow()
    origin = plot.mapToScene(QPointF(0, 0))
    # #2625: a háttér MÉRT — a rajzterületnek nincs saját kitöltése.
    hatter = _doboz_hattere(image, root)

    mismatches: list[str] = []
    for y in range(59):
        for x in range(213):
            actual = image.pixelColor(round(origin.x() + x), round(origin.y() + y))
            expected = _vart_kijelzo_szin(heights, x, y, hatter)
            if max(
                abs(actual.red() - expected.red()),
                abs(actual.green() - expected.green()),
                abs(actual.blue() - expected.blue()),
            ) > 1:
                mismatches.append(
                    f"({x}, {y}): várt {expected.name()}, kapott {actual.name()}"
                )
    assert not mismatches, (
        f"A 213 × 59-es kirajzolás eltér (origó: {origin.x()}, {origin.y()}):\n"
        + "\n".join(mismatches[:20])
    )


def test_real_photo_viewer_histogram_panel_geometry(qml_app, qt_app):
    """A Mainből nyitott PhotoViewer hisztogrampaneljének éles geometriája.

    #1323: a panel a bal fiókON BELÜL dokkolt — a fiók BAL szélétől 20 px-re
    —, nem a fiók jobb pereme mellett, a képterület fölött lebegve. Az
    ``editpanel.tre`` ``LEFTDRAWEROFFSET``-je a fiók be-/kicsúsztatását
    vezérlő változó (0 ↔ −279), nem a fiók szélessége.
    """
    window, _, _ = qml_app
    window.setProperty("viewerOpen", True)

    # #1463: itt korábban fix `for _ in range(5): processEvents();
    # QTest.qWait(20)` állt — 100 ezredmásodpercnyi fogadás arra, hogy a
    # néző és a bal fiók addigra felépül és a helyére kerül. Helyette a
    # VALÓDI feltételre várunk: legyen meg mind a négy elem, és a mért
    # geometriájuk álljon be (két egymást követő azonos minta). Ha ez
    # sosem következik be, a határidő lejár, és az alábbi állítások
    # ugyanúgy elbuknak — az őr foga változatlan.
    def _ujjlenyomat():
        elemek = [
            window.findChild(QObject, nev)
            for nev in ("photoViewer", "viewerLeftDrawer", "viewerHistogramBox", "histogramTitle")
        ]
        if not all(isinstance(item, QQuickItem) for item in elemek):
            return None
        doboz, felirat = elemek[2], elemek[3]
        return (
            doboz.width(),
            doboz.height(),
            doboz.mapToScene(doboz.boundingRect().topLeft()).x(),
            felirat.height(),
        )

    _elozo = None
    _hatarido = time.monotonic() + 10.0
    while time.monotonic() < _hatarido:
        qt_app.processEvents()
        _mostani = _ujjlenyomat()
        if _mostani is not None and _mostani == _elozo:
            break
        _elozo = _mostani
        time.sleep(0.01)

    viewer = window.findChild(QObject, "photoViewer")
    drawer = window.findChild(QObject, "viewerLeftDrawer")
    box = window.findChild(QObject, "viewerHistogramBox")
    title = window.findChild(QObject, "histogramTitle")
    assert all(isinstance(item, QQuickItem) for item in (viewer, drawer, box, title))

    assert (box.width(), box.height()) == (238, 144)
    drawer_left = drawer.mapToScene(drawer.boundingRect().topLeft()).x()
    drawer_right = drawer.mapToScene(drawer.boundingRect().topRight()).x()
    box_left = box.mapToScene(box.boundingRect().topLeft()).x()
    box_right = box.mapToScene(box.boundingRect().topRight()).x()
    viewer_bottom = viewer.mapToScene(viewer.boundingRect().bottomLeft()).y()
    box_bottom = box.mapToScene(box.boundingRect().bottomLeft()).y()
    assert box_left == pytest.approx(drawer_left + 20, abs=0.5)
    # #1905/3: a −95 az `editpanel.tre` `nerdview_container`
    # `YConstraint 1, 1, -95` sorából jött, DE annak a szülője `root`,
    # nem a bal fiók — a fiók aljára alkalmazva 95 px üres sáv maradt
    # alatta. A tulajdonos egymás mellé tett felvételén (Picasa 3 vs
    # PicasaPy, azonos mappa) MÉRVE: az eredetiben a doboz alsó
    # szegélye y=921, a panel alja y=925 — 4 px. A felvétel erősebb
    # bizonyíték, mint a mi olvasatunk a kényszerről.
    assert box_bottom == pytest.approx(viewer_bottom - 4, abs=0.5)
    # a doboz NEM lóghat ki a fiókból a képterületre
    assert box_right <= drawer_right + 0.5
    # #1344: a felirat NEM félkövér, és a mért 11 képpontos sormagasságot
    # kapja (a korábbi `pointSize: 14` + félkövér a mi kitalálásunk volt —
    # a `nerdview.tre`-ben SEMMI nem jelöl félkövéret).
    assert title.property("font").bold() is False
    assert title.height() == 11
