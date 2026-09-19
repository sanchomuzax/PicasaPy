"""#3132 — a db3-import felhasználói kiváltója: a vezérlő.

A #3002/#3184 óta a MAG kész (`pmpimport.db3_atvetel.rekordokat_atvesz`), de
`src/` alól semmi nem hívta: a felhasználó nem tudta elindítani. A tulajdonos
2026-09-18-án az **A** megoldást választotta — menüpont (`Eszközök ▸ Import a
Picasából…`), tehát KÉRÉSRE fut, és megismételhető.

Ez a fájl a vezérlőt méri: mit csinál, ha nincs telepítés, ha van, és mit
jelent vissza a felhasználónak. A db3 olvasását és az átvételt beadott
függvényekkel helyettesítjük — a magnak saját próbái vannak
(`tests/pmpimport/`), ezt nem kell újra lemérni.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.picasa_import_controller import PicasaImportController
from picasapy.pmpimport.db3_atvetel import AtvetelJelentes
from picasapy.scanner.discovery import PicasaInstallation


def _telepites(db3: Path | None) -> PicasaInstallation:
    return PicasaInstallation(
        label="próba",
        picasa2_dir=db3,
        picasa2albums_dir=None,
        watched_folders_file=None,
    )


class _Fogo:
    """Jelzés-fogó: a kibocsátott értékeket sorrendben gyűjti."""

    def __init__(self) -> None:
        self.tetelek: list[tuple] = []

    def __call__(self, *args) -> None:
        self.tetelek.append(args)


@pytest.fixture
def vezerlo_gyar(qt_app):
    keszult: list[PicasaImportController] = []

    def gyart(*, telepitesek, rekordok=(), jelentes=None, hiba=None):
        def felderito():
            return tuple(telepitesek)

        def olvaso(db3_dir, remapper):
            if hiba is not None:
                raise hiba
            return tuple(rekordok)

        def atvevo(rek, *, backup=True):
            return jelentes if jelentes is not None else AtvetelJelentes()

        v = PicasaImportController(felderito=felderito, olvaso=olvaso, atvevo=atvevo)
        keszult.append(v)
        return v

    yield gyart
    for v in keszult:
        v.waitForBackgroundWorkers(5.0)


def _lefut(vezerlo, qt_app) -> None:
    vezerlo.startImport()
    assert vezerlo.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()


class TestHaNincsMitAtvenni:
    def test_telepites_nelkul_KIMONDJA_hogy_nincs_mit_atvenni(self, vezerlo_gyar, qt_app):
        v = vezerlo_gyar(telepitesek=())
        fogo = _Fogo()
        v.importFailed.connect(fogo)
        nincs = _Fogo()
        v.noInstallationFound.connect(nincs)
        _lefut(v, qt_app)
        assert nincs.tetelek, "a felhasználó nem kap választ"
        assert not fogo.tetelek, "ez nem HIBA, hanem üres eredmény"

    def test_db3_KONYVTAR_nelkuli_telepites_sem_szamit_talalatnak(self, vezerlo_gyar, qt_app):
        """A `Picasa2Albums` önmagában nem elég: a db3 a `Picasa2`-ben van."""
        v = vezerlo_gyar(telepitesek=(_telepites(None),))
        nincs = _Fogo()
        v.noInstallationFound.connect(nincs)
        _lefut(v, qt_app)
        assert nincs.tetelek


class TestSikeresAtvetel:
    def test_a_jelentes_SZAMAI_mennek_ki(self, vezerlo_gyar, qt_app, tmp_path):
        db3 = tmp_path / "Picasa2"
        db3.mkdir()
        jelentes = AtvetelJelentes(mappak=3, kulcsszo=12, hely=4, arc=7, kihagyott=2)
        v = vezerlo_gyar(
            telepitesek=(_telepites(db3),),
            rekordok=("r1", "r2"),
            jelentes=jelentes,
        )
        kesz = _Fogo()
        v.importFinished.connect(kesz)
        _lefut(v, qt_app)
        assert kesz.tetelek == [(3, 12, 4, 7, 2)]

    def test_futas_kozben_a_running_IGAZ_utana_hamis(self, vezerlo_gyar, qt_app, tmp_path):
        db3 = tmp_path / "Picasa2"
        db3.mkdir()
        v = vezerlo_gyar(telepitesek=(_telepites(db3),))
        assert v.running is False
        _lefut(v, qt_app)
        assert v.running is False

    def test_KETSZER_is_elinditható_az_import(self, vezerlo_gyar, qt_app, tmp_path):
        """A tulajdonos döntésének a lényege: megismételhető."""
        db3 = tmp_path / "Picasa2"
        db3.mkdir()
        v = vezerlo_gyar(
            telepitesek=(_telepites(db3),),
            jelentes=AtvetelJelentes(mappak=1, arc=1),
        )
        kesz = _Fogo()
        v.importFinished.connect(kesz)
        _lefut(v, qt_app)
        _lefut(v, qt_app)
        assert len(kesz.tetelek) == 2


class TestHiba:
    def test_a_serult_db3_HIBAKENT_jon_vissza_nem_nemul_el(self, vezerlo_gyar, qt_app, tmp_path):
        db3 = tmp_path / "Picasa2"
        db3.mkdir()
        v = vezerlo_gyar(
            telepitesek=(_telepites(db3),),
            hiba=FileNotFoundError("hiányzó thumbindex"),
        )
        hibak = _Fogo()
        v.importFailed.connect(hibak)
        _lefut(v, qt_app)
        assert hibak.tetelek, "a hiba némán elnyelődött"
        assert "thumbindex" in hibak.tetelek[0][0]
        assert v.running is False
