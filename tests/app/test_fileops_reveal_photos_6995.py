"""#6995: a Locate on Disk TÖBB kijelölt képnél mappánként egy ablakot nyit.

Az eredeti `0x005c85e0` a kijelölt képek szülőmappáit összegyűjti, mappánként
egyszer veszi (`0x005c8754`-`0x005c87b5`), majd a `0x005c8dc4`-`0x005c8dee`
ciklusban minden érintett mappához külön fájlkezelő-ablakot nyit az adott
mappa ELSŐ kijelölt elemére állva (`0x00981280`).

A fájlkezelő indítása a `picasapy.app.fileops_controller` MODULSZINTŰ
`reveal_in_file_manager` fogantyúján át megy; a teszt ezt cseréli, és a
hívásait számolja. Valódi fájlkezelő nem indul.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app.fileops_controller as fileops_modul
from picasapy.app.fileops_controller import FileOpsController


@pytest.fixture
def vezerlo(qt_app):
    return FileOpsController()


@pytest.fixture
def hivasok(monkeypatch) -> list[Path]:
    """A fájlkezelő-fogantyú helyettesítője: a kapott utakat gyűjti."""
    lista: list[Path] = []
    monkeypatch.setattr(
        fileops_modul, "reveal_in_file_manager", lambda ut: lista.append(Path(ut))
    )
    return lista


def _utak(tmp_path: Path, *nevek: str) -> list[str]:
    return [str(tmp_path / nev) for nev in nevek]


class TestRevealPhotos:
    def test_egy_mappa_tobb_kepe_egyetlen_ablakot_nyit_az_elso_kepre(
        self, vezerlo, hivasok, tmp_path
    ):
        vezerlo.revealPhotos(_utak(tmp_path, "b.jpg", "c.jpg", "d.jpg"))

        assert hivasok == [tmp_path / "b.jpg"]

    def test_mappankent_egy_ablak_a_mappa_elso_kijelolt_kepevel(
        self, vezerlo, hivasok, tmp_path
    ):
        utak = _utak(
            tmp_path, "elso/a.jpg", "masik/x.jpg", "elso/b.jpg", "masik/y.jpg", "harmadik/z.jpg"
        )

        vezerlo.revealPhotos(utak)

        assert hivasok == [
            tmp_path / "elso" / "a.jpg",
            tmp_path / "masik" / "x.jpg",
            tmp_path / "harmadik" / "z.jpg",
        ]

    def test_az_ablakok_a_mappak_elso_elofordulasi_sorrendjeben_nyilnak(
        self, vezerlo, hivasok, tmp_path
    ):
        vezerlo.revealPhotos(_utak(tmp_path, "z/1.jpg", "a/1.jpg", "z/2.jpg"))

        assert hivasok == [tmp_path / "z" / "1.jpg", tmp_path / "a" / "1.jpg"]

    def test_egyetlen_kep_ugyanazt_adja_mint_a_reveal_photo(
        self, vezerlo, hivasok, tmp_path
    ):
        vezerlo.revealPhotos(_utak(tmp_path, "a.jpg"))

        assert hivasok == [tmp_path / "a.jpg"]

    def test_ures_lista_nem_nyit_ablakot(self, vezerlo, hivasok):
        vezerlo.revealPhotos([])

        assert hivasok == []

    def test_az_ures_utvonal_kimarad_es_nem_nyit_ablakot(self, vezerlo, hivasok, tmp_path):
        vezerlo.revealPhotos(["", *_utak(tmp_path, "a.jpg")])

        assert hivasok == [tmp_path / "a.jpg"]

    def test_ugyanaz_a_kep_ketszer_is_csak_egy_ablak(self, vezerlo, hivasok, tmp_path):
        vezerlo.revealPhotos(_utak(tmp_path, "a.jpg", "a.jpg"))

        assert hivasok == [tmp_path / "a.jpg"]

    def test_a_hiba_jelzodik_es_a_tobbi_mappa_ablaka_is_megnyilik(
        self, vezerlo, monkeypatch, tmp_path
    ):
        probalt: list[Path] = []

        def _elso_elhasal(ut):
            probalt.append(Path(ut))
            if len(probalt) == 1:
                raise OSError("a fájlkezelő megnyitása sikertelen")

        monkeypatch.setattr(fileops_modul, "reveal_in_file_manager", _elso_elhasal)
        hibak: list[tuple[str, str]] = []
        vezerlo.operationFailed.connect(lambda fajta, uzenet: hibak.append((fajta, uzenet)))

        vezerlo.revealPhotos(_utak(tmp_path, "elso/a.jpg", "masik/b.jpg"))

        assert probalt == [tmp_path / "elso" / "a.jpg", tmp_path / "masik" / "b.jpg"]
        assert [fajta for fajta, _uzenet in hibak] == ["reveal"]

    def test_a_file_url_helyi_utta_alakul_a_mappa_kulcsa(self, vezerlo, hivasok, tmp_path):
        a = tmp_path / "elso" / "a.jpg"
        b = tmp_path / "elso" / "b.jpg"

        vezerlo.revealPhotos([a.as_uri(), str(b)])

        assert len(hivasok) == 1
        assert Path(hivasok[0]) == a
