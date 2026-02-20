from yt_dlp import YoutubeDL


class MediaDownloader:

    def __init__(self, output_path="downloads"):
        self.output_path = output_path

    def download(self, url, format_type="mp3", quality="192", progress_callback=None):

        ydl_opts = {
            "outtmpl": f"{self.output_path}/%(title)s.%(ext)s",
            "noplaylist": True,
            "windowsfilenames": True,
            "progress_hooks": [progress_callback] if progress_callback else [],
        }

        if format_type == "mp3":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality,
                }],
            })

        elif format_type == "mp4":
            ydl_opts.update({
                "format": "bestvideo+bestaudio/best"
            })

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])