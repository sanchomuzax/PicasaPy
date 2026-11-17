"""#7153: a mappa átnevezése Windowson hozzáférési hibánál újrapróbál.

Az eredeti `0x00994400` a `MoveFileExW` 5-ös hibakódjánál (hozzáférés
megtagadva), ha a forrás létezik, 500 ezredmásodpercenként újrapróbálja a
műveletet, legfeljebb 5 másodpercig. Az első hiba után a ciklus bármely nem
nulla hibakódra folytatódik az időkorlátig.

A tesztek a modul fogantyúit cserélik (`_rename`, `_platform`, `_sleep`,
`_monotonic`), tehát valódi várakozás nincs, és a Windows-ág Linuxon is
mérhető. A MÉRT dolog: a próbálkozások száma, a várakozások listája és a
szimulált óra állása. Nem mér valódi Windows-hibakódot és valódi zárolt
mappát.
"""

from __future__ import annotations

import importlib
import os

import pytest

from picasapy.fileops import FolderRenameError, rename_folder

_modul = importlib.import_module("picasapy.fileops.rename_folder")

_HIBA_UZENET_ELEJE = "A mappa átnevezése nem sikerült: "


def _mappa(root, name="nyaralas"):
    folder = root / name
    (folder / "alalbum").mkdir(parents=True)
    (folder / "a.jpg").write_bytes(b"kep")
    return folder


def _hozzaferes(winerror=5):
    """A Windows `PermissionError`-ja; Linuxon a `winerror` kézzel kerül rá."""
    hiba = PermissionError(13, "Hozzáférés megtagadva")
    hiba.winerror = winerror
    return hiba


class _Ora:
    """Szimulált óra: az alvás előreviszi, valódi idő nem telik."""

    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def ora(monkeypatch):
    ora = _Ora()
    monkeypatch.setattr(_modul, "_sleep", ora.sleep)
    monkeypatch.setattr(_modul, "_monotonic", ora.monotonic)
    return ora


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(_modul, "_platform", lambda: "win32")


def _forgatokonyv(monkeypatch, kimenetek):
    """A `_rename` fogantyú: hívásonként a lista soron következő kimenete.

    `None` = a valódi átnevezés lefut, kivétel = azt dobja. Ha a lista
    elfogy, az utolsó kimenet ismétlődik."""
    hivasok = []

    def rename(source, target):
        hivasok.append((source, target))
        kimenet = kimenetek[min(len(hivasok), len(kimenetek)) - 1]
        if kimenet is not None:
            raise kimenet
        os.rename(source, target)

    monkeypatch.setattr(_modul, "_rename", rename)
    return hivasok


