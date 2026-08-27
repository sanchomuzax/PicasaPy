"""A megjelenítési mód a bélyegkép-úton — szerződések (#1596).

A rács KIRAJZOLT képpontjait a
`tests/app/qml_functional/test_megjelenitesi_mod_a_racson_1596.py` méri. Ez
a fájl a mögötte lévő három szerződést őrzi, motor nélkül:

1. **URL-cimke** — a `models._thumb_url()` és a
   `display_mode_paint.display_mode_from_thumb_id()` ugyanazt a nyelvet
   beszéli, és a képpontot nem mozdító módokra az URL bájtra a mód
   bevezetése előtti.
2. **Gyorstár-tisztaság** — a mód SEM a lemezes bélyegképbe, SEM a szűrt
   bélyegképek memóriarekeszébe (`_FilteredThumbMemo`) nem éghet bele. Ez a
   #1576-ban eldöntött szerződés: a mód megjelenítési átalakító, nem a
   bélyegkép tartalma. Ha beleégne, a mód kikapcsolása után is festve
   maradna a kép, és a webexport/kollázs is a képernyő figyelmeztető
   színét vinné tovább.
3. **Rács-modell** — a mód váltása lépteti a `revision`-t (ez hajtja a
   `LightboxFeed` `itemAt()`-mintáját), azonos érték viszont NEM.

## A várt színek KIÍRT LITERÁLOK

A spec egész-aritmetikájából kiszámolva, nem a termék konstansaiból
olvasva (`docs/specs/picasa-megjelenitesi-modok.md`):
`200·220>>8 = 171` (projektor), `200·246>>8 = 192` (LCD).
"""

from __future__ import annotations

import hashlib

import cv2
import numpy as np
import pytest
from PySide6.QtGui import QImage

from picasapy.app.display_mode_paint import (
    apply_display_mode_to_qimage,
    display_mode_from_thumb_id,
    display_mode_url_suffix,
)
from picasapy.app.models import PhotoGridModel, _thumb_url
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.edit.session import EditSession
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.ini.rect64 import Rect64
from picasapy.thumbs import ThumbnailCache

#: A próbakép egyenletes tónusa — egyenletes, mert a bélyegkép útja
#: átméretez és JPEG-be kódol; így a lánc BITRE pontos (mérve, #1596).
HATTER = (200, 200, 200)
#: `200·220>>8` — KIÍRVA, nem a `PROJECTOR_MULTIPLIER`-ből.
PROJEKTOROS = (171, 171, 171)
#: `200·246>>8` — KIÍRVA, nem az `LCD_MULTIPLIER`-ből.
LCD_S = (192, 192, 192)


def _konyvtar(tmp_path, ini_body: str | None = None):
    lib = tmp_path / "kepek"
    lib.mkdir()
    kep = np.full((160, 320, 3), HATTER[0], dtype=np.uint8)
    assert cv2.imwrite(
        str(lib / "a.jpg"), kep, [int(cv2.IMWRITE_JPEG_QUALITY), 100]
    )
    if ini_body is not None:
        (lib / ".picasa.ini").write_text(ini_body, encoding="utf-8")
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        return lib, photos_in_folder(conn, lib)


def _crop_ini(nev: str) -> str:
    """Egy `filters=` lánc, hogy a szűrt-bélyegkép MEMÓRIAREKESZE éljen."""
    value = (
        EditSession()
        .append_crop(Rect64(left=0.0, top=0.0, right=0.5, bottom=1.0))
        .to_value()
    )
    return f"[{nev}]\nfilters={value}\n"


def _provider(tmp_path, records):
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=128))
    provider.register_photos(records)
    return provider


def _szinek(image: QImage) -> set[tuple[int, int, int]]:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    raw = raw.reshape((height, converted.bytesPerLine()))
    tomb = raw[:, : width * 3].reshape((height, width, 3))
    return {tuple(int(c) for c in p) for p in np.unique(tomb.reshape(-1, 3), axis=0)}


