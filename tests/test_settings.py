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


class TestSponsorBlock:
    def test_default_disabled(self, _isolate_settings: AppSettings) -> None:
        assert _isolate_settings.get_sponsorblock_enabled() is False

    def test_round_trip(self, _isolate_settings: AppSettings) -> None:
        _isolate_settings.set_sponsorblock_enabled(True)
        assert _isolate_settings.get_sponsorblock_enabled() is True
        _isolate_settings.set_sponsorblock_enabled(False)
        assert _isolate_settings.get_sponsorblock_enabled() is False

    def test_parses_string_true(self, _isolate_settings: AppSettings) -> None:
        for raw in ("true", "True", "1", "yes", "on"):
            _isolate_settings.qs.setValue("download/sponsorblock", raw)
            assert _isolate_settings.get_sponsorblock_enabled() is True

    def test_parses_string_false(self, _isolate_settings: AppSettings) -> None:
        for raw in ("false", "0", "no", "", "garbage"):
            _isolate_settings.qs.setValue("download/sponsorblock", raw)
            assert _isolate_settings.get_sponsorblock_enabled() is False
