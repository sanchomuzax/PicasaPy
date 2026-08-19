"""A gombfelirat FÉRJEN BELE a gombba — magyar fordítással, kirajzolva (#992).

A felhasználó a 0.8.0 Kollázs-panelén látta: a magyar gombfeliratok
kilógnak a gombjukból és ráfolynak a szomszédra. A „Megjelenítés és
szerkesztés" felirat annyira túlért a gombján, hogy a felhasználó a lap
alatti „Véletlenszerű kollázs" gombot nem is találta meg — pedig az ott
volt, csak a ráfolyó szöveg takarta.

## Miért MAGYARUL fut ez a teszt

Az angol feliratok mind beférnek — a `.tre` doboz-méretei angol szövegre
készültek. Angolul tehát ez a teszt SOHA nem bukna el, és pontosan azt a
hibaosztályt hagyná ki, amit a felhasználó lát. Ezért a fájl a magyar
`.qm`-et a QML-motor felállítása ELŐTT telepíti — így a `qsTr()`-kötések
már a magyar szöveggel születnek meg.

## Miért RELATÍV az állítás

A betűméret platformfüggő (ugyanaz a felirat Linuxon és Windowson más
képpontszélességű). Beégetett képpont-küszöb tehát hamis bukást adna a
CI másik lábán. Az állítás ezért mindig két MÉRT érték viszonya:

> a felirat tényleges mérete (`contentWidth`/`contentHeight`)
> ≤ a rendelkezésére álló doboz (`contentItem.width`/`height`)

## Miért KIRAJZOLT

A `PicasaButton` a szélességét a szülőtől kapja (a Kollázs-panel gombjai
`.tre`-ből származó FIX méretűek). Property-t olvasó, komponenst izoláltan
betöltő teszt ezt nem látja. Fejnélküli környezetben ráadásul az
elrendezés késik (#918), ezért minden mérés előtt `_var()` pörgeti az
eseményhurkot határidővel.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Property, QObject, QTranslator, QUrl, Slot
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView

#: Tűrés képpontban. A QML geometriája tört szám lehet (a `Text.Fit`
#: pontosan a doboz széléig nyújtja a feliratot), ezért a fél képpont
#: körüli eltérés nem hiba — ugyanaz a nagyságrend, mint a #656 auditban.
TURES = 1.0

_KEEPALIVE: list[object] = []


@pytest.fixture(scope="module", autouse=True)
def magyar_forditas(qt_app):
    """A magyar `.qm` telepítve, MIELŐTT bármelyik QML-motor felállna.

    Modul-hatókörű és `autouse`: a pytest a tágabb hatókörű fixture-t
    állítja fel előbb, tehát a függvény-hatókörű `qml_app` (ami betölti a
    `Main.qml`-t) már magyar felülettel születik meg."""
    import picasapy.app as app_package

    i18n_dir = Path(app_package.__file__).parent / "i18n"
    translator = QTranslator()
    assert translator.load("picasapy_hu", str(i18n_dir)), (
        f"a picasapy_hu.qm nem tölthető be innen: {i18n_dir}"
    )
    qt_app.installTranslator(translator)
    yield translator
    qt_app.removeTranslator(translator)


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő).

    #918: fejnélküli környezetben az elrendezés késik — egyetlen
    `processEvents()` után a méretek még a kezdeti állapotot mutatják."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _geometria_ujjlenyomat(gyoker: QQuickItem) -> tuple:
    """A gombok és feliratuk MINDEN mérete, egyetlen összehasonlítható alakban.

    Ebből dől el, hogy az elrendezés megállapodott-e. A puszta „létezik már
    gomb" feltétel kevés: a `Text` a saját méretét (és a `Text.Fit`
    betűméretét) a doboz megérkezése UTÁN számolja újra, tehát a korai
    olvasás a tördelés előtti értéket adná vissza."""
    minta = []
    for gomb in _picasa_gombok(gyoker):
        meret = _felirat_doboza(gomb)
        minta.append((gomb.objectName(), gomb.width(), gomb.height(), meret))
    return tuple(minta)


def _var_a_stabil_elrendezesre(qt_app, gyoker: QQuickItem, masodperc: float = 5.0):
    """Vár, amíg a geometria KÉT egymást követő mintában azonos.

    #918 + a #992 Windows-lába: fejnélküli környezetben az elrendezés
    késik, és a késés platformfüggő. Egy „van már gomb" feltétel után
    olvasva a felirat mérete még a tördelés előtti állapotot mutathatja —
    onnantól a teszt akár hamis zöldet, akár hamis bukást adhat."""
    elozo = None
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        mostani = _geometria_ujjlenyomat(gyoker)
        if mostani and mostani == elozo:
            return mostani
        elozo = mostani
        time.sleep(0.02)
    assert elozo, "az elrendezés nem született meg az időkorláton belül"
    return elozo


def _bejar(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `findChild` nem lát mindent (#651)."""
    for child in item.childItems():
        yield child
        yield from _bejar(child)


