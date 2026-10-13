"""#4579: JPEG-minőség becslése a DQT-ből + mintavétel-utótag (spec 17. E)."""

import io
import struct

from PIL import Image

from picasapy.metadata.jpeg_quality import jpeg_quality_text


def _jpeg(tmp_path, quality, subsampling, name="k.jpg"):
    path = tmp_path / name
    Image.effect_noise((32, 32), 40).convert("RGB").save(
        path, "JPEG", quality=quality, subsampling=subsampling
    )
    return path


def test_q75_420_mintaval(tmp_path):
    assert jpeg_quality_text(_jpeg(tmp_path, 75, 2)) == "75 (411)"


def test_q90_420(tmp_path):
    assert jpeg_quality_text(_jpeg(tmp_path, 90, 2)) == "90 (411)"


def test_q95_444(tmp_path):
    assert jpeg_quality_text(_jpeg(tmp_path, 95, 0)) == "95 (444)"


def test_q75_422(tmp_path):
    assert jpeg_quality_text(_jpeg(tmp_path, 75, 1)) == "75 (422)"


def test_minden_elem_egy_szazat_ad(tmp_path):
    assert jpeg_quality_text(_jpeg(tmp_path, 100, 0)) == "100 (444)"


def test_alacsony_minoseg_is_kap_sort(tmp_path):
    """Szándékos eltérés: az eredeti előjeles hibáját nem vesszük át."""
    szoveg = jpeg_quality_text(_jpeg(tmp_path, 20, 0))
    assert szoveg is not None and szoveg.startswith("20")


def test_szurke_kep_444(tmp_path):
    path = tmp_path / "szurke.jpg"
    Image.effect_noise((32, 32), 40).save(path, "JPEG", quality=85)
    assert jpeg_quality_text(path) == "85 (444)"


def test_nem_jpeg_nincs_sor(tmp_path):
    path = tmp_path / "k.png"
    Image.new("RGB", (4, 4)).save(path, "PNG")
    assert jpeg_quality_text(path) is None


def test_hianyzo_fajl_nincs_sor(tmp_path):
    assert jpeg_quality_text(tmp_path / "nincs.jpg") is None


def test_csonka_dqt_nincs_sor(tmp_path):
    szegmens = b"\x00" + bytes(10)
    adat = b"\xff\xd8\xff\xdb" + struct.pack(">H", len(szegmens) + 2) + szegmens
    path = tmp_path / "csonka.jpg"
    path.write_bytes(adat + b"\xff\xd9")
    assert jpeg_quality_text(path) is None


def test_csak_az_utolso_tabla_szamit(tmp_path):
    """Két DQT-szegmens: az UTOLSÓ (szín) táblából jön a becslés."""
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), "red").save(buf, "JPEG", quality=60)
    path = tmp_path / "hatvan.jpg"
    path.write_bytes(buf.getvalue())
    assert jpeg_quality_text(path).startswith("60")


class _SzamlaloFajl(io.BufferedReader):
    """Számolja, hány bájtot olvasott le a hívó."""

    olvasott = 0

    def read(self, meret=-1):
        adat = super().read(meret)
        type(self).olvasott += len(adat)
        return adat


def test_nagy_fajlbol_csak_a_fejlecet_olvassa(tmp_path, monkeypatch):
    """Szegmensenkénti olvasás, SOS-nál stop: 6 MB-os fájlból pár tíz kB."""
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), "red").save(buf, "JPEG", quality=80)
    jpeg = buf.getvalue()
    sos = jpeg.index(b"\xff\xda")
    path = tmp_path / "nagy.jpg"
    path.write_bytes(jpeg[:sos] + b"\xff\xda\x00\x08" + bytes(6) + bytes(6 * 1024 * 1024))
    import builtins

    igazi_open = builtins.open
    _SzamlaloFajl.olvasott = 0

    def szamolo_open(fajl, mod="r", *a, **kw):
        if str(fajl) == str(path) and "b" in mod:
            return _SzamlaloFajl(igazi_open(fajl, "rb", buffering=0), 1)
        return igazi_open(fajl, mod, *a, **kw)

    monkeypatch.setattr("picasapy.metadata.jpeg_quality.open", szamolo_open, raising=False)
    assert jpeg_quality_text(path).startswith("80")
    assert _SzamlaloFajl.olvasott < 64 * 1024


def test_ffd8_nelkuli_fajlbol_nem_olvas_tobbet_par_bajtnal(tmp_path, monkeypatch):
    path = tmp_path / "x.jpg"
    path.write_bytes(b"\x89PNG" + bytes(1024 * 1024))
    import builtins

    igazi_open = builtins.open
    _SzamlaloFajl.olvasott = 0

    def szamolo_open(fajl, mod="r", *a, **kw):
        if str(fajl) == str(path) and "b" in mod:
            return _SzamlaloFajl(igazi_open(fajl, "rb", buffering=0), 1)
        return igazi_open(fajl, mod, *a, **kw)

    monkeypatch.setattr("picasapy.metadata.jpeg_quality.open", szamolo_open, raising=False)
    assert jpeg_quality_text(path) is None
    assert _SzamlaloFajl.olvasott <= 16
