"""A szerkesztő effektmixinjének bontása őrizze meg a régi útvonalat, a forrást
és a Qt-felületet (#6267)."""

from __future__ import annotations

import ast
import hashlib
import importlib
from pathlib import Path

from PySide6.QtCore import QMetaMethod

from picasapy.app import edit_controller_effects_mixin as homlokzat
from picasapy.app.edit_controller import EditController
from picasapy.app.edit_controller_signals import EditControllerSignalsMixin

_GYOKER = Path(__file__).resolve().parents[1]
_APP = _GYOKER / "src" / "picasapy" / "app"
_HOMLOKZAT = "edit_controller_effects_mixin"

# A bontás utáni mixinek, az MRO-ban a homlokzat után, ebben a sorrendben.
_UJ_MIXINEK = (
    ("edit_controller_effects_state_mixin", "EditControllerEffectsStateMixin"),
    ("edit_controller_effects_finetune_mixin", "EditControllerEffectsFinetuneMixin"),
    ("edit_controller_effects_params_mixin", "EditControllerEffectsParamsMixin"),
    ("edit_controller_effects_color_mixin", "EditControllerEffectsColorMixin"),
    ("edit_controller_effects_shift_mixin", "EditControllerEffectsShiftMixin"),
)

# A #6267 előtti edit_controller_effects_mixin.py nyilvános nevei.
_REGI_NYILVANOS_NEVEK = {
    "DEAD_LEGACY_OPS",
    "EditControllerEffectsMixin",
    "EditSession",
    "LEGACY_EFFECTS",
    "LEGACY_EFFECT_KEYS",
    "Property",
    "QCoreApplication",
    "QGuiApplication",
    "Slot",
    "build_finetune2_lut",
    "can_offer_filter_control",
    "estimate_neutral_color",
    "format_param_values",
    "gyors_elonezet",
    "has_params",
    "np",
    "one_click_keys",
    "parse_neutral_argb",
    "resolve_effect_params",
}

# A #6267 előtti osztálytörzs függvényeinek forrásszöveg-lenyomata (a dekorátortól
# a záró sorig). Az ast.dump Python-verziónként eltér, a forrás szövege nem.
_EREDETI_FORRAS_SHA256 = {
    "method:recentPickerColors": "b1bcf67dea13e23b94ef9a37bd62cad42bf99d86d3bcf46dad8e47e30e4e64c2",
    "method:rememberPickerColor": "d450bef209234c18688c4455135765a27b076b788a561c021c3898c0db492830",
    "method:legacyEffects": "dfec1470ee19110222fc59333399a17cbf4cd078a77bcd8472b1dbae326dee8d",
    "method:legacyEffectsInChain": "cc0639ab2d70b2072e7b6b5f7caec66bcc2a8d9f8c2bb80fd5b77ef074db40a2",
    "method:oneClickEffects": "ff20a3b8265f1a950b534946d36d8933316530f3eaeb621d2e27d57136b783a2",
    "method:effectChainCounts": "3649c49fa0ac17cc1a74a621d3e78e327d397648a15b7e3163ce82b23db0738f",
    "method:effectChain": "71647ebd0d25209f9ab8bbf9f2e6d857f96434edf7685740a214e0f1e21c4b09",
    "method:enhanceEnabled": "2171f872ee9b4ff7032ef53b462bcf3f912187e54642257b5a67912aa3f27ce0",
    "method:autolightEnabled": "aa1db352984797e86d3d82108162ebd94d03c533a56b1070ac753332ab22e85a",
    "method:autocolorEnabled": "026addd531629d2978aab2d6f9f8456f7fde1ee12805f653d0a105ae1f2e90d0",
    "method:tiltParam": "99f8da3c11b94fa9bab53733905dacc7ed6402b17662e8d49d7c072c5a92bef8",
    "method:fillLight": "94aaf55f38a43bf6940c4a3b01ffe91222b911e39c24b0b83fa1a73154b090ca",
    "method:highlights": "3ce75f04972af3dfb998a0cf313eafe19e89e0bc57f4d09775e679701504d410",
    "method:shadows": "b25a904a760988a5130f379027407b565f30676c3643f0aaabe4e208e867f72f",
    "method:colorTemp": "e5bf5128bd5ab3aa73c8a4622e07ad2c307f0cfb17cdf15998f0ac8b5154d6d8",
    "method:neutralColor": "c941d4fbd41aa30031513d6d291ea9623b64d92e7db9d0761a6cb7624128e1ef",
    "method:hasFinetune": "eadccf1596cb8b94c7d123fe59b2a6302706adbc4c0ce04de38056ef76ded70a",
    "method:setTilt": "9599a9d657f3d5fd6401d67f6d116cc1b6f138477596ae8a12b92be5bb505254",
    "method:previewTilt": "3ffe40fa6bd7583c71fd5c84036c1ef43dadb53089603b1056cf90e4b8ddc287",
    "method:discardTiltPreview": "9e5f4ce898d96640cff35de190c46d9a9d311d9d9e9b6e2798b3d180425a78aa",
    "method:previewFinetune": "823e9a0417f79b775821a34fd72d983d66dc94b89d1eaafd283e61d896871b66",
    "method:previewFinetuneGpu": "06834f26e3b2c5670ca11b9aebdd1ead5b799da1c2246b6bad603b73f810b545",
    "method:setFinetune": "06ae37daf24fbcefe6e9c495599bbe2a00001058b9bb739b2845ca21345cbf42",
    "method:applyEffect": "98af0d726e268e41b042b6e1963bfc35c9a95d1add2f80e631c7ed2b5c212c27",
    "method:effectHasParams": "093e48a706f64a6902a858cb22229e08abb2add1621c1a94bc1f487ad5534a7d",
    "method:effectParams": "7d399177dc974d6ec3e7c0008ae908b63a5169708c8ec47ddb254c4f42611a66",
    "method:previewEffect": "adf7c5bb25ddfa2d3f44a30b96b75ecb4eabb55b26c83ee86afa499263e6c46c",
    "method:discardEffectPreview": "024721e1a7fe86b0f1ab0b2899e6573c0825f2563ef9e297c3afa24babee6cc1",
    "method:applyEffectWithParams": "ded91fbb793684be76859b96d1ae53bdbf98563a51b0b2e686feb8da1af32552",
    "method:_session_with_effect": "b464866f2c399980312a8784e00a113933a3bbe907629dd28b7de1044a46918e",
    "method:_finetune_field": "56ba0746a9ca79a32dcea21d9b3f891f68dc47b1f8b04940383037925e7a19a7",
    "method:pickNeutralColor": "edffc637ad52366e6be9f5d4d86a501590df1aa8041628d408a7640c0ecde94f",
    "method:pickEffectColor": "9bc9106f540a20fb9223155e3d2471ad94561caccc3c77f2bd444b349a19ea52",
    "method:figyeldAShiftet": "43741eeb4fbedcddeb9d872b43224b390c9ccb6589834db9451ec3be10227561",
    "method:_allitsd_a_shiftet": "9a38ce944af8830ccd6deb106628ca92a00eef74845ca2d0538d8196d38746a7",
    "method:shiftAktiv": "5ff73952e946c6ccb49eff1afb96cecd134bcd47dd198ba2b8d1f8e2e21ccdaa",
    "method:shiftLenyomva": "a30294d1954188418f2d107f5e247e307989a6e2f3a844af021e4328bbf32f80",
    "method:applyColorWand": "a59d633fb06240f5d973e8180aebd8f39c2dc246b65ca5773b896c6f6c2dc4ac",
    "method:_gpu_lut_for": "2126442e75f76822ff903eb4bc0d56dde56b7f4dbe61f071a35c1c0ab8442f12",
}

