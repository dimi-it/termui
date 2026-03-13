"""ui.console — Shared ``rich`` Console singleton with thread-safe locking.

All other modules import from here so there is exactly one Console
instance for the lifetime of the process (no interleaved output).

Thread Safety
-------------
A module-level ``console_lock`` (``threading.RLock``) is exposed for callers
that need to guard multi-line atomic output.  The :class:`_ConsoleLock`
context manager wraps ``console.print`` for convenience.

Environment Variables
---------------------
- ``UI_FORCE_TERMINAL=1`` — force rich colour output even when stdout is not a TTY.
- ``NO_COLOR`` — any non-empty value disables colour (https://no-color.org).
- ``TERM=dumb`` — detected at import time; exposed as :data:`is_dumb_terminal`.
"""

from __future__ import annotations

import os
import sys
import threading
from contextlib import contextmanager
from typing import Any, Generator

from rich.console import Console

# ── Environment detection ────────────────────────────────────────────

_force_terminal: bool | None = None
if os.environ.get("UI_FORCE_TERMINAL", "").lower() in ("1", "true", "yes"):
    _force_terminal = True

_no_color: bool = bool(os.environ.get("NO_COLOR", ""))

is_dumb_terminal: bool = os.environ.get("TERM", "").lower() == "dumb"
"""``True`` when ``TERM=dumb`` — spinners and progress bars should be skipped."""

# Ensure UTF-8 encoding on Windows to support Unicode characters
if sys.platform == "win32":
    try:
        import io
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        else:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

console = Console(
    highlight=True,
    force_terminal=_force_terminal,
    no_color=_no_color,
)

console_lock: threading.RLock = threading.RLock()
"""Reentrant lock guarding the shared :data:`console`.

Use this directly or via :func:`locked_console` to prevent interleaved
output from concurrent threads.
"""


@contextmanager
def locked_console() -> Generator[Console, None, None]:
    """Context manager that acquires :data:`console_lock` and yields the console.

    Examples
    --------
    >>> with locked_console() as con:
    ...     con.print("line 1")
    ...     con.print("line 2")  # guaranteed atomic block
    """
    with console_lock:
        yield console


def get_console() -> Console:
    """Return the shared ``Console`` instance."""
    return console
