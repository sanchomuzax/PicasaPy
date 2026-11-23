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
# #7244: a nézőnyitáskor a finomhangolás tulajdonságai célzott értesítést
# használnak, az üres lánc LUT-ja pedig render-import nélkül készül.
_EREDETI_FORRAS_SHA256 = {
    "method:recentPickerColors": "b1bcf67dea13e23b94ef9a37bd62cad42bf99d86d3bcf46dad8e47e30e4e64c2",
    "method:rememberPickerColor": "d450bef209234c18688c4455135765a27b076b788a561c021c3898c0db492830",
    "method:legacyEffects": "dfec1470ee19110222fc59333399a17cbf4cd078a77bcd8472b1dbae326dee8d",
    "method:legacyEffectsInChain": "cc0639ab2d70b2072e7b6b5f7caec66bcc2a8d9f8c2bb80fd5b77ef074db40a2",
    "method:oneClickEffects": "ff20a3b8265f1a950b534946d36d8933316530f3eaeb621d2e27d57136b783a2",
    "method:effectChainCounts": "3649c49fa0ac17cc1a74a621d3e78e327d397648a15b7e3163ce82b23db0738f",
    "method:effectChain": "71647ebd0d25209f9ab8bbf9f2e6d857f96434edf7685740a214e0f1e21c4b09",
    "method:enhanceEnabled": "05c96197115ad1f7bff04c2b907e21dbc9d880ba08111067479ef66244555ca5",
    "method:autolightEnabled": "b763c707983e1322cb80a8d896f17e9a0d756610ca4779402e592b54a051094b",
    "method:autocolorEnabled": "da0d9a935df126b1d4cfbf2198b7c2ad7b6874cfbde3fca93eb6f5aa84739ecf",
    "method:tiltParam": "7e1bef898e69dde9dad1630a360089cede2e133726501b3b53c2c69ba2fce365",
    "method:fillLight": "ed988744d8fd4b2fb671864fbab3038ec1cb8cc1b79810682309a0b735abb10e",
    # #7369: a Gyakori javítások Derítőfénye külön `fill` réteg (a `finetune2`-től független)
    "method:fixesFillLight": "4baed149da6d233ef5a706f7fd0aab6e20d170f37df73a0d5e8a10fe5c3097c5",
    "method:previewFixesFill": "5b1d112aa385dbe1f3085d9ed9fb7a96fd5cb74a11500f640148a8180f2e8799",
    "method:setFixesFill": "376a50db5918f564fa647fee0c53f05aec179dcac1a66148cbfe5a3e351058d1",
    "method:_session_with_fill": "3ce319b623cb4dde7e5fe580e813945c6be5a719ee0b7054f976c20c63444ddb",
    "method:highlights": "10daf37e5d133de924ac0e7d386c0887120582eb880cb6e9046479e39e91957f",
    "method:shadows": "87b72d5c09e4daeea2562d8e060e453dcd8293dcafd76e832a32e0516492db7b",
    "method:colorTemp": "c190cffd835daadf8e5cc9519d497bec5c27717fcecb0aad9c9a9115e7f29813",
    "method:neutralColor": "34fcbc16b64cab4c180cc40ce1c53a159c441f6dce6fb14aa317ab7fd90509eb",
    "method:hasFinetune": "a1ae4e36ce02307c4f7d99c6b9b0992b106da8f07a2963fc7504727136ffdfdf",
    "method:setTilt": "9599a9d657f3d5fd6401d67f6d116cc1b6f138477596ae8a12b92be5bb505254",
    "method:previewTilt": "3ffe40fa6bd7583c71fd5c84036c1ef43dadb53089603b1056cf90e4b8ddc287",
    "method:discardTiltPreview": "9e5f4ce898d96640cff35de190c46d9a9d311d9d9e9b6e2798b3d180425a78aa",
    "method:previewFinetune": "f18330782af266eaebb44aa0cde3c43033c4f1fe40a73738b9d14ffecbbc4604",
    "method:previewFinetuneGpu": "fc7728438ca1b543ca6932e4b61e8eeeca3b751623034fa9658d518ba5653528",
    "method:setFinetune": "3117e12d363f402881570a6c3180662f8274768627b38e5990f36e8ca33f26f6",
    "method:applyEffect": "98af0d726e268e41b042b6e1963bfc35c9a95d1add2f80e631c7ed2b5c212c27",
    "method:effectHasParams": "093e48a706f64a6902a858cb22229e08abb2add1621c1a94bc1f487ad5534a7d",
    "method:effectParams": "7d399177dc974d6ec3e7c0008ae908b63a5169708c8ec47ddb254c4f42611a66",
    # #6685: a revision csak a háttér-render elkészültekor lép, nem azonnal.
    "method:previewEffect": "c973db81f4f615e3abf64e4243c202a112ee745168451223d5c8a30788ca4c9e",
    "method:discardEffectPreview": "024721e1a7fe86b0f1ab0b2899e6573c0825f2563ef9e297c3afa24babee6cc1",
    "method:applyEffectWithParams": "ded91fbb793684be76859b96d1ae53bdbf98563a51b0b2e686feb8da1af32552",
    "method:_session_with_effect": "b464866f2c399980312a8784e00a113933a3bbe907629dd28b7de1044a46918e",
    "method:_finetune_field": "79728f2475a5a708354fcac8a92144d6c0694ca6c72f30c1fed51778edfa1a1d",
    "method:pickNeutralColor": "2d88180fa236c4d687c98f11dfcac34b0f7bf7fc09d08e2cf2f1d1e326353447",
    "method:pickEffectColor": "9bc9106f540a20fb9223155e3d2471ad94561caccc3c77f2bd444b349a19ea52",
    "method:figyeldAShiftet": "43741eeb4fbedcddeb9d872b43224b390c9ccb6589834db9451ec3be10227561",
    "method:_allitsd_a_shiftet": "9a38ce944af8830ccd6deb106628ca92a00eef74845ca2d0538d8196d38746a7",
    "method:shiftAktiv": "5ff73952e946c6ccb49eff1afb96cecd134bcd47dd198ba2b8d1f8e2e21ccdaa",
    "method:shiftLenyomva": "a30294d1954188418f2d107f5e247e307989a6e2f3a844af021e4328bbf32f80",
    "method:applyColorWand": "974f2269fb4bed0762c408f3b9e1cab2375b6edaf47f324051d060f450ac477f",
    "method:_gpu_lut_for": "efef115f57051dc80c058c28ecbfa219b2f48b405fc68d023e47f3048d47c383",
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
    "M|previewFixesFill|1",
    "M|previewTilt|1",
    "M|rememberPickerColor|1",
    "M|setFinetune|4",
    "M|setFixesFill|1",
    "M|setTilt|1",
    "M|shiftLenyomva|0",
    "P|autocolorEnabled|autocolorEnabledChanged|False",
    "P|autolightEnabled|autolightEnabledChanged|False",
    "P|colorTemp|colorTempChanged|False",
    "P|effectChainCounts|revisionChanged|False",
    "P|effectChain|revisionChanged|False",
    "P|enhanceEnabled|enhanceEnabledChanged|False",
    "P|fillLight|fillLightChanged|False",
    "P|fixesFillLight|fixesFillLightChanged|False",
    "P|hasFinetune|hasFinetuneChanged|False",
    "P|highlights|highlightsChanged|False",
    "P|legacyEffectsInChain|revisionChanged|False",
    "P|legacyEffects||True",
    "P|neutralColor|neutralColorChanged|False",
    "P|oneClickEffects||True",
    "P|recentPickerColors|pickerRecentColorsChanged|False",
    "P|shadows|shadowsChanged|False",
    "P|shiftAktiv|shiftAktivChanged|False",
    "P|tiltParam|tiltParamChanged|False",
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
