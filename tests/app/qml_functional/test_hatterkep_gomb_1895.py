"""#1895: az „Asztali háttérkép" gomb nem ígérhet háttérkép-beállítást.

## A lelet

A gomb buboréksúgója szó szerint ezt ígérte:

> „Save the picture as a JPG in the Collages album, **then set it as your
> desktop background**"

A lánc viszont a `collageDesktopBackgroundReady` jelzésnél **véget ért**:
az egyetlen fogyasztója a `PicasaNotifier` értesítése („A kollázs kész"),
és a háttérkép beállítására a forrásban **sehol nincs kód** —
`set_wallpaper` / `SPI_SETDESKWALLPAPER` / `gsettings` / `swaybg` /
`feh`: nulla találat.

⇒ A felhasználó megnyomta a gombot, kapott egy „kész" értesítést, és az
asztala változatlan maradt.

## Amit ez a kör tesz — és amit NEM

A gomb **inaktív**, a súgója pedig már nem ígér háttérképet. A HELYE
megmarad: az eredetiben létezik, csak a tartalma nincs kész. A tényleges
megépítése a **#1775** tárgya (az eredeti BMP-t ír és középre teszi).

Egy kattintható vezérlő, ami mást ad, mint amit ígér, rosszabb, mint a
hiánya (#936, #1903).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_PANEL = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "CollagePanel.qml"
).read_text(encoding="utf-8")


def _blokk() -> str:
    kezdet = _PANEL.index('objectName: "collageMakeDesktopButton"')
    return _PANEL[kezdet : kezdet + 700]


class TestAGombNemIger:
    def test_a_gomb_INAKTIV(self):
        assert "enabled: false" in _blokk()

    def test_a_sugo_NEM_iger_hatterkepet(self):
        blokk = _blokk()
        assert "set it as your desktop background" not in blokk, (
            "a súgó továbbra is háttérkép-beállítást ígér, miközben a "
            "forrásban nincs rá kód (#1895)"
        )

    def test_a_HELYE_megmarad(self):
        """Az eredetiben létezik — csak a tartalma nincs kész."""
        blokk = _blokk()
        assert "x: 10; y: 415; width: 127; height: 28" in blokk
        assert 'text: qsTr("Desktop Background")' in blokk

    def test_a_forras_KIMONDJA_miert(self):
        """Hogy egy későbbi kör ne „elfelejtett engedélyezésként" oldja fel."""
        assert "#1895" in _PANEL and "#1775" in _PANEL


class TestNincsHatterkepKodSehol:
    """A jegy alapállítása — ha valaki megépíti, EZ a teszt bukik, és akkor
    a gombot is engedélyezni kell (a #1775 köre)."""

    def test_a_forrasban_nincs_hatterkep_beallitas(self):
        import subprocess
        import sys

        gyoker = Path(picasapy.app.__file__).parent.parent
        minta = "set_wallpaper|SPI_SETDESKWALLPAPER|swaybg|picture-uri"
        eredmeny = subprocess.run(
            [sys.executable, "-c",
             "import re,sys,pathlib\n"
             "gy=pathlib.Path(sys.argv[1]); m=re.compile(sys.argv[2])\n"
             "t=[str(p) for p in gy.rglob('*.py') if m.search(p.read_text(encoding='utf-8'))]\n"
             "print('\\n'.join(t))",
             str(gyoker), minta],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        talalatok = [s for s in eredmeny.stdout.split("\n") if s]
        assert not talalatok, (
            "van háttérkép-beállító kód — a gombot engedélyezni kell, és ez "
            f"a teszt elavult (#1775): {talalatok}"
        )
