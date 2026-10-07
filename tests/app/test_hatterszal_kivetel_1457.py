"""A háttérszál KIVÉTELE nem viheti magával a folyamatot (#1457).

## A mérés, ami ezt kikényszerítette

A `788877d6` main-futásán a windows 4/4 darab elbukott, **kétszer egymás
után** (a futtató újrapróbálása sem fedte el) — miközben a fájl MINDEN
tesztje átment:

```
tests\\app\\test_projekt_mappa_figyeles_1123.py
.......                                      [100%]
7 passed in 2.65s
Exception in thread picasapy-sync-dirty:
Fatal Python error: _enter_buffered_busy: could not acquire lock for
  <_io.BufferedWriter name='<stderr>'> at interpreter shutdown,
  possibly due to daemon threads
Python runtime state: finalizing
```

Kilépőkód `3221226505` = `0xC0000409`, windowsos **fast-fail** — pontosan az
az alak, amit a #1457 hónapok óta „véletlenszerű összeomlásként" gyűjt.

## A lánc, végig

1. egy `_start_background`-gal indított **daemon**-szál kivétellel áll le;
2. a `threading` alapértelmezett `excepthook`-ja a visszakövetést a
   **`sys.stderr`-re** írja;
3. ha ez az értelmező **leállása** közben történik, a `stderr` pufferének
   zárja már nem szerezhető meg, és a CPython **abortál**.

⇒ A tesztek UTÁN történik, ezért **egyetlen állítás sem fogja meg**, és a
bukás „véletlenszerűnek" látszik. Ez a lap a 2. lépést szünteti meg: a
kivétel a NAPLÓBA megy, nem a `stderr`-re, tehát a folyamat él.

⚠️ Amit ez **nem** old meg: azt, hogy a dirty-szinkron szál egyáltalán
kivételt dob. Az a #1457 következő lépése — de a naplósor mostantól
MEGMONDJA, melyik kivétel az; eddig a fatális abort elvitte magával.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import CancelledError as FutureCancelledError
import logging
import threading

import pytest

from picasapy.app.worker_thread import (
    BackgroundWorkerMixin,
    wait_for_all_background_workers,
)


class _Vezerlo(BackgroundWorkerMixin):
    pass


class TestAKivetelNemSzallElA_stderr_re:
    def test_a_szal_kivetele_NEM_jut_el_a_threading_excepthookig(self) -> None:
        """⛔ Ez a próba foga: ha a kivétel kiejtődik, a `threading`
        `excepthook`-ja fut — és élesen ez öli meg a folyamatot."""
        latott: list[object] = []
        eredeti = threading.excepthook
        threading.excepthook = latott.append
        try:
            vezerlo = _Vezerlo()

            def robban() -> None:
                raise RuntimeError("szándékos hiba a háttérszálon")

            szal = vezerlo._start_background(robban, name="proba-robbano")
            szal.join(5.0)
            assert not szal.is_alive()
        finally:
            threading.excepthook = eredeti

        assert latott == [], (
            "a kivétel eljutott a threading excepthookjáig — leállás közben "
            "ez `Fatal Python error: _enter_buffered_busy`-t adna"
        )

    def test_a_kivetel_a_NAPLOBA_kerul_a_szal_nevevel(self, caplog) -> None:
        """Nem elnémítás: a hibának látszania kell — a szál nevével, hogy a
        következő bukásnál tudjuk, MELYIK munka dobta."""
        vezerlo = _Vezerlo()

        def robban() -> None:
            raise ValueError("ez legyen a naplóban")

        with caplog.at_level(logging.ERROR, logger="picasapy.app.worker_thread"):
            szal = vezerlo._start_background(robban, name="picasapy-proba-dirty")
            szal.join(5.0)

        assert "picasapy-proba-dirty" in caplog.text
        assert "ez legyen a naplóban" in caplog.text

    def test_a_hibas_szal_is_KIKERUL_a_nyilvantartasbol(self) -> None:
        """A `finally`-ág könyvelése a kivételes úton is lefut — különben a
        bevárás egy halott szálra várna, a busy-csík meg pörögne."""
        vezerlo = _Vezerlo()

        def robban() -> None:
            raise RuntimeError("hiba")

        szal = vezerlo._start_background(robban, name="proba-konyveles")
        szal.join(5.0)
        assert wait_for_all_background_workers(5.0)
        assert not vezerlo.backgroundWorkersRunning()

    def test_a_kivetel_utan_is_indithato_uj_munka(self) -> None:
        vezerlo = _Vezerlo()
        eredmeny: list[str] = []

        vezerlo._start_background(
            lambda: (_ for _ in ()).throw(RuntimeError("első")), name="proba-1"
        ).join(5.0)
        vezerlo._start_background(
            lambda: eredmeny.append("lefutott"), name="proba-2"
        ).join(5.0)
        assert eredmeny == ["lefutott"]

    def test_a_normal_workerhiba_eljut_az_owner_error_callbackhez(self) -> None:
        """A mixin ne csak naplózza: az owner kapja meg az eredeti kivételt."""
        vezerlo = _Vezerlo()
        hiba = ValueError("diagnosztikához megtartandó hiba")
        latott: list[Exception] = []

        def robban() -> None:
            raise hiba

        szal = vezerlo._start_background(
            robban,
            name="proba-owner-hiba",
            on_error=latott.append,
        )
        szal.join(5.0)

        assert not szal.is_alive()
        assert latott == [hiba]
        assert type(latott[0]) is ValueError

    @pytest.mark.parametrize(
        "cancellation",
        (asyncio.CancelledError, FutureCancelledError),
    )
    def test_a_megszakitas_nem_hiba_es_nem_hivja_az_owner_callbacket(
        self, cancellation
    ) -> None:
        vezerlo = _Vezerlo()
        latott: list[Exception] = []

        def megszakitva() -> None:
            raise cancellation("felhasználó megszakította")

        szal = vezerlo._start_background(
            megszakitva,
            name="proba-megszakitas",
            on_error=latott.append,
        )
        szal.join(5.0)

        assert not szal.is_alive()
        assert latott == []
        assert vezerlo.takeBackgroundWorkerErrors() == ()

    def test_a_callback_hibaja_sem_jut_el_a_threading_excepthookig(
        self, caplog, monkeypatch
    ) -> None:
        vezerlo = _Vezerlo()
        excepthook_hivasok: list[object] = []
        monkeypatch.setattr(threading, "excepthook", excepthook_hivasok.append)

        def hibas_callback(_error: Exception) -> None:
            raise RuntimeError("a callback is hibázott")

        with caplog.at_level(
            logging.ERROR, logger="picasapy.app.worker_thread"
        ):
            szal = vezerlo._start_background(
                lambda: (_ for _ in ()).throw(ValueError("workerhiba")),
                name="proba-hibas-callback",
                on_error=hibas_callback,
            )
            szal.join(5.0)

        assert not szal.is_alive()
        assert excepthook_hivasok == []
        assert "a callback is hibázott" in caplog.text

    def test_handler_nelkul_is_lekerdezheto_a_strukturalt_workerhiba(self) -> None:
        vezerlo = _Vezerlo()
        hiba = OSError("nincs olvasási hozzáférés")

        def hibas_munka() -> None:
            raise hiba

        szal = vezerlo._start_background(
            hibas_munka,
            name="proba-strukturalt-hiba",
        )
        szal.join(5.0)

        assert not szal.is_alive()
        failures = vezerlo.takeBackgroundWorkerErrors()
        assert len(failures) == 1
        assert failures[0].worker_name == "proba-strukturalt-hiba"
        assert failures[0].exception_type == "OSError"
        assert failures[0].message == "nincs olvasási hozzáférés"
        assert vezerlo.takeBackgroundWorkerErrors() == ()
