"""#1798 — a „minden küldéskor kérdezz" beállítás ne legyen néma.

## A lelet (párhuzamos UI-kutatás, 2026-09-01)

A Beállítások „E-mail" fülén két rádiógomb van. A választás **tárolódik**
és a felület vissza is jelzi — a küldés viszont **soha nem olvassa el**:
a `sendRows()` feltétel nélkül az `xdg-email` / `mailto:` útra ment.

⇒ a második rádiógomb kiválasztható, megmarad, és nem csinál semmit.
Ugyanaz a hibaosztály, mint a #936 (néma jelzés) és a #1638 (néma
menütétel).

## Amit ezen felül MÉRTÜNK (#1798 felvételekor)

A `sendRows()`-nak **egyetlen hívója sem volt** — sem QML-ben, sem
Pythonban. A tálca „E-Mail" gombja engedélyezve van, kattintható, és a
`TrayBar.emailRequested()` jelzését **senki nem fogta el** (a testvérei —
Kollázs, Exportálás, Nyomtatás — mind be vannak kötve). Vagyis a
beállítás azért volt néma, mert az egész küldési út néma volt.

Ez a fájl a beállítás **szerződését** méri: ha a felhasználó azt kérte,
hogy kérdezzenek, akkor a küldés NEM indulhat el magától.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app.email_controller import EmailController


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _Jelzesfogo:
    """A `mailChoiceRequested` elkapott hívásai."""

    hivasok: list

    def __call__(self, *args):
        self.hivasok.append(args)


def _vezerlo(tmp_path, *, kerdezzen: bool):
    vezerlo = EmailController(
        photo_source=lambda: [],
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )
    vezerlo.setUseDefaultClient(not kerdezzen)
    return vezerlo


class TestAKerdezzModNemKuldMagatol:
    def test_a_sendRows_NEM_inditja_el_a_levelezot(self, qt_app, tmp_path):
        """Ez a hiba maga: a beállítás ellenére elment a levél."""
        vezerlo = _vezerlo(tmp_path, kerdezzen=True)
        with patch(
            "picasapy.app.email_controller._which",
            return_value="/usr/bin/xdg-email",
        ), patch("picasapy.app.email_controller._popen") as popen:
            eredmeny = vezerlo.sendRows(["/tmp/a.jpg"], "Tárgy", "Szöveg")

        popen.assert_not_called()
        assert eredmeny is False, (
            "a küldés sikert jelentett, pedig meg sem történt"
        )

    def test_valasztast_KER_a_felulettol(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, kerdezzen=True)
        fogo = _Jelzesfogo([])
        vezerlo.mailChoiceRequested.connect(fogo)

        with patch(
            "picasapy.app.email_controller._which",
            return_value="/usr/bin/xdg-email",
        ), patch("picasapy.app.email_controller._popen"):
            vezerlo.sendRows(["/tmp/a.jpg"], "Tárgy", "Szöveg")

        assert len(fogo.hivasok) == 1, (
            "a néma ág visszatért: nincs kérdés, és nincs küldés sem — "
            "a felhasználó azt hinné, elment a levél (#1798)"
        )
        utvonalak, targy, szoveg = fogo.hivasok[0]
        assert list(utvonalak) == ["/tmp/a.jpg"]
        assert targy == "Tárgy"
        assert szoveg == "Szöveg"


class TestAzAlapertelmezettModValtozatlan:
    def test_kuld_kerdes_nelkul(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, kerdezzen=False)
        fogo = _Jelzesfogo([])
        vezerlo.mailChoiceRequested.connect(fogo)

        with patch(
            "picasapy.app.email_controller._which",
            return_value="/usr/bin/xdg-email",
        ), patch("picasapy.app.email_controller._popen") as popen:
            eredmeny = vezerlo.sendRows(["/tmp/a.jpg"], "Tárgy", "Szöveg")

        assert eredmeny is True
        popen.assert_called_once()
        assert fogo.hivasok == [], "fölöslegesen kérdezett"


class TestAValasztasErvenyesitese:
    def test_a_valasz_utan_ELMEGY_a_level(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, kerdezzen=True)
        with patch(
            "picasapy.app.email_controller._which",
            return_value="/usr/bin/xdg-email",
        ), patch("picasapy.app.email_controller._popen") as popen:
            eredmeny = vezerlo.sendWithDefaultClient(
                ["/tmp/a.jpg"], "Tárgy", "Szöveg", False
            )

        assert eredmeny is True
        popen.assert_called_once()

    def test_a_ne_kerdezd_tobbet_atallitja_a_beallitast(
        self, qt_app, tmp_path
    ):
        """A mért `DoNotPromptForEmailPref` megfelelője."""
        vezerlo = _vezerlo(tmp_path, kerdezzen=True)
        assert vezerlo.useDefaultClient is False

        with patch(
            "picasapy.app.email_controller._which",
            return_value="/usr/bin/xdg-email",
        ), patch("picasapy.app.email_controller._popen"):
            vezerlo.sendWithDefaultClient(
                ["/tmp/a.jpg"], "Tárgy", "Szöveg", True
            )

        assert vezerlo.useDefaultClient is True, (
            "a „ne kérdezd többet\" jelölés nem állította vissza a "
            "Beállítások rádióját"
        )

    def test_a_jeloles_nelkul_marad_a_kerdezz_mod(self, qt_app, tmp_path):
        vezerlo = _vezerlo(tmp_path, kerdezzen=True)
        with patch(
            "picasapy.app.email_controller._which",
            return_value="/usr/bin/xdg-email",
        ), patch("picasapy.app.email_controller._popen"):
            vezerlo.sendWithDefaultClient(
                ["/tmp/a.jpg"], "Tárgy", "Szöveg", False
            )
        assert vezerlo.useDefaultClient is False
