"""#3237 — „További javaslatok keresése": a küszöb tízzel lejjebb.

Az eredeti `moresug` parancsa (kezelő `0x00602890`) a felismerési küszöböt
**tízzel lejjebb** viszi, és **nem írja vissza** a beállítást — így egy
kattintással több javaslat jön, de a program alapviselkedése nem változik.

⚠️ **Mértékegység-csapda (a #2187-ből):** a bináris `0,75`-ös SZÁMÁT nem
vesszük át, mert nálunk a küszöb más skálán él (`step_to_threshold`: a Picasa
50–95-ös lépcsője a saját `[0,30 … 0,55]` hasonlósági sávunkba). A hű
megfelelő a **LÉPCSŐ** csökkentése tízzel — a vezérlőt vesszük át, nem a
számot.
"""

from __future__ import annotations

import numpy as np

from picasapy.faces.clustering import (
    DEFAULT_SUGGEST_STEP,
    PICASA_STEPS,
    step_to_threshold,
)
from picasapy.index import open_index
from picasapy.index.face_groups import (
    LAZITAS_LEPCSO,
    javaslatokat_ujraszamol,
    lazitott_lepcso,
)
from picasapy.index.faces_detected import set_suggested_name


def _arc(conn, ut: str, lenyomat, *, allapot="unnamed", nev=None) -> int:
    conn.execute(
        "INSERT INTO photos (folder_id, name, kind, size, mtime_ns) "
        "VALUES (1, ?, 'image', 0, 0)",
        (ut,),
    )
    foto = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    #: a jelölőpontok NOT NULL-ok a sémában — a próbához semlegesek
    conn.execute(
        "INSERT INTO face (photo_id, rect_left, rect_top, rect_right, "
        "rect_bottom, det_conf, right_eye_x, right_eye_y, left_eye_x, "
        "left_eye_y, nose_x, nose_y, mouth_right_x, mouth_right_y, "
        "mouth_left_x, mouth_left_y, state, person_name, embedding) "
        "VALUES (?, 0.1, 0.1, 0.4, 0.4, 0.9, 0.2, 0.2, 0.3, 0.2, 0.25, 0.3, "
        "0.22, 0.35, 0.28, 0.35, ?, ?, ?)",
        (foto, allapot, nev, np.asarray(lenyomat, dtype=np.float32).tobytes()),
    )
    return conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]


def _mappa(conn, ut="/kepek"):
    conn.execute("INSERT INTO folders (path, has_ini) VALUES (?, 0)", (ut,))


class TestALazitottLepcso:
    def test_tizzel_lejjebb(self) -> None:
        assert lazitott_lepcso(DEFAULT_SUGGEST_STEP) == DEFAULT_SUGGEST_STEP - 10
        assert lazitott_lepcso(85) == 75
        assert LAZITAS_LEPCSO == 10

    def test_a_skala_aljat_nem_lepi_tul(self) -> None:
        """⛔ A lépcső nem mehet a saját skálánk alja alá — ott a
        `step_to_threshold` már extrapolálna, és a javaslat értelmét
        vesztené."""
        alja = PICASA_STEPS[0]
        assert lazitott_lepcso(alja) == alja
        assert lazitott_lepcso(alja + 5) == alja


class TestAzUjraszamolas:
    def _kozeli_lenyomat(self, alap, hasonlosag: float):
        """Olyan vektor, ami a megadott koszinusz-hasonlóságot adja."""
        merolegesen = np.array([0.0, 1.0], dtype=np.float32)
        vektor = hasonlosag * alap + np.sqrt(1 - hasonlosag**2) * merolegesen
        return (vektor / np.linalg.norm(vektor)).astype(np.float32)

    def test_a_koztes_arc_CSAK_a_lazitas_utan_kap_javaslatot(self, tmp_path):
        alap = np.array([1.0, 0.0], dtype=np.float32)
        alap_kuszob = step_to_threshold(DEFAULT_SUGGEST_STEP)
        lazitott = step_to_threshold(lazitott_lepcso(DEFAULT_SUGGEST_STEP))
        assert lazitott < alap_kuszob, "a lazítás nem csökkentette a küszöböt"
        kozepe = (alap_kuszob + lazitott) / 2

        with open_index(tmp_path / "index.db") as conn:
            _mappa(conn)
            _arc(conn, "anna.jpg", alap, allapot="named", nev="Kiss Anna")
            arc = _arc(conn, "ketes.jpg", self._kozeli_lenyomat(alap, kozepe))
            conn.commit()

            def javaslat():
                return conn.execute(
                    "SELECT suggested_name FROM face WHERE id = ?", (arc,)
                ).fetchone()["suggested_name"]

            # az ALAP küszöbön nincs javaslat
            assert javaslatokat_ujraszamol(conn, alap_kuszob) == 0
            assert javaslat() is None
            # a LAZÍTOTT küszöbön van
            assert javaslatokat_ujraszamol(conn, lazitott) == 1
            assert javaslat() == "Kiss Anna"

    def test_a_MAR_javasolt_arcot_nem_bantja(self, tmp_path):
        alap = np.array([1.0, 0.0], dtype=np.float32)
        with open_index(tmp_path / "index.db") as conn:
            _mappa(conn)
            _arc(conn, "anna.jpg", alap, allapot="named", nev="Kiss Anna")
            arc = _arc(conn, "mas.jpg", self._kozeli_lenyomat(alap, 0.99))
            set_suggested_name(conn, arc, "Kézzel Írt")
            conn.commit()
            assert javaslatokat_ujraszamol(conn, 0.0) == 0
            assert conn.execute(
                "SELECT suggested_name FROM face WHERE id = ?", (arc,)
            ).fetchone()["suggested_name"] == "Kézzel Írt"

    def test_a_NEVES_arcot_nem_bantja(self, tmp_path):
        alap = np.array([1.0, 0.0], dtype=np.float32)
        with open_index(tmp_path / "index.db") as conn:
            _mappa(conn)
            _arc(conn, "anna.jpg", alap, allapot="named", nev="Kiss Anna")
            conn.commit()
            assert javaslatokat_ujraszamol(conn, 0.0) == 0

    def test_nev_nelkuli_konyvtarban_nincs_mit_javasolni(self, tmp_path):
        """Nevesített arc nélkül nincs centroid — a lazítás sem talál semmit."""
        alap = np.array([1.0, 0.0], dtype=np.float32)
        with open_index(tmp_path / "index.db") as conn:
            _mappa(conn)
            _arc(conn, "egy.jpg", alap)
            conn.commit()
            assert javaslatokat_ujraszamol(conn, 0.0) == 0

    def test_a_csoportokat_nem_bantja(self, tmp_path):
        """⛔ Ez a lépés CSAK javaslatot ír: a csoportosítás érintetlen."""
        alap = np.array([1.0, 0.0], dtype=np.float32)
        with open_index(tmp_path / "index.db") as conn:
            _mappa(conn)
            _arc(conn, "anna.jpg", alap, allapot="named", nev="Kiss Anna")
            arc = _arc(conn, "ketes.jpg", self._kozeli_lenyomat(alap, 0.9))
            #: a `group_id` idegen kulcs — előbb legyen csoport
            conn.execute(
                "INSERT INTO face_group (id, centroid) VALUES (42, ?)",
                (alap.tobytes(),),
            )
            conn.execute("UPDATE face SET group_id = 42 WHERE id = ?", (arc,))
            conn.commit()
            javaslatokat_ujraszamol(conn, 0.0)
            assert conn.execute(
                "SELECT group_id FROM face WHERE id = ?", (arc,)
            ).fetchone()["group_id"] == 42
