from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadError

from app.downloader import MediaDownloader


def _fake_ydl(prepared_filename: str, info: dict | None = None):
    """Return a mock context-manager replacement for YoutubeDL."""
    info = info if info is not None else {"title": "Sample"}
    ctx = MagicMock()
    ctx.extract_info.return_value = info
    ctx.prepare_filename.return_value = prepared_filename
    cm = MagicMock()
    cm.__enter__.return_value = ctx
    cm.__exit__.return_value = False
    return cm, ctx


class TestBaseOpts:
    def test_creates_output_dir(self, tmp_output_dir: Path) -> None:
        target = tmp_output_dir / "nested" / "deeper"
        d = MediaDownloader(str(target))
        opts = d._base_opts()
        assert target.exists()
        assert opts["outtmpl"].startswith(str(target))
        assert opts["noplaylist"] is True
        assert opts["windowsfilenames"] is True
        assert opts["retries"] == 3
        assert opts["progress_hooks"] == []

    def test_registers_progress_callback(self, tmp_output_dir: Path) -> None:
        cb = lambda _d: None  # noqa: E731
        d = MediaDownloader(str(tmp_output_dir))
        opts = d._base_opts(progress_callback=cb)
        assert opts["progress_hooks"] == [cb]


class TestDownloadDispatch:
    @pytest.mark.parametrize(
        "fmt,expected_ext,embed_artwork",
        [
            ("mp3", "mp3", True),
            ("m4a", "m4a", True),
            ("wav", "wav", False),
            ("mp4", "mp4", False),
        ],
    )
    def test_each_format_returns_payload(
        self, tmp_output_dir: Path, fmt: str, expected_ext: str, embed_artwork: bool
    ) -> None:
        base_path = str(tmp_output_dir / "Song [abc123].webm")
        d = MediaDownloader(str(tmp_output_dir))

        cm, _ctx = _fake_ydl(base_path, info={"title": "Song"})
        with (
            patch("app.downloader.YoutubeDL", return_value=cm) as ydl_cls,
            patch.object(d, "_normalize_audio_tags") as norm,
            patch.object(d, "_embed_cover_art", return_value=(True, "")) as embed,
        ):
            result = d.download("https://youtu.be/abc", format_type=fmt)

        ydl_cls.assert_called_once()
        opts_passed = ydl_cls.call_args.args[0]
        # Postprocessor key should reference the requested format
        postprocessors = opts_passed.get("postprocessors", [])
        if fmt in ("mp3", "m4a", "wav"):
            assert postprocessors[0]["key"] == "FFmpegExtractAudio"
            assert postprocessors[0]["preferredcodec"] == fmt
        else:
            assert opts_passed["merge_output_format"] == "mp4"

        assert result["title"] == "Song"
        assert result["filepath"].endswith(f".{expected_ext}")
        if embed_artwork:
            norm.assert_called_once()
            embed.assert_called_once()
        else:
            norm.assert_not_called()
            embed.assert_not_called()

    def test_unsupported_format_raises(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        with pytest.raises(ValueError, match="Unsupported format_type"):
            d.download("https://youtu.be/abc", format_type="ogg")

    def test_passes_quality_to_postprocessor(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        cm, _ = _fake_ydl(str(tmp_output_dir / "t.webm"))
        with (
            patch("app.downloader.YoutubeDL", return_value=cm) as ydl_cls,
            patch.object(d, "_normalize_audio_tags"),
            patch.object(d, "_embed_cover_art", return_value=(True, "")),
        ):
            d.download("https://youtu.be/x", format_type="mp3", quality="320")

        opts_passed = ydl_cls.call_args.args[0]
        assert opts_passed["postprocessors"][0]["preferredquality"] == "320"


class TestFallbackStrategy:
    def test_succeeds_on_first_attempt(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        cm, _ = _fake_ydl(str(tmp_output_dir / "t.webm"))
        with patch("app.downloader.YoutubeDL", return_value=cm) as ydl_cls:
            d._try_download_with_fallback("https://youtu.be/x", d._base_opts())
        assert ydl_cls.call_count == 1

    def test_falls_back_on_403(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))

        cm_ok, _ = _fake_ydl(str(tmp_output_dir / "t.webm"))
        cm_fail = MagicMock()
        cm_fail.__enter__.side_effect = DownloadError("HTTP Error 403: Forbidden")
        cm_fail.__exit__.return_value = False

        # First call raises 403, second succeeds.
        with patch("app.downloader.YoutubeDL", side_effect=[cm_fail, cm_ok]) as ydl_cls:
            result = d._try_download_with_fallback("https://youtu.be/x", d._base_opts())
        assert ydl_cls.call_count == 2
        # Second call should have adjusted player_client to exclude more clients.
        fb_opts = ydl_cls.call_args_list[1].args[0]
        clients = fb_opts["extractor_args"]["youtube"]["player_client"]
        assert "-android" in clients
        assert result["info"]["title"] == "Sample"

    def test_propagates_non_403_errors(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        cm_fail = MagicMock()
        cm_fail.__enter__.side_effect = DownloadError("Some other failure")
        cm_fail.__exit__.return_value = False
        with patch("app.downloader.YoutubeDL", return_value=cm_fail):
            with pytest.raises(DownloadError, match="Some other failure"):
                d._try_download_with_fallback("https://youtu.be/x", d._base_opts())

    def test_uses_web_client_as_last_resort(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))

        def fail_403() -> MagicMock:
            cm = MagicMock()
            cm.__enter__.side_effect = DownloadError("HTTP Error 403: Forbidden")
            cm.__exit__.return_value = False
            return cm

        cm_ok, _ = _fake_ydl(str(tmp_output_dir / "t.webm"))
        with patch(
            "app.downloader.YoutubeDL",
            side_effect=[fail_403(), fail_403(), cm_ok],
        ) as ydl_cls:
            d._try_download_with_fallback("https://youtu.be/x", d._base_opts())
        assert ydl_cls.call_count == 3
        last_opts = ydl_cls.call_args_list[2].args[0]
        assert last_opts["extractor_args"]["youtube"]["player_client"] == ["web"]


class TestResultWithExtension:
    def test_swaps_extension(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        payload = d._result_with_extension(
            {"base_path": str(tmp_output_dir / "Song.webm"), "info": {"title": "T"}},
            "mp3",
        )
        assert payload["title"] == "T"
        assert payload["filepath"].endswith("Song.mp3")
        assert payload["artwork_embedded"] is False
        assert payload["artwork_warning"] == ""

    def test_returns_empty_filepath_when_base_missing(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        payload = d._result_with_extension({"info": {"title": "T"}}, "mp3")
        assert payload["filepath"] == ""

    def test_skips_artwork_when_no_path(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        with (
            patch.object(d, "_normalize_audio_tags") as norm,
            patch.object(d, "_embed_cover_art") as embed,
        ):
            d._result_with_extension({"info": {"title": "T"}}, "mp3", embed_artwork=True)
        norm.assert_not_called()
        embed.assert_not_called()


class TestThumbnailSelection:
    def test_picks_highest_resolution_from_list(self) -> None:
        d = MediaDownloader()
        info = {
            "thumbnails": [
                {"url": "small.jpg", "width": 120, "height": 90},
                {"url": "large.jpg", "width": 1920, "height": 1080},
                {"url": "medium.jpg", "width": 640, "height": 480},
            ]
        }
        assert d._best_thumbnail_url(info) == "large.jpg"

    def test_falls_back_to_thumbnail_field(self) -> None:
        d = MediaDownloader()
        assert d._best_thumbnail_url({"thumbnail": "fallback.jpg"}) == "fallback.jpg"

    def test_handles_no_data(self) -> None:
        d = MediaDownloader()
        assert d._best_thumbnail_url({}) == ""

    def test_skips_entries_without_url(self) -> None:
        d = MediaDownloader()
        info = {
            "thumbnails": [
                {"width": 100, "height": 100},
                {"url": "ok.jpg", "width": 50, "height": 50},
            ]
        }
        assert d._best_thumbnail_url(info) == "ok.jpg"


class TestEmbedCoverArt:
    def test_returns_warning_when_file_missing(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        ok, warning = d._embed_cover_art(str(tmp_output_dir / "missing.mp3"), {}, "mp3")
        assert ok is False
        assert "not found" in warning.lower()

    def test_returns_warning_when_no_thumbnail(self, tmp_output_dir: Path) -> None:
        path = tmp_output_dir / "song.mp3"
        path.write_bytes(b"\x00")
        d = MediaDownloader(str(tmp_output_dir))
        with patch.object(d, "_fetch_thumbnail_bytes", return_value=None):
            ok, warning = d._embed_cover_art(str(path), {}, "mp3")
        assert ok is False
        assert "thumbnail" in warning.lower()

    def test_unsupported_extension_returns_warning(self, tmp_output_dir: Path) -> None:
        path = tmp_output_dir / "song.wav"
        path.write_bytes(b"RIFF")
        d = MediaDownloader(str(tmp_output_dir))
        with (
            patch.object(d, "_fetch_thumbnail_bytes", return_value=b"raw"),
            patch.object(d, "_prepare_cover_jpeg", return_value=b"jpeg"),
        ):
            ok, warning = d._embed_cover_art(str(path), {}, "wav")
        assert ok is False
        assert "not supported" in warning.lower()


class TestNormalizeAudioTags:
    def test_silently_returns_when_file_missing(self, tmp_output_dir: Path) -> None:
        d = MediaDownloader(str(tmp_output_dir))
        # Should not raise.
        d._normalize_audio_tags(str(tmp_output_dir / "ghost.mp3"), {"title": "x"}, "mp3")

    def test_swallows_mutagen_errors(self, tmp_output_dir: Path) -> None:
        path = tmp_output_dir / "song.mp3"
        path.write_bytes(b"\x00\x00\x00")
        d = MediaDownloader(str(tmp_output_dir))
        with patch("app.downloader.ID3", side_effect=RuntimeError("boom")):
            # Should not propagate.
            d._normalize_audio_tags(str(path), {"title": "x"}, "mp3")


class TestMetadataText:
    def test_strips_value(self) -> None:
        d = MediaDownloader()
        assert d._metadata_text({"title": "  hi  "}, "title") == "hi"

    def test_returns_empty_for_missing_key(self) -> None:
        d = MediaDownloader()
        assert d._metadata_text({}, "title") == ""

    def test_returns_empty_for_non_dict(self) -> None:
        d = MediaDownloader()
        assert d._metadata_text(None, "title") == ""  # type: ignore[arg-type]


class TestFallbackAlbum:
    def test_uses_album_when_present(self) -> None:
        d = MediaDownloader()
        assert d._fallback_album({"album": "A", "title": "T"}) == "A"

    def test_falls_back_to_playlist_title(self) -> None:
        d = MediaDownloader()
        assert d._fallback_album({"playlist_title": "PL", "title": "T"}) == "PL"

    def test_falls_back_to_title(self) -> None:
        d = MediaDownloader()
        assert d._fallback_album({"title": "T"}) == "T"

    def test_returns_empty_when_nothing_available(self) -> None:
        d = MediaDownloader()
        assert d._fallback_album({}) == ""


class TestSponsorBlockInjection:
    def _capture_opts(self, tmp_output_dir: Path, *, fmt: str, sponsorblock: bool):
        d = MediaDownloader(str(tmp_output_dir))
        cm, _ = _fake_ydl(str(tmp_output_dir / "x.webm"))
        with (
            patch("app.downloader.YoutubeDL", return_value=cm) as ydl_cls,
            patch.object(d, "_normalize_audio_tags"),
            patch.object(d, "_embed_cover_art", return_value=(True, "")),
        ):
            d.download("https://youtu.be/x", format_type=fmt, sponsorblock=sponsorblock)
        return ydl_cls.call_args.args[0]

    def test_does_not_inject_when_disabled(self, tmp_output_dir: Path) -> None:
        opts = self._capture_opts(tmp_output_dir, fmt="mp3", sponsorblock=False)
        keys = [pp.get("key") for pp in opts.get("postprocessors", [])]
        assert "SponsorBlock" not in keys
        assert "ModifyChapters" not in keys

    @pytest.mark.parametrize("fmt", ["mp3", "m4a", "wav", "mp4"])
    def test_injects_sponsorblock_postprocessors(self, tmp_output_dir: Path, fmt: str) -> None:
        opts = self._capture_opts(tmp_output_dir, fmt=fmt, sponsorblock=True)
        keys = [pp.get("key") for pp in opts.get("postprocessors", [])]
        assert keys[0] == "SponsorBlock"
        assert "ModifyChapters" in keys

    def test_uses_expected_categories(self, tmp_output_dir: Path) -> None:
        opts = self._capture_opts(tmp_output_dir, fmt="mp3", sponsorblock=True)
        sponsor_pp = opts["postprocessors"][0]
        assert sponsor_pp["categories"] == [
            "sponsor",
            "selfpromo",
            "intro",
            "outro",
            "music_offtopic",
        ]


class TestTrimInjection:
    def _capture_opts(self, tmp_output_dir: Path, *, trim):
        d = MediaDownloader(str(tmp_output_dir))
        cm, _ = _fake_ydl(str(tmp_output_dir / "x.webm"))
        with (
            patch("app.downloader.YoutubeDL", return_value=cm) as ydl_cls,
            patch.object(d, "_normalize_audio_tags"),
            patch.object(d, "_embed_cover_art", return_value=(True, "")),
        ):
            d.download("https://youtu.be/x", format_type="mp3", trim=trim)
        return ydl_cls.call_args.args[0]

    def test_no_ranges_when_trim_absent(self, tmp_output_dir: Path) -> None:
        opts = self._capture_opts(tmp_output_dir, trim=None)
        assert "download_ranges" not in opts
        assert "force_keyframes_at_cuts" not in opts

    def test_no_ranges_when_both_bounds_none(self, tmp_output_dir: Path) -> None:
        opts = self._capture_opts(tmp_output_dir, trim=(None, None))
        assert "download_ranges" not in opts

    def test_injects_ranges_when_trim_provided(self, tmp_output_dir: Path) -> None:
        opts = self._capture_opts(tmp_output_dir, trim=(30, 90))
        assert callable(opts["download_ranges"])
        section = opts["download_ranges"](None, None)
        assert section == [{"start_time": 30.0, "end_time": 90.0}]
        assert opts["force_keyframes_at_cuts"] is True

    def test_supports_open_ended_start(self, tmp_output_dir: Path) -> None:
        opts = self._capture_opts(tmp_output_dir, trim=(None, 90))
        section = opts["download_ranges"](None, None)
        assert section == [{"start_time": 0.0, "end_time": 90.0}]

    def test_supports_open_ended_end(self, tmp_output_dir: Path) -> None:
        opts = self._capture_opts(tmp_output_dir, trim=(30, None))
        section = opts["download_ranges"](None, None)
        assert section == [{"start_time": 30.0, "end_time": None}]
