"""ui.output — High-level output helpers built on ``rich``.

All functions use the shared console and respect the active theme.
"""

from __future__ import annotations

import json as _json
from contextlib import contextmanager
from typing import Any, Generator, Iterable, Optional, Sequence, Union

from rich import print_json as _rprint_json
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

from .console import console
from . import theme as _theme


# ── Basic print ──────────────────────────────────────────────────────

def print_text(text: str, style: Optional[str] = None, *, markup: bool = True) -> None:
    """Print *text* to the shared console.

    Parameters
    ----------
    text:    The string to print (rich markup is enabled by default).
    style:   Optional rich style string, e.g. ``"bold blue"``.
    markup:  Set to ``False`` to treat *text* as plain text.
    """
    console.print(text, style=style, markup=markup)


# ── Semantic level messages ──────────────────────────────────────────

def print_success(text: str) -> None:
    """Print a green ✔ success line."""
    t = _theme.current()
    if t.success:
        console.print(f"[{t.success}]✔[/{t.success}] {text}")
    else:
        console.print(f"✔ {text}")


def print_error(text: str) -> None:
    """Print a red ✘ error line."""
    t = _theme.current()
    if t.error:
        console.print(f"[{t.error}]✘[/{t.error}] {text}")
    else:
        console.print(f"✘ {text}")


def print_warning(text: str) -> None:
    """Print a yellow ⚠ warning line."""
    t = _theme.current()
    if t.warning:
        console.print(f"[{t.warning}]⚠[/{t.warning}] {text}")
    else:
        console.print(f"⚠ {text}")


def print_info(text: str) -> None:
    """Print a cyan ℹ info line."""
    t = _theme.current()
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
    console.print(Markdown(text))


def print_rule(
    title: str = "",
    *,
    style: Optional[str] = None,
    align: str = "center",
) -> None:
    """Print a horizontal rule, optionally with a centred *title*."""
    rule_style = style or _theme.current().rule_style
    console.print(Rule(title, style=rule_style, align=align))  # type: ignore[arg-type]


def print_header(title: str, subtitle: str = "") -> None:
    """Print a prominent header panel (full-width, magenta border)."""
    t = _theme.current()
    content = f"[bold]{title}[/bold]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
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
    """
    t = _theme.current()
    table = Table(
        title=title,
        caption=caption,
        border_style=t.table_border,
        header_style=t.table_header,
        show_lines=show_lines,
        highlight=highlight,
    )
    for i, header in enumerate(headers):
        col_style = (column_styles[i] if column_styles and i < len(column_styles) else None)
        table.add_column(header, style=col_style)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
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
    console.print(tree)


# ── JSON ─────────────────────────────────────────────────────────────

def print_json(
    data: Union[str, dict, list],
    *,
    indent: int = 2,
    highlight: bool = True,
) -> None:
    """Pretty-print JSON.  Accepts a raw string or a Python object."""
    if not isinstance(data, str):
        data = _json.dumps(data, indent=indent, default=str)
    if highlight:
        console.print(JSON(data))
    else:
        console.print(data)


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
    columns_list = [
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
    yield from track(
        iterable,
        description=description,
        total=total,
        console=console,
    )
