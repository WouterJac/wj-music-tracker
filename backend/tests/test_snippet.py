from wj_music.domain.snippet import make_snippet


def test_surrounds_the_match_with_context_and_ellipses() -> None:
    text = "a" * 100 + " needle " + "b" * 100

    snippet = make_snippet(text, "needle", radius=10)

    assert snippet == "…" + "a" * 9 + " needle " + "b" * 9 + "…"


def test_match_near_the_start_has_no_leading_ellipsis() -> None:
    snippet = make_snippet("needle " + "b" * 100, "needle", radius=10)

    assert snippet == "needle " + "b" * 9 + "…"


def test_match_near_the_end_has_no_trailing_ellipsis() -> None:
    snippet = make_snippet("a" * 100 + " needle", "needle", radius=10)

    assert snippet == "…" + "a" * 9 + " needle"


def test_short_text_is_returned_whole() -> None:
    assert make_snippet("short text", "text") == "short text"


def test_lines_are_joined_with_slashes() -> None:
    assert make_snippet("one\ntwo\nthree", "two") == "one / two / three"


def test_blank_lines_and_extra_spaces_collapse() -> None:
    assert make_snippet("one\n\n\n  two   words", "two") == "one / two words"


def test_matching_ignores_case_but_keeps_the_original_text() -> None:
    assert make_snippet("Hello World", "WORLD") == "Hello World"


def test_matching_handles_non_ascii_case() -> None:
    assert make_snippet("Va à l'ÉCOLE", "école") == "Va à l'ÉCOLE"


def test_query_with_regex_characters_matches_literally() -> None:
    assert make_snippet("is it (really) so?", "(really)") == "is it (really) so?"


def test_without_a_match_the_start_of_the_text_is_shown() -> None:
    snippet = make_snippet("x" * 200, "needle", radius=10)

    assert snippet == "x" * 20 + "…"
