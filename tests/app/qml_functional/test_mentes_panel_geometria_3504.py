"""#3504 — a mentés-panel a VALÓDI magasságán, angolul ÉS magyarul: semmi
nem lóg ki, és a mappalista legalább három sort mutat.

## Miért kell ez az őr

Az átnézés (#3673) egy offscreen renderelt képen látta, hogy a „Select
All/None" gombok fele lelóg a panel aljáról, a magyar „Az összes
kijelölés megszüntetése" jobbra is kilóg a 2. lépés keretéből, a
mappalista másfél sort mutat, és a fejlécek csonkok. A régi tesztek ezt
nem látták: a közös kiszolgáló `root.setHeight(250)`-je FELÜLÍRTA a gazda
`height` kötését, tehát a tesztek egy magasabb, nem létező panelt néztek.

Ez a fájl ezért a gazdát a SAJÁT magasságán rendereli (a kiszolgáló nem
nyúl hozzá), és minden látható vezérlőre kimondja:

* a gazda jobb/alsó élén belül marad;
* a lépés-keretben lévő vezérlő a saját MÉRT keretében marad
  (`backuprect` 128,37 311×166 · `backuprect2` 448,37 324×166);
* egyetlen látható felirat sem csonk (`truncated`) és nem nagyobb a
  dobozánál — a gombok feliratai is.

⚠️ A mért geometriát a `respack.yt` rétegfejlécei adják
(`docs/specs/ajandek-cd-kimenet.md` 13.3, `biztonsagi-mentes.md` 14.1);
a 2. lépés `backuptext2`, `selectall`, `selectnone` sorai ugyanonnan
(ld. a `PublishPanel.qml` megjegyzéseit).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QPointF, QCoreApplication, QMetaObject, QTranslator
from PySide6.QtQml import QQmlExpression, QQmlProperty
from PySide6.QtQuick import QQuickItem

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre

_QML = Path(picasapy.app.__file__).parent / "qml"
_I18N = _QML.parent / "i18n"

#: a mért lépés-keretek (`respack.yt`): x, y, szélesség, magasság
_BACKUPRECT = (128, 37, 311, 166)
_BACKUPRECT2 = (448, 37, 324, 166)

#: a két keret vezérlői — ezeknek a SAJÁT keretükben kell maradniuk
_ELSO_LEPES = (
    "publishBackupCdHeader", "publishBackupText", "publishLabelBackupName",
    "publishBackupSetMenu", "publishNewBackupSet", "publishEditBackupSet",
    "publishDeleteBackupSet",
)
_MASODIK_LEPES = (
    "publishBackupCdHeader2", "publishBackupText2", "publishBackupText3",
    "publishBackupSelectAll", "publishBackupSelectNone",
)

_MAPPAK = ("alfa", "beta", "gamma", "delta", "epszilon")


@pytest.fixture(params=["en", "hu"])
def gazda(request, qt_app, tmp_path, monkeypatch):
    fordito = None
    if request.param == "hu":
        fordito = QTranslator()
        assert fordito.load("picasapy_hu", str(_I18N))
        QCoreApplication.installTranslator(fordito)
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    for mappa in _MAPPAK:
        (gyoker / mappa).mkdir(parents=True)
        make_jpeg(gyoker / mappa / "a.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    vezerlo = BackupController(db, (str(gyoker),))
    # KÉT készlet: a törlés gombja csak így látszik (spec 15.3/2)
    vezerlo.ujKeszlet("Külső meghajtó", str(tmp_path / "cel"), "minden",
                      "lemez")
    vezerlo.ujKeszlet("Második", str(tmp_path / "cel2"), "minden", "lemez")
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(ablak, "nyisd")
    ablak.setProperty("kivalasztott", 0)
    assert varj_feltetelre(
        qt_app, lambda: ablak.property("mappakToltodnek") is False)
    qt_app.processEvents()
    yield view, ablak
    view.hide()
    if fordito is not None:
        QCoreApplication.removeTranslator(fordito)


def _elem(gyoker, nev: str) -> QQuickItem:
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _teglalap(elem: QQuickItem, viszony: QQuickItem):
    # az elem SAJÁT geometriája: a `Text` boundingRect-je a kirajzolt
    # szöveghez igazodik (középre zárásnál eltolt), a szélessége viszont
    # az elemé — a kettő keverése betűkészlettől függő hamis kilógást adott
    bal_felso = elem.mapToItem(viszony, QPointF(0, 0))
    return (bal_felso.x(), bal_felso.y(), elem.width(), elem.height())


def _latszik(elem: QQuickItem) -> bool:
    return elem.isVisible() and elem.width() > 0 and elem.height() > 0


def _bejaras(gyoker: QQuickItem, *, vagasnal_megall: bool):
    """A látható vizuális fa. `vagasnal_megall`: a `clip`-es elem belsejébe
    nem megy le (ami ott kilóg, azt a vágás elrejti — nem hiba)."""
    verem = [gyoker]
    while verem:
        elem = verem.pop()
        if not elem.isVisible():
            continue
        yield elem
        if vagasnal_megall and elem.clip() and elem is not gyoker:
            continue
        verem.extend(elem.childItems())


def _benne(belso, kulso, turesz: float = 0.5) -> bool:
    bx, by, bw, bh = belso
    kx, ky, kw, kh = kulso
    return (bx >= kx - turesz and by >= ky - turesz
            and bx + bw <= kx + kw + turesz and by + bh <= ky + kh + turesz)


def _kozepen_rovidulhet(elem: QQuickItem, engine) -> bool:
    """Az elem `elide` tulajdonsága `Text.ElideMiddle`, ÉS a betűmérete már
    elérte a `minimumPixelSize`-t (tehát a `fontSizeMode: Text.HorizontalFit`
    előbb kicsinyített, és csak ezután, végső esetben rövidít). Az `elide`
    a `QQuickText::TextElideMode` C++ enum, amit sem `QObject.property`, sem
    `QQmlProperty.read` nem tud Python-értékre alakítani ("Can't find
    converter for 'QQuickText::TextElideMode'") — ezért JS-kifejezésként,
    `QQmlExpression`-nel kérdezzük le."""
    ctx = engine.contextForObject(elem)
    kifejezes = QQmlExpression(ctx, elem, "elide === Text.ElideMiddle")
    elide_kozepen, _ = kifejezes.evaluate()
    if not elide_kozepen:
        return False
    minimum = elem.property("minimumPixelSize")
    if not minimum:
        return False
    betumeret = QQmlProperty(elem, "font.pixelSize").read()
    return betumeret <= minimum


class TestAKiszolgaloNemIrjaFelul:
    def test_a_gazda_a_sajat_magassagan_all(self, gazda):
        view, ablak = gazda
        panel = _elem(ablak, "publishPanel")
        assert panel.height() == 212, "a mért vászon 1024 × 212"
        # a gazda magassága a SAJÁT kötéséből jön, a nézet ehhez igazodik
        assert ablak.height() >= panel.height()
        assert view.height() == round(ablak.height())


class TestSemmiNemLogKi:
    def test_minden_lathato_elem_a_gazda_jobb_es_also_elen_belul(
        self, gazda
    ):
        _, ablak = gazda
        doboz = (0, 0, ablak.width(), ablak.height())
        kilogok = [
            (e.objectName() or type(e).__name__, _teglalap(e, ablak))
            for e in _bejaras(ablak, vagasnal_megall=True)
            if e is not ablak and _latszik(e)
            and not _benne(_teglalap(e, ablak), doboz)
        ]
        assert not kilogok, kilogok

    @pytest.mark.parametrize("nevek, keret", [
        (_ELSO_LEPES, _BACKUPRECT),
        (_MASODIK_LEPES, _BACKUPRECT2),
    ])
    def test_a_lepes_vezerloi_a_mert_keretukben(self, gazda, nevek, keret):
        _, ablak = gazda
        panel = _elem(ablak, "publishPanel")
        kilogok = []
        for nev in nevek:
            elem = _elem(ablak, nev)
            assert _latszik(elem), f"{nev} nem látszik"
            # a vezérlő MINDEN látható része (pl. a gomb felirata is)
            for resz in _bejaras(elem, vagasnal_megall=True):
                if _latszik(resz) and not _benne(_teglalap(resz, panel),
                                                 keret):
                    kilogok.append((nev, resz.objectName()
                                    or type(resz).__name__,
                                    _teglalap(resz, panel)))
        assert not kilogok, kilogok

    def test_egyetlen_lathato_felirat_sem_csonk(self, gazda):
        view, ablak = gazda
        engine = view.engine()
        lista = _elem(ablak, "publishBackupFolderList")
        csonkok = []
        for elem in _bejaras(ablak, vagasnal_megall=False):
            if not _latszik(elem) or elem.property("truncated") is None:
                continue
            if elem.property("text") in (None, ""):
                continue
            # a mappalista fájlnév-sora szándékosan elidál (sok fájlnév)
            os_ = elem.parentItem()
            listaban = False
            while os_ is not None:
                if os_ is lista:
                    listaban = True
                    break
                os_ = os_.parentItem()
            if listaban:
                continue
            tul_szeles = elem.property("contentWidth") > elem.width() + 1
            tul_magas = elem.property("contentHeight") > elem.height() + 1
            # #3696: a `publishBackupInfo` a célutat FUTÁSIDŐBEN kapja
            # (`PublishPanel.qml`, `elide: Text.ElideMiddle`), és
            # SZÁNDÉKOSAN közepén rövidül, ha még a legkisebb betűméretnél
            # sem fér el (a Windows-CI mélyen ágyazott ideiglenes útjainál
            # ez a normális eset — a mappalista sorának fájlnév-elidálásához
            # hasonlóan, ld. fentebb). A `truncated` zászló ilyenkor NEM
            # hiba — a doboznál nagyobbra nyúlás viszont igen: azt a
            # `tul_szeles`/`tul_magas` továbbra is elkapja. A kivétel csak
            # azokra az elemekre él, amelyek TÉNYLEG `Text.ElideMiddle`-lel
            # vannak felcímkézve, ÉS már elérték a `minimumPixelSize`-t.
            kozepen_rovidulhet = _kozepen_rovidulhet(elem, engine)
            csonk = tul_szeles or tul_magas or (
                elem.property("truncated") and not kozepen_rovidulhet
            )
            if csonk:
                csonkok.append((elem.property("text"),
                                elem.property("contentWidth"), elem.width(),
                                elem.property("contentHeight"),
                                elem.height()))
        assert not csonkok, csonkok


class TestAMappalista:
    def test_legalabb_harom_sort_mutat(self, gazda, qt_app):
        _, ablak = gazda
        lista = _elem(ablak, "publishBackupFolderList")
        sorok = [
            e for e in _bejaras(lista, vagasnal_megall=False)
            if e.objectName() == "publishBackupFolderCheck" and _latszik(e)
        ]
        # a `ListView` csak a látványban lévő sorokat építi meg — öt
        # mappából legalább háromnak TELJESEN látszania kell
        assert len(sorok) >= 3
        teljesen_lathato = [
            s for s in sorok
            if _benne(_teglalap(s, lista), (0, 0, lista.width(),
                                             lista.height()))
        ]
        assert len(teljesen_lathato) >= 3, (
            len(teljesen_lathato), lista.height())
