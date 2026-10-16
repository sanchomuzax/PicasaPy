"""#4846 — a szerkesztő fülikonjainak rajza az eredeti iránya és formája.

Referencia: az eredeti Picasa 3.9 képernyőképe (`research/testdata/screenshot/
2026-07-17 20 56 36.png`): a csavarkulcs feje BAL FENT, az ecset sörtéje BAL
LENT, a nap korongjának jobb fele üres, a 4–5. fül ikonja zöld/kék tájképes
négyzet bal fent + az ecset jobb lent.

A próba a RENDERELT ablakképen (`grabWindow`) méri a festett képpontok
tömegének eloszlását az ikon negyedeiben — nem property-t olvas. A szomszéd
(méret, hely, szél) a #4552 tesztjében marad.
"""


import pytest
from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtQuick import QQuickView

_QML = """
import QtQuick
import PicasaPy 1.0
Rectangle {
    width: 276; height: 40; color: "#ffffff"
    QtObject {
        id: stub
        property int activeTab: 99
        property bool legacyEffectsPresent: false
        function selectTab(i) { activeTab = i }
    }
    EditorTabBar { objectName: "bar"; panel: stub; width: 276; y: 5 }
}
"""

KUSZOB = 60  # a három csatorna összegében


@pytest.fixture
def sav(qt_app, tmp_path):
    import picasapy.app.application as app_module

    qml = tmp_path / "fulikon_4846.qml"
    qml.write_text(_QML, encoding="utf-8")
    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Status.Ready, view.errors()
    view.resize(276, 40)
    view.show()
    for _ in range(30):
        qt_app.processEvents()
    yield view
    view.close()
    view.deleteLater()


class _Ikon:
    """Az ikon renderelt képe: festett-e egy képpont, és negyedenkénti tömeg."""

    def __init__(self, view, qt_app, nev):
        for _ in range(30):
            qt_app.processEvents()
        self.kep = view.grabWindow()
        obj = view.rootObject().findChild(QObject, nev + "Icon")
        assert obj is not None, nev
        p = obj.mapToScene(QPointF(0, 0))
        self.x0, self.y0 = round(p.x()), round(p.y())
        self.w, self.h = round(obj.width()), round(obj.height())
        self.hatter = self.kep.pixelColor(self.x0 - 3, self.y0 - 3)

    def szin(self, x, y):
        return self.kep.pixelColor(self.x0 + x, self.y0 + y)

    def festett(self, x, y):
        c, b = self.szin(x, y), self.hatter
        return (abs(c.red() - b.red()) + abs(c.green() - b.green())
                + abs(c.blue() - b.blue())) > KUSZOB

    def tomeg(self, xa, xb, ya, yb):
        return sum(self.festett(x, y) for x in range(xa, xb)
                   for y in range(ya, yb))

    def negyedek(self):
        mx, my = self.w // 2, self.h // 2
        return {
            "bf": self.tomeg(0, mx, 0, my), "jf": self.tomeg(mx, self.w, 0, my),
            "bl": self.tomeg(0, mx, my, self.h),
            "jl": self.tomeg(mx, self.w, my, self.h),
        }


def test_a_csavarkulcs_feje_bal_fent_van(sav, qt_app):
    n = _Ikon(sav, qt_app, "editTabFixes").negyedek()
    assert n["bf"] > n["jf"], n
    assert n["bf"] > n["bl"], n
    # a nyél a jobb alsó negyedbe ér
    assert n["jl"] > 0, n


def test_a_csavarkulcs_fejen_a_nyel_tengelyen_kerek_u_res_van(sav, qt_app):
    ikon = _Ikon(sav, qt_app, "editTabFixes")
    # a fej középpontja a tervezési doboz (4,7; 4,7) pontja; a rés a nyél
    # tengelye mentén (225°, bal-felfelé) 2–3 képpontra a középponttól üres
    for t in (2, 3):
        x = round(4.7 - t * 0.7071)
        assert not ikon.festett(x, x), (t, x)
    # a két pofa a rés két oldalán festett: balra és felfelé a középponttól
    assert ikon.festett(1, 4), "bal pofa (185°, 3 px)"
    assert ikon.festett(4, 1), "felső pofa (265°, 3 px)"


def test_az_ecset_sortéje_bal_lent_van(sav, qt_app):
    n = _Ikon(sav, qt_app, "editTabEffects").negyedek()
    assert n["bl"] > n["bf"], n
    assert n["bl"] > n["jl"], n
    # a nyél a jobb felső negyedbe ér
    assert n["jf"] > 0, n


def test_a_nap_korongjanak_jobb_fele_ures(sav, qt_app):
    ikon = _Ikon(sav, qt_app, "editTabFinetune")
    cx, cy = ikon.w // 2, ikon.h // 2
    # a korong belseje: a bal fele kitöltött, a jobb fele üres (az eredeti)
    assert ikon.festett(cx - 2, cy), "a korong bal fele kitöltött"
    assert not ikon.festett(cx + 2, cy), "a korong jobb fele üres"
    assert not ikon.festett(cx + 2, cy - 1)
    assert not ikon.festett(cx + 2, cy + 1)


@pytest.mark.parametrize("nev,csatorna", (
    ("editTabEffects2", "green"),
    ("editTabEffects3", "blue"),
))
def test_a_4_es_5_ful_tajkepes_negyzet_plusz_ecset(sav, qt_app, nev, csatorna):
    ikon = _Ikon(sav, qt_app, nev)
    # a négyzet bal fent: a színcsatorna a vörös fölött áll
    c = ikon.szin(3, ikon.h // 2 - 2)
    if csatorna == "green":
        assert c.green() > c.red() + 20 and c.green() > c.blue() + 20, c.name()
    else:
        assert c.blue() > c.red() + 40, c.name()
    # a jobb fent (a négyzeten kívül) csak az ecset nyele: sötét
    n = ikon.negyedek()
    assert n["bf"] > n["jf"], n
    # az ecset a jobb alsó negyedben sötét (nem színes)
    sotet = sum(
        1 for x in range(ikon.w // 2, ikon.w) for y in range(ikon.h // 2, ikon.h)
        if (lambda q: q.red() < 90 and q.green() < 90 and q.blue() < 90)(
            ikon.szin(x, y)))
    assert sotet >= 8, sotet
