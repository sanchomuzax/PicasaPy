"""#1838: a videó vágáspontjainak MENTÉSE (`setin` / `setout` / `reset_trim`).

A formátum mérve van (`ini/movie_trim.py`: `moviestart`/`movieend`, 64 bites
kisbetűs hex, 100 ns-os DirectShow `REFERENCE_TIME`), az olvasás és a
lejátszás-szorítás pedig a #1838 korábbi köreiben elkészült
(`test_videovagas_lejatszas_1838.py`). Ez a lap a hiányzó felet méri: a
vágáspontok **visszaírását** a `.picasa.ini` `filters=` láncába.

Amit a lap kikötése szerint tudni kell:

* a lánc többi tokenje **érintetlen** marad (round-trip elv),
* a `-1` azt jelenti, hogy azon az oldalon **nincs** vágás — a token kimarad,
  nem 0-ra áll,
* a Picasából örökölt érték **bitre azonosan** kerül vissza, ha nem nyúlunk
  hozzá,
* az írás bukása **nem lehet néma** (#2506 mintája).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject

from picasapy.index import PhotoRecord

#: a tulajdonos könyvtárából mért lánc (a `movieend` áll elöl)
VALODI_LANC = "movieend=b40728fd;moviestart=80252d;"


def _video(mappa: Path, nev: str = "M4V01962.MP4", filters: str = "") -> PhotoRecord:
    return PhotoRecord(
        id=7,
        folder_path=str(mappa),
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


class _Proba(QObject):
    """A mixin önmagában — a teljes AppController felépítése nélkül.

    A keverék két dolgot vár a gazdájától: a `photos` modellt és az írási
    hiba jelentését. Mindkettő itt a legszűkebb alakjában áll.
    """

    def __init__(self, modell):
        super().__init__()
        self.photos = modell
        self.irasi_hibak: list[str] = []

    def jelentsdAzIrasiHibat(self, hiba) -> None:  # noqa: N802 — QML-stílus
        self.irasi_hibak.append(str(hiba))


@pytest.fixture
def keret(qt_app, tmp_path):
    from picasapy.app.models import PhotoGridModel
    from picasapy.app.movie_trim_controller import MovieTrimMixin

    class _Vezerlo(MovieTrimMixin, _Proba):
        pass

    def epit(filters: str = ""):
        modell = PhotoGridModel()
        modell.set_photos((_video(tmp_path, filters=filters),))
        (tmp_path / "M4V01962.MP4").write_bytes(b"nem valodi video")
        return _Vezerlo(modell), modell

    return epit


def _ini_filters(mappa: Path, szakasz: str = "M4V01962.MP4") -> str | None:
    from picasapy.ini import load_document
    from picasapy.scanner import PICASA_INI_NAME

    section = load_document(mappa / PICASA_INI_NAME).section(szakasz)
    return section.get("filters") if section else None


class TestMentes:
    def test_mindket_pont_a_MERT_alakban(self, keret, tmp_path):
        """ÚJ vágásnál az ms-ből számolt tick megy ki, kisbetűs hexként.

        839 ms → 8 390 000 tick → `800570`; 302 036 ms → `b4070940`. (Az
        örökölt `80252d` ettől eltér: annak 839,8125 ms-os, ms-ban nem
        kifejezhető pontossága van — ld. a lenti round-trip tesztet.)
        """
        vezerlo, _ = keret()
        vezerlo.setMovieTrim(0, 839, 302_036)
        lanc = _ini_filters(tmp_path)
        assert lanc is not None
        assert "moviestart=800570" in lanc
        assert "movieend=b4070940" in lanc

    def test_a_MINUSZ_EGY_oldal_kimarad(self, keret, tmp_path):
        vezerlo, _ = keret()
        vezerlo.setMovieTrim(0, 839, -1)
        lanc = _ini_filters(tmp_path) or ""
        assert "moviestart=800570" in lanc
        assert "movieend" not in lanc, "a −1 oldalra NEM kerül token"

    def test_a_TOBBI_token_erintetlen(self, keret, tmp_path):
        vezerlo, _ = keret("bw=1;autolight=1;")
        vezerlo.setMovieTrim(0, 839, -1)
        lanc = _ini_filters(tmp_path) or ""
        assert "bw=1" in lanc and "autolight=1" in lanc

    def test_a_MODELL_sora_is_frissul(self, keret):
        """A néző a modellből olvas — enélkül a felület a régit mutatná."""
        vezerlo, modell = keret()
        vezerlo.setMovieTrim(0, 839, 302_036)
        assert modell.movieTrimAt(0) == {"start": 839, "end": 302_036}

    def test_a_VISSZAALLITAS_kiveszi_mindkettot(self, keret, tmp_path):
        vezerlo, modell = keret(VALODI_LANC + "bw=1;")
        vezerlo.resetMovieTrim(0)
        lanc = _ini_filters(tmp_path) or ""
        assert "moviestart" not in lanc and "movieend" not in lanc
        assert "bw=1" in lanc, "a visszaállítás csak a vágást veszi ki"
        assert modell.movieTrimAt(0) == {"start": -1, "end": -1}

    def test_az_OROKOLT_ertek_bitre_azonos_ha_nem_nyulunk_hozza(self, keret, tmp_path):
        """Round-trip: ugyanazt az ms-értéket visszaírva a hex sem változik."""
        vezerlo, modell = keret(VALODI_LANC)
        elozo = modell.movieTrimAt(0)
        vezerlo.setMovieTrim(0, elozo["start"], elozo["end"])
        lanc = _ini_filters(tmp_path) or ""
        assert "moviestart=80252d" in lanc
        assert "movieend=b40728fd" in lanc

    @pytest.mark.parametrize("sor", [-1, 1, 99])
    def test_ervenytelen_sor_nem_dob_es_nem_ir(self, keret, tmp_path, sor):
        vezerlo, _ = keret()
        vezerlo.setMovieTrim(sor, 839, -1)
        vezerlo.resetMovieTrim(sor)
        from picasapy.scanner import PICASA_INI_NAME

        assert not (tmp_path / PICASA_INI_NAME).exists()

    def test_a_NEM_VIDEO_sorra_nem_ir(self, qt_app, tmp_path):
        """A vágás videó-fogalom; fotóra hívva ne nyúljunk az inihez."""
        from picasapy.app.models import PhotoGridModel
        from picasapy.app.movie_trim_controller import MovieTrimMixin
        from picasapy.scanner import PICASA_INI_NAME

        class _Vezerlo(MovieTrimMixin, _Proba):
            pass

        foto = _video(tmp_path, nev="IMG_1.JPG")
        modell = PhotoGridModel()
        modell.set_photos((PhotoRecord(**{**foto.__dict__, "kind": "image"}),))
        _Vezerlo(modell).setMovieTrim(0, 839, -1)
        assert not (tmp_path / PICASA_INI_NAME).exists()


class TestHibaut:
    def test_az_irasi_hiba_NEM_nema(self, keret, tmp_path, monkeypatch):
        """#2506 mintája: a kivétel a jelentő csatornán megy ki."""
        vezerlo, modell = keret()

        def _bukik(*args, **kwargs):
            raise OSError("írásvédett mappa")

        monkeypatch.setattr(
            "picasapy.app.movie_trim_controller.update_document", _bukik
        )
        vezerlo.setMovieTrim(0, 839, -1)
        assert vezerlo.irasi_hibak, "az írási hiba némán elveszett"
        assert modell.movieTrimAt(0) == {"start": -1, "end": -1}, (
            "bukott írás után a modell NEM mutathatja a mentettet"
        )
