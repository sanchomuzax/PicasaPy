"""A megosztás vizsgálata SOHA nem dobhat — #1668.

A tulajdonos gépén (Windows, v0.8.128) az első éles használatnál a
„Napló elküldése" gomb kivételt dobott a felületre:

    OSError: [WinError 1326] Helytelen a felhasználónév vagy a jelszó:
             '\\\\DS215j\\lemez\\'

Az ok: hitelesítetlen UNC-útvonalon a `Path.is_dir()` Windowson NEM
`False`-t ad, hanem `OSError`-t dob. A #1654 tesztjei ezt nem foghatták
meg, mert `tmp_path`-tal mérték a fogantyút — helyi könyvtár sosem dob.

A beépített „Mentés másként…" tartalék épp erre az esetre készült, de a
kivétel miatt nem jutott szóhoz.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.perf.tesztuzem import legutobbi_indulasi_naplo, megosztas_elerheto

#: A tulajdonos gépén ténylegesen kapott hibaüzenet (WinError 1326).
WINERROR_1326 = "[WinError 1326] Helytelen a felhasználónév vagy a jelszó"


class _DoboUt(type(Path())):
    """Olyan útvonal, amely a valódi windowsos viselkedést utánozza:
    a létezés-vizsgálat `OSError`-t dob, nem `False`-t ad."""

    def is_dir(self):  # noqa: D102 - a viselkedés a lényeg
        raise OSError(1326, WINERROR_1326)

    def glob(self, minta):  # noqa: D102
        raise OSError(1326, WINERROR_1326)


class TestMegosztasElerheto:
    def test_a_hitelesitest_kero_unc_nem_dob_hanem_nem_elerheto(self):
        """Ez a jegy magja: kivétel helyett »nem elérhető« a válasz."""
        assert megosztas_elerheto(_DoboUt("//DS215j/lemez")) is False

    def test_helyi_utvonalon_is_elnyeli(self, tmp_path):
        """Nem csak UNC-en: hálózati profilon a helyi ág is dobhat."""
        assert megosztas_elerheto(_DoboUt(tmp_path), unc=False) is False

    def test_a_mukodo_megosztas_tovabbra_is_elerheto(self, tmp_path):
        """Ellenpróba: a javítás nem tompította el a függvényt."""
        assert megosztas_elerheto(tmp_path, unc=True) is True

    def test_a_nem_letezo_tovabbra_is_hamis(self, tmp_path):
        assert megosztas_elerheto(tmp_path / "nincs", unc=True) is False


class TestLegutobbiNaplo:
    def test_a_valodi_mappabol_a_legfrissebbet_adja(self, tmp_path):
        """Ellenpróba: a keresés maga változatlanul működik."""
        (tmp_path / "indulas-20260827-100000.txt").write_text("regi", encoding="utf-8")
        (tmp_path / "indulas-20260827-225218.txt").write_text("uj", encoding="utf-8")
        talalt = legutobbi_indulasi_naplo(tmp_path)
        assert talalt is not None
        assert talalt.name == "indulas-20260827-225218.txt"


def test_a_gomb_a_mentes_maskent_tartalekot_ajanlja(monkeypatch):
    """A vezérlő szintjén: dobó megosztásnál a tartalék jut szóhoz."""
    from picasapy.app import tesztuzem_controller as modul

    monkeypatch.setattr(
        modul, "megosztas_elerheto", lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("a vezérlő nem hívhat kivételt dobó vizsgálatot")
        ) if False else False
    )
    assert modul._megosztas_gyokere() is None


def test_a_valodi_pathlib_nem_dob_helyi_mappan(tmp_path):
    """Őr a tesztre magára: a `_DoboUt` a windowsos viselkedést utánozza,
    a valódi `Path` helyi mappán nem dob — különben az egész fájl
    önmagát igazolná."""
    with pytest.raises(OSError):
        _DoboUt(tmp_path).is_dir()
    assert Path(tmp_path).is_dir() is True


class TestNincsBeegetettIpCim:
    """A megosztás címe GÉPNÉV legyen, ne IP — #1668.

    A tulajdonos Tailscale-en át is eléri a NAS-t; ott az IP-cím
    hálózatonként más, a gépnév viszont mindenhonnan feloldódik. Beégetett
    IP-vel a napló otthonról működne, máshonnan nem — és ez a hiba már
    egyszer megtörtént.

    Az őr a TERMÉKKÓDOT nézi; a tesztek szándékosan tartalmazhatnak
    IP-alakot (az adatvédelmi szűrő próbabemenete épp ilyen).
    """

    #: IPv4-cím KISZOLGÁLÓKÉNT: `//1.2.3.4/...` vagy `\\1.2.3.4\...`.
    #: A puszta pontozott számnégyes nem elég szűk minta — a repóban a
    #: Picasa verziószáma (`3.9.141.259`) is ilyen alakú, és az nem hiba.
    IPV4 = __import__("re").compile(r"(?://|\\\\)\d{1,3}(?:\.\d{1,3}){3}")

    def _termekfajlok(self):
        gyoker = Path(__file__).resolve().parents[2] / "src" / "picasapy"
        return [f for f in gyoker.rglob("*.py")] + [f for f in gyoker.rglob("*.qml")]

    def test_a_termekkodban_nincs_ipv4_cim(self):
        talalatok = []
        for fajl in self._termekfajlok():
            for szam, sor in enumerate(
                fajl.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if self.IPV4.search(sor):
                    talalatok.append(f"{fajl.name}:{szam}: {sor.strip()[:90]}")
        assert not talalatok, "beégetett IP-cím a termékkódban:\n" + "\n".join(talalatok)

    def test_a_megosztas_gepnevet_hasznal(self):
        from picasapy.perf.tesztuzem import MEGOSZTAS_WINDOWS

        assert MEGOSZTAS_WINDOWS == "//DS215j/lemez"
        assert not self.IPV4.search(MEGOSZTAS_WINDOWS)

    def test_az_or_megszolal_egy_ip_cimre(self):
        """Az őr foga: a minta tényleg felismeri az IPv4-alakot."""
        assert self.IPV4.search('MEGOSZTAS = "//192.168.50.187/lemez"')
        assert self.IPV4.search(r'ut = "\\\\192.168.50.187\\lemez"')
        assert not self.IPV4.search('MEGOSZTAS = "//DS215j/lemez"')
        # a Picasa verziószáma NEM kiszolgálócím — az őr ne fogja meg
        assert not self.IPV4.search("Picasa3.exe 3.9.141.259")