def _ujjlenyomat(gyokér) -> dict:
    return {
        str(f.relative_to(gyokér)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(gyokér.rglob("*"))
        if f.is_file()
    }


class TestUrlCimke:
    """A cimkét író és olvasó fél ugyanazt a nyelvet beszéli."""

    def test_a_kepponot_mozdito_mod_cimket_kap(self, tmp_path):
        _lib, records = _konyvtar(tmp_path)
        url = _thumb_url(records[0], "projector")
        assert url.endswith("&d=projector"), url

    @pytest.mark.parametrize(
        "mod", ["", "auto", "normal", "dither16", "rdesk", "mac"]
    )
    def test_a_no_op_modok_nem_valtoztatjak_az_url_t(self, tmp_path, mod):
        """Az öt no-op mód és az alaphelyzet: az URL bájtra a régi.

        A `sepia` és a `bw` a #1657 óta KIKERÜLT innen: mozdítanak
        képpontot, tehát KELL nekik cimke — különben a Qt URL-kulcsú
        gyorstára a régi képpontokat tartaná a rácson.

        Ez nem kozmetika. Cimkével minden módváltás ELDOBNÁ a Qt
        URL-kulcsú bélyegkép-gyorstárát, és a rács hatás nélkül
        újrarenderelne mindent.
        """
        _lib, records = _konyvtar(tmp_path)
        assert _thumb_url(records[0], mod) == _thumb_url(records[0])

    @pytest.mark.parametrize(
        "mod", ["projector", "lcd", "linear", "overflow", "sepia", "bw"]
    )
    def test_a_cimke_korbejar(self, tmp_path, mod):
        _lib, records = _konyvtar(tmp_path)
        url = _thumb_url(records[0], mod)
        # a szolgáltató az `image://thumbs/` előtag NÉLKÜLI részt kapja
        azonosito = url.split("image://thumbs/", 1)[1]
        assert display_mode_from_thumb_id(azonosito) == mod

    def test_cimke_nelkuli_azonositobol_ures_mod(self, tmp_path):
        _lib, records = _konyvtar(tmp_path)
        azonosito = _thumb_url(records[0]).split("image://thumbs/", 1)[1]
        assert display_mode_from_thumb_id(azonosito) == ""

    def test_a_puszta_azonosito_is_ertelmezheto(self):
        """Lekérdezés nélküli id (pl. `face_scan_controller`) nem dől el."""
        assert display_mode_from_thumb_id("42") == ""
        assert display_mode_from_thumb_id("") == ""

    def test_ismeretlen_mod_nem_kap_cimket(self):
        assert display_mode_url_suffix("nincs-ilyen-mod") == ""


class TestSzolgaltato:
    """A cimkézett kérés festett, a cimkétlen festetlen képet ad."""

    def test_a_cimke_nelkuli_keres_valtozatlan(self, qt_app, tmp_path):
        _lib, records = _konyvtar(tmp_path)
        provider = _provider(tmp_path, records)
        azonosito = _thumb_url(records[0]).split("image://thumbs/", 1)[1]
        assert _szinek(provider.requestImage(azonosito, None, None)) == {HATTER}

    @pytest.mark.parametrize(
        ("mod", "vart"), [("projector", PROJEKTOROS), ("lcd", LCD_S)]
    )
    def test_a_cimkezett_keres_festett(self, qt_app, tmp_path, mod, vart):
        _lib, records = _konyvtar(tmp_path)
        provider = _provider(tmp_path, records)
        azonosito = _thumb_url(records[0], mod).split("image://thumbs/", 1)[1]
        assert _szinek(provider.requestImage(azonosito, None, None)) == {vart}


class TestGyorstarTisztasag:
    """A mód nem éghet bele SEM a lemezes, SEM a memóriabeli rekeszbe."""

    def test_a_lemezes_belyegkep_bajtra_azonos_marad(self, qt_app, tmp_path):
        _lib, records = _konyvtar(tmp_path)
        provider = _provider(tmp_path, records)
        alap = _thumb_url(records[0]).split("image://thumbs/", 1)[1]
        provider.requestImage(alap, None, None)

        gyorstar = tmp_path / "th"
        elotte = _ujjlenyomat(gyorstar)
        assert elotte, "a próba előfeltétele nem áll fenn: üres a gyorstár"

        festett = _thumb_url(records[0], "overflow").split("image://thumbs/", 1)[1]
        provider.requestImage(festett, None, None)

        assert _ujjlenyomat(gyorstar) == elotte, (
            "a megjelenítési mód BELEÉGETT a lemezen tárolt bélyegképbe"
        )

    def test_a_festett_keres_utan_a_cimketlen_eredeti(self, qt_app, tmp_path):
        """A sorrend a lényeg: előbb a festett kérés, azután a rendes."""
        _lib, records = _konyvtar(tmp_path)
        provider = _provider(tmp_path, records)
        festett = _thumb_url(records[0], "projector").split("image://thumbs/", 1)[1]
        assert _szinek(provider.requestImage(festett, None, None)) == {PROJEKTOROS}

        alap = _thumb_url(records[0]).split("image://thumbs/", 1)[1]
        assert _szinek(provider.requestImage(alap, None, None)) == {HATTER}, (
            "a festett kérés megmérgezte a gyorstárat — a mód kikapcsolása "
            "után is festve maradt a bélyegkép"
        )

    def test_a_szurt_belyegkep_memoriarekesze_tiszta_marad(
        self, qt_app, tmp_path
    ):
        """`filters=` lánccal a `_FilteredThumbMemo` is játszik (#144).

        Ez külön út: a szűrt bélyegkép a memóriarekeszből jön vissza, a
        lemez érintése nélkül. Ha a festés a rekeszbe kerülne, a mód
        kikapcsolása után is festve maradna — a lemezes őr ezt NEM fogná
        meg, mert a lemezhez hozzá sem nyúlunk.
        """
        _lib, records = _konyvtar(tmp_path, ini_body=_crop_ini("a.jpg"))
        assert records[0].filters, (
            "a próba előfeltétele nem áll fenn: nincs filters-lánc, tehát "
            "a memóriarekesz nem is épül fel"
        )
        provider = _provider(tmp_path, records)
        festett = _thumb_url(records[0], "lcd").split("image://thumbs/", 1)[1]
        assert _szinek(provider.requestImage(festett, None, None)) == {LCD_S}

        alap = _thumb_url(records[0]).split("image://thumbs/", 1)[1]
        assert _szinek(provider.requestImage(alap, None, None)) == {HATTER}, (
            "a festés a szűrt bélyegképek MEMÓRIAREKESZÉBE égett bele"
        )

    def test_az_atfestes_nem_irja_at_a_bemenetet(self, qt_app):
        """A közvetlen átfestő sem mutálhat: a hívó gyorstárból ad képet."""
        forras = QImage(4, 4, QImage.Format.Format_RGB32)
        forras.fill(0xFFC8C8C8)  # (200, 200, 200)
        eredmeny = apply_display_mode_to_qimage(forras, "projector")
        assert _szinek(eredmeny) == {PROJEKTOROS}
        assert _szinek(forras) == {HATTER}, "az átfestő HELYBEN írta át a bemenetet"


class TestRacsModell:
    """A modell a mód váltásakor újraköti a látható cellákat (#1596)."""

    def test_a_modvaltas_lepteti_a_revisiont(self, qt_app, tmp_path):
        _lib, records = _konyvtar(tmp_path)
        model = PhotoGridModel()
        model.set_photos(records)
        elotte = model.revision

        model.set_display_mode("projector")

        assert model.revision > elotte, (
            "a mód váltása nem léptette a `revision`-t — a feed "
            "`itemAt()`-mintája nem értékelődik újra, a rács nem frissül"
        )
        assert model.itemAt(0)["thumbUrl"].endswith("&d=projector")

    def test_azonos_mod_nem_lepteti_a_revisiont(self, qt_app, tmp_path):
        _lib, records = _konyvtar(tmp_path)
        model = PhotoGridModel()
        model.set_photos(records)
        model.set_display_mode("projector")
        elotte = model.revision

        model.set_display_mode("projector")

        assert model.revision == elotte, (
            "azonos módra is újrakötött a rács — minden látható bélyegkép "
            "fölöslegesen újrarenderelődne"
        )

    def test_a_modbol_kilepve_visszaall_az_eredeti_url(self, qt_app, tmp_path):
        _lib, records = _konyvtar(tmp_path)
        model = PhotoGridModel()
        model.set_photos(records)
        eredeti = model.itemAt(0)["thumbUrl"]

        model.set_display_mode("overflow")
        assert model.itemAt(0)["thumbUrl"] != eredeti

        model.set_display_mode("normal")
        assert model.itemAt(0)["thumbUrl"] == eredeti, (
            "a módból kilépve nem az EREDETI URL tér vissza — a Qt "
            "gyorstárában lévő festetlen kép nem használódna újra"
        )
