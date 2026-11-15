"""Az E-mail parancs küldési folyamatának eredeti Picasa szerinti részei (#6987).

Az eredeti (`docs/specs/paritas-ellenorzes.md`, #6984) sorrendje:

1. 20-nál több képnél megerősítő kérdés (`CThumbUI::OutputBottleneck`,
   `0x00531550`); Mégse esetén semmi sem készül elő;
2. a csatolmányok előkészítése;
3. a levél tárgya és törzse a képszám szerint (`0x0073d970`);
4. a levelező közvetlen megnyitása (saját levelezős ág, `EmailPrepType = 3`,
   `0x00742a2c`), belső szerkesztőpanel nélkül;
5. a MAPI hibakódok külön üzenete, a felhasználói megszakítás csendes
   (`0x0073d8c0`).

⚠️ A `]history:email` előzmény-jelölés SZÁNDÉKOSAN nincs itt: nem
`.picasa.ini`-token, hanem az `albumdata_token.pmp` album-sorának tokenje
(`docs/specs/export-parbeszed.md` 13.9), a PMP-t pedig a PicasaPy csak
olvassa (`docs/specs/pmp-database.md`).

⚠️ A levélbe SZÁNDÉKOSAN nem kerül az `IDS_MAPITAGLINE` reklámsor: az a
megszűnt Google Picasa oldalát hirdeti.

A szövegek az eredeti szövegtárból valók (`IDS_MAPI_SUBJ_*`, `IDS_MAPI_BODY_*`,
`IDS_MAPI_*`), a fordításaik mind a 41 nyelvben a hivatalosak. A `translate()`
hívások a `lupdate` miatt LITERÁL argumentumokkal állnak.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication, Slot

from picasapy.mailer.mapi import (
    MAPI_E_ATTACHMENT_NOT_FOUND,
    MAPI_E_ATTACHMENT_OPEN_FAILURE,
    MAPI_E_TOO_MANY_FILES,
    MAPI_E_UNKNOWN_RECIPIENT,
)

#: Ennél TÖBB kép elküldése előtt kérdez a program (`0x00531550`).
MEGEROSITES_HATAR = 20


def mail_subject(count: int) -> str:
    """A levél tárgya: `IDS_MAPI_SUBJ_SINGLE` / `IDS_MAPI_SUBJ_MULTI`."""
    if count == 1:
        return QCoreApplication.translate("EmailController", "a picture for you")
    return QCoreApplication.translate(
        "EmailController", "%d pictures for you"
    ).replace("%d", str(count))


def mail_body(count: int) -> str:
    """A levél törzse: `IDS_MAPI_BODY_SINGLE` / `IDS_MAPI_BODY_MULTI`."""
    if count == 1:
        return QCoreApplication.translate(
            "EmailController", "You have been sent 1 picture.\n\n"
        )
    return QCoreApplication.translate(
        "EmailController", "You have been sent %d pictures.\n\n"
    ).replace("%d", str(count))


def mapi_error_text(code: int) -> str:
    """A MAPI hibakód hivatalos üzenete (a felhasználói megszakítást a hívó
    csendben kezeli, ide nem jut el).

    A három külön megnevezett eset a túl sok melléklet, a nem található és a
    nem megnyitható melléklet; az ismeretlen címzett és az általános hiba
    szövege ugyanebből a szövegtárból való."""
    if code == MAPI_E_TOO_MANY_FILES:
        return QCoreApplication.translate(
            "EmailController", "Too many file attachments to send."
        )
    if code == MAPI_E_ATTACHMENT_NOT_FOUND:
        return QCoreApplication.translate(
            "EmailController", "Attachment was not found"
        )
    if code == MAPI_E_ATTACHMENT_OPEN_FAILURE:
        return QCoreApplication.translate(
            "EmailController", "Could not open an attachment."
        )
    if code == MAPI_E_UNKNOWN_RECIPIENT:
        return QCoreApplication.translate("EmailController", "Unknown recipient.")
    return QCoreApplication.translate(
        "EmailController", "The email could not be sent."
    )


class EmailSendFlowMixin:
    """A kijelölés elküldésének kapuja: kérdés, előkészítés, küldés."""

    @Slot(list, bool)
    def sendSelection(self, rows, confirmed: bool) -> None:  # noqa: N802
        """A kijelölt sorok elküldése az eredeti sorrendjében.

        `confirmed`: a felhasználó a 20 fölötti kérdésre már igent mondott.
        A kérdés a TÉNYLEGES kimenet darabszámáról szól (`_resolve_records`:
        a nem üres képtálca nyer), és `sendConfirmRequested`-del érkezik a
        felületre; Mégse esetén itt nem történik több semmi."""
        darab = len(self._resolve_records(rows))
        if darab > MEGEROSITES_HATAR and not confirmed:
            self.sendConfirmRequested.emit(list(rows), darab)
            return
        csatolmanyok = self.prepareAttachments(rows, len(rows) > 1)
        if csatolmanyok:
            self.sendRows(csatolmanyok, "", "")
