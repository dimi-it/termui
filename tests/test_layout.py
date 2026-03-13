"""Tests for termui.layout module."""

from __future__ import annotations

import pytest

from termui.layout import (
    DashboardLayout,
    LiveTable,
    clear_screen,
    columns,
    grid,
    pager,
    scrollable_panel,
    split_horizontal,
    terminal_size,
)
from rich.panel import Panel


# ── terminal_size ────────────────────────────────────────────────────

def test_terminal_size_returns_tuple():
    cols, lines = terminal_size()
    assert isinstance(cols, int)
    assert isinstance(lines, int)
    assert cols > 0 and lines > 0


# ── columns ──────────────────────────────────────────────────────────

def test_columns_no_error(capsys):
    columns("A", "B", "C")
    out = capsys.readouterr().out
    assert len(out) > 0


# ── grid ─────────────────────────────────────────────────────────────

def test_grid_basic(capsys):
    grid([["a", "b"], ["c", "d"]])
    out = capsys.readouterr().out
    assert "a" in out
    assert "d" in out


def test_grid_uneven_rows(capsys):
    grid([["a", "b"], ["c"]])
    out = capsys.readouterr().out
    assert "a" in out


# ── split_horizontal ─────────────────────────────────────────────────

def test_split_horizontal(capsys):
    split_horizontal(Panel("Top"), Panel("Bottom"))
    out = capsys.readouterr().out
    assert "Top" in out
    assert "Bottom" in out


# ── scrollable_panel ─────────────────────────────────────────────────

def test_scrollable_panel_truncates(capsys):
    content = "\n".join(f"Line {i}" for i in range(50))
    scrollable_panel(content, height=5)
    out = capsys.readouterr().out
    # Should show the last 5 lines
    assert "Line 49" in out
    assert "Line 0" not in out


def test_scrollable_panel_short_content(capsys):
    scrollable_panel("short", height=10)
    out = capsys.readouterr().out
    assert "short" in out


# ── DashboardLayout ──────────────────────────────────────────────────

def test_dashboard_layout_add_section():
    dash = DashboardLayout()
    dash.add_section("header", size=3, ratio=None)
    dash.add_section("body")
    assert dash["header"] is not None
    assert dash["body"] is not None


def test_dashboard_layout_update():
    dash = DashboardLayout()
    dash.add_section("main")
    dash.update("main", Panel("Hello"))
    # Should not raise


def test_dashboard_layout_layout_property():
    dash = DashboardLayout()
    dash.add_section("a")
    assert dash.layout is not None


# ── LiveTable ────────────────────────────────────────────────────────

def test_live_table_class():
    lt = LiveTable(["X", "Y"])
    lt.add_row("1", "2")
    assert lt.renderable is not None
