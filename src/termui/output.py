"""ui.output — High-level output helpers built on ``rich``.

All functions use the shared console and respect the active theme.
"""

from __future__ import annotations

import json as _json
import math
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    Literal,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from rich.columns import Columns
from rich.json import JSON
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    track,
)
from rich.rule import Rule
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .console import console, console_lock, is_dumb_terminal
from . import theme as _theme

T = TypeVar("T")
R = TypeVar("R")


# ── Basic print ──────────────────────────────────────────────────────

def print_text(text: str, style: Optional[str] = None, *, markup: bool = True) -> None:
    """Print *text* to the shared console.

    Parameters
    ----------
    text:    The string to print (rich markup is enabled by default).
    style:   Optional rich style string, e.g. ``"bold blue"``.
    markup:  Set to ``False`` to treat *text* as plain text.
    """
    with console_lock:
        console.print(text, style=style, markup=markup)


# ── Semantic level messages ──────────────────────────────────────────

def print_success(text: str) -> None:
    """Print a green ✔ success line."""
    t = _theme.current()
    with console_lock:
        if t.success:
            console.print(f"[{t.success}]✔[/{t.success}] {text}")
        else:
            console.print(f"✔ {text}")


def print_error(text: str) -> None:
    """Print a red ✘ error line."""
    t = _theme.current()
    with console_lock:
        if t.error:
            console.print(f"[{t.error}]✘[/{t.error}] {text}")
        else:
            console.print(f"✘ {text}")


def print_warning(text: str) -> None:
    """Print a yellow ⚠ warning line."""
    t = _theme.current()
    with console_lock:
        if t.warning:
            console.print(f"[{t.warning}]⚠[/{t.warning}] {text}")
        else:
            console.print(f"⚠ {text}")


def print_info(text: str) -> None:
    """Print a cyan ℹ info line."""
    t = _theme.current()
    with console_lock:
        if t.info:
            console.print(f"[{t.info}]ℹ[/{t.info}] {text}")
        else:
            console.print(f"ℹ {text}")


# ── Structural output ────────────────────────────────────────────────

def print_panel(
    text: str,
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    style: Optional[str] = None,
    expand: bool = True,
    padding: tuple[int, int] = (1, 2),
) -> None:
    """Render *text* (or a ``rich`` renderable) inside a panel border.

    Parameters
    ----------
    text:     Content – rich markup supported.
    title:    Optional panel title (top-left).
    subtitle: Optional panel subtitle (bottom-right).
    style:    Border style.  Falls back to theme ``panel_border``.
    expand:   Whether the panel should fill terminal width.
    padding:  ``(vertical, horizontal)`` padding inside the panel.
    """
    border = style or _theme.current().panel_border
    with console_lock:
        console.print(
            Panel(
                text,
                title=title,
                subtitle=subtitle,
                border_style=border,
                expand=expand,
                padding=padding,
            )
        )


def print_markdown(text: str) -> None:
    """Render a Markdown string via ``rich``."""
    with console_lock:
        console.print(Markdown(text))


def print_rule(
    title: str = "",
    *,
    style: Optional[str] = None,
    align: str = "center",
) -> None:
    """Print a horizontal rule, optionally with a centred *title*."""
    rule_style = style or _theme.current().rule_style
    with console_lock:
        console.print(Rule(title, style=rule_style, align=align))  # type: ignore[arg-type]


def print_header(title: str, subtitle: str = "") -> None:
    """Print a prominent header panel (full-width, magenta border)."""
    t = _theme.current()
    content = f"[bold]{title}[/bold]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    with console_lock:
        console.print(
            Panel(
                content,
                border_style=t.header_border,
                expand=True,
                padding=(1, 4),
            )
        )


# ── Table ────────────────────────────────────────────────────────────

