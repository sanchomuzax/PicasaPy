"""#7143: azonos mappában nincs Beillesztés, sikeres beillesztés után kiürül a belső vágólap.

Az eredeti (`0x0056ec92`, `0x00784100`): a Beillesztés csak akkor él, ha a
belső lista nem üres ÉS a mappa eltér a forrástól; azonos mappában nincs
fájlművelet. A sikeres beillesztés a belső listát kiüríti (`0x005feaeb-0x005feb05`),
a Mégse megtartja.

Ez a fájl a VEZÉRLŐ oldalát méri (a kapu, a köteg nem indulása, a vágólap
ürülése). A kirajzolt menüt és a billentyűt a
`qml_functional/test_kivagas_beillesztes_kapu_7143.py` méri a valódi főablakon.

Mit őriz (a jegy „Kész, ha” és „Nem szabad” pontjai):
  * azonos mappában (másolás és kivágás is) nincs köteg, nincs megerősítés,
    nem keletkezik fájl;
  * vegyes vágólapnál csak a másik mappából való fájl indul;
  * sikeres köteg után a SAJÁT vágólap üres, és a menüjelzés frissül;
  * hibás, nem indult vagy Mégse esetén a vágólap megmarad;
  * külső program vágólapjához (nem mi birtokoljuk) nem nyúlunk.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QByteArray, QMimeData, QUrl

from picasapy.app import fileops_controller as compat
from picasapy.app.fileops_controller import FileOpsController, vagolap_fajlok

_GNOME = "x-special/gnome-copied-files"


def _mime(utak, muvelet: str) -> QMimeData:
    adat = QMimeData()
    urlek = [QUrl.fromLocalFile(str(u)) for u in utak]
    adat.setUrls(urlek)
    sorok = [muvelet, *(u.toString() for u in urlek)]
    adat.setData(_GNOME, QByteArray("\n".join(sorok).encode("utf-8")))
    return adat


@pytest.fixture
def vezerlo(qt_app):
    return FileOpsController()


@pytest.fixture
def mappak(tmp_path):
    """`forras` (a.jpg, b.jpg) és egy üres `cel` mappa."""
    forras = tmp_path / "forras"
    cel = tmp_path / "cel"
    forras.mkdir()
    cel.mkdir()
    for nev in ("a.jpg", "b.jpg"):
        (forras / nev).write_bytes(nev.encode())
    return SimpleNamespace(forras=forras, cel=cel, gyoker=tmp_path)


def _fa(gyoker: Path) -> list[str]:
    return sorted(str(p.relative_to(gyoker)) for p in gyoker.rglob("*"))


def _kotegek(vezerlo, monkeypatch, eredmeny=None):
    """A két köteg-utat és a megerősítő jelzést figyeli; semmit nem futtat."""
    hivasok: list[tuple] = []
    for nev in ("_copy_batch", "_move_batch"):
        monkeypatch.setattr(
            vezerlo,
            nev,
            lambda *a, _nev=nev, **k: hivasok.append((_nev, a)) or eredmeny,
        )
    kerdesek: list[tuple] = []
    vezerlo.clipboardPasteConfirmationRequested.connect(
        lambda *args: kerdesek.append(args)
    )
    return hivasok, kerdesek


class TestAzonosMappaKapu:
    def test_a_vagolap_fajljai_mind_a_celmappaban_vannak(self, vezerlo, mappak):
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])

        assert vezerlo.clipboardOnlyInFolder(str(mappak.forras)) is True
        assert vezerlo.clipboardOnlyInFolder(str(mappak.cel)) is False

    def test_cel_nelkul_nem_tiltott_hogy_a_celhiany_uzenet_megjelenjen(
        self, vezerlo, mappak
    ):
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])

        assert vezerlo.clipboardOnlyInFolder("") is False

    def test_ures_vagolapnal_nem_tiltott(self, vezerlo, mappak):
        assert vezerlo.clipboardHasFiles is False

        assert vezerlo.clipboardOnlyInFolder(str(mappak.forras)) is False

    def test_vegyes_vagolapnal_nem_tiltott(self, vezerlo, mappak):
        (mappak.cel / "c.jpg").write_bytes(b"c")
        vezerlo.copyFilesToClipboard(
            [str(mappak.forras / "a.jpg"), str(mappak.cel / "c.jpg")]
        )

        assert vezerlo.clipboardOnlyInFolder(str(mappak.forras)) is False
        assert vezerlo.clipboardOnlyInFolder(str(mappak.cel)) is False

    @pytest.mark.parametrize("muvelet", ["copy", "cut"])
    @pytest.mark.parametrize("mappa_cel", [True, False])
    def test_azonos_mappaban_nincs_fajlmuvelet_kerdes_es_uj_fajl(
        self, vezerlo, mappak, monkeypatch, muvelet, mappa_cel
    ):
        kep = mappak.forras / "a.jpg"
        if muvelet == "copy":
            vezerlo.copyFilesToClipboard([str(kep)])
        else:
            vezerlo.cutFilesToClipboard([str(kep)])
        hivasok, kerdesek = _kotegek(vezerlo, monkeypatch)
        elotte = _fa(mappak.gyoker)

        assert vezerlo.pasteFilesFromClipboard(str(mappak.forras), mappa_cel) is False

        assert hivasok == [], "azonos mappában nem indulhat köteg"
        assert kerdesek == [], "azonos mappában nincs megerősítés"
        assert _fa(mappak.gyoker) == elotte, "azonos mappába fájl keletkezett vagy mozdult"
        assert kep.read_bytes() == b"a.jpg"

    def test_az_azonos_mappas_beillesztes_valodi_kotegen_sem_masol(
        self, vezerlo, mappak
    ):
        """A korábbi viselkedés `a-1.jpg`-t készített; most semmi nem jön létre."""
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])
        elotte = _fa(mappak.gyoker)

        assert vezerlo.pasteFilesFromClipboard(str(mappak.forras), False) is False

        assert _fa(mappak.gyoker) == elotte
        assert vezerlo.clipboardHasFiles is True, "a tiltott beillesztés nem üríthet"

    def test_vegyes_vagolapnal_csak_a_masik_mappa_fajlja_kerul_a_kerdesbe(
        self, vezerlo, mappak, monkeypatch
    ):
        (mappak.cel / "c.jpg").write_bytes(b"c")
        vezerlo.copyFilesToClipboard(
            [str(mappak.forras / "a.jpg"), str(mappak.cel / "c.jpg")]
        )
        hivasok, kerdesek = _kotegek(vezerlo, monkeypatch)

        assert vezerlo.pasteFilesFromClipboard(str(mappak.forras)) is True

        assert hivasok == []
        assert len(kerdesek) == 1
        paths, dest, muvelet = kerdesek[0]
        assert [Path(p) for p in paths] == [mappak.cel / "c.jpg"], (
            "a célmappában lévő fájl is felkerült a kérdésre"
        )
        assert Path(dest) == mappak.forras
        assert muvelet == "copy"

    def test_vegyes_vagolapnal_nem_mappacelnel_csak_a_masik_mappa_fajlja_indul(
        self, vezerlo, mappak, monkeypatch
    ):
        (mappak.cel / "c.jpg").write_bytes(b"c")
        vezerlo.copyFilesToClipboard(
            [str(mappak.forras / "a.jpg"), str(mappak.cel / "c.jpg")]
        )
        hivasok, kerdesek = _kotegek(vezerlo, monkeypatch)

        assert vezerlo.pasteFilesFromClipboard(str(mappak.forras), False) is True

        assert kerdesek == []
        assert [nev for nev, _ in hivasok] == ["_copy_batch"]
        utak, dest = hivasok[0][1][0], hivasok[0][1][1]
        assert [Path(p) for p in utak] == [mappak.cel / "c.jpg"]
        assert Path(dest) == mappak.forras


class TestSikeresBeillesztesUtan:
    @pytest.mark.parametrize("muvelet", ["copy", "cut"])
    def test_a_sikeres_kotegfuttatas_uriti_a_sajat_vagolapot(
        self, vezerlo, mappak, muvelet
    ):
        kep = mappak.forras / "a.jpg"
        if muvelet == "copy":
            vezerlo.copyFilesToClipboard([str(kep)])
        else:
            vezerlo.cutFilesToClipboard([str(kep)])
        assert vezerlo.clipboardHasFiles is True
        jelzesek: list[int] = []
        vezerlo.clipboardFilesChanged.connect(lambda: jelzesek.append(1))

        vezerlo.runPasteBatch(muvelet, [str(kep)], str(mappak.cel), "rename")

        assert (mappak.cel / "a.jpg").exists(), "a köteg nem másolt/mozgatott"
        assert vezerlo.clipboardHasFiles is False, "a sikeres beillesztés után él a tétel"
        assert vezerlo._vagolap_adat is None
        assert jelzesek, "a menü nem kapott jelzést a vágólap ürüléséről"

    def test_a_kozvetlen_nem_mappas_ut_is_uriti(self, vezerlo, mappak):
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])

        assert vezerlo.pasteFilesFromClipboard(str(mappak.cel), False) is True

        assert (mappak.cel / "a.jpg").exists()
        assert vezerlo.clipboardHasFiles is False

    def test_a_megerosites_kerese_meg_nem_uriti_a_mege_pedig_megtartja(
        self, vezerlo, mappak
    ):
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])
        kerdesek: list[tuple] = []
        vezerlo.clipboardPasteConfirmationRequested.connect(
            lambda *args: kerdesek.append(args)
        )

        assert vezerlo.pasteFilesFromClipboard(str(mappak.cel)) is True

        assert len(kerdesek) == 1
        assert vezerlo.clipboardHasFiles is True, "a Mégse-ig a lista nem üríthető"
        assert not (mappak.cel / "a.jpg").exists()

    def test_hibas_koteg_utan_a_vagolap_megmarad(self, vezerlo, mappak, monkeypatch):
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])
        hiba = SimpleNamespace(
            failed=[(mappak.forras / "a.jpg", "No space")], done=[], skipped=[]
        )
        _kotegek(vezerlo, monkeypatch, eredmeny=hiba)

        vezerlo.runPasteBatch(
            "copy", [str(mappak.forras / "a.jpg")], str(mappak.cel), "rename"
        )

        assert vezerlo.clipboardHasFiles is True

    def test_nem_indult_koteg_utan_a_vagolap_megmarad(
        self, vezerlo, mappak, monkeypatch
    ):
        vezerlo.cutFilesToClipboard([str(mappak.forras / "a.jpg")])
        _kotegek(vezerlo, monkeypatch, eredmeny=None)

        vezerlo.runPasteBatch(
            "cut", [str(mappak.forras / "a.jpg")], str(mappak.cel), "rename"
        )

        assert vezerlo.clipboardHasFiles is True

    def test_kozben_masra_cserelt_vagolapot_nem_uritunk(self, vezerlo, mappak):
        a, b = mappak.forras / "a.jpg", mappak.forras / "b.jpg"
        vezerlo.copyFilesToClipboard([str(a)])
        # a megerősítés közben új Másolás történt: a vágólap már a `b.jpg`
        vezerlo.copyFilesToClipboard([str(b)])

        vezerlo.runPasteBatch("copy", [str(a)], str(mappak.cel), "rename")

        assert (mappak.cel / "a.jpg").exists()
        fajlok, _ = vagolap_fajlok(vezerlo._vagolap_adata())
        assert [Path(f) for f in fajlok] == [b], "az újabb Másolás tartalma elveszett"

    def test_az_albumba_illesztes_is_uriti_a_sajat_vagolapot(self, vezerlo, mappak):
        vezerlo._album_tagsag_iro = lambda fajlok, token: True
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])

        assert vezerlo.pasteFilesFromClipboard("", True, "album-token") is True

        assert vezerlo.clipboardHasFiles is False

    def test_a_sikertelen_albumba_illesztes_megtartja_a_vagolapot(
        self, vezerlo, mappak
    ):
        vezerlo._album_tagsag_iro = lambda fajlok, token: False
        vezerlo.copyFilesToClipboard([str(mappak.forras / "a.jpg")])

        assert vezerlo.pasteFilesFromClipboard("", True, "album-token") is False

        assert vezerlo.clipboardHasFiles is True


class _HamisVagolap:
    """Egy valódi (nem fej nélküli) rendszervágólap szerepét játssza."""

    def __init__(self, adat: QMimeData, sajat: bool) -> None:
        self._adat = adat
        self._sajat = sajat
        self.torlesek = 0

    def mimeData(self):  # noqa: N802 - Qt-név
        return self._adat

    def ownsClipboard(self) -> bool:  # noqa: N802 - Qt-név
        return self._sajat

    def clear(self) -> None:
        self.torlesek += 1
        self._adat = QMimeData()


class _HamisAlkalmazas:
    """A `QGuiApplication` helyett: a mixin csak ezt a három hívást használja."""

    vagolap: _HamisVagolap | None = None

    @staticmethod
    def platformName() -> str:  # noqa: N802 - Qt-név
        return "xcb"

    @staticmethod
    def clipboard():
        return _HamisAlkalmazas.vagolap


class TestRendszervagolapNemHeadless:
    @pytest.fixture
    def hamis(self, vezerlo, monkeypatch):
        monkeypatch.setattr(compat, "QGuiApplication", _HamisAlkalmazas)
        yield _HamisAlkalmazas
        _HamisAlkalmazas.vagolap = None

    def test_kulso_program_vagolapjahoz_nem_nyulunk(self, vezerlo, mappak, hamis):
        kulso = _mime([mappak.forras / "a.jpg"], "copy")
        hamis.vagolap = _HamisVagolap(kulso, sajat=False)
        assert vezerlo.clipboardHasFiles is True

        vezerlo.runPasteBatch(
            "copy", [str(mappak.forras / "a.jpg")], str(mappak.cel), "rename"
        )

        assert (mappak.cel / "a.jpg").exists()
        assert hamis.vagolap.torlesek == 0, "külső program vágólapját töröltük"
        assert vezerlo.clipboardHasFiles is True

    def test_a_sajat_rendszervagolapot_uritjuk(self, vezerlo, mappak, hamis):
        sajat = _mime([mappak.forras / "a.jpg"], "copy")
        hamis.vagolap = _HamisVagolap(sajat, sajat=True)
        assert vezerlo.clipboardHasFiles is True

        vezerlo.runPasteBatch(
            "copy", [str(mappak.forras / "a.jpg")], str(mappak.cel), "rename"
        )

        assert hamis.vagolap.torlesek == 1
        assert vezerlo.clipboardHasFiles is False

    def test_a_sajat_de_mas_tartalmu_vagolapot_nem_uritjuk(
        self, vezerlo, mappak, hamis
    ):
        """A mi birtokunk, de már más fájlok vannak rajta (új Másolás)."""
        ujabb = _mime([mappak.forras / "b.jpg"], "copy")
        hamis.vagolap = _HamisVagolap(ujabb, sajat=True)

        vezerlo.runPasteBatch(
            "copy", [str(mappak.forras / "a.jpg")], str(mappak.cel), "rename"
        )

        assert hamis.vagolap.torlesek == 0
        assert vezerlo.clipboardHasFiles is True
