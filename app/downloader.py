from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, ID3NoHeaderError
from mutagen.mp4 import MP4, MP4Cover
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


class DownloadCancelled(Exception):
    """Raised from inside the yt-dlp progress hook to abort the current download."""


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

    def _result_with_extension(self, result: dict, ext: str, *, embed_artwork: bool = False) -> dict:
        """Normalize yt-dlp output to a consistent {title, filepath} payload."""
        base_path = result.get("base_path", "")
        final_path = str(Path(base_path).with_suffix(f".{ext}")) if base_path else ""
        payload = {
            "title": result.get("info", {}).get("title", ""),
            "filepath": final_path,
            "artwork_embedded": False,
            "artwork_warning": "",
        }
        if embed_artwork and final_path:
            self._normalize_audio_tags(final_path, result.get("info", {}), ext)
            ok, warning = self._embed_cover_art(final_path, result.get("info", {}), ext)
            payload["artwork_embedded"] = ok
            payload["artwork_warning"] = warning
        return payload

    def _base_opts(self, progress_callback=None) -> dict:
        out_dir = Path(self.output_path)
        out_dir.mkdir(parents=True, exist_ok=True)

        return {
            "outtmpl": str(out_dir / "%(title).180s [%(id)s].%(ext)s"),
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
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": str(quality)},
                    {"key": "FFmpegMetadata"},
                ],
                "postprocessor_args": {
                    "FFmpegMetadata+ffmpeg_o": ["-id3v2_version", "3"],
                },
                "parse_metadata": [
                    "%(uploader|)s:%(meta_artist)s",
                ],
            }
            r = self._try_download_with_fallback(url, opts)
            return self._result_with_extension(r, "mp3", embed_artwork=True)

        elif format_type == "m4a":
            opts = {
                **base,
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": str(quality)},
                    {"key": "FFmpegMetadata"},
                ],
            }
            r = self._try_download_with_fallback(url, opts)
            return self._result_with_extension(r, "m4a", embed_artwork=True)

        elif format_type == "wav":
            opts = {
                **base,
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "wav"},
                    {"key": "FFmpegMetadata"},
                ],
            }
            r = self._try_download_with_fallback(url, opts)
            return self._result_with_extension(r, "wav")

        elif format_type == "mp4":
            opts = {
                **base,
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "postprocessors": [{"key": "FFmpegMetadata"}],
            }
            r = self._try_download_with_fallback(url, opts)
            return self._result_with_extension(r, "mp4")

        else:
            raise ValueError(f"Unsupported format_type: {format_type}")

    def get_info(self, url: str, *, allow_playlist: bool = False) -> dict:
        """Fetch metadata without downloading."""
        base = self._base_opts(progress_callback=None)
        base.update({
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "color": "never",
            "noplaylist": not allow_playlist,
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

    def _best_thumbnail_url(self, info: dict) -> str:
        if not isinstance(info, dict):
            return ""

        thumbnails = info.get("thumbnails")
        if isinstance(thumbnails, list) and thumbnails:
            valid = [t for t in thumbnails if isinstance(t, dict) and t.get("url")]
            if valid:
                def _score(item: dict) -> int:
                    return int(item.get("width") or 0) * int(item.get("height") or 0)

                return str(max(valid, key=_score).get("url") or "")

        thumbnail = info.get("thumbnail")
        return str(thumbnail) if thumbnail else ""

    def _fetch_thumbnail_bytes(self, url: str) -> bytes | None:
        if not url:
            return None

        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=12) as resp:
                return resp.read(8 * 1024 * 1024)
        except Exception:
            return None

    def _prepare_cover_jpeg(self, raw: bytes, size: int = 800) -> bytes:
        from PIL import Image, ImageOps

        with Image.open(BytesIO(raw)) as img:
            img = img.convert("RGB")
            img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            out = BytesIO()
            img.save(out, format="JPEG", quality=88, optimize=True, progressive=False)
            return out.getvalue()

    def _embed_cover_art(self, media_path: str, info: dict, ext: str) -> tuple[bool, str]:
        path = Path(media_path)
        if not path.exists():
            return False, "Output file was not found for artwork embedding."

        raw = self._fetch_thumbnail_bytes(self._best_thumbnail_url(info))
        if not raw:
            return False, "No thumbnail was available to embed."

        try:
            cover = self._prepare_cover_jpeg(raw)
        except Exception as exc:
            return False, f"Thumbnail could not be normalized: {exc}"

        try:
            if ext == "mp3":
                try:
                    tags = ID3(path)
                except ID3NoHeaderError:
                    tags = ID3()
                tags.delall("APIC")
                tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=cover,
                    )
                )
                tags.save(path, v2_version=3)
                return True, ""

            if ext == "m4a":
                tags = MP4(path)
                tags["covr"] = [MP4Cover(cover, imageformat=MP4Cover.FORMAT_JPEG)]
                tags.save()
                return True, ""

            return False, f"Artwork embedding is not supported for .{ext}."
        except Exception as exc:
            return False, f"Artwork could not be embedded: {exc}"

    def _metadata_text(self, info: dict, key: str) -> str:
        value = info.get(key) if isinstance(info, dict) else ""
        return str(value).strip() if value else ""

    def _fallback_album(self, info: dict) -> str:
        return (
            self._metadata_text(info, "album")
            or self._metadata_text(info, "playlist_title")
            or self._metadata_text(info, "title")
        )

    def _normalize_audio_tags(self, media_path: str, info: dict, ext: str) -> None:
        path = Path(media_path)
        if not path.exists():
            return

        title = self._metadata_text(info, "title")
        artist = (
            self._metadata_text(info, "artist")
            or self._metadata_text(info, "uploader")
            or self._metadata_text(info, "channel")
        )
        album = self._fallback_album(info)

        try:
            if ext == "mp3":
                try:
                    tags = ID3(path)
                except ID3NoHeaderError:
                    tags = ID3()
                if title:
                    tags.delall("TIT2")
                    tags.add(TIT2(encoding=3, text=title))
                if artist:
                    tags.delall("TPE1")
                    tags.add(TPE1(encoding=3, text=artist))
                if album:
                    tags.delall("TALB")
                    tags.add(TALB(encoding=3, text=album))
                tags.save(path, v2_version=3)

            elif ext == "m4a":
                tags = MP4(path)
                if title:
                    tags["\xa9nam"] = [title]
                if artist:
                    tags["\xa9ART"] = [artist]
                if album:
                    tags["\xa9alb"] = [album]
                tags.save()
        except Exception:
            return