def print_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    title: Optional[str] = None,
    caption: Optional[str] = None,
    show_lines: bool = False,
    highlight: bool = False,
    column_styles: Optional[Sequence[Optional[str]]] = None,
    zebra: bool = False,
    max_col_width: Optional[int] = None,
    footer_row: Optional[Sequence[Any]] = None,
) -> None:
    """Render a ``rich`` Table.

    Parameters
    ----------
    headers:       Column header strings.
    rows:          Rows – each item is converted to ``str`` automatically.
    title:         Optional table title (printed above).
    caption:       Optional caption (printed below).
    show_lines:    Draw lines between rows.
    highlight:     Enable rich auto-highlight on cell values.
    column_styles: Per-column style strings (same length as *headers*).
    zebra:         Alternating row background shading.
    max_col_width: Truncate cell content to this width with ``…``.
    footer_row:    A highlighted summary / total row appended at the bottom.

    Examples
    --------
    >>> print_table(
    ...     ["Name", "Score"],
    ...     [["Alice", 95], ["Bob", 82]],
    ...     zebra=True,
    ...     footer_row=["Total", 177],
    ... )
    """
    t = _theme.current()
    table = Table(
        title=title,
        caption=caption,
        border_style=t.table_border,
        header_style=t.table_header,
        show_lines=show_lines,
        highlight=highlight,
        show_footer=footer_row is not None,
    )
    for i, header in enumerate(headers):
        col_style = (column_styles[i] if column_styles and i < len(column_styles) else None)
        footer_val = str(footer_row[i]) if footer_row and i < len(footer_row) else ""
        table.add_column(header, style=col_style, footer=footer_val if footer_row else "")
    for row_idx, row in enumerate(rows):
        cells: list[str] = []
        for cell in row:
            s = str(cell)
            if max_col_width is not None and len(s) > max_col_width:
                s = s[: max_col_width - 1] + "…"
            cells.append(s)
        row_style = "on #1a1a2e" if zebra and row_idx % 2 == 1 else None
        table.add_row(*cells, style=row_style)
    with console_lock:
        console.print(table)


# ── Key-value pairs ──────────────────────────────────────────────────

def print_key_value(
    data: dict[str, Any],
    *,
    title: Optional[str] = None,
    key_style: str = "bold cyan",
    value_style: str = "",
    separator: str = ":",
) -> None:
    """Neatly align *data* as key-value pairs inside an optional panel."""
    if not data:
        return
    max_len = max(len(str(k)) for k in data)
    lines: list[str] = []
    for k, v in data.items():
        key_str = str(k).ljust(max_len)
        val_part = f"[{value_style}]{v}[/{value_style}]" if value_style else str(v)
        lines.append(f"[{key_style}]{key_str}{separator}[/{key_style}] {val_part}")
    content = "\n".join(lines)
    if title:
        print_panel(content, title=title)
    else:
        with console_lock:
            console.print(content)


# ── Tree ─────────────────────────────────────────────────────────────

def print_tree(
    label: str,
    data: dict[str, Any],
    *,
    guide_style: str = "dim cyan",
) -> None:
    """Render a nested dictionary as a ``rich`` Tree.

    Parameters
    ----------
    label:       Root label shown at the top.
    data:        Arbitrarily nested ``dict`` (leaves may be any type).
    guide_style: Style for the connecting lines.
    """

    def _add(tree_node: Tree, mapping: dict[str, Any]) -> None:
        for k, v in mapping.items():
            if isinstance(v, dict):
                branch = tree_node.add(f"[bold]{k}[/bold]")
                _add(branch, v)
            elif isinstance(v, (list, tuple)):
                branch = tree_node.add(f"[bold]{k}[/bold]")
                for item in v:
                    if isinstance(item, dict):
                        _add(branch, item)
                    else:
                        branch.add(str(item))
            else:
                tree_node.add(f"[cyan]{k}[/cyan]: {v}")

    tree = Tree(label, guide_style=guide_style)
    _add(tree, data)
    with console_lock:
        console.print(tree)


# ── JSON ─────────────────────────────────────────────────────────────

