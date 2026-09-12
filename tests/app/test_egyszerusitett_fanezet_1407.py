"""#1407: az „Egyszerűsített fanézet" a fa HATÓKÖRÉT szűkíti.

## A mérés (`docs/specs/picasa-mappanezet.md` 4.1)

```
0x0057517c  cmp ebp, "all"            ; csak az „all" gyökérnél
0x00575194  push "SimplifiedHierarchy"
0x005751ec  mov ebp, "watched"        ; ⇐ A GYÖKÉR KICSERÉLŐDIK
```

`SimplifiedHierarchy = 1` esetén az `all` gyökér `watched`-re cserélődik:
az egyszerűsített fa **csak a figyelt mappák ágait** mutatja.

## Ami eddig nálunk volt

Útvonal-tömörítés: az egygyermekes, fotó nélküli köztes szintek
összevonása. A látvány hasonló, a mechanizmus más — és a hatóköre is: a mi
verziónk SOSEM rejtett el mappát, az eredeti igen.

## Egy mért szűrő is van

```
0x0057430b  cmp eax, 2
0x0057430e  jbe …                      ; ⇐ átugorja
```

A két karakternél nem hosszabb bejegyzések kimaradnak — a puszta
meghajtó-gyökerek (`C:`, `/`) nem lesznek ágak.
"""

from __future__ import annotations

import pytest

from picasapy.app.folder_hierarchy import build_hierarchy


def _nevek(csomopont) -> list[str]:
    return [gy.name for gy in csomopont.children]


def _utvonalak(csomopont) -> list[str]:
    return [gy.path for gy in csomopont.children]


MAPPAK = [
    {"path": "/media/kepek/2024", "count": 3},
    {"path": "/media/kepek/2025", "count": 5},
    {"path": "/home/sancho/Letoltesek", "count": 2},
    {"path": "/mnt/idegen/valami", "count": 7},
]


class TestAHatokor:
    """A figyelt mappák ágai látszanak, a többi NEM."""

    def test_a_figyelt_mappa_a_gyoker(self):
        fa = build_hierarchy(
            MAPPAK, simplified=True, watched_roots=("/media/kepek",)
        )
        assert _utvonalak(fa) == ["/media/kepek"]

    def test_a_NEM_figyelt_ag_eltunik(self):
        """Ez a különbség a régi viselkedéshez képest: a szűkítés REJT."""
        fa = build_hierarchy(
            MAPPAK, simplified=True, watched_roots=("/media/kepek",)
        )
        assert not any("idegen" in ut for ut in _utvonalak(fa))

    def test_TOBB_figyelt_mappa_tobb_ag(self):
        fa = build_hierarchy(
            MAPPAK, simplified=True,
            watched_roots=("/media/kepek", "/home/sancho/Letoltesek"),
        )
        assert sorted(_utvonalak(fa)) == [
            "/home/sancho/Letoltesek", "/media/kepek"
        ]

    def test_a_figyelt_ag_GYERMEKEI_megmaradnak(self):
        fa = build_hierarchy(
            MAPPAK, simplified=True, watched_roots=("/media/kepek",)
        )
        ag = fa.children[0]
        assert sorted(gy.name for gy in ag.children) == ["2024", "2025"]

    def test_a_darabszam_a_reszfa_osszege(self):
        fa = build_hierarchy(
            MAPPAK, simplified=True, watched_roots=("/media/kepek",)
        )
        assert fa.children[0].total == 8


class TestAMertSzuro:
    """`cmp eax, 2 / jbe` — a két karakternél nem hosszabb bejegyzés kimarad."""

    @pytest.mark.parametrize("rovid", ["/", "C:", ""])
    def test_a_rovid_bejegyzes_nem_lesz_ag(self, rovid):
        fa = build_hierarchy(
            MAPPAK, simplified=True, watched_roots=(rovid, "/media/kepek")
        )
        assert _utvonalak(fa) == ["/media/kepek"]


class TestAmiNEM_valtozik:
    def test_a_FANEZET_valtozatlan(self):
        """A szűkítés CSAK az egyszerűsített módra vonatkozik."""
        fa = build_hierarchy(MAPPAK, simplified=False)
        assert len(fa.children) >= 1
        osszes = fa.total
        assert osszes == 17

    def test_figyelt_lista_NELKUL_nem_rejtunk_el_semmit(self):
        """Ha nem tudjuk, mi a figyelt mappa, a szűkítés NEM találgat.

        Üres listára a teljes fa marad — az „elrejtettük a felhasználó
        mappáit" rosszabb kimenet, mint a szűkítés elmaradása."""
        szukitett = build_hierarchy(MAPPAK, simplified=True, watched_roots=())
        teljes = build_hierarchy(MAPPAK, simplified=False)
        assert szukitett.total == teljes.total


class TestAVezerlo:
    """A vezérlő oldala: a figyelt mappák átvétele és a szűkítés."""

    @pytest.fixture
    def vezerlo(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app.folder_hierarchy_controller import (
            FolderHierarchyController,
        )

        ctl = FolderHierarchyController(
            settings=QSettings(
                str(tmp_path / "beall.ini"), QSettings.Format.IniFormat
            )
        )
        ctl.setFolders(MAPPAK)
        return ctl

    def _utak(self, ctl) -> list[str]:
        """A fa MINDEN csomópontjának útvonala.

        A sorlistát nem használjuk: a fa csukottan indul, tehát az csak a
        gyökeret mutatná, és a próba akkor is „zöld" lenne, ha a szűkítés
        egyáltalán nem fut le."""
        def bejar(csomopont):
            yield csomopont.path
            for gyerek in csomopont.children:
                yield from bejar(gyerek)

        return list(bejar(ctl._tree()))

    def test_a_szukites_a_figyelt_mappara_hat(self, vezerlo):
        vezerlo.setWatchedRoots(["/media/kepek"])
        vezerlo.setSimplified(True)

        utak = self._utak(vezerlo)
        assert any("/media/kepek" in ut for ut in utak)
        assert not any("idegen" in ut for ut in utak), (
            f"a nem figyelt ág benne maradt: {utak}"
        )

    def test_kikapcsolva_MINDEN_ag_latszik(self, vezerlo):
        vezerlo.setWatchedRoots(["/media/kepek"])
        vezerlo.setSimplified(True)
        vezerlo.setSimplified(False)

        assert any("idegen" in ut for ut in self._utak(vezerlo))

    def test_a_figyelt_lista_KESOBBI_valtozasa_is_hat(self, vezerlo):
        """A mappakezelőben hozzáadott mappa azonnal ággá válik."""
        vezerlo.setWatchedRoots(["/media/kepek"])
        vezerlo.setSimplified(True)
        assert not any("idegen" in ut for ut in self._utak(vezerlo))

        vezerlo.setWatchedRoots(["/media/kepek", "/mnt/idegen"])

        assert any("idegen" in ut for ut in self._utak(vezerlo))
