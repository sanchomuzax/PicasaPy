"""#1838: a Picasából örökölt vágáspontok a lejátszásban.

A vágáspontok formátuma mérve van (`ini/movie_trim.py`); ez a lap a
**bekötést** méri: a modell ezredmásodpercre váltva adja őket, a néző átadja
a lejátszónak, és a lejátszó a szakaszra szorítja magát.

⚠️ **Amit NEM mér:** a tényleges lejátszást. A CI-n nincs videó-dekódolás, és
egy `MediaPlayer` valódi pozícióját gépi teszt itt nem tudja kimérni — a lap
a kötéseket és a határértékeket állítja, a modul-őr pedig a számokat.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_NEZO = (_QML / "PhotoViewer.qml").read_text(encoding="utf-8")
_LEJATSZO = (_QML / "VideoPlayerView.qml").read_text(encoding="utf-8")

#: a tulajdonos könyvtárából mért lánc (a `movieend` áll elöl)
VALODI_LANC = "movieend=b40728fd;moviestart=80252d;"


def _video(nev: str = "M4V01962.MP4", filters: str = ""):
    from picasapy.index import PhotoRecord

    return PhotoRecord(
        id=7,
        folder_path="/videok",
        name=nev,
        kind="video",
        size=1000,
        mtime_ns=5,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=filters or None,
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
    )


class TestAModell:
    def _modell(self, *records):
        from picasapy.app.models import PhotoGridModel

        modell = PhotoGridModel()
        modell.set_photos(records)
        return modell

    def test_a_VALODI_lanc_mindket_pontja_ms_ben(self):
        modell = self._modell(_video(filters=VALODI_LANC))
        assert modell.movieTrimAt(0) == {"start": 839, "end": 302_036}

    def test_a_HIANYZO_oldal_minusz_egy(self):
        """A −1 más, mint a 0: a 0 a nulla pontra állított kezdés lenne."""
        modell = self._modell(_video(filters="moviestart=bf0df826;"))
        assert modell.movieTrimAt(0) == {"start": 320_536, "end": -1}

    def test_vagas_nelkuli_video(self):
        modell = self._modell(_video(filters="bw=1;"))
        assert modell.movieTrimAt(0) == {"start": -1, "end": -1}

    def test_filters_NELKULI_video(self):
        modell = self._modell(_video())
        assert modell.movieTrimAt(0) == {"start": -1, "end": -1}

    @pytest.mark.parametrize("sor", [-1, 1, 99])
    def test_ervenytelen_sor_nem_dob(self, sor):
        modell = self._modell(_video(filters=VALODI_LANC))
        assert modell.movieTrimAt(sor) == {"start": -1, "end": -1}


class TestANezoAtadja:
    def test_mindket_pont_kotese_megvan(self):
        assert 'property: "trimStartMs"' in _NEZO
        assert 'property: "trimEndMs"' in _NEZO

    def test_a_MODELLBOL_jon(self):
        assert "movieTrimAt(" in _NEZO

    def test_a_kotes_csak_VIDEONAL_el(self):
        """A fotó-nézetet nem érintheti — a Loader is csak videónál aktív."""
        kezd = _NEZO.index('property: "trimStartMs"')
        veg = _NEZO.index('property: "trimEndMs"', kezd)
        assert "viewer.isCurrentVideo" in _NEZO[kezd:veg]


class TestALejatszo:
    def test_a_ket_pont_property(self):
        assert "property int trimStartMs: -1" in _LEJATSZO
        assert "property int trimEndMs: -1" in _LEJATSZO

    def test_a_kezdopontra_a_HOSSZ_ismereteben_ugrik(self):
        """A `position` írása üres médián elveszik — a hossz a kapu."""
        kezd = _LEJATSZO.index("function seekToTrimStart()")
        blokk = _LEJATSZO[kezd : _LEJATSZO.index("}", _LEJATSZO.index("{", kezd))]
        assert "media.duration > 0" in blokk
        assert "onDurationChanged" in _LEJATSZO

    def test_a_kimeneti_ponton_MEGALL(self):
        assert "player.trimEndMs >= 0 && media.position > player.trimEndMs" in _LEJATSZO
        assert "media.pause()" in _LEJATSZO

    def test_a_csuszka_a_VAGOTT_szakaszra_szorul(self):
        kezd = _LEJATSZO.index('objectName: "videoSeekSlider"')
        veg = _LEJATSZO.index('objectName: "videoTimeLabel"', kezd)
        blokk = _LEJATSZO[kezd:veg]
        assert "from: player.playFromMs" in blokk
        assert "player.playToMs" in blokk

    def test_vagas_NELKUL_a_fajl_hatara_marad(self):
        """A −1 oldalon nincs szűkítés: a szakasz a fájl eleje/vége."""
        assert "playFromMs: Math.max(0, trimStartMs)" in _LEJATSZO
        assert "trimEndMs >= 0" in _LEJATSZO
        assert "Math.max(1, media.duration)" in _LEJATSZO

    def test_a_hatokort_a_kod_KIMONDJA(self):
        """A vágás ma csak a lejátszásra hat — a fájlt nem alakítjuk át, és a
        pontokat a felületen még nem lehet állítani. Ha ez nincs kimondva, a
        következő olvasó kész funkciónak veszi."""
        assert "CSAK a lejátszásra hat" in _LEJATSZO
