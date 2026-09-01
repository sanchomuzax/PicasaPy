"""#1637/2 — a rejtett mappák NEM vegyülnek vissza a listába.

## A lelet

A #1637 első köre után a „Mappa elrejtése" működött: a mappa eltűnt a bal
hasábról, és a Nézet ▸ Rejtett képek kapcsolóval visszajött. Csakhogy
**ugyanoda jött vissza**, ahol azelőtt állt — a többi mappa közé keveredve,
semmilyen jelölés nélkül. Aki bekapcsolta a rejtett elemeket, nem tudta
megmondani, melyik mappa volt elrejtve; aki kikapcsolta, nem tudta
megmondani, van-e egyáltalán rejtett mappája.

Az eredetiben az elrejtés **adatvédelmi** funkció, nem nézeti szűrő: a
rejtett mappák külön, néven nevezett gyűjteménybe kerülnek
(`IDS_HIDDEN` = „Rejtett mappák", 6 hivatkozás a binárisban). A
csomópont léte a funkció lényege — enélkül az elrejtés csak „eltűnik
valahol".

## Amit ez az őr rögzít

1. rejtett mappa nélkül **nincs** fejléc (üres csomópont nem ül a hasábon);
2. a rejtettek a lista VÉGÉN állnak, a fejléc UTÁN — nem a többi közt;
3. a fejléc nem kattintható sor (nincs útvonala), mint az évszám-elválasztó;
4. kikapcsolt kapcsolónál se fejléc, se rejtett mappa;
5. a `folderCount` a fejlécet nem számolja mappának.

⚠️ Ez az őr a MODELLT méri, nem a képernyőt. A sorok megjelenítését a
`FolderPane.qml` delegate-je végzi; hogy a `hidden` fajtájú sor ott
fejlécként rajzolódik, azt a `test_qml_functional` szintű őrök fedik.
"""

from __future__ import annotations

import pytest

from picasapy.app.models import FolderListModel
from picasapy.index import open_index, set_folder_hidden, sync_tree

REJTETT_FEJLEC = "Rejtett mappák"


@pytest.fixture
def conn(tmp_path):
    gyoker = tmp_path / "kepek"
    for nev in ("nyaralas", "titkos", "vegyes"):
        (gyoker / nev).mkdir(parents=True)
        (gyoker / nev / "a.jpg").write_bytes(b"1")
    with open_index(tmp_path / "index.db") as kapcsolat:
        sync_tree(kapcsolat, gyoker)
        yield kapcsolat


def _sorok(model: FolderListModel) -> list[tuple[str, str]]:
    """(fajta, név) párok — a modell belső sorai olvasható alakban."""
    return [(sor[0], sor[1]) for sor in model._rows]


def _betolt(conn, *, rejtettel: bool) -> FolderListModel:
    model = FolderListModel()
    model.load(conn, "name", False, include_hidden=rejtettel)
    return model


class TestNincsRejtettMappa:
    def test_nincs_ures_fejlec(self, conn):
        """Rejtett mappa nélkül a csomópont NEM jelenik meg."""
        assert REJTETT_FEJLEC not in [nev for _, nev in _sorok(_betolt(conn, rejtettel=True))]


