"""A gyorstár RENDERELT képpontot tárol — de elavultat is (#1447).

A #951 negatív eredményét (`docs/specs/pmp-database.md`) egy SZÍNALAPÚ
kontroll-mérés zárta le, ami jogosan nem tudta a szerkesztett képpontot a
meleg tónusú EREDETIKTŐL megkülönböztetni. A kérdés viszont eldönthető
**színek nélkül, geometriával**: a `crop64` külön rögzített téglalap, tehát a
vágott kép aránya előre jelezhető, és a bélyegkép arányával összevethető.

Ez a fájl a mérést **őrzi**, hogy egy későbbi kör ne kezdje elölről, és hogy
az állítás ne csússzon el a kód alatt:

1. a párosítás kontrollja (szerkesztetlen fotók: az arány egyezik) — és hogy
   a kivételek MIND arc-rekordok, nem párosítási hibák;
2. mindkét állapot előfordul: vágott arányú ÉS eredeti arányú bélyegkép is,
   **köztes eset nélkül**;
3. a „elavult" csoport magyarázata: ugyanaz a fájlnév más mappában.

⚠️ **Kimondva: a próbák a gitignore-olt `research/testdata`-t igénylik, tehát
a CI-n KIMARADNAK.** Ez a fájl nem futásidejű viselkedést őriz, hanem egy
MÉRÉST — a helye a spec mellett van, és a számai csak akkor ellenőrizhetők, ha
a katalógus kézzel megvan. Útvonalat SOSEM ír a kimenetbe (magánadat).
"""

from __future__ import annotations

import re
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.ini.rect64 import decode_rect64
from picasapy.pmpimport import (
    open_cache_store,
    read_pmp_column,
    read_thumb_index,
    resolve_path,
)

_VALODI = Path(
    "/home/sancho/Documents/PicasaPy/research/testdata/Picasa2-arcok/Picasa2/db3"
)

pytestmark = pytest.mark.skipif(
    not _VALODI.is_dir(), reason="a valódi katalógus nincs itt (gitignore)"
)

#: „döntő" eset: a vágott és az eredeti arány legalább ennyiben eltér
_DONTO_KULONBSEG = 0.05
#: egyezés-tűrés: a bélyegkép hosszabb oldala 144 képpontra kvantált
_TURES = 0.02


def _oszlop(nev: str) -> list:
    return list(read_pmp_column(_VALODI / f"imagedata_{nev}.pmp").values)


def _forgatas_lepes(ertek: str) -> int:
    egyezes = re.match(r"rotate\((\d)\)", ertek or "")
    return int(egyezes.group(1)) if egyezes else 0


@pytest.fixture(scope="module")
def katalogus():
    return {
        "filters": _oszlop("filters"),
        "width": _oszlop("width"),
        "height": _oszlop("height"),
        "rotate": _oszlop("rotate"),
        "tar": open_cache_store(_VALODI, "thumbs"),
        "bejegyzesek": read_thumb_index(_VALODI / "thumbindex.db"),
    }


def _belyegkep_arany(tar, slot: int) -> float | None:
    bejegyzes = tar.slot(slot)
    if bejegyzes is None or bejegyzes.ures:
        return None
    kep = cv2.imdecode(np.frombuffer(tar.blob(slot), np.uint8), cv2.IMREAD_COLOR)
    if kep is None:
        return None
    return kep.shape[1] / kep.shape[0]


class TestAParositasKontrollja:
    def test_a_szerkesztetlen_fotok_aranya_HIBATLANUL_egyezik(self, katalogus) -> None:
        tar, bej = katalogus["tar"], katalogus["bejegyzesek"]
        egyezik = elter = 0
        for slot, lanc in enumerate(katalogus["filters"]):
            if slot >= len(bej) or bej[slot].is_face_record or bej[slot].is_directory:
                continue
            szeles, magas = katalogus["width"][slot], katalogus["height"][slot]
            if lanc or not szeles or not magas:
                continue
            arany = _belyegkep_arany(tar, slot)
            if arany is None:
                continue
            fordit = _forgatas_lepes(katalogus["rotate"][slot]) % 2 == 1
            vart = (magas / szeles) if fordit else (szeles / magas)
            if abs(arany - vart) / vart < _TURES:
                egyezik += 1
            else:
                elter += 1
        assert egyezik > 1000, f"túl kevés mért eset ({egyezik})"
        assert elter == 0, (
            f"#1447: a szerkesztetlen fotók közül {elter} bélyegképének aránya "
            "nem egyezik a katalógus méreteivel — a slot ↔ PMP-sor párosítás "
            "nem hibátlan, tehát a #1446 olvasója rossz képhez rendelhet blobot"
        )

    def test_az_arc_rekordok_aranya_MASE_es_ez_nem_parositasi_hiba(
        self, katalogus
    ) -> None:
        """A nyers összevetés 85,7 %-ot adna; a kivételek mind arc-rekordok."""
        tar, bej = katalogus["tar"], katalogus["bejegyzesek"]
        arc_elter = 0
        for slot, lanc in enumerate(katalogus["filters"]):
            if slot >= len(bej) or not bej[slot].is_face_record:
                continue
            szeles, magas = katalogus["width"][slot], katalogus["height"][slot]
            if lanc or not szeles or not magas:
                continue
            arany = _belyegkep_arany(tar, slot)
            if arany is None:
                continue
            legjobb = min(
                abs(arany - szeles / magas) / (szeles / magas),
                abs(arany - magas / szeles) / (magas / szeles),
            )
            if legjobb >= _TURES:
                arc_elter += 1
        assert arc_elter > 100, (
            "az arc-rekordok aránya a szülő fotóétól ELTÉR — ha ez nullára "
            "csökken, a magyarázat elavult, és a 240 kivételt újra kell vizsgálni"
        )


