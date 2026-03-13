"""Shared pytest fixtures for termui tests."""

from __future__ import annotations

import io
from typing import Generator

import pytest
from rich.console import Console


@pytest.fixture()
def capture_console() -> Generator[Console, None, None]:
    """Return a ``Console`` that writes to an in-memory buffer.

    Use ``con.file.getvalue()`` to read captured output.
    """
    buf = io.StringIO()
    con = Console(file=buf, force_terminal=True, width=120, no_color=True)
    yield con


@pytest.fixture(autouse=True)
def _reset_theme() -> Generator[None, None, None]:
    """Ensure every test starts with the default DARK theme."""
    from termui.theme import apply_theme, Theme
    apply_theme(Theme.DARK)
    yield
    apply_theme(Theme.DARK)
