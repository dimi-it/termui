"""Tests for termui.termui_logging module."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from termui.termui_logging import (
    RichHandler,
    capture_logs,
    get_logger,
    set_level,
)


# ── get_logger ───────────────────────────────────────────────────────

def test_get_logger_returns_logger():
    log = get_logger("test_basic")
    assert isinstance(log, logging.Logger)
    assert log.name == "test_basic"


def test_get_logger_no_duplicate_handlers():
    log1 = get_logger("test_dup")
    n = len(log1.handlers)
    log2 = get_logger("test_dup")
    assert log2 is log1
    assert len(log2.handlers) == n


def test_get_logger_with_file(tmp_path: Path):
    log_file = tmp_path / "test.log"
    log = get_logger("test_file_logger", log_file=log_file)
    log.info("hello file")
    # flush handlers
    for h in log.handlers:
        h.flush()
    content = log_file.read_text(encoding="utf-8")
    assert "hello file" in content


# ── set_level ────────────────────────────────────────────────────────

def test_set_level():
    log = get_logger("test_set_level")
    set_level("test_set_level", logging.WARNING)
    assert log.level == logging.WARNING


# ── RichHandler ──────────────────────────────────────────────────────

def test_rich_handler_emits(capsys):
    handler = RichHandler(show_time=False)
    handler.setLevel(logging.DEBUG)
    log = logging.getLogger("test_rich_emit")
    log.handlers.clear()
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    log.info("rich handler test")
    out = capsys.readouterr().out
    assert "rich handler test" in out


def test_rich_handler_structured_fields(capsys):
    handler = RichHandler(show_time=False)
    handler.setLevel(logging.DEBUG)
    log = logging.getLogger("test_structured")
    log.handlers.clear()
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    log.info("req done", extra={"fields": {"status": 200, "latency": 42}})
    out = capsys.readouterr().out
    assert "status=200" in out
    assert "latency=42" in out


# ── capture_logs ─────────────────────────────────────────────────────

def test_capture_logs_basic():
    log = get_logger("test_capture")
    with capture_logs("test_capture") as records:
        log.info("captured message")
    assert len(records) >= 1
    assert "captured message" in records[-1].getMessage()


def test_capture_logs_cleans_up():
    log = get_logger("test_capture_cleanup")
    n_before = len(log.handlers)
    with capture_logs("test_capture_cleanup") as records:
        log.info("temp")
    assert len(log.handlers) == n_before


def test_capture_logs_multiple():
    log = get_logger("test_capture_multi")
    with capture_logs("test_capture_multi") as records:
        log.info("one")
        log.warning("two")
        log.error("three")
    assert len(records) >= 3
