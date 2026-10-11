"""#4579: személynevek a fájl XMP-régióiból (spec 17. F)."""

from picasapy.metadata.xmp_people import xmp_person_names

_NS = (
    'xmlns:x="adobe:ns:meta/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
    'xmlns:mwg-rs="http://www.metadataworkinggroup.com/schemas/regions/" '
    'xmlns:stArea="http://ns.adobe.com/xap/1.0/sType/Area#" '
    'xmlns:MP="http://ns.microsoft.com/photo/1.2/" '
    'xmlns:MPRI="http://ns.microsoft.com/photo/1.2/t/RegionInfo#" '
    'xmlns:MPReg="http://ns.microsoft.com/photo/1.2/t/Region#"'
)


def _mwg(*regions):
    lis = "".join(
        f'<rdf:li rdf:parseType="Resource">{r}</rdf:li>' for r in regions
    )
    return (
        f'<x:xmpmeta {_NS}><rdf:RDF><rdf:Description>'
        '<mwg-rs:Regions rdf:parseType="Resource"><mwg-rs:RegionList>'
        f"<rdf:Bag>{lis}</rdf:Bag></mwg-rs:RegionList></mwg-rs:Regions>"
    )


def _mwg_zar():
    return "</rdf:Description></rdf:RDF></x:xmpmeta>"


def _mp(*regions):
    lis = "".join(
        f'<rdf:li rdf:parseType="Resource">{r}</rdf:li>' for r in regions
    )
    return (
        f'<x:xmpmeta {_NS}><rdf:RDF><rdf:Description>'
        '<MP:RegionInfo rdf:parseType="Resource"><MPRI:Regions>'
        f"<rdf:Bag>{lis}</rdf:Bag></MPRI:Regions></MP:RegionInfo>"
    )


AREA = '<mwg-rs:Area stArea:x="0.5" stArea:y="0.5" stArea:w="0.2" stArea:h="0.2" stArea:unit="normalized"/>'


def _reg(name, tipus="Face", area=AREA):
    t = f"<mwg-rs:Type>{tipus}</mwg-rs:Type>" if tipus else ""
    return f"<mwg-rs:Name>{name}</mwg-rs:Name>{t}{area}"


def test_mwg_nevek_sorrendben():
    xmp = _mwg(_reg("Kata"), _reg("Bela")) + _mwg_zar()
    assert xmp_person_names(xmp) == ("Kata", "Bela")


def test_tipus_hianyzik_vagy_face_kisnagybetu_nelkul():
    xmp = _mwg(_reg("A", tipus=None), _reg("B", tipus="face"), _reg("C", tipus="Pet")) + _mwg_zar()
    assert xmp_person_names(xmp) == ("A", "B")


def test_ures_nev_es_elfajult_teglalap_kimarad():
    elfajult = '<mwg-rs:Area stArea:x="0.5" stArea:y="0.5" stArea:w="0" stArea:h="0.2"/>'
    xmp = _mwg(_reg(""), _reg("X", area=elfajult), _reg("Y")) + _mwg_zar()
    assert xmp_person_names(xmp) == ("Y",)


def test_mp_nevek_ha_nincs_mwg():
    mp_reg = (
        "<MPReg:PersonDisplayName>Zsuzsa</MPReg:PersonDisplayName>"
        "<MPReg:Rectangle>0.1, 0.1, 0.2, 0.2</MPReg:Rectangle>"
    )
    xmp = _mp(mp_reg) + _mwg_zar()
    assert xmp_person_names(xmp) == ("Zsuzsa",)


def test_mwg_kiszoritja_az_mp_t():
    mp_reg = (
        "<MPReg:PersonDisplayName>Zsuzsa</MPReg:PersonDisplayName>"
        "<MPReg:Rectangle>0.1, 0.1, 0.2, 0.2</MPReg:Rectangle>"
    )
    xmp = (
        _mp(mp_reg).replace("</rdf:Description>", "")
        + _mwg(_reg("Kata")).split("<rdf:Description>", 1)[1]
        + _mwg_zar()
    )
    assert xmp_person_names(xmp) == ("Kata",)


def test_hibas_vagy_hianyzo_xmp_ures():
    assert xmp_person_names(None) == ()
    assert xmp_person_names(b"nem xml") == ()
    assert xmp_person_names(b"") == ()
