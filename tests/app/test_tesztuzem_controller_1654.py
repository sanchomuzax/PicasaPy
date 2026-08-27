"""#1654: a tesztüzem vezérlő-szelete — tartósság és egykattintásos átadás.

⚠️ A `/mnt/nas` ÉLES családi adat. Ez a fájl SOHA nem ír oda: a közös
mappa útvonala fogantyún (`_megosztas_gyokere`) érkezik, és a tesztek
`tmp_path`-t adnak be.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app import tesztuzem_controller as modul
from picasapy.app.tesztuzem_controller import TesztuzemMixin
from picasapy.perf.tesztuzem import (
    NAPLO_ALMAPPA,
    TESZTUZEM_BEALLITAS_KULCS,
)


class _Probe(TesztuzemMixin, QObject):
    """A mixin önmagában — az AppController teljes felépítése nélkül.

    (A `test_appearance_controller.py` mintája: a szelet csak a
    `_get_settings()`-re támaszkodik.)"""

    def __init__(self, settings):
        super().__init__()
        self._settings = settings
        self._init_tesztuzem()

    def _get_settings(self):
        return self._settings


@pytest.fixture
def ini(tmp_path):
    return tmp_path / "settings.ini"


@pytest.fixture
def controller(qt_app, ini, monkeypatch):
    # a parancssori kapcsoló ne szivárogjon be a valós sys.argv-ból
    monkeypatch.setattr(modul, "_argv", lambda: ["pytest"])
    return _Probe(QSettings(str(ini), QSettings.Format.IniFormat))


class TestAlapallapot:
    def test_alapbol_ki_van_kapcsolva(self, controller):
        assert controller.tesztuzemEnabled is False

    def test_a_TAROLT_allapotbol_indul(self, qt_app, ini, monkeypatch):
        monkeypatch.setattr(modul, "_argv", lambda: ["pytest"])
        tarolo = QSettings(str(ini), QSettings.Format.IniFormat)
        tarolo.setValue(TESZTUZEM_BEALLITAS_KULCS, True)
        tarolo.sync()
        assert _Probe(
            QSettings(str(ini), QSettings.Format.IniFormat)
        ).tesztuzemEnabled is True

    def test_a_parancssori_kapcsolo_is_bekapcsolja(self, qt_app, ini, monkeypatch):
        """`--tesztuzem`-mel indítva a menü PIPÁLT, és a „Napló elküldése"
        látszik — enélkül a felhasználó nem tudná átadni azt a naplót,
        amit épp most készített a program."""
        monkeypatch.setattr(modul, "_argv", lambda: ["picasapy", "--tesztuzem"])
        assert _Probe(
            QSettings(str(ini), QSettings.Format.IniFormat)
        ).tesztuzemEnabled is True


class TestTartossag:
    """⚠️ A jegy DoD-ja: „A kapcsoló TÚLÉLI az újraindítást"."""

    def test_a_bekapcsolas_LEMEZRE_irodik(self, controller, ini, qt_app):
        controller.setTesztuzemEnabled(True)

        # ÚJ QSettings-példány UGYANARRÓL a fájlról — ez a „következő
        # indítás" próbája. Ha a vezérlő csak memóriában tartaná az
        # állapotot, itt hamisat kapnánk.
        ujra = QSettings(str(ini), QSettings.Format.IniFormat)
        assert ujra.value(TESZTUZEM_BEALLITAS_KULCS) in (True, "true")

    def test_ujrainditas_utan_is_bekapcsolva_marad(self, controller, ini, qt_app):
        controller.setTesztuzemEnabled(True)
        masodik = _Probe(QSettings(str(ini), QSettings.Format.IniFormat))
        assert masodik.tesztuzemEnabled is True

    def test_a_kikapcsolas_is_tartos(self, controller, ini, qt_app):
        controller.setTesztuzemEnabled(True)
        controller.setTesztuzemEnabled(False)
        masodik = _Probe(QSettings(str(ini), QSettings.Format.IniFormat))
        assert masodik.tesztuzemEnabled is False

    def test_a_valtas_jelzest_bocsat_ki(self, controller, qt_app):
        latott = []
        controller.tesztuzemChanged.connect(lambda: latott.append(True))
        controller.toggleTesztuzem()
        assert latott and controller.tesztuzemEnabled is True

    def test_azonos_ertekre_allitas_nem_jelez(self, controller, qt_app):
        latott = []
        controller.tesztuzemChanged.connect(lambda: latott.append(True))
        controller.setTesztuzemEnabled(False)
        assert latott == []


class TestAFeluletKimondja:
    """A jegy: „A felület mondja ki magyarul, hogy a hatás a következő
    indításnál látszik, és hogy a mód bekapcsolva marad."""

    def test_bekapcsolaskor_uzen(self, controller, qt_app):
        uzenetek = []
        controller.tesztuzemUzenet.connect(uzenetek.append)
        controller.setTesztuzemEnabled(True)
        assert uzenetek, "a bekapcsolás néma maradt"
        szoveg = uzenetek[0]
        assert "következő" in szoveg.casefold()
        assert "bekapcsolva marad" in szoveg.casefold()

    def test_kikapcsolaskor_is_uzen(self, controller, qt_app):
        controller.setTesztuzemEnabled(True)
        uzenetek = []
        controller.tesztuzemUzenet.connect(uzenetek.append)
        controller.setTesztuzemEnabled(False)
        assert uzenetek and "kikapcsol" in uzenetek[0].casefold()


