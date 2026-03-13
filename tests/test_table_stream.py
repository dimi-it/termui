"""Tests for termui.table_stream module."""

from __future__ import annotations

import threading

import pytest

from termui.table_stream import StreamingTable


def test_streaming_table_add_row():
    st = StreamingTable(["A", "B"])
    idx = st.add_row("1", "2")
    assert idx == 0
    assert st.row_count == 1


def test_streaming_table_update_cell():
    st = StreamingTable(["A", "B"])
    st.add_row("1", "2")
    st.update_cell(0, 1, "updated")
    assert st._rows[0][1] == "updated"


def test_streaming_table_update_row():
    st = StreamingTable(["A", "B"])
    st.add_row("1", "2")
    st.update_row(0, "x", "y")
    assert st._rows[0] == ["x", "y"]


def test_streaming_table_thread_safety():
    """Multiple threads adding rows concurrently."""
    st = StreamingTable(["ID"])
    errors: list[Exception] = []

    def _add(n: int) -> None:
        try:
            for i in range(10):
                st.add_row(f"{n}-{i}")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_add, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert st.row_count == 40


def test_streaming_table_renderable():
    st = StreamingTable(["Col"])
    st.add_row("val")
    table = st.renderable
    assert table is not None
