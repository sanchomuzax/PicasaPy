"""A frissítési ablak kiadási leírása olvasható szöveg (#6358)."""

from __future__ import annotations

from picasapy.app.update_manager import olvashato_jegyzet

_BODY = """## Mi került a kiadásba

<!-- kep-nelkul: belső megjegyzés -->
![A frissítési ablak](https://example.test/kep.png)

* **Gyorsabb indulás** elérhetetlen NAS mellett (#6355).
- A [súgó](https://example.test/sugo) frissült.


Részletek: `CHANGELOG.md`
"""


def test_a_markdown_jelek_es_a_kepek_kimaradnak():
    assert olvashato_jegyzet(_BODY) == (
        "Mi került a kiadásba\n"
        "\n"
        "• Gyorsabb indulás elérhetetlen NAS mellett (#6355).\n"
        "• A súgó frissült.\n"
        "\n"
        "Részletek: CHANGELOG.md"
    )


def test_ures_leiras_ures_szoveg():
    assert olvashato_jegyzet("") == ""
    assert olvashato_jegyzet(None) == ""
