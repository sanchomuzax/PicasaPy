"""A `FileOpsController` a Lomtár `0x0f` eredményénél külön kérdést kér (#6969).

Az eredeti (`0x005c9b00` -> `0x005fdb80` -> `0x009929b0`): ha a Lomtárba
helyezés a Shell-művelettől PONTOSAN `0x0f`-et kap, külön `Delete` /
`Cancel` kérdés nyílik, és csak jóváhagyásra próbál végleges törlést. Más
hibakód nem indít végleges törlést.

⚠️ A Shell-hívás a `picasapy.fileops.trash._shfileoperation` modulszintű
fogantyún át van cserélve, a platform a `_platform`-on át van rögzítve
(#1217/#1375) - a globális `ctypes.windll`-hoz nem nyúlunk.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.fileops import trash


@pytest.fixture
def controller(qt_app):
    from picasapy.app.fileops_controller import FileOpsController

    return FileOpsController()


def _shell(monkeypatch, kod: int) -> list[int]:
    monkeypatch.setattr(trash, "_platform", lambda: "win32")
    hivasok: list[int] = []

    def hamis(muvelet) -> int:
        hivasok.append(muvelet.fFlags)
        return kod

    monkeypatch.setattr(trash, "_shfileoperation", hamis)
    return hivasok


def _kep(tmp_path):
    kep = tmp_path / "a.jpg"
    kep.write_bytes(b"kep")
    return kep


def _figyel(controller):
    esemenyek: dict[str, list] = {
        "kerdes": [], "hiba": [], "torolve": [],
    }
    controller.immediateDeletionRequired.connect(esemenyek["kerdes"].append)
    controller.operationFailed.connect(
        lambda muvelet, uzenet: esemenyek["hiba"].append((muvelet, uzenet))
    )
    controller.photoDeleted.connect(esemenyek["torolve"].append)
    return esemenyek


class TestA0fAg:
    def test_a_0f_kerdest_jelez_es_nem_hibat_es_nem_torol(
        self, controller, tmp_path, monkeypatch
    ):
        _shell(monkeypatch, 0x0F)
        kep = _kep(tmp_path)
        esemenyek = _figyel(controller)

        controller.deletePhoto(str(kep))

        assert [Path(p) for p in esemenyek["kerdes"]] == [kep]
        assert esemenyek["hiba"] == [], "a 0x0f NEM hibaablak, hanem kérdés"
        assert esemenyek["torolve"] == [], "jóváhagyás előtt nincs törlés"
        assert kep.exists()

    def test_jovahagyasra_a_vegleges_torles_tenyleg_torol(
        self, controller, tmp_path, monkeypatch
    ):
        _shell(monkeypatch, 0x0F)
        kep = _kep(tmp_path)
        esemenyek = _figyel(controller)
        controller.deletePhoto(str(kep))

        controller.deletePhotoPermanently(str(kep))

        assert not kep.exists()
        assert [Path(p) for p in esemenyek["torolve"]] == [kep]
        assert esemenyek["hiba"] == []

    def test_cancel_utan_a_fajl_marad(self, controller, tmp_path, monkeypatch):
        """A Cancel egyszerűen NEM hív semmit: a fájl érintetlen marad."""
        _shell(monkeypatch, 0x0F)
        kep = _kep(tmp_path)
        esemenyek = _figyel(controller)

        controller.deletePhoto(str(kep))

        assert kep.exists()
        assert esemenyek["torolve"] == []

    @pytest.mark.parametrize("kod", [0x02, 0x05, 0x0E, 0x10, 0x7C, 0x402])
    def test_mas_hibakod_hiba_es_nem_kerdez_nem_torol(
        self, controller, tmp_path, monkeypatch, kod
    ):
        hivasok = _shell(monkeypatch, kod)
        kep = _kep(tmp_path)
        esemenyek = _figyel(controller)

        controller.deletePhoto(str(kep))

        assert esemenyek["kerdes"] == [], (
            f"a {kod:#x} hibakódnál nem szabad végleges törlést kérdezni"
        )
        assert [muvelet for muvelet, _ in esemenyek["hiba"]] == ["delete"]
        assert esemenyek["torolve"] == []
        assert kep.exists()
        assert len(hivasok) == 1, "újrapróbálás csak a 0x0f ágon van"

    def test_sikeres_lomtarazas_nem_kerdez(
        self, controller, tmp_path, monkeypatch
    ):
        _shell(monkeypatch, 0)
        kep = _kep(tmp_path)
        esemenyek = _figyel(controller)

        controller.deletePhoto(str(kep))

        assert esemenyek["kerdes"] == []
        assert [Path(p) for p in esemenyek["torolve"]] == [kep]
