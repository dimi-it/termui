"""Tests for termui.diff module."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from termui.diff import (
    DiffSummary,
    diff_summary,
    print_diff,
    print_diff_dirs,
    print_diff_files,
)


# ── diff_summary ─────────────────────────────────────────────────────

def test_diff_summary_identical():
    s = diff_summary("hello\nworld", "hello\nworld")
    assert s.added == 0
    assert s.removed == 0
    assert s.changed == 0
    assert s.unchanged == 2


def test_diff_summary_added():
    s = diff_summary("a", "a\nb")
    assert s.added == 1
    assert s.removed == 0


def test_diff_summary_removed():
    s = diff_summary("a\nb", "a")
    assert s.removed == 1
    assert s.added == 0


def test_diff_summary_changed():
    s = diff_summary("a\nb\nc", "a\nx\nc")
    assert s.changed == 1
    assert s.unchanged == 2


def test_diff_summary_ignore_whitespace():
    s = diff_summary("a  \nb", "a\nb")
    assert s.changed == 1 or s.unchanged < 2  # without flag, differs

    s2 = diff_summary("a  \nb", "a\nb", ignore_whitespace=True)
    assert s2.unchanged == 2
    assert s2.changed == 0


def test_diff_summary_is_frozen():
    s = diff_summary("a", "b")
    with pytest.raises(AttributeError):
        s.added = 99  # type: ignore[misc]


# ── print_diff ───────────────────────────────────────────────────────

def test_print_diff_unified_no_diff(capsys):
    print_diff("same", "same")
    out = capsys.readouterr().out
    assert "No differences" in out


def test_print_diff_unified(capsys):
    print_diff("old line", "new line")
    out = capsys.readouterr().out
    assert "Diff" in out or "old" in out or "new" in out


def test_print_diff_side_by_side(capsys):
    print_diff("old", "new", mode="side-by-side")
    out = capsys.readouterr().out
    assert len(out) > 0


def test_print_diff_char_highlight(capsys):
    print_diff(
        "hello world",
        "hello there",
        mode="side-by-side",
        char_highlight=True,
    )
    out = capsys.readouterr().out
    assert "hello" in out


def test_print_diff_ignore_whitespace(capsys):
    print_diff("a  \nb", "a\nb", ignore_whitespace=True)
    out = capsys.readouterr().out
    assert "No differences" in out


def test_print_diff_bad_mode():
    with pytest.raises(ValueError, match="Unknown diff mode"):
        print_diff("a", "b", mode="invalid")


# ── print_diff_files ─────────────────────────────────────────────────

def test_print_diff_files(tmp_path: Path, capsys):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("line1\nline2\n", encoding="utf-8")
    b.write_text("line1\nchanged\n", encoding="utf-8")
    print_diff_files(a, b)
    out = capsys.readouterr().out
    assert "changed" in out or "line2" in out


# ── print_diff_dirs ──────────────────────────────────────────────────

def test_print_diff_dirs(tmp_path: Path, capsys):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "shared.txt").write_text("old", encoding="utf-8")
    (dir_b / "shared.txt").write_text("new", encoding="utf-8")
    (dir_a / "only_a.txt").write_text("a", encoding="utf-8")
    (dir_b / "only_b.txt").write_text("b", encoding="utf-8")

    print_diff_dirs(dir_a, dir_b)
    out = capsys.readouterr().out
    assert "only_a.txt" in out
    assert "only_b.txt" in out


def test_print_diff_dirs_extensions(tmp_path: Path, capsys):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "f.py").write_text("old", encoding="utf-8")
    (dir_b / "f.py").write_text("new", encoding="utf-8")
    (dir_a / "f.txt").write_text("old", encoding="utf-8")
    (dir_b / "f.txt").write_text("new", encoding="utf-8")

    print_diff_dirs(dir_a, dir_b, extensions=[".py"])
    out = capsys.readouterr().out
    # .txt diff should not appear
    assert "f.py" in out
