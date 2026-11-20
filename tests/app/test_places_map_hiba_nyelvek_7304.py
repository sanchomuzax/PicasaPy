"""#7304: a Helyek panel térképhibája szolgáltatónév nélkül, minden nyelven.

A térkép QtLocation/OSM, az eredeti Google Maps-es hibaszöveg ezért félrevezető.
Az őr a `.ts` fájlokat nézi: mind a 41 nyelvben meg kell lennie a szolgáltató
nélküli üzenet BEFEJEZETT fordításának, a régi szövegnek pedig nem szabad
megmaradnia. Azt nem méri, hogy a fordítás nyelvtanilag jó-e (azt olvasni kell).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from picasapy.app.language_controller import SUPPORTED_LANGUAGES

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"
_UJ = (
    "The map could not be loaded. "
    "Please make sure that you are connected to the Internet."
)
_ANGOL_NYELVEK = ("en", "enUK")


def _uzenetek(code: str, kontextus: str) -> list[ET.Element]:
    root = ET.parse(_I18N / f"picasapy_{code}.ts").getroot()
    return [
        message
        for context in root.iter("context")
        if context.findtext("name") == kontextus
        for message in context.findall("message")
    ]


@pytest.mark.parametrize("code", SUPPORTED_LANGUAGES)
def test_a_terkephiba_minden_nyelven_szolgaltatonev_nelkul_leforditva(code):
    uzenetek = _uzenetek(code, "PlacesPanel")
    google = [
        m.findtext("source") for m in uzenetek if "Google" in (m.findtext("source") or "")
    ]
    assert not google, f"{code}: a régi Google-szöveg megmaradt: {google}"

    uj = [m for m in uzenetek if m.findtext("source") == _UJ]
    assert len(uj) == 1, f"{code}: az új üzenet hiányzik vagy kétszer szerepel"
    message = uj[0]
    assert "picasapy-origin: picasapy" in (message.findtext("extracomment") or "")
    assert "picasapy-origin-key" not in (message.findtext("extracomment") or "")

    translation = message.find("translation")
    assert translation is not None and translation.get("type") is None, (
        f"{code}: a fordítás nincs befejezve"
    )
    text = (translation.text or "").strip()
    assert text, f"{code}: üres fordítás"
    assert "Google" not in text, f"{code}: a fordítás szolgáltatót nevez meg"
    if code in _ANGOL_NYELVEK:
        assert text == _UJ
    else:
        assert text != _UJ, f"{code}: a fordítás az angol forrás másolata"


def test_a_magyar_terkephiba_a_megadott_szoveg():
    (message,) = [
        m for m in _uzenetek("hu", "PlacesPanel") if m.findtext("source") == _UJ
    ]
    assert message.findtext("translation") == (
        "A térkép nem tölthető be. Ellenőrizze az internetkapcsolatot."
    )
