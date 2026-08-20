"""A Kollázsok mappa INDULÁSKOR is bekerül a Projektekbe (#1075).

## A tulajdonos jelentése a v0.8.18-ról

> „nincsen Kollázsok mappa sehol, eltűnt. A Projektek mappa alatt sincsen
> semmi ismét."

## Miért nem elég a mentéskori megjelölés

A Projektek gyűjtemény két feltételt kér (`index/project_folders.py`):

1. a mappa az INDEXBEN legyen (`has_ini = 1`), és
2. a `.picasa.ini`-je hordozza a `P2category=Projects (internal)` kulcsot.

Mindkettőt a MENTÉS állítja elő (#1046, #1048) — **visszamenőleg semmi**.
Ebből két, egymástól független módon lesz „eltűnt mappa":

* a **0.8.8 ELŐTT** készült kollázsok mappájában nincs `.picasa.ini`, és a
  frissítés nem javítja utólag: a felhasználó örökre üres Projekteket lát;
* ha az indexelés egyszer elbukik (jogosultság, zárolt adatbázis), a
  mentés-ág **némán** továbbmegy (`except Exception` + `warning`), és a
  mappa soha többé nem kerül be.

Ezért az önjavításnak **induláskor** kell futnia, a mentéstől függetlenül.

## A biztonsági szabály: csak a MI kollázsainkat jelöljük meg

A megjelölés a felhasználó mappájába ír. Csak akkor tesszük, ha a mappában
tényleg a mi kimenetünk áll: **egy `.jpg`, amihez tartozik azonos nevű
`.cxf`**. Egy tetszőleges képmappát projekt-albumnak jelölni rosszabb volna
a hibánál, amit javítunk.

A meglévő kulcsokat a `write_album_ini` megőrzi — a mappában korábbi
Picasa-adat is lehet.
"""

from __future__ import annotations


from picasapy.app.collage_output import (
    PROJECTS_CATEGORY,
    ensure_project_album,
)
from support.jpeg_factory import make_jpeg


def _kollazst_tesz(mappa, nev="Nyaralás"):
    """Egy „mi készítettük" kollázs: JPEG + azonos nevű `.cxf`."""
    mappa.mkdir(parents=True, exist_ok=True)
    make_jpeg(mappa / f"{nev}.jpg", size=(80, 60))
    (mappa / f"{nev}.cxf").write_bytes(b'<?xml version="1.0"?><collage/>')
    return mappa


class TestAzOnjavitas:
    def test_a_regi_kollazs_mappa_megjelolodik(self, tmp_path):
        """⚠️ Ez a tulajdonos esete: 0.8.8 előtt készült kollázs, nincs ini."""
        mappa = _kollazst_tesz(tmp_path / "Kollázsok")

        assert ensure_project_album(mappa) is True
        assert PROJECTS_CATEGORY in (mappa / ".picasa.ini").read_text(
            encoding="utf-8"
        )

    def test_a_mar_megjelolt_mappat_nem_irja_ujra(self, tmp_path):
        mappa = _kollazst_tesz(tmp_path / "Kollázsok")
        ensure_project_album(mappa)
        elotte = (mappa / ".picasa.ini").read_bytes()

        assert ensure_project_album(mappa) is False
        assert (mappa / ".picasa.ini").read_bytes() == elotte

    def test_a_meglevo_kulcsokat_MEGORZI(self, tmp_path):
        """A mappában korábbi Picasa-adat is lehet — azt felülírni
        adatvesztés volna."""
        mappa = _kollazst_tesz(tmp_path / "Kollázsok")
        (mappa / ".picasa.ini").write_text(
            "[Nyaralás.jpg]\nstar=yes\n", encoding="utf-8"
        )

        ensure_project_album(mappa)

        tartalom = (mappa / ".picasa.ini").read_text(encoding="utf-8")
        assert "star=yes" in tartalom
        assert PROJECTS_CATEGORY in tartalom


class TestAmitNEM_jelolunk_meg:
    """Csak a MI kimenetünket — egy tetszőleges képmappát soha."""

    def test_cxf_par_nelkuli_kepmappat_nem(self, tmp_path):
        mappa = tmp_path / "Nyaralás 2026"
        mappa.mkdir()
        make_jpeg(mappa / "a.jpg", size=(80, 60))

        assert ensure_project_album(mappa) is False
        assert not (mappa / ".picasa.ini").exists()

    def test_ures_mappat_nem(self, tmp_path):
        mappa = tmp_path / "Kollázsok"
        mappa.mkdir()

        assert ensure_project_album(mappa) is False
        assert not (mappa / ".picasa.ini").exists()

    def test_nem_letezo_mappat_nem(self, tmp_path):
        assert ensure_project_album(tmp_path / "nincs") is False

    def test_csak_cxf_van_kep_nelkul_nem(self, tmp_path):
        """Piszkozat-mappa (csak `autosave.cxf`) NEM projekt-album."""
        mappa = tmp_path / "Kollázsok"
        mappa.mkdir()
        (mappa / "autosave.cxf").write_bytes(b"<collage/>")

        assert ensure_project_album(mappa) is False


class TestALancVege:
    """A megjelölés után a mappa tényleg megjelenik a Projektek alatt."""

    def test_indulaskori_felvetel_utan_lathato(self, tmp_path):
        from picasapy.index import open_index
        from picasapy.index.project_folders import project_folders
        from picasapy.index.sync import sync_folder

        mappa = _kollazst_tesz(tmp_path / "Kollázsok")
        db = tmp_path / "index.db"

        ensure_project_album(mappa)
        with open_index(db) as conn:
            sync_folder(conn, mappa, mappa)
            nevek = [m.name for m in project_folders(conn)]

        assert nevek == ["Kollázsok"]

    def test_megjeloles_NELKUL_nem_lathato(self, tmp_path):
        """A foga: enélkül pontosan azt látja a felhasználó, amit jelentett."""
        from picasapy.index import open_index
        from picasapy.index.project_folders import project_folders
        from picasapy.index.sync import sync_folder

        mappa = _kollazst_tesz(tmp_path / "Kollázsok")
        db = tmp_path / "index.db"

        with open_index(db) as conn:
            sync_folder(conn, mappa, mappa)
            assert list(project_folders(conn)) == []