# A #6267 előtti Qt-lenyomat, csak a mixincsalád saját tagjai. Szándékosan nincs
# benne a típusnév és az isWritable, mert PySide-verziónként eltér.
_EREDETI_QT_LENYOMAT = [
    "M|applyColorWand|0",
    "M|applyEffectWithParams|2",
    "M|applyEffect|1",
    "M|discardEffectPreview|0",
    "M|discardTiltPreview|0",
    "M|effectHasParams|1",
    "M|effectParams|1",
    "M|figyeldAShiftet|1",
    "M|pickEffectColor|2",
    "M|pickNeutralColor|2",
    "M|previewEffect|2",
    "M|previewFinetuneGpu|4",
    "M|previewFinetune|4",
    "M|previewTilt|1",
    "M|rememberPickerColor|1",
    "M|setFinetune|4",
    "M|setTilt|1",
    "M|shiftLenyomva|0",
    "P|autocolorEnabled|toolsChanged|False",
    "P|autolightEnabled|toolsChanged|False",
    "P|colorTemp|toolsChanged|False",
    "P|effectChainCounts|revisionChanged|False",
    "P|effectChain|revisionChanged|False",
    "P|enhanceEnabled|toolsChanged|False",
    "P|fillLight|toolsChanged|False",
    "P|hasFinetune|toolsChanged|False",
    "P|highlights|toolsChanged|False",
    "P|legacyEffectsInChain|revisionChanged|False",
    "P|legacyEffects||True",
    "P|neutralColor|toolsChanged|False",
    "P|oneClickEffects||True",
    "P|recentPickerColors|pickerRecentColorsChanged|False",
    "P|shadows|toolsChanged|False",
    "P|shiftAktiv|shiftAktivChanged|False",
    "P|tiltParam|toolsChanged|False",
]


def _osztaly(modul: str, nev: str) -> type:
    return getattr(importlib.import_module(f"picasapy.app.{modul}"), nev)