def _picasa_gombok(gyoker: QQuickItem) -> list[QQuickItem]:
    """Minden LÁTHATÓ, feliratos `PicasaButton` a kirajzolt fából.

    A típusra szűrünk (`PicasaButton_QMLTYPE_…`), mert a jegy tárgya a
    KÖZÖS gombkomponens; az ikonos gombokat a felirat hiánya rostálja ki."""
    talalatok = []
    for item in _bejar(gyoker):
        osztaly = item.metaObject().className()
        if not osztaly.startswith("PicasaButton"):
            continue
        if not item.isVisible() or item.width() <= 0 or item.height() <= 0:
            continue
        if not item.property("text"):
            continue
        talalatok.append(item)
    return talalatok


def _felirat_doboza(gomb: QQuickItem):
    """A felirat tényleges és rendelkezésre álló mérete.

    `None`, ha a gomb tartalma nem szöveg (ikonos gomb `Item`-mel)."""
    tartalom = gomb.property("contentItem")
    if tartalom is None:
        return None
    szeles = tartalom.property("contentWidth")
    magas = tartalom.property("contentHeight")
    if szeles is None or magas is None:
        return None
    return (szeles, magas, tartalom.width(), tartalom.height())


def _tullogasok(gyoker: QQuickItem) -> list[str]:
    """Beszédes lista azokról a gombokról, amelyeknél a felirat kilóg."""
    leletek = []
    for gomb in _picasa_gombok(gyoker):
        meret = _felirat_doboza(gomb)
        if meret is None:
            continue
        szeles, magas, doboz_sz, doboz_m = meret
        vizszintes = szeles - doboz_sz
        fuggoleges = magas - doboz_m
        if vizszintes <= TURES and fuggoleges <= TURES:
            continue
        nev = gomb.objectName() or "<névtelen>"
        leletek.append(
            f"{nev} ({gomb.property('text')!r}): a felirat "
            f"{szeles:.1f}×{magas:.1f}, a hely {doboz_sz:.1f}×{doboz_m:.1f} "
            f"— túllógás {max(vizszintes, 0):.1f}×{max(fuggoleges, 0):.1f} px"
        )
    return leletek


class _KollazsVezerloCsonk(QObject):
    """Annyi a vezérlőből, amennyitől a Kollázs-panel geometriája megszületik.

    Ugyanaz a csonk-alak, mint a #945 méretezési tesztjében: a
    `collagePageRatio` MAGASSÁG / SZÉLESSÉG (spec 8.1), ebből él a lap
    alakja, és ebből származik a lap fölötti/alatti gombsor helye."""

    @Slot()
    def closeCollage(self) -> None:  # a panel Bezárás gombja hívja
        pass

    @Property(float, constant=True)
    def collagePageRatio(self) -> float:
        return 0.75

    @Property(int, constant=True)
    def collageClipCount(self) -> int:
        return 3


