"""#1798 — a tálca „E-Mail" gombja ne legyen néma.

**Amit mértünk.** A `TrayBar.emailRequested()` jelzésnek **egyetlen
kezelője sem volt** a QML-oldalon, pedig a gomb engedélyezve van és
kattintható. A testvérei (Kollázs, Exportálás, Nyomtatás) mind be voltak
kötve — ez a jelzés maradt ki. Emiatt a `sendRows()`-nak sem volt hívója,
és emiatt látszott némának a Beállítások e-mail-módja is: nem a beállítás
volt néma, hanem az egész küldési út.

Ugyanígy: az `emailFailed` jelzésnek sem volt kezelője, tehát a
„nincs levelezőprogram" hibaüzenet a naplóban maradt volna.

Ez a teszt a BEKÖTÉST méri, nem a levélküldést — az utóbbi nem
tesztelhető determinisztikusan (ld. az `email_controller` docstringjét).
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _forras() -> str:
    from pathlib import Path

    return (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/qml/Main.qml"
    ).read_text(encoding="utf-8")


class TestABekotesLetezik:
    def test_a_talca_email_jelzesenek_van_kezeloje(self):
        assert "onEmailRequested:" in _forras(), (
            "a tálca „E-Mail\" gombja kattintható, de a jelzését senki nem "
            "fogja el — néma vezérlő (#1798)"
        )

    def test_az_emailFailed_nek_van_kezeloje(self):
        assert "function onEmailFailed(" in _forras(), (
            "a levelezős hibaüzenet sehol nem jelenik meg a felhasználónak"
        )

    def test_a_valasztas_kerdesenek_van_kezeloje(self):
        assert "function onMailChoiceRequested(" in _forras(), (
            "a „minden küldéskor kérdezz\" mód kérdését senki nem fogja el "
            "— a beállítás továbbra is néma lenne"
        )


class TestAzEloFaban:
    def test_a_talca_email_gombja_letezik_es_kotott(self, qml_app, qt_app):
        """Az élő fában is meglegyen a gomb, amiről a jegy szól."""
        window, _controller, _engine = qml_app
        gomb = window.findChild(QObject, "trayEmailButton")
        assert gomb is not None, "a tálca E-Mail gombja eltűnt"

    def test_a_valaszto_parbeszed_nem_epul_fel_indulaskor(
        self, qml_app, qt_app
    ):
        """#1720: halasztott — indításkor nincs példánya."""
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "emailChoiceDialog") is None, (
            "a választó-párbeszéd induláskor felépült — a #1720 halasztási "
            "mintája sérült"
        )