def print_json(
    data: Union[str, dict, list],
    *,
    indent: int = 2,
    highlight: bool = True,
    highlight_path: Optional[str] = None,
) -> None:
    """Pretty-print JSON.  Accepts a raw string or a Python object.

    Parameters
    ----------
    data : str | dict | list
        JSON string or Python object to render.
    indent : int
        Indentation level for pretty-printing.
    highlight : bool
        Enable syntax highlighting.
    highlight_path : str | None
        JSONPath-style path (e.g. ``"$.model"``) to visually emphasise a
        specific key.  Only simple dot-notation paths are supported
        (e.g. ``"$.a.b"``).

    Examples
    --------
    >>> print_json({"model": "gpt-4", "tokens": 100}, highlight_path="$.model")
    """
    if isinstance(data, str):
        obj = _json.loads(data)
    else:
        obj = data

    json_str = _json.dumps(obj, indent=indent, default=str)

    if highlight_path and isinstance(obj, dict):
        # Simple dot-notation path resolution
        parts = highlight_path.lstrip("$").lstrip(".").split(".")
        target_key = parts[-1] if parts else None
        if target_key:
            # Highlight the key in the rendered output
            json_str = json_str.replace(
                f'"{target_key}":', f'>>"{target_key}"<<:'
            )

    with console_lock:
        if highlight:
            console.print(JSON(json_str) if not highlight_path else Text(json_str))
        else:
            console.print(json_str)


# ── Syntax-highlighted code ──────────────────────────────────────────

def print_syntax(
    code: str,
    language: str,
    *,
    title: Optional[str] = None,
    line_numbers: bool = True,
    theme: Optional[str] = None,
    highlight_lines: Optional[set[int]] = None,
    word_wrap: bool = False,
) -> None:
    """Render a syntax-highlighted code block.

    Parameters
    ----------
    code:            Source code string.
    language:        Pygments language identifier, e.g. ``"python"``.
    title:           Optional filename / label shown in the panel header.
    line_numbers:    Show line numbers.
    theme:           Pygments colour theme; defaults to the active theme value.
    highlight_lines: Set of 1-based line numbers to highlight.
    word_wrap:       Wrap long lines instead of scrolling.
    """
    syntax_theme = theme or _theme.current().syntax_theme
    syn = Syntax(
        code,
        language,
        theme=syntax_theme,
        line_numbers=line_numbers,
        highlight_lines=highlight_lines or set(),
        word_wrap=word_wrap,
    )
    with console_lock:
        if title:
            console.print(Panel(syn, title=title, border_style=_theme.current().panel_border))
        else:
            console.print(syn)


# ── Spinner / Status ─────────────────────────────────────────────────

@contextmanager
def spinner(
    text: str,
    *,
    spinner_name: str = "dots",
    style: Optional[str] = None,
) -> Generator[Status, None, None]:
    """Context manager that displays an animated spinner while work runs.

    Falls back to a plain print when ``TERM=dumb``.

    Usage::

        with spinner("Loading model…") as s:
            result = heavy_computation()
            s.update("Finalising…")

    Parameters
    ----------
    text:         Initial status message.
    spinner_name: Any ``rich`` spinner name (dots, arc, bouncingBar, …).
    style:        Override spinner colour; falls back to theme.
    """
    if is_dumb_terminal:
        console.print(text)
        yield Status(text, console=console)  # type: ignore[arg-type]
        return
    spin_style = style or _theme.current().spinner_style
    with console.status(text, spinner=spinner_name, spinner_style=spin_style) as status:
        yield status


# ── Progress bar ─────────────────────────────────────────────────────

@contextmanager
def progress_bar(
    description: str = "Processing",
    *,
    total: Optional[int] = None,
    show_time: bool = True,
    show_speed: bool = False,
) -> Generator[Progress, None, None]:
    """Context manager that exposes a ``rich.Progress`` instance.

    Falls back to a simple print when ``TERM=dumb``.

    Usage::

        with progress_bar("Uploading", total=100) as bar:
            task = bar.add_task("file.bin", total=100)
            for chunk in chunks:
                upload(chunk)
                bar.advance(task)

    Parameters
    ----------
    description: Default task description label.
    total:       Default total steps (can be ``None`` for indeterminate).
    show_time:   Include elapsed / remaining time columns.
    show_speed:  Include speed (items/s) column.
    """
    if is_dumb_terminal:
        console.print(f"{description}...")
        progress = Progress(console=console, disable=True)
        progress.start()
        try:
            yield progress
        finally:
            progress.stop()
        return

    columns_list: list[Any] = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
    ]
    if show_time:
        columns_list += [TimeElapsedColumn(), TimeRemainingColumn()]

    with Progress(*columns_list, console=console, transient=False) as progress:
        yield progress


