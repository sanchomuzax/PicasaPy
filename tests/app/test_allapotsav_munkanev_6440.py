"""#6440: az alsó állapotsáv kiírja, min dolgozik a program (egységtesztek).

A névtábla, a szöveg összeállítása, a nyilvántartás munkanevei, a háttérszál
szálnevéből származó munkanév és a tartós kapcsoló. A látványt a
`tests/app/qml_functional/test_allapotsav_hattermunka_6440.py` méri.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

import picasapy.app
import picasapy.app.busy_registry as busy_registry_module
from picasapy.app.activity_status_mixin import (
    ACTIVITY_STATUS_KEY,
    ActivityStatusMixin,
    activity_status_enabled_from,
)
from picasapy.app.busy_activity import (
    ALAP_MUNKANEV,
    MUNKANEVEK,
    aktivitas_szoveg,
    munka_neve,
)
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry
from picasapy.app.worker_thread import BackgroundWorkerMixin
from tests.support.varakozas import var_feltetelre


@pytest.fixture(autouse=True)
def _kis_busy_idozitesek(monkeypatch):
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", 40)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", 60)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


def _beallitas(tmp_path: Path, nev: str = "beallitas.ini") -> QSettings:
    return QSettings(str(tmp_path / nev), QSettings.Format.IniFormat)


class TestMunkanevek:
    @pytest.mark.parametrize("szalnev", ["picasapy-export", "backup-run", "picasapy-webexport"])
    def test_a_szalnev_emberi_nevet_ad(self, szalnev):
        nev = munka_neve(szalnev)
        assert nev == MUNKANEVEK[szalnev]
        assert not nev.startswith(("picasapy-", "backup-"))

    def test_ismeretlen_vagy_hianyzo_nev_az_altalanos_szoveget_adja(self):
        assert munka_neve(None) == ALAP_MUNKANEV
        assert munka_neve("") == ALAP_MUNKANEV
        assert munka_neve("picasapy-nincs-ilyen") == ALAP_MUNKANEV

    def test_a_tabla_minden_neve_emberi(self):
        for szalnev, nev in MUNKANEVEK.items():
            assert nev, f"{szalnev}: üres munkanév"
            assert not nev.startswith(("picasapy-", "backup-")), szalnev

    def test_minden_hattermunka_szalneve_a_tablaban_van(self):
        """Őr: új `_start_background(name=...)` vagy `munka_neve(...)` hívás
        nem maradhat névtelen, mert különben az állapotsáv általános szöveget
        mutat rá, és senki nem veszi észre.

        Kivétel: a `submit(..., name=...)` sorok. Az indexíró-sor a futó
        szálat a SAJÁT `RUNNER_NAME`-jével indítja, a sorelem neve sosem jut el
        a nyilvántartásba, így az a név nem jelenik meg."""
        mappa = Path(picasapy.app.__file__).parent
        minta = re.compile(
            r'(?:name=|RUNNER_NAME = |munka_neve\()"((?:picasapy|backup)-[\w-]+)"'
        )
        hianyzo = []
        for fajl in sorted(mappa.glob("*.py")):
            sorok = fajl.read_text(encoding="utf-8").splitlines()
            if not any("_start_background(" in s or "munka_neve(" in s for s in sorok):
                continue
            for szam, sor in enumerate(sorok):
                elozo = sorok[szam - 1] if szam else ""
                if "submit(" in sor or "submit(" in elozo:
                    continue
                for nev in minta.findall(sor):
                    if nev not in MUNKANEVEK:
                        hianyzo.append(f"{fajl.name}:{szam + 1}: {nev}")
        assert not hianyzo, (
            "névtelen háttérmunka (adj nevet a busy_activity.py táblájába): "
            + ", ".join(hianyzo)
        )


class TestAllapotSzoveg:
    def test_egy_munka_neve_onmagaban(self):
        assert aktivitas_szoveg(("Exporting photos",)) == "Exporting photos"

    def test_tobb_munkanal_a_legfrissebb_es_a_tovabbi_darabszama(self):
        munkak = ("Exporting photos", "Creating backup image", "Finding similar photos")
        assert aktivitas_szoveg(munkak) == "Finding similar photos (+2 more)"

    def test_ures_lista_ures_szoveg(self):
        assert aktivitas_szoveg(()) == ""

    def test_a_nev_sajat_helyoldzoje_nem_torik_el(self):
        assert aktivitas_szoveg(("Exporting", "%1 %2")) == "%1 %2 (+1 more)"

    def test_nev_nelkuli_munka_az_altalanos_szoveget_kapja(self):
        assert aktivitas_szoveg(("",)) == ALAP_MUNKANEV


class TestNyilvantartasNevei:
    def test_a_legfrissebb_munka_a_vegen_all(self, qt_app):
        reg = get_app_busy_registry()
        elso = reg.begin("Exporting photos")
        masodik = reg.begin("Creating backup image")
        try:
            assert reg.aktiv_munkak() == ("Exporting photos", "Creating backup image")
        finally:
            reg.end(masodik)
            reg.end(elso)

    def test_a_befejezett_munka_neve_kiesik(self, qt_app):
        reg = get_app_busy_registry()
        elso = reg.begin("Exporting photos")
        masodik = reg.begin("Creating backup image")
        reg.end(elso)
        assert reg.aktiv_munkak() == ("Creating backup image",)
        reg.end(masodik)
        assert reg.aktiv_munkak() == ()

    def test_jegy_nelkuli_end_a_legregebbit_zarja(self, qt_app):
        reg = get_app_busy_registry()
        reg.begin("A")
        reg.begin("B")
        reg.end()
        assert reg.aktiv_munkak() == ("B",)
        assert reg.activeCount == 1
        reg.end()

    def test_ketszeri_zaras_nem_viszi_negativba_es_nem_zar_masikat(self, qt_app):
        reg = get_app_busy_registry()
        egy = reg.begin("A")
        ket = reg.begin("B")
        reg.end(egy)
        reg.end(egy)
        assert reg.aktiv_munkak() == ("B",)
        assert reg.activeCount == 1
        reg.end(ket)
        assert reg.activeCount == 0

    def test_a_nevvaltozas_jelzest_ad(self, qt_app):
        reg = get_app_busy_registry()
        jelzesek = []
        reg.activityChanged.connect(lambda: jelzesek.append(1))
        jegy = reg.begin("Exporting photos")
        reg.end(jegy)
        assert len(jelzesek) == 2


class TestSzalnevBolNev:
    def test_a_hattermunka_a_szalneve_alapjan_nevet_kap(self, qt_app):
        class Tulajdonos(BackgroundWorkerMixin):
            pass

        reg = get_app_busy_registry()
        indult = threading.Event()
        leall = threading.Event()

        def munka():
            indult.set()
            leall.wait(5)

        szal = Tulajdonos()._start_background(munka, name="picasapy-export")
        assert indult.wait(5)
        assert var_feltetelre(
            qt_app, lambda: reg.aktiv_munkak() == ("Exporting photos",), 3.0
        ), "a háttérmunka nem a szálneve szerinti nevet kapta"
        leall.set()
        szal.join(5)
        assert var_feltetelre(qt_app, lambda: reg.aktiv_munkak() == (), 3.0)


class _Vezerlo(ActivityStatusMixin, QObject):
    """A mixin és a `_get_settings` egy QObject-vezérlőn, mint az AppController-en."""

    def __init__(self, settings: QSettings) -> None:
        super().__init__()
        self._settings = settings
        self._init_activity_status()

    def _get_settings(self) -> QSettings:
        return self._settings


class TestTartosKapcsolo:
    def test_alapertelmezes_bekapcsolt(self, tmp_path):
        assert activity_status_enabled_from(_beallitas(tmp_path)) is True

    @pytest.mark.parametrize(
        ("ertek", "varhato"),
        [("false", False), ("true", True), ("0", False), ("1", True), (False, False), (True, True)],
    )
    def test_az_ertek_felismerese(self, tmp_path, ertek, varhato):
        settings = _beallitas(tmp_path)
        settings.setValue(ACTIVITY_STATUS_KEY, ertek)
        settings.sync()
        assert activity_status_enabled_from(settings) is varhato

    def test_a_kikapcsolas_tartosan_mentodik(self, qt_app, tmp_path):
        fajl = tmp_path / "mentes.ini"
        vezerlo = _Vezerlo(QSettings(str(fajl), QSettings.Format.IniFormat))
        vezerlo.setStatusActivityEnabled(False)
        ujra = QSettings(str(fajl), QSettings.Format.IniFormat)
        assert activity_status_enabled_from(ujra) is False
        assert _Vezerlo(ujra).statusActivityEnabled is False

    def test_a_valtas_visszakapcsol(self, qt_app, tmp_path):
        vezerlo = _Vezerlo(_beallitas(tmp_path))
        vezerlo.toggleStatusActivity()
        assert vezerlo.statusActivityEnabled is False
        vezerlo.toggleStatusActivity()
        assert vezerlo.statusActivityEnabled is True


class TestSzovegAKapcsolotol:
    def test_kikapcsolva_nincs_munkaszoveg_akkor_sem_ha_fut_a_munka(self, qt_app, tmp_path):
        vezerlo = _Vezerlo(_beallitas(tmp_path))
        vezerlo.setStatusActivityEnabled(False)
        reg = get_app_busy_registry()
        jegy = reg.begin("Exporting photos")
        try:
            assert var_feltetelre(qt_app, lambda: reg.visible, 3.0)
            assert vezerlo.statusActivityText == ""
        finally:
            reg.end(jegy)

    def test_bekapcsolva_a_lathato_munka_neve_a_szoveg(self, qt_app, tmp_path):
        vezerlo = _Vezerlo(_beallitas(tmp_path))
        reg = get_app_busy_registry()
        jegy = reg.begin("Exporting photos")
        try:
            assert var_feltetelre(qt_app, lambda: reg.visible, 3.0)
            assert vezerlo.statusActivityText == "Exporting photos"
        finally:
            reg.end(jegy)
        assert var_feltetelre(qt_app, lambda: vezerlo.statusActivityText == "", 3.0)

    def test_a_rovid_munka_nem_ad_szoveget(self, qt_app, tmp_path):
        vezerlo = _Vezerlo(_beallitas(tmp_path))
        reg = get_app_busy_registry()
        jegy = reg.begin("Exporting photos")
        reg.end(jegy)
        qt_app.processEvents()
        assert vezerlo.statusActivityText == ""