def _keszits_naplot(mappa: Path, nev: str = "indulas-20260827-204105.txt") -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    ut = mappa / nev
    ut.write_text("PicasaPy — tesztüzem: indulási napló\n", encoding="utf-8")
    return ut


class TestNaploAtadasa:
    """Egykattintásos átadás a NAS közös mappájába — semmi feltöltés."""

    @pytest.fixture
    def kornyezet(self, controller, tmp_path, monkeypatch):
        naplok = tmp_path / "cache" / "perf"
        _keszits_naplot(naplok)
        megosztas = tmp_path / "nas"
        megosztas.mkdir()
        vagolap: list[str] = []
        monkeypatch.setattr(modul, "_naplo_mappa", lambda: naplok)
        monkeypatch.setattr(modul, "_megosztas_gyokere", lambda: megosztas)
        monkeypatch.setattr(modul, "_vagolapra", vagolap.append)
        monkeypatch.setattr(
            modul, "_most", lambda: datetime(2026, 8, 27, 21, 0, 0)
        )
        return controller, megosztas, vagolap

    def test_a_naplo_a_rogzitett_almappaba_kerul(self, kornyezet, qt_app):
        controller, megosztas, _vagolap = kornyezet
        eredmeny = controller.tesztuzemNaploAtadasa()
        cel = megosztas / NAPLO_ALMAPPA / "picasapy-indulas-20260827-210000.txt"
        assert eredmeny == str(cel)
        assert cel.exists()

    def test_az_utvonal_a_vagolapra_kerul(self, kornyezet, qt_app):
        controller, megosztas, vagolap = kornyezet
        controller.tesztuzemNaploAtadasa()
        assert vagolap == [
            str(megosztas / NAPLO_ALMAPPA / "picasapy-indulas-20260827-210000.txt")
        ]

    def test_sikernel_magyarul_visszajelez(self, kornyezet, qt_app):
        controller, _megosztas, _vagolap = kornyezet
        uzenetek = []
        controller.tesztuzemUzenet.connect(uzenetek.append)
        controller.tesztuzemNaploAtadasa()
        assert uzenetek and "vágólap" in uzenetek[0].casefold()

    def test_nincs_naplo_eseten_ERTHETO_uzenet(
        self, controller, tmp_path, monkeypatch, qt_app
    ):
        monkeypatch.setattr(modul, "_naplo_mappa", lambda: tmp_path / "ures")
        uzenetek = []
        controller.tesztuzemUzenet.connect(uzenetek.append)
        assert controller.tesztuzemNaploAtadasa() == ""
        assert uzenetek and "napló" in uzenetek[0].casefold()


class TestMentesMaskentTartalek:
    """„Ha a megosztás nem érhető el, érthető magyar üzenet + Mentés
    másként…" — a néma sikertelenség a legrosszabb kimenet."""

    @pytest.fixture
    def elerhetetlen(self, controller, tmp_path, monkeypatch):
        naplok = tmp_path / "cache" / "perf"
        _keszits_naplot(naplok)
        monkeypatch.setattr(modul, "_naplo_mappa", lambda: naplok)
        monkeypatch.setattr(modul, "_megosztas_gyokere", lambda: None)
        monkeypatch.setattr(modul, "_vagolapra", lambda _szoveg: None)
        return controller

    def test_a_mentes_maskentet_keri(self, elerhetetlen, qt_app):
        kerések = []
        elerhetetlen.tesztuzemMentesMaskentKert.connect(kerések.append)
        assert elerhetetlen.tesztuzemNaploAtadasa() == ""
        assert kerések, "a megosztás hiányát némán elnyelte"
        assert "nem érhető el" in kerések[0].casefold()

    def test_a_tartalek_mentes_kiirja_a_naplot(self, elerhetetlen, tmp_path, qt_app):
        elerhetetlen.tesztuzemNaploAtadasa()
        cel = tmp_path / "asztal" / "naplo.txt"
        cel.parent.mkdir()

        assert elerhetetlen.tesztuzemNaploMentese(cel.as_uri()) is True

        assert cel.read_text(encoding="utf-8").startswith("PicasaPy")

    def test_a_tartalek_sima_utvonalat_is_elfogad(
        self, elerhetetlen, tmp_path, qt_app
    ):
        elerhetetlen.tesztuzemNaploAtadasa()
        cel = tmp_path / "naplo.txt"
        assert elerhetetlen.tesztuzemNaploMentese(str(cel)) is True
        assert cel.exists()

    def test_ures_celnal_hamis(self, elerhetetlen, qt_app):
        assert elerhetetlen.tesztuzemNaploMentese("") is False


class TestNemIrElesbe:
    """⚠️ A `/mnt/nas` ÉLES családi adat — a teszt SOHA nem írhat oda."""

    def test_a_megosztas_fogantyun_erkezik(self):
        """A produkciós útvonal EGYETLEN helyen dől el, és az cserélhető."""
        assert callable(modul._megosztas_gyokere)

    def test_a_nem_csatolt_megosztas_nem_szamit_elerhetonek(self, tmp_path):
        """A `/mnt/nas` felcsatolatlanul is létező, ÜRES könyvtár. Enélkül
        az ellenőrzés nélkül a napló némán a helyi lemezre kerülne, és a
        felhasználó azt hinné, hogy átadta."""
        assert modul._megosztas_gyokere(tmp_path, ismount=lambda _p: False) is None

    def test_a_csatolt_megosztas_elerheto(self, tmp_path):
        assert (
            modul._megosztas_gyokere(tmp_path, ismount=lambda _p: True) == tmp_path
        )
