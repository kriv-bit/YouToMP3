import subprocess
from pathlib import Path

URLS = [
    

    # Las que faltaban (6)
    "https://youtu.be/eTKeQhYVvbQ?si=f_auiymUIYtyadIG",
    "https://youtu.be/6NXnxTNIWkc?si=XWbPVVEPFW-U3JMM",
    "https://youtu.be/3eT464L1YRA?si=n6GuVbrbMEeIFmhs",
    "https://youtu.be/oNjQXmoxiQ8?si=6gQd_hT2un4Yo_sL",
    "https://youtu.be/UtUPSXkJ4UI?si=OYjXMdmDnGfpSHZm",
    "https://youtu.be/SCeK-z3qElo?si=7KpgEi64nzxe01f1",
]

def descargar_mp3_con_portada(urls, carpeta_salida="MP3"):
    """
    Descarga audio, convierte a MP3, agrega metadatos e incrusta portada.
    Requiere: yt-dlp + ffmpeg.
    """
    out_dir = Path(carpeta_salida)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo = título del video
    output_template = str(out_dir / "%(title)s.%(ext)s")

    for url in urls:
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--windows-filenames",

            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",

            "--add-metadata",
            "--embed-thumbnail",
            "--convert-thumbnails", "jpg",

            "-o", output_template,
            url,
        ]

        print(f"Descargando: {url}")
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    descargar_mp3_con_portada(URLS)
    print("✅ Listo. Revisa la carpeta 'MP3'.")
