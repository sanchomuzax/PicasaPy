"""ISO 9660 / Joliet lemezképek biztonságos, csak olvasó bejárása."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

_SZEKTOR = 2048
_ELSO_LEIRO = 16
_MAX_MELYSEG = 128


@dataclass(frozen=True)
class ISOFajl:
    """Egy fájl adatai az ISO-képen belül."""

    utvonal: PurePosixPath
    eltolás: int
    meret: int


def _kulcs(utvonal: str | PurePosixPath) -> str:
    return "/".join(resz.casefold() for resz in PurePosixPath(utvonal).parts)


def _nev(adat: bytes, *, joliet: bool) -> str:
    if joliet:
        nev = adat.decode("utf-16-be", errors="replace")
    else:
        nev = adat.decode("ascii", errors="replace")
    return re.sub(r";[0-9]+$", "", nev)


class ISOOlvaso:
    """Egyszerű ECMA-119 olvasó a mentések Joliet-fájlfájával.

    A mentőmodul nem csatolja fel a lemezképet, így Windows alatt is működik.
    A PicasaPy ISO-írója egy kiterjedést használ fájlonként; a többkiterjedésű
    rekordot hangosan elutasítjuk, hogy ne adjunk vissza csonka fájlt.
    """

    def __init__(self, kep: Path) -> None:
        self.kep = Path(kep)
        self._meret = self.kep.stat().st_size
        self._joliet = False
        self._fajlok: dict[str, ISOFajl] = {}
        self._beolvas()

    def fajl(self, utvonal: str | PurePosixPath) -> ISOFajl | None:
        """Fájlt keres kis-/nagybetűtől és ISO-verzióutótagtól függetlenül."""
        return self._fajlok.get(_kulcs(utvonal))

    def fajlok(self) -> tuple[ISOFajl, ...]:
        return tuple(self._fajlok.values())

    def olvas_bajtokat(self, fajl: ISOFajl, *, max_meret: int) -> bytes:
        if fajl.meret > max_meret:
            raise ValueError(
                f"Az ISO-leltár túl nagy ({fajl.meret} bájt): {fajl.utvonal}"
            )
        with self.kep.open("rb") as be:
            be.seek(fajl.eltolás)
            adat = be.read(fajl.meret)
        if len(adat) != fajl.meret:
            raise ValueError(f"Csonka ISO-fájl: {fajl.utvonal}")
        return adat

    def masol(self, fajl: ISOFajl, cel: Path) -> None:
        cel.parent.mkdir(parents=True, exist_ok=True)
        hatralevo = fajl.meret
        with self.kep.open("rb") as be, cel.open("wb") as ki:
            be.seek(fajl.eltolás)
            while hatralevo:
                darab = be.read(min(1 << 20, hatralevo))
                if not darab:
                    raise ValueError(f"Csonka ISO-fájl: {fajl.utvonal}")
                ki.write(darab)
                hatralevo -= len(darab)

    def _szakasz(self, eltolás: int, meret: int) -> bytes:
        if meret < 0 or eltolás < 0 or eltolás + meret > self._meret:
            raise ValueError("A lemezkép egy adatrekordja túlnyúlik a fájlon.")
        with self.kep.open("rb") as be:
            be.seek(eltolás)
            adat = be.read(meret)
        if len(adat) != meret:
            raise ValueError("A lemezkép olvasása csonka adatot adott.")
        return adat

    @staticmethod
    def _rekord(adat: bytes) -> tuple[int, int, int, bytes] | None:
        if len(adat) < 34 or adat[0] < 34:
            return None
        hossz = adat[0]
        if hossz > len(adat) or 33 + adat[32] > hossz:
            return None
        szektor = int.from_bytes(adat[2:6], "little")
        meret = int.from_bytes(adat[10:14], "little")
        jelzok = adat[25]
        nev_hossz = adat[32]
        return szektor, meret, jelzok, adat[33 : 33 + nev_hossz]

    def _kotetgyoker(self) -> tuple[int, int]:
        pvd: bytes | None = None
        joliet: bytes | None = None
        for sorszam in range(64):
            leiro = self._szakasz(
                (_ELSO_LEIRO + sorszam) * _SZEKTOR, _SZEKTOR
            )
            if leiro[1:6] != b"CD001" or leiro[6] != 1:
                raise ValueError("Nem érvényes ISO 9660 lemezkép.")
            if leiro[0] == 1:
                pvd = leiro
            elif (
                leiro[0] == 2
                and leiro[88:90] == b"%/"
                and leiro[90:91] in (b"@", b"C", b"E")
            ):
                joliet = leiro
            elif leiro[0] == 255:
                break
        valasztott = joliet or pvd
        if valasztott is None:
            raise ValueError("A lemezképben nincs ISO 9660 kötetleíró.")
        self._joliet = joliet is not None
        rekord = self._rekord(valasztott[156:])
        if rekord is None or not (rekord[2] & 0x02):
            raise ValueError("A lemezkép gyökérkönyvtára hibás.")
        return rekord[0], rekord[1]

    def _konyvtar(
        self,
        szektor: int,
        meret: int,
        prefix: PurePosixPath,
        latott: set[tuple[int, int]],
        melyseg: int,
    ) -> None:
        if melyseg > _MAX_MELYSEG:
            raise ValueError("A lemezkép könyvtárai túl mélyen egymásba ágyazottak.")
        azon = (szektor, meret)
        if azon in latott:
            return
        latott.add(azon)
        adat = self._szakasz(szektor * _SZEKTOR, meret)
        i = 0
        while i < len(adat):
            hossz = adat[i]
            if hossz == 0:
                i = ((i // _SZEKTOR) + 1) * _SZEKTOR
                continue
            rekord_adat = adat[i : i + hossz]
            rekord = self._rekord(rekord_adat)
            if rekord is None:
                raise ValueError("Hibás könyvtárrekord van a lemezképben.")
            i += hossz
            cel_szektor, cel_meret, jelzok, raw_nev = rekord
            if raw_nev in (b"\x00", b"\x01"):
                continue
            if jelzok & 0x80:
                raise ValueError("A többkiterjedésű ISO-fájl nem támogatott.")
            nev = _nev(raw_nev, joliet=self._joliet)
            if not nev or nev in (".", ".."):
                continue
            relativ = prefix / nev
            if jelzok & 0x02:
                self._konyvtar(
                    cel_szektor, cel_meret, relativ, latott, melyseg + 1
                )
            else:
                bejegyzes = ISOFajl(
                    utvonal=relativ,
                    eltolás=cel_szektor * _SZEKTOR,
                    meret=cel_meret,
                )
                self._fajlok.setdefault(_kulcs(relativ), bejegyzes)

    def _beolvas(self) -> None:
        gyoker_szektor, gyoker_meret = self._kotetgyoker()
        self._konyvtar(
            gyoker_szektor, gyoker_meret, PurePosixPath(), set(), 0
        )


__all__ = ["ISOFajl", "ISOOlvaso"]
