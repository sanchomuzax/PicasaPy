"""#5018: az angol (brit) katalógus minden saját felirata legyen kész."""

from pathlib import Path
import xml.etree.ElementTree as ET


_ENUK = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "picasapy"
    / "app"
    / "i18n"
    / "picasapy_enUK.ts"
)


def test_british_english_catalog_has_no_unfinished_messages():
    root = ET.parse(_ENUK).getroot()
    unfinished = [
        f"{context.findtext('name')} / {message.findtext('source')}"
        for context in root.findall("context")
        for message in context.findall("message")
        if (message.find("translation") is not None)
        and message.find("translation").get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} enUK üzenet unfinished: "
        + "; ".join(unfinished[:10])
    )
