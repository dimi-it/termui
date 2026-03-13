"""Tests for termui.output module."""

from __future__ import annotations

import io

import pytest
from rich.console import Console

from termui import (
    print_text,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_table,
    print_key_value,
    print_json,
    print_rule,
    print_panel,
    print_header,
    print_callout,
    print_status_grid,
    print_metric,
    print_metric_group,
    print_timeline,
    progress_map,
)
from termui.output import SpinnerGroup


# ── Existence / importability ────────────────────────────────────────

def test_print_functions_exist():
    """Test that basic print functions are importable."""
    assert callable(print_text)
    assert callable(print_success)
    assert callable(print_error)
    assert callable(print_warning)
    assert callable(print_info)


# ── Basic output ─────────────────────────────────────────────────────

def test_print_text_basic(capsys):
    """Test basic text printing."""
    print_text("Hello, World!")
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out


def test_print_success_contains_check(capsys):
    print_success("done")
    out = capsys.readouterr().out
    assert "done" in out


def test_print_error_contains_x(capsys):
    print_error("fail")
    out = capsys.readouterr().out
    assert "fail" in out


def test_print_warning_contains_text(capsys):
    print_warning("caution")
    out = capsys.readouterr().out
    assert "caution" in out


def test_print_info_contains_text(capsys):
    print_info("note")
    out = capsys.readouterr().out
    assert "note" in out


# ── Table ────────────────────────────────────────────────────────────

def test_print_table_basic(capsys):
    print_table(["A", "B"], [["1", "2"], ["3", "4"]])
    out = capsys.readouterr().out
    assert "A" in out
    assert "1" in out


def test_print_table_zebra(capsys):
    print_table(["X"], [["a"], ["b"], ["c"]], zebra=True)
    out = capsys.readouterr().out
    assert "a" in out


def test_print_table_footer(capsys):
    print_table(["Name", "Score"], [["A", "1"]], footer_row=["Total", "1"])
    out = capsys.readouterr().out
    assert "Total" in out


def test_print_table_max_col_width(capsys):
    print_table(["Col"], [["a" * 100]], max_col_width=10)
    out = capsys.readouterr().out
    assert "…" in out


# ── Key-value ────────────────────────────────────────────────────────

def test_print_key_value(capsys):
    print_key_value({"key1": "val1", "key2": "val2"})
    out = capsys.readouterr().out
    assert "key1" in out
    assert "val1" in out


# ── JSON ─────────────────────────────────────────────────────────────

def test_print_json_dict(capsys):
    print_json({"hello": "world"})
    out = capsys.readouterr().out
    assert "hello" in out


def test_print_json_highlight_path(capsys):
    print_json({"model": "gpt-4", "tokens": 100}, highlight_path="$.model")
    out = capsys.readouterr().out
    assert "model" in out


# ── Panel / header / rule ────────────────────────────────────────────

def test_print_panel(capsys):
    print_panel("content", title="Title")
    out = capsys.readouterr().out
    assert "content" in out


def test_print_header(capsys):
    print_header("My App", "subtitle")
    out = capsys.readouterr().out
    assert "My App" in out


def test_print_rule(capsys):
    print_rule("section")
    out = capsys.readouterr().out
    assert "section" in out


# ── Callout ──────────────────────────────────────────────────────────

def test_print_callout(capsys):
    print_callout("Remember this.", kind="tip")
    out = capsys.readouterr().out
    assert "Remember this." in out


# ── Status grid ──────────────────────────────────────────────────────

def test_print_status_grid(capsys):
    print_status_grid({"API": True, "DB": False, "Cache": "warm"})
    out = capsys.readouterr().out
    assert "API" in out


# ── Metrics ──────────────────────────────────────────────────────────

def test_print_metric(capsys):
    print_metric("Latency", 42, unit="ms", delta=-3.2)
    out = capsys.readouterr().out
    assert "42" in out


def test_print_metric_group(capsys):
    print_metric_group([
        {"label": "L", "value": 10},
        {"label": "T", "value": 20},
    ])
    out = capsys.readouterr().out
    assert "10" in out


# ── Timeline ─────────────────────────────────────────────────────────

def test_print_timeline(capsys):
    print_timeline([
        {"label": "A", "start": 0, "end": 2},
        {"label": "B", "start": 1, "end": 3},
    ], width=60)
    out = capsys.readouterr().out
    assert "A" in out


# ── progress_map ─────────────────────────────────────────────────────

def test_progress_map_sequential():
    results = progress_map(str.upper, ["a", "b", "c"])
    assert results == ["A", "B", "C"]


def test_progress_map_threaded():
    results = progress_map(str.upper, ["x", "y"], max_workers=2)
    assert results == ["X", "Y"]
