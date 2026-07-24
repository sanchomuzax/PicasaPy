"""Egységteszt: időrendi csoportosítás (#24) — `picasapy.timeline`.

Tiszta Python, Qt/GUI nélkül: a `resolve_date` dátum-feloldását és a
`build_periods` csoportosítását/rendezését fedi le, a peremesetekkel
együtt (üres bemenet, hiányzó dátum, azonos hónap több évben).
"""

from datetime import date

from picasapy.timeline import (
    UNKNOWN_MONTH,
    UNKNOWN_YEAR,
    TimelinePhoto,
    build_periods,
    resolve_date,
)

# néhány kényelmi időbélyeg (mtime_ns) a resolve_date teszteléséhez —
# 2026-03-15 00:00:00 UTC egésznek megfelelő nanoszekundum-érték
_MTIME_2026_03_15 = 1773571200_000_000_000


class TestResolveDate:
    def test_prefers_taken_at_over_mtime(self):
        # a taken_at 2024-es, az mtime 2026-os — a taken_at nyer
        assert resolve_date("2024-01-02T10:00:00", _MTIME_2026_03_15) == date(
            2024, 1, 2
        )

    def test_falls_back_to_mtime_when_taken_at_missing(self):
        assert resolve_date(None, _MTIME_2026_03_15) == date(2026, 3, 15)

    def test_falls_back_to_mtime_when_taken_at_invalid(self):
        # sérült/olvashatatlan EXIF-dátum — nem eshet pánikba, mtime-ra esik
        assert resolve_date("nem-dátum", _MTIME_2026_03_15) == date(2026, 3, 15)

    def test_none_when_neither_available(self):
        assert resolve_date(None, 0) is None

    def test_empty_string_taken_at_falls_back(self):
        assert resolve_date("", _MTIME_2026_03_15) == date(2026, 3, 15)


class TestBuildPeriodsEmptyInput:
    def test_empty_list_returns_empty_tuple(self):
        assert build_periods([]) == ()

    def test_empty_tuple_returns_empty_tuple(self):
        assert build_periods(()) == ()


class TestBuildPeriodsGrouping:
    def test_groups_by_year_and_month(self):
        photos = [
            TimelinePhoto(photo_id=1, date=date(2026, 7, 1)),
            TimelinePhoto(photo_id=2, date=date(2026, 7, 20)),
            TimelinePhoto(photo_id=3, date=date(2026, 6, 5)),
        ]
        periods = build_periods(photos)
        assert len(periods) == 2
        assert periods[0].year == 2026 and periods[0].month == 7
        assert {p.photo_id for p in periods[0].photos} == {1, 2}
        assert periods[1].year == 2026 and periods[1].month == 6
        assert {p.photo_id for p in periods[1].photos} == {3}

    def test_newest_period_first(self):
        photos = [
            TimelinePhoto(photo_id=1, date=date(2020, 1, 1)),
            TimelinePhoto(photo_id=2, date=date(2026, 7, 1)),
            TimelinePhoto(photo_id=3, date=date(2023, 12, 1)),
        ]
        periods = build_periods(photos)
        assert [(p.year, p.month) for p in periods] == [
            (2026, 7),
            (2023, 12),
            (2020, 1),
        ]

    def test_same_month_different_years_are_distinct_groups(self):
        # peremeset: ugyanaz a hónap (március) több évben — nem mosódhat
        # egy csoportba
        photos = [
            TimelinePhoto(photo_id=1, date=date(2024, 3, 10)),
            TimelinePhoto(photo_id=2, date=date(2025, 3, 10)),
            TimelinePhoto(photo_id=3, date=date(2026, 3, 10)),
        ]
        periods = build_periods(photos)
        assert len(periods) == 3
        assert [(p.year, p.month) for p in periods] == [
            (2026, 3),
            (2025, 3),
            (2024, 3),
        ]

    def test_within_group_order_is_newest_first(self):
        photos = [
            TimelinePhoto(photo_id=1, date=date(2026, 7, 1)),
            TimelinePhoto(photo_id=2, date=date(2026, 7, 31)),
            TimelinePhoto(photo_id=3, date=date(2026, 7, 15)),
        ]
        periods = build_periods(photos)
        assert [p.photo_id for p in periods[0].photos] == [2, 3, 1]

    def test_equal_dates_keep_input_order(self):
        # stabil rendezés: azonos dátumnál a bemeneti sorrend megmarad
        photos = [
            TimelinePhoto(photo_id=1, date=date(2026, 7, 1)),
            TimelinePhoto(photo_id=2, date=date(2026, 7, 1)),
        ]
        periods = build_periods(photos)
        assert [p.photo_id for p in periods[0].photos] == [1, 2]


class TestBuildPeriodsUndated:
    def test_missing_date_grouped_separately_at_end(self):
        photos = [
            TimelinePhoto(photo_id=1, date=date(2026, 7, 1)),
            TimelinePhoto(photo_id=2, date=None),
            TimelinePhoto(photo_id=3, date=date(2025, 1, 1)),
        ]
        periods = build_periods(photos)
        assert len(periods) == 3
        assert periods[-1].year == UNKNOWN_YEAR
        assert periods[-1].month == UNKNOWN_MONTH
        assert [p.photo_id for p in periods[-1].photos] == [2]

    def test_all_undated_single_group(self):
        photos = [
            TimelinePhoto(photo_id=1, date=None),
            TimelinePhoto(photo_id=2, date=None),
        ]
        periods = build_periods(photos)
        assert len(periods) == 1
        assert periods[0].year == UNKNOWN_YEAR
        assert {p.photo_id for p in periods[0].photos} == {1, 2}

    def test_immutable_result_types(self):
        # a kimenet tuple-tuple (nem lista) — a hívó (controller) felelős
        # a QML-nek adható lista-alakra fordításért
        photos = (TimelinePhoto(photo_id=1, date=date(2026, 1, 1)),)
        periods = build_periods(photos)
        assert isinstance(periods, tuple)
        assert isinstance(periods[0].photos, tuple)