def _csalad() -> list[type]:
    return [
        homlokzat.EditControllerEffectsMixin,
        *(_osztaly(modul, nev) for modul, nev in _UJ_MIXINEK),
    ]


def _csalad_fajlok() -> tuple[Path, ...]:
    return (
        _APP / f"{_HOMLOKZAT}.py",
        *(_APP / f"{modul}.py" for modul, _ in _UJ_MIXINEK),
    )


def _lenyomat(forras: bytes, node: ast.AST) -> str:
    sorok = forras.splitlines(keepends=True)
    kezdo = min([node.lineno, *(dekorator.lineno for dekorator in node.decorator_list)])
    return hashlib.sha256(b"".join(sorok[kezdo - 1 : node.end_lineno])).hexdigest()


def _forraslenyomatok() -> dict[str, str]:
    eredmeny: dict[str, str] = {}
    for fajl in _csalad_fajlok():
        # windowsos checkout: CRLF, ezért LF-re normalizálunk (#6260)
        forras = fajl.read_bytes().replace(b"\r\n", b"\n")
        fa = ast.parse(forras.decode("utf-8"), filename=str(fajl))
        for osztaly in fa.body:
            if not isinstance(osztaly, ast.ClassDef):
                continue
            for tag in osztaly.body:
                if isinstance(tag, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kulcs = f"method:{tag.name}"
                    assert kulcs not in eredmeny, f"többszörös definíció: {kulcs}"
                    eredmeny[kulcs] = _lenyomat(forras, tag)
    return eredmeny


def _szoveg(ertek: object) -> str:
    return ertek if isinstance(ertek, str) else bytes(ertek).decode()


def _qt_lenyomat() -> list[str]:
    nevek = {nev for osztaly in _csalad() for nev in vars(osztaly)}
    meta = EditController.staticMetaObject
    lenyomat: list[str] = []
    for index in range(meta.methodCount()):
        metodus = meta.method(index)
        nev = _szoveg(metodus.name())
        if nev in nevek and metodus.methodType() == QMetaMethod.MethodType.Slot:
            lenyomat.append(f"M|{nev}|{metodus.parameterCount()}")
    for index in range(meta.propertyCount()):
        tulajdonsag = meta.property(index)
        nev = _szoveg(tulajdonsag.name())
        if nev in nevek:
            jelzes = ""
            if tulajdonsag.hasNotifySignal():
                jelzes = _szoveg(tulajdonsag.notifySignal().name())
            lenyomat.append(f"P|{nev}|{jelzes}|{tulajdonsag.isConstant()}")
    return sorted(lenyomat)


def test_a_bontott_modulok_leteznek_es_400_sor_alatt_maradnak() -> None:
    hianyzik = [fajl.name for fajl in _csalad_fajlok() if not fajl.is_file()]
    assert not hianyzik, f"hiányzó bontott modul(ok): {hianyzik}"

    for fajl in _csalad_fajlok()[1:]:
        sorok = len(fajl.read_text(encoding="utf-8").splitlines())
        assert sorok < 400, f"{fajl.name} elérte a 400 soros határt: {sorok}"


def test_a_bontott_metodusok_forrasszovege_bajtra_azonos() -> None:
    aktualis = _forraslenyomatok()
    assert aktualis == _EREDETI_FORRAS_SHA256, (
        "a metódusok forrásszövege megváltozott vagy hiányzik: "
        f"hiány/többlet={sorted(set(aktualis) ^ set(_EREDETI_FORRAS_SHA256))}; "
        "eltérő hash="
        f"{sorted(k for k in aktualis.keys() & _EREDETI_FORRAS_SHA256.keys() if aktualis[k] != _EREDETI_FORRAS_SHA256[k])}"
    )


def test_a_homlokzat_megtartja_a_regi_nyilvanos_neveket() -> None:
    hianyzik = sorted(nev for nev in _REGI_NYILVANOS_NEVEK if not hasattr(homlokzat, nev))
    assert not hianyzik, f"hiányzó régi név a homlokzaton: {hianyzik}"


def test_az_effektmixin_qt_felulete_valtozatlan() -> None:
    aktualis = _qt_lenyomat()
    assert aktualis == _EREDETI_QT_LENYOMAT, (
        f"hiány={sorted(set(_EREDETI_QT_LENYOMAT) - set(aktualis))}; "
        f"többlet={sorted(set(aktualis) - set(_EREDETI_QT_LENYOMAT))}"
    )


def test_az_uj_mixinek_a_homlokzat_utan_allnak_az_mro_ban() -> None:
    uj = tuple(_osztaly(modul, nev) for modul, nev in _UJ_MIXINEK)
    assert homlokzat.EditControllerEffectsMixin.__bases__ == uj

    mro = EditController.__mro__
    index = mro.index(homlokzat.EditControllerEffectsMixin)
    assert mro[index + 1 : index + 1 + len(uj)] == uj
    assert mro[index + 1 + len(uj)] is EditControllerSignalsMixin
