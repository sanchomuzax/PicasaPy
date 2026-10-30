"""A mentésvezérlő bontása őrizze meg a régi API-t és Qt-felületet (#6271)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from PySide6.QtCore import QMetaMethod

from picasapy.app import backup_controller


_GYOKER = Path(__file__).resolve().parents[1]
_FORRAS = _GYOKER / "src" / "picasapy" / "app"
_MODULOK = (
    "backup_controller.py",
    "backup_controller_sets.py",
    "backup_controller_runs.py",
)

# A bontás előtti backup_controller.py látható, nem aláhúzással kezdődő nevei.
_REGI_NYILVANOS_NEVEK = {
    "BackgroundWorkerMixin",
    "BackupController",
    "CD",
    "DVD",
    "LemezkepTetel",
    "Path",
    "QObject",
    "QStandardPaths",
    "SZUROK",
    "Signal",
    "Slot",
    "TIPUSOK",
    "TIPUS_CD_DVD",
    "TIPUS_LEMEZ",
    "annotations",
    "datetime",
    "flat_key",
    "futtasd",
    "hasznalhato_kapacitas",
    "jegyezd_fel_a_futast",
    "jegyezd_fel_az_elmentettet",
    "keszlet_letrehozasa",
    "keszlet_modositasa",
    "keszlet_torlese",
    "keszletek",
    "lemezek_szama",
    "lemezkepekbe",
    "logging",
    "mappankent",
    "normalize_path",
    "open_index",
    "tervezd_meg",
    "threading",
    "timezone",
    "visszaallit",
}

# UTF-8 forrásszöveg-hash a dekorátortól a függvény záró soráig, LF
# sorvégre normalizált olvasással. Az AST csak a forrástartományt jelöli ki.
_EREDETI_FORRASHASH = {
    "__init__": "b77332f99485c54e39eaf44d16e10de6e965a453b166ffe9886dcac768cd289a",
    "keszletek": "065294d4dde0ee719d2491d09cafefc2a84d52c5fe23cf7e66339b04aca71d26",
    "lemezkepAlapHely": "e5b4df54f19573aed5b79ac4c5f9cea23e64a773842719f644ba4b1452e347fa",
    "ujKeszlet": "9bcfbcca521af65a82724d137b7009a7f42bd30db33722e4a01e3781ef12af97",
    "modositsdAKeszletet": "236f7579444857b458092555be736645b6a43927e218bfc6faf15d12a1606ded",
    "torisdAKeszletet": "c8e83f686a4407a1ed1e50a57488ace099b5547fa61a8c7cebbd8c77f3368f55",
    "_keszlet": "a84fef74a7a35088b6bdb2508ff8be1c2be485b3bd5b75c64a89fd100cf49f89",
    "_tervezd": "87b3f700fbb623748bef778bbe96df1d523bc46bad6042c09386d918c9601a29",
    "_jeloltek": "e479a4e7ca395c4def435c43b16b7bc018e6c9cbc0215503c7e9cea8a046b527",
    "_mentetlen_sorok": "40ecc043a25dc812e0d8c1941a8b98a677aefad7436083dee7635b2fc74e582b",
    "mentesKulcs": "6a0a40602f66b6aafd0cfb670a5dfa06c91ee8dcaef6b58e4cd2d6f09e03ec41",
    "mentetlenMappakLekerese": "61596d32d9c568cea86715c7fd50aacd194a1e623c4dbd02c39035f8f4da9ac3",
    "_mentetlen_hattereben": "dc0da78fa36cbe32fd90987ab0573f19a760ce1bc5c15d8f743372657e723692",
    "terv": "aef0e69ca7df3b58d7be29c1e6c52678e75cc5c7404e57b96f73a4bd3580b28e",
    "tervezdHattereben": "8adb5b3f0588649eef5192e3f63b8b48644da098c3298f7f8042112f301dbe91",
    "_terv_hattereben": "acfbc0a7611e8357fc4ff9359185cc7d0b33e6257b1454199954a3f90e911b29",
    "_mappalista": "653058451bd640b3c8fbdfca55d4e773074e16cd4136cbb32e2238ddbc91bdab",
    "futtasdMost": "5c9f89f48fdf8165d56004b321b6c50946416f93fececab5f75cadbba148ce6a",
    "futtasdLemezkepbe": "76a34add4f5791dd94b180bca92165202d2c1c6f0a2149371881aa9e0995663f",
    "_lemezkepek_hattereben": "3a0bc34e3282a689b00277af7db630b52f58c9cbc52afc13c86189ee7d6ee192",
    "szakitsdMeg": "3684222bed10b1674165a1a80c8d368439f8d5ae88263e49e2dbf622bd42d60d",
    "_futtatas_hattereben": "8dbbb1ec7b73bc7a0bcea38c39c4d2de97b28803b56233442485ddf29d4a5e41",
    "visszaallitastFuttat": "c2ad46cd3d17292969b4fdddda6de01c3eecdef55c3e8dac300246f767abe33f",
    "_visszaallitas_hattereben": "266b37a081443ee8807c19049363e21fc3d8d8525a14e6ad95bca970fceeba10",
}

_QT_TAGOK = {
    "methods": sorted([
        ("signal", "futasIndult", 1),
        ("signal", "futasKesz", 2),
        ("signal", "haladas", 2),
        ("signal", "hibatJelez", 1),
        ("signal", "keszletekValtoztak", 0),
        ("signal", "lemezkepekKeszek", 2),
        ("signal", "mentetlenMappakKeszek", 3),
        ("signal", "tervKeszult", 4),
        ("signal", "visszaallitasKesz", 2),
        ("slot", "futtasdLemezkepbe", 2),
        ("slot", "futtasdLemezkepbe", 3),
        ("slot", "futtasdMost", 1),
        ("slot", "futtasdMost", 2),
        ("slot", "keszletek", 0),
        ("slot", "lemezkepAlapHely", 0),
        ("slot", "mentesKulcs", 1),
        ("slot", "mentetlenMappakLekerese", 1),
        ("slot", "modositsdAKeszletet", 4),
        ("slot", "modositsdAKeszletet", 5),
        ("slot", "szakitsdMeg", 0),
        ("slot", "torisdAKeszletet", 1),
        ("slot", "tervezdHattereben", 3),
        ("slot", "ujKeszlet", 3),
        ("slot", "ujKeszlet", 4),
        ("slot", "visszaallitastFuttat", 2),
    ]),
    "properties": [],
}


def _forras_hash(forras: str, node: ast.AST) -> str:
    sorok = forras.splitlines(keepends=True)
    kezdet = min(
        [node.lineno, *(decorator.lineno for decorator in getattr(node, "decorator_list", []))]
    )
    reszlet = "".join(sorok[kezdet - 1 : node.end_lineno]).encode("utf-8")
    return hashlib.sha256(reszlet).hexdigest()


def _definicio_hashok() -> dict[str, str]:
    eredmeny = {}
    for fajlnev in _MODULOK:
        utvonal = _FORRAS / fajlnev
        if not utvonal.is_file():
            continue
        forras = utvonal.read_text(encoding="utf-8")  # CRLF → LF
        fa = ast.parse(forras, filename=str(utvonal))
        for osztaly in (n for n in fa.body if isinstance(n, ast.ClassDef)):
            for node in osztaly.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    assert node.name not in eredmeny, f"többszörös függvény: {node.name}"
                    eredmeny[node.name] = _forras_hash(forras, node)
    return eredmeny


def _qt_tagok() -> dict[str, list[tuple]]:
    mo = backup_controller.BackupController.staticMetaObject
    fajtak = {
        QMetaMethod.MethodType.Signal: "signal",
        QMetaMethod.MethodType.Slot: "slot",
        QMetaMethod.MethodType.Method: "method",
        QMetaMethod.MethodType.Constructor: "constructor",
    }
    methods = []
    for index in range(mo.methodOffset(), mo.methodCount()):
        method = mo.method(index)
        methods.append(
            (
                fajtak[method.methodType()],
                bytes(method.name()).decode("utf-8"),
                method.parameterCount(),
            )
        )
    properties = []
    for index in range(mo.propertyOffset(), mo.propertyCount()):
        prop = mo.property(index)
        notify = prop.notifySignal()
        properties.append(
            (
                bytes(prop.name()).decode("utf-8"),
                bytes(notify.name()).decode("utf-8") if notify.isValid() else None,
                prop.isConstant(),
            )
        )
    return {
        "methods": sorted(methods),
        "properties": sorted(properties),
    }


def test_a_regi_importutvonal_nevei_forrasa_es_qt_felulete_valtozatlan():
    aktualis_nevek = {nev for nev in vars(backup_controller) if not nev.startswith("_")}
    assert aktualis_nevek == _REGI_NYILVANOS_NEVEK, (
        "a backup_controller homlokzat nevei eltérnek: "
        f"hiányzik={sorted(_REGI_NYILVANOS_NEVEK - aktualis_nevek)}, "
        f"többlet={sorted(aktualis_nevek - _REGI_NYILVANOS_NEVEK)}"
    )

    hianyzo = [nev for nev in _MODULOK if not (_FORRAS / nev).is_file()]
    assert not hianyzo, f"hiányzó backup_controller-bontott modulok: {hianyzo}"
    hosszu = {
        nev: len((_FORRAS / nev).read_text(encoding="utf-8").splitlines())
        for nev in _MODULOK
        if len((_FORRAS / nev).read_text(encoding="utf-8").splitlines()) >= 400
    }
    assert not hosszu, f"400 soros vagy hosszabb backup_controller-modulok: {hosszu}"

    kapott_hashok = _definicio_hashok()
    assert kapott_hashok == _EREDETI_FORRASHASH, (
        "a bontás előtti függvényforrás hiányzik vagy megváltozott: "
        f"hiányzik/új={sorted(set(_EREDETI_FORRASHASH) ^ set(kapott_hashok))}; "
        "eltérő="
        f"{sorted(n for n in kapott_hashok.keys() & _EREDETI_FORRASHASH.keys() if kapott_hashok[n] != _EREDETI_FORRASHASH[n])}"
    )

    assert _qt_tagok() == _QT_TAGOK, "megváltozott a BackupController Qt-metaobjektum-felülete"
    assert backup_controller.BackupController.staticMetaObject.className() == "BackupController"
    assert backup_controller.BackupController._tervezd.__globals__ is vars(backup_controller)
    assert backup_controller.BackupController.lemezkepAlapHely.__globals__ is vars(backup_controller)
    assert backup_controller.BackupController._lemezkepek_hattereben.__globals__ is vars(backup_controller)
    assert backup_controller.BackupController._futtatas_hattereben.__globals__ is vars(backup_controller)

    mro_nevek = [osztaly.__name__ for osztaly in backup_controller.BackupController.__mro__]
    vart_sorrend = [
        "_BackupControllerSetsMixin",
        "_BackupControllerRunsMixin",
        "BackgroundWorkerMixin",
    ]
    helyek = [mro_nevek.index(nev) for nev in vart_sorrend]
    assert helyek == sorted(helyek), f"megváltozott a releváns mixinek sorrendje: {mro_nevek}"
