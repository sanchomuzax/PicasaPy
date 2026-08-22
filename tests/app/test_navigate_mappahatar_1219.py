"""A nyilas léptetés MEGÁLL a mappahatáron (#1219).

## A bizonyíték (a kutatói kör mérése, spec 15. szakasz)

Az eredetiben ez **nem ellenőrzés, hanem szerkezet**: a feed konténere
(`0x0076a390`, `CMultiAlbumNode` vtábla 33. rés) mindig PONTOSAN EGY
albumsor kijelölés-csomópontját éri el — nincs ciklus a `[+0x300]`
sortömbön. Mind a négy mag a saját csomópontja `count()`/`itemAt()`
párján iterál.

**A korábban NYITOTT kérdés eldőlt:** a léptetés a mappa végén **megáll**.

```asm
0x00718031  cmp/jbe        ; ELŐJEL NÉLKÜLI — a -1-re csökkenő index is ide fut,
                           ; mindkét vég ugyanaz az ág
0x00717e76  [this+0x2e0] = 0xFFFFFFFF   ; törli a jelölőt, ÉS NEM jelöl ki újat
```

⚠️ Tehát **nem lép át és nem fordul át** — ezért NEM építünk átvitelt a
szomszéd csoportra. A mi `navigate()`-ünk fel/le iránynál SZÁNDÉKOSAN a
szomszéd csoportra ugrott (a docstring ki is mondta) — ez az eltérés.
"""

from __future__ import annotations



def _modell(csoportok: list[int]):
    """Feed-modell megadott mappacsoport-méretekkel.

    A `PhotoGridModel` a `folder_path` VÁLTÁSÁBÓL képzi a csoportokat
    (`_group_bounds`), tehát elég külön mappát adni a rekordoknak."""
    from picasapy.app.models import PhotoGridModel
    from picasapy.index import PhotoRecord

    fotok = []
    for i, darab in enumerate(csoportok):
        for j in range(darab):
            fotok.append(
                PhotoRecord(
                    id=i * 100 + j,
                    folder_path=f"/mappa{i}",
                    name=f"k{j}.jpg",
                    kind="image",
                    size=1,
                    mtime_ns=1,
                    star=False,
                    caption=None,
                    keywords=(),
                    rotate_steps=0,
                    filters=None,
                    taken_at=None,
                    orientation=1,
                    width=100,
                    height=100,
                    hidden=False,
                )
            )
    modell = PhotoGridModel()
    modell.set_photos(tuple(fotok))
    return modell


class TestNavigateMegall:
    """Mind a NÉGY irány a mappacsoporton belül marad."""

    def test_lefele_a_csoport_aljan_MEGALL(self):
        """⚠️ Eddig a szomszéd csoport azonos oszlopára ugrott."""
        modell = _modell([4, 4])  # 0-3 az első, 4-7 a második mappa
        # 2 oszlop: a 0. csoport rácssorai [0,1] és [2,3]
        cel = modell.navigate(2, "down", 2)

        assert cel < 4, (
            f"a lefelé lépés átment a második mappába (cél={cel})"
        )

    def test_felfele_a_csoport_tetejen_MEGALL(self):
        modell = _modell([4, 4])
        cel = modell.navigate(4, "up", 2)  # a MÁSODIK csoport első sora

        assert cel >= 4, (
            f"a felfelé lépés visszament az első mappába (cél={cel})"
        )

    def test_jobbra_a_csoport_vegen_MEGALL(self):
        """A vízszintes léptetés is a csomóponton belül marad."""
        modell = _modell([4, 4])
        cel = modell.navigate(3, "right", 2)  # az első csoport UTOLSÓ képe

        assert cel < 4, f"a jobbra lépés átment a második mappába (cél={cel})"

    def test_balra_a_csoport_elejen_MEGALL(self):
        modell = _modell([4, 4])
        cel = modell.navigate(4, "left", 2)  # a második csoport ELSŐ képe

        assert cel >= 4, f"a balra lépés visszament az első mappába (cél={cel})"

    def test_a_csoporton_BELUL_valtozatlan(self):
        """⚠️ A működő viselkedés nem romolhat el."""
        modell = _modell([4, 4])

        assert modell.navigate(0, "right", 2) == 1
        assert modell.navigate(1, "left", 2) == 0
        assert modell.navigate(0, "down", 2) == 2
        assert modell.navigate(2, "up", 2) == 0
