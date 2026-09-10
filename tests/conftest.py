import os
import sys
import tempfile

TEST_DB = os.path.join(tempfile.gettempdir(), "medikiosk_test.db")

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)


def pytest_configure(config):
    os.environ.setdefault("GEMINI_API_KEY", "test_dummy_key")


def get_test_db_path():
    return TEST_DB