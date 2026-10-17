"""#5180: a deferredface azonosító a kontaktlistával oldódik fel, és az
ismeretlen db3-régiók a Név nélküliek indexébe kerülnek.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.ini.faces import parse_faces
from picasapy.pmpimport.db3_atvetel import rekordokat_atvesz
from picasapy.pmpimport.importer import iter_photo_records
from picasapy.pmpimport.remap import PathRemapper
from support.pmp_factory import build_pmp_column, build_thumb_index


_PERSON_ID = "1234567890abcdef"
_UNKNOWN_ID = "ffffffffffffffff"
_NAMED_RECT = "1000200030004000"
_UNKNOWN_RECT = "5000600070008000"


def _db3(db3: Path, *, deferredface: str, deferredregion: str = "") -> None:
    db3.mkdir(parents=True)
    (db3 / "thumbindex.db").write_bytes(
        build_thumb_index(
            [("C:\\Pictures", None), ("a.jpg", 0)],
        )
    )
    (db3 / "imagedata_deferredface.pmp").write_bytes(
        build_pmp_column(0x0, ["", deferredface])
    )
    (db3 / "imagedata_deferredregion.pmp").write_bytes(
        build_pmp_column(0x0, ["", deferredregion])
    )
    contacts = db3 / "contacts" / "contacts.xml"
    contacts.parent.mkdir()
    contacts.write_text(
        '<contacts><contact id="1234567890abcdef" name="Új Név" '
        'modified_time="2026-10-17T12:00:00+02:00" local_contact="1"/>'
        "</contacts>",
        encoding="utf-8",
    )


def test_deferredface_nev_az_aktualis_contact_xmlbol_jon(tmp_path):
    db3 = tmp_path / "db3"
    _db3(
        db3,
        deferredface=f"rect64({_NAMED_RECT}),{_PERSON_ID};",
        deferredregion=f"rect64({_NAMED_RECT}),Régi Név;",
    )
    records = iter_photo_records(
        db3, PathRemapper.from_dict({"C:\\Pictures": str(tmp_path / "kepek")})
    )

    assert len(records) == 1
    assert records[0].faces[0].name == "Új Név"
    assert records[0].faces[0].contact_id == _PERSON_ID


def test_ignored_ini_regio_mellett_is_atjon_a_nevesitett_arc(tmp_path):
    library = tmp_path / "kepek"
    library.mkdir()
    photo = library / "a.jpg"
    photo.write_bytes(b"")
    old_region = "rect64(1111111111111111),ffffffffffffffff"
    ini_path = library / ".picasa.ini"
    ini_path.write_text(
        f"[a.jpg]\nfaces={old_region}\ncaption=marad\n", encoding="utf-8"
    )

    from picasapy.pmpimport.deferredregion import DeferredFace
    from picasapy.pmpimport.importer import PhotoRecord
    from picasapy.ini.rect64 import Rect64

    record = PhotoRecord(
        local_path=str(photo),
        windows_path="C:\\Pictures\\a.jpg",
        row=1,
        caption=None,
        rotate=None,
        star=False,
        filters=None,
        crop64=None,
        tags=(),
        latitude=None,
        longitude=None,
        faces=(
            DeferredFace(
                rect=Rect64(left=0.2, top=0.2, right=0.4, bottom=0.4),
                name="Új Név",
            ),
        ),
    )

    rekordokat_atvesz([record], backup=False)

    text = ini_path.read_text(encoding="utf-8")
    value = next(line.removeprefix("faces=") for line in text.splitlines() if line.startswith("faces="))
    assert value.startswith(old_region + ";")
    parsed = parse_faces(value)
    assert len(parsed) == 2
    assert parsed[0].contact_id == _UNKNOWN_ID
    assert "Új Név" in text
