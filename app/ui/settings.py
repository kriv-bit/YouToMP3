import os

from PySide6.QtCore import QSettings


class AppSettings:
    def __init__(self):
        self.qs = QSettings("kriv-bit", "YouToMp3Pro")

    def get_language(self) -> str:
        return self.qs.value("language", "en")

    def set_language(self, lang: str):
        self.qs.setValue("language", "es" if lang == "es" else "en")

    def get_output_folder(self) -> str:
        return self.qs.value("output_folder", os.path.abspath("downloads"))

    def set_output_folder(self, folder: str):
        self.qs.setValue("output_folder", folder)

    # ya te sirve para el punto 4
    def get_format(self) -> str:
        return self.qs.value("download/format", "mp3")

    def set_format(self, fmt: str):
        self.qs.setValue("download/format", fmt)

    def get_quality(self) -> str:
        return self.qs.value("download/quality", "192")

    def set_quality(self, q: str):
        self.qs.setValue("download/quality", q)

    def restore_geometry(self, window):
        geo = self.qs.value("ui/geometry")
        if geo:
            window.restoreGeometry(geo)

    def save_geometry(self, window):
        self.qs.setValue("ui/geometry", window.saveGeometry())

    def get_theme(self) -> str:
        return self.qs.value("ui/theme", "dark")

    def set_theme(self, theme: str):
        self.qs.setValue("ui/theme", "light" if theme == "light" else "dark")

    def get_concurrency(self) -> int:
        try:
            n = int(self.qs.value("download/concurrency", 1))
        except (TypeError, ValueError):
            n = 1
        return max(1, min(4, n))

    def set_concurrency(self, n: int):
        try:
            value = max(1, min(4, int(n)))
        except (TypeError, ValueError):
            value = 1
        self.qs.setValue("download/concurrency", value)

    def get_sponsorblock_enabled(self) -> bool:
        raw = self.qs.value("download/sponsorblock", False)
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    def set_sponsorblock_enabled(self, enabled: bool):
        self.qs.setValue("download/sponsorblock", bool(enabled))

