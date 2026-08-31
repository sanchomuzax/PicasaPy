"""#1643 — a „Másolat mentése" NEM ír a `.picasa.ini`-be.

**A #1527 döntése megdőlt.** Akkor a binárisból nem lehetett kiolvasni,
mit ír az eredeti, ezért a kör józan alapértelmezést választott: a másolat
kapjon `redo=` + `originhash` könyvelést, mint a mentés. A tulajdonos
referencia-mérése ezt megcáfolta.

**A mérés** (`research/testdata/1557-masolat-mentese/`, valódi Picasa 3.9):

| idő | esemény | `.picasa.ini` |
|---|---|---|
| 19:30 | másolat SZERKESZTETLEN képről → `…-001.jpg` | **nem jött létre** |
| 19:33 | auto kontraszt a FORRÁSRA | ekkor keletkezett, 65 bájt |
| 19:35 | másolat SZERKESZTETT képről → `…-002.jpg` | **változatlan**, 65 bájt |

Hogy a második eset tényleg szerkesztett képről készült, képponti méréssel
bizonyított: a `…-002.jpg` a forrástól 99,9%-ban eltér, a `…-001.jpg` csak
7,3%-ban (újrakódolási zaj).

⇒ Mi olyan kulcsokat írtunk, amiket az eredeti soha. A kétirányú
`.picasa.ini`-kompatibilitás a projekt magígérete, ezért ez valódi eltérés
volt: a mi ini-jeink a windowsos Picasában idegen bejegyzéseket mutattak.
"""

from __future__ import annotations

import numpy as np

from picasapy.edit.save_copy import save_copy
from picasapy.edit.session import EditSession


def _kep(path, ertek: int = 128) -> None:
    import cv2

    cv2.imwrite(str(path), np.full((8, 8, 3), ertek, dtype=np.uint8))


class TestNemIrAzIniBe:
    def test_ini_nelkuli_mappaban_NEM_jon_letre_ini(self, tmp_path):
        """A mérés első sora: a másolás nem hozza létre az ini-t."""
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        ini = tmp_path / ".picasa.ini"
        assert not ini.exists()

        save_copy(
            forras,
            np.full((8, 8, 3), 200, dtype=np.uint8),
            EditSession.from_value("crop64=1,0,0,ffff,ffff;"),
        )

        assert (tmp_path / "kep-001.jpg").exists(), "a másolat nem készült el"
        assert not ini.exists(), (
            "a másolás létrehozta a .picasa.ini-t — az eredeti nem teszi "
            "(#1643, mérve)"
        )

    def test_a_meglevo_ini_BAJTRA_valtozatlan_marad(self, tmp_path):
        """A mérés harmadik sora: a meglévő ini időbélyege és mérete sem
        változott. Itt bájtra hasonlítunk — ez a szigorúbb állítás."""
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        ini = tmp_path / ".picasa.ini"
        # a mért minta szerkezete: a FORRÁS kapott szakaszt a szerkesztéstől
        ini.write_text(
            "[kep.jpg]\nfilters=autolight=1;\nbackuphash=58355\n",
            encoding="utf-8",
        )
        elotte = ini.read_bytes()

        save_copy(
            forras,
            np.full((8, 8, 3), 200, dtype=np.uint8),
            EditSession.from_value("autolight=1;"),
        )

        assert ini.read_bytes() == elotte, (
            "a másolás megváltoztatta a .picasa.ini-t — az eredeti bájtra "
            "változatlanul hagyja (#1643, mérve)"
        )

    def test_a_masodik_masolat_sem_ir(self, tmp_path):
        """A mérés a `-002`-t is lefedi: a második másolat sem könyvel."""
        forras = tmp_path / "kep.jpg"
        _kep(forras)
        (tmp_path / "kep-001.jpg").write_bytes(b"foglalt")
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[kep.jpg]\nfilters=autolight=1;\n", encoding="utf-8")
        elotte = ini.read_bytes()

        eredmeny = save_copy(
            forras,
            np.full((8, 8, 3), 200, dtype=np.uint8),
            EditSession.from_value("autolight=1;"),
        )

        assert eredmeny.target_path.name == "kep-002.jpg"
        assert ini.read_bytes() == elotte
