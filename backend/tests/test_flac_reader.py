from pathlib import Path

import pytest

from flac_builder import build_flac
from wj_music.scanner.errors import InvalidFlacError
from wj_music.scanner.flac_reader import read_flac


def write_flac(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def test_reads_vorbis_comment_tags(tmp_path: Path) -> None:
    path = write_flac(
        tmp_path / "track.flac",
        build_flac(
            tags={
                "TITLE": ["Heroes"],
                "ARTIST": ["David Bowie"],
                "ALBUMARTIST": ["David Bowie"],
                "ALBUM": ['"Heroes"'],
                "TRACKNUMBER": ["2"],
                "DISCNUMBER": ["1"],
                "DATE": ["1977"],
                "GENRE": ["Rock"],
                "COMPOSER": ["Brian Eno"],
                "LABEL": ["RCA"],
                "LYRICS": ["I, I will be king"],
            }
        ),
    )

    tags = read_flac(path).tags

    assert tags.title == "Heroes"
    assert tags.artist == "David Bowie"
    assert tags.albumartist == "David Bowie"
    assert tags.album == '"Heroes"'
    assert tags.tracknumber == "2"
    assert tags.discnumber == "1"
    assert tags.date == "1977"
    assert tags.genre == "Rock"
    assert tags.composer == "Brian Eno"
    assert tags.label == "RCA"
    assert tags.lyrics == "I, I will be king"


def test_missing_tags_are_none(tmp_path: Path) -> None:
    path = write_flac(tmp_path / "bare.flac", build_flac(tags={"TITLE": ["Only title"]}))

    tags = read_flac(path).tags

    assert tags.title == "Only title"
    assert tags.artist is None
    assert tags.lyrics is None


def test_file_without_vorbis_comment_block_has_no_tags(tmp_path: Path) -> None:
    path = write_flac(tmp_path / "no-tags.flac", build_flac())

    tags = read_flac(path).tags

    assert tags.title is None
    assert tags.artist is None


def test_reads_stream_info(tmp_path: Path) -> None:
    data = build_flac(
        sample_rate=48000,
        channels=2,
        bits_per_sample=24,
        total_samples=48000 * 90,
    )
    path = write_flac(tmp_path / "hires.flac", data)

    audio = read_flac(path).audio

    assert audio.sample_rate == 48000
    assert audio.bit_depth == 24
    assert audio.channels == 2
    assert audio.duration_seconds == pytest.approx(90.0)
    assert audio.file_size_bytes == len(data)


def test_reads_mono_16_bit_stream_info(tmp_path: Path) -> None:
    path = write_flac(
        tmp_path / "mono.flac",
        build_flac(channels=1, bits_per_sample=16, sample_rate=22050, total_samples=22050),
    )

    audio = read_flac(path).audio

    assert audio.channels == 1
    assert audio.bit_depth == 16
    assert audio.sample_rate == 22050
    assert audio.duration_seconds == pytest.approx(1.0)


def test_result_points_at_the_file(tmp_path: Path) -> None:
    path = write_flac(tmp_path / "track.flac", build_flac())

    assert read_flac(path).path == path


def test_reading_does_not_modify_the_file(tmp_path: Path) -> None:
    data = build_flac(tags={"TITLE": ["Untouched"]})
    path = write_flac(tmp_path / "track.flac", data)

    read_flac(path)

    assert path.read_bytes() == data


def test_non_flac_file_raises_invalid_flac_error(tmp_path: Path) -> None:
    path = write_flac(tmp_path / "notes.flac", b"this is not audio at all")

    with pytest.raises(InvalidFlacError, match="notes.flac"):
        read_flac(path)


def test_truncated_flac_raises_invalid_flac_error(tmp_path: Path) -> None:
    data = build_flac(tags={"TITLE": ["Cut short"]})
    path = write_flac(tmp_path / "truncated.flac", data[:20])

    with pytest.raises(InvalidFlacError):
        read_flac(path)


def test_missing_file_is_not_reported_as_invalid_flac(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_flac(tmp_path / "gone.flac")
