from __future__ import annotations

import pytest

from app.timestamp import (
    TimestampError,
    format_timestamp,
    parse_timestamp,
    validate_range,
)


class TestParseTimestamp:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("0", 0.0),
            ("30", 30.0),
            ("90", 90.0),
            ("1:30", 90.0),
            ("0:01", 1.0),
            ("10:00", 600.0),
            ("1:00:00", 3600.0),
            ("1:30:00", 5400.0),
            ("0:0:5", 5.0),
            ("0:0:5.5", 5.5),
            ("0:1:30.25", 90.25),
        ],
    )
    def test_parses_canonical_values(self, raw: str, expected: float) -> None:
        assert parse_timestamp(raw) == pytest.approx(expected)

    def test_returns_none_for_empty(self) -> None:
        assert parse_timestamp(None) is None
        assert parse_timestamp("") is None
        assert parse_timestamp("   ") is None

    @pytest.mark.parametrize(
        "raw",
        [
            "abc",
            "1:abc",
            "1:2:3:4",
            "-5",
            "1:-30",
            "1:60:00",
            "0:30.5:00",
        ],
    )
    def test_rejects_invalid_input(self, raw: str) -> None:
        with pytest.raises(TimestampError):
            parse_timestamp(raw)


class TestFormatTimestamp:
    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (None, ""),
            (0, "0:00"),
            (5, "0:05"),
            (90, "1:30"),
            (3600, "1:00:00"),
            (3725, "1:02:05"),
            (-10, "0:00"),
        ],
    )
    def test_formats(self, seconds, expected) -> None:
        assert format_timestamp(seconds) == expected


class TestValidateRange:
    def test_passes_through_valid_range(self) -> None:
        assert validate_range(10, 30) == (10, 30)

    def test_allows_one_side_open(self) -> None:
        assert validate_range(None, 30) == (None, 30)
        assert validate_range(10, None) == (10, None)
        assert validate_range(None, None) == (None, None)

    def test_rejects_negative(self) -> None:
        with pytest.raises(TimestampError):
            validate_range(-1, 5)
        with pytest.raises(TimestampError):
            validate_range(0, -1)

    def test_rejects_end_not_after_start(self) -> None:
        with pytest.raises(TimestampError):
            validate_range(30, 30)
        with pytest.raises(TimestampError):
            validate_range(30, 10)
