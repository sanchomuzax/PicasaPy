"""#2496 — a rács rendezőkulcsa nem szállhat el romlott fájlidőtől.

## A lelet (a #2304 átnézése)

A `photo_date()` EXIF nélkül a fájl idejéből számol, és ez **dobhat**::

    mtime_ns = 10**26  →  OSError: [Errno 75] Value too large …
    mtime_ns = 0       →  '1970-01-01T01:00:00'   (nem dob, csak régi)

A #2304 a FEJLÉC és az ÁLLAPOTSOR útján ezt lekezeli
(`formatting.photo_dates` rekordonként elnyeli és kihagyja a rossz sort),
a RENDEZÉS viszont nyersen hívta a `photo_date()`-et: egyetlen romlott
indexsor a rács felépítését vitte volna ki.

## A választott viselkedés — és miért MÁS, mint a fejlécé

| út | mit tesz a romlott sorral | miért |
|---|---|---|
| fejléc (`photo_dates`) | **kihagyja** | ott egy SZÉLSŐÉRTÉK kell; egy romlott sor évekkel elhúzná a mappa dátumát |
| rendezés (`_sort_key`) | **a lista VÉGÉRE teszi** | itt minden képnek helyet kell kapnia — a kihagyás ELTÜNTETNÉ a képet a rácsból, ami sokkal nagyobb kár, mint egy rossz helyre került sor |

A kettő szándékosan tér el; az indoklás a `photo_sort` docstringjében is
ott áll.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from picasapy.app.photo_sort import photo_date, sort_folder_blocks


@dataclass
class _Foto:
    name: str
    folder_path: str = "/kepek"
    taken_at: str | None = None
    size: int = 100
    mtime_ns: int = 0
    first_seen_mtime_ns: int | None = None

    @property
    def sort_mtime_ns(self) -> int:
        if self.first_seen_mtime_ns is None:
            return self.mtime_ns
        return self.first_seen_mtime_ns


#: 2025-01-02 03:04:05 körüli, ÉP érték
_EP_NS = 1_735_785_845_000_000_000
#: MÉRT romlott érték (a #2304 átnézéséből): a `fromtimestamp` OSError-t ad
_ROMLOTT_NS = 10**26


class TestAzElofeltetel:
    """A nyers hívás TÉNYLEG dob — enélkül az őr semmit nem bizonyít."""

    def test_a_nyers_photo_date_dob_a_romlott_ertekre(self):
        with pytest.raises((OSError, ValueError, OverflowError)):
            photo_date(_Foto("romlott.jpg", first_seen_mtime_ns=_ROMLOTT_NS))

    def test_ep_ertekre_nem_dob(self):
        assert photo_date(_Foto("ep.jpg", first_seen_mtime_ns=_EP_NS))


class TestARendezesFELEPUL:
    def test_romlott_sor_mellett_is_rendez(self):
        fotok = (
            _Foto("b.jpg", first_seen_mtime_ns=_EP_NS),
            _Foto("romlott.jpg", first_seen_mtime_ns=_ROMLOTT_NS),
            _Foto("a.jpg", first_seen_mtime_ns=_EP_NS - 10**9),
        )
        eredmeny = sort_folder_blocks(fotok, "date")
        assert [f.name for f in eredmeny] == ["a.jpg", "b.jpg", "romlott.jpg"]

    def test_egyetlen_kep_sem_VESZ_EL(self):
        """A fejléc kihagyja a romlott sort; a rendezés NEM teheti — az a
        képet tüntetné el a rácsból."""
        fotok = tuple(
            _Foto(f"k{i}.jpg", first_seen_mtime_ns=_ROMLOTT_NS) for i in range(5)
        )
        assert len(sort_folder_blocks(fotok, "date")) == 5

    def test_a_romlott_sor_a_VEGERE_kerul(self):
        fotok = (
            _Foto("romlott.jpg", first_seen_mtime_ns=_ROMLOTT_NS),
            _Foto("ep.jpg", first_seen_mtime_ns=_EP_NS),
        )
        assert [f.name for f in sort_folder_blocks(fotok, "date")] == [
            "ep.jpg",
            "romlott.jpg",
        ]

    def test_forditott_sorrendben_is_felepul(self):
        fotok = (
            _Foto("romlott.jpg", first_seen_mtime_ns=_ROMLOTT_NS),
            _Foto("ep.jpg", first_seen_mtime_ns=_EP_NS),
        )
        assert len(sort_folder_blocks(fotok, "date", reverse=True)) == 2

    def test_TOBB_romlott_sor_egymas_kozt_NEVSORRENDBEN(self):
        """A másodlagos kulcs (fájlnév) a romlott sorokra is érvényes —
        különben a sorrendjük futásfüggő volna."""
        fotok = (
            _Foto("z.jpg", first_seen_mtime_ns=_ROMLOTT_NS),
            _Foto("a.jpg", first_seen_mtime_ns=_ROMLOTT_NS),
            _Foto("m.jpg", first_seen_mtime_ns=_ROMLOTT_NS),
        )
        assert [f.name for f in sort_folder_blocks(fotok, "date")] == [
            "a.jpg",
            "m.jpg",
            "z.jpg",
        ]

    def test_a_MAPPA_blokkok_hatara_marad(self):
        fotok = (
            _Foto("b.jpg", folder_path="/egy", first_seen_mtime_ns=_EP_NS),
            _Foto("r.jpg", folder_path="/egy", first_seen_mtime_ns=_ROMLOTT_NS),
            _Foto("a.jpg", folder_path="/ketto", first_seen_mtime_ns=_EP_NS),
        )
        eredmeny = sort_folder_blocks(fotok, "date")
        assert [f.folder_path for f in eredmeny] == ["/egy", "/egy", "/ketto"]

    def test_EXIF_datummal_a_romlott_fajlido_nem_szamit(self):
        """Ha van felvételi idő, a fájlidőt meg sem nézzük."""
        fotok = (
            _Foto("a.jpg", taken_at="2020-01-01T00:00:00",
                  first_seen_mtime_ns=_ROMLOTT_NS),
            _Foto("b.jpg", taken_at="2019-01-01T00:00:00",
                  first_seen_mtime_ns=_ROMLOTT_NS),
        )
        assert [f.name for f in sort_folder_blocks(fotok, "date")] == [
            "b.jpg",
            "a.jpg",
        ]
