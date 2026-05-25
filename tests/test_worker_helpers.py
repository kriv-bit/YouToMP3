from __future__ import annotations

from app.ui.worker import (
    _best_thumbnail_url,
    _display_title,
    _fetch_thumbnail_bytes,
    _metadata_payload,
    _needs_metadata,
)


class TestBestThumbnailUrl:
    def test_prefers_single_thumbnail_field(self) -> None:
        info = {"thumbnail": "https://img/a.jpg", "thumbnails": [{"url": "https://img/b.jpg"}]}
        assert _best_thumbnail_url(info) == "https://img/a.jpg"

    def test_falls_back_to_thumbnails_list_last_item(self) -> None:
        info = {
            "thumbnails": [
                {"url": "https://img/small.jpg"},
                {"url": "https://img/large.jpg"},
            ]
        }
        # Iteration is reversed → last valid entry returned first.
        assert _best_thumbnail_url(info) == "https://img/large.jpg"

    def test_skips_invalid_entries_in_thumbnails(self) -> None:
        info = {
            "thumbnails": [
                {"url": "https://img/ok.jpg"},
                "not-a-dict",
                {"no_url_key": True},
            ]
        }
        assert _best_thumbnail_url(info) == "https://img/ok.jpg"

    def test_returns_empty_when_no_thumbnail(self) -> None:
        assert _best_thumbnail_url({}) == ""

    def test_handles_non_dict_input(self) -> None:
        assert _best_thumbnail_url(None) == ""  # type: ignore[arg-type]
        assert _best_thumbnail_url("nope") == ""  # type: ignore[arg-type]


class TestDisplayTitle:
    def test_returns_title_when_present(self) -> None:
        assert _display_title({"title": "Cool Song"}, "fallback") == "Cool Song"

    def test_strips_whitespace(self) -> None:
        assert _display_title({"title": "  Padded  "}, "fallback") == "Padded"

    def test_uses_fallback_when_title_missing(self) -> None:
        assert _display_title({}, "fallback-url") == "fallback-url"

    def test_uses_fallback_when_title_blank(self) -> None:
        assert _display_title({"title": "   "}, "fallback-url") == "fallback-url"

    def test_handles_non_dict(self) -> None:
        assert _display_title(None, "fb") == "fb"  # type: ignore[arg-type]


class TestMetadataPayload:
    def test_includes_all_fields(self) -> None:
        info = {
            "title": "T",
            "uploader": "U",
            "duration": 240,
            "thumbnail": "https://img/x.jpg",
        }
        payload = _metadata_payload(info, "fallback", thumbnail_data=b"\x00\x01")
        assert payload == {
            "title": "T",
            "uploader": "U",
            "duration": 240,
            "thumbnail": "https://img/x.jpg",
            "thumbnail_data": b"\x00\x01",
        }

    def test_uploader_falls_back_to_channel(self) -> None:
        info = {"title": "T", "channel": "Some Channel"}
        payload = _metadata_payload(info, "fb")
        assert payload["uploader"] == "Some Channel"

    def test_empty_uploader_when_neither_field_present(self) -> None:
        payload = _metadata_payload({"title": "T"}, "fb")
        assert payload["uploader"] == ""
        assert payload["thumbnail_data"] is None


class TestNeedsMetadata:
    def test_true_when_title_missing(self) -> None:
        assert _needs_metadata({"thumbnail": "x", "uploader": "y"}) is True

    def test_true_when_thumbnail_missing(self) -> None:
        assert _needs_metadata({"title": "x", "uploader": "y"}) is True

    def test_true_when_uploader_missing(self) -> None:
        assert _needs_metadata({"title": "x", "thumbnail": "y"}) is True

    def test_false_when_all_present(self) -> None:
        meta = {"title": "x", "thumbnail": "y", "uploader": "z"}
        assert _needs_metadata(meta) is False


class TestFetchThumbnailBytes:
    def test_returns_none_for_empty_url(self) -> None:
        assert _fetch_thumbnail_bytes("") is None

    def test_returns_none_when_request_raises(self, monkeypatch) -> None:
        def boom(*_a, **_kw):
            raise OSError("network down")

        monkeypatch.setattr("app.ui.worker.urlopen", boom)
        assert _fetch_thumbnail_bytes("https://example.com/x.jpg") is None
