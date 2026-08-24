"""A kollázs PISZKOZAT-ÁLLAPOTA a lemezen (#1072).

A jegy azt kérte számon, hogy a piszkozatnak nálunk **nincs fogalma**: a
program sehol nem tudja megkülönböztetni a félkész kollázst a késztől,
tehát nem is tud rá következményt kötni (tiltás, befejező lépés).

A megkülönböztetés a spec 1. szakaszának NORMATÍV táblájából jön
(`docs/specs/kollazs-eletciklus.md`):

| állapot | fájlok a Kollázsok mappában |
|---|---|
| **PISZKOZAT** | `<név>.jpg` (640 hosszú él) + `autosave.cxf` |
| **kész** | `<név>.jpg` (5120 hosszú él) + `<név>.cxf` |

Vagyis a kérdés tisztán fájl-létezés: van-e a képnek SAJÁT `.cxf` párja
(→ kész), és áll-e mellette `autosave.cxf` (→ piszkozat). Ugyanez a pár
dönti el a „Kollázs szerkesztése" gomb megjelenését is (#1002), csak ott a
kész ágra kérdeztünk.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.collage.autosave import AUTOSAVE_NAME
from picasapy.collage.draft_state import draft_project_path, is_draft_image


def _kep(mappa: Path, nev: str) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    ut = mappa / nev
    ut.write_bytes(b"nem valodi JPEG, a fajl LETEZESE a kerdes")
    return ut


class TestPiszkozatFelismerese:
    def test_autosave_mellett_allo_kep_PISZKOZAT(self, tmp_path):
        """Ez a piszkozat definíciója: kép + `autosave.cxf`, saját `.cxf`
        nélkül."""
        kep = _kep(tmp_path, "AI10.jpg")
        (tmp_path / AUTOSAVE_NAME).write_text("<collage/>", encoding="utf-8")

        assert is_draft_image(kep) is True

    def test_sajat_cxf_parral_KESZ_kollazs(self, tmp_path):
        """A kész kollázs mellett ott a projektfájlja — akkor is, ha egy
        MÁSIK, félbehagyott munka `autosave.cxf`-je is a mappában van."""
        kep = _kep(tmp_path, "AI10.jpg")
        kep.with_suffix(".cxf").write_text("<collage/>", encoding="utf-8")
        (tmp_path / AUTOSAVE_NAME).write_text("<collage/>", encoding="utf-8")

        assert is_draft_image(kep) is False

    def test_autosave_nelkul_NEM_piszkozat(self, tmp_path):
        """Egy sima fénykép egy sima mappában nem piszkozat."""
        assert is_draft_image(_kep(tmp_path, "nyaralas.jpg")) is False

    def test_nem_letezo_fajl_NEM_piszkozat(self, tmp_path):
        (tmp_path / AUTOSAVE_NAME).write_text("<collage/>", encoding="utf-8")

        assert is_draft_image(tmp_path / "nincs.jpg") is False

    def test_ures_utvonal_NEM_piszkozat(self):
        """A felület null-őre: a néző sor nélkül üres útvonalat ad."""
        assert is_draft_image("") is False


class TestPiszkozatProjektfajlja:
    def test_a_piszkozat_projektje_az_autosave(self, tmp_path):
        """A befejező lépésnek a piszkozat PROJEKTJÉT kell betöltenie — az
        pedig az `autosave.cxf`, nem a kép melletti (nem létező) `.cxf`."""
        kep = _kep(tmp_path, "AI10.jpg")
        autosave = tmp_path / AUTOSAVE_NAME
        autosave.write_text("<collage/>", encoding="utf-8")

        assert draft_project_path(kep) == autosave

    def test_kesz_kollazsnak_nincs_piszkozat_projektje(self, tmp_path):
        kep = _kep(tmp_path, "AI10.jpg")
        kep.with_suffix(".cxf").write_text("<collage/>", encoding="utf-8")
        (tmp_path / AUTOSAVE_NAME).write_text("<collage/>", encoding="utf-8")

        assert draft_project_path(kep) is None
