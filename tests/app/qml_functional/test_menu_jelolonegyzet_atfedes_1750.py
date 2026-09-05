"""#1750: a jelölőnégyzetes menütétel felirata RÁLÓG a négyzetre.

## A jelentés

A tulajdonos képernyőmentése (v0.8.146) azt mutatja, hogy a jelölőnégyzetes
menüpontok szövege a négyzet ALATT kezdődik, tehát átfedik egymást. Angol
nyelven is jelentkezik, vagyis nem fordítás-hossz kérdése.

## Az ok — mérve, nem találgatva

A `PicasaMenuItem` SAJÁT `contentItem`-et ad (#757: a mnemonikus `&` miatt
`IconLabel` kell). A Qt alapértelmezett `MenuItem`-je a saját
`contentItem`-jében **helyet hagy a jelölőnek**:

    leftPadding: control.checkable && control.indicator
                 ? control.indicator.width + control.spacing : 0

A miénkből ez KIMARADT, ezért a felirat a tétel bal széléről indul — a
jelölőnégyzet alól. A sima `MenuItem`-et használó (működő) menüpontokon a
hiba NEM látszik, mert azok az alapértelmezett `contentItem`-et kapják;
csak a `PicasaMenuItem` öt jelölőnégyzetes tételén.

## Amit ez az őr állít

1. jelölőnégyzetes tételnél a felirat bal oldali térköze LEFEDI a jelölőt;
2. jelölő NÉLKÜLI tételnél nincs felesleges behúzás (nem tolódik el a
   többi felirathoz képest);
3. almenü-nyíl esetén a jobb oldali térköz ugyanígy megvan.

A 2. pont nem díszítés: az „adjunk mindig behúzást" megoldás elrontaná a
menü többi sorának igazítását, és a hibát egy másikra cserélné.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent


def _tetel(engine, torzs: str):
    """Egy `PicasaMenuItem` egy `Menu`-ben — a jelölő csak ott épül fel.

    ⚠️ A `QQmlComponent`-et IS vissza kell adni: ha csak a létrehozott
    ablakra tartunk Python-hivatkozást, a komponens felszabadul, és vele a
    C++ oldali gyerekek is — a próba `RuntimeError: Internal C++ object …
    already deleted`-tel bukna, nem a mért állításon.
    """
    komponens = QQmlComponent(engine)
    komponens.setData(
        f"""
        import QtQuick
        import QtQuick.Controls
        import PicasaPy 1.0
        ApplicationWindow {{ width: 400; height: 300; visible: true
          Menu {{ id: menu; objectName: "probaMenu"; visible: true
            PicasaMenuItem {{ objectName: "probaTetel"; {torzs} }}
          }}
        }}
        """.encode(),
        QUrl(),
    )
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    tetel = ablak.findChild(QObject, "probaTetel")
    assert tetel is not None, "a próba-menütétel nem épült fel"
    return komponens, ablak, tetel


class TestJelolonegyzetAtfedes:
    def test_a_jelolonegyzetes_tetel_felirata_NEM_log_ra_a_negyzetre(
        self, qml_app, qt_app
    ):
        _window, _controller, engine = qml_app
        komponens, ablak, tetel = _tetel(
            engine, 'text: "Proba"; checkable: true; placeholder: false'
        )
        qt_app.processEvents()

        jelolo = tetel.property("indicator")
        assert jelolo is not None, "a jelölőnégyzetes tételnek nincs jelölője"
        tartalom = tetel.property("contentItem")
        assert tartalom is not None

        jelolo_szelesseg = float(jelolo.property("width"))
        assert jelolo_szelesseg > 0, (
            "a jelölő szélessége 0 — a próba nem mér semmit"
        )
        bal_terkoz = float(tartalom.property("leftPadding"))

        assert bal_terkoz >= jelolo_szelesseg, (
            "a felirat bal térköze "
            f"({bal_terkoz:.1f}) kisebb a jelölőnégyzet szélességénél "
            f"({jelolo_szelesseg:.1f}) — a szöveg ráfut a négyzetre (#1750)"
        )
        ablak.deleteLater()
        del komponens

    def test_jelolo_NELKUL_nincs_felesleges_behuzas(self, qml_app, qt_app):
        """A hibát nem szabad egy másikra cserélni: a jelölő nélküli
        tételek felirata maradjon ott, ahol volt."""
        _window, _controller, engine = qml_app
        komponens, ablak, tetel = _tetel(
            engine, 'text: "Proba"; placeholder: false'
        )
        qt_app.processEvents()

        tartalom = tetel.property("contentItem")
        assert float(tartalom.property("leftPadding")) == pytest.approx(0.0), (
            "a jelölő nélküli tétel felirata elcsúszott — a többi sorhoz "
            "képest nem igazodna"
        )
        ablak.deleteLater()
        del komponens
