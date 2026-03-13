"""ui.layout — Multi-column layouts, live dashboards, and screen helpers.

Provides:
- ``columns()``          — render multiple renderables side-by-side.
- ``grid()``             — NxM grid of renderables.
- ``split_horizontal()`` — two-pane vertical split.
- ``live_dashboard()``   — context manager for live-updating terminal UIs.
- ``live_table()``       — context manager for a live-updating table.
- ``scrollable_panel()`` — panel with scrollable content.
- ``clear_screen()``     — clear the terminal.
- ``print_header()``     — re-exported from output for convenience.
"""

from __future__ import annotations

import shutil
from contextlib import contextmanager
from typing import Any, Generator, Optional, Sequence

from rich.columns import Columns
from rich.console import RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .console import console, console_lock
from . import theme as _theme
from .output import print_header  # re-export  # noqa: F401


# ── Multi-column layout ──────────────────────────────────────────────

def columns(
    *renderables: Any,
    equal: bool = True,
    expand: bool = True,
) -> None:
    """Print multiple ``rich`` renderables side-by-side.

    Parameters
    ----------
    *renderables: Any rich-compatible objects (Text, Panel, Table, …).
    equal:        Give each column equal width.
    expand:       Expand columns to fill terminal width.
    """
    with console_lock:
        console.print(Columns(renderables, equal=equal, expand=expand))


# ── Grid ─────────────────────────────────────────────────────────────

def grid(
    renderables: list[list[Any]],
    *,
    padding: tuple[int, int] = (0, 1),
    expand: bool = True,
) -> None:
    """Render an NxM grid of renderables.

    More flexible than :func:`columns` — each row is an inner list.

    Parameters
    ----------
    renderables : list[list[Any]]
        Outer list = rows; inner list = cells in that row.
    padding : tuple[int, int]
        ``(vertical, horizontal)`` padding between cells.
    expand : bool
        Expand the table to fill terminal width.

    Examples
    --------
    >>> from rich.panel import Panel
    >>> grid([[Panel("A"), Panel("B")], [Panel("C"), Panel("D")]])
    """
    t = _theme.current()
    table = Table(
        show_header=False,
        show_edge=False,
        border_style=t.table_border,
        padding=padding,
        expand=expand,
    )
    # Determine column count from the widest row
    max_cols = max((len(row) for row in renderables), default=0)
    for _ in range(max_cols):
        table.add_column()
    for row in renderables:
        cells = list(row) + [""] * (max_cols - len(row))
        table.add_row(*cells)
    with console_lock:
        console.print(table)


# ── Split horizontal ─────────────────────────────────────────────────

def split_horizontal(
    top: Any,
    bottom: Any,
    *,
    ratio: tuple[int, int] = (1, 1),
) -> None:
    """Render a two-pane vertical split.

    Parameters
    ----------
    top : Any
        Rich renderable for the top pane.
    bottom : Any
        Rich renderable for the bottom pane.
    ratio : tuple[int, int]
        Relative sizes of the two panes.

    Examples
    --------
    >>> from rich.panel import Panel
    >>> split_horizontal(Panel("Top"), Panel("Bottom"), ratio=(2, 1))
    """
    layout = Layout()
    layout.split(
        Layout(top, ratio=ratio[0]),
        Layout(bottom, ratio=ratio[1]),
    )
    with console_lock:
        console.print(layout)


# ── Live dashboard ───────────────────────────────────────────────────

@contextmanager
def live_dashboard(
    refresh_per_second: float = 4,
    *,
    transient: bool = False,
    vertical_overflow: str = "ellipsis",
) -> Generator[Live, None, None]:
    """Context manager that exposes a ``rich.Live`` instance.

    Anything you assign to ``live.update(renderable)`` is re-rendered at
    *refresh_per_second* frames per second.

    Usage::

        with live_dashboard(refresh_per_second=2) as live:
            for step in steps:
                process(step)
                table = build_table(step)
                live.update(table)

    Parameters
    ----------
    refresh_per_second: Frame rate.
    transient:          Clear the display when the context exits.
    vertical_overflow:  ``"ellipsis"`` | ``"visible"`` | ``"crop"``.
    """
    with Live(
        console=console,
        refresh_per_second=refresh_per_second,
        transient=transient,
        vertical_overflow=vertical_overflow,  # type: ignore[arg-type]
    ) as live:
        yield live


# ── Screen helpers ───────────────────────────────────────────────────

def clear_screen() -> None:
    """Clear the terminal screen (cross-platform)."""
    console.clear()


def terminal_size() -> tuple[int, int]:
    """Return ``(columns, lines)`` of the current terminal."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


# ── Paged output ─────────────────────────────────────────────────────

def pager(text: str) -> None:
    """Display *text* in the console's built-in pager (like ``less``)."""
    with console.pager():
        console.print(text)


# ── Live table ───────────────────────────────────────────────────────

