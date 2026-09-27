"""#3741: kettős nézetben a FÓKUSZBAN lévő fél viszi a nagyítást, a
pásztázást, a forgatást, az arc-átfedőt és az eszközök képarányát.

„ab" módban a bal fél (`viewerImageElotte`) a `currentIndex` fotóját, a
jobb (`viewerImage`) az `abMasikSor`-ét mutatja (#3773). Bal fókusznál a
KIJELÖLT kép a bal — a szerkesztő, az eszközátfedő és minden, ami a
képhez tartozik, ide kell kerüljön.

A próbák a KIRAJZOLT képpontokat nézik (`grabWindow`), nem csak a
geometriát: a tulajdonos szava szerint „a tesztednek látnia kellett volna,
nem csak kiszámolnia".

A próbaképek szándékosan eltérő arányúak és egyszínűek, egy sarokjellel:
- `a.jpg` 640×400, zöld;
- `b.jpg` 300×500, narancs, a bal FELSŐ sarkában kék jellel.
A jel helyéből látszik, hogy a forgatás ténylegesen kirajzolódik-e.

#3773: a próbák a B képet („jelölt", forgatható, arcos próbakép) akarják a
BAL oldalon látni, a `_ab_modba` helyi csomagolója ezért a belépés után a
`currentIndex`-et a B sorára állítja (a 2 fotós mappában ettől az
`abMasikSor` — `hasNext()` hiányában visszafelé lépve — az A sorára esik).
Ez a bal=B / jobb=A párosítás a `_bal_fokusz`/`_jobb_fokusz` segédekkel
mindkét fókusz-irányban elérhető — tartalomban változatlan a #3773 előtti
próbákhoz képest, csak a fókusz eléréséhez szükséges kattintás fordult meg
(az alapfókusz mostantól a bal)."""

from __future__ import annotations

import configparser

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_fokuszvaltas_johagyasa_3693 import (
    _eszkozt_nyit_kattintva,
    _nyitva,
)
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _ab_modba as _ab_modba_alap,
    _elem_teglalap,
    _gyerek,
    _kep_teglalap,
    _klikk,
)

#: RGB — a JPEG-tömörítés miatt a próbák tűréssel hasonlítanak
ZOLD = (60, 160, 60)
NARANCS = (230, 120, 40)
KEK = (40, 60, 220)

def _kepek(lib, *, b_forgatva=False) -> None:
    a = np.full((400, 640, 3), ZOLD[::-1], np.uint8)
    b = np.full((500, 300, 3), NARANCS[::-1], np.uint8)
    b[0:100, 0:100] = KEK[::-1]
    cv2.imwrite(str(lib / "a.jpg"), a, [cv2.IMWRITE_JPEG_QUALITY, 98])
    cv2.imwrite(str(lib / "b.jpg"), b, [cv2.IMWRITE_JPEG_QUALITY, 98])
    ini = (
        "[a.jpg]\n"
        "faces=rect64(1000100050005000),ffffffffffffffff\n"
        "[b.jpg]\n"
        "faces=rect64(80006000c000a000),ffffffffffffffff\n"
    )
    if b_forgatva:
        ini += "rotate=rotate(1)\n"
    (lib / ".picasa.ini").write_text(ini, encoding="utf-8")


@pytest.fixture
def ket_kep(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek)


@pytest.fixture
def ket_kep_b_forgatva(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path,
        kepeket_keszit=lambda lib: _kepek(lib, b_forgatva=True),
    )


# -- segédek ---------------------------------------------------------------


def _ab_modba(window, qt_app, *, meret=(1280, 1024)):
    """#3773: a bal a `currentIndex`-et mutatja — a `currentIndex`-et a B
    (jelölt próbakép) sorára állítjuk, hogy a bal=B / jobb=A párosítás a
    #3773 előtti próbákkal megegyezzen (ld. a modul docstringjét)."""
    nezo = _ab_modba_alap(window, qt_app, meret=meret)
    nezo.setProperty("currentIndex", 1)
    qt_app.processEvents()
    return nezo


def _bal_fokusz(window, qt_app):
    """#3773: az alapfókusz a bal — nincs szükség váltásra."""
    nezo = _ab_modba(window, qt_app)
    assert nezo.property("aktivOldal") == "bal"
    return nezo


def _jobb_fokusz(window, qt_app):
    nezo = _ab_modba(window, qt_app)
    _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
    assert nezo.property("aktivOldal") == "jobb"
    return nezo


