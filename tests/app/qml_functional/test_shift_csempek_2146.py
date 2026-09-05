"""#2146 — a Shift lenyomva tartása KILENC csempén másik szűrőt ad.

## A mérés

Az eredeti a fül felépülésekor **egyszer** lekérdezi a Shift állapotát
(`GetAsyncKeyState(VK_SHIFT)`, `0x005d7c91`–`0x005d7cc0`), és eltárolja
(`[ecx+0x33a8]`). A csempe-tábla (`0x00c7e5a0`) rekordjai **hármasak** —
elsődleges, másodlagos, 0 —, és a másodlagos akkor és csak akkor fut, ha a
tárolt bit igaz (`0x005d7d63`–`0x005d7d78`).

| elsődleges | Shift-tel | a másodlagos felirata |
|---|---|---|
| `unsharp2` | `unsharp` | Sharpen (Old) |
| `picnikgrain` | `grain` | Film Grain (Old) |
| `picniktint` | `tint` | Tint (Old) |
| `glow2` | `glow` | Glow (Old) |
| `dir_tint` | `radtint` | Radial Tint |
| `heatmap` | `nightvision` | Night Vision |
| `vignette` | `matte` | Matte |
| `pixelate` | `picnikfocalpixelate` | Focal Pixelate |
| `border` | `roundededges` | Rounded Edges |

A maradék 27 csempén a Shift **nem hat** (a második mező `NULL`).

⚠️ Négy másodlagos felirata „(Old)", öté viszont **saját név** — ott a
Shift nem régi változatot, hanem MÁSIK effektet ad.

⚠️ A `picnikgrain` nálunk KÉT csempén szerepel (`effectGrain2` az 1.
fülön, `effectPicnikGrain` a 4.-en) — ez a MI kettőzésünk, az eredetiben
egy csempe. Mindkettő ugyanúgy viselkedik, különben a felhasználó
ugyanattól az effekttől két különböző Shift-választ kapna.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app as app_csomag

_QML_DIR = Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
_FULEK = {
    nev: (_QML_DIR / f"EditorEffectsTab{nev}.qml").read_text(encoding="utf-8")
    for nev in ("1", "2", "3", "4")
}
_PANEL = (_QML_DIR / "EditorPanel.qml").read_text(encoding="utf-8")

#: A MÉRT kilenc pár: elsődleges -> (másodlagos, a másodlagos felirata)
PAROK = {
    "unsharp2": ("unsharp", "Sharpen (Old)"),
    "picnikgrain": ("grain", "Film Grain (Old)"),
    "picniktint": ("tint", "Tint (Old)"),
    "glow2": ("glow", "Glow (Old)"),
    "dir_tint": ("radtint", "Radial Tint"),
    "heatmap": ("nightvision", "Night Vision"),
    "vignette": ("matte", "Matte"),
    "pixelate": ("picnikfocalpixelate", "Focal Pixelate"),
    "border": ("roundededges", "Rounded Edges"),
}

#: Két csempe, amire a Shift NEM hat — a változatlanság is állítás.
SHIFT_MENTES = ("sepia", "bw")


def _osszes_ful() -> str:
    return "\n".join(_FULEK.values())


class TestAKapcsolo:
    def test_a_panel_TAROLJA_a_shift_allapotot(self):
        assert "shiftMasodlagos" in _PANEL, (
            "a panelnek nincs Shift-állapota — az eredeti a fül "
            "felépülésekor EGYSZER kérdezi le, nem folyamatosan figyeli"
        )

    def test_a_vezerlo_tudja_lekerdezni(self):
        import picasapy.app.edit_controller as ec

        assert hasattr(ec.EditController, "shiftLenyomva"), (
            "nincs mód lekérdezni a Shift állapotát a QML-ből"
        )

    def test_a_FUL_felepulesekor_dol_el(self):
        """Nem billeg a Shift minden le-fel nyomására."""
        assert "onVisibleChanged" in _PANEL or "onActiveTabChanged" in _PANEL


class TestAKilencPar:
    def test_mind_a_kilenc_masodlagos_szuro_ott_van(self):
        forras = _osszes_ful()
        hianyzik = [
            elsodleges
            for elsodleges, (masodlagos, _felirat) in PAROK.items()
            if f'"{masodlagos}"' not in forras
        ]
        assert not hianyzik, (
            f"nincs Shift-ág ezeken a csempéken: {hianyzik}"
        )

    def test_mind_a_kilenc_masodlagos_FELIRAT_ott_van(self):
        forras = _osszes_ful()
        hianyzik = [
            felirat
            for _m, (_masodlagos, felirat) in PAROK.items()
            if f'qsTr("{felirat}")' not in forras
        ]
        assert not hianyzik, (
            f"a csempe nem mondja meg, mit kap a felhasználó Shifttel: "
            f"{hianyzik}"
        )

    def test_a_valasztas_a_SHIFT_allapotatol_fugg(self):
        """Minden érintett csempén a panel Shift-állapota dönt.

        ⚠️ A választó KIFEJEZÉST keressük (`? "másodlagos" : "elsődleges"`),
        nem a szűrőnév első előfordulását: a név a kommentekben is szerepel,
        és ott találva a próba hamis helyet mérne.
        """
        forras = _osszes_ful()
        for elsodleges, (masodlagos, _f) in PAROK.items():
            valaszto = f'? "{masodlagos}" : "{elsodleges}"'
            assert valaszto in forras, (
                f"a(z) {elsodleges} -> {masodlagos} váltás nincs bekötve"
            )
            kezd = forras.index(valaszto)
            kornyek = forras[max(0, kezd - 200) : kezd]
            assert "shiftMasodlagos" in kornyek, (
                f"a(z) {elsodleges} -> {masodlagos} váltás nem a Shift "
                f"állapotától függ"
            )


class TestAShiftMentesCsempek:
    def test_nem_kaptak_masodlagos_agat(self):
        forras = _osszes_ful()
        for nev in SHIFT_MENTES:
            kezd = forras.find(f'effectRequested("{nev}")')
            assert kezd > 0, f"nincs ilyen csempe: {nev}"
            sor_eleje = forras.rfind("\n", 0, kezd)
            assert "shiftMasodlagos" not in forras[sor_eleje:kezd], (
                f"a(z) {nev} csempére a Shift hat, pedig a mérés szerint a "
                f"második mezője NULL"
            )


class TestAFrissitesBEKOTESE:
    """⚠️ Ez az osztály a MAGVETÉSBŐL született: a frissítő hívás törlésére
    egyetlen próba sem bukott el, pedig enélkül a Shift-állapot örökre
    hamis maradna — a kilenc csempe soha nem váltana."""

    def test_a_fulvaltas_UJRAOLVASSA(self):
        kezd = _PANEL.index("onActiveTabChanged")
        blokk = _PANEL[kezd : kezd + 900]
        assert "frissitsdAShiftAllapotot()" in blokk, (
            "fülváltáskor nem olvassuk újra a Shift állapotát — az eredeti "
            "a fül FELÉPÜLÉSEKOR teszi"
        )

    def test_INDULASKOR_is_olvas(self):
        assert (
            "Component.onCompleted: panel.frissitsdAShiftAllapotot()" in _PANEL
        ), "induláskor nem olvassuk ki a Shift állapotát"

    def test_a_frissito_a_VEZERLOT_hivja(self):
        # ⚠️ A függvény TELJES törzse kell, kapcsos zárójel szerint vágva:
        # rögzített karakterablakkal egy jogos komment-bővítés kivágná a
        # keresett sort, és a próba hamisan bukna (ez meg is történt).
        kezd = _PANEL.index("function frissitsdAShiftAllapotot")
        nyito = _PANEL.index("{", kezd)
        melyseg = 0
        vege = nyito
        for i in range(nyito, len(_PANEL)):
            if _PANEL[i] == "{":
                melyseg += 1
            elif _PANEL[i] == "}":
                melyseg -= 1
                if melyseg == 0:
                    vege = i + 1
                    break
        blokk = _PANEL[kezd:vege]
        assert "editController.shiftLenyomva()" in blokk, (
            "a frissítő nem a vezérlőt kérdezi — a QML-ből nincs más mód a "
            "pillanatnyi Shift-állapot megismerésére"
        )
        assert 'typeof editController === "undefined"' in blokk, (
            "hiányzik a #305 null-őr: az engine leépítésekor a vezérlő "
            "null lehet"
        )
        assert 'typeof editController.shiftLenyomva !== "function"' in blokk, (
            "⚠️ a null-őr NEM ELÉG: a QML-tesztek csonk vezérlője LÉTEZIK, "
            "csak ezt a metódust nem ismeri — a hívás `TypeError`-t dobna, "
            "az pedig megszakítaná a fülváltás-kezelő hátralévő részét "
            "(a paraméter-panel bezárását). A CI ezt el is kapta."
        )
