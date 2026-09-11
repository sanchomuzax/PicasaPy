"""#534: MIND a hét gyári sablon végigfut, és a kimenete ÉRVÉNYES jelölés.

Az eredeti Picasa hat HTML-sablont (`whitebg`, `whitefrm`, `greybg`,
`greyfrm`, `blackbg`, `blackfrm`) és egy `xml` sablont szállított; a mi
készletünk ugyanezt a hetet adja, saját HTML/CSS-sel.

⚠️ Amit ez az őr NEM mér: a LÁTVÁNYT. Hogy a „Fekete keret" tényleg úgy
néz-e ki, mint az eredeti, csak referencia-képernyőképpel dönthető el, és
olyan a sablonokhoz nincs. Az őr a SZERKEZETET mondja ki: minden sablon
lefut, minden kiadott oldal címkéi párba állnak, és a feliratból származó
attribútum-érték ÉPSÉGBEN kerül a kimenetbe (egy nyersen kiírt idézőjel itt
bukik meg — #2932). Az XML-sablonnál a mérce az érvényes XML.
"""

from __future__ import annotations

from pathlib import Path
from html.parser import HTMLParser
from xml.etree import ElementTree

import pytest

import picasapy.webexport as webexport_pkg
from picasapy.webexport import list_bundled_templates
from picasapy.webexport.context import AlbumExportData, WebExportSettings
from picasapy.webexport.engine import run_web_export

_TEMPLATES = Path(webexport_pkg.__file__).resolve().parent / "templates"

#: A hét gyári sablon és az eredeti Picasa-megfelelője.
VART_KESZLET = {
    "feher": "whitebg",
    "feher-keret": "whitefrm",
    "szurke": "greybg",
    "szurke-keret": "greyfrm",
    "fekete": "blackbg",
    "fekete-keret": "blackfrm",
    "xml": "xml",
}


@pytest.fixture
def album(tmp_path):
    """Kétképes album valódi JPEG-ekkel — az egyik felirata KÜLÖNÖS
    karaktereket tartalmaz (#2932), mert épp azok törik el a kimenetet."""
    from picasapy.index import PhotoRecord
    from picasapy.webexport.images import prepare_photo_exports
    from support.jpeg_factory import make_jpeg

    library = tmp_path / "kepek"
    library.mkdir()
    for nev in ("a.jpg", "b.jpg"):
        make_jpeg(library / nev, size=(400, 300))

    def rekord(azonosito: int, nev: str, felirat: str | None) -> PhotoRecord:
        return PhotoRecord(
            id=azonosito, folder_path=str(library), name=nev, kind="photo",
            size=(library / nev).stat().st_size, mtime_ns=0, star=False,
            caption=felirat, keywords=None, rotate_steps=0, filters=None,
            taken_at=None, orientation=1, width=400, height=300,
        )

    cel = tmp_path / "kimenet"
    settings = WebExportSettings(thumbnail_max_dimension=120, image_max_dimension=800)
    kepek = prepare_photo_exports(
        (rekord(1, "a.jpg", 'Anyu & Apu <a "nyaralás">'), rekord(2, "b.jpg", None)),
        cel, settings,
    )
    return AlbumExportData(
        name="Nyaralás & tábor", caption="2026 nyara", date="2026. augusztus",
        photos=kepek.photos,
    ), cel, settings


def test_pontosan_a_het_sablon_van_csomagolva():
    assert {t.id for t in list_bundled_templates()} == set(VART_KESZLET)


def test_mindegyiknek_van_elonezeti_rajza():
    """A választó előnézetet mutat — sablon rajz nélkül ott lyuk lenne."""
    for info in list_bundled_templates():
        assert info.preview_path is not None, info.id
        assert info.preview_path.is_file()
        # a rajz a sablon SAJÁT palettáját mutassa, ne egy általános ikont
        assert "<svg" in info.preview_path.read_text(encoding="utf-8")


def test_mindegyiknek_van_neve_es_leirasa():
    """A választó-lista ezt mutatja — üres név vagy leírás ott lyuk."""
    for info in list_bundled_templates():
        assert info.name and info.description, info.id


