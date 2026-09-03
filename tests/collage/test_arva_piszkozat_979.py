"""Az elárvult kollázs-piszkozat helyreállítása induláskor (#979).

## Az eredeti

A #960 bekötötte az `autosave.cxf` **írását**. A másik fele hiányzott: mi
történik a piszkozattal a KÖVETKEZŐ indításkor. Az eredeti Picasa
induláskor megkeresi az elárvult automentést, **átnevezi**, és indexeli,
hogy a felhasználó megtalálja a Kollázsok albumban — nálunk a fájl eddig
ott maradt, és a következő munkamenet felülírta.

## A MÉRT értékek

| mi | érték | cím |
|---|---|---|
| belépő induláskor | — | `0x00689f40` → `0x008419e0` |
| az új név | `collage::recoveredautosave` | `0x00841b65` |
| ütközés-számozás | `"%s%lu"` — szóköz NÉLKÜL | `0x00993030` (`0x00841bb8`) |
| helykitöltő méret | **640 × 480** | `0x0068a767` (0x280), `0x0068a79c` (0x1e0) |
| helykitöltő szín | **`0xFF3F3F3F`** | `0x0068a7c6` |
| helykitöltő minőség | **q85** | `0x0068a7f6` (`{1, 4, 0x55}`) |

A név a HIVATALOS magyar fordításból (`stringres`:
`collage::recoveredautosave` → „Helyreállított automatikus másolat"), nem
a mi megfogalmazásunkból.
"""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.collage.autosave import (
    AUTOSAVE_NAME,
    RECOVERED_NAME,
    recover_orphan_draft,
    write_autosave,
)
from picasapy.collage.cxf import CxfNode, CxfProject


def _projekt(kep_ut: str = "") -> CxfProject:
    csomopontok = (CxfNode(src=kep_ut),) if kep_ut else ()
    return CxfProject(nodes=csomopontok)


@pytest.fixture
def mappa(tmp_path):
    return tmp_path


class TestAzAtnevezes:
    def test_a_HIVATALOS_magyar_nevre_nevez(self, mappa):
        write_autosave(mappa, _projekt())
        uj = recover_orphan_draft(mappa)
        assert uj is not None
        assert uj.name == f"{RECOVERED_NAME}.cxf"
        assert RECOVERED_NAME == "Helyreállított automatikus másolat"
        assert not (mappa / AUTOSAVE_NAME).exists(), "az árva fájl ottmaradt"

    def test_a_jpg_parja_is_atmegy(self, mappa):
        write_autosave(mappa, _projekt())
        (mappa / "autosave.jpg").write_bytes(b"nem valodi jpeg")
        recover_orphan_draft(mappa)
        assert (mappa / f"{RECOVERED_NAME}.jpg").is_file()
        assert not (mappa / "autosave.jpg").exists()

    def test_nincs_piszkozat_eseten_None(self, mappa):
        assert recover_orphan_draft(mappa) is None


class TestAzUtkozesSzamozasa:
    def test_szokoz_NELKUL_szamoz(self, mappa):
        """MÉRT: `"%s%lu"` — „…másolat1", nem „…másolat 1"."""
        (mappa / f"{RECOVERED_NAME}.cxf").write_text("foglalt", encoding="utf-8")
        write_autosave(mappa, _projekt())
        uj = recover_orphan_draft(mappa)
        assert uj.name == f"{RECOVERED_NAME}1.cxf", uj.name

    def test_tobbszoros_utkozesnel_tovabb_szamoz(self, mappa):
        for utotag in ("", "1"):
            (mappa / f"{RECOVERED_NAME}{utotag}.cxf").write_text(
                "foglalt", encoding="utf-8"
            )
        write_autosave(mappa, _projekt())
        uj = recover_orphan_draft(mappa)
        assert uj.name == f"{RECOVERED_NAME}2.cxf", uj.name


