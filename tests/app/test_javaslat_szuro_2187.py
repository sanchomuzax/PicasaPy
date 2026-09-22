"""#2187: a személy-album rácsa a javaslatokat is mutatja, és a
javaslat-szűrő (`sug_filter`) rájuk szűkít.

Az eredeti személy-album fejlécén a `sug_filter` kapcsoló mért súgója:
„Csak a javaslatok megjelenítése (ha be van kapcsolva)"
(`docs/specs/picasa-arcfelismeres.md` 15.4). Ehhez a rácsnak előbb
látnia kell a javaslatokat — enélkül a kijelölt hatókörű „Jóváhagyás"
és „Eltávolítás" üres halmazra hatna.

Amit ez a fájl NEM mér: a fejléc gombjának megjelenését és helyét (az a
QML-funkcionális teszté), sem azt, hogy a javaslat-jelölés látszik-e a
csempén.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_RECT = "3f840000c3509f84"
_LANDMARKS = FaceLandmarks(
    right_eye=(10.0, 20.0),
    left_eye=(30.0, 20.0),
    nose=(20.0, 30.0),
    mouth_right=(15.0, 40.0),
    mouth_left=(25.0, 40.0),
)


@pytest.fixture
def library(tmp_path):
    """`a.jpg`: Roy MEGERŐSÍTVE (ini). `b.jpg`: Royra JAVASOLVA (face tábla).
    `c.jpg`: se ez, se az."""
    root = tmp_path / "kepek"
    root.mkdir()
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / nev)
    (root / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def host(qt_app, tmp_path, library):
    from picasapy.app.people_controller import PeopleMixin
    from picasapy.index import open_index, replace_faces, sync_tree
    from picasapy.index.faces_detected import set_suggested_name

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        foto = conn.execute(
            "SELECT id FROM photos WHERE name = 'b.jpg'"
        ).fetchone()["id"]
        replace_faces(conn, foto, [FaceDetection(
            left=5.0, top=10.0, right=40.0, bottom=50.0, score=0.9,
            landmarks=_LANDMARKS)])
        arc = conn.execute(
            "SELECT id FROM face WHERE photo_id = ?", (foto,)
        ).fetchone()
        set_suggested_name(conn, arc["id"], "Roy Avery")
        conn.commit()

    class _Host(PeopleMixin, QObject):
        def __init__(self, db_path):
            super().__init__()
            self._db_path = db_path
            self._view_mode = ("folder", "")
            self._filter_active = False
            self._filter_status = ""
            self._shown: tuple = ()
            self._init_people()

        def _show(self, records):
            self._shown = records

        def _get_settings(self):
            if getattr(self, "_beallitasok", None) is None:
                self._beallitasok = QSettings(
                    str(Path(self._db_path).parent / "settings.ini"),
                    QSettings.Format.IniFormat,
                )
            return self._beallitasok

    return _Host(tmp_path / "index.db")


def _nevek(host):
    return sorted(r.name for r in host._shown)


class TestJavaslatokARacsban:
    def test_a_szemely_albuma_a_javaslatot_is_mutatja(self, host):
        host.showPerson("Roy Avery")
        assert _nevek(host) == ["a.jpg", "b.jpg"]

    def test_a_nem_erintett_kep_kimarad(self, host):
        host.showPerson("Roy Avery")
        assert "c.jpg" not in _nevek(host)

    def test_a_kep_egyszer_szerepel_ha_mindketto_igaz(self, host, tmp_path):
        """Ugyanazon a képen lehet Roy megerősítve ÉS javasolva (másik
        arcon) — a rácsban akkor is egy sor."""
        from picasapy.index import open_index, replace_faces
        from picasapy.index.faces_detected import set_suggested_name

        with open_index(tmp_path / "index.db") as conn:
            foto = conn.execute(
                "SELECT id FROM photos WHERE name = 'a.jpg'"
            ).fetchone()["id"]
            replace_faces(conn, foto, [FaceDetection(
                left=60.0, top=60.0, right=90.0, bottom=90.0, score=0.8,
                landmarks=_LANDMARKS)])
            arc = conn.execute(
                "SELECT id FROM face WHERE photo_id = ?", (foto,)
            ).fetchone()
            set_suggested_name(conn, arc["id"], "Roy Avery")
            conn.commit()
        host.showPerson("Roy Avery")
        assert _nevek(host).count("a.jpg") == 1


class TestJavaslatSzuro:
    def test_alapbol_ki_van_kapcsolva(self, host):
        assert host.personSuggestionsOnly is False

    def test_bekapcsolva_csak_a_javaslatok_latszanak(self, host):
        host.showPerson("Roy Avery")
        host.setPersonSuggestionsOnly(True)
        assert _nevek(host) == ["b.jpg"]

    def test_visszakapcsolva_ujra_minden_latszik(self, host):
        host.showPerson("Roy Avery")
        host.setPersonSuggestionsOnly(True)
        host.setPersonSuggestionsOnly(False)
        assert _nevek(host) == ["a.jpg", "b.jpg"]

    def test_a_kapcsolo_jelez(self, host, qt_app):
        latott = []
        host.personViewChanged.connect(lambda: latott.append(1))
        host.showPerson("Roy Avery")
        latott.clear()
        host.setPersonSuggestionsOnly(True)
        assert latott, "a kapcsoló nem jelzett — a fejléc kötése elavulna"

    def test_azonos_ertekre_nem_tolt_ujra(self, host):
        """A kapcsoló kétszeri bekapcsolása ne olvassa újra az indexet."""
        host.showPerson("Roy Avery")
        host.setPersonSuggestionsOnly(True)
        elso = host._shown
        host.setPersonSuggestionsOnly(True)
        assert host._shown is elso

    def test_mappa_nezetben_nem_hat(self, host):
        """Nem személy-album van nyitva: a kapcsoló nem tölt be semmit."""
        host.setPersonSuggestionsOnly(True)
        assert host._shown == ()


class TestUjratoltes:
    """A jóváhagyás/elvetés után a rács újratöltődik — a szűrő állása
    ilyenkor MEGMARAD, különben a gomb magától visszaugrana."""

    def test_ujratoltes_megtartja_a_szurot(self, host):
        host.showPerson("Roy Avery")
        host.setPersonSuggestionsOnly(True)
        host.refreshPersonAlbum()
        assert host.personSuggestionsOnly is True
        assert _nevek(host) == ["b.jpg"]

    def test_masik_szemely_megnyitasa_kikapcsolja(self, host):
        """Új album = tiszta lap: a szűrő kikapcsolt állapotból indul."""
        host.showPerson("Roy Avery")
        host.setPersonSuggestionsOnly(True)
        host.showPerson("Roy Avery")
        assert host.personSuggestionsOnly is False

    def test_mappa_nezetben_nem_csinal_semmit(self, host):
        host.refreshPersonAlbum()
        assert host._shown == ()