def progress_track(
    iterable: Iterable[Any],
    *,
    description: str = "Working…",
    total: Optional[int] = None,
) -> Iterable[Any]:
    """Wrap *iterable* with a rich progress bar. Yields each item.

    Usage::

        for item in progress_track(items, description="Indexing"):
            process(item)
    """
    if is_dumb_terminal:
        console.print(f"{description}...")
        yield from iterable
        return
    yield from track(
        iterable,
        description=description,
        total=total,
        console=console,
    )


# ── progress_map ─────────────────────────────────────────────────────

def progress_map(
    fn: Callable[[T], R],
    items: Iterable[T],
    *,
    description: str = "Processing",
    max_workers: int = 1,
) -> list[R]:
    """Apply *fn* to each item with a progress bar, optionally multi-threaded.

    Parameters
    ----------
    fn : Callable[[T], R]
        Function to apply to each item.
    items : Iterable[T]
        Items to process.
    description : str
        Progress bar description.
    max_workers : int
        Number of threads.  ``1`` means sequential; ``>1`` uses
        ``ThreadPoolExecutor``.

    Returns
    -------
    list[R]
        Results in the same order as *items*.

    Examples
    --------
    >>> results = progress_map(str.upper, ["a", "b", "c"])
    """
    item_list = list(items)
    results: list[R] = [None] * len(item_list)  # type: ignore[list-item]

    with progress_bar(description, total=len(item_list)) as bar:
        task = bar.add_task(description, total=len(item_list))

        if max_workers <= 1:
            for i, item in enumerate(item_list):
                results[i] = fn(item)
                bar.advance(task)
        else:
            lock = threading.Lock()

            def _work(idx_item: tuple[int, T]) -> None:
                idx, item = idx_item
                result = fn(item)
                with lock:
                    results[idx] = result
                bar.advance(task)

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                list(pool.map(_work, enumerate(item_list)))

    return results


# ── Spinner group ────────────────────────────────────────────────────

class _SpinnerHandle:
    """Handle returned by :meth:`SpinnerGroup.add`."""

    def __init__(self, label: str, task_id: Any, group: "SpinnerGroup") -> None:
        self._label = label
        self._task_id = task_id
        self._group = group

    def done(self, message: str = "✔") -> None:
        """Mark this spinner as successfully completed.

        Parameters
        ----------
        message : str
            Suffix shown after the label.
        """
        self._group._update_task(self._task_id, f"[green]{self._label} {message}[/green]")

    def fail(self, message: str = "✘") -> None:
        """Mark this spinner as failed.

        Parameters
        ----------
        message : str
            Suffix shown after the label.
        """
        self._group._update_task(self._task_id, f"[red]{self._label} {message}[/red]")

    def update(self, text: str) -> None:
        """Update the spinner label text.

        Parameters
        ----------
        text : str
            New label text.
        """
        self._group._update_task(self._task_id, text)


class SpinnerGroup:
    """A group of spinners displayed simultaneously via ``rich.Progress``.

    Not intended to be instantiated directly — use :func:`spinner_group`.
    """

    def __init__(self, progress: Progress) -> None:
        self._progress = progress
        self._lock = threading.Lock()

    def add(self, label: str) -> _SpinnerHandle:
        """Add a new spinner to the group.

        Parameters
        ----------
        label : str
            Label shown next to the spinner.

        Returns
        -------
        _SpinnerHandle
            Handle with ``.done()``, ``.fail()``, and ``.update()`` methods.
        """
        with self._lock:
            task_id = self._progress.add_task(label, total=None)
        return _SpinnerHandle(label, task_id, self)

    def _update_task(self, task_id: Any, description: str) -> None:
        with self._lock:
            self._progress.update(task_id, description=description, total=1, completed=1)


