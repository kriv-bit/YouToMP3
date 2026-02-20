from app.downloader import MediaDownloader

d = MediaDownloader("downloads")
d.download("https://youtu.be/dQw4w9WgXcQ", format_type="mp3", quality="192")
print("ok")