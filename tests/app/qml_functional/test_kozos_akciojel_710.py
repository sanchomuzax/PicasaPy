"""A panelgombok közös jele megmarad, a kép fölötti sávé eltűnik (#4037).

## Amit az audit mond

A vágás-panel és a csúszkás paraméter-alpanel **ugyanazt** az Alkalmaz/Mégse
gombot használja: zöld pipa / sötétvörös X a felirat jobb oldalán, a gomb jobb
szélétől **9 képpontra** (`docs/specs/ui-audit-editor.md` 7.4).

Nálunk két külön megoldás élt:

| panel | a jel |
|---|---|
| paraméter-alpanel (#700) | rajzolt kör, panelen belüli `component` |
| vágás-panel | a felirat végére fűzött `„✔"` / `„✘"` karakter |

## ⛔ Miért nem egyenértékű a Unicode-os alak

A glif **betűtípusfüggő**, és ha hiányzik, **nyomtalanul eltűnik** — a
gombon csak a felirat marad, hibaüzenet nélkül. Ezt a #700 kommentje már
kimondta a saját paneljére; a vágás-panel viszont épp azon az úton maradt.
A rajzolt jel minden betűtípussal ugyanazt adja.

## Amit ez a lap kiköt

Egyetlen komponens (`EditorActionBadge`) a paraméter-panelen. A kiegyenesítés
sávján nincs jel; a felirat nyelvi erőforrásból jön: `APPLY` / `CANCEL`,
magyarul `ALKALMAZ` / `MÉGSE`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import picasapy.app
from PySide6.QtCore import QTranslator

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_I18N = Path(picasapy.app.__file__).parent / "i18n"

#: A két felület, ahol a jel maradását/eltűnését együtt őrizzük.
#:
#: #4037: a `tool_ok`/`tool_cancel` gombokon nincs jel; a paraméter-panel
#: gombjain viszont marad az `EditorActionBadge`.
PANELEK = ("EditorToolBar.qml", "EditorParamPanel.qml")


def _kod_sorok(ut: Path) -> str:
    """A fájl KOMMENT NÉLKÜLI sorai — a kapu csak ezeket nézi."""
    return "\n".join(
        sor
        for sor in ut.read_text(encoding="utf-8").splitlines()
        if not sor.lstrip().startswith("//")
    )


class TestAKozosKomponens:
    def test_a_komponens_letezik_es_regisztralva_van(self) -> None:
        assert (_QML / "EditorActionBadge.qml").is_file()
        qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
        assert "EditorActionBadge 1.0 EditorActionBadge.qml" in qmldir, (
            "a komponens nincs a qmldir-ben — a QML-import nem találná meg"
        )

    def test_a_jel_a_parampanelen_marad_de_a_savrol_lekerul(self) -> None:
        sav, panel = PANELEK
        sav_forras = _kod_sorok(_QML / sav)
        panel_forras = _kod_sorok(_QML / panel)
        assert "EditorActionBadge {" not in sav_forras, (
            "EditorToolBar: a kiegyenesítés sávján az eredetiben nincs jel"
        )
        assert "EditorActionBadge {" in panel_forras, (
            "EditorParamPanel: a panelgombok közös jele eltűnt"
        )

    def test_a_panelen_beluli_masolat_MEGSZUNT(self) -> None:
        """A #700 `component ActionBadge`-e kikerült a panelből — különben
        két rajz élne tovább, és a következő stílus-javítás megint csak az
        egyiken menne át."""
        forras = (_QML / "EditorParamPanel.qml").read_text(encoding="utf-8")
        assert "component ActionBadge" not in forras


class TestAUnicodeJelNemJonVISSZA:
    """⛔ A hiányzó glif némán tünteti el a jelet — ezért kikötés."""

    def test_nincs_pipa_vagy_X_karakter_a_ket_panelben(self) -> None:
        """⚠️ A kapu a KÓDOT nézi, a kommentet nem.

        Az első változatom a teljes fájlra keresett, és a SAJÁT
        magyarázó kommentemen bukott el — abban idézőjelben szerepel a
        két karakter, épp azért, hogy a következő olvasó tudja, miért
        tűntek el. Egy kapu, ami az őszinte magyarázatot bünteti, arra
        tanít, hogy ne írjunk magyarázatot."""
        for nev in PANELEK:
            forras = _kod_sorok(_QML / nev)
            for jel in ("✔", "✘", "✓", "✗"):
                assert jel not in forras, (
                    f"{nev}: visszakerült a(z) {jel!r} karakter — a glif "
                    "betűtípusfüggő, hiányzó glifnél a jel nyomtalanul "
                    "eltűnik. A rajzolt `EditorActionBadge` a helyes út."
                )

    def test_a_feliratok_tisztak_maradtak(self) -> None:
        """A sáv nagybetűs forrásszövege a nyelvi fájl kulcsa."""
        forras = (_QML / "EditorToolBar.qml").read_text(encoding="utf-8")
        assert 'qsTr("APPLY")' in forras
        assert 'qsTr("CANCEL")' in forras


class TestASavForditasa:
    def test_a_ts_a_kulon_savfeliratokat_tartalmazza(self) -> None:
        ts = ET.parse(_I18N / "picasapy_hu.ts")
        editor_toolbar = next(
            context
            for context in ts.findall("context")
            if context.findtext("name") == "EditorToolBar"
        )
        forditasok = {
            uzenet.findtext("source"): uzenet.findtext("translation")
            for uzenet in editor_toolbar.findall("message")
        }
        assert forditasok.get("APPLY") == "ALKALMAZ"
        assert forditasok.get("CANCEL") == "MÉGSE"

    def test_a_forditott_qm_fajl_is_a_nagybetus_feliratot_adja(self) -> None:
        ford = QTranslator()
        assert ford.load(str(_I18N / "picasapy_hu.qm")), "a magyar .qm nem tölthető be"
        assert ford.translate("EditorToolBar", "APPLY") == "ALKALMAZ"
        assert ford.translate("EditorToolBar", "CANCEL") == "MÉGSE"


class TestAJelHELYE:
    """A paraméter-panel jele a gomb jobb szélétől 9 képpontra ül."""

    def test_a_parampanel_9_kepponttal_horgonyoz(self) -> None:
        nev = "EditorParamPanel.qml"
        forras = (_QML / nev).read_text(encoding="utf-8")
        blokkok = forras.split("EditorActionBadge {")[1:]
        assert blokkok, f"{nev}: nincs jel-blokk"
        for blokk in blokkok:
            fej = blokk[:400]
            assert "anchors.rightMargin: 9" in fej, (
                f"{nev}: a jel nem a jobb széltől 9 képpontra ül"
            )
