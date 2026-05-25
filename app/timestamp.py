"""Tiny helpers for parsing ``MM:SS`` style timestamps."""

from __future__ import annotations


class TimestampError(ValueError):
    """Raised when a timestamp string cannot be parsed."""


def parse_timestamp(value: str | None) -> float | None:
    """Parse ``SS``, ``MM:SS`` or ``HH:MM:SS`` into seconds.

    Empty/None returns None (means "no bound here"). Accepts fractional seconds.
    Raises :class:`TimestampError` for malformed input.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    parts = text.split(":")
    if len(parts) > 3:
        raise TimestampError(f"too many ':' in timestamp: {value!r}")

    try:
        components = [float(p) for p in parts]
    except ValueError as exc:
        raise TimestampError(f"non-numeric timestamp: {value!r}") from exc

    for c in components[:-1]:
        if not c.is_integer():
            raise TimestampError(f"only seconds may be fractional: {value!r}")
        if c < 0:
            raise TimestampError(f"negative component in timestamp: {value!r}")

    if components[-1] < 0:
        raise TimestampError(f"negative component in timestamp: {value!r}")

    if len(components) == 1:
        return components[0]
    if len(components) == 2:
        minutes, seconds = components
        return minutes * 60 + seconds
    hours, minutes, seconds = components
    if minutes >= 60 or seconds >= 60:
        raise TimestampError(f"minutes/seconds must be < 60: {value!r}")
    return hours * 3600 + minutes * 60 + seconds


def format_timestamp(seconds: float | int | None) -> str:
    """Format ``seconds`` back into ``HH:MM:SS`` (or ``MM:SS`` when short)."""
    if seconds is None:
        return ""
    total = int(round(float(seconds)))
    if total < 0:
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def validate_range(
    start: float | None, end: float | None
) -> tuple[float | None, float | None]:
    """Sanity-check a trim range. Returns the normalized (start, end) tuple."""
    if start is not None and start < 0:
        raise TimestampError("start must be >= 0")
    if end is not None and end < 0:
        raise TimestampError("end must be >= 0")
    if start is not None and end is not None and end <= start:
        raise TimestampError("end must be greater than start")
    return start, end
