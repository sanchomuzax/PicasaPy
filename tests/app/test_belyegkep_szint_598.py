"""#598: a bélyegkép-szint bekötése — URL, modell, vezérlő, felület.

A szint **az URL-ben utazik** (`&sz=<px>`), nem a szolgáltató állapotában:
a Qt URL szerint gyorstárazza a kész képet, tehát ha a szint kívülről jönne,
egy szintváltás után a régi képpontok maradnának — más méretben. Ugyanaz az
elv, amit a megjelenítési mód (`&d=`) őre már rögzít.

A cimke **csak a nem-felső szinten** kerül ki, hogy a mai URL-ek bájtra
változatlanok legyenek, és a meglévő lemez-gyorsítótár érvényes maradjon.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from picasapy.app.models import _thumb_url
from picasapy.app.thumb_level_url import szint_from_thumb_id
from picasapy.index.queries import PhotoRecord

_QML = Path(picasapy.app.__file__).parent / "qml"
_FUL = (_QML / "PicasaPy" / "OptionsTabGeneral.qml").read_text(encoding="utf-8")
_MAIN = (_QML / "Main.qml").read_text(encoding="utf-8")


def _foto(**extra) -> PhotoRecord:
    alap = dict(
        id=7,
        folder_path="/k",
        name="a.jpg",
        kind="photo",
        size=22,
        mtime_ns=11,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
    )
    alap.update(extra)
    return PhotoRecord(**alap)


class TestAzUrlCimke:
    def test_szint_nelkul_az_URL_valtozatlan(self):
        """A #598 előtti alak — a meglévő Qt- és lemez-gyorstár érvényes."""
        assert "sz=" not in _thumb_url(_foto(), "")

    def test_a_szint_bekerul_az_URLbe(self):
        assert "&sz=144" in _thumb_url(_foto(), "", 144)

    @pytest.mark.parametrize("px", [72, 144, 256])
    def test_a_cimke_visszaolvasható(self, px):
        assert szint_from_thumb_id(_thumb_url(_foto(), "", px)) == px

    def test_cimke_nelkul_None(self):
        assert szint_from_thumb_id(_thumb_url(_foto(), "")) is None

    @pytest.mark.parametrize(
        "rossz", ["", "7?sz=", "7?sz=abc", "7?sz=0", "7?sz=-9", "7"]
    )
    def test_a_hibas_cimke_a_FELSO_szintre_esik_vissza(self, rossz):
        """A felső szint minden cellára elég (kicsinyítéssel), tehát rossz
        cimkéből sosem lesz homályos kép."""
        assert szint_from_thumb_id(rossz) is None

    def test_a_szint_es_a_MOD_megfer_egymas_mellett(self):
        url = _thumb_url(_foto(), "sepia", 72)
        assert "&sz=72" in url and "&d=sepia" in url
        assert szint_from_thumb_id(url) == 72


class TestATarKapcsolata:
    def test_a_tar_dönti_el_a_szintet_a_cellabol(self, tmp_path):
        from picasapy.thumbs import ThumbnailCache

        tar = ThumbnailCache(tmp_path, size=256)
        assert tar.level_for(48) == 72
        assert tar.level_for(120) == 144
        assert tar.level_for(200) == 256


class TestAModell:
    def _modell(self):
        from picasapy.app.models import PhotoGridModel

        return PhotoGridModel()

    def test_a_kezdoallapot_a_FELSO_szint(self):
        modell = self._modell()
        modell.set_photos((_foto(),))
        assert "sz=" not in modell.thumbUrlAt(0)

    def test_a_szint_beallitasa_atvezet_az_URLre(self):
        modell = self._modell()
        modell.set_photos((_foto(),))
        modell.set_thumb_level(72)
        assert "&sz=72" in modell.thumbUrlAt(0)

    def test_UGYANARRA_az_ertekre_nem_jelez(self):
        """A rács újrakötése minden látható bélyegkép újrakérése — a csúszka
        húzása ezt fokozatonként nem válthatja ki."""
        modell = self._modell()
        modell.set_photos((_foto(),))
        modell.set_thumb_level(144)
        elozo = modell.revision
        modell.set_thumb_level(144)
        assert modell.revision == elozo

    def test_szintvaltaskor_JELEZ(self):
        modell = self._modell()
        modell.set_photos((_foto(),))
        modell.set_thumb_level(144)
        elozo = modell.revision
        modell.set_thumb_level(72)
        assert modell.revision > elozo


class TestAFelulet:
    def test_a_racs_atadja_a_cellameretet(self):
        assert "controller.setThumbCellSize(thumbSize)" in _MAIN
        #: az induló fokozat is, különben a rács a felső szintről indulna
        assert "controller.setThumbCellSize(window.thumbSize)" in _MAIN

    def test_a_gyorsitotar_urito_gomb_ELO(self):
        kezd = _FUL.index('objectName: "optionsClearCacheButton"')
        blokk = _FUL[kezd : kezd + 500]
        assert "enabled: false" not in blokk
        assert "clearCacheConfirm.ask" in blokk

    def test_az_urites_MEGERŐSITEST_ker(self):
        """A felirat hármas pontja azt ígéri, hogy kérdez."""
        assert 'text: qsTr("Clear Cache...")' in _FUL
        assert "ConfirmDialog {" in _FUL
        assert "controller.clearThumbnailCache()" in _FUL

    def test_a_komment_sem_hazudik_a_hianyzo_funkciorol(self):
        """A fájl feje korábban a gyorsítótár-törlés HIÁNYÁT sorolta fel."""
        assert "nincs\n// gyorsítótár-törlés funkció" not in _FUL
        assert "gyorsítótár-törlés funkció" not in _FUL
