"""#1875 — a csak-megjegyzés változás nem kíván CHANGELOG-mondatot.

## A hibaosztály

A CHANGELOG-őr (#1340) **fájlnév alapján** dönti el, hogy egy PR eljut-e a
felhasználóhoz. Ezért a `src/` alatti **csak-megjegyzés** változást is
felhasználói változásnak veszi, és emberi mondatot követel a naplóba.

Éles eset: a #1873 (a #1607 mérésének beírása a konstans `#:` blokkjába)
elbukott rajta, holott **egyetlen kódsor sem változott**. A PR-t lezártam,
mert nem-felhasználói mondatot írni a felhasználói naplóba épp azt rontaná
el, amit a #1340 véd.

## ⚠️ Miért SZŰK a szabály

Ez az őr a felhasználót védi: a **téves riasztás** bosszantó, a **téves
átengedés** viszont NÉMA, és hónapok múlva derül ki, egy tartalmatlan
kiadási jegyzeten (v0.8.71–73). Ezért:

* csak `#`-kezdetű (és üres) sorok — bármely érdemi sor kiüti;
* a Python-**docstring** NEM tartozik ide (nem `#`-sor) — ott a szigor marad;
* üres diff = „nem tudjuk" ⇒ NEM komment.

A készlet súlypontja ezért a NEM-eken van: mindegyik azt méri, hogy a
lazítás **nem lyukadt ki**.
"""

from __future__ import annotations

import pytest

from scripts.changelog_or import csak_komment_valtozas

KOMMENT_DIFF = """--- a/src/picasapy/render/x.py
+++ b/src/picasapy/render/x.py
@@ -1,3 +1,4 @@
-#: régi magyarázat
+#: új magyarázat
+#: még egy sor
"""


class TestAmiKOMMENT:
    def test_csak_kommentsorok(self):
        assert csak_komment_valtozas(KOMMENT_DIFF)

    def test_ures_sorok_is_beleferenek(self):
        diff = "--- a/x.py\n+++ b/x.py\n@@\n+\n+# valami\n-\n"
        assert csak_komment_valtozas(diff)

    def test_behuzott_komment_is_komment(self):
        diff = "--- a/x.py\n+++ b/x.py\n@@\n+    # behúzva\n"
        assert csak_komment_valtozas(diff)


class TestAmiNEM_komment:
    def test_egyetlen_kodsor_a_kommentek_MELLETT_kiuti(self):
        """A legfontosabb eset: kód ÉS komment ugyanabban a fájlban."""
        diff = KOMMENT_DIFF + "+X = 3\n"
        assert not csak_komment_valtozas(diff)

    def test_kodsor_TORLESE_is_kiuti(self):
        diff = "--- a/x.py\n+++ b/x.py\n@@\n+# magyarázat\n-X = 3\n"
        assert not csak_komment_valtozas(diff)

    def test_a_DOCSTRING_valtozas_NEM_komment(self):
        """A docstring nem `#`-sor — ott a szigor szándékosan marad."""
        diff = '--- a/x.py\n+++ b/x.py\n@@\n+    """új docstring."""\n'
        assert not csak_komment_valtozas(diff)

    def test_ures_diff_NEM_komment(self):
        """A sikertelen mérésből sosem lehet zöld út."""
        assert not csak_komment_valtozas("")

    def test_csak_fejlec_NEM_komment(self):
        assert not csak_komment_valtozas("--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n")

    @pytest.mark.parametrize(
        "sor",
        ["+import os", "+    return 3", "-def f():", "+}", "+X = '# nem komment'"],
    )
    def test_kodsorok_kiutik(self, sor):
        assert not csak_komment_valtozas(KOMMENT_DIFF + sor + "\n")