def test_ket_hozzaferesi_hiba_utan_a_harmadik_probalkozas_atnevez(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    hivasok = _forgatokonyv(monkeypatch, [_hozzaferes(), _hozzaferes(), None])

    target = rename_folder(source, "uj-nev")

    assert target == tmp_path / "uj-nev"
    assert (target / "a.jpg").read_bytes() == b"kep"
    assert not source.exists()
    assert len(hivasok) == 3
    assert ora.sleeps == [0.5, 0.5]


def test_folyamatos_hibanal_5_masodperc_utan_a_regi_hibauzenet(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    hiba = _hozzaferes()
    hivasok = _forgatokonyv(monkeypatch, [hiba])

    with pytest.raises(FolderRenameError) as kivetel:
        rename_folder(source, "uj-nev")

    assert str(kivetel.value) == f"{_HIBA_UZENET_ELEJE}{hiba}"
    assert ora.sleeps == [0.5] * 10
    assert ora.now == 5.0
    # az első próba + tíz újrapróba, az 5 másodperces ablak végén megáll
    assert len(hivasok) == 11
    assert (source / "a.jpg").read_bytes() == b"kep"
    assert not (tmp_path / "uj-nev").exists()


def test_az_elso_hiba_utan_barmely_hibakodra_folytatodik_az_idokorlatig(
    tmp_path, windows, ora, monkeypatch
):
    """Az eredeti ciklusa az első (5-ös) hiba után nem nézi a kódot."""
    source = _mappa(tmp_path)
    foglalt = _hozzaferes(winerror=32)
    hivasok = _forgatokonyv(monkeypatch, [_hozzaferes(), foglalt])

    with pytest.raises(FolderRenameError) as kivetel:
        rename_folder(source, "uj-nev")

    assert str(kivetel.value) == f"{_HIBA_UZENET_ELEJE}{foglalt}"
    assert ora.now == 5.0
    assert len(hivasok) == 11


def test_az_elso_hiba_utani_mas_hibakod_utan_is_sikerulhet_az_atnevezes(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    hivasok = _forgatokonyv(
        monkeypatch,
        [_hozzaferes(), _hozzaferes(winerror=32), OSError(5, "I/O hiba"), None],
    )

    target = rename_folder(source, "uj-nev")

    assert target == tmp_path / "uj-nev"
    assert len(hivasok) == 4
    assert ora.sleeps == [0.5, 0.5, 0.5]


def test_nem_letezo_forrasnal_nincs_ujraprobalas(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    hivasok = []

    def rename(forras, cel):
        hivasok.append((forras, cel))
        os.rename(forras, tmp_path / "elvitt")  # a forrás a hiba előtt eltűnik
        raise _hozzaferes()

    monkeypatch.setattr(_modul, "_rename", rename)

    with pytest.raises(FolderRenameError, match="nem sikerült"):
        rename_folder(source, "uj-nev")

    assert len(hivasok) == 1
    assert ora.sleeps == []


@pytest.mark.parametrize(
    "hiba",
    [
        _hozzaferes(winerror=32),
        FileNotFoundError(2, "Nincs ilyen fájl"),
        OSError(5, "I/O hiba"),
        PermissionError(13, "Hozzáférés megtagadva"),
    ],
    ids=["32-es-hibakod", "nem-hozzaferesi-hiba", "altalanos-oserror", "winerror-nelkul"],
)
def test_az_elso_hiba_csak_az_5_os_hozzaferesi_hibanal_indit_ujraprobat(
    tmp_path, windows, ora, monkeypatch, hiba
):
    source = _mappa(tmp_path)
    hivasok = _forgatokonyv(monkeypatch, [hiba])

    with pytest.raises(FolderRenameError) as kivetel:
        rename_folder(source, "uj-nev")

    assert str(kivetel.value) == f"{_HIBA_UZENET_ELEJE}{hiba}"
    assert len(hivasok) == 1
    assert ora.sleeps == []
    assert source.is_dir()


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_nem_windowson_a_viselkedes_valtozatlan(
    tmp_path, ora, monkeypatch, platform
):
    monkeypatch.setattr(_modul, "_platform", lambda: platform)
    source = _mappa(tmp_path)
    hiba = _hozzaferes()
    hivasok = _forgatokonyv(monkeypatch, [hiba, None])

    with pytest.raises(FolderRenameError) as kivetel:
        rename_folder(source, "uj-nev")

    assert str(kivetel.value) == f"{_HIBA_UZENET_ELEJE}{hiba}"
    assert len(hivasok) == 1
    assert ora.sleeps == []
    assert source.is_dir()
    assert not (tmp_path / "uj-nev").exists()


def test_windowson_hiba_nelkul_nincs_varakozas(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    hivasok = _forgatokonyv(monkeypatch, [None])

    target = rename_folder(source, "uj-nev")

    assert target == tmp_path / "uj-nev"
    assert len(hivasok) == 1
    assert ora.sleeps == []


def test_a_kis_nagybetus_atnevezes_utja_nem_probal_ujra(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    hiba = _hozzaferes()
    hivasok = _forgatokonyv(monkeypatch, [hiba])

    with pytest.raises(FolderRenameError) as kivetel:
        rename_folder(source, "Nyaralas")

    assert str(kivetel.value) == f"{_HIBA_UZENET_ELEJE}{hiba}"
    assert len(hivasok) == 1
    assert ora.sleeps == []
    assert source.is_dir()


def test_a_kis_nagybetus_atnevezes_masodik_lepese_sem_probal_ujra(
    tmp_path, windows, ora, monkeypatch
):
    """A köztes névről a célra váltás hibája visszagördül, újrapróba nélkül."""
    source = _mappa(tmp_path)
    hiba = _hozzaferes()
    hivasok = _forgatokonyv(monkeypatch, [None, hiba, None])

    with pytest.raises(FolderRenameError) as kivetel:
        rename_folder(source, "Nyaralas")

    assert str(kivetel.value) == f"{_HIBA_UZENET_ELEJE}{hiba}"
    assert len(hivasok) == 3
    assert ora.sleeps == []
    assert (source / "a.jpg").read_bytes() == b"kep"


def test_a_kis_nagybetus_atnevezes_sikeres_utja_valtozatlan(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    hivasok = _forgatokonyv(monkeypatch, [None, None])

    target = rename_folder(source, "Nyaralas")

    assert target == tmp_path / "Nyaralas"
    assert (target / "a.jpg").read_bytes() == b"kep"
    assert len(hivasok) == 2
    assert ora.sleeps == []


def test_letezo_celmappat_windowson_is_elutasit_probalkozas_nelkul(
    tmp_path, windows, ora, monkeypatch
):
    source = _mappa(tmp_path)
    _mappa(tmp_path, "mar-foglalt")
    hivasok = _forgatokonyv(monkeypatch, [None])

    with pytest.raises(FolderRenameError, match="Ilyen nevű mappa már létezik"):
        rename_folder(source, "mar-foglalt")

    assert hivasok == []
    assert ora.sleeps == []
    assert (source / "a.jpg").read_bytes() == b"kep"
