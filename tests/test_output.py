"""Basic tests for termui.output module."""

import pytest
from termui import print_text, print_success, print_error, print_warning, print_info


def test_print_functions_exist():
    """Test that basic print functions are importable."""
    assert callable(print_text)
    assert callable(print_success)
    assert callable(print_error)
    assert callable(print_warning)
    assert callable(print_info)


def test_print_text_basic(capsys):
    """Test basic text printing."""
    print_text("Hello, World!")
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out
