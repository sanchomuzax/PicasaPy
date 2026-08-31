"""#1671 — a Nyomtatás és az e-mail a KÉPTÁLCA tartalmán dolgozzon.

A `print_controller.py` és az `email_controller.py` végig rács-sorokat
oldott fel (`_resolve_records(rows)`), ezért kijelölés nélkül — vagy más
mappából tartott képre — néma maradt. A #455 a mappába exportálást már
átkötötte a tálcára; ez a kettő maradt.

Az eredeti súgója kimondja: *„Print photos in the Photo Tray"*.

A szerződés: **ha a tálca nem üres, ő a forrás** — a rács pillanatnyi
kijelölése és a látott mappa nem számít. Üres tálcánál marad a régi,
sor-alapú viselkedés.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from picasapy.app.email_controller import EmailController
from picasapy.app.print_controller import PrintController


@dataclass(frozen=True)
class Rekord:
    """A `PhotoRecord` minimális helyettese — csak amit a feloldás néz."""

    folder_path: str
    name: str


#: a RÁCS (a látott mappa) képei
RACS = (Rekord("/kepek/nyaralas", "racs1.jpg"), Rekord("/kepek/nyaralas", "racs2.jpg"))
#: a TÁLCÁN tartott kép — MÁSIK mappából, tehát a rácsban nincs is sora
TALCA = (Rekord("/kepek/regi", "tartott.jpg"),)


@pytest.fixture(params=[PrintController, EmailController], ids=["print", "email"])
def vezerlo_osztaly(request):
    return request.param


class TestATalcaNyerHaNemUres:
    def test_a_talcan_tartott_kep_kerul_a_kimenetbe_nem_a_racsbeli(
        self, vezerlo_osztaly, qt_app
    ):
        vezerlo = vezerlo_osztaly(
            photo_source=lambda: RACS, tray_source=lambda: TALCA
        )
        # a hívó a rács 0. sorát kéri — a tálca viszont nem üres
        rekordok = vezerlo._resolve_records([0])
        nevek = [r.name for r in rekordok]
        assert nevek == ["tartott.jpg"], (
            f"a rács kijelölése nyert a tálcával szemben: {nevek}"
        )

    def test_kijeloles_nelkul_sem_nema(self, vezerlo_osztaly, qt_app):
        """A jelentett tünet: kijelölés nélkül a parancs nem csinált semmit."""
        vezerlo = vezerlo_osztaly(
            photo_source=lambda: RACS, tray_source=lambda: TALCA
        )
        rekordok = vezerlo._resolve_records([])
        assert [r.name for r in rekordok] == ["tartott.jpg"], (
            "üres kijelöléssel a tálca tartalma sem jött — a parancs néma "
            "marad (#1671)"
        )

    def test_ures_talcanal_marad_a_racs(self, vezerlo_osztaly, qt_app):
        vezerlo = vezerlo_osztaly(
            photo_source=lambda: RACS, tray_source=lambda: ()
        )
        assert [r.name for r in vezerlo._resolve_records([1])] == ["racs2.jpg"]

    def test_talca_forras_nelkul_a_regi_viselkedes(self, vezerlo_osztaly, qt_app):
        """A `tray_source` elhagyható — a meglévő hívók és tesztek nem
        törhetnek el tőle."""
        vezerlo = vezerlo_osztaly(photo_source=lambda: RACS)
        assert [r.name for r in vezerlo._resolve_records([0])] == ["racs1.jpg"]
