"""Az „aa" mód második felének CSAK MEMÓRIÁBAN élő lánca (#3014).

## Miért

Az eredetiben az „aa" mód két fele két önálló szerkesztési állapot
ugyanarról a fotóról (`docs/specs/ui-audit-editor.md` 4/b.1). Nálunk a
szerkesztő minden lépése azonnal a `.picasa.ini`-be ír — ha a második fél is
írna, a két fél ugyanazt a `filters=` sort írná felül egymás elől. Ezért a
KIJELÖLT fél (a fő vezérlő) ír, a másik csak memóriában él, és a kilépéskori
döntés írja ki, ha azt kell megtartani.

## Amit ez az őr állít

- memóriás munkamenetben egy effekt NEM kerül az ini-be;
- a `chainValue` a fél jelenlegi lánca, a `setChainValue` lecseréli;
- a `persistChain` kiírja a memóriában élő láncot;
- a sima `beginEdit` visszakapcsolja az írást (AB módban a második rekesz
  más fotót kap, azt nem szabad memóriában ragadni).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def vezerlo(qt_app):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditController(EditPreviewProvider(), slot="masodik")


@pytest.fixture
def foto(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


def _ini_lanc(foto) -> str:
    ini = foto.parent / ".picasa.ini"
    if not ini.exists():
        return ""
    for sor in ini.read_text(encoding="utf-8").splitlines():
        if sor.startswith("filters="):
            return sor[len("filters=") :]
    return ""


class TestAMemoriasMunkamenet:
    def test_az_effekt_NEM_kerul_az_inibe(self, vezerlo, foto):
        vezerlo.beginEditInMemory("1", str(foto))
        vezerlo.applyEffect("bw")
        assert "bw" in vezerlo.chainValue
        assert _ini_lanc(foto) == ""

    def test_a_mentett_lanccal_indul(self, vezerlo, foto):
        vezerlo.beginEdit("1", str(foto))
        vezerlo.applyEffect("sepia")
        mentett = _ini_lanc(foto)
        vezerlo.beginEditInMemory("1", str(foto))
        assert vezerlo.chainValue == mentett

    def test_a_persistChain_kiirja(self, vezerlo, foto):
        vezerlo.beginEditInMemory("1", str(foto))
        vezerlo.applyEffect("bw")
        vezerlo.persistChain()
        assert _ini_lanc(foto) == vezerlo.chainValue

    def test_a_sima_beginEdit_visszakapcsolja_az_irast(self, vezerlo, foto):
        vezerlo.beginEditInMemory("1", str(foto))
        vezerlo.beginEdit("1", str(foto))
        vezerlo.applyEffect("bw")
        assert "bw" in _ini_lanc(foto)


class TestANaplo:
    """#644: minden kiírt lánc a tartós naplóba is kerül (`chainSaved`)."""

    def test_memoriasban_NEM_jelez(self, vezerlo, foto):
        jelzesek = []
        vezerlo.chainSaved.connect(lambda ut, lanc: jelzesek.append(lanc))
        vezerlo.beginEditInMemory("1", str(foto))
        vezerlo.applyEffect("bw")
        assert jelzesek == []

    def test_a_persistChain_jelez(self, vezerlo, foto):
        jelzesek = []
        vezerlo.chainSaved.connect(lambda ut, lanc: jelzesek.append(lanc))
        vezerlo.beginEditInMemory("1", str(foto))
        vezerlo.applyEffect("bw")
        vezerlo.persistChain()
        assert jelzesek == [vezerlo.chainValue]

    def test_az_alkalmazas_a_masodik_rekeszt_is_naplozza(self):
        """A bekötés az `application.py`-ban él (a teljes indítás tesztben
        nem fut) — forrás-szintű őr."""
        from pathlib import Path

        import picasapy.app.application as alkalmazas

        forras = Path(alkalmazas.__file__).read_text(encoding="utf-8")
        assert (
            "edit_controller_masodik.chainSaved.connect(controller.recordSavedChain)"
            in forras
        )


class TestALancCsere:
    def test_a_setChainValue_lecsereli_es_ir(self, vezerlo, foto):
        vezerlo.beginEdit("1", str(foto))
        vezerlo.applyEffect("bw")
        masik = vezerlo.chainValue
        vezerlo.applyEffect("sepia")
        vezerlo.setChainValue(masik)
        assert vezerlo.chainValue == masik
        assert _ini_lanc(foto) == masik

    def test_a_setChainValue_memoriasban_nem_ir(self, vezerlo, foto):
        vezerlo.beginEditInMemory("1", str(foto))
        vezerlo.setChainValue("")
        vezerlo.applyEffect("bw")
        lanc = vezerlo.chainValue
        vezerlo.setChainValue(lanc)
        assert _ini_lanc(foto) == ""

    def test_a_visszavonas_a_lanc_retegeit_koveti(self, vezerlo, foto):
        """Csere után a visszavonás az ÚJ lánc rétegeit bontja le."""
        vezerlo.beginEditInMemory("1", str(foto))
        vezerlo.applyEffect("bw")
        vezerlo.applyEffect("sepia")
        ket_reteg = vezerlo.chainValue
        vezerlo.setChainValue("")
        vezerlo.setChainValue(ket_reteg)
        vezerlo.undo()
        assert "sepia" not in vezerlo.chainValue
        assert "bw" in vezerlo.chainValue