def _jelenet(
    qt_app, qml: str, width: int, height: int, *, vezerlo=None
) -> QQuickItem:
    """A megadott QML valódi, kirajzolt ablakban, kivárt elrendezéssel."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    assert [e.toString() for e in component.errors()] == []
    root = component.create()
    assert root is not None
    if vezerlo is not None:
        root.setProperty("controller", vezerlo)
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    view.show()
    _KEEPALIVE.extend((view, root, component, vezerlo))
    # az elrendezés megszületésére VÁRUNK, nem feltételezzük (#918), és nem
    # elég, hogy a gomb létezik: a MÉRETEKNEK kell megállapodniuk
    assert _var(qt_app, lambda: len(_picasa_gombok(root)) > 0), (
        "a jelenetben egyetlen PicasaButton sem rajzolódott ki"
    )
    _var_a_stabil_elrendezesre(qt_app, root)
    return root


#: A Kollázs-panel azon részei, ahol a gombok mérete a `.tre`-ből származó
#: FIX szám — épp ezért itt bukik meg először a hosszabb magyar felirat.
KOLLAZS_JELENET = """
import QtQuick
import PicasaPy 1.0
Item {
    width: 620
    height: 720
    CollageActionRow  { objectName: "akciosor";   x: 0; y: 0 }
    CollageRandomRow  { objectName: "veletlensor"; x: 0; y: 40 }
    CollageSettingsTab { objectName: "beallitasok"; x: 0; y: 80 }
    CollageBackgroundBox { objectName: "hatterdoboz"; x: 300; y: 80 }
}
"""


def test_a_kollazs_panel_gombfeliratai_beleferek_a_gombjukba(qt_app):
    """A jegy tárgya: FIX méretű gomb + hosszú magyar felirat.

    A `.tre` doboz-méretei az ANGOL feliratra készültek; a hivatalos
    magyar szöveg (pl. „Az összes kijelölés megszüntetése" a 100 képpontos
    `select_none` gombon) másfélszer ilyen hosszú. A gomb mérete a spec
    szerint kötött (`kollazs-panel-ui-spec.md` 2.4/2.6), tehát a
    feliratnak kell alkalmazkodnia — TÖRDELÉSSEL, nem néma csonkítással."""
    gyoker = _jelenet(qt_app, KOLLAZS_JELENET, 620, 720)
    gombok = _picasa_gombok(gyoker)
    assert len(gombok) >= 7, (
        f"túl kevés gomb rajzolódott ki ({len(gombok)}) — a jelenet nem áll össze"
    )
    leletek = _tullogasok(gyoker)
    assert not leletek, (
        "magyar gombfelirat lóg ki a gombjából (#992):\n" + "\n".join(leletek)
    )


def test_a_felirat_nem_folyik_a_szomszed_gombra(qt_app):
    """A felhasználó panasza szó szerint: a feliratok EGYMÁSRA csúsznak.

    Nem elég, hogy a szöveg „nagyjából" a helyén van: a kirajzolt felirat
    téglalapja egyetlen MÁSIK gomb dobozába sem érhet bele. A „Véletlen-
    szerű kollázs" gombot pontosan ez tüntette el: a szomszéd gomb túlérő
    felirata takarta ki."""
    gyoker = _jelenet(qt_app, KOLLAZS_JELENET, 620, 720)
    gombok = _picasa_gombok(gyoker)

    def _jelenetben(item: QQuickItem):
        sarok = item.mapToScene(item.boundingRect().topLeft())
        return (sarok.x(), sarok.y(), item.width(), item.height())

    def _felirat_teglalap(gomb: QQuickItem):
        """A KIRAJZOLT felirat téglalapja a jelenet koordinátáiban."""
        tartalom = gomb.property("contentItem")
        szeles = tartalom.property("contentWidth")
        magas = tartalom.property("contentHeight")
        if szeles is None or magas is None:
            return None
        x, y, doboz_sz, doboz_m = _jelenetben(tartalom)
        # a felirat vízszintesen középre, függőlegesen középre zárt
        return (
            x + (doboz_sz - szeles) / 2,
            y + (doboz_m - magas) / 2,
            szeles,
            magas,
        )

    utkozesek = []
    for gomb in gombok:
        felirat = _felirat_teglalap(gomb)
        if felirat is None:
            continue
        fx, fy, fsz, fm = felirat
        for masik in gombok:
            if masik is gomb:
                continue
            mx, my, msz, mm = _jelenetben(masik)
            atfed_x = min(fx + fsz, mx + msz) - max(fx, mx)
            atfed_y = min(fy + fm, my + mm) - max(fy, my)
            if atfed_x > TURES and atfed_y > TURES:
                utkozesek.append(
                    f"{gomb.objectName()} felirata "
                    f"({gomb.property('text')!r}) belelóg ebbe: "
                    f"{masik.objectName()} — átfedés "
                    f"{atfed_x:.1f}×{atfed_y:.1f} px"
                )
    assert not utkozesek, (
        "gombfelirat folyik a szomszéd gombra (#992):\n" + "\n".join(utkozesek)
    )


def test_a_teljes_kollazs_panel_gombfeliratai_beleferek(qt_app):
    """A felhasználó által látott felület EGÉSZBEN, 1280 × 800-as ablakban.

    Az előző teszt a panel darabjait rakja ki; ez a valódi `CollagePanel`-t
    tölti be — így a panel SAJÁT négy alsó gombja (Asztali háttérkép,
    Kollázs létrehozása, Alaphelyzet, Bezárás) is a mérce alá kerül."""
    gyoker = _jelenet(
        qt_app,
        'import QtQuick\nimport PicasaPy 1.0\nCollagePanel { objectName: "panel" }\n',
        1280,
        800,
        vezerlo=_KollazsVezerloCsonk(),
    )
    gombok = _picasa_gombok(gyoker)
    assert len(gombok) >= 10, (
        f"túl kevés gomb rajzolódott ki ({len(gombok)}) — a panel nem áll össze"
    )
    leletek = _tullogasok(gyoker)
    assert not leletek, (
        "magyar gombfelirat lóg ki a gombjából a Kollázs-panelen (#992):\n"
        + "\n".join(leletek)
    )


def test_az_egesz_alkalmazas_gombfeliratai_beleferek(qt_app, qml_app):
    """Széles seprés: a fő ablak MINDEN látható `PicasaButton`-ja.

    A `PicasaButton` sok tucat helyen használt közös komponens — az
    eszköztárban, a fiókokban, a párbeszédekben. A jegy javítása ott is
    hat, ezért az őr ott is néz."""
    window, _controller, _engine = qml_app
    # a `QQuickWindow` maga nem `Item` — a vizuális fa a `contentItem` alatt van
    gyoker = window.contentItem()
    assert _var(qt_app, lambda: len(_picasa_gombok(gyoker)) > 0), (
        "a fő ablakban egyetlen PicasaButton sem rajzolódott ki"
    )
    _var_a_stabil_elrendezesre(qt_app, gyoker)
    leletek = _tullogasok(gyoker)
    assert not leletek, (
        "magyar gombfelirat lóg ki a gombjából a fő ablakban (#992):\n"
        + "\n".join(leletek)
    )


def test_a_felirat_megkapja_a_gomb_teljes_magassagat(qt_app):
    """A tördeléshez HELY kell — és azt egyetlen stílus se vehesse el.

    A `padding` a QtQuick Controlsban csak TARTALÉK érték: ha a beállított
    stílus a maga `Button`-jában explicit `verticalPadding`-et ad, az
    erősebb nála. A Windows natív stílusa pontosan ezt teszi, ezért a
    komponens első változatában a `padding: 0` ott nem érvényesült: a
    26 képpontos gombból 16 maradt a feliratnak, a két sor nem fért el, és
    a felhasználó megint kilógó szöveget látott volna.

    Linuxon egyik stílus sem csinálja ezt, tehát a hiba helyben
    LÁTHATATLAN volt — a PR Windows-lába fogta meg. Ez az őr a
    következményt méri, platformfüggetlenül: a felirat doboza a gomb
    TELJES magassága legyen."""
    qml = """
