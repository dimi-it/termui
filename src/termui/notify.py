"""ui.notify — In-terminal toast-style notification banners.

Usage
-----
    from ui.notify import notify, NotifyLevel

    notify("Model ready", level=NotifyLevel.SUCCESS, duration=3)
    notify("Rate limit hit", level=NotifyLevel.WARNING)
    notify("Disk full", level=NotifyLevel.ERROR, title="Storage alert")

Notification history and replay::

    from ui.notify import notification_history, replay_notifications
    history = notification_history(n=10)
    replay_notifications()

Batching notifications for async contexts::

    from ui.notify import NotifyQueue
    q = NotifyQueue()
    q.put("step 1 done")
    q.put("step 2 done")
    q.flush()  # prints all at once
"""

from __future__ import annotations

import collections
import sys
import time
import threading
from contextlib import contextmanager
from enum import Enum
from typing import Any, Generator, Optional

from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .console import console, console_lock
from . import theme as _theme


class NotifyLevel(Enum):
    """Notification severity levels."""

    INFO    = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR   = "error"


_ICONS: dict[NotifyLevel, str] = {
    NotifyLevel.INFO:    "ℹ",
    NotifyLevel.SUCCESS: "✔",
    NotifyLevel.WARNING: "⚠",
    NotifyLevel.ERROR:   "✘",
}


# ── History ──────────────────────────────────────────────────────────

_MAX_HISTORY = 100
_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=_MAX_HISTORY)


def notify(
    message: str,
    *,
    level: NotifyLevel = NotifyLevel.INFO,
    title: Optional[str] = None,
    duration: Optional[float] = None,
    blocking: bool = False,
    bell: bool = False,
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
    bell:     If ``True``, write ``\\a`` to stderr to trigger the terminal bell.
              Respects ``NO_COLOR`` (= silent).

    Examples
    --------
    >>> notify("Build complete", level=NotifyLevel.SUCCESS, bell=True)
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
    with console_lock:
        console.print(
            Panel(content, title=panel_title, border_style=border_style, expand=False)
        )

    # Store in history
    _history.append({
        "message": message,
        "level": level.value,
        "title": panel_title,
    })

    # Terminal bell
    if bell and not console.no_color:
        sys.stderr.write("\a")
        sys.stderr.flush()

    if duration is not None:
        def _clear() -> None:
            time.sleep(duration)
            with console_lock:
                console.print()  # visual separation after toast

        if blocking:
            _clear()
        else:
            threading.Thread(target=_clear, daemon=True).start()


# ── History / replay ─────────────────────────────────────────────────

def notification_history(n: int = 20) -> list[dict[str, Any]]:
    """Return the last *n* notifications.

    Parameters
    ----------
    n : int
        Maximum number of entries to return.

    Returns
    -------
    list[dict[str, Any]]
        Each dict has ``message``, ``level``, and ``title`` keys.

    Examples
    --------
    >>> notify("test")
    >>> len(notification_history()) >= 1
    True
    """
    return list(_history)[-n:]


def replay_notifications() -> None:
    """Re-print all stored notifications.

    Examples
    --------
    >>> replay_notifications()
    """
    for entry in _history:
        lvl = NotifyLevel(entry["level"])
        notify(entry["message"], level=lvl, title=entry["title"])


# ── NotifyQueue for async / threaded contexts ────────────────────────

class NotifyQueue:
    """Batch-collect notifications and flush them all at once.

    Useful when an agent is running in async/threaded mode and wants to
    print notifications only at safe checkpoints.

    Examples
    --------
    >>> q = NotifyQueue()
    >>> q.put("step 1 done")
    >>> q.put("step 2 failed", level=NotifyLevel.ERROR)
    >>> q.flush()
    """

    def __init__(self) -> None:
        self._queue: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def put(
        self,
        message: str,
        *,
        level: NotifyLevel = NotifyLevel.INFO,
        title: Optional[str] = None,
    ) -> None:
        """Enqueue a notification.

        Parameters
        ----------
        message : str
            Notification body.
        level : NotifyLevel
            Severity level.
        title : str | None
            Optional title.
        """
        with self._lock:
            self._queue.append({
                "message": message,
                "level": level,
                "title": title,
            })

    def flush(self) -> None:
        """Print and clear all queued notifications."""
        with self._lock:
            items = list(self._queue)
            self._queue.clear()
        for item in items:
            notify(item["message"], level=item["level"], title=item["title"])


# ── Sticky banner ────────────────────────────────────────────────────

@contextmanager
def sticky_notify(
    message: str,
    *,
    level: NotifyLevel = NotifyLevel.INFO,
) -> Generator[None, None, None]:
    """A notification that persists at the top of output until dismissed.

    Uses ``rich.Live`` to keep the banner visible.  The banner is removed
    when the context exits.

    Parameters
    ----------
    message : str
        Banner text.
    level : NotifyLevel
        Severity level controlling colour/icon.

    Examples
    --------
    >>> with sticky_notify("Build in progress…", level=NotifyLevel.INFO):
    ...     do_build()
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
    panel_title = level.name.capitalize()
    content = Text(f"{icon}  {message}")
    panel = Panel(content, title=panel_title, border_style=border_style, expand=False)

    with Live(panel, console=console, refresh_per_second=1, transient=True):
        yield