@contextmanager
def spinner_group(title: str = "") -> Generator[SpinnerGroup, None, None]:
    """Context manager for multiple concurrent spinners.

    Parameters
    ----------
    title : str
        Optional title printed above the spinner group.

    Yields
    ------
    SpinnerGroup
        Object whose ``.add(label)`` method returns thread-safe handles.

    Examples
    --------
    >>> with spinner_group("Initialising") as sg:
    ...     h1 = sg.add("Loading model")
    ...     h2 = sg.add("Connecting DB")
    ...     # ... do work ...
    ...     h1.done()
    ...     h2.done()
    """
    if title:
        with console_lock:
            console.print(f"[bold]{title}[/bold]")

    if is_dumb_terminal:
        progress = Progress(console=console, disable=True)
        progress.start()
        try:
            yield SpinnerGroup(progress)
        finally:
            progress.stop()
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=False,
    ) as progress:
        yield SpinnerGroup(progress)


# ── Status grid ──────────────────────────────────────────────────────

def print_status_grid(
    items: dict[str, bool | str],
    *,
    cols: int = 3,
    title: Optional[str] = None,
) -> None:
    """Print a compact grid of labelled status indicators.

    Parameters
    ----------
    items : dict[str, bool | str]
        Each key is a label.  ``True`` → ✔ green, ``False`` → ✘ red,
        ``str`` → the string as-is in yellow.
    cols : int
        Number of columns in the grid.
    title : str | None
        Optional title above the grid.

    Examples
    --------
    >>> print_status_grid({"API": True, "DB": False, "Cache": "warm"})
    """
    cells: list[str] = []
    for label, value in items.items():
        if value is True:
            cells.append(f"[green]✔[/green] {label}")
        elif value is False:
            cells.append(f"[red]✘[/red] {label}")
        else:
            cells.append(f"[yellow]{value}[/yellow] {label}")

    t = _theme.current()
    table = Table(
        show_header=False,
        show_edge=False,
        border_style=t.table_border,
        title=title,
        padding=(0, 2),
    )
    for _ in range(cols):
        table.add_column()

    for i in range(0, len(cells), cols):
        chunk = cells[i : i + cols]
        while len(chunk) < cols:
            chunk.append("")
        table.add_row(*chunk)

    with console_lock:
        console.print(table)


# ── Metric cards ─────────────────────────────────────────────────────

def print_metric(
    label: str,
    value: int | float | str,
    *,
    unit: str = "",
    delta: Optional[float] = None,
    width: int = 20,
) -> None:
    """Render a big-number "metric card" for dashboards.

    Parameters
    ----------
    label : str
        Short label above the value.
    value : int | float | str
        The main metric value.
    unit : str
        Unit suffix (e.g. ``"ms"``, ``"%"``).
    delta : float | None
        Change indicator.  Positive → green ▲, negative → red ▼.
    width : int
        Panel width in characters.

    Examples
    --------
    >>> print_metric("Latency", 42, unit="ms", delta=-3.2)
    """
    delta_str = ""
    if delta is not None:
        if delta >= 0:
            delta_str = f"  [green]▲ {delta:+.1f}[/green]"
        else:
            delta_str = f"  [red]▼ {delta:+.1f}[/red]"
    body = f"[dim]{label}[/dim]\n[bold]{value}[/bold] {unit}{delta_str}"
    t = _theme.current()
    with console_lock:
        console.print(
            Panel(body, border_style=t.panel_border, expand=False, width=width)
        )


