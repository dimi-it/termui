"""ui.notify — In-terminal toast-style notification banners.

Usage
-----
    from ui.notify import notify, NotifyLevel

    notify("Model ready", level=NotifyLevel.SUCCESS, duration=3)
    notify("Rate limit hit", level=NotifyLevel.WARNING)
    notify("Disk full", level=NotifyLevel.ERROR, title="Storage alert")
"""

from __future__ import annotations

import time
import threading
from enum import Enum
from typing import Optional

from rich.panel import Panel
from rich.text import Text

from .console import console
from . import theme as _theme


class NotifyLevel(Enum):
    INFO    = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR   = "error"


_ICONS = {
    NotifyLevel.INFO:    "ℹ",
    NotifyLevel.SUCCESS: "✔",
    NotifyLevel.WARNING: "⚠",
    NotifyLevel.ERROR:   "✘",
}


def notify(
    message: str,
    *,
    level: NotifyLevel = NotifyLevel.INFO,
    title: Optional[str] = None,
    duration: Optional[float] = None,
    blocking: bool = False,
) -> None:
    """Display a styled notification banner.

    Parameters
    ----------
    message:  Body text.
    level:    ``NotifyLevel`` enum value controlling colour/icon.
    title:    Optional panel title; defaults to the level name.
    duration: Seconds after which a blank line is printed (visual separation).
              ``None`` → no timer.  Requires *blocking=False* for async behaviour.
    blocking: If ``True`` and *duration* is set, block the calling thread.
    """
    t = _theme.current()
    style_map = {
        NotifyLevel.INFO:    t.info,
        NotifyLevel.SUCCESS: t.success,
        NotifyLevel.WARNING: t.warning,
        NotifyLevel.ERROR:   t.error,
    }
    border_style = style_map[level]
    icon = _ICONS[level]
    panel_title = title or level.name.capitalize()

    content = Text(f"{icon}  {message}")
    console.print(
        Panel(content, title=panel_title, border_style=border_style, expand=False)
    )

    if duration is not None:
        def _clear() -> None:
            time.sleep(duration)
            console.print()  # visual separation after toast

        if blocking:
            _clear()
        else:
            threading.Thread(target=_clear, daemon=True).start()