class LiveTable:
    """A table wired to a ``rich.Live`` display.

    Use :func:`live_table` to create instances.

    Examples
    --------
    >>> with live_table(["Name", "Score"]) as lt:
    ...     lt.add_row("Alice", 95)
    ...     lt.add_row("Bob", 82)
    """

    def __init__(self, headers: Sequence[str], *, title: str | None = None) -> None:
        self._headers = list(headers)
        self._title = title
        self._rows: list[list[str]] = []
        self._table = self._build()

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

    def add_row(self, *cells: Any) -> None:
        """Append a row and refresh the live display.

        Parameters
        ----------
        *cells : Any
            Cell values (converted to ``str``).
        """
        self._rows.append([str(c) for c in cells])
        self._table = self._build()

    @property
    def renderable(self) -> Table:
        """The underlying ``rich.Table``."""
        return self._table


@contextmanager
def live_table(
    headers: Sequence[str],
    *,
    title: str | None = None,
    refresh_per_second: float = 4,
) -> Generator[LiveTable, None, None]:
    """Context manager that returns a ``LiveTable`` wired to a ``Live`` display.

    Parameters
    ----------
    headers : Sequence[str]
        Column header strings.
    title : str | None
        Optional table title.
    refresh_per_second : float
        Frame rate.

    Yields
    ------
    LiveTable
        Call ``.add_row(*cells)`` to append and auto-refresh.

    Examples
    --------
    >>> with live_table(["Step", "Status"]) as lt:
    ...     lt.add_row("1", "running")
    ...     lt.add_row("2", "pending")
    """
    lt = LiveTable(headers, title=title)
    with Live(
        lt.renderable,
        console=console,
        refresh_per_second=refresh_per_second,
    ) as live:
        _orig_add_row = lt.add_row

        def _add_and_refresh(*cells: Any) -> None:
            _orig_add_row(*cells)
            live.update(lt.renderable)

        lt.add_row = _add_and_refresh  # type: ignore[assignment]
        yield lt


# ── Scrollable panel ─────────────────────────────────────────────────

def scrollable_panel(
    content: str | RenderableType,
    *,
    height: int = 20,
    title: str | None = None,
) -> None:
    """Print a panel whose content is truncated to *height* lines.

    If the content exceeds *height* lines, only the last *height* lines
    are shown — giving a "scrolled to bottom" effect.

    Parameters
    ----------
    content : str | RenderableType
        The body text or rich renderable.
    height : int
        Maximum visible lines.
    title : str | None
        Optional panel title.

    Examples
    --------
    >>> scrollable_panel("\\n".join(f"Line {i}" for i in range(50)), height=10)
    """
    t = _theme.current()
    if isinstance(content, str):
        lines = content.splitlines()
        if len(lines) > height:
            lines = lines[-height:]
        display_text = "\n".join(lines)
    else:
        display_text = content  # type: ignore[assignment]

    with console_lock:
        console.print(
            Panel(
                display_text,
                title=title,
                border_style=t.panel_border,
                height=height + 2,  # +2 for border
            )
        )


# ── Split-pane layout builder ────────────────────────────────────────

class DashboardLayout:
    """Helper that builds a named ``rich.Layout`` and renders it live.

    Usage::

        dash = DashboardLayout()
        dash.add_section("header", size=3, ratio=None)
        dash.add_section("body")
        dash.add_section("footer", size=3, ratio=None)

        with dash.live(refresh_per_second=2) as live:
            while True:
                dash.update("header", Panel("My App"))
                dash.update("body", build_body_table())
                dash.update("footer", Panel(f"Time: {now()}"))
                live.update(dash.layout)
                time.sleep(0.5)
    """

    def __init__(self) -> None:
        self._layout = Layout()
        self._sections: list[dict[str, Any]] = []

    def add_section(
        self,
        name: str,
        *,
        size: int | None = None,
        ratio: int | None = 1,
        minimum_size: int = 1,
    ) -> "DashboardLayout":
        """Add a named horizontal band to the layout."""
        kwargs: dict[str, Any] = {"name": name, "minimum_size": minimum_size}
        if size is not None:
            kwargs["size"] = size
        elif ratio is not None:
            kwargs["ratio"] = ratio
        self._sections.append(kwargs)
        self._layout.split(*[Layout(**s) for s in self._sections])
        return self

    def update(self, name: str, renderable: Any) -> None:
        """Update a named section with a new renderable.

        Parameters
        ----------
        name : str
            Section name (must have been added via :meth:`add_section`).
        renderable : Any
            Rich renderable to display in the section.

        Examples
        --------
        >>> dash.update("header", Panel("Updated Header"))
        """
        self._layout[name].update(renderable)

    def __getitem__(self, name: str) -> Layout:
        return self._layout[name]

    @property
    def layout(self) -> Layout:
        return self._layout

    @contextmanager
    def live(self, refresh_per_second: float = 4) -> Generator[Live, None, None]:
        """Return a ``Live`` context pre-bound to this layout."""
        with Live(
            self._layout,
            console=console,
            refresh_per_second=refresh_per_second,
        ) as live:
            yield live
