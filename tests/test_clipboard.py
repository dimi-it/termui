"""Tests for termui.clipboard module."""

from __future__ import annotations

import pytest

from termui.clipboard import clipboard_available


def test_clipboard_available_returns_bool():
    result = clipboard_available()
    assert isinstance(result, bool)


def test_copy_import_error_without_pyperclip(monkeypatch):
    """If pyperclip is missing, copy_to_clipboard raises ImportError."""
    import importlib
    import sys

    # Temporarily hide pyperclip
    saved = sys.modules.get("pyperclip")
    sys.modules["pyperclip"] = None  # type: ignore[assignment]
    try:
        from termui.clipboard import _get_pyperclip
        with pytest.raises(ImportError, match="pyperclip"):
            _get_pyperclip()
    finally:
        if saved is not None:
            sys.modules["pyperclip"] = saved
        else:
            sys.modules.pop("pyperclip", None)
