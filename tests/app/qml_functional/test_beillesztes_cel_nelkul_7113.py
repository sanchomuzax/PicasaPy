"""#7113: a cél nélküli Beillesztés a hiányzó célmappát jelzi, nem az üres vágólapot.

Az eredeti (`0x005791d0`) a cél hiányakor az `IDS_NEED_SELECTED_ALBUM`
üzenetet hívja (`0x005791fb-0x00579220`); a hivatalos szöveg: „A Folder or
Album must be selected to do this.” Nálunk a `beillesztAVagolaprol` minden
elmaradt beillesztésre az üres vágólap szövegét mutatta, a célmappa
hiányára is.

A próbák a VALÓDI főablakon futnak (`qml_app`): a függvényt az ablakról hívjuk,
és a kirajzolt hibasávot olvassuk vissza, nem a forrást.

Mit őriz (a jegy „Kész, ha” és „Nem szabad” pontjai):
  * fájl a vágólapon, de nincs célmappa: célhiány-üzenet, semmi nem indul;
  * üres vágólap (célmappával és anélkül is): az üres vágólap üzenete;
  * egyik elutasított esetben sem jön létre vagy mozdul el fájl;
  * a rendes beillesztés (van fájl és van cél) változatlanul elindul, és
    nem hoz hibasávot.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, QTranslator, Qt

_CEL_HIANY = "A Folder or Album must be selected to do this."
_URES_VAGOLAP = "There are no files on the clipboard to paste."
_CEL_HIANY_HU = (
    "Ennek a műveletnek az elvégzéséhez ki kell jelölnie egy mappát vagy egy albumot."
)
_URES_VAGOLAP_HU = "Nincs beilleszthető fájl a vágólapon."

_I18N = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "i18n"


@pytest.fixture
def magyar_forditas(qt_app):
    from picasapy.app import application

    fordito = QTranslator(qt_app)
    qm = Path(application.__file__).parent / "i18n" / "picasapy_hu.qm"
    assert fordito.load(str(qm)), f"a magyar fordítás nem tölthető be: {qm}"
    assert qt_app.installTranslator(fordito)
    yield
    qt_app.removeTranslator(fordito)


@pytest.fixture
def qml_app_magyar(magyar_forditas, qml_app):
    """A QML az angol forrásszöveg ELLEN, a magyar fordító telepítése után tölt."""
    return qml_app


def _gyerek(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _fajlmuveletek(engine):
    vezerlo = engine.rootContext().contextProperty("fileOpsController")
    assert vezerlo is not None, "a fileOpsController nincs bekötve"
    return vezerlo


def _beillesztes(window, qt_app) -> None:
    """A menü és a billentyű ugyanezt a főablak-függvényt hívja."""
    QMetaObject.invokeMethod(
        window, "beillesztAVagolaprol", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _hibasav(window) -> tuple[str, bool, bool]:
    szoveg = _gyerek(window, "errorBannerText").property("text")
    sav = _gyerek(window, "errorBanner")
    return szoveg, sav.property("visible") is True, sav.property("notice") is True


def _fa(gyoker: Path) -> list[str]:
    return sorted(str(p.relative_to(gyoker)) for p in gyoker.rglob("*"))


class _Hivasok:
    """A beillesztés két köteg-útja: ha NEM indul művelet, egyik sem hívódik."""

    def __init__(self, vezerlo, monkeypatch):
        self.masolas: list[tuple] = []
        self.athelyezes: list[tuple] = []
        self.paste_megerositesek: list[tuple] = []
        vezerlo.clipboardPasteConfirmationRequested.connect(
            lambda *args: self.paste_megerositesek.append(args)
        )
        monkeypatch.setattr(
            vezerlo, "copyPhotos", lambda *a: self.masolas.append(a)
        )
        monkeypatch.setattr(
            vezerlo, "movePhotos", lambda *a: self.athelyezes.append(a)
        )

    @property
    def semmi(self) -> bool:
        return not self.masolas and not self.athelyezes and not self.paste_megerositesek

    def ellenorzi_a_megerositest(self, kep: Path, cel: Path, operation: str) -> None:
        assert not self.masolas and not self.athelyezes
        assert len(self.paste_megerositesek) == 1
        paths, dest, kapott_operation = self.paste_megerositesek[0]
        assert [Path(path) for path in paths] == [kep]
        assert Path(dest) == cel
        assert kapott_operation == operation


@pytest.fixture
def helyzet(qml_app, qt_app, tmp_path, monkeypatch):
    """Egy másolható fájl a vágólapon, és egy üres célmappa a lemezen."""
    window, controller, engine = qml_app
    vezerlo = _fajlmuveletek(engine)
    forras = tmp_path / "vagolap-forras"
    forras.mkdir()
    kep = forras / "vagolapon.jpg"
    kep.write_bytes(b"kep")
    cel = tmp_path / "cel-mappa"
    cel.mkdir()
    hivasok = _Hivasok(vezerlo, monkeypatch)
    return {
        "window": window,
        "controller": controller,
        "vezerlo": vezerlo,
        "qt_app": qt_app,
        "kep": kep,
        "cel": cel,
        "gyoker": tmp_path,
        "hivasok": hivasok,
    }


def _vagolapra(h) -> None:
    h["vezerlo"].copyFilesToClipboard([str(h["kep"])])
    assert h["vezerlo"].clipboardHasFiles is True, "a próba vágólapja nem töltődött"


def _ures_vagolap(h) -> None:
    h["vezerlo"]._vagolap_adat = None
    assert h["vezerlo"].clipboardHasFiles is False


def _celmappa(h, ertek: str) -> None:
    h["controller"]._current_folder = ertek
    assert h["controller"].currentFolder == ertek


class TestACelHiany:
    def test_fajl_a_vagolapon_cel_nelkul_a_celhianyt_nevezi_meg(self, helyzet):
        _vagolapra(helyzet)
        _celmappa(helyzet, "")
        elotte = _fa(helyzet["gyoker"])

        _beillesztes(helyzet["window"], helyzet["qt_app"])

        szoveg, latszik, tajekoztatas = _hibasav(helyzet["window"])
        assert szoveg == _CEL_HIANY, szoveg
        assert latszik, "a célhiány jelzése nem látszik a hibasávban"
        assert tajekoztatas, "a célhiány tájékoztatás (borostyán), nem hiba"
        assert szoveg != _URES_VAGOLAP, "a célhiányt az üres vágólap szövege takarja"
        assert helyzet["hivasok"].semmi, "cél nélkül nem indulhat másolás/áthelyezés"
        assert _fa(helyzet["gyoker"]) == elotte, "fájl jött létre vagy mozdult"
        assert helyzet["kep"].read_bytes() == b"kep"

    def test_a_celhiany_kivagasnal_is_ugyanaz_es_a_forras_marad(self, helyzet):
        helyzet["vezerlo"].cutFilesToClipboard([str(helyzet["kep"])])
        assert helyzet["vezerlo"].clipboardHasFiles is True
        _celmappa(helyzet, "")
        elotte = _fa(helyzet["gyoker"])

        _beillesztes(helyzet["window"], helyzet["qt_app"])

        assert _hibasav(helyzet["window"])[0] == _CEL_HIANY
        assert helyzet["hivasok"].semmi
        assert _fa(helyzet["gyoker"]) == elotte, "kivágásnál a forrás nem mozdulhat"

    def test_a_celhiany_sav_a_kepernyon_belul_es_teljes_szoveggel_all(self, helyzet):
        """Kirajzolt eredmény: a sáv látszik, és a teljes szöveg a sávon belül van."""
        _vagolapra(helyzet)
        _celmappa(helyzet, "")

        _beillesztes(helyzet["window"], helyzet["qt_app"])

        sav = _gyerek(helyzet["window"], "errorBanner")
        szoveg = _gyerek(helyzet["window"], "errorBannerText")
        assert szoveg.property("text") == _CEL_HIANY
        assert sav.property("width") > 0 and sav.property("height") > 0
        bal_felso = szoveg.mapToItem(sav, QPointF(0, 0))
        assert bal_felso.x() >= 0 and bal_felso.y() >= 0
        assert bal_felso.x() + szoveg.property("width") <= sav.property("width")
        assert bal_felso.y() + szoveg.property("height") <= sav.property("height")
        # a Text nem vágja le: egész sorok férnek a megjelenített magasságba
        assert szoveg.property("contentHeight") <= szoveg.property("height") + 0.5
        assert szoveg.property("truncated") is not True


class TestAzUresVagolap:
    def test_ures_vagolap_cel_nelkul_az_ures_vagolap_uzenete_marad(self, helyzet):
        _ures_vagolap(helyzet)
        _celmappa(helyzet, "")
        elotte = _fa(helyzet["gyoker"])

        _beillesztes(helyzet["window"], helyzet["qt_app"])

        szoveg, latszik, tajekoztatas = _hibasav(helyzet["window"])
        assert szoveg == _URES_VAGOLAP, szoveg
        assert latszik and tajekoztatas
        assert helyzet["hivasok"].semmi
        assert _fa(helyzet["gyoker"]) == elotte

    def test_ures_vagolap_celmappaval_az_ures_vagolap_uzenete_marad(self, helyzet):
        _ures_vagolap(helyzet)
        _celmappa(helyzet, str(helyzet["cel"]))
        elotte = _fa(helyzet["gyoker"])

        _beillesztes(helyzet["window"], helyzet["qt_app"])

        szoveg, latszik, tajekoztatas = _hibasav(helyzet["window"])
        assert szoveg == _URES_VAGOLAP, szoveg
        assert latszik and tajekoztatas
        assert helyzet["hivasok"].semmi
        assert _fa(helyzet["gyoker"]) == elotte


class TestARendesBeillesztesNemSerul:
    def test_fajl_es_cel_eseten_elindul_a_masolas_es_nincs_figyelmeztetes(self, helyzet):
        _vagolapra(helyzet)
        _celmappa(helyzet, str(helyzet["cel"]))

        _beillesztes(helyzet["window"], helyzet["qt_app"])

        hivasok = helyzet["hivasok"]
        hivasok.ellenorzi_a_megerositest(
            helyzet["kep"], helyzet["cel"], "copy"
        )
        szoveg, latszik, _ = _hibasav(helyzet["window"])
        assert szoveg == "" and not latszik, (
            f"megerősítés előtt nem maradhat hibasáv: {szoveg!r}"
        )

    def test_kivagas_es_cel_eseten_athelyezes_indul(self, helyzet):
        helyzet["vezerlo"].cutFilesToClipboard([str(helyzet["kep"])])
        _celmappa(helyzet, str(helyzet["cel"]))

        _beillesztes(helyzet["window"], helyzet["qt_app"])

        hivasok = helyzet["hivasok"]
        hivasok.ellenorzi_a_megerositest(
            helyzet["kep"], helyzet["cel"], "cut"
        )
        assert _hibasav(helyzet["window"])[0] == ""


class TestAMagyarFelirat:
    def test_a_celhiany_a_hivatalos_magyar_szoveggel_jelenik_meg(
        self, qml_app_magyar, qt_app, tmp_path, monkeypatch
    ):
        window, controller, engine = qml_app_magyar
        vezerlo = _fajlmuveletek(engine)
        kep = tmp_path / "a.jpg"
        kep.write_bytes(b"x")
        hivasok = _Hivasok(vezerlo, monkeypatch)
        vezerlo.copyFilesToClipboard([str(kep)])
        controller._current_folder = ""

        _beillesztes(window, qt_app)

        assert _hibasav(window)[0] == _CEL_HIANY_HU
        assert hivasok.semmi

    def test_az_ures_vagolap_magyar_szovege_valtozatlan(
        self, qml_app_magyar, qt_app
    ):
        window, controller, engine = qml_app_magyar
        _fajlmuveletek(engine)._vagolap_adat = None
        controller._current_folder = ""

        _beillesztes(window, qt_app)

        assert _hibasav(window)[0] == _URES_VAGOLAP_HU


def _ts_uzenetek(ts: Path, forras: str) -> list[ET.Element]:
    gyoker = ET.parse(ts).getroot()
    return [
        uzenet
        for uzenet in gyoker.iter("message")
        if uzenet.findtext("source") == forras
    ]


class TestAFordites:
    def test_mind_a_41_nyelvben_van_kitoltott_celhiany_fordites(self):
        """„Hivatalos fordítás a szövegtárból": minden nyelvi `.ts`-ben a
        MainWindowCommands-kontextusban ott áll a szöveg, nem `unfinished`,
        nem üres."""
        fajlok = sorted(_I18N.glob("picasapy_*.ts"))
        assert len(fajlok) == 41, len(fajlok)
        hibak = []
        for ts in fajlok:
            kontextusok = {
                kontextus.findtext("name"): kontextus
                for kontextus in ET.parse(ts).getroot().iter("context")
            }
            kontextus = kontextusok.get("MainWindowCommands")
            talalat = [
                uzenet
                for uzenet in (kontextus.iter("message") if kontextus is not None else ())
                if uzenet.findtext("source") == _CEL_HIANY
            ]
            if not talalat:
                hibak.append(f"{ts.name}: hiányzik")
                continue
            for uzenet in talalat:
                fordites = uzenet.find("translation")
                szoveg = (fordites.text or "").strip() if fordites is not None else ""
                if not szoveg or fordites.get("type") == "unfinished":
                    hibak.append(f"{ts.name}: üres vagy unfinished")
        assert not hibak, hibak

    def test_a_magyar_az_eredeti_hivatalos_szoveg(self):
        talalat = _ts_uzenetek(_I18N / "picasapy_hu.ts", _CEL_HIANY)
        assert talalat, "a magyar szótárban hiányzik"
        assert {u.findtext("translation") for u in talalat} == {_CEL_HIANY_HU}

    def test_az_ures_vagolap_szovege_a_magyarban_valtozatlan(self):
        talalat = _ts_uzenetek(_I18N / "picasapy_hu.ts", _URES_VAGOLAP)
        assert talalat
        assert {u.findtext("translation") for u in talalat} == {_URES_VAGOLAP_HU}
