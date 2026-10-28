"""A #6073 szerkezeti őre: a nyomtatási párbeszéd részei külön QML-fájlok."""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app


_QML_DIR = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_RESZEK = (
    "PrintSelectionPanel.qml",
    "PrintSettingsPanel.qml",
    "PrintPreviewPanel.qml",
    "PrintPrinterPanel.qml",
    "PrintFitPanel.qml",
    "PrintStatusPanel.qml",
    "PrintButtonRow.qml",
    "PrintReviewPanel.qml",
    "PrintRemoveAllDialog.qml",
)

_MEGŐRZENDŐ_OBJECT_NEVEK = {
    "printDialog",
    "printContentFlick",
    "printSelectionText",
    "printQualityModeRow",
    "printModeNormalRadio",
    "printModeOptimizedRadio",
    "printNoPrinterText",
    "printOptionsButton",
    "printOptionsTooltip",
    "printSizeBox",
    "printSizePresetRepeater",
    "printPresetFullPage",
    "printContactColumnsBox",
    "printCopiesMinusButton",
    "printCopiesText",
    "printCopiesPlusButton",
    "printPreviewBlock",
    "printPreviewImage",
    "printPreviewPrevButton",
    "printPreviewPageText",
    "printPreviewNextButton",
    "printQualityText",
    "printReviewButton",
    "printPrinterBox",
    "printPrinterSetupButton",
    "printPaperInfoText",
    "printPdfTargetText",
    "printPdfBrowseButton",
    "printFitRadio",
    "printFillRadio",
    "printOrientationBox",
    "printStatusFlick",
    "printSkippedText",
    "printErrorText",
    "printProgressText",
    "printResultText",
    "printHelpButton",
    "printStartButton",
    "printCloseButton",
    "printOptionsPanel",
    "printReviewPanel",
    "printReviewWarningText",
    "printReviewList",
    "printReviewListRow",
    "printReviewListRowText",
    "printReviewEmptyText",
    "printReviewRemoveSelectedButton",
    "printReviewRemoveLowButton",
    "printReviewAcceptButton",
    "printReviewCancelButton",
    "printRemoveAllDialog",
    "printRemoveAllMessage",
    "printRemoveAllYesButton",
    "printRemoveAllNoButton",
}


def _dialogus_es_reszei() -> str:
    utak = (_QML_DIR / "PrintDialog.qml", *(_QML_DIR / nev for nev in _RESZEK))
    return "\n".join(
        ut.read_text(encoding="utf-8") for ut in utak if ut.exists()
    )


def test_a_parbeszed_reszei_kulon_fajlban_es_800_sor_alatt_vannak() -> None:
    hianyzo = [nev for nev in _RESZEK if not (_QML_DIR / nev).is_file()]
    assert not hianyzo, f"hiányzó nyomtatási komponensek: {hianyzo}"

    hosszak = {
        nev: len((_QML_DIR / nev).read_text(encoding="utf-8").splitlines())
        for nev in ("PrintDialog.qml", *_RESZEK)
    }
    tul_hosszu = {nev: sor for nev, sor in hosszak.items() if sor > 800}
    assert not tul_hosszu, f"800 sornál hosszabb nyomtatási QML-részek: {tul_hosszu}"


def test_a_parbeszed_hasznalja_a_kulon_komponenseket() -> None:
    for fajl in _RESZEK:
        tipus = fajl.removesuffix(".qml")
        hasznalok = [
            nev for nev in ("PrintDialog.qml", *_RESZEK)
            if nev != fajl
            and re.search(
                rf"\b{re.escape(tipus)}\s*\{{",
                (_QML_DIR / nev).read_text(encoding="utf-8"),
            )
        ]
        assert hasznalok, f"a {tipus} nincs bekötve a nyomtatási komponensekbe"


def test_minden_meglevo_objectname_megmarad() -> None:
    qml = _dialogus_es_reszei()
    kapott = set(re.findall(r'objectName:\s*"([^"]+)"', qml))
    hianyzo = sorted(_MEGŐRZENDŐ_OBJECT_NEVEK - kapott)
    assert not hianyzo, f"megszűnt PrintDialog objectName-ek: {hianyzo}"
    assert '"printPresetSize" + index' in qml, (
        "a gyorsméret-gombok dinamikus objectName-je megváltozott"
    )
