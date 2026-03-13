"""Tests for termui.notify module."""

from __future__ import annotations

import pytest

from termui.notify import (
    NotifyLevel,
    NotifyQueue,
    notification_history,
    notify,
    _history,
)


@pytest.fixture(autouse=True)
def _clear_history():
    """Clear notification history before each test."""
    _history.clear()
    yield
    _history.clear()


# ── notify ───────────────────────────────────────────────────────────

def test_notify_basic(capsys):
    notify("hello", level=NotifyLevel.INFO)
    out = capsys.readouterr().out
    assert "hello" in out


def test_notify_success(capsys):
    notify("ok", level=NotifyLevel.SUCCESS)
    out = capsys.readouterr().out
    assert "ok" in out


def test_notify_error(capsys):
    notify("bad", level=NotifyLevel.ERROR)
    out = capsys.readouterr().out
    assert "bad" in out


def test_notify_custom_title(capsys):
    notify("msg", title="Custom")
    out = capsys.readouterr().out
    assert "Custom" in out


# ── History ──────────────────────────────────────────────────────────

def test_notification_history_records():
    notify("first")
    notify("second")
    h = notification_history()
    assert len(h) == 2
    assert h[0]["message"] == "first"
    assert h[1]["message"] == "second"


def test_notification_history_limit():
    for i in range(5):
        notify(f"msg {i}")
    h = notification_history(n=3)
    assert len(h) == 3
    assert h[0]["message"] == "msg 2"


# ── NotifyQueue ──────────────────────────────────────────────────────

def test_notify_queue_flush(capsys):
    q = NotifyQueue()
    q.put("queued 1")
    q.put("queued 2", level=NotifyLevel.WARNING)
    # nothing printed yet
    mid = capsys.readouterr().out
    assert "queued" not in mid

    q.flush()
    out = capsys.readouterr().out
    assert "queued 1" in out
    assert "queued 2" in out


def test_notify_queue_empty_flush(capsys):
    q = NotifyQueue()
    q.flush()  # should not raise
    out = capsys.readouterr().out
    assert out == "" or "queued" not in out
