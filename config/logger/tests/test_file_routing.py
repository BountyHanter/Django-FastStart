"""Проверки настоящего django.setup() в отдельных процессах без подключения к БД."""

import json
import logging
import os
from pathlib import Path
import subprocess
import sys

import pytest

from config.logger.config import build_logging
from config.logger.context import clear_context, get_context, set_context
from config.logger.formatters import JsonFormatter, TextFormatter


@pytest.fixture
def run_logging(tmp_path):
    def run(script, **overrides):
        env = {key: value for key, value in os.environ.items() if not key.startswith("LOG_")}
        env.update({
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "SECRET_KEY": "logger-tests-only",
            "DEBUG": "False",
            "ALLOWED_HOSTS": "testserver",
            "LOG_LEVEL": "DEBUG",
            "LOG_CONSOLE": "False",
            "LOG_FILE_TEXT": "True",
            "LOG_FILE_JSON": "True",
            "LOG_FILE_TEXT_PATH": str(tmp_path / "nested/app.log"),
            "LOG_FILE_TEXT_ERROR_PATH": str(tmp_path / "nested/error.log"),
            "LOG_FILE_JSON_PATH": str(tmp_path / "nested/app.json.log"),
            "LOG_FILE_JSON_ERROR_PATH": str(tmp_path / "nested/error.json.log"),
        })
        env.update(overrides)
        result = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()\n" + script],
            cwd=Path(__file__).resolve().parents[3], env=env,
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        return result
    return run


