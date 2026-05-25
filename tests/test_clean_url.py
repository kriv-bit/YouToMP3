from __future__ import annotations

import pytest

from app.downloader import clean_url


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://youtu.be/abc123", "https://youtu.be/abc123"),
        ("  https://youtu.be/abc123  ", "https://youtu.be/abc123"),
        (
            "https://www.youtube.com/watch?v=abc123&si=tracking",
            "https://www.youtube.com/watch?v=abc123",
        ),
        (
            "https://www.youtube.com/watch?v=abc123&feature=share",
            "https://www.youtube.com/watch?v=abc123",
        ),
        (
            "https://www.youtube.com/watch?v=abc123&utm_source=x&utm_medium=y&utm_campaign=z",
            "https://www.youtube.com/watch?v=abc123",
        ),
        (
            "https://www.youtube.com/watch?v=abc123&list=PL1&si=x",
            "https://www.youtube.com/watch?v=abc123&list=PL1",
        ),
    ],
)
def test_clean_url_strips_tracking_params(raw: str, expected: str) -> None:
    assert clean_url(raw) == expected


def test_clean_url_keeps_unknown_params() -> None:
    url = "https://www.youtube.com/watch?v=abc&t=42s"
    assert clean_url(url) == url


def test_clean_url_returns_input_when_no_scheme() -> None:
    assert clean_url("not-a-url") == "not-a-url"