import QtQuick
import PicasaPy 1.0
Item {
    width: 300
    height: 100
    PicasaButton {
        objectName: "fixmeretu"
        x: 10; y: 10; width: 100; height: 26
        text: "Az összes kijelölés megszüntetése"
    }
}
"""
    gyoker = _jelenet(qt_app, qml, 300, 100)
    gomb = _picasa_gombok(gyoker)[0]
    tartalom = gomb.property("contentItem")
    assert tartalom.height() >= gomb.height() - TURES, (
        f"a felirat doboza csak {tartalom.height():.1f} képpont magas a "
        f"{gomb.height():.1f} képpontos gombon — a függőleges kitöltést "
        "elvette valami (a stílus explicit `verticalPadding`-je erősebb a "
        "gyűjtő `padding`-nél; `topPadding`/`bottomPadding` kell)"
    )
    # …és a felirat tényleg tördel, nem egyetlen csonka sor
    assert tartalom.property("lineCount") >= 2, (
        "a 33 karakteres magyar felirat egyetlen sorban maradt a 100 "
        "képpontos gombon — nem tördel"
    )


def test_a_tartalomhoz_igazodo_gomb_merete_nem_zsugorodott(qt_app):
    """Regresszió-őr: a javítás NEM szűkítheti az egész alkalmazás gombjait.

    A javítás a felirat körüli belső margót csökkenti, hogy a fix méretű
    gomboknak legyen hova tördelni. Ez azonban nem apaszthatja el azokat a
    gombokat, amelyek a TARTALMUKHOZ igazodnak (nincs rájuk `width`) —
    azok mérete és levegője maradjon a régi."""
    qml = """
import QtQuick
import PicasaPy 1.0
Item {
    width: 400
    height: 120
    PicasaButton { objectName: "sajatmeretu"; x: 10; y: 10; text: "Eltávolítás" }
}
"""
    gyoker = _jelenet(qt_app, qml, 400, 120)
    gomb = _picasa_gombok(gyoker)[0]
    szeles, magas, _doboz_sz, _doboz_m = _felirat_doboza(gomb)
    # a korábbi kitöltés 10 + 10 vízszintesen és 6 + 6 függőlegesen volt
    assert gomb.width() - szeles >= 20.0 - TURES, (
        f"a gomb elszűkült: {gomb.width():.1f} széles a {szeles:.1f} képpontos "
        "felirathoz — a vízszintes levegő 20 képpont volt"
    )
    assert gomb.height() - magas >= 12.0 - TURES, (
        f"a gomb ellaposodott: {gomb.height():.1f} magas a {magas:.1f} képpontos "
        "felirathoz — a függőleges levegő 12 képpont volt"
    )
