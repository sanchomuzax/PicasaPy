"""A cseh fordítás teljességét és helyőrzőit őrző ellenőrzések."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


CS_TS = (
    Path(__file__).resolve().parents[1]
    / "src/picasapy/app/i18n/picasapy_cs.ts"
)

_FORMATTING_TOKEN = re.compile(
    r"%(?:n|L?\d+|[diuoxX])|\{[^{}]+\}|</?[A-Za-z][^>]*>|\n"
)
_LITERAL_AMPERSAND = re.compile(r"\b[A-Z]&[A-Z]\b|\s&\s")

# Régi, már kitöltött Picasa-sorok, amelyeknél az angol és a cseh
# gyorsbillentyű-jelölők száma eleve eltér. Ezekhez a jegy nem nyúlhat.
_EXISTING_SHORTCUT_EXCEPTIONS = frozenset(
    {
        ("FolderContextMenu", "Move to Collection..."),
        ("FolderContextMenu", "Edit Folder Description..."),
        ("FolderContextMenu", "Select All Pictures"),
        ("FolderContextMenu", "Invert Selection"),
        ("FolderContextMenu", "Sort Folder By"),
        ("FolderContextMenu", "Reverse Order"),
        ("FolderContextMenu", "Hide Folder"),
        ("FolderContextMenu", "Unhide Folder"),
        ("FolderContextMenu", "Add Name Tags"),
        ("PassportErrorDialog", "Passport photo"),
        ("CreateDialogs", "Picture Collage..."),
        ("ExportDialogs", "Export Picture to Folder..."),
        ("SaveDialogs", "Save As..."),
        ("BatchEditProgressPanel", "Batch Edit"),
        ("PublishPanel", "Choose folders & albums to back up"),
        ("Main", "Save search results"),
        ("Main", "Reset Faces"),
        ("Main", "Export Picture to Folder..."),
        ("PhotoContextMenu", "Remove from People Album"),
        ("PhotoContextMenu", "Set as People Album Thumbnail"),
        ("PhotoContextMenu", "Add to People Album"),
        ("PhotoContextMenu", "Locate Original on Disk"),
        ("PhotoContextMenu", "Add to Album"),
        ("PhotoContextMenu", "Remove from Album"),
        ("PhotoContextMenu", "Unhide"),
        ("PhotoContextMenu", "Copy Full Path"),
        ("PhotoContextMenu", "Upload to Picasa Web Albums..."),
        ("PhotoContextMenu", "Block from Uploading"),
        ("PhotoContextMenu", "Reset Faces"),
        ("PicasaMenuBar", "Remove from Album"),
        ("PicasaMenuBar", "Remove from People Album"),
        ("PicasaMenuBar", "Sort by recent changes"),
        ("PicasaMenuBar", "Sort by size"),
        ("PicasaToolsMenu", "Adjust &Date and Time..."),
        ("PicasaMenuBar", "Show"),
        ("PicasaFolderMenu", "Print Contact Sheet..."),
        ("PicasaMenuBar", "Reset Faces"),
        ("PicasaHelpMenu", "Online Information"),
        ("PicasaHelpMenu", "Product Release Notes"),
        ("ImportSourceDialogSourcePanel", "Upload to Picasa Web Albums..."),
        ("AddFileDialog", "Add File to PicasaPy..."),
        ("ViewerContextMenu", "Back to Library"),
        ("ViewerContextMenu", "Add to Album"),
        ("ViewerContextMenu", "Unhide"),
        ("ViewerContextMenu", "Locate Original on Disk"),
        ("ViewerContextMenu", "Remove from Album"),
        ("ViewerContextMenu", "Copy Full Path"),
        ("ViewerContextMenu", "Block from Uploading"),
        ("ViewerContextMenu", "Reset Faces"),
        ("FolderPropertiesDialog", "Edit Folder Description"),
        ("FolderListContextMenu", "Sort by Date"),
        ("FolderListContextMenu", "Sort by Size"),
        ("FolderListContextMenu", "Sort by Most Recent Changes"),
        ("FolderListContextMenu", "Sort People by Name"),
        ("FolderListContextMenu", "Sort People by Count"),
        ("FolderListContextMenu", "Simplified Tree View"),
        ("FolderListContextMenu", "Show Thumbnails in Library"),
        ("AlbumContextMenu", "Edit Album Description..."),
        ("AlbumContextMenu", "Add Name Tags"),
        ("AlbumContextMenu", "Select All Pictures"),
        ("AlbumContextMenu", "Invert Selection"),
        ("AlbumContextMenu", "Upload to Picasa Web Albums..."),
        ("CollectionContextMenu", "Set/Change Password..."),
        ("PeopleAlbumContextMenu", "Delete People Album"),
        ("PeopleAlbumContextMenu", "Edit People Album..."),
        ("TextFieldContextMenu", "Auto-Complete"),
        ("TextFieldContextMenu", "Paste"),
        ("LegacyEffects", "Shadow & Highlight"),
        ("FolderContextMenu", "&Color"),
        ("HelpDialog", "Help Contents and Index"),
        ("GiftCdHost", "Create a Gift CD..."),
    }
)


def _messages():
    root = ET.parse(CS_TS).getroot()
    for context in root.findall("context"):
        context_name = context.findtext("name") or ""
        for message in context.findall("message"):
            yield context_name, message


def _translation_text(translation):
    return "".join(translation.itertext()) if translation is not None else ""


def _translation_forms(translation):
    forms = translation.findall("numerusform") if translation is not None else []
    return [_translation_text(form) for form in forms] or [
        _translation_text(translation)
    ]


def _shortcut_count(text):
    # A dupla & és a szövegközi „&” nem Qt-gyorsbillentyű.
    text = _LITERAL_AMPERSAND.sub("", text)
    return text.count("&") - 2 * text.count("&&")


def test_czech_translation_has_no_unfinished_messages():
    unfinished = [
        f"{context}: {message.findtext('source')}"
        for context, message in _messages()
        if (message.find("translation") is not None)
        and message.find("translation").get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished cseh üzenet maradt; példák: "
        + "; ".join(unfinished[:8])
    )


def test_czech_translation_preserves_placeholders_and_shortcuts():
    mismatches = []
    for context, message in _messages():
        source = message.findtext("source") or ""
        translation = message.find("translation")
        key = (context, source)

        for translated in _translation_forms(translation):
            if Counter(_FORMATTING_TOKEN.findall(source)) != Counter(
                _FORMATTING_TOKEN.findall(translated)
            ):
                mismatches.append(
                    f"{context}: helyőrző vagy HTML eltérés: {source!r}"
                )
            if (
                key not in _EXISTING_SHORTCUT_EXCEPTIONS
                and _shortcut_count(source) != _shortcut_count(translated)
            ):
                mismatches.append(f"{context}: gyorsbillentyű-eltérés: {source!r}")

    assert not mismatches, "\n".join(mismatches[:20])


def test_czech_numerus_messages_have_three_nonempty_forms():
    errors = []
    for context, message in _messages():
        if message.get("numerus") != "yes":
            continue
        translation = message.find("translation")
        forms = translation.findall("numerusform") if translation is not None else []
        if len(forms) != 3 or any(not (form.text or "").strip() for form in forms):
            errors.append(f"{context}: {message.findtext('source')}")

    assert not errors, "A cseh többes alakok hibásak: " + "; ".join(errors[:8])
