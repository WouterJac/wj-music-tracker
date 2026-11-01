import pytest

from wj_music.domain.lyrics import (
    LyricLine,
    Lyrics,
    has_timestamps,
    lrc_to_plain,
    parse_lrc,
    resolve_lyrics,
)


class TestParseLrc:
    def test_reads_time_and_text(self) -> None:
        assert parse_lrc("[00:12.00]Hello") == [LyricLine(12.0, "Hello")]

    def test_minutes_may_exceed_59(self) -> None:
        assert parse_lrc("[75:30.50]Late") == [LyricLine(4530.5, "Late")]

    @pytest.mark.parametrize(
        ("stamp", "seconds"),
        [("[01:02]", 62.0), ("[00:01.5]", 1.5), ("[00:01.50]", 1.5), ("[00:01.250]", 1.25)],
    )
    def test_fraction_has_one_to_three_digits_or_none(self, stamp: str, seconds: float) -> None:
        assert parse_lrc(f"{stamp}x")[0].time_seconds == seconds

    def test_several_timestamps_repeat_the_line(self) -> None:
        lines = parse_lrc("[00:20.00][00:10.00]Chorus")

        assert lines == [LyricLine(10.0, "Chorus"), LyricLine(20.0, "Chorus")]

    def test_lines_are_sorted_by_time(self) -> None:
        lines = parse_lrc("[00:30.00]c\n[00:10.00]a\n[00:20.00]b")

        assert [line.text for line in lines] == ["a", "b", "c"]

    def test_metadata_tags_are_not_lyrics(self) -> None:
        text = "[ar:Artist]\n[ti:Title]\n[al:Album]\n[00:01.00]Only line"

        assert parse_lrc(text) == [LyricLine(1.0, "Only line")]

    @pytest.mark.parametrize(("offset", "expected"), [("+1000", 4.0), ("-500", 5.5), ("0", 5.0)])
    def test_offset_shifts_every_line(self, offset: str, expected: float) -> None:
        assert parse_lrc(f"[offset:{offset}]\n[00:05.00]a") == [LyricLine(expected, "a")]

    def test_offset_never_makes_a_time_negative(self) -> None:
        assert parse_lrc("[offset:+9000]\n[00:05.00]a")[0].time_seconds == 0.0

    def test_word_timing_tags_are_removed_from_the_text(self) -> None:
        assert parse_lrc("[00:01.00]<00:01.00>Hel<00:01.50>lo")[0].text == "Hello"

    def test_empty_text_is_kept_as_an_instrumental_break(self) -> None:
        assert parse_lrc("[00:05.00]") == [LyricLine(5.0, "")]

    def test_handles_windows_line_endings(self) -> None:
        assert [line.text for line in parse_lrc("[00:01.00]a\r\n[00:02.00]b\r\n")] == ["a", "b"]

    def test_text_without_timestamps_has_no_lines(self) -> None:
        assert parse_lrc("Just words\nand more words") == []


class TestHasTimestamps:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [("[00:01.00]a", True), ("a\n[12:34]b", True), ("plain words", False), ("[ar:x]", False)],
    )
    def test_detects_lrc_timestamps(self, text: str, expected: bool) -> None:
        assert has_timestamps(text) is expected


class TestLrcToPlain:
    def test_drops_timestamps_and_metadata(self) -> None:
        text = "[ar:X]\n[00:01.00]Line one\n[00:02.00]Line two"

        assert lrc_to_plain(text) == "Line one\nLine two"

    def test_keeps_blank_lines_between_stanzas(self) -> None:
        assert lrc_to_plain("[00:01.00]a\n[00:02.00]\n[00:03.00]b") == "a\n\nb"

    def test_repeated_timestamps_give_repeated_text_in_time_order(self) -> None:
        assert (
            lrc_to_plain("[00:20.00][00:10.00]Chorus\n[00:15.00]Verse") == "Chorus\nVerse\nChorus"
        )


class TestResolveLyrics:
    def resolve(self, **sources: str | None) -> Lyrics | None:
        return resolve_lyrics(
            lyrics=sources.get("lyrics"),
            unsynced=sources.get("unsynced"),
            synced=sources.get("synced"),
            sidecar=sources.get("sidecar"),
        )

    def test_nothing_means_no_lyrics(self) -> None:
        assert self.resolve() is None

    def test_blank_sources_mean_no_lyrics(self) -> None:
        assert self.resolve(lyrics="  \n ", sidecar="") is None

    def test_plain_lyrics_tag_is_unsynced(self) -> None:
        assert self.resolve(lyrics="la la") == Lyrics(plain="la la", synced_lrc=None)

    def test_lyrics_tag_with_timestamps_is_synced_and_plain_is_derived(self) -> None:
        assert self.resolve(lyrics="[00:01.00]la") == Lyrics(plain="la", synced_lrc="[00:01.00]la")

    def test_unsynced_and_synced_tags_are_both_kept(self) -> None:
        result = self.resolve(unsynced="words", synced="[00:01.00]words")

        assert result == Lyrics(plain="words", synced_lrc="[00:01.00]words")

    def test_synced_tag_alone_gives_derived_plain_text(self) -> None:
        assert self.resolve(synced="[00:01.00]a\n[00:02.00]b") == Lyrics(
            plain="a\nb", synced_lrc="[00:01.00]a\n[00:02.00]b"
        )

    def test_sidecar_with_timestamps_is_synced(self) -> None:
        assert self.resolve(sidecar="[00:01.00]a") == Lyrics(plain="a", synced_lrc="[00:01.00]a")

    def test_sidecar_without_timestamps_is_unsynced(self) -> None:
        assert self.resolve(sidecar="just words") == Lyrics(plain="just words", synced_lrc=None)

    def test_embedded_plain_wins_over_sidecar_plain(self) -> None:
        result = self.resolve(lyrics="embedded", sidecar="sidecar words")

        assert result == Lyrics(plain="embedded", synced_lrc=None)

    def test_sidecar_adds_synced_lyrics_to_embedded_plain_lyrics(self) -> None:
        result = self.resolve(lyrics="embedded", sidecar="[00:01.00]sidecar")

        assert result == Lyrics(plain="embedded", synced_lrc="[00:01.00]sidecar")

    def test_embedded_synced_wins_over_sidecar_synced(self) -> None:
        result = self.resolve(synced="[00:01.00]embedded", sidecar="[00:01.00]sidecar")

        assert result is not None
        assert result.synced_lrc == "[00:01.00]embedded"

    def test_surrounding_whitespace_is_trimmed(self) -> None:
        assert self.resolve(lyrics="\n  la la  \n") == Lyrics(plain="la la", synced_lrc=None)


class TestLineEndings:
    def test_windows_line_endings_are_normalised(self) -> None:
        result = resolve_lyrics(
            lyrics=None, unsynced=None, synced=None, sidecar="[00:01.00]a\r\n[00:02.00]b\r\n"
        )

        assert result == Lyrics(plain="a\nb", synced_lrc="[00:01.00]a\n[00:02.00]b")

    def test_old_mac_line_endings_are_normalised(self) -> None:
        result = resolve_lyrics(lyrics="one\rtwo", unsynced=None, synced=None, sidecar=None)

        assert result == Lyrics(plain="one\ntwo", synced_lrc=None)
