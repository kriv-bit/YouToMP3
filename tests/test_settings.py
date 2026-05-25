from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication

from app.ui.settings import AppSettings


@pytest.fixture(autouse=True)
def _isolate_settings():
    """Each test sees a clean QSettings backing store."""
    QCoreApplication.setOrganizationName("kriv-bit")
    QCoreApplication.setApplicationName("YouToMp3Pro-tests")
    settings = AppSettings()
    settings.qs.clear()
    yield settings
    settings.qs.clear()


class TestConcurrency:
    def test_default_is_one(self, _isolate_settings: AppSettings) -> None:
        assert _isolate_settings.get_concurrency() == 1

    def test_round_trip(self, _isolate_settings: AppSettings) -> None:
        _isolate_settings.set_concurrency(3)
        assert _isolate_settings.get_concurrency() == 3

    def test_clamps_low(self, _isolate_settings: AppSettings) -> None:
        _isolate_settings.set_concurrency(0)
        assert _isolate_settings.get_concurrency() == 1
        _isolate_settings.set_concurrency(-5)
        assert _isolate_settings.get_concurrency() == 1

    def test_clamps_high(self, _isolate_settings: AppSettings) -> None:
        _isolate_settings.set_concurrency(100)
        assert _isolate_settings.get_concurrency() == 4

    def test_handles_non_integer_input(self, _isolate_settings: AppSettings) -> None:
        _isolate_settings.set_concurrency("garbage")  # type: ignore[arg-type]
        assert _isolate_settings.get_concurrency() == 1

    def test_handles_non_integer_stored(self, _isolate_settings: AppSettings) -> None:
        _isolate_settings.qs.setValue("download/concurrency", "garbage")
        assert _isolate_settings.get_concurrency() == 1
