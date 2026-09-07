"""#2624 — a hisztogram-doboz fejléce a HIVATALOS magyar alak.

Nálunk „Hisztogram és fényképadatok" állt; az eredeti Picasa 3 magyar
felirata **„Hisztogram és fényképezőgép-adatok"** — és ez nem szemből
olvasott szöveg, hanem a Picasa saját erőforrásából:

    referencia/panel-feliratok-hu.tsv:4921
    tooltips  Text  nerdview/nvhead  Hisztogram és fényképezőgép-adatok

A tulajdonos 2026-09-06 22:32-i A/B felvételén
(`research/felirat-ki-bekapcsolva/`) mindkét alak látszik egymás mellett,
ugyanazon a képen, ugyanabban a percben.

## Miért nem stílus-kérdés

A `fényképadat` és a `fényképezőgép-adat` NEM ugyanaz: az előbbi a képről
szól, az utóbbi a GÉPRŐL, ami készítette (a `nerdview` az EXIF-blokk —
expozíció, rekesz, ISO). A rövidítés jelentést veszít, és a hivatalos
magyar alak megvan, tehát nem is kell fordítani.

⚠️ A referencia-táblák a PRIVÁT `picasapy-agent` repóban élnek, tehát a
CI-n nincsenek ott. A hivatalos alakot ezért ide ÁTÍRVA őrizzük, a
forrás megnevezésével — egy CI-n mindig kihagyott teszt nem őr.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app

#: A hivatalos magyar felirat (`nerdview/nvhead`,
#: `panel-feliratok-hu.tsv:4921`).
HIVATALOS = "Hisztogram és fényképezőgép-adatok"
#: A forrásszöveg, amihez a fordítás tartozik.
FORRAS = "Histogram and camera information"

_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")
_QML = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "HistogramBox.qml"
).read_text(encoding="utf-8")


def _forditasok() -> list[str]:
    return re.findall(
        rf"<source>{re.escape(FORRAS)}</source>\s*<translation[^>]*>(.*?)</translation>",
        _TS,
        re.DOTALL,
    )


class TestAHivatalosAlak:
    def test_a_qml_a_MERT_forrasszoveget_hasznalja(self):
        """Ha a forrásszöveg elmozdul, a fordítás sem talál rá."""
        assert f'qsTr("{FORRAS}")' in _QML

    def test_van_forditas(self):
        assert _forditasok(), (
            f"nincs magyar fordítás a(z) {FORRAS!r} szöveghez"
        )

    def test_MINDEN_elofordulas_a_hivatalos_alak(self):
        """A `.ts` KÉT kontextusban is tartalmazza — mindkettőnek egyeznie
        kell, különben a felület attól függ, melyik kontextus szólal meg."""
        forditasok = _forditasok()
        assert len(forditasok) == 2, (
            f"{len(forditasok)} fordítást találtam, mérve 2 volt"
        )
        for forditas in forditasok:
            assert forditas.strip() == HIVATALOS, (
                f"a fordítás {forditas.strip()!r}, a Picasa saját magyar "
                f"alakja {HIVATALOS!r} (panel-feliratok-hu.tsv:4921, "
                "`nerdview/nvhead`)"
            )

    def test_a_ROVIDITETT_alak_sehol_nincs(self):
        """A foga: a „fényképadatok" alak jelentést veszít (a kép adatai
        vs. a FÉNYKÉPEZŐGÉPÉ)."""
        assert "Hisztogram és fényképadatok" not in _TS

    def test_a_lefordult_qm_is_a_hivatalos_alakot_viszi(self):
        """A `.ts` javítása önmagában nem elég: a program a `.qm`-et
        olvassa. Ez a próba a #2448 tanulságát rögzíti — a fordítás
        HÁROM lépés, és a harmadik a `pyside6-lrelease`."""
        qm = (
            Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.qm"
        ).read_bytes()
        assert HIVATALOS.encode("utf-16-be") in qm, (
            "a lefordított `.qm` nem tartalmazza a hivatalos alakot — "
            "lefutott a `pyside6-lrelease`?"
        )
        assert "Hisztogram és fényképadatok".encode("utf-16-be") not in qm
