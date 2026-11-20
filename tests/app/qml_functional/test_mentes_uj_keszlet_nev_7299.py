"""#7299 - a mentés Új készlet űrlapja üres névvel indul, és a Létrehozás gomb
tiltott üres vagy foglalt névnél; VALÓDI egérkattintással és gépeléssel.

Az eredeti (`docs/specs/paritas-folyamat-7298.md` 3-4. szakasz):

* `0x00678c09` / `0x006791d0`: a név mező üresen nyílik, alapérték nincs.
* `0x00679570`: a párbeszéd figyelője MINDEN eseményre lefut, és az `ok`
  gombot (`0x0067983b`) csak akkor engedi, ha a név nem üres, nem egyezik
  egy létező készlet nevével ASCII A-Z kisbetűsítve (nincs levágás, a nem
  ASCII betűk kis/nagybetűs alakja KÜLÖN név), és lemez-lemez típusnál a
  mappa sem üres. Hibaszöveg névütközésre nincs.
* `0x0067921b`: szerkesztéskor a típus-csoport tiltott; a cím és a gomb
  felirata is más (`newbackupset.fen`: "New Backup Set" és "Create").

Tudatos eltérés az eredetitől (a jegy 4. pontja): szerkesztéskor a SAJÁT név
kis/nagybetűs átírása engedett (az eredeti ezt is tiltja, hibának tűnik).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QEvent, QMetaObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtTest import QTest

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._racs_maradek_5150_helpers import keres
from tests.app.qml_functional._utolso_maradek_5150_helpers import (
    kattint,
    kijelol_mindent,
    varj,
)

_QML = Path(picasapy.app.__file__).parent / "qml"
_ALAPNEV = "My Backup Set"


def _gepel(view, qt_app, szoveg: str) -> None:
    """Valódi billentyű-események a fókuszált mezőre, karakterenként.

    Az ASCII-t a `QTest.keyClick` adja; a `QTest.keyClicks` csak widgetre
    él, a `_utolso_maradek_5150_helpers.gepel` pedig csak ASCII-t tud, ezért
    az ékezetes betűt (`Á`, `á`, `é`) a szövegét hordozó `QKeyEvent` viszi."""
    for karakter in szoveg:
        if ord(karakter) < 128:
            QTest.keyClick(view, karakter)
        else:
            for tipus in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
                QGuiApplication.sendEvent(
                    view,
                    QKeyEvent(tipus, 0, Qt.KeyboardModifier.NoModifier, karakter),
                )
        qt_app.processEvents()


@pytest.fixture
def kornyezet(qt_app, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    nezetek: list = []
    yield db, gyoker, nezetek
    for view in nezetek:
        view.hide()


def _indit(kornyezet, qt_app):
    """Új vezérlő + gazda ugyanazon az adatbázison, a menü `nyisd()`-jével."""
    from picasapy.app.backup_controller import BackupController

    db, gyoker, nezetek = kornyezet
    vezerlo = BackupController(db, (str(gyoker),))
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    nezetek.append(view)
    QMetaObject.invokeMethod(ablak, "nyisd")
    qt_app.processEvents()
    return view, ablak, vezerlo


@pytest.fixture
def ures_lista(kornyezet, qt_app):
    """Üres adatbázis: az első megnyitás hozza létre az alapkészletet (#7294)."""
    return _indit(kornyezet, qt_app)


def _uj_urlap(view, ablak, qt_app):
    """Az „Új készlet" gomb valódi kattintása, és a név mezőre fókusz."""
    kattint(view, qt_app, "publishNewBackupSet")
    assert varj(qt_app, lambda: ablak.property("szerkesztes") is True)
    kattint(view, qt_app, "backupSetName")


def _gomb_engedett(ablak) -> bool:
    return keres(ablak, "backupFormSave").property("enabled") is True


def _mezo_torles(view, qt_app):
    """A fókuszált mező teljes tartalmának törlése (Ctrl+A, Backspace)."""
    kijelol_mindent(view, qt_app)
    QTest.keyClick(view, Qt.Key.Key_Backspace)
    qt_app.processEvents()


class TestAzUrlapUresenIndul:
    def test_az_elso_megnyitas_utan_pontosan_egy_keszlet_van(self, ures_lista):
        _, _, vezerlo = ures_lista

        assert [k["nev"] for k in vezerlo.keszletek()] == [_ALAPNEV]

    def test_az_uj_keszlet_neve_ures_es_a_gomb_tiltott(
        self, ures_lista, qt_app
    ):
        view, ablak, _ = ures_lista

        _uj_urlap(view, ablak, qt_app)

        assert keres(ablak, "backupSetName").property("text") == ""
        assert ablak.property("urlapNev") == ""
        assert not _gomb_engedett(ablak)

    def test_a_masodik_megnyitas_sem_tolt_elo_nevet(self, ures_lista, qt_app):
        view, ablak, _ = ures_lista
        _uj_urlap(view, ablak, qt_app)
        _gepel(view, qt_app, "Nyaralas")
        kattint(view, qt_app, "backupFormCancel")
        assert varj(qt_app, lambda: ablak.property("szerkesztes") is False)

        _uj_urlap(view, ablak, qt_app)

        assert keres(ablak, "backupSetName").property("text") == ""
        assert not _gomb_engedett(ablak)


class TestAzUrlapCdDvdTipussalIndul:
    """#7302: az Új készlet űrlap a CD/DVD rádióval nyílik.

    Az eredeti felépítője (`0x00678e80`) a `type` rádiót a `[dlg+0xd0]` (a
    cél) üres voltából tölti: `0x00678ec0` betölti, `0x00678ec6` nullához
    hasonlítja, és üresnél az `0x00678ef1`-es ágra ugrik (`push "type"`,
    rádió 0 = CD/DVD); csak nem üres célnál megy a másik ágra. Új módban a
    konstruktor a célt nullázza (`0x00678c09`..`0x00678c3e`), tehát az űrlap
    CD/DVD-vel indul. Nálunk a CD/DVD típus célja a `lemezkepAlapHely()`.
    A típust SOHA nem kattintjuk be: az induló állapotot mérjük."""

    def test_a_cd_dvd_radio_van_kivalasztva_es_a_hely_nem_valaszthato(
        self, ures_lista, qt_app
    ):
        view, ablak, vezerlo = ures_lista

        _uj_urlap(view, ablak, qt_app)

        assert keres(ablak, "backupTypeCdDvd").property("checked") is True
        assert keres(ablak, "backupTypeDisk").property("checked") is False
        assert ablak.property("urlapTipus") == "cddvd"
        assert ablak.property("urlapCel") == vezerlo.lemezkepAlapHely()
        assert keres(ablak, "backupChooseTarget").property("enabled") is False
        assert keres(ablak, "backupSetTarget").property("enabled") is False
        assert keres(ablak, "backupSetTarget").property("text") == (
            vezerlo.lemezkepAlapHely())

    def test_a_nev_beirasa_utan_a_letrehozas_azonnal_engedett(
        self, ures_lista, qt_app
    ):
        view, ablak, vezerlo = ures_lista
        _uj_urlap(view, ablak, qt_app)
        assert not _gomb_engedett(ablak), "név nélkül tiltott"

        _gepel(view, qt_app, "Nyaralas")

        # sem rádió-, sem mappa-kattintás: a név egymaga elég
        assert _gomb_engedett(ablak)
        kattint(view, qt_app, "backupFormSave")
        uj = [k for k in vezerlo.keszletek() if k["nev"] == "Nyaralas"]
        assert len(uj) == 1
        assert uj[0]["tipus"] == "cddvd"
        assert uj[0]["cel"] == vezerlo.lemezkepAlapHely()
        assert ablak.property("szerkesztes") is False

    def test_a_masodik_megnyitas_is_cd_dvd_vel_indul_lemez_valasztas_utan(
        self, ures_lista, qt_app
    ):
        view, ablak, vezerlo = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeDisk")
        assert keres(ablak, "backupTypeDisk").property("checked") is True
        kattint(view, qt_app, "backupFormCancel")
        assert varj(qt_app, lambda: ablak.property("szerkesztes") is False)

        _uj_urlap(view, ablak, qt_app)

        assert keres(ablak, "backupTypeCdDvd").property("checked") is True
        assert keres(ablak, "backupTypeDisk").property("checked") is False
        assert ablak.property("urlapCel") == vezerlo.lemezkepAlapHely()

    def test_a_lemez_lemez_valasztas_kiuriti_az_alaphelyet(
        self, ures_lista, qt_app
    ):
        view, ablak, _ = ures_lista
        _uj_urlap(view, ablak, qt_app)

        kattint(view, qt_app, "backupTypeDisk")

        # a lemezkép-alaphely nem lehet a mappába mentés célja
        assert ablak.property("urlapCel") == ""
        assert keres(ablak, "backupSetTarget").property("text") == ""
        assert keres(ablak, "backupChooseTarget").property("enabled") is True


class TestAFoglaltNev:
    def test_a_baitra_azonos_meglevo_nev_tiltott(self, ures_lista, qt_app):
        view, ablak, vezerlo = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeCdDvd")
        kattint(view, qt_app, "backupSetName")

        _gepel(view, qt_app, "My")
        _gepel(view, qt_app, " ")
        _gepel(view, qt_app, "Backup")
        _gepel(view, qt_app, " ")
        _gepel(view, qt_app, "Set")

        assert ablak.property("urlapNev") == _ALAPNEV
        assert not _gomb_engedett(ablak)
        # a tiltott gombra kattintva nem jön létre második készlet
        kattint(view, qt_app, "backupFormSave")
        assert len(vezerlo.keszletek()) == 1
        assert ablak.property("szerkesztes") is True

    def test_az_ascii_kis_nagybetu_elteres_is_foglalt(self, ures_lista, qt_app):
        view, ablak, _ = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeCdDvd")
        kattint(view, qt_app, "backupSetName")

        _gepel(view, qt_app, "my backup set")
        qt_app.processEvents()

        assert ablak.property("urlapNev") == "my backup set"
        assert not _gomb_engedett(ablak)

    def test_minden_esemenyre_ujraertekelodik(self, ures_lista, qt_app):
        view, ablak, _ = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeCdDvd")
        kattint(view, qt_app, "backupSetName")
        _gepel(view, qt_app, _ALAPNEV)
        qt_app.processEvents()
        assert not _gomb_engedett(ablak)

        QTest.keyClick(view, Qt.Key.Key_Backspace)
        qt_app.processEvents()
        assert _gomb_engedett(ablak), "a rövidebb név már szabad"

        _gepel(view, qt_app, "t")
        qt_app.processEvents()
        assert not _gomb_engedett(ablak), "a visszaírt név újra foglalt"

        _mezo_torles(view, qt_app)
        assert ablak.property("urlapNev") == ""
        assert not _gomb_engedett(ablak), "az üres név tiltott"

    def test_nem_ascii_betu_kulon_nevnek_szamit(self, kornyezet, qt_app):
        from picasapy.app.backup_controller import BackupController

        db, gyoker, _ = kornyezet
        elo = BackupController(db, (str(gyoker),))
        assert elo.ujKeszlet("Saját mentési készlet", "", "minden", "cddvd")
        view, ablak, vezerlo = _indit(kornyezet, qt_app)
        assert "Saját mentési készlet" in [k["nev"] for k in vezerlo.keszletek()]
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeCdDvd")
        kattint(view, qt_app, "backupSetName")

        # a bájtra azonos név: tiltott
        _gepel(view, qt_app, "Saját mentési készlet")
        qt_app.processEvents()
        assert ablak.property("urlapNev") == "Saját mentési készlet"
        assert not _gomb_engedett(ablak)

        # kis `s` az elején: ASCII-eltérés, tiltott
        _mezo_torles(view, qt_app)
        _gepel(view, qt_app, "saját mentési készlet")
        qt_app.processEvents()
        assert ablak.property("urlapNev") == "saját mentési készlet"
        assert not _gomb_engedett(ablak)

        # `SAJÁT`: az `Á` nem ASCII, a kisbetűsítés nem hozza az `á`-ra: szabad
        _mezo_torles(view, qt_app)
        _gepel(view, qt_app, "SAJÁT mentési készlet")
        qt_app.processEvents()
        assert ablak.property("urlapNev") == "SAJÁT mentési készlet"
        assert _gomb_engedett(ablak)

    def test_a_vegi_szokoz_nincs_levagva_az_ellenorzes_elott(
        self, ures_lista, qt_app
    ):
        view, ablak, _ = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeCdDvd")
        kattint(view, qt_app, "backupSetName")

        _gepel(view, qt_app, _ALAPNEV + " ")
        qt_app.processEvents()

        assert ablak.property("urlapNev") == _ALAPNEV + " "
        assert _gomb_engedett(ablak), "az eredetiben nincs levágás"

    def test_nincs_uj_hibaszoveg_a_nevutkozesre(self, ures_lista, qt_app):
        view, ablak, _ = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeCdDvd")
        kattint(view, qt_app, "backupSetName")

        _gepel(view, qt_app, _ALAPNEV)
        qt_app.processEvents()

        assert not keres(ablak, "backupFormError").isVisible()
        assert ablak.property("urlapHiba") == ""


class TestAzUjNevLetrejon:
    def test_cd_dvd_tipusnal_a_nev_eleg_es_a_kattintas_letrehozza(
        self, ures_lista, qt_app
    ):
        view, ablak, vezerlo = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeCdDvd")
        kattint(view, qt_app, "backupSetName")

        _gepel(view, qt_app, "Nyaralas")
        assert _gomb_engedett(ablak)
        kattint(view, qt_app, "backupFormSave")

        assert sorted(k["nev"] for k in vezerlo.keszletek()) == [
            _ALAPNEV, "Nyaralas"]
        assert ablak.property("szerkesztes") is False

    def test_lemez_tipusnal_a_mappa_is_kell(self, ures_lista, qt_app, tmp_path):
        view, ablak, vezerlo = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeDisk")
        kattint(view, qt_app, "backupSetName")
        _gepel(view, qt_app, "Kulso")
        assert not _gomb_engedett(ablak), "mappa nélkül nem hozható létre"

        kattint(view, qt_app, "backupSetTarget")
        cel = str(tmp_path / "cel")
        _gepel(view, qt_app, cel)
        qt_app.processEvents()
        assert ablak.property("urlapCel") == cel
        assert _gomb_engedett(ablak)

        _mezo_torles(view, qt_app)
        assert not _gomb_engedett(ablak), "a mappa törlése újra tiltja"

        _gepel(view, qt_app, cel)
        qt_app.processEvents()
        kattint(view, qt_app, "backupFormSave")
        assert sorted(k["nev"] for k in vezerlo.keszletek()) == [
            "Kulso", _ALAPNEV]
        assert ablak.property("szerkesztes") is False

    def test_a_cd_dvd_tipusra_valtas_a_mappa_nelkul_is_engedi(
        self, ures_lista, qt_app
    ):
        view, ablak, _ = ures_lista
        _uj_urlap(view, ablak, qt_app)
        kattint(view, qt_app, "backupTypeDisk")
        kattint(view, qt_app, "backupSetName")
        _gepel(view, qt_app, "Kulso")
        assert not _gomb_engedett(ablak)

        kattint(view, qt_app, "backupTypeCdDvd")

        assert _gomb_engedett(ablak)


class TestASzerkesztes:
    @pytest.fixture
    def ketto(self, kornyezet, qt_app, tmp_path):
        """Két meglévő készlet (Alfa, Külső); a „Külső" van kiválasztva.

        Az alapkészlet csak üres listán jön létre (#7294), ezért itt nincs."""
        from picasapy.app.backup_controller import BackupController

        db, gyoker, _ = kornyezet
        elo = BackupController(db, (str(gyoker),))
        assert elo.ujKeszlet("Alfa", str(tmp_path / "alfa"), "minden", "lemez")
        assert elo.ujKeszlet("Külső", str(tmp_path / "kulso"), "minden", "lemez")
        view, ablak, vezerlo = _indit(kornyezet, qt_app)
        nevek = [k["nev"] for k in vezerlo.keszletek()]
        ablak.setProperty("kivalasztott", nevek.index("Külső"))
        qt_app.processEvents()
        return view, ablak, vezerlo

    def _szerkeszt(self, ketto, qt_app):
        view, ablak, _ = ketto
        kattint(view, qt_app, "publishEditBackupSet")
        assert varj(qt_app, lambda: ablak.property("szerkesztes") is True)
        assert ablak.property("szerkesztettId") >= 0

    def test_a_sajat_nev_valtozatlanul_engedett(self, ketto, qt_app):
        _, ablak, _ = ketto

        self._szerkeszt(ketto, qt_app)

        assert ablak.property("urlapNev") == "Külső"
        assert _gomb_engedett(ablak)

    def test_masik_keszlet_neve_tiltott(self, ketto, qt_app):
        view, ablak, _ = ketto
        self._szerkeszt(ketto, qt_app)
        kattint(view, qt_app, "backupSetName")

        _mezo_torles(view, qt_app)
        _gepel(view, qt_app, "alfa")
        qt_app.processEvents()

        assert not _gomb_engedett(ablak)

    def test_a_sajat_nev_kisbetus_atirasa_tudatosan_engedett(
        self, ketto, qt_app
    ):
        """Tudatos eltérés: az eredeti ezt is tiltja, hibának tűnik."""
        view, ablak, _ = ketto
        self._szerkeszt(ketto, qt_app)
        kattint(view, qt_app, "backupSetName")

        _mezo_torles(view, qt_app)
        _gepel(view, qt_app, "kulso")
        qt_app.processEvents()

        assert _gomb_engedett(ablak)

    def test_az_ures_nev_szerkeszteskor_is_tiltott(self, ketto, qt_app):
        view, ablak, _ = ketto
        self._szerkeszt(ketto, qt_app)
        kattint(view, qt_app, "backupSetName")

        _mezo_torles(view, qt_app)

        assert not _gomb_engedett(ablak)

    def test_a_szerkeszto_a_keszlet_sajat_tipusat_es_helyet_mutatja(
        self, ketto, qt_app, tmp_path
    ):
        """#7302: az új űrlap CD/DVD-s alapja a szerkesztést nem érinti: a
        lemez-lemez készlet a saját rádióját és mappáját kapja."""
        _, ablak, _ = ketto

        self._szerkeszt(ketto, qt_app)

        assert ablak.property("urlapTipus") == "lemez"
        assert keres(ablak, "backupTypeDisk").property("checked") is True
        assert keres(ablak, "backupTypeCdDvd").property("checked") is False
        # Path-összevetés: Windowson a nyers `str(Path)` visszaperjeles (#5155)
        assert Path(ablak.property("urlapCel")) == tmp_path / "kulso"
        assert Path(
            keres(ablak, "backupSetTarget").property("text")
        ) == tmp_path / "kulso"

    def test_a_tipus_csoport_szerkeszteskor_tiltott(self, ketto, qt_app):
        _, ablak, _ = ketto

        self._szerkeszt(ketto, qt_app)

        assert keres(ablak, "backupTypeCdDvd").property("enabled") is False
        assert keres(ablak, "backupTypeDisk").property("enabled") is False

    def test_a_tipus_csoport_uj_keszletnel_engedett(self, ures_lista, qt_app):
        view, ablak, _ = ures_lista

        _uj_urlap(view, ablak, qt_app)

        assert keres(ablak, "backupTypeCdDvd").property("enabled") is True
        assert keres(ablak, "backupTypeDisk").property("enabled") is True

    def test_az_atnevezes_menti_az_uj_nevet(self, ketto, qt_app):
        view, ablak, vezerlo = ketto
        self._szerkeszt(ketto, qt_app)
        kattint(view, qt_app, "backupSetName")
        _mezo_torles(view, qt_app)
        _gepel(view, qt_app, "Masik")
        qt_app.processEvents()

        kattint(view, qt_app, "backupFormSave")

        assert sorted(k["nev"] for k in vezerlo.keszletek()) == [
            "Alfa", "Masik"]
        assert ablak.property("szerkesztes") is False


def _felirat_kontraszt(view, qt_app, elem) -> int:
    """A rádió FELIRATÁNAK kontrasztja a háttérhez képest a kirajzolt képen (a
    jelölő kör nélkül): a háttértől legtávolabbi képpont csatornánkénti
    távolsága. A paletta platformfüggő (a CI-n világos, a sötét témájú gépen
    sötét), ezért nem a legfényesebb képpontot mérjük: az világos háttéren
    maga a háttér. A halványabb felirat a háttér felé közelít, kontrasztja
    kisebb."""
    qt_app.processEvents()
    bal_felso = elem.mapToScene(QPointF(0, 0))
    kep = view.grabWindow()
    kezd_x = round(bal_felso.x()) + 30
    veg_x = round(bal_felso.x() + elem.width())
    teteje = round(bal_felso.y())
    # a vezérlő legfelső sora a felirat fölötti háttér
    hatter = kep.pixelColor(kezd_x, teteje)
    legnagyobb = 0
    for y in range(teteje, round(bal_felso.y() + elem.height())):
        for x in range(kezd_x, veg_x):
            szin = kep.pixelColor(x, y)
            legnagyobb = max(
                legnagyobb,
                abs(szin.red() - hatter.red()),
                abs(szin.green() - hatter.green()),
                abs(szin.blue() - hatter.blue()),
            )
    return legnagyobb


class TestATiltottTipusCsoportLatszik:
    """A tiltás nem csak `enabled`: a felhasználó a képen lássa (a stílus a
    rádiót magától nem halványítja)."""

    def test_szerkeszteskor_a_rado_felirata_halvanyabb_mint_ujnal(
        self, kornyezet, qt_app, tmp_path
    ):
        from picasapy.app.backup_controller import BackupController

        db, gyoker, _ = kornyezet
        elo = BackupController(db, (str(gyoker),))
        assert elo.ujKeszlet("Alfa", str(tmp_path / "alfa"), "minden", "lemez")
        view, ablak, _ = _indit(kornyezet, qt_app)

        _uj_urlap(view, ablak, qt_app)
        cd_dvd = keres(ablak, "backupTypeCdDvd")
        assert varj(qt_app, lambda: cd_dvd.property("opacity") == 1.0)
        engedett = _felirat_kontraszt(view, qt_app, cd_dvd)
        kattint(view, qt_app, "backupFormCancel")
        assert varj(qt_app, lambda: ablak.property("szerkesztes") is False)

        kattint(view, qt_app, "publishEditBackupSet")
        assert varj(qt_app, lambda: ablak.property("szerkesztes") is True)
        assert varj(qt_app, lambda: cd_dvd.property("opacity") < 1.0)
        tiltott = _felirat_kontraszt(view, qt_app, cd_dvd)

        assert engedett > 100, "a mérés nem a feliratot találta el"
        assert tiltott < engedett - 30, (
            f"a tiltott rádió felirata nem halványabb: kontraszt {tiltott} vs {engedett}")


class TestAFeliratok:
    def test_uj_keszletnel_new_backup_set_name_create(self, ures_lista, qt_app):
        view, ablak, _ = ures_lista

        _uj_urlap(view, ablak, qt_app)

        assert keres(ablak, "backupSetDialog").property("title") == (
            "New Backup Set")
        assert keres(ablak, "backupSetNameLabel").property("text") == "Name:"
        assert keres(ablak, "backupFormSave").property("text") == "Create"

    def test_szerkeszteskor_edit_backup_set_name_change(self, ures_lista, qt_app):
        view, ablak, _ = ures_lista
        kattint(view, qt_app, "publishEditBackupSet")
        assert varj(qt_app, lambda: ablak.property("szerkesztes") is True)

        assert keres(ablak, "backupSetDialog").property("title") == (
            "Edit Backup Set")
        assert keres(ablak, "backupSetNameLabel").property("text") == "Name:"
        assert keres(ablak, "backupFormSave").property("text") == "Change"


class TestASzomszedosElemekValtozatlanok:
    def test_a_legordulo_a_torles_es_a_mentes_gomb_nem_valtozott(
        self, kornyezet, qt_app, tmp_path
    ):
        from picasapy.app.backup_controller import BackupController

        db, gyoker, _ = kornyezet
        elo = BackupController(db, (str(gyoker),))
        assert elo.ujKeszlet("Alfa", str(tmp_path / "alfa"), "minden", "lemez")
        assert elo.ujKeszlet("Külső", str(tmp_path / "kulso"), "minden", "lemez")
        view, ablak, vezerlo = _indit(kornyezet, qt_app)
        kombo = keres(ablak, "publishBackupSetMenu")
        torles = keres(ablak, "publishDeleteBackupSet")
        inditas = keres(ablak, "publishBackupGo")

        def allapot():
            return (
                kombo.property("visible"), kombo.property("enabled"),
                kombo.property("currentText"), torles.isVisible(),
                torles.property("enabled"), inditas.property("enabled"),
                ablak.property("kivalasztott"),
            )

        elotte = allapot()
        assert elotte[3] is True, "két készletnél a Törlés látszik"

        # az űrlap megnyitása, gépelés és Mégse nem érinti a szomszédokat
        _uj_urlap(view, ablak, qt_app)
        _gepel(view, qt_app, "Nyaralas")
        kattint(view, qt_app, "backupFormCancel")
        assert varj(qt_app, lambda: ablak.property("szerkesztes") is False)

        assert allapot() == elotte
        assert len(vezerlo.keszletek()) == 2