class _Olvaso(HTMLParser):
    """Címke-párosítást és attribútumokat gyűjtő, elnéző HTML-olvasó.

    SZÁNDÉKOSAN nem XML-parszer: a HTML5-oldal `<!doctype html>`-lel kezdődik
    és üres elemeket (`<img>`, `<link>`, `<meta>`) tartalmaz, amiket egy
    XML-parszer joggal utasít el. Ami itt mérhető: a nyitó/záró címkék
    egyensúlya és az attribútum-értékek épsége."""

    URES = {"img", "link", "meta", "br", "hr", "input"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.verem: list[str] = []
        self.parosites_hibak: list[str] = []
        self.attributumok: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag, attrs):
        self.attributumok.append((tag, {k: v or "" for k, v in attrs}))
        if tag not in self.URES:
            self.verem.append(tag)

    def handle_endtag(self, tag):
        if tag in self.URES:
            return
        if not self.verem or self.verem[-1] != tag:
            self.parosites_hibak.append(
                f"</{tag}> a(z) {self.verem[-1:] or ['semmi']} után"
            )
            return
        self.verem.pop()

    def ertek(self, tag: str, attributum: str) -> list[str]:
        return [a[attributum] for t, a in self.attributumok if t == tag and attributum in a]


@pytest.mark.parametrize("sablon_id", sorted(set(VART_KESZLET) - {"xml"}))
def test_a_HTML_sablon_oldalai_szerkezetileg_epek(sablon_id, album):
    adat, cel, settings = album
    report = run_web_export(_TEMPLATES / sablon_id, cel, adat, settings)
    assert report.output_files, sablon_id
    for fajl in report.output_files:
        olvaso = _Olvaso()
        olvaso.feed(fajl.read_text(encoding="utf-8"))
        assert not olvaso.parosites_hibak, (sablon_id, fajl.name, olvaso.parosites_hibak)
        assert not olvaso.verem, (sablon_id, fajl.name, olvaso.verem)


@pytest.mark.parametrize("sablon_id", sorted(set(VART_KESZLET) - {"xml"}))
def test_a_felirat_EPSEGBEN_kerul_az_attributumba(sablon_id, album):
    """A felirat idézőjelet és `&`-t tartalmaz: nyersen kiírva az `alt`
    értéke csonkulna, és a maradék szöveg jelöléssé válna (#2932)."""
    adat, cel, settings = album
    run_web_export(_TEMPLATES / sablon_id, cel, adat, settings)
    olvaso = _Olvaso()
    olvaso.feed((cel / "index.html").read_text(encoding="utf-8"))
    assert 'Anyu & Apu <a "nyaralás">' in olvaso.ertek("img", "alt")


@pytest.mark.parametrize("sablon_id", sorted(set(VART_KESZLET) - {"xml"}))
def test_a_navigacio_letezo_fajlra_mutat(sablon_id, album):
    """Az egyenkénti nézet hivatkozásai a valóban kiadott oldalakra
    mutassanak — a törött hivatkozás néma hiba volna."""
    adat, cel, settings = album
    report = run_web_export(_TEMPLATES / sablon_id, cel, adat, settings)
    kiadott = {f.name for f in report.output_files}
    olvaso = _Olvaso()
    olvaso.feed((cel / "index.html").read_text(encoding="utf-8"))
    oldal_hivatkozasok = [h for h in olvaso.ertek("a", "href") if h.endswith(".html")]
    assert oldal_hivatkozasok
    assert set(oldal_hivatkozasok) <= kiadott


@pytest.mark.parametrize("sablon_id", sorted(set(VART_KESZLET) - {"xml"}))
def test_a_HTML_sablonok_sajat_stiluslapot_masolnak(sablon_id, album):
    adat, cel, settings = album
    run_web_export(_TEMPLATES / sablon_id, cel, adat, settings)
    stilus = (cel / "style.css").read_text(encoding="utf-8")
    assert "PicasaPy" in stilus
    assert (cel / "assets" / "extra.css").is_file()


def test_az_xml_sablon_album_es_kepadatot_ad(album):
    """A gépi kimenet: egyetlen `album.xml`, album- és képadatokkal."""
    adat, cel, settings = album
    report = run_web_export(_TEMPLATES / "xml", cel, adat, settings)
    assert [f.name for f in report.output_files] == ["album.xml"]

    gyoker = ElementTree.parse(cel / "album.xml").getroot()
    assert gyoker.tag == "album"
    assert gyoker.get("name") == "Nyaralás & tábor"
    assert gyoker.get("itemCount") == "2"
    assert gyoker.findtext("caption") == "2026 nyara"

    kepek = gyoker.findall("./photos/photo")
    assert [k.get("name") for k in kepek] == ["a.jpg", "b.jpg"]
    assert kepek[0].findtext("caption") == 'Anyu & Apu <a "nyaralás">'
    assert kepek[1].find("caption") is None  # felirat nélküli kép
    assert kepek[0].find("original").get("width") == "400"
    assert kepek[0].find("thumbnail").get("src")
    assert kepek[0].find("large").get("src")
