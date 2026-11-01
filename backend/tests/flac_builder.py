"""Builds minimal FLAC files in memory. Tests use these instead of real audio."""

import struct
from collections.abc import Mapping, Sequence

FLAC_MARKER = b"fLaC"
BLOCK_STREAMINFO = 0
BLOCK_VORBIS_COMMENT = 4


def _block(block_type: int, body: bytes, *, last: bool) -> bytes:
    header = (0x80 if last else 0x00) | block_type
    return bytes([header]) + len(body).to_bytes(3, "big") + body


def _streaminfo(
    *,
    sample_rate: int,
    channels: int,
    bits_per_sample: int,
    total_samples: int,
) -> bytes:
    packed = (
        (sample_rate << 44) | ((channels - 1) << 41) | ((bits_per_sample - 1) << 36) | total_samples
    )
    block_sizes = struct.pack(">HH", 4096, 4096)
    frame_sizes = bytes(6)
    md5 = bytes(16)
    return block_sizes + frame_sizes + packed.to_bytes(8, "big") + md5


def _vorbis_comment(tags: Mapping[str, Sequence[str]]) -> bytes:
    vendor = b"wj-music test"
    entries = [f"{key}={value}".encode() for key, values in tags.items() for value in values]
    body = struct.pack("<I", len(vendor)) + vendor + struct.pack("<I", len(entries))
    for entry in entries:
        body += struct.pack("<I", len(entry)) + entry
    return body


def build_flac(
    *,
    tags: Mapping[str, Sequence[str]] | None = None,
    sample_rate: int = 44100,
    channels: int = 2,
    bits_per_sample: int = 16,
    total_samples: int = 44100 * 180,
) -> bytes:
    """Return a FLAC stream with STREAMINFO and Vorbis comments but no audio frames."""
    streaminfo = _streaminfo(
        sample_rate=sample_rate,
        channels=channels,
        bits_per_sample=bits_per_sample,
        total_samples=total_samples,
    )
    blocks = [_block(BLOCK_STREAMINFO, streaminfo, last=tags is None)]
    if tags is not None:
        blocks.append(_block(BLOCK_VORBIS_COMMENT, _vorbis_comment(tags), last=True))
    return FLAC_MARKER + b"".join(blocks)
