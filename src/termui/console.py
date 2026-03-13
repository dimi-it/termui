"""ui.console — Shared ``rich`` Console singleton.

All other modules import from here so there is exactly one Console
instance for the lifetime of the process (no interleaved output).
"""

from __future__ import annotations

import os
import sys
from rich.console import Console

# Respect NO_COLOR / TERM env vars automatically.
_force_terminal: bool | None = None
if os.environ.get("UI_FORCE_TERMINAL", "").lower() in ("1", "true", "yes"):
    _force_terminal = True

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
)


def get_console() -> Console:
    """Return the shared ``Console`` instance."""
    return console
