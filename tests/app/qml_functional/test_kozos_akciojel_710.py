"""Egy Alkalmaz/Mégse JEL szolgálja ki mindkét panelt — a #710 őre.

## Amit az audit mond

A vágás-panel és a csúszkás paraméter-alpanel **ugyanazt** az Alkalmaz/Mégse
gombot használja: zöld pipa / indigó X a felirat jobb oldalán, a gomb jobb
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

Egyetlen komponens (`EditorActionBadge`), mindkét panelen, és a régi
Unicode-os alak ne szivárogjon vissza.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"

#: A két hely, aminek az auditja szerint UGYANAZ a gombja.
#:
#: ⚠️ #3123: a vágás Alkalmaz/Mégse párja KIKERÜLT a panelből — az
#: eredetiben a KÉP FÖLÖTT lebeg (`editpanel/tool_container: editpanel/preview`).
#: A jel vele együtt költözött, tehát a kapu az `EditorToolBar.qml`-t nézi a
#: `EditorCropPanel.qml` helyett. A kikötés változatlan: EGY komponens, és a
#: Unicode-os alak ne szivárogjon vissza.
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

    def test_MINDKET_panel_ezt_hasznalja(self) -> None:
        for nev in PANELEK:
            forras = (_QML / nev).read_text(encoding="utf-8")
            assert "EditorActionBadge {" in forras, (
                f"{nev}: nem a közös jelet használja"
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
        """A gomb felirata a puszta szó — a jelet a komponens adja."""
        forras = (_QML / "EditorToolBar.qml").read_text(encoding="utf-8")
        assert 'qsTr("Apply")' in forras
        assert 'qsTr("Cancel")' in forras


class TestAJelHELYE:
    """Az audit mérése: a jel a gomb jobb szélétől 9 képponton ül."""

    def test_mindket_panel_9_kepponttal_horgonyoz(self) -> None:
        for nev in PANELEK:
            forras = (_QML / nev).read_text(encoding="utf-8")
            blokkok = forras.split("EditorActionBadge {")[1:]
            assert blokkok, f"{nev}: nincs jel-blokk"
            for blokk in blokkok:
                fej = blokk[:400]
                assert "anchors.rightMargin: 9" in fej, (
                    f"{nev}: a jel nem a jobb széltől 9 képpontra ül"
                )
