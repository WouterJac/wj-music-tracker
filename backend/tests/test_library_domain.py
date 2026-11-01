import pytest

from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    TrackDetail,
    leading_int,
    year_from_date,
)


@pytest.mark.parametrize(
    ("date", "year"),
    [
        ("1977", 1977),
        ("1977-01-14", 1977),
        ("2009/03", 2009),
        ("77", None),
        ("", None),
        (None, None),
    ],
)
def test_year_comes_from_the_leading_four_digits(date: str | None, year: int | None) -> None:
    assert year_from_date(date) == year


@pytest.mark.parametrize(
    ("text", "number"),
    [("3", 3), ("3/12", 3), (" 07 ", 7), ("A1", None), ("", None), (None, None)],
)
def test_leading_int_reads_free_text_track_numbers(text: str | None, number: int | None) -> None:
    assert leading_int(text) == number


def test_total_duration_is_rounded_to_milliseconds() -> None:
    summary = AlbumSummary(1, "Album", None, None, None, 2, False)
    tracks = [TrackDetail(i, None, i, "t", 0.1 * i, 44100, 16, 2) for i in (1, 2)]

    detail = AlbumDetail(summary=summary, tracks=tracks)

    assert detail.total_duration_seconds == 0.3