class TestAHelykitoltoKep:
    def test_kep_nelkul_helykitoltot_ir(self, mappa):
        write_autosave(mappa, _projekt())
        recover_orphan_draft(mappa)
        kep_ut = mappa / f"{RECOVERED_NAME}.jpg"
        assert kep_ut.is_file(), "nem készült helykitöltő"
        # #2084: a helykitöltő neve ÉKEZETES („Helyreállított automatikus
        # másolat"), a `cv2.imread` fájlútvonalas alakja pedig Windowson az
        # ANSI kódlapon megy át — ott némán `None`-t ad (#190/#1991). A
        # gyártó oldal ezért ír `imencode` + Python-IO párossal
        # (`collage/autosave.py::_helykitolto`); az olvasó oldalnak
        # ugyanígy kell. Ez volt a windows-láb utolsó ismert bukása, és
        # ettől ment a main CI-je minden kód-merge után pirosra.
        kep = cv2.imdecode(
            np.frombuffer(kep_ut.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        assert kep is not None
        assert (kep.shape[1], kep.shape[0]) == (640, 480), "a MÉRT méret 640×480"
        #: `0xFF3F3F3F` → BGR (0x3F, 0x3F, 0x3F) = (63, 63, 63).
        #: A JPEG veszteséges, ezért tűréssel mérünk.
        assert np.all(np.abs(kep.astype(int) - 63) <= 3), (
            f"a helykitöltő színe nem #3F3F3F: {kep[0, 0]}"
        )

    def test_NEM_a_fajlutvonalas_irot_hasznalja(self, mappa, monkeypatch):
        """A helykitöltő neve ékezetes, ezért a `cv2` fájlútvonalas írója
        Windowson némán nem írná ki (#190).

        Foga: a `cv2.imwrite`-ot robbanóra cseréljük. Ha a megvalósítás
        mégis azon menne, a teszt elbukik — Linuxon is, ahol a valódi
        hiba nem jelentkezne.
        """

        def _tilos(*_args, **_kwargs):  # pragma: no cover - csak bukáskor fut
            raise AssertionError(
                "a helykitöltő fájlútvonalas írót hív — ékezetes néven "
                "Windowson némán nem ír (#190)"
            )

        monkeypatch.setattr(cv2, "imwrite", _tilos)
        write_autosave(mappa, _projekt())
        recover_orphan_draft(mappa)
        assert (mappa / f"{RECOVERED_NAME}.jpg").is_file()

    def test_MEGLEVO_kep_mellett_nem_ir_helykitoltot(self, mappa):
        """Ha a `.jpg` pár megvan, azt kell átnevezni — nem felülírni."""
        write_autosave(mappa, _projekt())
        (mappa / "autosave.jpg").write_bytes(b"sajat tartalom")
        recover_orphan_draft(mappa)
        assert (mappa / f"{RECOVERED_NAME}.jpg").read_bytes() == b"sajat tartalom"


class TestNemFutLeKetszer:
    def test_masodszorra_None(self, mappa):
        """A helyreállítás után nincs `autosave.cxf` — a második hívás
        nem csinálhat semmit, különben minden indulás új másolatot
        gyártana."""
        write_autosave(mappa, _projekt())
        assert recover_orphan_draft(mappa) is not None
        assert recover_orphan_draft(mappa) is None
        #: és nem keletkezett „…másolat1"
        assert not (mappa / f"{RECOVERED_NAME}1.cxf").exists()


class TestABekotes:
    """A »nem állítom vissza« ág MEGŐRIZ, nem töröl (#979).

    ⚠️ Az eredeti Picasa INDULÁSKOR, kérdés nélkül nevezi át az árvát
    (`0x008419e0`). Nálunk van egy felajánlás-lépés (#1064), ami az
    eredetiben nincs — ha induláskor neveznénk át, a felajánlásnak nem
    maradna mit felajánlania. Ezért a „nem" ágra van kötve; a végeredmény
    ugyanaz: a piszkozat megmarad, néven nevezve.

    A MENTÉS utáni eldobás továbbra is törlés — ott a piszkozat betöltötte
    a szerepét.
    """

    def test_a_discard_ag_ATNEVEZ_nem_torol(self):
        from pathlib import Path

        import picasapy.app.create_controller as cc

        forras = Path(cc.__file__).read_text(encoding="utf-8")
        #: a blokk a KÖVETKEZŐ függvényig tart — egy fix karakterablak
        #: átlógna a szomszédokba, és ott a `_drop_collage_draft` jogosan
        #: szerepel (a mentés utáni ág).
        kezdet = forras.find("def discardCollageDraft")
        veg = forras.find("\n    def ", kezdet + 10)
        blokk = forras[kezdet:veg if veg > 0 else None]
        assert "recover_orphan_draft" in blokk, (
            "a »nem« ág még mindig TÖRLI a piszkozatot — az eredeti megőrzi"
        )
        #: ⚠️ A HÍVÁST keressük, nem a puszta nevet: a függvény
        #: docstringje SZÁNDÉKOSAN megemlíti a `_drop_collage_draft`-ot
        #: (azt magyarázza, miért marad AZ törlés). A névre keresve a saját
        #: indoklásunk buktatná a tesztet — ugyanaz a csapda, mint amikor
        #: egy forrás-szintű őr a kódot és a kommentet nem különbözteti meg.
        assert "self._drop_collage_draft()" not in blokk, (
            "a »nem« ág az eldobó úton megy"
        )

    def test_a_MENTES_utani_ag_tovabbra_is_torol(self):
        """Ellenpróba: a megőrzés NEM terjedhet ki a mentés utáni ágra,
        különben minden sikeres mentés szemetet hagyna."""
        from pathlib import Path

        import picasapy.app.create_controller as cc

        forras = Path(cc.__file__).read_text(encoding="utf-8")
        kezdet = forras.find("def _drop_collage_draft")
        veg = forras.find("\n    @", kezdet + 10)
        blokk = forras[kezdet:veg if veg > 0 else None]
        assert "discard_autosave" in blokk
        assert "recover_orphan_draft" not in blokk
