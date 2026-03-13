"""ui.confirm_panel — Rich confirmation panels for destructive actions.

Usage
-----
    from ui.confirm_panel import confirm_action

    if confirm_action("Delete all logs?", details="This cannot be undone."):
        delete_logs()

The panel renders a styled warning box with the question and optional
detail text before falling through to a yes/no prompt.
"""

from __future__ import annotations

from typing import Optional

from rich.panel import Panel
from rich.text import Text

from .console import console, console_lock
from . import theme as _theme
from .input import ask_confirm


def confirm_action(
    question: str,
    *,
    details: str = "",
    default: bool = False,
    danger: bool = True,
    title: str | None = None,
) -> bool:
    """Display a confirmation panel and return the user's choice.

    Parameters
    ----------
    question : str
        The main question (e.g. "Delete all logs?").
    details : str
        Extra detail text rendered inside the panel.
    default : bool
        Default answer when the user presses Enter.
    danger : bool
        If ``True``, the panel uses the theme's ``error`` colour for the
        border to visually signal a destructive operation.  If ``False``,
        the ``warning`` colour is used instead.
    title : str | None
        Custom panel title; defaults to ``"⚠ Confirm"`` / ``"🔴 Danger"``.

    Returns
    -------
    bool
        ``True`` if the user confirmed, ``False`` otherwise.

    Examples
    --------
    >>> if confirm_action("Drop database?", details="All data will be lost."):
    ...     drop_db()
    """
    t = _theme.current()
    if danger:
        border_style = t.error or "bold red"
        default_title = "🔴 Danger"
    else:
        border_style = t.warning or "bold yellow"
        default_title = "⚠ Confirm"

    panel_title = title or default_title

    body_parts: list[str] = [f"[bold]{question}[/bold]"]
    if details:
        body_parts.append(f"\n[dim]{details}[/dim]")
    body = "\n".join(body_parts)

    with console_lock:
        console.print(
            Panel(
                body,
                title=panel_title,
                border_style=border_style,
                expand=False,
                padding=(1, 3),
            )
        )

    return ask_confirm(question, default=default)