def _kep(window, qt_app):
    for _ in range(10):
        qt_app.processEvents()
    QTest.qWait(200)
    return window.grabWindow()


def _szin(kep, x, y):
    c = kep.pixelColor(int(round(x)), int(round(y)))
    return (c.red(), c.green(), c.blue())


def _kozel(szin, cel, tures=40) -> bool:
    return all(abs(a - b) <= tures for a, b in zip(szin, cel, strict=True))


def _feher(szin) -> bool:
    return all(c >= 235 for c in szin)


def _sotetebb(szin, eredeti, arany=0.75) -> bool:
    return sum(szin) < arany * sum(eredeti)


def _relativ_pont(r, rx, ry):
    return (r["bal"] + rx * (r["jobb"] - r["bal"]),
            r["fent"] + ry * (r["lent"] - r["fent"]))


def _vagas_kattintva(window, qt_app, teglalap=None):
    """A Vágás VALÓDI kattintással nyílik (#3693 mintája), majd a
    kijelölés a próbához ismert helyre kerül."""
    if teglalap is None:
        teglalap = QRectF(0.2, 0.2, 0.6, 0.6)
    panel = _eszkozt_nyit_kattintva(window, qt_app, "editToolCrop", "cropActive")
    overlay = _gyerek(window, "cropOverlay")
    overlay.setProperty("cropRect", teglalap)
    overlay.setProperty("hasSelection", True)
    qt_app.processEvents()
    return panel, overlay


def _fogantyu_kozep(overlay, rx, ry):
    """A kijelölés (rx, ry) relatív pontja jelenet-koordinátában — a
    `mapToScene` a nagyítást és a forgatást is követi."""
    p = overlay.mapToScene(QPointF(rx * overlay.property("width"),
                                   ry * overlay.property("height")))
    return p.x(), p.y()


def _felek(window):
    return (_kep_teglalap(_gyerek(window, "viewerImageElotte")),
            _kep_teglalap(_gyerek(window, "viewerImage")))


def _ini_szakasz(tmp_path, nev) -> str:
    ini = configparser.ConfigParser(interpolation=None, strict=False)
    ini.optionxform = str
    ini.read(tmp_path / "kepek" / ".picasa.ini", encoding="utf-8")
    return ini.get(nev, "faces", fallback="")


# -- 1. arc-átfedő ------------------------------------------------------------


