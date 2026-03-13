"""ui.layout — Multi-column layouts, live dashboards, and screen helpers.

Provides:
- ``columns()``        — render multiple renderables side-by-side.
- ``live_dashboard()`` — context manager for live-updating terminal UIs.
- ``clear_screen()``   — clear the terminal.
- ``print_header()``   — re-exported from output for convenience.
"""

from __future__ import annotations

import os
import shutil
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional

from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .console import console
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
    console.print(Columns(renderables, equal=equal, expand=expand))


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
                dash["header"].update(Panel("My App"))
                dash["body"].update(build_body_table())
                dash["footer"].update(Panel(f"Time: {now()}"))
                live.update(dash.layout)
                time.sleep(0.5)
    """

    def __init__(self) -> None:
        self._layout = Layout()
        self._sections: list[dict] = []

    def add_section(
        self,
        name: str,
        *,
        size: Optional[int] = None,
        ratio: Optional[int] = 1,
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
