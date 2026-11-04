"""Marks the slowest tests (whole-page runs and hourly sizing) so ``pytest -m "not slow"`` gives a quick check."""
import pytest

SLOW = {"test_app_views.py", "test_hourly.py"}
SLOW_TESTS = {"test_sensitivity", "test_excel_workbook", "test_curve_changes_the_design", "test_zip_bundle",
              "test_pdf_report", "test_reports"}


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: takes several seconds (deselect with -m 'not slow')")


def pytest_collection_modifyitems(items):
    for item in items:
        if item.path.name in SLOW or item.originalname in SLOW_TESTS:
            item.add_marker(pytest.mark.slow)
