from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


def clean_url(url: str) -> str:
    """Remove tracking params like ?si=... that sometimes cause weirdness."""
    u = url.strip()
    try:
        p = urlparse(u)
        if not p.scheme:
            return u
        qs = parse_qs(p.query, keep_blank_values=True)

        # strip common tracking params
        for k in ("si", "feature", "utm_source", "utm_medium", "utm_campaign"):
            qs.pop(k, None)

        # rebuild query
        new_query = urlencode({k: v for k, v in qs.items()}, doseq=True)
        return urlunparse(p._replace(query=new_query))
    except Exception:
        return u


class MediaDownloader:
    def __init__(self, output_path: str = "downloads"):
        self.output_path = output_path

    def _base_opts(self, progress_callback=None) -> dict:
        out_dir = Path(self.output_path)
        out_dir.mkdir(parents=True, exist_ok=True)

        return {
            "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "windowsfilenames": True,
            "retries": 3,
            "progress_hooks": [progress_callback] if progress_callback else [],
            #  no ANSI color codes in exception/log text
            "color": "never",  # :contentReference[oaicite:5]{index=5}
            #  more "browser-like" headers helps sometimes
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
            # YouTube client selection. Excluding buggy clients is supported
            #    (you can prefix with '-' to exclude). :contentReference[oaicite:6]{index=6}
            "extractor_args": {
                "youtube": {
                    # default clients, but exclude android_sdkless (common 403 culprit)
                    "player_client": ["default", "-android_sdkless"],
                }
            },
        }

    def download(self, url: str, format_type: str = "mp3", quality: str = "192", progress_callback=None):
        url = clean_url(url)
        base = self._base_opts(progress_callback=progress_callback)

        if format_type == "mp3":
            opts = {
                **base,
                "format": "bestaudio/best",
                "writethumbnail": True,
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": str(quality)},
                    {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
                    {"key": "EmbedThumbnail"},
                    {"key": "FFmpegMetadata"},
                ],
                "postprocessor_args": ["-id3v2_version", "3"],
            }
            r = self._try_download_with_fallback(url, opts)
            base_path = r.get("base_path", "")
            final_path = str(Path(base_path).with_suffix(".mp3")) if base_path else ""
            return {"title": r.get("info", {}).get("title", ""), "filepath": final_path}

        elif format_type == "m4a":
            opts = {
                **base,
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": str(quality)},
                    {"key": "FFmpegMetadata"},
                ],
            }
            self._try_download_with_fallback(url, opts)

        elif format_type == "wav":
            opts = {
                **base,
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "wav"},
                    {"key": "FFmpegMetadata"},
                ],
            }
            self._try_download_with_fallback(url, opts)

        elif format_type == "mp4":
            opts = {
                **base,
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "postprocessors": [{"key": "FFmpegMetadata"}],
            }
            r = self._try_download_with_fallback(url, opts)
            base_path = r.get("base_path", "")
            final_path = str(Path(base_path).with_suffix(".mp4")) if base_path else ""
            return {"title": r.get("info", {}).get("title", ""), "filepath": final_path}

        else:
            raise ValueError(f"Unsupported format_type: {format_type}")
    def get_info(self, url: str) -> dict:
        """Fetch metadata without downloading."""
        base = self._base_opts(progress_callback=None)
        base.update({
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "color": "never",
        })
        with YoutubeDL(base) as ydl:
            return ydl.extract_info(url, download=False)

    def _try_download_with_fallback(self, url: str, opts: dict) -> dict:
        def _run(o):
            with YoutubeDL(o) as ydl:
                info = ydl.extract_info(url, download=True)
                base_path = ydl.prepare_filename(info)
                return {"info": info, "base_path": base_path}

        try:
            return _run(opts)
        except DownloadError as e:
            msg = str(e)
            if "HTTP Error 403" not in msg and "Forbidden" not in msg:
                raise

            fb1 = dict(opts)
            fb1["extractor_args"] = {"youtube": {"player_client": ["default", "-android_sdkless", "-android"]}}
            try:
                return _run(fb1)
            except DownloadError:
                pass

            fb2 = dict(opts)
            fb2["extractor_args"] = {"youtube": {"player_client": ["web"]}}
            return _run(fb2)