class TestMindkETALLAPOT_elofordul:
    @staticmethod
    def _dontő_esetek(katalogus):
        tar, bej = katalogus["tar"], katalogus["bejegyzesek"]
        vagott: list[int] = []
        eredeti: list[int] = []
        egyik_sem: list[int] = []
        for slot, lanc in enumerate(katalogus["filters"]):
            if slot >= len(bej) or bej[slot].is_face_record or bej[slot].is_directory:
                continue
            if not lanc or "crop64" not in lanc or "tilt" in lanc:
                continue
            egyezes = re.search(r"crop64=1,([0-9a-fA-F]+)", lanc)
            szeles, magas = katalogus["width"][slot], katalogus["height"][slot]
            if not egyezes or not szeles or not magas:
                continue
            teglalap = decode_rect64(egyezes.group(1))
            vagott_sz = (teglalap.right - teglalap.left) * szeles
            vagott_ma = (teglalap.bottom - teglalap.top) * magas
            if vagott_sz <= 0 or vagott_ma <= 0:
                continue
            arany = _belyegkep_arany(tar, slot)
            if arany is None:
                continue
            fordit = _forgatas_lepes(katalogus["rotate"][slot]) % 2 == 1
            av = (vagott_ma / vagott_sz) if fordit else (vagott_sz / vagott_ma)
            ae = (magas / szeles) if fordit else (szeles / magas)
            if abs(av - ae) / max(av, ae) < _DONTO_KULONBSEG:
                continue
            jo_v = abs(arany - av) / av < _TURES
            jo_e = abs(arany - ae) / ae < _TURES
            if jo_v and not jo_e:
                vagott.append(slot)
            elif jo_e and not jo_v:
                eredeti.append(slot)
            else:
                egyik_sem.append(slot)
        return vagott, eredeti, egyik_sem

    def test_van_VAGOTT_aranyu_belyegkep(self, katalogus) -> None:
        vagott, _eredeti, _egyik = self._dontő_esetek(katalogus)
        assert len(vagott) >= 40, (
            "#1447: a tár RENDERELT képpontot tárol — ezt a vágott arányú "
            f"bélyegképek mutatják, most {len(vagott)} van (mérve: 42)"
        )

    def test_van_ELAVULT_belyegkep_is(self, katalogus) -> None:
        _vagott, eredeti, _egyik = self._dontő_esetek(katalogus)
        assert len(eredeti) >= 20, (
            "#1447: a tár NEM igazságforrás — a vágás előtti arányú bélyegképek "
            f"ezt mutatják, most {len(eredeti)} van (mérve: 26)"
        )

    def test_KOZTES_eset_NINCS(self, katalogus) -> None:
        """A bimodalitás a bizonyíték: minden bélyegkép élesen az egyik
        állapotot mutatja. Köztes esetek megjelenése azt jelentené, hogy az
        arány-összevetés nem elég éles őr."""
        _vagott, _eredeti, egyik_sem = self._dontő_esetek(katalogus)
        assert egyik_sem == [], (
            "#1447: olyan bélyegkép, ami se a vágott, se az eredeti aránnyal "
            f"nem egyezik: {len(egyik_sem)} db"
        )


class TestAzElavultCsoportMagyarazata:
    def test_ugyanaz_a_fajlnev_MAS_mappaban(self, katalogus) -> None:
        """Az elavult példányok a kétszer meglévő képek másodpéldányai."""
        bej = katalogus["bejegyzesek"]
        _vagott, eredeti, _egyik = TestMindkETALLAPOT_elofordul._dontő_esetek(
            katalogus
        )
        assert eredeti, "nincs elavult eset — a magyarázat elavult"
        nevek: dict[str, list[int]] = {}
        for slot in range(len(bej)):
            if bej[slot].is_face_record or bej[slot].is_directory:
                continue
            nev = resolve_path(bej, bej[slot]).rsplit("\\", 1)[-1].lower()
            nevek.setdefault(nev, []).append(slot)
        tobbszorosek = sum(
            1 for slot in eredeti
            if len(nevek.get(
                resolve_path(bej, bej[slot]).rsplit("\\", 1)[-1].lower(), []
            )) > 1
        )
        assert tobbszorosek == len(eredeti), (
            "#1447: nem minden elavult bélyegkép tartozik többször meglévő "
            f"fájlnévhez ({tobbszorosek}/{len(eredeti)}) — a magyarázat "
            "(kétszer meglévő kép, csak az egyik példány gyorstára friss) "
            "nem tartható"
        )