class TestACsereEszkozallapota:
    """#3644 3.: a lánc-csere (fókuszváltás) a fél ALKALMAZATLAN
    eszközpufferét nem viheti át a másik fél láncára."""

    def test_a_retusalas_puffere_urul(self, vezerlo, foto):
        vezerlo.beginEdit("1", str(foto))
        vezerlo.enterRetouchTool()
        vezerlo.beginRetouchPatch(0.2, 0.2)
        vezerlo.commitRetouchPatch(0.6, 0.6)
        vezerlo.beginRetouchPatch(0.3, 0.3)
        assert vezerlo.retouchPendingCount == 1
        vezerlo.setChainValue("")
        assert vezerlo.retouchPendingCount == 0
        assert not vezerlo.retouchPatchPending
        assert not vezerlo.canUndoPatch

    def test_a_vorosszem_regiok_urulnek(self, vezerlo, foto):
        vezerlo.beginEdit("1", str(foto))
        vezerlo.enterRedeyeTool()
        vezerlo.addRedeyeRegion(0.1, 0.1, 0.3, 0.3)
        assert vezerlo.redeyeRegionCount == 1
        vezerlo.setChainValue("")
        assert vezerlo.redeyeRegionCount == 0
        assert not vezerlo.canUndoRedeyeRegion

    def test_a_festett_maszk_urul(self, vezerlo, foto):
        vezerlo.beginEdit("1", str(foto))
        vezerlo.applyEffect("soften")
        lanc = vezerlo.chainValue
        vezerlo.paintStroke(0.5, 0.5)
        assert vezerlo._paint_strokes()
        vezerlo.setChainValue(lanc)
        assert vezerlo._paint_strokes() == ()


class TestASwapAaFocus:
    """#3649: a `swapAaFocus` (a valódi fókuszváltás) a festett maszkot A
    PÁRRAL cseréli, nem üríti — a félkész festés a saját felén marad."""

    @pytest.fixture
    def part(self, qt_app):
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider

        szolgaltato = EditPreviewProvider()
        elso = EditController(szolgaltato)
        masodik = EditController(szolgaltato, slot="masodik")
        elso.link_aa_partner(masodik)
        masodik.link_aa_partner(elso)
        return elso, masodik

    def test_a_festett_maszk_oda_vissza_cserelodik(self, part, foto):
        elso, masodik = part
        elso.beginEditInMemory("1", str(foto))
        masodik.beginEditInMemory("1", str(foto))
        elso.applyEffect("soften")
        elso.paintStroke(0.5, 0.5)
        assert elso._paint_strokes()
        assert not masodik._paint_strokes()

        elso.swapAaFocus()
        assert not elso._paint_strokes()
        assert masodik._paint_strokes()

        elso.swapAaFocus()
        assert elso._paint_strokes()
        assert not masodik._paint_strokes()

    def test_a_lanc_is_cserelodik(self, part, foto):
        elso, masodik = part
        elso.beginEditInMemory("1", str(foto))
        masodik.beginEditInMemory("1", str(foto))
        elso.applyEffect("bw")
        lanc_elso = elso.chainValue
        lanc_masodik = masodik.chainValue
        elso.swapAaFocus()
        assert elso.chainValue == lanc_masodik
        assert masodik.chainValue == lanc_elso

    def test_par_nelkul_no_op(self, vezerlo, foto):
        vezerlo.beginEdit("1", str(foto))
        vezerlo.applyEffect("soften")
        vezerlo.paintStroke(0.5, 0.5)
        vezerlo.swapAaFocus()
        assert vezerlo._paint_strokes()


class TestAHid:
    def test_a_hid_tovabbadja(self, vezerlo, foto):
        from picasapy.app.second_preview import SecondPreview

        hid = SecondPreview(vezerlo)
        hid.beginEditInMemory("1", str(foto))
        vezerlo.applyEffect("bw")
        assert hid.chainValue == vezerlo.chainValue
        assert _ini_lanc(foto) == ""
        hid.setChainValue("")
        assert hid.chainValue == ""
        vezerlo.applyEffect("sepia")
        hid.persistChain()
        assert "sepia" in _ini_lanc(foto)
