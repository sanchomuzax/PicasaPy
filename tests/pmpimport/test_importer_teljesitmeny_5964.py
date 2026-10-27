"""A nagy wordhash-import ne szerkessze újra a teljes ini-t minden képnél."""

from picasapy.ini.document import IniDocument, parse_document
from picasapy.pmpimport.db3_atvetel import rekordokat_atvesz
from picasapy.pmpimport.importer import PhotoRecord


def test_mappasorrend_atvetele_nem_egyenkent_irja_ujra_a_szekciokat(
    tmp_path, monkeypatch
):
    photos = tmp_path / "photos"
    photos.mkdir()
    records = tuple(
        PhotoRecord(
            local_path=str(photos / f"photo-{index:03}.jpg"),
            windows_path=rf"C:\Photos\photo-{index:03}.jpg",
            row=index,
            caption=None,
            rotate=None,
            star=False,
            filters=None,
            crop64=None,
            tags=(),
            latitude=None,
            longitude=None,
            faces=(),
            manual_priority=float(index),
        )
        for index in range(256)
    )

    eredeti = IniDocument.with_value
    with_value_calls = 0

    def counted_with_value(self, section_name, key, value, *, carried=False):
        nonlocal with_value_calls
        with_value_calls += 1
        return eredeti(self, section_name, key, value, carried=carried)

    monkeypatch.setattr(IniDocument, "with_value", counted_with_value)

    report = rekordokat_atvesz(records, backup=False)
    document = parse_document((photos / ".picasa.ini").read_text(encoding="utf-8"))

    assert report.sorrend == len(records)
    assert sum(section.get("priority") is not None for section in document.file_sections()) == len(records)
    assert with_value_calls < len(records) // 10
