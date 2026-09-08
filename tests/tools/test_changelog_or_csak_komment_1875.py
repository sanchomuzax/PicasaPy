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

## #2708 — a docstring bővítése

A fenti „a docstring NEM tartozik ide" mondat **csak fájlnév nélkül** igaz
(visszafelé kompatibilitás — ld. `test_fajlnev_nelkul_a_regi_viselkedes`).
`.py` fájlnévvel az őr immár felismeri a **biztonságos** docstring-only
esetet is (`TestPythonDocstring` osztály lent) — az élő #2707 diffjén
bizonyítva."""

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

    def test_nem_komment_sor_a_diffben_BUKTAT(self) -> None:
        """Vegyes diff: a nem-komment sor már a `startswith` próbán elbukik.

        (Korábban ezt a próbát »sablonsztring« címen a backtick-szabály is
        megfogta volna — de nem az fogta meg, hanem ez. Ld. a #2306-os
        regresszió-próbát alább.)
        """
        diff = self._diff(
            "src/picasapy/app/qml/PicasaPy/Main.qml",
            "+        // magyarázat",
            "+        const s = `https://pelda`",
        )
        assert not csak_komment_valtozas(
            diff, "src/picasapy/app/qml/PicasaPy/Main.qml"
        )

    def test_2306_backtick_a_KOMMENTBEN_nem_buktat(self) -> None:
        """#2306: a projekt MINDEN kommentje backtickkel jelöli az
        azonosítókat — ha a backtick önmagában szigorra váltana, az őr
        gyakorlatilag az összes valódi QML-komment-változást megfogná.

        Élesben meg is történt: a #2302 (tisztán komment-változás a
        `PicasaMenuBar.qml`-ben) ezen bukott el az ubuntu-lábon. A #2042
        próbái csak azért voltak zöldek, mert backtick NÉLKÜLI mintákat
        használtak — a bővítés a valódi kódon sosem tudott működni.
        """
        diff = self._diff(
            "src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml",
            "-        // (`eMenuEdit::ID_UNDO`). A felirat megnevezi a műveletet",
            "+        // a `docs/specs/picasa-menusor-csoportok.md` szerint mérve",
        )
        assert csak_komment_valtozas(
            diff, "src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml"
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


# #2707 valódi diffje (git diff 73b082aa 2f33c067, ubuntu-lábon pirosat
# kapott a régi őrön) — a `#2708` biztonságos docstring-felismerésének
# közvetlen bizonyítéka. A `"""` a diff SAJÁT tartalma, ezért a Python-
# sztringet hármas EGYES idézőjellel kell nyitni, nem hármas dupla-val.
_CVIMAGE_2707_DIFF = '''--- a/src/picasapy/cvimage.py
+++ b/src/picasapy/cvimage.py
@@ -98,6 +98,14 @@ def scale_down(image: np.ndarray, max_dimension: int | None) -> np.ndarray:
     felhasználó munkáját nem szabad, ezért az export-út a mag
     GYORSÍTÁSÁIG marad az `INTER_AREA`-n — #2669.
 
+    **A gyorsítást a #2669 köre megpróbálta, és nem sikerült** (mérve
+    2026-09-08, RPi5): nyolc irányból a legjobb 2,0×-t hozott a magon, így
+    a teljes út 16,1× helyett 7,9× — a 3×-os küszöb több mint kétszerese.
+    Már az elő-szűrés önmagában 1,6–1,9×, tehát a magra ~1,2× jutna. A mért
+    ok az, hogy a Pythonból hívható `cv2.sepFilter2D` nem decimál és egy
+    szálon fut; a gyors, decimáló OpenCV-utak magja rögzített. A teljes
+    tábla: `docs/benchmarks/2026-09-08-2669-mag-gyorsitas.md`.
+
     `max_dimension=None` vagy már elég kicsi kép esetén a bemenet
     változatlanul (azonos objektumként) tér vissza."""
     if max_dimension is None:
'''

_RESAMPLE_2707_DIFF = '''--- a/src/picasapy/resample.py
+++ b/src/picasapy/resample.py
@@ -168,7 +168,19 @@ _FELEZO_HORGONY = 7
 
 
 def _gyors_felezes(kep: np.ndarray) -> np.ndarray:
-    """Pontosan 2 : 1 kicsinyítés a rögzített maggal, OpenCV-vel."""
+    """Pontosan 2 : 1 kicsinyítés a rögzített maggal, OpenCV-vel.
+
+    ⚠️ **Ez a Picasa-út legdrágább fele, és a #2669 köre lemérte, hogy
+    Pythonból nem gyorsítható eleget.** Nyolc irányt próbáltunk (polifázis
+    decimálás, négyfázisú 2D bontás, fixpontos `CV_16S`/`CV_8U`,
+    csatornánkénti szűrés, sávos feldolgozás, kézi szálasítás és ezek
+    kombinációi); a legjobb **2,0×**-t hozott, a küszöbhöz ~10× kellett
+    volna. Az ok mérve: a `cv2.sepFilter2D` nem decimál és egy szálon fut
+    (~3 GMAC/s), a decimáló, fixpontos, szálas OpenCV-utaknak (`resize`,
+    `pyrDown`; 9–12 GMAC/s) viszont be van égetve a magjuk. A teljes tábla
+    és az, mi vinné át a küszöbön:
+    `docs/benchmarks/2026-09-08-2669-mag-gyorsitas.md`.
+    """
     mag = felezo_mag().reshape(-1, 1)
     szurt = cv2.sepFilter2D(
         kep,
'''


class TestPythonDocstring:
    """#2708: a `.py` docstring biztonságos esete is komment-értékű.

    A négy alosztály a jegy „Kész, ha" listáját fedi: docstring-only ÁTMEGY,
    docstring MELLETT valódi kódsor NEM megy át, a #2707 valódi diffje
    átmenne, és a „határeltolás" (kód beszippantása a docstringbe) szigorú
    marad.
    """

    def test_docstring_only_tobbsoros_beszuras_atmegy(self) -> None:
        """A valódi #2707-mintázat: meglévő docstring VÉGÉBE szúrt új
        bekezdés, a záró `\"\"\"` változatlan kontextusként látszik."""
        assert csak_komment_valtozas(_CVIMAGE_2707_DIFF, "src/picasapy/cvimage.py")

    def test_docstring_only_egysoros_docstring_atalakitasa_atmegy(self) -> None:
        """A másik valódi #2707-mintázat: egysoros docstring lesz
        többsorossá — a nyitó `\"\"\"` a hozzáadott sorban NYIT, a záró
        önálló sorban ZÁR, közte minden hozzáadott sor a döntés alapja."""
        assert csak_komment_valtozas(_RESAMPLE_2707_DIFF, "src/picasapy/resample.py")

    def test_a_2707_MINDKET_fajlja_atmegy_a_teljes_orön(self) -> None:
        """Bizonyíték a jegy 3. Kész-ha pontjához: a #2707 EREDETI diffje
        (a workaround ELŐTT, `git diff 73b082aa 2f33c067`) mindkét érintett
        fájlon átmenne az új őrön — tehát nem lett volna szükség a
        docstring→komment átalakításra."""
        assert csak_komment_valtozas(_CVIMAGE_2707_DIFF, "src/picasapy/cvimage.py")
        assert csak_komment_valtozas(_RESAMPLE_2707_DIFF, "src/picasapy/resample.py")

    def test_docstring_MELLETT_valodi_kodsor_tovabbra_is_BUKIK(self) -> None:
        """A jegy 2. Kész-ha pontja: docstring-változás MELLETT egy valódi
        kódsor ne csússzon át."""
        diff = '''--- a/x.py
+++ b/x.py
@@ -1,4 +1,5 @@
 def f():
-    """régi docstring."""
+    """új docstring."""
+    return 3
'''
        assert not csak_komment_valtozas(diff, "x.py")

    def test_docstring_only_egysoros_csere_atmegy(self) -> None:
        """A legegyszerűbb biztonságos eset: egysoros docstring cseréje —
        a nyitó ÉS záró jel is látszik, ugyanazon a (törölt/hozzáadott)
        soron, nincs mit kitalálni."""
        diff = '''--- a/x.py
+++ b/x.py
@@ -1,3 +1,3 @@
 def f():
-    """régi docstring."""
+    """új docstring."""
     return 3
'''
        assert csak_komment_valtozas(diff, "x.py")

    def test_docstring_hatar_athelyezese_kodot_nyel_BUKIK(self) -> None:
        """Biztonsági határeset: a záró `\"\"\"` ELTŰNIK, és egy korábban
        VÁLTOZATLANNAK látszó kódsor emiatt a docstringbe kerülne — ez a
        `render()` sor a régi fájlban KÍVÜL, az újban BELÜL lenne. Az őr ezt
        a kontextus-sorok ütköző állapotával fogja meg, és szigorú marad."""
        diff = '''--- a/x.py
+++ b/x.py
@@ -1,4 +1,3 @@
 def f():
-    """régi docstring."""
-    render()
+    """régi docstring.
     return 3
'''
        assert not csak_komment_valtozas(diff, "x.py")

    def test_nem_py_fajlon_a_docstring_felismeres_nem_fut(self) -> None:
        """A hármas idézőjel Pythonon kívül nem docstring — más
        kiterjesztésnél a felismerés ki sem próbálja (szigor marad)."""
        diff = '''--- a/x.toml
+++ b/x.toml
@@ -1,2 +1,2 @@
-leiras = """régi"""
+leiras = """új"""
'''
        assert not csak_komment_valtozas(diff, "x.toml")

    def test_fajlnev_nelkul_a_docstring_meg_szigoru_marad(self) -> None:
        """Fájlnév nélkül a döntés nem tudja, hogy `.py`-ról van szó —
        a régi, szigorú viselkedés él tovább (ld. modul-docstring #2708
        szakasza)."""
        diff = '''--- a/x.py
+++ b/x.py
@@ -1,3 +1,3 @@
 def f():
-    """régi docstring."""
+    """új docstring."""
     return 3
'''
        assert not csak_komment_valtozas(diff)