def print_metric_group(
    metrics: list[dict[str, Any]],
    *,
    cols: int = 3,
) -> None:
    """Render a row of metric cards.

    Parameters
    ----------
    metrics : list[dict]
        Each dict is passed as kwargs to :func:`print_metric`.
        Required keys: ``label``, ``value``.
    cols : int
        Max cards per row.

    Examples
    --------
    >>> print_metric_group([
    ...     {"label": "Latency", "value": 42, "unit": "ms"},
    ...     {"label": "Tokens", "value": 1200},
    ... ])
    """
    panels: list[Panel] = []
    t = _theme.current()
    for m in metrics:
        label = m["label"]
        value = m["value"]
        unit = m.get("unit", "")
        delta = m.get("delta")
        width = m.get("width", 20)
        delta_str = ""
        if delta is not None:
            if delta >= 0:
                delta_str = f"  [green]▲ {delta:+.1f}[/green]"
            else:
                delta_str = f"  [red]▼ {delta:+.1f}[/red]"
        body = f"[dim]{label}[/dim]\n[bold]{value}[/bold] {unit}{delta_str}"
        panels.append(Panel(body, border_style=t.panel_border, expand=False, width=width))

    with console_lock:
        console.print(Columns(panels, equal=False, expand=False))


# ── Timeline ─────────────────────────────────────────────────────────

def print_timeline(
    events: list[dict[str, Any]],
    *,
    title: Optional[str] = None,
    width: Optional[int] = None,
) -> None:
    """Render an ASCII/Unicode Gantt-style timeline.

    Parameters
    ----------
    events : list[dict]
        Each dict must have ``"label"`` (str), ``"start"`` (float), and
        ``"end"`` (float) keys.
    title : str | None
        Optional title above the timeline.
    width : int | None
        Total render width; defaults to terminal width.

    Examples
    --------
    >>> print_timeline([
    ...     {"label": "Task A", "start": 0, "end": 3},
    ...     {"label": "Task B", "start": 2, "end": 5},
    ... ])
    """
    if not events:
        return

    term_width = width or shutil.get_terminal_size((80, 24)).columns
    max_label = max(len(e["label"]) for e in events)
    bar_width = term_width - max_label - 4  # padding

    global_start = min(e["start"] for e in events)
    global_end = max(e["end"] for e in events)
    span = global_end - global_start or 1.0

    lines: list[str] = []
    if title:
        lines.append(f"[bold]{title}[/bold]")

    colors = ["cyan", "green", "yellow", "magenta", "blue"]
    for i, event in enumerate(events):
        label = event["label"].ljust(max_label)
        start_frac = (event["start"] - global_start) / span
        end_frac = (event["end"] - global_start) / span
        start_col = int(start_frac * bar_width)
        end_col = max(start_col + 1, int(end_frac * bar_width))
        color = colors[i % len(colors)]
        bar = " " * start_col + f"[{color}]" + "█" * (end_col - start_col) + f"[/{color}]"
        bar += " " * max(0, bar_width - end_col)
        lines.append(f"{label} │{bar}│")

    with console_lock:
        console.print("\n".join(lines))


# ── Callout ──────────────────────────────────────────────────────────

_CALLOUT_STYLES: dict[str, tuple[str, str]] = {
    "note": ("ℹ", "blue"),
    "tip": ("💡", "green"),
    "warning": ("⚠", "yellow"),
    "danger": ("🔴", "red"),
    "info": ("ℹ", "cyan"),
}


def print_callout(
    text: str,
    *,
    kind: Literal["note", "tip", "warning", "danger", "info"] = "note",
    title: Optional[str] = None,
) -> None:
    """Print a highlighted callout block.

    Parameters
    ----------
    text : str
        Body text of the callout.
    kind : str
        One of ``"note"``, ``"tip"``, ``"warning"``, ``"danger"``, ``"info"``.
    title : str | None
        Custom title; defaults to the *kind* name.

    Examples
    --------
    >>> print_callout("Remember to set API keys.", kind="tip")
    """
    icon, color = _CALLOUT_STYLES.get(kind, ("ℹ", "blue"))
    display_title = title or kind.upper()
    with console_lock:
        console.print(
            Panel(
                f"{icon}  {text}",
                title=f"[bold]{display_title}[/bold]",
                border_style=color,
                expand=True,
                padding=(0, 2),
            )
        )
