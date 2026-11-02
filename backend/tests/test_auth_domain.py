from datetime import UTC, datetime, timedelta

from wj_music.domain.auth import (
    CODE_ALPHABET,
    CODE_LENGTH,
    FailureLimiter,
    format_code,
    new_pairing_code,
    normalise_code,
)

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def test_pairing_codes_are_random_and_use_the_unambiguous_alphabet() -> None:
    codes = {new_pairing_code() for _ in range(50)}

    assert len(codes) == 50
    for code in codes:
        assert len(code) == CODE_LENGTH
        assert set(code) <= set(CODE_ALPHABET)


def test_the_alphabet_leaves_out_look_alike_characters() -> None:
    assert not set("01OIL") & set(CODE_ALPHABET)


def test_codes_are_shown_in_two_groups_and_read_back_forgivingly() -> None:
    assert format_code("ABCD2345") == "ABCD-2345"
    assert normalise_code(" abcd-2345 ") == "ABCD2345"


def test_failures_below_the_limit_do_not_block() -> None:
    limiter = FailureLimiter(max_failures=3, window=timedelta(seconds=60))
    limiter.record_failure("phone", NOW)
    limiter.record_failure("phone", NOW)

    assert not limiter.is_blocked("phone", NOW)


def test_reaching_the_limit_blocks_only_that_client() -> None:
    limiter = FailureLimiter(max_failures=3, window=timedelta(seconds=60))
    for _ in range(3):
        limiter.record_failure("phone", NOW)

    assert limiter.is_blocked("phone", NOW)
    assert not limiter.is_blocked("laptop", NOW)


def test_failures_age_out_of_the_window() -> None:
    limiter = FailureLimiter(max_failures=3, window=timedelta(seconds=60))
    for _ in range(3):
        limiter.record_failure("phone", NOW)

    assert limiter.is_blocked("phone", NOW + timedelta(seconds=59))
    assert not limiter.is_blocked("phone", NOW + timedelta(seconds=61))
