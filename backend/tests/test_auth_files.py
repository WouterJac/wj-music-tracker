from datetime import UTC, datetime, timedelta
from pathlib import Path

from wj_music.storage.auth_files import FilePairingCodes, load_or_create_token

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def test_a_token_is_created_once_and_then_reused(tmp_path: Path) -> None:
    path = tmp_path / "data" / "auth_token"

    first = load_or_create_token(path)
    second = load_or_create_token(path)

    assert first == second
    assert len(first) >= 32
    assert path.read_text(encoding="utf-8").strip() == first


def test_different_data_directories_get_different_tokens(tmp_path: Path) -> None:
    assert load_or_create_token(tmp_path / "a") != load_or_create_token(tmp_path / "b")


def test_a_code_can_be_redeemed_once(tmp_path: Path) -> None:
    codes = FilePairingCodes(tmp_path / "pairing.json")
    codes.issue("ABCD2345", NOW + timedelta(minutes=5))

    assert codes.redeem("ABCD2345", NOW)
    assert not codes.redeem("ABCD2345", NOW)


def test_a_wrong_code_does_not_use_up_the_real_one(tmp_path: Path) -> None:
    codes = FilePairingCodes(tmp_path / "pairing.json")
    codes.issue("ABCD2345", NOW + timedelta(minutes=5))

    assert not codes.redeem("WRONG999", NOW)
    assert codes.redeem("ABCD2345", NOW)


def test_an_expired_code_is_refused(tmp_path: Path) -> None:
    codes = FilePairingCodes(tmp_path / "pairing.json")
    codes.issue("ABCD2345", NOW + timedelta(minutes=5))

    assert not codes.redeem("ABCD2345", NOW + timedelta(minutes=5, seconds=1))


def test_nothing_to_redeem_when_no_code_was_issued(tmp_path: Path) -> None:
    assert not FilePairingCodes(tmp_path / "pairing.json").redeem("ABCD2345", NOW)


def test_issuing_a_new_code_replaces_the_old_one(tmp_path: Path) -> None:
    codes = FilePairingCodes(tmp_path / "pairing.json")
    codes.issue("ABCD2345", NOW + timedelta(minutes=5))
    codes.issue("WXYZ6789", NOW + timedelta(minutes=5))

    assert not codes.redeem("ABCD2345", NOW)
    assert codes.redeem("WXYZ6789", NOW)


def test_the_code_itself_is_not_stored(tmp_path: Path) -> None:
    path = tmp_path / "pairing.json"
    FilePairingCodes(path).issue("ABCD2345", NOW + timedelta(minutes=5))

    assert "ABCD2345" not in path.read_text(encoding="utf-8")