class TestVanRejtettMappa:
    @pytest.fixture(autouse=True)
    def _rejts_el(self, conn, tmp_path):
        set_folder_hidden(conn, str(tmp_path / "kepek" / "titkos"), True)

    def test_kikapcsolva_se_fejlec_se_mappa(self, conn):
        nevek = [nev for _, nev in _sorok(_betolt(conn, rejtettel=False))]
        assert REJTETT_FEJLEC not in nevek
        assert "titkos" not in nevek

    def test_a_fejlec_utan_a_lista_vegen_all(self, conn):
        sorok = _sorok(_betolt(conn, rejtettel=True))
        assert sorok[-2:] == [("hidden", REJTETT_FEJLEC), ("folder", "titkos")]

    def test_nem_vegyul_a_tobbi_koze(self, conn):
        """A rejtett mappa nem állhat a fejléc ELŐTT — épp ez volt a hiba."""
        sorok = _sorok(_betolt(conn, rejtettel=True))
        fejlec = [i for i, (fajta, _) in enumerate(sorok) if fajta == "hidden"]
        assert len(fejlec) == 1, "pontosan egy Rejtett mappák fejléc kell"
        elotte = [nev for _, nev in sorok[: fejlec[0]]]
        assert "titkos" not in elotte
        assert elotte == ["nyaralas", "vegyes"]

    def test_a_fejlec_nem_kattinthato_sor(self, conn):
        """Útvonal nélkül a delegate MouseArea-ja nem talál mit kijelölni."""
        model = _betolt(conn, rejtettel=True)
        fejlec = next(sor for sor in model._rows if sor[0] == "hidden")
        assert fejlec[2] == ""

    def test_a_folderCount_nem_szamolja_a_fejlecet(self, conn):
        """Három mappánk van; a fejléc nem negyedik."""
        assert _betolt(conn, rejtettel=True).folderCount == 3


class TestAVezerlonAt:
    """Az ÉLES úton: a menütétel vezérlője → index → a hasáb modellje.

    A fenti osztályok a modellt önmagában mérik. Ez itt azt köti össze,
    amit a felhasználó tesz (elrejt egy mappát, majd bekapcsolja a
    rejtett elemeket) azzal, amit lát — ezért használ igazi
    `AppController`-t, nem kézzel töltött modellt.
    """

    @pytest.fixture
    def ctl(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        gyoker = tmp_path / "kepek"
        for nev in ("nyaralas", "titkos"):
            (gyoker / nev).mkdir(parents=True)
            (gyoker / nev / "a.jpg").write_bytes(b"1")
        with open_index(tmp_path / "index.db") as kapcsolat:
            sync_tree(kapcsolat, gyoker)
        vezerlo = AppController(
            tmp_path / "index.db",
            (str(gyoker),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
            settings=QSettings(
                str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
            ),
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        vezerlo._reload()
        yield vezerlo
        vezerlo.shutdown()

    def test_elrejtes_utan_a_csomopont_alatt_jon_vissza(self, ctl, tmp_path):
        """Ez fogta meg a #1637/1 néma hibáját: a `setShowHidden` csak a
        RÁCSOT töltötte újra, a bal hasábot nem — a rejtett mappa így csak
        egy későbbi, más okból kiváltott újratöltéskor bukkant elő. A
        kapcsoló látszólag működött, mert a rejtett KÉPEK azonnal
        megjelentek."""
        titkos = str(tmp_path / "kepek" / "titkos")
        ctl.toggleFolderHidden(titkos)

        nevek = [sor[1] for sor in ctl._folders._rows]
        assert "titkos" not in nevek, "elrejtés után nem szabad látszania"
        assert REJTETT_FEJLEC not in nevek, "kikapcsolt kapcsolónál nincs fejléc"

        ctl.setShowHidden(True)
        sorok = [(sor[0], sor[1]) for sor in ctl._folders._rows]
        assert sorok[-2:] == [("hidden", REJTETT_FEJLEC), ("folder", "titkos")]

    def test_visszahozas_utan_a_csomopont_eltunik(self, ctl, tmp_path):
        """A megjelenítés visszakapcsolása üresen hagyja a csomópontot —
        akkor pedig nem szabad ott maradnia."""
        titkos = str(tmp_path / "kepek" / "titkos")
        ctl.setShowHidden(True)
        ctl.toggleFolderHidden(titkos)
        ctl.toggleFolderHidden(titkos)
        sorok = [(sor[0], sor[1]) for sor in ctl._folders._rows]
        assert not any(fajta == "hidden" for fajta, _ in sorok)
        assert ("folder", "titkos") in sorok
