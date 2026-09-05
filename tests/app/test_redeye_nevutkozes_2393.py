"""#2393: a vezérlő „mentett vörösszem" jelzője NEM a nyitott eszközé.

## A csapda

Két, ellentétes jelentésű tag élt azonos néven:

| név | jelentés | hol |
|---|---|---|
| `redeyeActive` | van-e **MENTETT** vörösszem-javítás | `edit_controller.py` |
| `redeyeActive` | **NYITVA van-e az eszköz** (mód-kapcsoló) | `EditorPanel.qml:132` |

Ez már félrevitt egy jegyet: a #1485 duplikált állapotnak nézte őket, és
azt írta elő, hogy a panel kösse a vezérlőét. Az a javítás hibás lett
volna — egy mentett javítású képnél a csempe állandóan benyomva látszana.

A vezérlő tagja ezért `hasSavedRedeye` néven él tovább. A panelé
változatlan: az a mód-kapcsoló.

## Amit ez az őr állít

Hogy a vezérlő tagja a MENTETT szerkesztésről szól: üres munkamenetnél
hamis, `redeye` művelet felvétele után igaz — és hogy a régi, félrevezető
név nem tér vissza.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def vezerlo(qt_app):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditController(EditPreviewProvider())


def test_a_mentett_szerkesztest_jelzi(vezerlo) -> None:
    from picasapy.edit.session import EditSession

    vezerlo._session = EditSession()
    assert vezerlo.hasSavedRedeye is False

    vezerlo._session = EditSession.from_value("redeye=1;")
    assert vezerlo.hasSavedRedeye is True


def test_a_felrevezeto_nev_nem_ter_vissza() -> None:
    """A `redeyeActive` a PANELÉ — a vezérlőn nem élhet újra."""
    from picasapy.app import edit_controller

    assert not hasattr(edit_controller.EditController, "redeyeActive"), (
        "a vezérlőn újra megjelent a `redeyeActive` — ez ütközik az "
        "EditorPanel mód-kapcsolójával, és pontosan ez vitte félre a #1485-öt"
    )
