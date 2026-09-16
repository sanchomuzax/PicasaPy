"""#3237 — „További javaslatok keresése" a vezérlőn és a felületen.

Amit mérünk:

* a lazítás a **lépcsőt** csökkenti tízzel (nem a bináris `0,75`-ös számát
  veszi át — más a skálánk, #2187);
* a tárolt beállítás **kétszeri** hívás után is változatlan (az eredeti sem
  írja vissza a küszöböt);
* a hívás ténylegesen ír javaslatot, és a nézetnek van rá gombja.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QSettings

from picasapy.app.face_scan_controller import FaceScanController
from picasapy.faces.clustering import DEFAULT_SUGGEST_STEP, step_to_threshold
from picasapy.index import open_index
from picasapy.index.face_groups import lazitott_lepcso

_QML_DIR = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml/PicasaPy"


def _arc(conn, nev_fajl: str, lenyomat, *, allapot="unnamed", nev=None) -> int:
    conn.execute(
        "INSERT INTO photos (folder_id, name, kind, size, mtime_ns) "
        "VALUES (1, ?, 'image', 0, 0)",
        (nev_fajl,),
    )
    foto = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
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


def _kozeli(alap, hasonlosag: float):
    merolegesen = np.array([0.0, 1.0], dtype=np.float32)
    vektor = hasonlosag * alap + np.sqrt(1 - hasonlosag**2) * merolegesen
    return (vektor / np.linalg.norm(vektor)).astype(np.float32)


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    """Vezérlő két arccal: egy nevesített és egy „köztes" hasonlóságú."""
    alap = np.array([1.0, 0.0], dtype=np.float32)
    alap_kuszob = step_to_threshold(DEFAULT_SUGGEST_STEP)
    lazitott = step_to_threshold(lazitott_lepcso(DEFAULT_SUGGEST_STEP))
    kozepe = (alap_kuszob + lazitott) / 2
    with open_index(tmp_path / "index.db") as conn:
        conn.execute("INSERT INTO folders (path, has_ini) VALUES ('/k', 0)")
        _arc(conn, "anna.jpg", alap, allapot="named", nev="Kiss Anna")
        arc = _arc(conn, "ketes.jpg", _kozeli(alap, kozepe))
        conn.commit()
    beallitas = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    ctl = FaceScanController(tmp_path / "index.db", settings=beallitas)
    return ctl, tmp_path, arc, beallitas


def _javaslat(tmp_path, arc):
    with open_index(tmp_path / "index.db") as conn:
        return conn.execute(
            "SELECT suggested_name FROM face WHERE id = ?", (arc,)
        ).fetchone()["suggested_name"]


class TestALazitas:
    def test_a_hivas_javaslatot_ir(self, vezerlo):
        ctl, tmp_path, arc, _beallitas = vezerlo
        assert _javaslat(tmp_path, arc) is None
        assert ctl.moreSuggestions() == 1
        assert _javaslat(tmp_path, arc) == "Kiss Anna"

    def test_masodik_hivas_MAR_nem_ir(self, vezerlo):
        """A javaslat megvan — a lazítás nem írja felül, és nem duplázza."""
        ctl, _tmp_path, _arc, _b = vezerlo
        assert ctl.moreSuggestions() == 1
        assert ctl.moreSuggestions() == 0

    def test_a_TAROLT_beallitast_nem_irja_vissza(self, vezerlo):
        """⛔ Az eredeti `moresug` sem írja vissza a küszöböt."""
        ctl, _tmp_path, _arc, beallitas = vezerlo
        kulcs = FaceScanController.SUGGEST_STEP_KEY
        assert beallitas.value(kulcs) is None
        ctl.moreSuggestions()
        ctl.moreSuggestions()
        assert beallitas.value(kulcs) is None, (
            "a lazítás beírta a beállítást — az EGYSZERI kellene, hogy legyen"
        )

    def test_a_tarolt_lepcsobol_indul(self, vezerlo):
        """Ha a felhasználó állította a lépcsőt, abból számol — nem a
        beépített alapértékből."""
        ctl, tmp_path, arc, beallitas = vezerlo
        #: a skála alja: a lazítás ott már nem csökkent, tehát a köztes arc
        #: NEM kap javaslatot a magas küszöbön
        beallitas.setValue(FaceScanController.SUGGEST_STEP_KEY, 95)
        beallitas.sync()
        assert ctl.moreSuggestions() == 0
        assert _javaslat(tmp_path, arc) is None


class TestAFelulet:
    def test_van_gomb_a_nevtelen_nezetben(self):
        forras = (_QML_DIR / "UnnamedFacesView.qml").read_text(encoding="utf-8")
        assert 'objectName: "moreSuggestionsButton"' in forras
        assert "faceScanController.moreSuggestions()" in forras
        # a mellőzött nézetben nincs értelme
        assert "visible: !root.ignoredMode" in forras
