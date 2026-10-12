"""Képek és kísérő .picasa.ini fájlok visszaállítása mentési készletből."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import shutil
import xml.etree.ElementTree as ET

from picasapy.ini import ini_source_path
from picasapy.ini.names import INI_NAME, LEGACY_INI_NAME
from picasapy.scanner.filetypes import media_kind_of

from .iso_olvaso import ISOFajl, ISOOlvaso

_LELTAR_MAX = 16 * 1024 * 1024
_MEGENGEDETT_KEPFAJTAK = {"photo", "raw"}


@dataclass(frozen=True)
class VisszaallitasiEredmeny:
    """A művelet során helyreállított és kihagyott fájlok száma."""

    visszaallitott: int
    kihagyott: int


@dataclass(frozen=True)
class _ForrasFajl:
    relativ: PurePosixPath
    forras: Path | None = None
    iso: ISOOlvaso | None = None
    iso_fajl: ISOFajl | None = None

    def masol(self, cel: Path) -> None:
        if self.forras is not None:
            shutil.copy2(self.forras, cel)
        elif self.iso is not None and self.iso_fajl is not None:
            self.iso.masol(self.iso_fajl, cel)
        else:
            raise RuntimeError("A visszaállítandó fájl forrása hiányzik.")


def _relativ_ut(ertek: str, *, alias: bool = True) -> PurePosixPath | None:
    """A mentés útját célon belüli POSIX-úttá alakítja.

    A Windows-gyökér és a [P] lemezalias nem része a visszaállított
    könyvtárfának. A .. elemet elutasítjuk, nem próbáljuk normalizálni.
    """
    szoveg = str(ertek).strip().replace("\\", "/")
    if not szoveg:
        return None
    szoveg = re.sub(r"^[A-Za-z]:", "", szoveg).lstrip("/")
    reszek = [resz for resz in szoveg.split("/") if resz not in ("", ".")]
    if not reszek or any(resz == ".." for resz in reszek):
        return None
    if alias and reszek[0].casefold() == "[p]":
        reszek = reszek[1:]
    if not reszek or reszek[0].casefold() == "$application data":
        return None
    return PurePosixPath(*reszek)


def _kep_e(ut: PurePosixPath) -> bool:
    return media_kind_of(ut.name) in _MEGENGEDETT_KEPFAJTAK


def _leltar_utvonalak(szoveg: str) -> tuple[PurePosixPath, ...]:
    sorok = szoveg.lstrip("\ufeff").splitlines()
    utvonalak: list[PurePosixPath] = []
    i = 0
    while i < len(sorok):
        sor = sorok[i].rstrip("\r")
        i += 1
        if not sor or sor.startswith("#") or sor.startswith(("ft,", "hf,")):
            continue
        nyers_ut = sor.split("\t", 1)[0] if "\t" in sor else sor
        relativ = _relativ_ut(nyers_ut)
        if relativ is not None and _kep_e(relativ):
            utvonalak.append(relativ)
        # A Picasa files.txt tételszerkezete útvonal, felirat (akár üres),
        # majd opcionális ft,/hf, rekord. A PicasaPy-s sorok egytabos
        # rekordok, így azoknál nincs következő sor, amit át kellene ugrani.
        if "\t" not in sor and i < len(sorok):
            if not sorok[i].startswith(("#", "ft,", "hf,")):
                i += 1
        while i < len(sorok) and sorok[i].startswith(("ft,", "hf,")):
            i += 1
    return tuple(utvonalak)


def _manifeszt_utvonalak(adat: bytes) -> tuple[PurePosixPath, ...]:
    try:
        gyoker = ET.fromstring(adat)
    except ET.ParseError as hiba:
        raise ValueError("A PicasaManifest.xml sérült.") from hiba
    utvonalak: list[PurePosixPath] = []
    for fajl_lista in gyoker.findall("./files"):
        for tetel in fajl_lista.findall("./file"):
            visszaallitando = tetel.get("shouldRestore", "YES").upper()
            if visszaallitando in {"NO", "FALSE"}:
                continue
            ut = tetel.findtext("./path")
            if not ut:
                continue
            relativ = _relativ_ut(ut)
            if relativ is not None and _kep_e(relativ):
                utvonalak.append(relativ)
    return tuple(utvonalak)


def _mappafajlok(gyoker: Path) -> dict[str, Path]:
    eredmeny: dict[str, Path] = {}
    for fajl in gyoker.rglob("*"):
        if not fajl.is_file() or fajl.is_symlink():
            continue
        relativ = fajl.relative_to(gyoker).as_posix()
        eredmeny.setdefault(relativ.casefold(), fajl)
    return eredmeny


def _mappabol(gyoker: Path) -> list[_ForrasFajl]:
    fajlok = _mappafajlok(gyoker)
    manifest_xml = gyoker / "PicasaManifest.xml"
    files_txt = gyoker / "files.txt"
    if manifest_xml.is_file():
        if manifest_xml.stat().st_size > _LELTAR_MAX:
            raise ValueError("A PicasaManifest.xml túl nagy.")
        utvonalak = _manifeszt_utvonalak(manifest_xml.read_bytes())
    elif files_txt.is_file():
        if files_txt.stat().st_size > _LELTAR_MAX:
            raise ValueError("A files.txt túl nagy.")
        utvonalak = _leltar_utvonalak(
            files_txt.read_text(encoding="utf-8-sig", errors="replace")
        )
    else:
        utvonalak = tuple(
            relativ
            for ut in fajlok
            if _kep_e(PurePosixPath(ut))
            for relativ in [_relativ_ut(ut)]
            if relativ is not None
        )
    kivalasztott: dict[str, _ForrasFajl] = {}
    for relativ in utvonalak:
        kulcs = relativ.as_posix().casefold()
        forras = fajlok.get(kulcs)
        if forras is None:
            forras = fajlok.get(f"[p]/{kulcs}")
        if forras is None:
            # Régi Picasa-leltárban lehet meghajtóval kezdődő út. A
            # mentés könyvtárának relatív fáját a név egyértelműen oldja fel.
            nev = relativ.name.casefold()
            egyezesek = [
                ut for ut in fajlok.values()
                if ut.name.casefold() == nev and _kep_e(PurePosixPath(ut.name))
            ]
            if len(egyezesek) == 1:
                forras = egyezesek[0]
                relativ = PurePosixPath(forras.relative_to(gyoker).as_posix())
                kulcs = relativ.as_posix().casefold()
        if forras is not None:
            kivalasztott.setdefault(
                kulcs, _ForrasFajl(relativ=relativ, forras=forras)
            )
    _ini_tarsak_mappabol(kivalasztott, fajlok)
    return list(kivalasztott.values())


def _ini_tarsak_mappabol(
    tetelek: dict[str, _ForrasFajl],
    fajlok: dict[str, Path],
) -> None:
    kepek = tuple(t for t in tetelek.values() if _kep_e(t.relativ))
    for kep in kepek:
        if kep.forras is None:
            continue
        ini = ini_source_path(kep.forras.parent / INI_NAME)
        if ini is None:
            ini = _ini_kisbetuvel(fajlok, kep.forras.parent)
        if ini is None:
            continue
        relativ = kep.relativ.parent / ini.name
        kulcs = relativ.as_posix().casefold()
        tetelek.setdefault(kulcs, _ForrasFajl(relativ=relativ, forras=ini))


def _ini_kisbetuvel(fajlok: dict[str, Path], mappa: Path) -> Path | None:
    """Tartalék: más betűzésű ini (pl. `.PICASA.INI`) a mentés térképében."""
    for nev in (INI_NAME, LEGACY_INI_NAME):
        for ut in fajlok.values():
            if ut.parent == mappa and ut.name.casefold() == nev.casefold():
                return ut
    return None


def _ini_fajl_az_isoban(
    bejaras: ISOOlvaso, mappa: PurePosixPath
) -> tuple[PurePosixPath, ISOFajl] | None:
    """A modern, majd a legacy ini az ISO-ban; a találat neve megmarad.

    Az ISO olvasó virtuális útvonalakat ad, ezért itt a fájlrendszeri
    `ini_source_path` helyett ugyanazt a név- és elsőbbségi sorrendet
    alkalmazzuk közvetlenül a lemezkép bejegyzéseire.
    """
    for nev in (INI_NAME, LEGACY_INI_NAME):
        relativ = mappa / nev
        fajl = _iso_utvonal(bejaras, relativ)
        if fajl is not None:
            return relativ, fajl
    return None


def _iso_szett(kep: Path) -> tuple[Path, ...]:
    minta = re.fullmatch(r"(.*?)[-_ ](\d+)", kep.stem)
    if not minta:
        return (kep,)
    prefix = minta.group(1)
    testverek = []
    for ut in kep.parent.iterdir():
        if not ut.is_file() or ut.suffix.casefold() != ".iso":
            continue
        masik = re.fullmatch(r"(.*?)[-_ ](\d+)", ut.stem)
        if masik and masik.group(1).casefold() == prefix.casefold():
            testverek.append((int(masik.group(2)), ut))
    return tuple(ut for _sorszam, ut in sorted(testverek)) or (kep,)


def _iso_utvonal(bejaras: ISOOlvaso, ut: PurePosixPath) -> ISOFajl | None:
    jeloltek = (ut, PurePosixPath("[P]") / ut)
    for jelolt in jeloltek:
        fajl = bejaras.fajl(jelolt)
        if fajl is not None:
            return fajl
    return None


def _isobol(kep: Path) -> list[_ForrasFajl]:
    talalatok: dict[str, _ForrasFajl] = {}
    for iso_ut in _iso_szett(kep):
        bejaras = ISOOlvaso(iso_ut)
        lemez_tetelek: dict[str, _ForrasFajl] = {}
        xml_fajl = bejaras.fajl("PicasaManifest.xml")
        files_fajl = bejaras.fajl("files.txt")
        if xml_fajl is not None:
            utvonalak = _manifeszt_utvonalak(
                bejaras.olvas_bajtokat(xml_fajl, max_meret=_LELTAR_MAX)
            )
        elif files_fajl is not None:
            utvonalak = _leltar_utvonalak(
                bejaras.olvas_bajtokat(files_fajl, max_meret=_LELTAR_MAX)
                .decode("utf-8-sig", errors="replace")
            )
        else:
            utvonalak = tuple(
                fajl.utvonal for fajl in bejaras.fajlok() if _kep_e(fajl.utvonal)
            )
        for relativ in utvonalak:
            forras = _iso_utvonal(bejaras, relativ)
            if forras is not None:
                lemez_tetelek.setdefault(
                    relativ.as_posix().casefold(),
                    _ForrasFajl(relativ=relativ, iso=bejaras, iso_fajl=forras),
                )
        kepek = tuple(t for t in lemez_tetelek.values() if _kep_e(t.relativ))
        for photo in kepek:
            talalat = _ini_fajl_az_isoban(bejaras, photo.relativ.parent)
            if talalat is not None:
                relativ, sidecar = talalat
                lemez_tetelek.setdefault(
                    relativ.as_posix().casefold(),
                    _ForrasFajl(relativ=relativ, iso=bejaras, iso_fajl=sidecar),
                )
        for kulcs, tetel in lemez_tetelek.items():
            talalatok.setdefault(kulcs, tetel)
    return list(talalatok.values())


def _cel_ut(cel_gyoker: Path, relativ: PurePosixPath) -> Path:
    if relativ.is_absolute() or any(
        resz in ("", ".", "..") for resz in relativ.parts
    ):
        raise ValueError(f"Nem biztonságos mentési útvonal: {relativ}")
    cel = cel_gyoker.joinpath(*relativ.parts)
    gyoker = cel_gyoker.resolve()
    if not cel.resolve(strict=False).is_relative_to(gyoker):
        raise ValueError(
            f"A célfájl kilépne a visszaállítási mappából: {relativ}"
        )
    return cel


def _forrasfajlok(forras: Path) -> list[_ForrasFajl]:
    if forras.is_dir():
        if (forras / "files.txt").is_file() or (
            forras / "PicasaManifest.xml"
        ).is_file():
            return _mappabol(forras)
        iso_fajlok = sorted(
            ut for ut in forras.iterdir()
            if ut.is_file() and ut.suffix.casefold() == ".iso"
        )
        if iso_fajlok:
            talalatok: list[_ForrasFajl] = []
            apolt: set[Path] = set()
            for iso in iso_fajlok:
                sorozat = _iso_szett(iso)
                if any(ut.resolve() in apolt for ut in sorozat):
                    continue
                talalatok.extend(_isobol(iso))
                apolt.update(ut.resolve() for ut in sorozat)
            return talalatok
        return _mappabol(forras)
    if forras.is_file() and forras.suffix.casefold() == ".iso":
        return _isobol(forras)
    raise ValueError("Válasszon mentési mappát vagy ISO-lemezképet.")


def visszaallit(forras: Path, cel: Path) -> VisszaallitasiEredmeny:
    """Képeket és .picasa.ini társaikat állít vissza egy választott mappába.

    A mappás PicasaPy-leltárt, a Picasa files.txt-t és a lemezkép
    PicasaManifest.xml-jét olvassa. Többlemezes sorozatnál a kiválasztott
    *-01.iso kép az azonos előtagú ISO-készletet nyitja meg. Létező célfájlt
    nem ír felül.
    """
    forras = Path(forras)
    cel = Path(cel)
    tetelek = _forrasfajlok(forras)
    if not tetelek:
        raise ValueError("A mentésben nem található visszaállítható kép.")
    cel.mkdir(parents=True, exist_ok=True)
    visszaallitott = kihagyott = 0
    for tetel in tetelek:
        cel_fajl = _cel_ut(cel, tetel.relativ)
        if cel_fajl.exists() or (
            tetel.relativ.name == LEGACY_INI_NAME
            and cel_fajl.with_name(INI_NAME).exists()
        ):
            kihagyott += 1
            continue
        cel_fajl.parent.mkdir(parents=True, exist_ok=True)
        tetel.masol(cel_fajl)
        visszaallitott += 1
    return VisszaallitasiEredmeny(visszaallitott, kihagyott)


__all__ = ["VisszaallitasiEredmeny", "visszaallit"]
