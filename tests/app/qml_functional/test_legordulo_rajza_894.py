"""#894 — a legördülő panel és a görgetősáv MÉRT rajza.

A `respack.yt` `listdecrect/listdecrect` rétege (17 × 17, nyújtható)
képpontból olvasva:

| sor | szín | mi ez |
|---|---|---|
| 2 | `#D6D6D6` | lágy árnyék (a kereten KÍVÜL) |
| 3 | `#BABABA` | a keret, 1 px |
| 4–12 | `#E8E8E8` | a kitöltés — **SÍK**, színátmenet nélkül |
| 13 | `#F8F8F8` | belső fénykiemelés alul |
| 14 | `#F0F0F0` | |

A görgetősáv hüvelykje (`scrollart/base_win`, 15 × 25) **vízszintes**
átmenet, függőlegesen állandó: `#B6B6B6` · `#C7C7C7` → `#D9D9D9` →
`#EDEDED` · `#C8C8C8`.

⚠️ A mért értékek a VILÁGOS módra érvényesek; sötét módban a saját
króm-tónusaink állnak (a mért világos szürkékkel a panel olvashatatlan
lenne). Az őr ezért a világos mód színeit méri.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_TEMA = (_QML / "Theme.qml").read_text(encoding="utf-8")
_COMBO = (_QML / "PicasaComboBox.qml").read_text(encoding="utf-8")
_SAV = (_QML / "PicasaScrollBar.qml").read_text(encoding="utf-8")


class TestAMertSzinek:
    @pytest.mark.parametrize(
        "token,vart",
        [
            ("listPanelBg", "#e8e8e8"),
            ("listPanelBorder", "#bababa"),
            ("listPanelShadow", "#d6d6d6"),
            ("listPanelInnerLight", "#f8f8f8"),
            ("listPanelInnerLight2", "#f0f0f0"),
            ("scrollThumbEdgeDark", "#b6b6b6"),
            ("scrollThumbMid", "#d9d9d9"),
            ("scrollThumbLight", "#ededed"),
            ("scrollThumbEdgeSoft", "#c8c8c8"),
        ],
    )
    def test_a_temaban_a_MERT_ertek_all(self, token, vart):
        """A szám a mérésből jön; ha valaki „szebbre" hangolja, ez bukik."""
        kezd = _TEMA.index(f"readonly property color {token}:")
        sor = _TEMA[kezd : _TEMA.index("\n", kezd)]
        assert vart in sor.lower(), f"{token}: nem a mért érték ({sor.strip()})"

    def test_mindegyik_szinnek_van_sotet_valtozata(self):
        for token in ("listPanelBg", "listPanelBorder", "scrollThumbMid"):
            kezd = _TEMA.index(f"readonly property color {token}:")
            assert "dark ?" in _TEMA[kezd : kezd + 120], token


class TestALegorduloPanel:
    def test_SIK_kitoltes_nincs_atmenet(self):
        """A panel az eredetiben SÍK — színátmenet a gomboknál van, itt nem."""
        kezd = _COMBO.index('objectName: "picasaComboPopupBackground"')
        blokk = _COMBO[kezd : kezd + 1400]
        assert "gradient" not in blokk, (
            "színátmenet került a legördülő panel hátterébe (#894)"
        )
        assert "Theme.listPanelBg" in blokk
        assert "Theme.listPanelBorder" in blokk

    def test_a_keret_EGY_kepont(self):
        kezd = _COMBO.index('objectName: "picasaComboPopupPanel"')
        assert "border.width: 1" in _COMBO[kezd : kezd + 400]

    def test_az_arnyek_a_kereten_KIVUL_van(self):
        """A mérés szerint az árnyék-sor a keret ELŐTT áll (kívül)."""
        assert _COMBO.index("Theme.listPanelShadow") < _COMBO.index(
            "Theme.listPanelBorder"
        )

    def test_a_kiemelt_sor_2px_lekerekitesu(self):
        kezd = _COMBO.index('objectName: "picasaComboRowHighlight"')
        assert "radius: 2" in _COMBO[kezd : kezd + 400]

    def test_a_kiemeles_4_keppontal_szelesebb_oldalankent(self):
        assert "highlightOverhang: 4" in _COMBO

    def test_a_forras_megnevezi_a_MERT_reteget(self):
        assert "listdecrect/listdecrect" in _COMBO

    def test_az_EGYSZERUSITES_ki_van_mondva(self):
        """A mért réteg kilencszeletes, 2 px lágy árnyékkal; mi egy képpontot
        adunk. Ha ez nincs kimondva, a komment hazudik."""
        assert "EGYSZERŰSÍTETT" in _COMBO


class TestAGorgetosav:
    def test_a_huvelyk_a_MERT_atmenetet_hasznalja(self):
        kezd = _SAV.index('objectName: "picasaScrollThumb"')
        blokk = _SAV[kezd : kezd + 1600]
        for token in (
            "scrollThumbEdgeDark", "scrollThumbEdgeSoft", "scrollThumbMid",
            "scrollThumbLight",
        ):
            assert f"Theme.{token}" in blokk, token

    def test_az_atmenet_TENGELYE_a_sav_iranyat_koveti(self):
        """A mérés függőleges sávra szól (vízszintes átmenet); vízszintes
        sávnál elfordítva kell."""
        kezd = _SAV.index('objectName: "picasaScrollThumb"')
        blokk = _SAV[kezd : kezd + 1600]
        assert "control.horizontal" in blokk
        assert "Gradient.Vertical" in blokk
        assert "Gradient.Horizontal" in blokk

    def test_a_platform_valasztas_KI_VAN_MONDVA(self):
        """Az eredeti külön `_win`/`_mac` rajzot szállít — mi a windowsosat
        vettük át, és ezt a forrás kimondja."""
        assert "_mac" in _SAV
        assert "base_win" in _SAV


class TestARegisztracio:
    def test_a_combobox_a_qmldir_ben_van(self):
        assert "PicasaComboBox 1.0 PicasaComboBox.qml" in (
            _QML / "qmldir"
        ).read_text(encoding="utf-8")
