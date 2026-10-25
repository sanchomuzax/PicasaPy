"""A Picasa `moddate` kulcsának Windows FILETIME-kódolása."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from picasapy.ini.moddate import moddate_from_timestamp_ns


def test_moddate_a_megadott_utc_ido_kis_endian_filetime_kent_irodik():
    expected = datetime(2026, 10, 25, 10, 13, 9, 17_039, tzinfo=UTC)
    unix_epoch = datetime(1970, 1, 1, tzinfo=UTC)
    elapsed = expected - unix_epoch
    timestamp_ns = (
        (elapsed.days * 86_400 + elapsed.seconds) * 1_000_000_000
        + elapsed.microseconds * 1_000
        + 200
    )

    encoded = moddate_from_timestamp_ns(timestamp_ns)

    assert encoded == "1842276f6964dd01"
    filetime = int.from_bytes(bytes.fromhex(encoded), "little")
    decoded = datetime(1601, 1, 1, tzinfo=UTC) + timedelta(
        microseconds=filetime // 10
    )
    assert decoded == expected
    assert (filetime - 116_444_736_000_000_000) * 100 == timestamp_ns