class TestFrissBelepesLapozasNelkul:
    """#3773: a friss belépés — lapozás és kattintás NÉLKÜL. A fenti
    `_ab_modba` csomagoló belépés után lapoz, ami a belépéskori hibát
    elfedte (a bal fél a helykitöltőt mutatta, amíg valami újra nem
    töltötte). Itt a bal az A (zöld, 640×400, `currentIndex`), a jobb a B
    (narancs)."""

    def test_a_bal_fel_a_jelenlegi_kepet_rajzolja_ki(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _ab_modba_alap(window, qt_app)
        assert nezo.property("aktivOldal") == "bal"
        kep = _kep(window, qt_app)
        bal, jobb = _felek(window)

        bal_kozep = _szin(kep, (bal["bal"] + bal["jobb"]) / 2,
                          (bal["fent"] + bal["lent"]) / 2)
        jobb_kozep = _szin(kep, (jobb["bal"] + jobb["jobb"]) / 2,
                           (jobb["fent"] + jobb["lent"]) / 2)
        assert _kozel(bal_kozep, ZOLD), bal_kozep
        assert _kozel(jobb_kozep, NARANCS), jobb_kozep
        szel = bal["jobb"] - bal["bal"]
        mag = bal["lent"] - bal["fent"]
        assert szel / mag == pytest.approx(640 / 400, abs=0.02), (szel, mag)

    def test_a_szerkeszto_a_bal_kep_aranyat_kapja(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        _ab_modba_alap(window, qt_app)
        panel = _gyerek(window, "viewerEditorPanel")
        assert panel.property("imageAspect") == pytest.approx(640 / 400, abs=0.01)


class TestAzArcAtfedoAKijeloltKepetMutatja:
    """Bal fókusznál a bal (B) kép arcai látszanak, és az arcszerkesztés a
    B fájl sorába ír — nem a jobb oldali A-éba."""

    def test_bal_fokusznal_a_b_arcait_mutatja_a_b_kepen(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("facesVisible", True)
        qt_app.processEvents()
        atfedo = _gyerek(window, "facesOverlay")

        assert atfedo.property("imagePath").endswith("b.jpg")
        arcok = atfedo.property("faces")
        assert len(arcok) == 1
        # B arca a kép közepén (0,5…0,375), A-é a bal felső negyedben
        assert arcok[0]["left"] == pytest.approx(0.5, abs=0.01)
        bal_r, _jobb_r = _felek(window)
        atfedo_r = _elem_teglalap(atfedo)
        for kulcs in ("bal", "fent", "jobb", "lent"):
            assert abs(atfedo_r[kulcs] - bal_r[kulcs]) <= 1.0

    def test_jobb_fokusznal_az_a_arcai_valtozatlanul(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _jobb_fokusz(window, qt_app)
        nezo.setProperty("facesVisible", True)
        qt_app.processEvents()
        atfedo = _gyerek(window, "facesOverlay")
        assert atfedo.property("imagePath").endswith("a.jpg")
        assert atfedo.property("faces")[0]["left"] == pytest.approx(
            1 / 16, abs=0.01)

    def test_bal_fokusznal_az_uj_arc_a_b_fajlba_irodik(
        self, ket_kep, qt_app, tmp_path
    ):
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        a_elotte = _ini_szakasz(tmp_path, "a.jpg")
        nezo.setProperty("facesEditMode", True)
        nezo.setProperty("facesVisible", True)
        qt_app.processEvents()
        atfedo = _gyerek(window, "facesOverlay")

        from tests.app.qml_functional.test_viewer_faces_edit import _invoke
        _invoke(atfedo, "openEditorFor", 0.05, 0.05, 0.2, 0.2, "", True)
        qt_app.processEvents()
        _gyerek(window, "faceNameField").setProperty("text", "Béla")
        _invoke(atfedo, "commitEditor")
        qt_app.processEvents()

        assert _ini_szakasz(tmp_path, "a.jpg") == a_elotte, (
            "az új arc a MÁSIK (nem kijelölt) kép sorába került"
        )
        assert _ini_szakasz(tmp_path, "b.jpg").count("rect64(") == 2
        assert len(atfedo.property("faces")) == 2

    def test_bal_fokusznal_az_atnevezes_a_b_fajlba_irodik(
        self, ket_kep, qt_app, tmp_path
    ):
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        a_elotte = _ini_szakasz(tmp_path, "a.jpg")
        nezo.setProperty("facesEditMode", True)
        nezo.setProperty("facesVisible", True)
        qt_app.processEvents()
        atfedo = _gyerek(window, "facesOverlay")
        arc = atfedo.property("faces")[0]

        from tests.app.qml_functional.test_viewer_faces_edit import _invoke
        _invoke(atfedo, "openEditorFor", arc["left"], arc["top"],
                arc["right"], arc["bottom"], "", False)
        qt_app.processEvents()
        _gyerek(window, "faceNameField").setProperty("text", "Kis Éva")
        _invoke(atfedo, "commitEditor")
        qt_app.processEvents()

        assert _ini_szakasz(tmp_path, "a.jpg") == a_elotte
        b_sor = _ini_szakasz(tmp_path, "b.jpg")
        assert "ffffffffffffffff" not in b_sor, "a B arca nem kapott nevet"
        assert atfedo.property("faces")[0]["name"] == "Kis Éva"

    def test_a_kirajzolt_arckeret_a_b_kepen_all(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("facesVisible", True)
        kep = _kep(window, qt_app)
        bal_r, jobb_r = _felek(window)
        # B arcának bal éle a B kép 0,5-énél (középmagasságban, 0,45)
        x, y = _relativ_pont(bal_r, 0.5, 0.45)
        keret_a_b_en = any(
            not _kozel(_szin(kep, x + dx, y), NARANCS) for dx in (-1, 0, 1)
        )
        assert keret_a_b_en, "a B kép arckerete nem rajzolódott ki"
        # az A arcának helye (1/16) a JOBB képen üres zöld maradt
        x, y = _relativ_pont(jobb_r, 1 / 16, 0.2)
        assert all(_kozel(_szin(kep, x + dx, y), ZOLD) for dx in (-1, 0, 1))


# -- 2. nagyítás, pásztázás, forgatás ------------------------------------------


class TestANagyitasAFokuszbanLevoFelen:
    def test_bal_fokusznal_a_bal_kep_nagyul_a_jobb_nem(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.7)
        qt_app.processEvents()
        # a B (300 képpont széles) valódi mérete kisebb a kirajzoltnál,
        # tehát a 0,7-es állás nála ~1,1-szeres
        assert _gyerek(window, "viewerImageElotte").property("scale") > 1.05
        assert _gyerek(window, "viewerImage").property("scale") == 1.0

    def test_jobb_fokusznal_a_jobb_kep_nagyul_a_bal_nem(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _jobb_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.7)
        qt_app.processEvents()
        assert _gyerek(window, "viewerImage").property("scale") > 1.5
        assert _gyerek(window, "viewerImageElotte").property("scale") == 1.0

    def test_a_valodi_meret_a_kijelolt_kep_kepponjait_adja(
        self, ket_kep, qt_app
    ):
        """1:1 bal fókusznál: a B (300 képpont széles) kép kirajzolt
        szélessége 300 képpont — nem az A 640-es szélességéből számolt."""
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.5)
        qt_app.processEvents()
        bal = _gyerek(window, "viewerImageElotte")
        szel = bal.property("paintedWidth") * bal.property("scale")
        assert szel == pytest.approx(300, abs=1.5)

    def test_nagyitva_a_bal_kep_nem_log_at_a_jobbra(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        _bal_elotte, jobb_r = _felek(window)
        nezo.setProperty("zoomValue", 0.8)
        kep = _kep(window, qt_app)
        # a jobb kép TELJES szélességében zöld marad (a bal kép nem takarja)
        for rx in (0.01, 0.1, 0.5, 0.9):
            x, y = _relativ_pont(jobb_r, rx, 0.5)
            assert _kozel(_szin(kep, x, y), ZOLD), (
                f"a jobb kép {rx:.2f}-es pontját a nagyított bal kép takarja: "
                f"{_szin(kep, x, y)}"
            )

    def test_nagyitva_a_jobb_kep_nem_log_at_a_balra(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _jobb_fokusz(window, qt_app)
        bal_r, _jobb = _felek(window)
        nezo.setProperty("zoomValue", 0.8)
        kep = _kep(window, qt_app)
        for rx in (0.5, 0.9, 0.99):
            x, y = _relativ_pont(bal_r, rx, 0.5)
            assert _kozel(_szin(kep, x, y), NARANCS), (
                f"a bal kép {rx:.2f}-es pontját a nagyított jobb kép takarja"
            )

    def test_a_pasztazas_a_bal_kepet_mozgatja(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.8)
        qt_app.processEvents()
        bal = _gyerek(window, "viewerImageElotte")
        jobb = _gyerek(window, "viewerImage")
        bal_elotte = bal.mapToScene(QPointF(0, 0))
        jobb_elotte = jobb.mapToScene(QPointF(0, 0))
        nezo.setProperty("panX", 5000.0)
        from tests.app.qml_functional.test_viewer_faces_edit import _invoke
        _invoke(nezo, "clampPan")
        qt_app.processEvents()
        assert bal.mapToScene(QPointF(0, 0)).x() > bal_elotte.x() + 10
        assert jobb.mapToScene(QPointF(0, 0)) == jobb_elotte
        # a pásztázás határa a bal fél: a kép bal éle nem jön be a félbe
        bal_kepe = _kep_teglalap(bal)
        keret = _elem_teglalap(_gyerek(window, "viewerImageElotteKeret"))
        # (`_kep_teglalap` bal éle a `mapToScene` miatt már a nagyított)
        szel = bal.property("paintedWidth") * bal.property("scale")
        assert szel > keret["jobb"] - keret["bal"]
        assert bal_kepe["bal"] == pytest.approx(keret["bal"], abs=1.0)


class TestAForgatasAFelekenKirajzolva:
    def test_a_nem_kijelolt_bal_kep_a_sajat_forgatasaval_latszik(
        self, ket_kep_b_forgatva, qt_app
    ):
        """Jobb fókusz: a bal (B, `rotate(1)`) kép 90°-kal elforgatva — a
        kék sarokjel a bal FELSŐ sarokból a jobb FELSŐ-be kerül."""
        window, _c, _e = ket_kep_b_forgatva
        _jobb_fokusz(window, qt_app)
        kep = _kep(window, qt_app)
        bal_r = _elem_teglalap(_gyerek(window, "viewerImageElotteKeret"))
        elotte = _gyerek(window, "viewerImageElotte")
        assert elotte.property("rotation") == 90
        # a kirajzolt kép fekvő lett: a befoglaló dobozban szélesebb, mint magas
        pw = elotte.property("paintedWidth")
        ph = elotte.property("paintedHeight")
        kozep_x = (bal_r["bal"] + bal_r["jobb"]) / 2
        kozep_y = (bal_r["fent"] + bal_r["lent"]) / 2
        # forgatva a kirajzolt terület (ph × pw) a képernyőn
        bal, jobb = kozep_x - ph / 2, kozep_x + ph / 2
        fent, lent = kozep_y - pw / 2, kozep_y + pw / 2
        sz = jobb - bal
        m = lent - fent
        assert _kozel(_szin(kep, jobb - 0.05 * sz, fent + 0.1 * m), KEK), (
            "a kék jel nem a jobb felső sarokban: a kép nincs elforgatva"
        )
        assert _kozel(_szin(kep, bal + 0.05 * sz, fent + 0.1 * m), NARANCS)

    def test_bal_fokusznal_a_vagokeret_a_forgatott_b_kepen(
        self, ket_kep_b_forgatva, qt_app
    ):
        window, _c, _e = ket_kep_b_forgatva
        _bal_fokusz(window, qt_app)
        _panel, overlay = _vagas_kattintva(window, qt_app)
        kep = _kep(window, qt_app)
        keret = _elem_teglalap(_gyerek(window, "viewerImageElotteKeret"))
        _bal, jobb_r = _felek(window)
        for rx, ry in ((0.2, 0.2), (0.8, 0.2), (0.2, 0.8), (0.8, 0.8)):
            x, y = _fogantyu_kozep(overlay, rx, ry)
            assert keret["bal"] <= x <= keret["jobb"], "a fogantyú nem a bal félen"
            assert _feher(_szin(kep, x, y)), (
                f"a ({rx}, {ry}) fogantyú nem rajzolódott ki: {_szin(kep, x, y)}"
            )
        # a jobb (A) kép sötétítetlen és fogantyútlan
        x, y = _relativ_pont(jobb_r, 0.1, 0.1)
        assert _kozel(_szin(kep, x, y), ZOLD)


# -- 3. képarány ---------------------------------------------------------------


class TestAzEszkozokKeparanyaAKijeloltKepe:
    def test_bal_fokusznal_a_b_kep_aranya(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        _bal_fokusz(window, qt_app)
        panel = _gyerek(window, "viewerEditorPanel")
        assert panel.property("imageAspect") == pytest.approx(300 / 500, abs=0.01)

    def test_jobb_fokusznal_az_a_kep_aranya(self, ket_kep, qt_app):
        window, _c, _e = ket_kep
        _jobb_fokusz(window, qt_app)
        panel = _gyerek(window, "viewerEditorPanel")
        assert panel.property("imageAspect") == pytest.approx(640 / 400, abs=0.01)


# -- 4. kirajzolt vágókeret, valódi kattintással --------------------------------


class TestAVagokeretKirajzolva:
    @pytest.mark.parametrize("oldal", ["bal", "jobb"])
    def test_a_fogantyuk_es_a_sotetites_a_kijelolt_kepen(
        self, ket_kep, qt_app, oldal
    ):
        window, _c, _e = ket_kep
        if oldal == "bal":
            _bal_fokusz(window, qt_app)
        else:
            _jobb_fokusz(window, qt_app)
        _panel, overlay = _vagas_kattintva(window, qt_app)
        kep = _kep(window, qt_app)
        bal_r, jobb_r = _felek(window)
        kijelolt, masik = (bal_r, jobb_r) if oldal == "bal" else (jobb_r, bal_r)
        k_szin, m_szin = (NARANCS, ZOLD) if oldal == "bal" else (ZOLD, NARANCS)

        for rx, ry in ((0.2, 0.2), (0.8, 0.8)):
            x, y = _fogantyu_kozep(overlay, rx, ry)
            assert kijelolt["bal"] <= x <= kijelolt["jobb"]
            assert _feher(_szin(kep, x, y))
        # a kijelölésen kívüli sáv sötétítve a kijelölt képen…
        x, y = _relativ_pont(kijelolt, 0.9, 0.5)
        assert _sotetebb(_szin(kep, x, y), k_szin)
        # …a kijelölés belseje nem
        x, y = _relativ_pont(kijelolt, 0.5, 0.5)
        assert _kozel(_szin(kep, x, y), k_szin)
        # a másik képen se sötétítés, se fogantyú
        for rx, ry in ((0.9, 0.5), (0.8, 0.3), (0.8, 0.8), (0.5, 0.9)):
            x, y = _relativ_pont(masik, rx, ry)
            assert _kozel(_szin(kep, x, y), m_szin), (
                f"a nem kijelölt kép ({rx}, {ry}) pontja: {_szin(kep, x, y)}"
            )

    def test_bal_fokusz_nagyitva_a_fogantyuk_a_bal_kepen_latszanak(
        self, ket_kep, qt_app
    ):
        """A hiba: nagyításkor a NEM kijelölt jobb kép nőtt meg, rácsúszott
        a bal képre, és eltakarta a vágókeret fogantyúit."""
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        _panel, overlay = _vagas_kattintva(window, qt_app,
                                           QRectF(0.3, 0.3, 0.4, 0.4))
        nezo.setProperty("zoomValue", 0.6)
        kep = _kep(window, qt_app)
        keret = _elem_teglalap(_gyerek(window, "viewerImageElotteKeret"))
        latszo = 0
        for rx, ry in ((0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)):
            x, y = _fogantyu_kozep(overlay, rx, ry)
            if keret["bal"] + 6 <= x <= keret["jobb"] - 6 \
                    and keret["fent"] + 6 <= y <= keret["lent"] - 6:
                latszo += 1
                assert _feher(_szin(kep, x, y)), (
                    f"a ({rx}, {ry}) fogantyú takarva: {_szin(kep, x, y)}"
                )
        assert latszo >= 2, "a nagyított kijelölés fogantyúi kívül estek"

    def test_bal_fokusz_nagyitva_a_bal_kepre_kattintas_a_vagase(
        self, ket_kep, qt_app
    ):
        """Nagyítva a bal kép közepére kattintás a vágó-eszközé marad: nem
        a jobb kép TapHandlere kapja (az kérdezne és fókuszt váltana)."""
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        _vagas_kattintva(window, qt_app, QRectF(0.25, 0.25, 0.5, 0.5))
        nezo.setProperty("zoomValue", 0.8)
        qt_app.processEvents()
        keret = _gyerek(window, "viewerImageElotteKeret")
        _klikk(qt_app, window, keret,
               x=keret.property("width") * 0.9,
               y=keret.property("height") * 0.5)
        assert not _nyitva(window)
        assert nezo.property("aktivOldal") == "bal"


class TestEgyKepesNezetBalFokuszUtan:
    def test_visszavaltva_az_atfedo_a_foto_kepen(self, ket_kep, qt_app):
        """Bal fókusz után egy képre váltva az `aktivOldal` „bal" marad —
        az átfedő ekkor is a (látható) fő képre kerüljön, ne a rejtett,
        nulla méretű bal félre."""
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerLayoutOnly1up"))
        assert nezo.property("layoutMode") == "1up"
        panel = _gyerek(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        atfedo_r = _elem_teglalap(_gyerek(window, "cropOverlay"))
        kep_r = _kep_teglalap(_gyerek(window, "viewerImage"))
        assert atfedo_r["jobb"] - atfedo_r["bal"] > 100
        for kulcs in ("bal", "fent", "jobb", "lent"):
            assert abs(atfedo_r[kulcs] - kep_r[kulcs]) <= 1.0


class TestAJelvenyAForgatottKepFolott:
    def test_bal_fokusznal_a_forgatott_b_fole_kerul(
        self, ket_kep_b_forgatva, qt_app
    ):
        """A bal kép most a saját forgatásával látszik — a „Kijelölve"
        jelvény a KÉPERNYŐN látszó (elforgatott) kép fölé kerüljön, ne
        lógjon bele."""
        window, _c, _e = ket_kep_b_forgatva
        _bal_fokusz(window, qt_app)
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))
        elotte = _gyerek(window, "viewerImageElotte")
        keret = _elem_teglalap(_gyerek(window, "viewerImageElotteKeret"))
        latszo_mag = elotte.property("paintedWidth")
        kep_fent = (keret["fent"] + keret["lent"]) / 2 - latszo_mag / 2
        assert jelveny["lent"] == pytest.approx(kep_fent - 27, abs=1.5)
