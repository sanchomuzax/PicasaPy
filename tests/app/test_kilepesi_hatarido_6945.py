"""#6945: a rendezett leállás nem tarthatja vissza a folyamatot korlátlanul.

A kilépés (`app.exec()` utáni lánc) több helyen vár háttérmunkára, és az egyik
várakozás szándékosan KORLÁTLAN (a `controller.shutdown()` az átnevező szálakra
`None` időkorláttal vár, hogy az objektumok ne semmisüljenek meg futó átnevezés
mellett). Ha egy ilyen várakozás elakad, a program az `exec()` UTÁN fagyna le,
ablak nélkül, és csak kívülről lehetne megölni.

A kilépési határidő-őr az `aboutToQuit`-tól számít: ha a folyamat a határidőn
belül nem ér véget, a naplóba kerül, hol áll a fő szál és mely háttérmunkák
futnak, a beállítások mentődnek, és a program kényszerítve kilép.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, Signal

from picasapy.app import kilepesi_hatarido
from picasapy.app.worker_thread import BackgroundWorkerMixin
from support.jpeg_factory import make_jpeg
from support.kilepes_proba_6945 import futtasd

#: a felső korlát egy esemény megvárására (a lassú CI-gépet is elbírja)
VARAKOZAS_S = 15.0


class _Tarto(BackgroundWorkerMixin):
    pass


class _AlkalmazasHelyettes(QObject):
    aboutToQuit = Signal()


@pytest.fixture
def kilepesek(monkeypatch):
    """A kényszerített kilépés és a mentés helyettesítve: a tesztfolyamat él marad."""
    hivasok: list[int] = []
    esemeny = threading.Event()
    mentesek: list[str] = []

    def kilep(kod: int) -> None:
        hivasok.append(kod)
        esemeny.set()

    monkeypatch.setattr(kilepesi_hatarido, "_kilep", kilep)
    monkeypatch.setattr(
        kilepesi_hatarido, "_beallitasok_mentese", lambda: mentesek.append("mentes")
    )
    monkeypatch.setattr(kilepesi_hatarido, "_orszem", None)
    monkeypatch.setattr(kilepesi_hatarido, "_leallitas_jelzo", threading.Event())
    yield SimpleNamespace(hivasok=hivasok, esemeny=esemeny, mentesek=mentesek)
    # a próbaszál ne éljen tovább a teszt után
    szal = kilepesi_hatarido._orszem
    if szal is not None:
        szal.join(VARAKOZAS_S)


class TestAHataridoOr:
    def test_a_hatarido_utan_kenyszeritve_kilep(self, kilepesek):
        kezdet = time.monotonic()

        kilepesi_hatarido.inditsd_a_hatarido_orzot(0.3)

        assert kilepesek.esemeny.wait(VARAKOZAS_S), "a határidő után nem lépett ki"
        assert kilepesek.hivasok == [0]
        assert time.monotonic() - kezdet >= 0.3

    def test_a_hatarido_ELOTT_nem_lep_ki(self, kilepesek):
        kilepesi_hatarido.inditsd_a_hatarido_orzot(VARAKOZAS_S * 4)

        assert not kilepesek.esemeny.wait(0.5)
        assert kilepesek.hivasok == []
        # a próbaszál tisztán álljon le: a határidőt lejárat nélkül nem várjuk végig
        kilepesi_hatarido._leallitas_jelzo.set()

    def test_ketszer_inditva_egy_orszem_van(self, kilepesek):
        elso = kilepesi_hatarido.inditsd_a_hatarido_orzot(0.3)
        masodik = kilepesi_hatarido.inditsd_a_hatarido_orzot(0.3)

        assert masodik is elso
        assert kilepesek.esemeny.wait(VARAKOZAS_S)
        elso.join(VARAKOZAS_S)
        assert kilepesek.hivasok == [0], "a kilépés kétszer futott"

    def test_a_beallitasok_mentese_mar_az_indulaskor_megtortenik(self, kilepesek):
        """A megerősített kilépés után a felhasználó beállításai még a
        rendezett leállás ELŐTT lemezre kerülnek, a határidőtől függetlenül."""
        kilepesi_hatarido.inditsd_a_hatarido_orzot(VARAKOZAS_S * 4)

        assert kilepesek.mentesek == ["mentes"]
        kilepesi_hatarido._leallitas_jelzo.set()

    def test_a_kenyszeritett_kilepes_elott_ujra_ment(self, kilepesek):
        kilepesi_hatarido.inditsd_a_hatarido_orzot(0.3)

        assert kilepesek.esemeny.wait(VARAKOZAS_S)
        assert kilepesek.mentesek == ["mentes", "mentes"]

    def test_a_naplo_megnevezi_a_futo_hattermunkat_es_a_fo_szal_helyet(
        self, kilepesek, caplog
    ):
        felenged = threading.Event()
        tarto = _Tarto()
        tarto._start_background(felenged.wait, name="picasapy-proba-export")
        try:
            with caplog.at_level("ERROR", logger=kilepesi_hatarido.__name__):
                kilepesi_hatarido.inditsd_a_hatarido_orzot(0.3)
                assert kilepesek.esemeny.wait(VARAKOZAS_S)
        finally:
            felenged.set()
            tarto.waitForBackgroundWorkers(VARAKOZAS_S)

        szoveg = "\n".join(rekord.getMessage() for rekord in caplog.records)
        assert "kényszerített kilépés" in szoveg
        assert "picasapy-proba-export" in szoveg
        assert "A fő szál itt áll" in szoveg

    def test_a_mentes_hibaja_nem_akadalyozza_a_kilepest(self, kilepesek, monkeypatch):
        def rossz() -> None:
            raise RuntimeError("a beállítások nem írhatók")

        monkeypatch.setattr(kilepesi_hatarido, "_beallitasok_mentese", rossz)

        kilepesi_hatarido.inditsd_a_hatarido_orzot(0.3)

        assert kilepesek.esemeny.wait(VARAKOZAS_S)
        assert kilepesek.hivasok == [0]

    def test_az_elakadt_mentes_sem_tartja_vissza_a_kilepest(
        self, kilepesek, monkeypatch
    ):
        """Az őrszál a mentésre is csak korlátozott ideig vár."""
        beragadt = threading.Event()
        monkeypatch.setattr(kilepesi_hatarido, "_MENTES_IDOKORLAT_S", 0.3)
        monkeypatch.setattr(
            kilepesi_hatarido, "_beallitasok_mentese", lambda: beragadt.wait(VARAKOZAS_S)
        )

        kilepesi_hatarido._kenyszeritsd_a_kilepest()

        assert kilepesek.hivasok == [0]
        beragadt.set()


class TestAzAzonnaliKilepes:
    """A kényszerített kilépés platformágai (a platform fogantyúval rögzítve)."""

    def test_linuxon_az_os_exit_fut(self, monkeypatch):
        kodok: list[int] = []
        monkeypatch.setattr(kilepesi_hatarido, "_platform", lambda: "linux")
        monkeypatch.setattr(kilepesi_hatarido, "_os_exit", kodok.append)

        kilepesi_hatarido._azonnali_kilepes(3)

        assert kodok == [3]

    def test_windowson_elobb_a_folyamat_vegleges_leallitasa_fut(self, monkeypatch):
        esemenyek: list[tuple] = []

        class _Kernel32:
            def GetCurrentProcess(self) -> int:
                return 42

            def TerminateProcess(self, azonosito: int, kod: int) -> None:
                esemenyek.append(("TerminateProcess", azonosito, kod))

        monkeypatch.setattr(kilepesi_hatarido, "_kernel32", _Kernel32)
        monkeypatch.setattr(kilepesi_hatarido, "_platform", lambda: "win32")
        monkeypatch.setattr(
            kilepesi_hatarido, "_os_exit", lambda kod: esemenyek.append(("os_exit", kod))
        )

        kilepesi_hatarido._azonnali_kilepes(0)

        assert esemenyek == [("TerminateProcess", 42, 0), ("os_exit", 0)]


class TestABekotes:
    def test_az_aboutToQuit_inditja_az_orszemet(self, kilepesek):
        alkalmazas = _AlkalmazasHelyettes()
        kilepesi_hatarido.figyeld_a_kilepest(alkalmazas, hatarido_s=0.3)

        assert kilepesek.hivasok == [], "kilépés előtt az őrnek nem szabad futnia"
        alkalmazas.aboutToQuit.emit()

        assert kilepesek.esemeny.wait(VARAKOZAS_S)

    def test_a_run_az_ELSO_kezelokent_kotje_be(self):
        """A többi `aboutToQuit`-kezelő egyike is elakadhat: az őr csak akkor véd,
        ha ő fut elsőként, vagyis a vezérlők regisztrálása ELŐTT köt be."""
        forras = Path(kilepesi_hatarido.__file__).with_name("application.py").read_text(
            encoding="utf-8"
        )
        qml_forras = Path(kilepesi_hatarido.__file__).with_name(
            "application_startup_qml.py"
        ).read_text(encoding="utf-8")
        elokeszites = Path(kilepesi_hatarido.__file__).with_name(
            "application_startup_prepare.py"
        ).read_text(encoding="utf-8")
        beallitas = forras.index("_startup_step_log_and_qt_setup(state)")
        regisztracio = forras.index("_startup_step_register_qml_context(state)")
        exec_hivas = forras.index("exit_code = app.exec()")
        # az őrt a Qt-beállító lépés köti be, rögtön az alkalmazás létrejötte után
        app_kesz = elokeszites.index("state.app = app")
        orszem = elokeszites.index("figyeld_a_kilepest(app)")

        assert beallitas < regisztracio < exec_hivas
        assert app_kesz < orszem
        assert "aboutToQuit.connect" in qml_forras


class TestAFolyamatSzintuKenyszeritettKilepes:
    def test_az_elakadt_rendezett_leallas_utan_a_folyamat_kilep(self, tmp_path):
        """A vezérlő átnevező-szálai közt beragadt szálra a `controller.shutdown()`
        korlátlanul vár: a határidő-őr nélkül a folyamat örökre élne."""
        mappa = tmp_path / "kepek"
        mappa.mkdir()
        make_jpeg(mappa / "a.jpg", size=(64, 48))
        felso_korlat_s = kilepesi_hatarido.KILEPESI_HATARIDO_S + 12.0

        eredmeny = futtasd(
            tmp_path / "profil",
            mappa,
            belepes="kilepes",
            munka="atnevezes",
            hatarido_s=felso_korlat_s,
        )

        diag = (
            f"kilepett={eredmeny.kilepett} ido={eredmeny.kilepesi_ido_s} "
            f"kod={eredmeny.visszateresi_kod}\n{eredmeny.kimenet[-2500:]}"
            f"\n{eredmeny.veremkep[-2500:]}"
        )
        assert eredmeny.eljutott_a_kattintasig, diag
        assert eredmeny.kilepett, (
            f"a folyamat {felso_korlat_s} s után is fut a beragadt leállás mellett\n"
            + diag
        )
        assert eredmeny.visszateresi_kod == 0, diag
        assert eredmeny.kilepesi_ido_s >= kilepesi_hatarido.KILEPESI_HATARIDO_S - 1, (
            "a kilépés a határidő előtt megtörtént: ez nem a határidő-őr működése\n"
            + diag
        )
        naplok = list((tmp_path / "profil").rglob("errorlog.txt"))
        assert len(naplok) == 1, diag
        naplo = naplok[0].read_text(encoding="utf-8")
        assert "kényszerített kilépés" in naplo, diag
        assert "_wait_for_rename_workers" in naplo, (
            "a napló nem mondja meg, hol állt a fő szál\n" + naplo[-2500:]
        )