class TestAzEgeszOr:
    """Végponttól végpontig: a #1873 esete zöld, a valódi kódváltozás nem."""

    def _runner(self, fajlok: str, diffek: dict[str, str]):
        class Valasz:
            def __init__(self, out):
                self.returncode = 0
                self.stdout = out
                self.stderr = ""

        def runner(args):
            if "--name-only" in args:
                return Valasz(fajlok)
            for kulcs, diff in diffek.items():
                if kulcs in args:
                    return Valasz(diff)
            return Valasz("")

        return runner

    def test_a_1873_esete_ZOLD(self, tmp_path):
        from scripts.changelog_or import main

        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n", encoding="utf-8")
        kod = main(
            ["--base", "A", "--head", "B", "--changelog", str(naplo)],
            runner=self._runner(
                "src/picasapy/render/glimmer_ops.py\n",
                {"src/picasapy/render/glimmer_ops.py": KOMMENT_DIFF},
            ),
        )
        assert kod == 0

    def test_valodi_kodvaltozas_tovabbra_is_BUKIK(self, tmp_path):
        from scripts.changelog_or import main

        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n", encoding="utf-8")
        kod = main(
            ["--base", "A", "--head", "B", "--changelog", str(naplo)],
            runner=self._runner(
                "src/picasapy/render/glimmer_ops.py\n",
                {"src/picasapy/render/glimmer_ops.py": KOMMENT_DIFF + "+X = 3\n"},
            ),
        )
        assert kod == 1, "kódváltozásra CHANGELOG-mondat kell"


class TestQmlKomment:
    """#2042: a QML `//`-megjegyzés is megjegyzés.

    Élesben (#2036) egy docs-PR bukott el EGYETLEN QML-komment miatt, és a
    megoldás az lett, hogy a komment kikerült a PR-ből — vagyis az őr
    munkát tolt ki a fájlból. A `#`-eset a #1875 óta kezelve van; a `//`
    nem volt.
    """

    def _diff(self, fajl: str, *sorok: str) -> str:
        fej = f"--- a/{fajl}\n+++ b/{fajl}\n@@ -1,2 +1,2 @@\n"
        return fej + "".join(s + "\n" for s in sorok)

    def test_qml_kettos_perjeles_komment_atmegy(self) -> None:
        diff = self._diff(
            "src/picasapy/app/qml/PicasaPy/Main.qml",
            "-        // régi magyarázat",
            "+        // #2042: friss magyarázat",
        )
        assert csak_komment_valtozas(diff, "src/picasapy/app/qml/PicasaPy/Main.qml")

    def test_qml_valodi_kodsor_BUKTAT(self) -> None:
        diff = self._diff(
            "src/picasapy/app/qml/PicasaPy/Main.qml",
            "+        // magyarázat",
            "+        visible: false",
        )
        assert not csak_komment_valtozas(
            diff, "src/picasapy/app/qml/PicasaPy/Main.qml"
        )

    def test_qml_blokk_komment_eseten_a_SZIGOR_nyer(self) -> None:
        """A `/* */` több sorra nyúlik; egy megváltozott belső sor
        közönséges kódnak látszik. Bizonytalanságnál a szigorú ág."""
        diff = self._diff(
            "src/picasapy/app/qml/PicasaPy/Main.qml",
            "+        /* magyarázat",
            "+           folytatás */",
        )
        assert not csak_komment_valtozas(
            diff, "src/picasapy/app/qml/PicasaPy/Main.qml"
        )

    def test_sablonsztring_eseten_a_SZIGOR_nyer(self) -> None:
        """A JS-sablonsztring (backtick) több sorra nyúlhat, tehát egy
        `//`-kezdetű sor lehet SZTRING belseje is."""
        diff = self._diff(
            "src/picasapy/app/qml/PicasaPy/Main.qml",
            "+        // magyarázat",
            "+        const s = `https://pelda`",
        )
        assert not csak_komment_valtozas(
            diff, "src/picasapy/app/qml/PicasaPy/Main.qml"
        )

    def test_qml_fajlnal_a_kettoskereszt_NEM_komment(self) -> None:
        """A `#` a QML-ben nem megjegyzés (szín-literál kezdete lehet)."""
        diff = self._diff(
            "src/picasapy/app/qml/PicasaPy/Theme.qml",
            "+        color: #ff0000",
        )
        assert not csak_komment_valtozas(
            diff, "src/picasapy/app/qml/PicasaPy/Theme.qml"
        )

    def test_fajlnev_nelkul_a_regi_viselkedes(self) -> None:
        """Visszafelé kompatibilitás: fájlnév nélkül a `#`-szabály él."""
        assert csak_komment_valtozas(KOMMENT_DIFF)
