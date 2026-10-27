"""Az ini-mentés újrapróbálása átmeneti Windows-fájlzár esetén (#6043)."""

from __future__ import annotations

from picasapy import ioutil
from picasapy.ini import load_document, update_document


def test_update_document_ujraprobalja_az_atmenetileg_zarolt_celcserejet(
    tmp_path, monkeypatch
):
    ini = tmp_path / ".picasa.ini"
    ini.write_text("[a.jpg]\ncaption=eredeti\n", encoding="utf-8")
    eredeti_csere = ioutil._replace
    probalkozasok = []

    def egyszer_zarolt(src, dst):
        if dst == ini and not probalkozasok:
            probalkozasok.append("zárolt")
            raise PermissionError(13, "Permission denied", str(dst))
        probalkozasok.append("sikeres")
        return eredeti_csere(src, dst)

    monkeypatch.setattr(ioutil, "_replace", egyszer_zarolt)

    update_document(
        ini,
        lambda document: document.with_value("a.jpg", "caption", "friss"),
        backup=False,
    )

    assert probalkozasok == ["zárolt", "sikeres"]
    assert load_document(ini).section("a.jpg").get("caption") == "friss"
