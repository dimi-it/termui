"""ui.table_stream — Streaming table for incremental row display.

Usage
-----
    from ui.table_stream import StreamingTable

    with StreamingTable(["Step", "Status", "Time"]) as st:
        st.add_row("1", "running", "0s")
        st.add_row("2", "pending", "-")
        st.update_cell(0, 1, "✔ done")

The table is rendered via ``rich.Live`` so rows appear incrementally
without clearing the screen.
"""

from __future__ import annotations

import threading
from typing import Any, Generator, Sequence

from contextlib import contextmanager

from rich.live import Live
from rich.table import Table

from .console import console
from . import theme as _theme


class StreamingTable:
    """A live-updating table that supports incremental row additions and
    in-place cell updates.

    This class is **thread-safe**: ``add_row``, ``update_cell``, and
    ``update_row`` can be called from any thread.

    Parameters
    ----------
    headers : Sequence[str]
        Column header strings.
    title : str | None
        Optional title displayed above the table.
    refresh_per_second : float
        ``rich.Live`` refresh rate.

    Examples
    --------
    >>> with StreamingTable(["Name", "Score"]) as st:
    ...     st.add_row("Alice", 95)
    ...     st.add_row("Bob", 82)
    ...     st.update_cell(0, 1, 100)
    """

    def __init__(
        self,
        headers: Sequence[str],
        *,
        title: str | None = None,
        refresh_per_second: float = 4,
    ) -> None:
        self._headers = list(headers)
        self._title = title
        self._refresh = refresh_per_second
        self._rows: list[list[str]] = []
        self._lock = threading.Lock()
        self._live: Live | None = None

    # ── Build the rich Table from current state ──────────────────────

    def _build(self) -> Table:
        t = _theme.current()
        table = Table(
            title=self._title,
            border_style=t.table_border,
            header_style=t.table_header,
        )
        for h in self._headers:
            table.add_column(h)
        for row in self._rows:
            table.add_row(*row)
        return table

    def _refresh_live(self) -> None:
        if self._live is not None:
            self._live.update(self._build())

    # ── Public mutation methods (all thread-safe) ────────────────────

    def add_row(self, *cells: Any) -> int:
        """Append a row and refresh the live display.

        Parameters
        ----------
        *cells : Any
            Cell values (converted to ``str``).

        Returns
        -------
        int
            0-based index of the new row.
        """
        with self._lock:
            self._rows.append([str(c) for c in cells])
            idx = len(self._rows) - 1
            self._refresh_live()
        return idx

    def update_cell(self, row: int, col: int, value: Any) -> None:
        """Update a single cell in-place.

        Parameters
        ----------
        row : int
            0-based row index.
        col : int
            0-based column index.
        value : Any
            New cell value (converted to ``str``).
        """
        with self._lock:
            self._rows[row][col] = str(value)
            self._refresh_live()

    def update_row(self, row: int, *cells: Any) -> None:
        """Replace an entire row in-place.

        Parameters
        ----------
        row : int
            0-based row index.
        *cells : Any
            New cell values (must match column count).
        """
        with self._lock:
            self._rows[row] = [str(c) for c in cells]
            self._refresh_live()

    @property
    def row_count(self) -> int:
        """Current number of rows."""
        with self._lock:
            return len(self._rows)

    @property
    def renderable(self) -> Table:
        """The underlying ``rich.Table``."""
        with self._lock:
            return self._build()

    # ── Context manager ──────────────────────────────────────────────

    def __enter__(self) -> "StreamingTable":
        self._live = Live(
            self._build(),
            console=console,
            refresh_per_second=self._refresh,
        )
        self._live.__enter__()
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._live is not None:
            self._live.__exit__(*exc)
            self._live = None
