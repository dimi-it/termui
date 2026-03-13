"""ui.logging — Drop-in ``logging.Handler`` that renders through rich.

Usage
-----
    from ui.logging import get_logger

    log = get_logger("my_agent")
    log.info("Model loaded")
    log.warning("Context window at 80 %%")
    log.error("API call failed", exc_info=True)

Or, to integrate with an existing ``logging`` hierarchy::

    import logging
    from ui.logging import RichHandler

    logging.basicConfig(handlers=[RichHandler()], level=logging.DEBUG)
"""

from __future__ import annotations

import logging
import traceback
from datetime import datetime
from typing import Optional

from rich.text import Text

from .console import console
from . import theme as _theme


# ── Handler ──────────────────────────────────────────────────────────

class RichHandler(logging.Handler):
    """A ``logging.Handler`` that renders log records via the shared ``rich``
    console with timestamps, coloured level labels, and optional tracebacks.

    Parameters
    ----------
    show_time:   Include a timestamp column.
    show_path:   Include the module/filename:lineno column.
    markup:      Allow rich markup in log messages.
    level:       Minimum log level to handle.
    """

    LEVEL_STYLES: dict[int, str] = {
        logging.DEBUG:    "dim cyan",
        logging.INFO:     "bold cyan",
        logging.WARNING:  "bold yellow",
        logging.ERROR:    "bold red",
        logging.CRITICAL: "bold white on red",
    }

    LEVEL_ICONS: dict[int, str] = {
        logging.DEBUG:    "·",
        logging.INFO:     "ℹ",
        logging.WARNING:  "⚠",
        logging.ERROR:    "✘",
        logging.CRITICAL: "☠",
    }

    def __init__(
        self,
        *,
        show_time: bool = True,
        show_path: bool = False,
        markup: bool = True,
        level: int = logging.NOTSET,
    ) -> None:
        super().__init__(level)
        self.show_time = show_time
        self.show_path = show_path
        self.markup = markup

    def emit(self, record: logging.LogRecord) -> None:
        t = _theme.current()
        level_style = self.LEVEL_STYLES.get(record.levelno, "")
        icon = self.LEVEL_ICONS.get(record.levelno, "•")
        level_name = record.levelname.ljust(8)

        parts: list[str] = []

        if self.show_time:
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            parts.append(f"[dim]{ts}[/dim]")

        parts.append(f"[{level_style}]{icon} {level_name}[/{level_style}]")

        if self.show_path:
            path = f"{record.module}:{record.lineno}"
            parts.append(f"[dim]{path}[/dim]")

        msg = record.getMessage()
        parts.append(msg)

        console.print(" ".join(parts), markup=self.markup, highlight=False)

        if record.exc_info:
            console.print_exception(extra_lines=1)


# ── Convenience factory ──────────────────────────────────────────────

def get_logger(
    name: str,
    *,
    level: int = logging.DEBUG,
    show_time: bool = True,
    show_path: bool = False,
) -> logging.Logger:
    """Return a ``Logger`` pre-configured with a ``RichHandler``.

    Repeated calls with the same *name* return the same logger (standard
    Python logging behaviour) but will not add duplicate handlers.

    Parameters
    ----------
    name:      Logger name (typically the module or agent name).
    level:     Minimum level to capture.
    show_time: Show timestamps in output.
    show_path: Show ``module:lineno`` source location.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(show_time=show_time, show_path=show_path, level=level)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # avoid double-printing to root logger
    return logger