def read_json(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_django_logging_routes_levels_and_exceptions(run_logging, tmp_path):
    run_logging('''
from config.logger import log
from config.logger.context import set_context
set_context(request_id="req-42")
log.debug("debug-message")
log.info("info-message")
log.warning("warning-message")
log.error("error-message")
log.critical("critical-message")
try:
    1 / 0
except ZeroDivisionError:
    log.exception("exception-message", extra={"request_id": "req-43"})
''')
    app = read_json(tmp_path / "nested/app.json.log")
    error = read_json(tmp_path / "nested/error.json.log")
    assert [r["message"] for r in app] == ["debug-message", "info-message"]
    assert [r["message"] for r in error] == [
        "warning-message", "error-message", "critical-message", "exception-message",
    ]
    assert app[0]["request_id"] == "req-42"
    assert error[-1]["request_id"] == "req-43"
    assert "ZeroDivisionError" in error[-1]["exc"]
    assert all("asctime" not in r for r in app + error)
    app_text = (tmp_path / "nested/app.log").read_text()
    error_text = (tmp_path / "nested/error.log").read_text()
    for message in ("debug-message", "info-message"):
        assert app_text.count(message) == 1
        assert message not in error_text
    for message in ("warning-message", "error-message", "critical-message", "exception-message"):
        assert error_text.count(message) == 1
        assert message not in app_text


def test_http_errors_and_server_logs_are_not_duplicated(run_logging, tmp_path):
    run_logging('''
import logging
import sys
import types
from django.conf import settings
from django.test import Client
from django.urls import path

def broken(request):
    raise ValueError("broken-view")

urls = types.ModuleType("logger_test_urls")
urls.urlpatterns = [path("broken/", broken)]
sys.modules[urls.__name__] = urls
settings.ROOT_URLCONF = urls.__name__
client = Client(raise_request_exception=False)
assert client.get("/missing/").status_code == 404
assert client.get("/broken/").status_code == 500
logging.getLogger("django.server").info("server-message")
logging.getLogger("another_app.views").info("application-message")
''')
    app = read_json(tmp_path / "nested/app.json.log")
    error = read_json(tmp_path / "nested/error.json.log")
    assert [r["message"] for r in app] == ["server-message", "application-message"]
    assert [r["status_code"] for r in error] == [404, 500]
    assert [r["level"] for r in error] == ["WARNING", "ERROR"]
    assert "ValueError: broken-view" in error[-1]["exc"]


@pytest.mark.parametrize("level,expected", [("INFO", ["INFO", "ERROR"]), ("ERROR", ["ERROR"])])
def test_global_level_applies_to_console_and_files(run_logging, tmp_path, level, expected):
    result = run_logging('''
import logging
log = logging.getLogger("child.application")
log.setLevel(logging.DEBUG)
log.debug("debug-message")
log.info("info-message")
log.error("error-message")
''', LOG_LEVEL=level, LOG_CONSOLE="True", LOG_CONSOLE_FORMAT="json")
    assert [json.loads(line)["level"] for line in result.stderr.splitlines()] == expected
    assert result.stdout == ""
    app_path = tmp_path / "nested/app.json.log"
    app = read_json(app_path) if app_path.exists() else []
    error = read_json(tmp_path / "nested/error.json.log")
    assert [r["level"] for r in app + error] == expected


def test_disabled_outputs_stay_silent(run_logging, tmp_path):
    result = run_logging('''
from config.logger import log
log.error("must-stay-silent")
''', LOG_FILE_TEXT="False", LOG_FILE_JSON="False")
    assert result.stderr == result.stdout == ""
    assert not (tmp_path / "nested").exists()


def test_import_has_no_logging_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", '''
import logging
import config.logger
assert not logging.getLogger().handlers
assert not config.logger.log.handlers
'''], cwd=Path(__file__).resolve().parents[3], capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_paths_and_rotation_settings(monkeypatch, tmp_path):
    for key in os.environ:
        if key.startswith("LOG_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("LOG_ROTATION_WHEN", "S")
    monkeypatch.setenv("LOG_ROTATION_INTERVAL", "3")
    monkeypatch.setenv("LOG_ROTATION_BACKUP", "11")
    monkeypatch.setenv("LOG_ROTATION_UTC", "True")
    config = build_logging(tmp_path)
    # Отдельный логгер проверяет реальное создание и параметры обработчика.
    file_handlers = {k: v for k, v in config["handlers"].items() if k != "console"}
    config["handlers"] = file_handlers
    config["root"] = {"handlers": [], "level": "INFO"}
    config["loggers"] = {"rotation-test": {"handlers": list(file_handlers), "propagate": False}}
    # Конфигурацию выполняем в отдельном процессе, не меняя logging pytest.
    result = subprocess.run([sys.executable, "-c", f'''
import logging
from logging.config import dictConfig
dictConfig({config!r})
handlers = logging.getLogger("rotation-test").handlers
assert len(handlers) == 4
for h in handlers:
    assert h.when == "S"
    assert h.interval == 3
    assert h.backupCount == 11
    assert h.utc is True
    assert h.baseFilename.startswith({str(tmp_path)!r})
logging.shutdown()
'''], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_context_and_formatters_do_not_overwrite_base_json_fields():
    clear_context()
    try:
        set_context(request_id="context-id", user_id=42, logger="forged")
        record = logging.LogRecord("actual", logging.INFO, __file__, 1, "hello", (), None)
        record.request_id = "extra-id"
        record.level = "forged"
        TextFormatter("%(asctime)s %(message)s").format(record)
        data = json.loads(JsonFormatter("ts").format(record))
        assert data["logger"] == "actual"
        assert data["level"] == "INFO"
        assert data["request_id"] == "extra-id"
        assert data["user_id"] == 42
        assert "asctime" not in data
        snapshot = get_context()
        snapshot["user_id"] = 99
        assert get_context()["user_id"] == 42
    finally:
        clear_context()


def test_async_context_is_isolated():
    import asyncio

    async def worker(value):
        set_context(request_id=value)
        await asyncio.sleep(0)
        return get_context()["request_id"]

    async def run():
        return await asyncio.gather(worker("first"), worker("second"))

    clear_context()
    assert asyncio.run(run()) == ["first", "second"]
    assert get_context() == {}
