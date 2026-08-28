"""FileOpsController.moveSelectionToNewFolder — Fájl ▸ „Áthelyezés új
mappába…" magja (#1614).

A vezérlő szintjén mérjük: a `.picasa.ini` bejegyzés a képpel költözik
(ugyanaz a `move_photos` mag, mint a „Áthelyezés…"-nél, #457), az
érvénytelen név és a már foglalt célmappa pedig `operationFailed`-et
kap — a lemezen SEMMI nem történik.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(qt_app):
    from picasapy.app.fileops_controller import FileOpsController

    return FileOpsController()


class TestMoveSelectionToNewFolderSiker:
    def test_uj_mappaba_kerul_a_kep(self, controller, tmp_path):
        forras = tmp_path / "forras"
        forras.mkdir()
        photo = forras / "a.jpg"
        make_jpeg(photo)
        (forras / ".picasa.ini").write_text(
            "[a.jpg]\ncaption=Nyaralás\n", encoding="utf-8"
        )

        moved = []
        controller.photoMoved.connect(lambda old, new: moved.append((old, new)))
        controller.moveSelectionToNewFolder([str(photo)], "Új mappa")

        cel = forras / "Új mappa" / "a.jpg"
        assert moved == [(str(photo), str(cel))]
        assert cel.exists()
        assert not photo.exists()

    def test_az_ini_bejegyzes_a_keppel_koltozik(self, controller, tmp_path):
        forras = tmp_path / "forras"
        forras.mkdir()
        photo = forras / "a.jpg"
        make_jpeg(photo)
        (forras / ".picasa.ini").write_text(
            "[a.jpg]\ncaption=Nyaralás\n", encoding="utf-8"
        )

        controller.moveSelectionToNewFolder([str(photo)], "Címkézett")

        cel_ini = forras / "Címkézett" / ".picasa.ini"
        assert cel_ini.exists()
        assert "caption=Nyaralás" in cel_ini.read_text(encoding="utf-8")

    def test_tobb_kijelolt_kep_egyutt_kerul_at(self, controller, tmp_path):
        forras = tmp_path / "forras"
        forras.mkdir()
        elso = forras / "a.jpg"
        masodik = forras / "b.jpg"
        make_jpeg(elso)
        make_jpeg(masodik)

        controller.moveSelectionToNewFolder([str(elso), str(masodik)], "Kettő")

        cel = forras / "Kettő"
        assert (cel / "a.jpg").exists()
        assert (cel / "b.jpg").exists()


class TestMoveSelectionToNewFolderHibak:
    """MUTÁCIÓS BIZONYÍTÉK (d): érvénytelen/foglalt név esetén a lemezen
    NEM történik semmi, és a felhasználó a meglévő `operationFailed`
    csatornán kap üzenetet."""

    def test_ures_kijeloles_nem_csinal_semmit(self, controller):
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.moveSelectionToNewFolder([], "Bármi")
        assert failures[0][0] == "move_to_new_folder"

    @pytest.mark.parametrize("tiltott_nev", ["", "   ", "nyár?", "a/b", 'a"b'])
    def test_ervenytelen_nev_eseten_semmi_nem_mozdul(
        self, controller, tmp_path, tiltott_nev
    ):
        forras = tmp_path / "forras"
        forras.mkdir()
        photo = forras / "a.jpg"
        make_jpeg(photo)

        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.moveSelectionToNewFolder([str(photo)], tiltott_nev)

        assert failures[0][0] == "move_to_new_folder"
        assert photo.exists(), "a kép elmozdult, holott a név érvénytelen volt"
        # nem jött létre semmilyen új mappa a szülőben
        assert [p for p in forras.iterdir() if p.is_dir()] == []

    def test_mar_letezo_mappaneven_semmi_nem_mozdul(self, controller, tmp_path):
        forras = tmp_path / "forras"
        forras.mkdir()
        photo = forras / "a.jpg"
        make_jpeg(photo)
        (forras / "Foglalt").mkdir()
        (forras / "Foglalt" / "mar-itt.jpg").write_bytes(b"eredeti")

        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.moveSelectionToNewFolder([str(photo)], "Foglalt")

        assert failures[0][0] == "move_to_new_folder"
        assert photo.exists()
        # a foglalt mappa tartalma érintetlen — nem írtuk felül
        assert (forras / "Foglalt" / "mar-itt.jpg").read_bytes() == b"eredeti"
        assert not (forras / "Foglalt" / "a.jpg").exists()
